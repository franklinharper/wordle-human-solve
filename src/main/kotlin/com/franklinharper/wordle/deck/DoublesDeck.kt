package com.franklinharper.wordle.deck

internal data class DoublesCard(
    val role: String,
    val answer: String,
    val guesses: List<String>,
    val headline: String,
)

internal fun DeckBuild.buildDoubles() {
    // -------------------------------------------------------
    // 5. Doubles: the before-Y rule and five boards.
    //
    // Two board rules, both asserted below (Frank's grill,
    // 2026-11-13): a CCY drill board's consistent set is
    // entirely CCY — the board itself forces the shape, so
    // the drill never argues against the fresh-letters
    // principle the way the old mixed boards did — and no
    // guess in the line lands a green at position 3 or 4,
    // so the doubled consonant is the player's own move,
    // never half-given by the board (the old CANNY board's
    // TANGY pinned its first N green). The back's family is
    // derived, not listed: the board's computed candidate
    // set minus the answer, alphabetically.
    add(
        "doubles:rule",
        wrap(bodyDiv("When a word ends in Y, what's the most likely shape?")),
        wrap(
            bodyDiv(
                "The consonant before the Y doubles &mdash; " +
                    "_ _ CCY. 28% of Y-ending answers " +
                    "(CANNY, TALLY, NUTTY)."
            )
        ),
    )

    fun isCcy(word: String): Boolean =
        word[2] == word[3] && word[4] == 'y' && word[2] !in "aeiou"

    val doublesCards = listOf(
        DoublesCard(
            "doubles:tally", "tally",
            listOf("raise", "tangy", "tacky"),
            "Double the L:",
        ),
        DoublesCard(
            "doubles:happy", "happy",
            listOf("raise", "tangy", "bawdy"),
            "Double the P:",
        ),
        DoublesCard(
            "doubles:bunny", "bunny",
            listOf("raise", "cloth", "bumpy"),
            "Double the N:",
        ),
        DoublesCard(
            "doubles:batty", "batty",
            listOf("raise", "tangy"),
            "Double the T:",
        ),
        DoublesCard(
            "doubles:giddy", "giddy",
            listOf("raise", "pilot", "kinky"),
            "Double the D:",
        ),
    )

    for ((role, answer, guesses, headline) in doublesCards) {
        validateLine(role, answer, guesses)
        if (!isCcy(answer)) {
            fail(
                "error: $role: ${answer.uppercase()} is not a " +
                    "_ _ CCY word"
            )
        }
        for (g in guesses) {
            val pattern = feedbackString(g, answer)
            if (pattern[2] == '2' || pattern[3] == '2') {
                fail(
                    "error: $role: ${g.uppercase()} lands a green " +
                        "at position 3 or 4 on this board " +
                        "(pattern $pattern) -- a CCY drill board " +
                        "leaves the doubled consonant to the player"
                )
            }
        }
        val candidates = pool.filter { w ->
            guesses.all {
                feedbackString(it, w) == feedbackString(it, answer)
            }
        }.toSet()
        val impure = candidates.filter { !isCcy(it) }
        if (impure.isNotEmpty()) {
            fail(
                "error: $role: board's candidate set is not " +
                    "pure CCY -- non-CCY candidates: " +
                    pyList(impure.sorted().map { it.uppercase() })
            )
        }
        val family = (candidates - answer).sorted()
        if (family.isEmpty()) {
            fail(
                "error: $role: board's candidate set is just " +
                    "${answer.uppercase()} -- a doubles board " +
                    "needs a family"
            )
        }
        val cardText = "$headline <b>${answer.uppercase()}</b>" +
            " &mdash; also " +
            family.joinToString(", ") { it.uppercase() } + "."
        add(
            role,
            boardFront(answer, guesses, "What's the next guess?"),
            wrap(bodyDiv(cardText)),
        )
    }
}
