package com.franklinharper.wordle

import com.franklinharper.wordle.core.RepoRoot
import com.franklinharper.wordle.core.letterFrequency
import com.franklinharper.wordle.core.loadAnswers
import com.franklinharper.wordle.core.positionalLetterFrequency
import com.franklinharper.wordle.core.rankOpeningWords
import com.github.ajalt.clikt.command.SuspendingCliktCommand
import com.github.ajalt.clikt.core.Context
import java.util.Locale
import kotlin.math.abs
import kotlin.math.log2

/**
 * The analysis.py main report: letter frequencies, the 50%
 * principle, and the top opening words by expected information.
 */
class AnalysisCommand : SuspendingCliktCommand(name = "analysis") {
    override fun help(context: Context): String =
        "Letter-frequency report and top opening words over the answer list."

    override suspend fun run() {
        val repoRoot = RepoRoot.resolve()
        Freshness.ensureFresh(repoRoot)
        val answers = loadAnswers(repoRoot)
        val n = answers.size
        println("Answer list: $n words")
        println("Theoretical minimum info needed: %.2f bits".format(Locale.US, log2(n.toDouble())))
        println("Max info per guess: %.2f bits".format(Locale.US, log2(243.0)))
        println()

        val freq = letterFrequency(answers)
        val posFreq = positionalLetterFrequency(answers)
        val byCount = freq.entries.sortedByDescending { it.value }

        println("=== LETTER FREQUENCY (% of answer words containing each letter) ===")
        for ((ch, count) in byCount) {
            val pct = count.toDouble() / n * 100
            val bar = "█".repeat((pct / 2).toInt())
            println("  %s: %5.1f%% (%4d) %s".format(Locale.US, ch, pct, count, bar))
        }
        println()

        println("=== POSITIONAL FREQUENCY (top 5 letters per position) ===")
        for (i in 0..4) {
            val top5 = posFreq[i].entries
                .sortedByDescending { it.value }
                .take(5)
            val parts = top5.joinToString(", ") { (ch, count) ->
                "%s:%.0f%%".format(Locale.US, ch, count.toDouble() / n * 100)
            }
            println("  Position ${i + 1}: $parts")
        }
        println()

        println("=== 50% PRINCIPLE: Letters closest to 50% frequency ===")
        println("  (These give maximum information per letter test)")
        val byDistance = freq.entries
            .sortedBy { abs(it.value.toDouble() / n - 0.5) }
        for ((ch, count) in byDistance.take(10)) {
            println("  %s: %.1f%%".format(Locale.US, ch, count.toDouble() / n * 100))
        }
        println()

        println("=== TOP OPENING WORDS (by expected information, answer-list only) ===")
        println("  Computing... (evaluating all $n answer words)")
        val top = rankOpeningWords(answers, topN = 25) { done, total ->
            println("  Evaluated $done/$total...")
        }
        println("  %-8s %11s %13s %11s".format("Word", "Info (bits)", "E[remaining]", "Worst case"))
        for (rank in top) {
            println(
                "  %-8s %11.4f %13.2f %11d".format(
                    Locale.US, rank.word, rank.info,
                    rank.expectedRemaining, rank.worstCase,
                )
            )
        }
    }
}
