package com.franklinharper.wordle.deck

internal data class MiddleCard(
    val role: String,
    val answer: String,
    val guesses: List<String>,
    // The doubled vowel, and the first of its two slots
    // (0-based): the pair sits across a middle boundary,
    // slots 2-3 (firstSlot 1) or slots 3-4 (firstSlot 2).
    val vowel: Char,
    val firstSlot: Int,
)

internal fun DeckBuild.buildMiddleDoubles() {
    // -------------------------------------------------------
    // 14. Middle doubles: the E/O rule and four boards.
    //
    // The strategy's middle-doubles rule (entered
    // 2026-11-24, from that morning's STEER game): E and O
    // are the only letters that double side by side, and
    // they do it across the middle -- 107 answers carry an
    // EE or an OO across slots 2-3 or 3-4 -- while A, I
    // and U doubles always split. Each board pins the
    // doubled vowel green at exactly one of its two slots
    // and leaves the twin slot open, so the double is the
    // player's own move, and the board's pool completions
    // all carry the same vowel doubled across a middle
    // boundary (the shape purity the CCY boards assert,
    // transposed). The back names the play and every other
    // word the board admits over pool and guess list
    // together -- possible solutions from the player's
    // seat, the pair drills' convention.
    add(
        "middle:rule",
        wrap(bodyDiv("Which vowels double side by side, and where?")),
        wrap(
            bodyDiv(
                "Only <b>E</b> and <b>O</b> &mdash; across the " +
                    "middle, slots 2&ndash;3 and above all " +
                    "3&ndash;4 (107 answers). A pinned middle " +
                    "E or O: try its double next door first. " +
                    "A, I and U never double side by side " +
                    "&mdash; their doubles split."
            )
        ),
    )

    val middleCards = listOf(
        MiddleCard(
            "middle:breed", "breed",
            listOf("raise", "deter"), 'e', 2,
        ),
        MiddleCard(
            "middle:leery", "leery",
            listOf("raise", "deter"), 'e', 1,
        ),
        MiddleCard(
            "middle:afoot", "afoot",
            listOf("raise", "float"), 'o', 2,
        ),
        MiddleCard(
            "middle:pooch", "pooch",
            listOf("raise", "cloth"), 'o', 1,
        ),
    )

    fun hasMiddleDouble(w: String, v: Char): Boolean =
        (w[1] == v && w[2] == v) || (w[2] == v && w[3] == v)

    for ((role, answer, guesses, vowel, firstSlot)
        in middleCards) {
        if (firstSlot !in 1..2 ||
            answer[firstSlot] != vowel ||
            answer[firstSlot + 1] != vowel
        ) {
            fail(
                "error: $role: ${answer.uppercase()} does not " +
                    "carry $vowel doubled at slots " +
                    "${firstSlot + 1}-${firstSlot + 2}"
            )
        }
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
        if (answer in guesses) {
            fail(
                "error: $role: a guess in the line solves " +
                    "the board -- the drill would be over"
            )
        }
        // The setup the rule addresses, asserted: the
        // doubled vowel is green at exactly one of its two
        // slots, and the twin slot carries no green at all
        // -- the double is proposed, never half-given twice.
        val greens = knowledge(answer, guesses).greens
        val pinned = listOf(firstSlot, firstSlot + 1)
            .filter { greens[it] == vowel }
        if (pinned.size != 1 ||
            greens.containsKey(firstSlot) &&
            greens.containsKey(firstSlot + 1)
        ) {
            fail(
                "error: $role: greens on the double's slots " +
                    "are $greens -- exactly one slot of the " +
                    "pair must pin the vowel, the twin open"
            )
        }
        val candidates = pool.filter { w ->
            guesses.all {
                feedbackString(it, w) == feedbackString(it, answer)
            }
        }.toSet()
        if (answer !in candidates) {
            fail(
                "error: $role: ${answer.uppercase()} is not " +
                    "consistent with its own board"
            )
        }
        val impure = candidates.filter {
            !hasMiddleDouble(it, vowel)
        }
        if (impure.isNotEmpty()) {
            fail(
                "error: $role: board's candidate set is not " +
                    "pure middle-$vowel -- candidates without " +
                    "the double: " +
                    pyList(impure.sorted().map { it.uppercase() })
            )
        }
        val alsoFits = allGuesses.filter { w ->
            w != answer && guesses.all {
                feedbackString(it, w) == feedbackString(it, answer)
            }
        }.sorted()
        val headline = "Double the ${vowel.uppercaseChar()}:"
        val cardText = "$headline <b>${answer.uppercase()}</b>" +
            if (alsoFits.isEmpty()) {
                ""
            } else {
                " &mdash; also " +
                    alsoFits.joinToString(", ") { it.uppercase() } +
                    "."
            }
        add(
            role,
            boardFront(answer, guesses, "What's the next guess?"),
            wrap(bodyDiv(cardText)),
        )
    }
}
