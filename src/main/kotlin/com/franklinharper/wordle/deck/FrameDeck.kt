package com.franklinharper.wordle.deck

internal fun DeckBuild.buildFrame() {
    // -------------------------------------------------------
    // 10. Frame drills: the chant applied to a floating yellow.
    //
    // The TRUCE board (2026-11-10, #1970): RAISE came back
    // R yellow, E green — pattern 10002, untabled (the table
    // holds R+E both yellow and E green alone, not this mix).
    // The play is derived, not memorized (Frank, 2026-11-13):
    // the yellow R must move; the chant's first two untested
    // letters are O and T (RAISE's five sit in the chant but
    // are already tested here), so those are the fresh
    // letters to reach for; building them with the R around
    // the green E gives TRO?E, and P completes TROPE. Frank
    // actually played CHORE and still solved in 3 — the card
    // teaches the derivation he can run from the seat. The
    // recommended guess is asserted legal on the board, an
    // answer itself, and built by exactly that derivation:
    // R moved, the chant's head O and T around the green E,
    // and slot 4 filled by running the chant down to the
    // first letter that completes a recognisable word. The
    // card is NOT gated on what the board leaves behind —
    // from the seat you never know how many candidates
    // remain (Frank's rule; review F2, 2026-11-14).
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
        // letters on the chant's first two untested letters,
        // O and T — the head of the chant as a hunt reads
        // it, RAISE's already-tested letters skipped (F3
        // grill Q3, 2026-11-20).
        val tested = guesses.joinToString("").toSet()
        val untested = chant.filter { it.lowercaseChar() !in tested }
        val head = untested.take(2)
        if (recommended[0] == 'r' || 'r' !in recommended ||
            recommended[4] != 'e' ||
            head[0].lowercaseChar() !in recommended ||
            head[1].lowercaseChar() !in recommended
        ) {
            fail(
                "error: $role: ${recommended.uppercase()} is not " +
                    "the chant derivation (moved R, chant head " +
                    "$head, green E at 5)"
            )
        }
        // Slot 4, asserted (review F3, 2026-11-14): running
        // the untested chant down from the top — past O and
        // T, which the frame already spends — the letters
        // before P complete no answer at TRO?E; P is the
        // first that does. (N and D complete valid guesses,
        // TRONE and TRODE, but no word you'd know — the back
        // says exactly that.) The back's skip list is built
        // from slot4Skips itself, so the text cannot drift
        // from this assertion (review F2, 2026-11-15).
        val slot4Skips = untested
            .substring(0, untested.indexOf('P'))
            .filter { it !in head }
        if (recommended[3] != 'p' ||
            slot4Skips.any { "tro${it.lowercaseChar()}e" in pool }
        ) {
            fail(
                "error: $role: slot 4 is not derived — the " +
                    "chant scan past $head " +
                    "must reach P first, skipping $slot4Skips"
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
                            "TRO?E. Fill the last slot down the " +
                            "chant: " +
                            slot4Skips.toList()
                                .joinToString(", ") {
                                    it.uppercase()
                                } +
                            " make no word you'd know " +
                            "&mdash; P does."
                    )
            ),
        )
    }
}
