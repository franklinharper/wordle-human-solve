package com.franklinharper.wordle.deck

import com.franklinharper.wordle.core.loadAllGuesses

internal fun DeckBuild.buildPrinciple() {
    // -------------------------------------------------------
    // 10. Principle drills: buy information with fresh
    // letters.
    //
    // The RAISE / PILOT / DINGY board used to be a doubles
    // card whose back named DIZZY — but that lesson rested
    // on knowing DIZZY is the board's unique answer, which
    // the player cannot know from the seat: he is searching,
    // not counting candidates, and the answer list itself
    // keeps growing (GRIST was an answer before it was on
    // the list). Frank's ruling (2026-11-12): cards drill
    // general principles, not special cases. The principle
    // here: a guess that tests two fresh letters beats one
    // that spends the guess doubling a single unconfirmed
    // letter. DICKY is that play — it fits this exact board
    // (asserted below: it scores the shown feedback against
    // every guess played) and tests C and K, both fresh;
    // DIZZY tests only Z, twice.
    run {
        val role = "principle:dicky"
        val boardAnswer = "dizzy"
        val guesses = listOf("raise", "pilot", "dingy")
        val recommended = "dicky"
        val validGuesses =
            loadAllGuesses(repoRoot).map { it.value }.toSet()
        if (recommended !in validGuesses) {
            fail(
                "error: $role: '$recommended' is not a " +
                    "valid guess"
            )
        }
        for (guess in guesses) {
            if (feedbackString(guess, recommended) !=
                feedbackString(guess, boardAnswer)
            ) {
                fail(
                    "error: $role: ${guess.uppercase()} " +
                        "against ${recommended.uppercase()} " +
                        "gives " +
                        feedbackString(guess, recommended) +
                        ", not the board's " +
                        feedbackString(guess, boardAnswer)
                )
            }
        }
        if (!legal(recommended, knowledge(boardAnswer, guesses))) {
            fail(
                "error: $role: ${recommended.uppercase()} is " +
                    "not a legal hard-mode guess on this board"
            )
        }
        val tested = guesses.joinToString("").toSet()
        val fresh: (String) -> Set<Char> =
            { w -> w.toSet() - tested }
        if (fresh(recommended) != setOf('c', 'k')) {
            fail(
                "error: $role: ${recommended.uppercase()} " +
                    "tests fresh letters " +
                    fresh(recommended).sorted() +
                    ", not C and K"
            )
        }
        if (fresh(boardAnswer) != setOf('z')) {
            fail(
                "error: $role: ${boardAnswer.uppercase()} " +
                    "tests fresh letters " +
                    fresh(boardAnswer).sorted() + ", not only Z"
            )
        }
        add(
            role,
            boardFront(
                boardAnswer, guesses, "What's the next guess?"
            ),
            wrap(
                bodyDiv("<b>${recommended.uppercase()}</b>") +
                    promptDiv(
                        "Tests two fresh letters, C and K. " +
                            "Don't spend the guess doubling " +
                            "one letter (Z) you haven't " +
                            "confirmed."
                    )
            ),
        )
    }
}
