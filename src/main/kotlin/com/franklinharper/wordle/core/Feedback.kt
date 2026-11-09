package com.franklinharper.wordle.core

/** One tile of Wordle feedback. [digit] is the 0/1/2 encoding. */
enum class Tile(val digit: Int) {
    GRAY(0),
    YELLOW(1),
    GREEN(2);

    companion object {
        fun fromDigit(digit: Int): Tile = entries.first { it.digit == digit }
    }
}

/**
 * The feedback for one guess: five tiles, held as a base-3 code
 * (0..242) so equality and map keys are exact. [digits] is the
 * familiar string form, e.g. "10120".
 */
@JvmInline
value class Feedback(val code: Int) {
    init {
        require(code in 0..242) { "feedback code out of range: $code" }
    }

    val tiles: List<Tile>
        get() = digits.map { Tile.fromDigit(it.digitToInt()) }

    val digits: String
        get() {
            val chars = CharArray(5)
            var rest = code
            for (i in 4 downTo 0) {
                chars[i] = '0' + (rest % 3)
                rest /= 3
            }
            return String(chars)
        }

    fun emoji(): String = tiles.joinToString("") {
        when (it) {
            Tile.GRAY -> "⬛"
            Tile.YELLOW -> "🟨"
            Tile.GREEN -> "🟩"
        }
    }

    override fun toString(): String = digits

    companion object {
        fun of(tiles: List<Tile>): Feedback {
            require(tiles.size == 5) { "feedback needs 5 tiles" }
            var code = 0
            for (tile in tiles) code = code * 3 + tile.digit
            return Feedback(code)
        }

        fun parse(digits: String): Feedback {
            require(digits.length == 5 && digits.all { it in '0'..'2' }) {
                "feedback must be 5 digits of 0/1/2: '$digits'"
            }
            return of(digits.map { Tile.fromDigit(it.digitToInt()) })
        }
    }
}

/**
 * Wordle feedback for [guess] against [target], with duplicate
 * letters handled the Wordle way: greens consume their target
 * letters first, then yellows consume what remains, left to right.
 */
fun computeFeedback(guess: Word, target: Word): Feedback {
    val tiles = MutableList(5) { Tile.GRAY }
    val remaining = IntArray(26)
    for (i in 0..4) {
        if (guess[i] == target[i]) {
            tiles[i] = Tile.GREEN
        } else {
            remaining[target[i] - 'a']++
        }
    }
    for (i in 0..4) {
        if (tiles[i] == Tile.GREEN) continue
        val letter = guess[i] - 'a'
        if (remaining[letter] > 0) {
            tiles[i] = Tile.YELLOW
            remaining[letter]--
        }
    }
    return Feedback.of(tiles)
}
