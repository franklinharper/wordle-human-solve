package com.franklinharper.wordle.deck

import com.franklinharper.wordle.core.Word
import com.franklinharper.wordle.core.computeFeedback

/** Feedback digits (0 gray, 1 yellow, 2 green) for a guess against an answer. */
fun feedbackDigits(guess: String, answer: String): List<Int> =
    computeFeedback(Word(guess), Word(answer)).tiles.map { it.digit }

/** Feedback as a digit string, e.g. "01000". */
fun feedbackString(guess: String, answer: String): String =
    feedbackDigits(guess, answer).joinToString("")

/**
 * The hard-mode knowledge state after playing guesses at the
 * answer: what the board has established, in one named bundle.
 */
data class KnowledgeState(
    /** position -> letter pinned green there */
    val greens: Map<Int, Char>,
    /** letter -> at least this many copies */
    val minCounts: Map<Char, Int>,
    /** letter -> exactly this many copies */
    val caps: Map<Char, Int>,
    /** letters known not to be in the word */
    val absent: Set<Char>,
    /** letter -> positions it cannot occupy */
    val yellowForbidden: Map<Char, Set<Int>>,
)

fun knowledge(answer: String, guesses: List<String>): KnowledgeState {
    val greens = mutableMapOf<Int, Char>()
    val minCounts = mutableMapOf<Char, Int>()
    val caps = mutableMapOf<Char, Int>()
    val yellowForbidden = mutableMapOf<Char, MutableSet<Int>>()
    for (guess in guesses) {
        val result = feedbackDigits(guess, answer)
        val guessCounts = guess.groupingBy { it }.eachCount()
        val coloredCounts = mutableMapOf<Char, Int>()
        for (i in 0..4) {
            val ch = guess[i]
            when (result[i]) {
                2 -> {
                    greens[i] = ch
                    coloredCounts[ch] = (coloredCounts[ch] ?: 0) + 1
                }
                1 -> {
                    coloredCounts[ch] = (coloredCounts[ch] ?: 0) + 1
                    yellowForbidden.getOrPut(ch) { mutableSetOf() }.add(i)
                }
            }
        }
        for (ch in guessCounts.keys) {
            minCounts[ch] = maxOf(minCounts[ch] ?: 0, coloredCounts[ch] ?: 0)
            if ((coloredCounts[ch] ?: 0) < guessCounts.getValue(ch)) {
                caps[ch] = coloredCounts[ch] ?: 0
            }
        }
    }
    val absent = caps.filterValues { it == 0 }.keys
    for (ch in caps.keys) {
        minCounts[ch] = caps.getValue(ch)
    }
    return KnowledgeState(
        greens, minCounts, caps, absent,
        yellowForbidden.mapValues { it.value.toSet() },
    )
}

/**
 * Is [word] a legal hard-mode guess given the knowledge state?
 * Greens pinned, known-present letters included (and never where
 * they showed yellow), absent letters never replayed, exact
 * counts respected.
 */
fun legal(word: String, state: KnowledgeState): Boolean {
    val wordCounts = word.groupingBy { it }.eachCount()
    for ((pos, ch) in state.greens) {
        if (word[pos] != ch) return false
    }
    for (ch in state.absent) {
        if ((wordCounts[ch] ?: 0) > 0) return false
    }
    for ((ch, minimum) in state.minCounts) {
        if ((wordCounts[ch] ?: 0) < minimum) return false
    }
    for ((ch, cap) in state.caps) {
        if ((wordCounts[ch] ?: 0) > cap) return false
    }
    for ((ch, positions) in state.yellowForbidden) {
        for (pos in positions) {
            if (word[pos] == ch && state.greens[pos] != ch) return false
        }
    }
    return true
}
