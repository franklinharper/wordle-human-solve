package com.franklinharper.wordle.deck

internal data class DoublesCard(
    val role: String,
    val answer: String,
    val guesses: List<String>,
    val headline: String,
    // Guess-list words that fit the board without being CCY,
    // declared per board: each must be an obscurity, a proper
    // noun or a nonstandard spelling -- never a plausible word.
    // The set must match the board's computed non-CCY guess-list
    // fits exactly, in both directions (asserted below).
    val obscureGuessFits: Set<String> = emptySet(),
    // BATTY only (Frank's pick, 2026-11-17): guess 3 is PATTY,
    // itself a CCY candidate, and it lands the TT green. That
    // is the price of killing MALTY, the one plausible
    // mixed-pair word the two-guess board admitted over the
    // guess list; with PATTY played, the board's guess-list
    // fits are exactly _ATTY and no obscure fits remain.
    val allowGreenPair: Boolean = false,
)

internal fun DeckBuild.buildDoubles() {
    // -------------------------------------------------------
    // 5. Doubles: the before-Y rule and four boards.
    //
    // Board rules, all asserted below (Frank's grill,
    // 2026-11-13): the line is on the rails — guess 1 is
    // RAISE and guess 2 is the table word for its pattern
    // (the rails cover guesses 1-2 only; later guesses are
    // free); a CCY drill board's consistent set is entirely
    // CCY — over the candidate pool outright, and over the
    // full guess list up to the board's declared obscure
    // fits (Frank's CCY-purity rule, 2026-11-16, checked in
    // the strong sense since 2026-11-17) — so the board
    // itself forces the shape, and the drill never argues
    // against the fresh-letters principle the way the old
    // mixed boards did — and no guess in the line lands a
    // green at position 3 or 4, so the doubled consonant is
    // the player's own move, never half-given by the board
    // (the old CANNY board's TANGY pinned its first N
    // green). One exception, BATTY: see allowGreenPair on
    // DoublesCard. The back's family is derived, not
    // listed: the board's computed candidate set minus the
    // answer, alphabetically.
    //
    // The fifth board (HAPPY) left the family on
    // 2026-11-16: over the pool its completions are all
    // doubles, but its best play is CAMPY, a mixed pair
    // that can itself be the answer — so the board now
    // teaches the pair-frame play instead (PairFrameDeck).
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
            obscureGuessFits = setOf("tauty"),
        ),
        DoublesCard(
            "doubles:bunny", "bunny",
            listOf("raise", "cloth", "bumpy"),
            "Double the N:",
            obscureGuessFits = setOf("bundy", "bungy", "bunjy"),
        ),
        DoublesCard(
            "doubles:batty", "batty",
            listOf("raise", "tangy", "patty"),
            "Double the T:",
            allowGreenPair = true,
        ),
        DoublesCard(
            "doubles:giddy", "giddy",
            listOf("raise", "pilot", "kinky"),
            "Double the D:",
            obscureGuessFits = setOf("midgy", "vichy"),
        ),
    )

    for ((role, answer, guesses, headline, obscureGuessFits,
        allowGreenPair) in doublesCards) {
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
            if (!allowGreenPair &&
                (pattern[2] == '2' || pattern[3] == '2')
            ) {
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
        val guessFits = allGuesses.filter { w ->
            guesses.all {
                feedbackString(it, w) == feedbackString(it, answer)
            }
        }.toSet()
        val nonCcyGuessFits =
            guessFits.filter { !isCcy(it) }.toSet()
        if (nonCcyGuessFits != obscureGuessFits) {
            fail(
                "error: $role: board's non-CCY guess-list fits " +
                    "are " +
                    pyList(nonCcyGuessFits.sorted()
                        .map { it.uppercase() }) +
                    " but the declared obscure fits are " +
                    pyList(obscureGuessFits.sorted()
                        .map { it.uppercase() }) +
                    " -- an undeclared fit breaks CCY purity " +
                    "(a plausible mixed-pair word must be " +
                    "killed by the line, never declared), and " +
                    "a declared fit that no longer fits is " +
                    "cruft"
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
