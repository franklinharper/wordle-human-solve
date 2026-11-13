package com.franklinharper.wordle.deck

internal fun DeckBuild.buildFrame() {
    // -------------------------------------------------------
    // 9. Frame drills: the ?RO?E frame.
    //
    // The TRUCE board (2026-11-10, #1970): RAISE came back
    // R yellow, E green — pattern 10002, untabled (the table
    // holds R+E both yellow and E green alone, not this mix).
    // Frank played CHORE, parking R at slot 4, its least
    // likely home on this board (5 of the 40 candidates);
    // it paid off — TRUCE was left alone — but its largest
    // feedback bucket lumps 13 candidates together. The
    // frame lesson: think ?RO?E first, R at 2 and O at 3,
    // their likeliest slots. The recommended guess, TROPE,
    // is asserted legal on the board and an answer itself,
    // and its feedback on this board leaves TRUCE as the
    // pool's only candidate — the same solve in 3, earned
    // by the frame instead of by luck.
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
                        "The ?RO?E frame &mdash; R at 2, O at 3. " +
                            "Tests T, P."
                    )
            ),
        )
    }
}
