package com.franklinharper.wordle

import com.franklinharper.wordle.core.PositionalPattern
import com.franklinharper.wordle.core.RepoRoot
import com.franklinharper.wordle.core.Word
import com.franklinharper.wordle.core.loadWordLists
import com.franklinharper.wordle.core.matchPattern
import com.franklinharper.wordle.core.positionalBigramCounts
import com.github.ajalt.clikt.command.SuspendingCliktCommand
import com.github.ajalt.clikt.core.Context
import com.github.ajalt.clikt.parameters.arguments.argument
import com.github.ajalt.clikt.parameters.arguments.multiple
import com.github.ajalt.clikt.parameters.options.flag
import com.github.ajalt.clikt.parameters.options.option
import java.util.Locale

/**
 * Positional pattern analysis (port of patterns.py): counts and
 * examples over both the answer list and the valid-guess list.
 */
class PatternsCommand : SuspendingCliktCommand(name = "patterns") {
    override fun help(context: Context): String =
        "Count answers/guesses matching positional patterns " +
            "(5 chars, '_' = wildcard), or --top-bigrams."

    private val patterns by argument(
        "PATTERN", help = "Positional patterns, e.g. ___er or __re_."
    ).multiple()
    private val topBigrams by option(
        "--top-bigrams", help = "Show the most common 2-letter combos per position."
    ).flag()

    override suspend fun run() {
        val repoRoot = RepoRoot.resolve()
        Freshness.ensureFresh(repoRoot)
        val lists = loadWordLists(repoRoot)
        when {
            topBigrams -> {
                println("=== MOST COMMON 2-LETTER COMBOS BY POSITION: ANSWERS ===")
                printTopBigrams(lists.answers)
                println()
                println("=== MOST COMMON 2-LETTER COMBOS BY POSITION: VALID GUESSES ===")
                printTopBigrams(lists.guesses)
            }
            patterns.isNotEmpty() -> report(patterns)
            else -> report(listOf("___er", "__re_"))
        }
    }

    private fun report(rawPatterns: List<String>, showExamples: Int = 6) {
        val lists = loadWordLists(RepoRoot.resolve())
        val answers = lists.answers
        val guesses = lists.guesses
        val na = answers.size
        val ng = guesses.size
        val parsed = rawPatterns.map { it to PositionalPattern.parse(it) }
        println("Valid answers: $na words | Valid guesses: $ng words\n")
        println("  %-10s%20s%18s".format("Pattern", "Valid answers", "Valid guesses"))
        for ((raw, pat) in parsed) {
            val ma = matchPattern(answers, pat)
            val mg = matchPattern(guesses, pat)
            println(
                "  %-10s%12d (%4.1f%%)%9d (%4.1f%%)".format(
                    Locale.US, raw, ma.size, ma.size.toDouble() / na * 100,
                    mg.size, mg.size.toDouble() / ng * 100,
                )
            )
        }
        println()
        for ((raw, pat) in parsed) {
            val ma = matchPattern(answers, pat)
            val mg = matchPattern(guesses, pat)
            var ea = ma.take(showExamples).joinToString(", ") { it.value }
            var eg = mg.take(showExamples).joinToString(", ") { it.value }
            if (ma.size > showExamples) ea += ", ..."
            if (mg.size > showExamples) eg += ", ..."
            println("  $raw valid answers: $ea")
            println("  $raw valid guesses: $eg")
        }
    }

    private fun printTopBigrams(words: List<Word>, topN: Int = 10) {
        val counts = positionalBigramCounts(words)
        for (i in 0..3) {
            val pairs = counts.entries
                .filter { it.key.first == i }
                .sortedByDescending { it.value }
                .take(topN)
            val cells = pairs.joinToString("  ") { "${it.key.second}:${it.value}" }
            println("  Positions ${i + 1}-${i + 2}: $cells")
        }
    }
}
