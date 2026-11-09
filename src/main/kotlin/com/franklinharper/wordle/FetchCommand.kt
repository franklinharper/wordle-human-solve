package com.franklinharper.wordle

import com.franklinharper.wordle.core.RepoRoot
import com.franklinharper.wordle.fetch.WordleRefreshError
import com.franklinharper.wordle.fetch.refreshAll
import com.github.ajalt.clikt.command.SuspendingCliktCommand
import com.github.ajalt.clikt.core.Context
import java.time.LocalDate
import java.time.ZoneId
import java.util.Locale
import kotlin.system.exitProcess

/** Refresh the word lists from the NYT (fetch_wordle_words.py's CLI). */
class FetchCommand : SuspendingCliktCommand(name = "fetch") {
    override fun help(context: Context): String =
        "Re-download the valid-guess list and forward-collect daily solutions."

    override suspend fun run() {
        val repoRoot = RepoRoot.resolve()
        val today = LocalDate.now(ZoneId.of("America/Los_Angeles"))
        println("Wordle word lists, refreshed $today (America/Los_Angeles):\n")

        val summary = try {
            refreshAll(repoRoot)
        } catch (e: WordleRefreshError) {
            fail("${e.label()}: ${e.message}\n  Hint: ${e.hint}")
        } catch (e: Exception) {
            fail(
                "unexpected error: ${e.message}\n  Hint: " +
                    "set WORDLE_STALE_OK=1 to proceed on stale data anyway."
            )
        }

        val g = summary.guesses
        val a = summary.answers
        println(
            "  valid guesses: %,d words (+%d added, -%d removed)".format(
                Locale.US, g.count, g.added.size, g.removed.size)
        )
        if (g.added.isNotEmpty()) {
            println(
                "    added: ${g.added.take(10).joinToString(", ")}" +
                    if (g.added.size > 10) "..." else ""
            )
        }
        if (g.removed.isNotEmpty()) {
            println(
                "    removed: ${g.removed.take(10).joinToString(", ")}" +
                    if (g.removed.size > 10) "..." else ""
            )
        }
        println(
            "  valid answers: %,d words (+%d newly observed, %d days checked)".format(
                Locale.US, a.count, a.added.size, a.checked)
        )
        for ((word, date) in a.added.take(20)) {
            println("    + $word (first seen $date)")
        }
        if (a.added.size > 20) {
            println("    ... and ${a.added.size - 20} more")
        }

        if (!summary.changed) {
            println("\n  lists unchanged; files left as-is (freshness clock reset).")
        } else {
            println("\n  updated: word lists changed -- consider committing.")
        }
    }

    private fun fail(msg: String): Nothing {
        System.err.println("  ERROR: $msg")
        System.err.println("  Keeping existing word lists unchanged.")
        exitProcess(1)
    }
}
