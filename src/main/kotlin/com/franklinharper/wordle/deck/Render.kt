package com.franklinharper.wordle.deck

/**
 * Card HTML rendering. Every string here matches the Python
 * generator's output byte-for-byte; the feedback colours are
 * always computed from the card's answer, never typed by hand.
 */

// The blank that stands in for a missing word or chunk, and the
// separator between chunks. Shared by card fronts and backs so
// the two sides can never drift apart.
const val BLANK = "________"
const val SEPARATOR = " – "

fun wrap(inner: String): String =
    """<div style="text-align: center;">$inner</div>"""

fun promptDiv(text: String): String =
    """<div style="font-size: 16px; color: #555; margin-bottom: 6px;">$text</div>"""

fun bodyDiv(html: String): String =
    """<div style="font-size: 20px; margin: 4px 0;">$html</div>"""

// Wordle's own tile colours, by feedback digit.
private val TILE_COLORS = mapOf(2 to "#6aaa64", 1 to "#c9b458", 0 to "#787c7e")

fun tileRow(word: String, pattern: List<Int>): String {
    val tiles = StringBuilder()
    for (i in word.indices) {
        val ch = word[i]
        val v = pattern[i]
        tiles.append(
            """<span style="display: inline-block; width: 32px; height: 32px; line-height: 32px; text-align: center; background: ${TILE_COLORS[v]}; color: #ffffff; font-weight: bold; font-size: 19px; margin: 1px; border-radius: 3px;">${ch.uppercaseChar()}</span>"""
        )
    }
    return tiles.toString()
}

/** The board for a line of guesses against answer, as tile rows. */
fun board(answer: String, guesses: List<String>): String {
    val rows = guesses.joinToString("<br>") { g ->
        tileRow(g, feedbackDigits(g, answer))
    }
    return """<div style="margin: 6px 0;">$rows</div>"""
}

// The keyboard under every board: the three QWERTY rows as the
// real game draws them, ENTER and backspace included as inert
// keys. Each letter key takes the best state the board gives it
// (green beats yellow beats dead); a letter the board never
// tested keeps the game's light gray for unexplored keys.
private val KEYBOARD_ROWS = listOf("qwertyuiop", "asdfghjkl", "zxcvbnm")

// Wordle's own unexplored-key gray.
private const val KEY_NEUTRAL = "#d3d6da"

// The near-black text on unexplored (light) keys; tested keys
// take white text on their tile colour instead.
private const val KEY_TEXT_DARK = "#1a1a1b"

// Key widths in px: a letter key is one unit wide, and the
// ENTER and ⌫ keys are double that.
private const val KEY_WIDTH = 24
private const val KEY_WIDE_WIDTH = 48

private fun keySpan(label: String, background: String, color: String, width: Int): String =
    """<span style="display: inline-block; width: ${width}px; height: 30px; line-height: 30px; text-align: center; background: $background; color: $color; font-weight: bold; font-size: 13px; margin: 1px; border-radius: 3px;">$label</span>"""

fun keyboard(answer: String, guesses: List<String>): String {
    val best = mutableMapOf<Char, Int>()
    for (g in guesses) {
        val pattern = feedbackDigits(g, answer)
        for (i in g.indices) {
            val ch = g[i]
            val v = pattern[i]
            if (v > (best[ch] ?: -1)) best[ch] = v
        }
    }
    val rows = KEYBOARD_ROWS.map { rowLetters ->
        val keys = StringBuilder()
        if (rowLetters == "zxcvbnm") {
            keys.append(keySpan("ENTER", KEY_NEUTRAL, KEY_TEXT_DARK, KEY_WIDE_WIDTH))
        }
        for (ch in rowLetters) {
            val v = best[ch]
            val bg = if (v == null) KEY_NEUTRAL else TILE_COLORS.getValue(v)
            val color = if (v == null) KEY_TEXT_DARK else "#ffffff"
            keys.append(keySpan(ch.uppercase(), bg, color, KEY_WIDTH))
        }
        if (rowLetters == "zxcvbnm") {
            keys.append(keySpan("⌫", KEY_NEUTRAL, KEY_TEXT_DARK, KEY_WIDE_WIDTH))
        }
        keys.toString()
    }
    return """<div style="margin: 6px 0;">${rows.joinToString("<br>")}</div>"""
}

fun boardFront(answer: String, guesses: List<String>, question: String): String =
    // No front in the deck carries a header (Frank's rule, settled
    // 2026-11-06/07): a header either gives away what the card
    // tests or duplicates the question, and anything worth saying
    // belongs in the question itself.
    wrap(board(answer, guesses) + keyboard(answer, guesses) + bodyDiv(question))
