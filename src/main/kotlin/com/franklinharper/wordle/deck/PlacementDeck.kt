package com.franklinharper.wordle.deck

internal data class PlacementCard(
    val role: String,
    val answer: String,
    val guesses: List<String>,
    val others: List<String>,
)

internal fun DeckBuild.buildPlacement() {
    // -------------------------------------------------------
    // 8. Placement drills: three floating yellows.
    //
    // Each board is frozen at the LOAMY moment: three distinct
    // yellow letters, no green tile anywhere, and a candidate
    // set of two to five words over the pool, all named on
    // the back. Construction rules, all asserted: guess 2 is
    // the mnemonic's table word; the board's candidate set is
    // exactly the back's named set.
    val placementCards = listOf(
        PlacementCard(
            "placement:loamy", "loamy", listOf("raise", "float"),
            listOf("aglow", "koala", "polka")),
        PlacementCard(
            "placement:dwell", "dwell", listOf("raise", "olden"),
            listOf("dwelt")),
        PlacementCard(
            "placement:erect", "erect", listOf("raise", "deter"),
            listOf("exert")),
        PlacementCard(
            "placement:knelt", "knelt", listOf("raise", "olden"),
            listOf("newly")),
        PlacementCard(
            "placement:logic", "logic", listOf("raise", "pilot"),
            listOf("login")),
        PlacementCard(
            "placement:beach", "beach", listOf("raise", "cleat"),
            listOf("mecca", "peach")),
        PlacementCard(
            "placement:dusky", "dusky", listOf("raise", "stunk"),
            listOf("husky", "musky")),
        PlacementCard(
            "placement:draft", "draft", listOf("raise", "adorn"),
            listOf("drama", "drawl", "fraud")),
    )

    for ((role, answer, guesses, others) in placementCards) {
        if (answer !in pool) {
            fail("error: $role: '$answer' is not in the candidate pool")
        }
        if (guesses[0] != "raise") {
            fail("error: $role: first guess is not RAISE")
        }
        val pattern = feedbackString("raise", answer)
        if (pattern !in table || guesses[1] != table[pattern]) {
            fail(
                "error: $role: guess 2 is '${guesses[1]}', but " +
                    "the table word for $pattern is " +
                    "'${table[pattern] ?: "None"}'"
            )
        }
        for ((i, g) in guesses.withIndex()) {
            if (g !in pool) {
                fail("error: $role: '$g' is not in the candidate pool")
            }
            if (g == answer) {
                fail(
                    "error: $role: guess ${i + 1} solves the " +
                        "board -- the drill would be over"
                )
            }
            if (i > 0 && !legal(g, knowledge(answer, guesses.take(i)))) {
                fail(
                    "error: $role: guess ${i + 1} (${g.uppercase()}) " +
                        "is not a legal hard-mode guess on this board"
                )
            }
        }
        val rows = guesses.map { feedbackDigits(it, answer) }
        if (rows.any { row -> row.any { it == 2 } }) {
            fail(
                "error: $role: board has a green tile -- " +
                    "placement drills hold floating yellows only"
            )
        }
        val yellowLetters = guesses.indices.flatMap { gi ->
            (0..4).filter { pos -> rows[gi][pos] == 1 }
                .map { pos -> guesses[gi][pos] }
        }.toSet()
        if (yellowLetters.size != 3) {
            fail(
                "error: $role: board floats " +
                    pyList(yellowLetters.sorted().map { it.toString() }) +
                    ", not three letters"
            )
        }
        val candidates = pool.filter { w ->
            guesses.all {
                feedbackString(it, w) == feedbackString(it, answer)
            }
        }.toSet()
        val named = setOf(answer) + others
        if (candidates != named) {
            fail(
                "error: $role: board's candidate set is " +
                    pyList(candidates.sorted().map { it.uppercase() }) +
                    " but the back names " +
                    pyList(named.sorted().map { it.uppercase() })
            )
        }
        add(
            role,
            boardFront(answer, guesses, "What's the next guess?"),
            wrap(
                bodyDiv(
                    "<b>${answer.uppercase()}</b> &mdash; also " +
                        "consistent: " +
                        others.joinToString(", ") { it.uppercase() } +
                        "."
                )
            ),
        )
    }
}
