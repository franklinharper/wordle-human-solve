package com.franklinharper.wordle.deck

internal fun DeckBuild.buildTable() {
    // -------------------------------------------------------
    // 3. The guess-2 lookup table.

    for ((pattern, word, letters) in tableRows) {
        if (word !in answers) {
            fail("error: table word '$word' is not an answer")
        }
        if (answers.none { feedbackString("raise", it) == pattern }) {
            fail("error: no answer gives RAISE pattern $pattern")
        }
        val front = wrap(
            """<div style="margin: 6px 0;">""" +
                tileRow("raise", pattern.map { it.digitToInt() }) +
                "</div>" +
                bodyDiv("What's the next guess?")
        )
        val back = wrap(
            bodyDiv("<b>${word.uppercase()}</b>") +
                promptDiv("Tests $letters")
        )
        add("guess2:$pattern", front, back)
    }
}
