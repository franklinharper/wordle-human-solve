package com.franklinharper.wordle.deck

internal fun DeckBuild.buildOneGap() {
    // -------------------------------------------------------
    // 13. One-gap drills: the chant slotted through a
    // single open slot.
    //
    // The CLOUT board (2026-11-19, #1979): RAISE came back
    // all gray and the table word CLOTH pinned C, L, O
    // green with T yellow at slot 4 — T cannot stay at 4
    // and slots 1-3 are taken, so T's only home is slot 5
    // and the frame is CLO?T with one open slot. Frank
    // solved in 1:23, and the minute went on generating
    // the missing letter by scanning the keyboard. The
    // card teaches the strategy's one-gap scan instead
    // (entered 2026-11-19): slot the chant through the
    // gap and pronounce each skeleton until one sounds
    // like a word. The derivation is asserted, not just
    // told: the chant reaches U fifth — O completes
    // CLOOT, a guess-list word but no answer; T, L and N
    // complete no playable word — and the back's skip
    // list is built from the asserted scan, so the text
    // cannot drift from it.
    run {
        val role = "onegap:clout"
        val boardAnswer = "clout"
        val guesses = listOf("raise", "cloth")
        val play = "clout"

        validateLine(role, boardAnswer, guesses)
        val tableWord = table[feedbackString("raise", boardAnswer)]
        if (guesses[1] != tableWord) {
            fail(
                "error: $role: guess 2 is " +
                    guesses[1].uppercase() +
                    ", but the rails play the table word " +
                    (tableWord?.uppercase() ?: "(pattern untabled)") +
                    " after RAISE on this board"
            )
        }
        if (feedbackString("cloth", boardAnswer) != "22210") {
            fail(
                "error: $role: CLOTH pattern is " +
                    feedbackString("cloth", boardAnswer) +
                    ", not 22210 (C, L, O green; T yellow; H gray)"
            )
        }
        if (!legal(play, knowledge(boardAnswer, guesses))) {
            fail(
                "error: $role: ${play.uppercase()} is not a " +
                    "legal hard-mode guess on this board"
            )
        }
        // The frame the back teaches, asserted: slots 1-3
        // are CLOTH's greens, T sits at slot 5 (its only
        // home), and slot 4 is the one open slot.
        if (play.substring(0, 3) != "clo" || play[4] != 't') {
            fail(
                "error: $role: ${play.uppercase()} does not " +
                    "have the CLO?T frame (greens at 1-3, T at 5)"
            )
        }
        // The scan, asserted against the guess list —
        // the list the game enforces (review F4,
        // 2026-11-20): running the chant from the top,
        // the letters before U complete no playable word
        // at CLO?T, with one named exception. O completes
        // CLOOT, a valid guess but no answer — its
        // absence from the pool is the evidence for
        // that; the criterion for passing it over is the
        // back's own argument, that it is a Scots word,
        // not one to settle on. The chant's shape is
        // asserted, not assumed (review F2, 2026-11-20):
        // the scan must reach a U, and O must come first
        // on the way, because the back's prose and the
        // skip list below both single O out.
        val uIndex = chant.indexOf('U')
        if (uIndex < 0) {
            fail("error: $role: the chant has no U to scan to")
        }
        val gapSkips = chant.substring(0, uIndex)
        if (gapSkips.firstOrNull() != 'O') {
            fail(
                "error: $role: the chant must reach O first " +
                    "on the way to U, got $gapSkips"
            )
        }
        val laterSkips = gapSkips.drop(1).toList()
        if (play[3] != 'u' ||
            laterSkips.any { "clo${it.lowercaseChar()}t" in allGuesses }
        ) {
            fail(
                "error: $role: slot 4 is not derived — the " +
                    "chant scan must reach U first, skipping " +
                    gapSkips
            )
        }
        if ("cloot" !in allGuesses || "cloot" in pool) {
            fail(
                "error: $role: CLOOT must be a valid guess " +
                    "but not a candidate — the back says so"
            )
        }
        add(
            role,
            boardFront(boardAnswer, guesses, "What's the next guess?"),
            wrap(
                bodyDiv("<b>${play.uppercase()}</b>") +
                    promptDiv(
                        "One slot open &mdash; slot 4: slots 1-3 " +
                            "are pinned, and T can't stay at 4, so " +
                            "it belongs at 5. Run the one-gap scan: " +
                            "slot the chant through the gap and " +
                            "pronounce each skeleton. O makes " +
                            "CLOOT &mdash; a Scots word, not one to " +
                            "settle on; " +
                            laterSkips.joinToString(", ") +
                            " make nothing you'd know; U does."
                    )
            ),
        )
    }
}
