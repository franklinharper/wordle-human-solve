package com.franklinharper.wordle.deck

internal fun DeckBuild.buildFrame() {
    // -------------------------------------------------------
    // 9. Frame drills: the chant applied to a floating yellow.
    //
    // The TRUCE board (2026-11-10, #1970): RAISE came back
    // R yellow, E green — pattern 10002, untabled (the table
    // holds R+E both yellow and E green alone, not this mix).
    // The play is derived, not memorized (Frank, 2026-11-13):
    // the yellow R must move; the chant's first chunk is
    // OTLN, so its first two letters, O and T, are the fresh
    // letters to reach for; building them with the R around
    // the green E gives TRO?E, and P completes TROPE. Frank
    // actually played CHORE and still solved in 3 — the card
    // teaches the derivation he can run from the seat. The
    // recommended guess is asserted legal on the board, an
    // answer itself, built by exactly that derivation, and
    // its feedback leaves TRUCE as the pool's only candidate.
    run {
        val role = "frame:truce"
        val answer = "truce"
        val guesses = listOf("raise")
        val recommended = "trope"
        if (answer !in pool) {
            fail("error: $role: '$answer' is not in the candidate pool")
        }
        if (feedbackString("raise", answer) != "10002") {
            fail(
                "error: $role: RAISE pattern is " +
                    feedbackString("raise", answer) + ", not 10002"
            )
        }
        if (recommended !in answers) {
            fail("error: $role: '$recommended' is not an answer")
        }
        if (!legal(recommended, knowledge(answer, guesses))) {
            fail(
                "error: $role: ${recommended.uppercase()} is not a " +
                    "legal hard-mode guess on this board"
            )
        }
        // The derivation the back teaches, asserted: the
        // recommended guess moves the yellow R off slot 1,
        // keeps the green E at slot 5, and spends its fresh
        // letters on the chant's first two, O and T.
        if (recommended[0] == 'r' || 'r' !in recommended ||
            recommended[4] != 'e' ||
            chant[0].lowercaseChar() !in recommended ||
            chant[1].lowercaseChar() !in recommended
        ) {
            fail(
                "error: $role: ${recommended.uppercase()} is not " +
                    "the chant derivation (moved R, chant head " +
                    "${chant[0]} and ${chant[1]}, green E at 5)"
            )
        }
        val line = guesses + recommended
        val candidates = pool.filter { w ->
            line.all {
                feedbackString(it, w) == feedbackString(it, answer)
            }
        }.toSet()
        if (candidates != setOf(answer)) {
            fail(
                "error: $role: RAISE + ${recommended.uppercase()} " +
                    "leaves " +
                    pyList(candidates.sorted().map { it.uppercase() }) +
                    ", not just ${answer.uppercase()}"
            )
        }
        add(
            role,
            boardFront(answer, guesses, "What's the next guess?"),
            wrap(
                bodyDiv("<b>${recommended.uppercase()}</b>") +
                    promptDiv(
                        "R must move &mdash; take the chant's head, " +
                            "O and T, and build round the green E: " +
                            "TRO?E. P completes it."
                    )
            ),
        )
    }
}
