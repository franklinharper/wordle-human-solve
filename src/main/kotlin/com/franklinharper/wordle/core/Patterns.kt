package com.franklinharper.wordle.core

/** A positional pattern: five characters, '_' wildcards, letters fixed. */
@JvmInline
value class PositionalPattern(val value: String) {
    init {
        require(
            value.length == 5 &&
                value.all { it == '_' || it in 'a'..'z' }
        ) { "Pattern must be 5 chars of letters/_: '$value'" }
    }

    override fun toString(): String = value

    companion object {
        fun parse(raw: String): PositionalPattern =
            PositionalPattern(raw.lowercase())
    }
}

/** Words matching a 5-char positional pattern ('_' = wildcard). */
fun matchPattern(
    words: List<Word>,
    pattern: PositionalPattern,
): List<Word> = words.filter { word ->
    pattern.value.indices.all { i ->
        pattern.value[i] == '_' || word[i] == pattern.value[i]
    }
}

/**
 * Count every 2-letter combo at each adjacent position pair.
 * Keys are (start position 0-based, bigram); iteration order is
 * first-occurrence order, matching the Python Counter.
 */
fun positionalBigramCounts(
    words: List<Word>,
): Map<Pair<Int, String>, Int> {
    val counts = LinkedHashMap<Pair<Int, String>, Int>()
    for (word in words) {
        for (i in 0..3) {
            val key = i to word.value.substring(i, i + 2)
            counts[key] = (counts[key] ?: 0) + 1
        }
    }
    return counts
}
