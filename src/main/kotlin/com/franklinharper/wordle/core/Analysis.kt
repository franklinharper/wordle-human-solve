package com.franklinharper.wordle.core

import kotlin.math.log2

/** Partition candidates by the feedback pattern [guess] produces. */
fun partitionByFeedback(
    guess: Word,
    candidates: List<Word>,
): Map<Feedback, List<Word>> {
    val buckets = LinkedHashMap<Feedback, MutableList<Word>>()
    for (target in candidates) {
        buckets.getOrPut(computeFeedback(guess, target)) { mutableListOf() }
            .add(target)
    }
    return buckets
}

/** Expected information gain (Shannon entropy, bits) of a guess. Higher = better. */
fun expectedInformation(guess: Word, candidates: List<Word>): Double {
    val n = candidates.size
    if (n <= 1) return 0.0
    var entropy = 0.0
    for (bucket in partitionByFeedback(guess, candidates).values) {
        val p = bucket.size.toDouble() / n
        if (p > 0) entropy -= p * log2(p)
    }
    return entropy
}

/** Expected number of remaining candidates after the guess. Lower = better. */
fun expectedRemaining(guess: Word, candidates: List<Word>): Double {
    val n = candidates.size
    if (n <= 1) return 0.0
    val buckets = partitionByFeedback(guess, candidates)
    return buckets.values.sumOf { it.size.toDouble() * it.size } / n
}

/** Worst-case (largest) bucket size after the guess. */
fun worstCaseRemaining(guess: Word, candidates: List<Word>): Int =
    partitionByFeedback(guess, candidates).values.maxOf { it.size }

/** Letter frequency: each letter counted once per word containing it. */
fun letterFrequency(words: List<Word>): Map<Char, Int> {
    val counts = LinkedHashMap<Char, Int>()
    for (word in words) {
        for (ch in word.value.toSet()) {
            counts[ch] = (counts[ch] ?: 0) + 1
        }
    }
    return counts
}

/** Letter frequency at each position (0..4). */
fun positionalLetterFrequency(words: List<Word>): List<Map<Char, Int>> {
    val positions = List(5) { LinkedHashMap<Char, Int>() }
    for (word in words) {
        for (i in 0..4) {
            val counts = positions[i]
            counts[word[i]] = (counts[word[i]] ?: 0) + 1
        }
    }
    return positions
}

/**
 * Score a word by how close its unique letters are to 50% frequency.
 * The 50% principle: a letter appearing in 50% of candidates gives
 * maximum information (1 bit per letter); deviation is penalized.
 * Duplicate letters in the guess are wasteful and counted once.
 */
fun scoreWordByFrequency(word: Word, freq: Map<Char, Int>, nWords: Int): Double {
    var score = 0.0
    val seen = HashSet<Char>()
    for (ch in word.value) {
        if (!seen.add(ch)) continue
        val p = (freq[ch] ?: 0).toDouble() / nWords
        if (p > 0.0 && p < 1.0) {
            score += -p * log2(p) - (1 - p) * log2(1 - p)
        }
    }
    return score
}

/** Score a word using position-specific letter frequencies. */
fun scoreWordPositional(
    word: Word,
    posFreq: List<Map<Char, Int>>,
    nWords: Int,
): Double {
    var score = 0.0
    for (i in 0..4) {
        val p = (posFreq[i][word[i]] ?: 0).toDouble() / nWords
        if (p > 0.0 && p < 1.0) {
            score += -p * log2(p) - (1 - p) * log2(1 - p)
        }
    }
    return score
}

/**
 * Candidates consistent with the observed feedback for [guess] —
 * the hard-mode filter: only words that could still be the answer.
 */
fun filterCandidates(
    candidates: List<Word>,
    guess: Word,
    feedback: Feedback,
): List<Word> = candidates.filter { computeFeedback(guess, it) == feedback }

data class OpeningRank(
    val word: Word,
    val info: Double,
    val expectedRemaining: Double,
    val worstCase: Int,
)

/** Rank words by expected information gain as an opening guess. */
fun rankOpeningWords(
    answers: List<Word>,
    topN: Int = 20,
    guessPool: List<Word> = answers,
    onProgress: ((done: Int, total: Int) -> Unit)? = null,
): List<OpeningRank> {
    val results = ArrayList<OpeningRank>(guessPool.size)
    for ((i, word) in guessPool.withIndex()) {
        if (onProgress != null && (i + 1) % 500 == 0) {
            onProgress(i + 1, guessPool.size)
        }
        results.add(
            OpeningRank(
                word,
                expectedInformation(word, answers),
                expectedRemaining(word, answers),
                worstCaseRemaining(word, answers),
            )
        )
    }
    results.sortByDescending { it.info }
    return results.take(topN)
}
