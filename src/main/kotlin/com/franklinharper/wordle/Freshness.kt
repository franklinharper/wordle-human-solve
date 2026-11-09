package com.franklinharper.wordle

import com.franklinharper.wordle.fetch.META_FILE
import com.franklinharper.wordle.fetch.WordleRefreshError
import com.franklinharper.wordle.fetch.refreshAll
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.nio.file.Files
import java.nio.file.Path
import java.time.Duration
import java.time.OffsetDateTime
import kotlin.system.exitProcess

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

    private fun loudFail(label: String, detail: String?, hint: String): Nothing {
        err("ERROR: Wordle word-list refresh failed ($label): $detail")
        err("  The local word lists may be stale; refusing to run analysis on them.")
        err("  Hint: $hint")
        exitProcess(1)
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
            } catch (e: Exception) {
                stale = true // unreadable meta -> treat as stale
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
        val summary = try {
            refreshAll(repoRoot)
        } catch (e: WordleRefreshError) {
            loudFail(e.label(), e.message, e.hint)
        } catch (e: Exception) {
            loudFail(
                "unexpected error", e.message,
                "set WORDLE_STALE_OK=1 to proceed on stale data anyway.",
            )
        }
        if (summary.changed) {
            err("word lists updated -- consider committing.")
        } else {
            err("word lists refreshed -- no changes.")
        }
    }
}
