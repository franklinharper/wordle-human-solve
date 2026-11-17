package com.franklinharper.wordle.deck

internal data class DoublesCard(
    val role: String,
    val answer: String,
    val guesses: List<String>,
    val headline: String,
    val bystander: String? = null,
)

internal fun DeckBuild.buildDoubles() {
    // -------------------------------------------------------
    // 5. Doubles: the before-Y rule and five boards.
    //
    // Board rules, all asserted below (Frank's grill,
    // 2026-11-13): the line is on the rails — guess 1 is
    // RAISE and guess 2 is the table word for its pattern
    // (the rails cover guesses 1-2 only; later guesses are
    // free); a CCY drill board's consistent set is entirely
    // CCY — the board itself forces the shape, so the drill
    // never argues against the fresh-letters principle the
    // way the old mixed boards did — and no guess in the
    // line lands a green at position 3 or 4, so the doubled
    // consonant is the player's own move, never half-given
    // by the board (the old CANNY board's TANGY pinned its
    // first N green). The back's family is derived, not
    // listed: the board's computed candidate set minus the
    // answer, alphabetically.
    //
    // A card may also name a bystander (Frank, 2026-11-16):
    // a playable word that fits the board and retires
    // several fresh letters, yet is a poor guess because
    // none of its fresh letters can be the double — it
    // scores the same against every candidate, so it
    // splits nothing and cannot solve. Every clause of
    // that claim is asserted below, so the note cannot
    // drift from the board it sits on.
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
            bystander = "lacky",
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

    for ((role, answer, guesses, headline, bystander)
        in doublesCards) {
        validateLine(role, answer, guesses)
        val tableWord = table[feedbackString("raise", answer)]
        if (guesses.size < 2 || guesses[1] != tableWord) {
            fail(
                "error: $role: guess 2 is " +
                    (guesses.getOrNull(1)?.uppercase() ?: "missing") +
                    ", but the rails play the table word " +
                    (tableWord?.uppercase() ?: "(pattern untabled)") +
                    " after RAISE on this board"
            )
        }
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
        var back = bodyDiv(cardText)
        if (bystander != null) {
            if (bystander !in allGuesses) {
                fail(
                    "error: $role: bystander " +
                        "${bystander.uppercase()} is not a " +
                        "valid guess"
                )
            }
            if (!guesses.all {
                    feedbackString(it, bystander) ==
                        feedbackString(it, answer)
                }
            ) {
                fail(
                    "error: $role: bystander " +
                        "${bystander.uppercase()} does not " +
                        "fit the board"
                )
            }
            if (bystander in candidates) {
                fail(
                    "error: $role: bystander " +
                        "${bystander.uppercase()} is in the " +
                        "board's candidate set -- it could " +
                        "be the answer"
                )
            }
            if (candidates.map {
                    feedbackString(bystander, it)
                }.distinct().size != 1
            ) {
                fail(
                    "error: $role: bystander " +
                        "${bystander.uppercase()} does not " +
                        "score the same against every " +
                        "candidate -- it does split the family"
                )
            }
            val boardLetters = guesses.flatMap { it.toList() }
                .toSet()
            val fresh = bystander.toList().distinct()
                .filter { it !in boardLetters }
            val doubles = candidates.map { it[2] }.toSet()
            if (fresh.size < 2 || fresh.any { it in doubles }) {
                fail(
                    "error: $role: bystander " +
                        "${bystander.uppercase()}: fresh " +
                        "letters ${fresh} -- the note needs " +
                        "several fresh letters, none of them " +
                        "a candidate double $doubles"
                )
            }
            val freshText = fresh.dropLast(1)
                .joinToString(", ") { it.uppercase().toString() } +
                " and " + fresh.last().uppercase()
            val candidateText = candidates.sorted().dropLast(1)
                .joinToString(", ") { it.uppercase() } +
                " and " + candidates.sorted().last().uppercase()
            back += bodyDiv(
                "${bystander.uppercase()} fits &mdash; " +
                    "$freshText are all fresh &mdash; but " +
                    "none can be the double. It scores the " +
                    "same against $candidateText, so it " +
                    "splits nothing and cannot solve. " +
                    "Guess a double."
            )
        }
        add(
            role,
            boardFront(answer, guesses, "What's the next guess?"),
            wrap(back),
        )
    }
}
