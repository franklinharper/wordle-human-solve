package com.franklinharper.wordle.fetch

import io.ktor.client.HttpClient
import io.ktor.client.engine.cio.CIO
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.request.get
import io.ktor.client.request.header
import io.ktor.client.statement.HttpResponse
import io.ktor.client.statement.bodyAsText
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption
import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

/**
 * Fetch the Wordle word lists from the NYT (port of
 * fetch_wordle_words.py).
 *
 * The two lists come from two different NYT sources:
 *   valid guesses — extracted from the NYT Wordle JavaScript bundle;
 *   valid answers — collected forward from the NYT daily solution
 *   endpoint, one newly observed solution at a time.
 *
 * Update policy: fetched data is validated before anything is
 * written. The canonical files are only replaced when every check
 * passes; any failure keeps the old files byte-identical and throws.
 *
 * Environment overrides (mainly for testing): WORDLE_URL,
 * WORDLE_SOLUTION_URL (with {date}), WORDLE_BACKFILL_START.
 */

private val wordleUrl: String =
    System.getenv("WORDLE_URL")
        ?: "https://www.nytimes.com/games/wordle/index.html"
private val solutionUrlTemplate: String =
    System.getenv("WORDLE_SOLUTION_URL")
        ?: "https://www.nytimes.com/svc/wordle/v2/{date}.json"
private val backfillStart: String =
    System.getenv("WORDLE_BACKFILL_START") ?: "2026-02-17"

private const val REQUEST_TIMEOUT_MS = 20_000L
// Seconds between daily-solution requests, as a polite rate limit.
private const val POLITE_DELAY_MS = 200L
private val LA_TZ: ZoneId = ZoneId.of("America/Los_Angeles")
// Sanity floor for the guess list.
private const val MIN_GUESSES = 10_000
private const val USER_AGENT =
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

const val GUESSES_FILE = "wordle_valid_guesses.json"
const val ANSWERS_FILE = "answers.txt"
const val OBSERVED_FILE = "answers_observed.json"
const val META_FILE = "wordlists.meta.json"

/** A refresh failure, with a one-line remediation hint. */
sealed class WordleRefreshError(message: String) : Exception(message) {
    open fun label(): String = "refresh failure"
    open val hint: String =
        "set WORDLE_STALE_OK=1 to proceed on stale data anyway."
}

class NetworkError(message: String) : WordleRefreshError(message) {
    override fun label(): String = "network failure"
    override val hint: String =
        "check the network/proxy, then retry; " +
            "or set WORDLE_STALE_OK=1 to proceed on stale data anyway."
}

class BundleFormatError(message: String) : WordleRefreshError(message) {
    override fun label(): String = "NYT bundle format change"
    override val hint: String =
        "the NYT changed their bundle format -- the guess-list " +
            "extractor in the fetch package needs updating; " +
            "or set WORDLE_STALE_OK=1 to proceed on stale data anyway."
}

class ValidationError(message: String) : WordleRefreshError(message) {
    override fun label(): String = "validation failure"
    override val hint: String =
        "fetched data failed sanity checks -- refusing to use it; " +
            "inspect the fetched data manually, " +
            "or set WORDLE_STALE_OK=1 to proceed on stale data anyway."
}

data class GuessesSummary(
    val added: List<String>,
    val removed: List<String>,
    val changed: Boolean,
    val count: Int,
)

data class AnswersSummary(
    val added: List<Pair<String, String>>,
    val checked: Int,
    val changed: Boolean,
    val count: Int,
)

data class RefreshSummary(
    val guesses: GuessesSummary,
    val answers: AnswersSummary,
    val changed: Boolean,
)

private fun newClient(): HttpClient = HttpClient(CIO) {
    install(HttpTimeout) {
        requestTimeoutMillis = REQUEST_TIMEOUT_MS
        connectTimeoutMillis = REQUEST_TIMEOUT_MS
        socketTimeoutMillis = REQUEST_TIMEOUT_MS
    }
}

/** Fetch a URL's response. Transport problems -> [NetworkError]. */
private suspend fun fetchResponse(client: HttpClient, url: String): HttpResponse =
    try {
        client.get(url) { header("User-Agent", USER_AGENT) }
    } catch (e: Exception) {
        throw NetworkError("could not fetch $url: ${e.message}")
    }

private data class Solution(val word: String?, val daysSinceLaunch: Int?)

/** One day's solution, or null when not published yet (HTTP 404). */
private suspend fun fetchSolution(
    client: HttpClient,
    dateIso: String,
): Solution? {
    val url = solutionUrlTemplate.replace("{date}", dateIso)
    val resp = try {
        client.get(url) { header("User-Agent", USER_AGENT) }
    } catch (e: Exception) {
        throw NetworkError("could not fetch solution for $dateIso: ${e.message}")
    }
    if (resp.status.value == 404) return null
    if (resp.status.value != 200) {
        throw NetworkError(
            "solution endpoint returned HTTP ${resp.status.value} for $dateIso")
    }
    val data = Json.parseToJsonElement(resp.bodyAsText()).jsonObject
    return Solution(
        data["solution"]?.jsonPrimitive?.content,
        data["days_since_launch"]?.jsonPrimitive?.content?.toIntOrNull(),
    )
}

private val scriptSrcRegex =
    Regex("""<script[^>]*\bsrc\s*=\s*["']([^"']+)["']""", RegexOption.IGNORE_CASE)

private val wordArrayRegex =
    Regex("""\[("(?:[a-z]{5})",?\s*){20,}]""")
private val quotedWordRegex = Regex(""""([a-z]{5})"""")

/**
 * Search JS text for arrays of 5-letter lowercase words. Returns
 * unique word-list candidates, largest first.
 */
fun findWordArrays(jsText: String): List<List<String>> {
    val candidates = mutableListOf<List<String>>()
    for (match in wordArrayRegex.findAll(jsText)) {
        val words = quotedWordRegex.findAll(match.value)
            .map { it.groupValues[1] }.toList()
        if (words.size >= 20) {
            candidates.add(words.distinct())
        }
    }
    val seen = HashSet<Set<String>>()
    val uniqueLists = candidates.filter { seen.add(it.toSet()) }
    return uniqueLists.sortedByDescending { it.size }
}

private val jsonPretty = Json { prettyPrint = true; prettyPrintIndent = "  " }

private fun atomicWrite(path: Path, content: String) {
    val tmp = Files.createTempFile(
        path.parent ?: Path.of("."), ".tmp-", null)
    try {
        Files.writeString(tmp, content)
        Files.move(
            tmp, path,
            StandardCopyOption.ATOMIC_MOVE,
            StandardCopyOption.REPLACE_EXISTING,
        )
    } catch (e: Exception) {
        Files.deleteIfExists(tmp)
        throw e
    }
}

private fun atomicWriteJson(path: Path, element: kotlinx.serialization.json.JsonElement) {
    atomicWrite(path, jsonPretty.encodeToString(
        kotlinx.serialization.json.JsonElement.serializer(), element) + "\n")
}

private data class CurrentLists(
    val guesses: Set<String>,
    val answers: Set<String>,
    val observed: Map<String, String>,
)

/** Load the current canonical files; missing files -> empty. */
private fun loadCurrent(repoRoot: Path): CurrentLists {
    val guessesPath = repoRoot.resolve(GUESSES_FILE)
    val answersPath = repoRoot.resolve(ANSWERS_FILE)
    val observedPath = repoRoot.resolve(OBSERVED_FILE)
    val guesses = if (Files.exists(guessesPath)) {
        Json.parseToJsonElement(Files.readString(guessesPath))
            .jsonArray.map { it.jsonPrimitive.content }.toSet()
    } else emptySet()
    val answers = if (Files.exists(answersPath)) {
        Files.readAllLines(answersPath)
            .map { it.trim() }.filter { it.isNotEmpty() }.toSet()
    } else emptySet()
    val observed = if (Files.exists(observedPath)) {
        Json.parseToJsonElement(Files.readString(observedPath))
            .jsonObject.mapValues { it.value.jsonPrimitive.content }
    } else emptyMap()
    return CurrentLists(guesses, answers, observed)
}

/** Re-download the valid-guess list from the NYT JS bundle. */
suspend fun refreshGuesses(repoRoot: Path): GuessesSummary {
    val client = newClient()
    try {
        val pageResp = fetchResponse(client, wordleUrl)
        if (pageResp.status.value != 200) {
            throw NetworkError(
                "NYT Wordle page returned HTTP ${pageResp.status.value}")
        }
        val html = pageResp.bodyAsText()
        val base = "https://www.nytimes.com"
        val scriptUrls = scriptSrcRegex.findAll(html)
            .map { it.groupValues[1] }
            .filter { it.isNotEmpty() }
            .map { src ->
                if (src.startsWith("http://") || src.startsWith("https://") ||
                    src.startsWith("file://")
                ) src else base + src
            }
            .toList()
        if (scriptUrls.isEmpty()) {
            throw BundleFormatError(
                "no <script src=...> tags found on the NYT Wordle page; " +
                    "the page structure may have changed")
        }
        val candidates = mutableListOf<List<String>>()
        for (url in scriptUrls) {
            try {
                val resp = fetchResponse(client, url)
                if (resp.status.value != 200) {
                    throw NetworkError(
                        "script returned HTTP ${resp.status.value}")
                }
                candidates.addAll(findWordArrays(resp.bodyAsText()))
            } catch (e: Exception) {
                // One bad script URL must not kill the refresh; the
                // page itself already fetched fine, so this is just
                // a stale link.
                println("  (skipping script, fetch failed: ${e.message})")
            }
        }
        if (candidates.isEmpty()) {
            throw BundleFormatError(
                "could not identify the valid-guess word array in the " +
                    "NYT bundle; the bundle format may have changed")
        }
        val guesses = candidates.maxByOrNull { it.size }!!
        val okWords = guesses.all {
            it.length == 5 && it.all { c -> c.isLetter() } && it == it.lowercase()
        }
        if (!okWords) {
            throw ValidationError("guess list contains malformed words")
        }
        if (guesses.size < MIN_GUESSES) {
            throw ValidationError(
                "guess list has ${guesses.size} words, below sanity " +
                    "floor $MIN_GUESSES")
        }
        val old = loadCurrent(repoRoot).guesses
        val added = (guesses.toSet() - old).sorted()
        val removed = (old - guesses.toSet()).sorted()
        val changed = added.isNotEmpty() || removed.isNotEmpty()
        if (changed) {
            val array = kotlinx.serialization.json.JsonArray(
                guesses.sorted().map {
                    kotlinx.serialization.json.JsonPrimitive(it)
                })
            atomicWriteJson(repoRoot.resolve(GUESSES_FILE), array)
        }
        return GuessesSummary(added, removed, changed, guesses.size)
    } finally {
        client.close()
    }
}

/**
 * Forward-collect daily solutions from the NYT solution endpoint,
 * walking every date from (last recorded date + 1) through today
 * (America/Los_Angeles), so missed days self-heal.
 */
suspend fun refreshAnswers(repoRoot: Path): AnswersSummary {
    val current = loadCurrent(repoRoot)
    val answers = current.answers.toMutableSet()
    val observed = current.observed.toMutableMap()

    val start: LocalDate = if (observed.isNotEmpty()) {
        LocalDate.parse(observed.values.maxOrNull()!!).plusDays(1)
    } else {
        LocalDate.parse(backfillStart)
    }
    val today = LocalDate.now(LA_TZ)

    val added = mutableListOf<Pair<String, String>>()
    var checked = 0
    var expectedN: Int? = null
    val client = newClient()
    try {
        var date = start
        while (!date.isAfter(today)) {
            val dateIso = date.toString()
            val solution = fetchSolution(client, dateIso)
            if (solution == null) {
                System.err.println(
                    "  (no solution published yet for $dateIso; skipping)")
                date = date.plusDays(1)
                continue
            }
            checked++
            val word = solution.word
            if (word == null || word.length != 5 ||
                !word.all { it.isLetter() } || word != word.lowercase()
            ) {
                throw ValidationError(
                    "solution for $dateIso is malformed: $word")
            }
            val n = solution.daysSinceLaunch
            if (expectedN != null && n != expectedN) {
                throw ValidationError(
                    "days_since_launch discontinuity at $dateIso: " +
                        "got $n, expected $expectedN")
            }
            expectedN = n?.plus(1)
            if (word !in answers) {
                answers.add(word)
                observed[word] = dateIso
                added.add(word to dateIso)
            }
            Thread.sleep(POLITE_DELAY_MS)
            date = date.plusDays(1)
        }
    } finally {
        client.close()
    }

    val changed = added.isNotEmpty()
    if (changed) {
        atomicWrite(
            repoRoot.resolve(ANSWERS_FILE),
            answers.sorted().joinToString("") { "$it\n" },
        )
        val obj = JsonObject(
            observed.toSortedMap().mapValues {
                kotlinx.serialization.json.JsonPrimitive(it.value)
            })
        atomicWriteJson(repoRoot.resolve(OBSERVED_FILE), obj)
    }
    return AnswersSummary(added, checked, changed, answers.size)
}

fun writeMeta(repoRoot: Path) {
    val fetchedAt = OffsetDateTime.now(ZoneOffset.UTC)
        .format(DateTimeFormatter.ISO_OFFSET_DATE_TIME)
    val meta = JsonObject(
        mapOf(
            "fetched_at" to kotlinx.serialization.json.JsonPrimitive(fetchedAt),
            "sources" to JsonObject(
                mapOf(
                    "guesses" to kotlinx.serialization.json.JsonPrimitive(wordleUrl),
                    "answers" to kotlinx.serialization.json.JsonPrimitive(
                        solutionUrlTemplate),
                )
            ),
        )
    )
    atomicWriteJson(repoRoot.resolve(META_FILE), meta)
}

/** Run both refresh paths; write the meta file on success. */
suspend fun refreshAll(repoRoot: Path): RefreshSummary {
    val guesses = refreshGuesses(repoRoot)
    val answers = refreshAnswers(repoRoot)
    writeMeta(repoRoot)
    return RefreshSummary(guesses, answers, guesses.changed || answers.changed)
}
