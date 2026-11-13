package com.franklinharper.wordle.deck

internal data class DoublesCard(
    val role: String,
    val answer: String,
    val guesses: List<String>,
    val headline: String,
    val family: List<String>,
    val others: List<String>,
)

internal fun DeckBuild.buildDoubles() {
    // -------------------------------------------------------
    // 5. Doubles: the before-Y rule and four boards.
    //
    // Each board's answer doubles its consonant at positions
    // 3-4 before the Y — asserted below. Each back names every
    // word consistent with its board: the doubling family
    // first, then the rest — asserted against the board's
    // computed candidate set.
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
            "doubles:canny", "canny", listOf("raise", "tangy"),
            "Extend the N into 4:",
            listOf("fanny", "nanny"),
            listOf("candy", "dandy", "fancy", "handy", "lanky", "manly"),
        ),
        DoublesCard(
            "doubles:tally", "tally",
            listOf("raise", "tangy", "tacky"),
            "Double the L:",
            listOf("tabby", "taffy", "tatty"),
            emptyList(),
        ),
        DoublesCard(
            "doubles:happy", "happy",
            listOf("raise", "tangy", "wacky"),
            "Double the P:",
            listOf("daddy", "dally", "jazzy", "mammy", "paddy"),
            listOf("badly", "balmy", "madly"),
        ),
    )

    for ((role, answer, guesses, headline, family, others)
        in doublesCards) {
        validateLine(role, answer, guesses)
        if (!isCcy(answer)) {
            fail(
                "error: $role: ${answer.uppercase()} is not a " +
                    "_ _ CCY word"
            )
        }
        for (w in family) {
            if (!isCcy(w)) {
                fail(
                    "error: $role: family word ${w.uppercase()} " +
                        "is not a _ _ CCY word"
                )
            }
        }
        for (w in others) {
            if (isCcy(w)) {
                fail(
                    "error: $role: ${w.uppercase()} doubles its " +
                        "consonant -- it belongs in the family, " +
                        "not the others"
                )
            }
        }
        val candidates = pool.filter { w ->
            guesses.all {
                feedbackString(it, w) == feedbackString(it, answer)
            }
        }.toSet()
        val named = setOf(answer) + family + others
        if (candidates != named) {
            fail(
                "error: $role: board's candidate set is " +
                    pyList(candidates.sorted().map { it.uppercase() }) +
                    " but the back names " +
                    pyList(named.sorted().map { it.uppercase() })
            )
        }
        var cardText = "$headline <b>${answer.uppercase()}</b>"
        cardText += if (family.isNotEmpty()) {
            " &mdash; also " +
                family.joinToString(", ") { it.uppercase() } + "."
        } else {
            "."
        }
        if (others.isNotEmpty()) {
            cardText += " Also consistent: " +
                others.joinToString(", ") { it.uppercase() } + "."
        }
        add(
            role,
            boardFront(answer, guesses, "What's the next guess?"),
            wrap(bodyDiv(cardText)),
        )
    }
}
