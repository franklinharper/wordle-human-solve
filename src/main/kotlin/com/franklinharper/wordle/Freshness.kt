package com.franklinharper.wordle

import com.franklinharper.wordle.fetch.META_FILE
import com.franklinharper.wordle.fetch.RefreshOutcome
import com.franklinharper.wordle.fetch.attemptRefresh
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.io.IOException
import java.nio.file.Files
import java.nio.file.Path
import java.time.Duration
import java.time.OffsetDateTime
import java.time.format.DateTimeParseException
import com.github.ajalt.clikt.core.ProgramResult

/**
 * The word-list freshness gate (port of analysis.py's
 * ensure_wordlists_fresh). Runs at most once per process. On
 * refresh failure the error is loud and the process exits
 * non-zero — analysis never runs silently on stale data.
 * WORDLE_STALE_OK=1 bypasses with a visible warning;
 * WORDLE_MAX_STALE_HOURS sets the threshold (default 24).
 */
object Freshness {
    private var checked = false

    private fun staleOk(): Boolean = System.getenv("WORDLE_STALE_OK") == "1"

    private fun maxStaleHours(): Double =
        System.getenv("WORDLE_MAX_STALE_HOURS")?.toDoubleOrNull() ?: 24.0

    private fun err(msg: String) = System.err.println(msg)

    /** An unreadable meta file means stale — say why, with the cause. */
    private fun unreadableMeta(e: Exception) {
        err(
            "wordlists.meta.json unreadable " +
                "(${e::class.simpleName}: ${e.message}) -- " +
                "treating the word lists as stale."
        )
    }

    private fun loudFail(label: String, detail: String?, hint: String): Nothing {
        err("ERROR: Wordle word-list refresh failed ($label): $detail")
        err("  The local word lists may be stale; refusing to run analysis on them.")
        err("  Hint: $hint")
        throw ProgramResult(1)
    }

    suspend fun ensureFresh(repoRoot: Path) {
        if (checked) return
        checked = true

        var stale = true
        val metaPath = repoRoot.resolve(META_FILE)
        if (Files.exists(metaPath)) {
            try {
                val meta = Json.parseToJsonElement(
                    Files.readString(metaPath)).jsonObject
                val fetched = OffsetDateTime.parse(
                    meta.getValue("fetched_at").jsonPrimitive.content)
                val ageHours = Duration.between(
                    fetched, OffsetDateTime.now(fetched.offset)
                ).seconds / 3600.0
                stale = ageHours > maxStaleHours()
            } catch (e: IOException) {
                unreadableMeta(e) // unreadable meta -> treat as stale
            } catch (e: SerializationException) {
                unreadableMeta(e)
            } catch (e: DateTimeParseException) {
                unreadableMeta(e)
            } catch (e: NoSuchElementException) {
                unreadableMeta(e)
            }
        }
        if (!stale) return

        if (staleOk()) {
            err(
                "WARNING: WORDLE_STALE_OK=1 -- skipping word-list refresh; " +
                    "analysis is running on possibly-stale data."
            )
            return
        }

        // The refresh hits the network and can take ~20s (NYT page +
        // JS bundles + daily-solution endpoint). Say so on stderr --
        // otherwise a simple patterns query looks hung while it works.
        err(
            "word lists are stale (>%.0fh old) -- ".format(maxStaleHours()) +
                "refreshing from NYT (takes ~20s)..."
        )
        val summary = when (val outcome = attemptRefresh(repoRoot)) {
            is RefreshOutcome.Ok -> outcome.summary
            is RefreshOutcome.Failed ->
                loudFail(outcome.label, outcome.detail, outcome.hint)
        }
        if (summary.changed) {
            err("word lists updated -- consider committing.")
        } else {
            err("word lists refreshed -- no changes.")
        }
    }
}
