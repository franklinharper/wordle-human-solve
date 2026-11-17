package com.franklinharper.wordle.deck

internal fun DeckBuild.buildPairFrame() {
    // -------------------------------------------------------
    // 6. Pair-frame drills: the pair before the Y.
    //
    // Frank's reframing (2026-11-16): the two slots before
    // a pinned Y are a pair in their own right, scanned
    // the way the ending-pair scan scans slots 4-5 — and
    // the pair is usually mixed (72% of Y-ending answers
    // carry two different consonants there, not a double).
    // The doubles rule names the shape to reach for first,
    // not the only shape on the board.
    //
    // The board is the retired doubles:happy board recast.
    // Over the candidate pool its completions are all
    // doubles (HAPPY, JAZZY, MAMMY), so the doubles drill
    // taught "double the P". But the board's best play is
    // CAMPY: MP is a recurring pair before Y, CAMPY can
    // itself be the answer (a common word — and the answer
    // list is a snapshot, not a boundary: GRIST, KARAT and
    // MOXIE were all answers while off it), and its pair
    // letters cross-examine the doubles, each sitting in
    // one candidate's telling slot, so every outcome names
    // the word. Asserted below: of the four live words
    // (the three doubles and CAMPY), CAMPY is the only
    // one whose feedback splits the whole set — every
    // double merges two of the others. LACKY is the foil,
    // carried over from the old
    // card: it fits and tests three fresh letters, none of
    // them a candidate double, but it is not in the pool
    // (a nonstandard spelling of LACKEY) and scores the
    // same against all three doubles — it splits nothing
    // and cannot solve.
    run {
        val role = "pairframe:campy"
        val boardAnswer = "happy"
        val guesses = listOf("raise", "tangy", "bawdy")
        val play = "campy"
        val foil = "lacky"

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

        fun isCcy(word: String): Boolean =
            word[2] == word[3] && word[4] == 'y' &&
                word[2] !in "aeiou"

        val candidates = pool.filter { w ->
            guesses.all {
                feedbackString(it, w) ==
                    feedbackString(it, boardAnswer)
            }
        }.toSet()
        if (candidates.size < 2 ||
            !candidates.all { isCcy(it) }
        ) {
            fail(
                "error: $role: board's candidate set over " +
                    "the pool must be a family of CCY words, " +
                    "got " +
                    pyList(candidates.sorted().map {
                        it.uppercase()
                    })
            )
        }
        if (play !in allGuesses) {
            fail(
                "error: $role: ${play.uppercase()} is not " +
                    "a valid guess"
            )
        }
        if (play in pool) {
            fail(
                "error: $role: ${play.uppercase()} is in " +
                    "the candidate pool -- the pair-frame " +
                    "play is the live word the pool misses"
            )
        }
        if (!guesses.all {
                feedbackString(it, play) ==
                    feedbackString(it, boardAnswer)
            }
        ) {
            fail(
                "error: $role: ${play.uppercase()} does " +
                    "not fit the board"
            )
        }
        if (!legal(play, knowledge(boardAnswer, guesses))) {
            fail(
                "error: $role: ${play.uppercase()} is not " +
                    "a legal hard-mode guess on this board"
            )
        }
        if (isCcy(play) || play[4] != 'y') {
            fail(
                "error: $role: ${play.uppercase()} must " +
                    "end in Y with a mixed pair before it"
            )
        }

        // The split property: the play's feedback names
        // every live word, itself included, and none of
        // the doubles does that.
        val live = candidates + play
        fun splitsAll(guess: String): Boolean =
            live.map { feedbackString(guess, it) }
                .distinct().size == live.size
        if (!splitsAll(play)) {
            fail(
                "error: $role: ${play.uppercase()} does " +
                    "not split the live set " +
                    pyList(live.sorted().map { it.uppercase() }) +
                    " -- two live words score the same " +
                    "against it"
            )
        }
        for (other in candidates) {
            if (splitsAll(other)) {
                fail(
                    "error: $role: ${other.uppercase()} " +
                        "also splits the whole live set -- " +
                        "${play.uppercase()} is not the " +
                        "only one of the live words that does"
                )
            }
        }

        // The decode on the back is derived from the play's
        // actual feedback: each double but one shows a
        // green in exactly one pair slot, naming the play's
        // letter there; the remaining double is the
        // "neither" case.
        val decode = mutableListOf<String>()
        var neither: String? = null
        for (w in candidates.sorted()) {
            val pattern = feedbackString(play, w)
            val greenSlots = (2..3).filter { pattern[it] == '2' }
            if (greenSlots.isEmpty()) {
                if (neither != null) {
                    fail(
                        "error: $role: two candidates " +
                            "show no pair-slot green against " +
                            "${play.uppercase()} -- the " +
                            "decode has no single 'neither' " +
                            "case"
                    )
                }
                neither = w
            } else {
                if (greenSlots.size != 1) {
                    fail(
                        "error: $role: ${w.uppercase()} " +
                            "shows pair-slot greens at " +
                            "$greenSlots against " +
                            "${play.uppercase()} -- the " +
                            "decode names one slot per word"
                    )
                }
                val slot = greenSlots.single()
                decode += "${play[slot].uppercase()} green " +
                    "at ${slot + 1} means ${w.uppercase()}"
            }
        }
        if (neither == null) {
            fail(
                "error: $role: every candidate shows a " +
                    "pair-slot green against " +
                    "${play.uppercase()} -- the decode " +
                    "needs a 'neither' case"
            )
        }
        val decodeText = decode.joinToString("; ") +
            "; neither means ${neither.uppercase()}"

        // The foil: playable, fits the board, outside the
        // pool, and scores the same against every candidate.
        if (foil !in allGuesses) {
            fail(
                "error: $role: foil ${foil.uppercase()} " +
                    "is not a valid guess"
            )
        }
        if (!guesses.all {
                feedbackString(it, foil) ==
                    feedbackString(it, boardAnswer)
            }
        ) {
            fail(
                "error: $role: foil ${foil.uppercase()} " +
                    "does not fit the board"
            )
        }
        if (foil in pool) {
            fail(
                "error: $role: foil ${foil.uppercase()} " +
                    "is in the candidate pool -- it could " +
                    "be the answer"
            )
        }
        if (candidates.map {
                feedbackString(foil, it)
            }.distinct().size != 1
        ) {
            fail(
                "error: $role: foil ${foil.uppercase()} " +
                    "does not score the same against " +
                    "every candidate -- it does split " +
                    "the family"
            )
        }
        val boardLetters = guesses.flatMap { it.toList() }
            .toSet()
        val fresh = foil.toList().distinct()
            .filter { it !in boardLetters }
        val doubles = candidates.map { it[2] }.toSet()
        if (fresh.size < 2 || fresh.any { it in doubles }) {
            fail(
                "error: $role: foil ${foil.uppercase()}: " +
                    "fresh letters $fresh -- the note needs " +
                    "several fresh letters, none of them " +
                    "a candidate double $doubles"
            )
        }

        val doublesPairs = candidates
            .map { it.substring(2, 4).uppercase() }
            .sorted()
        val headline = "<b>${play.uppercase()}</b> &mdash; " +
            "the pair before the Y is the unknown: " +
            doublesPairs.joinToString(", ") +
            " &mdash; or ${play.substring(2, 4).uppercase()}."
        val back = bodyDiv(headline) + promptDiv(
            "$decodeText. ${play.uppercase()} can itself " +
                "be the answer, and it is the only one of " +
                "the four that splits them all. " +
                "${foil.uppercase()} " +
                "fits too, but it can never be the answer " +
                "and splits nothing."
        )
        add(
            role,
            boardFront(
                boardAnswer, guesses, "What's the next guess?"
            ),
            wrap(back),
        )
    }
}
