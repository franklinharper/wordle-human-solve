package com.franklinharper.wordle.deck

internal data class PairCard(
    val role: String,
    val pair: String,
    val answer: String,
    val guesses: List<String>,
)

internal fun DeckBuild.buildPairDrills() {
    // -------------------------------------------------------
    // 7. Ending-pair drills, one per pair.
    //
    // Construction rules, all asserted: guess 2 is the
    // mnemonic's table word; every board carries at least one
    // green and one yellow somewhere; and at slots 4-5 at most
    // one letter of the pair may be green, and only where the
    // system's own line pins it. ST, SH and SS pin S at slot 4
    // from RAISE itself — those patterns are untabled, so
    // their guess 2 is an S-word probe; RT, RD, RN and RK pin
    // R at slot 4; PT pins T at slot 5.
    val pairCards = listOf(
        PairCard("pairs:ch", "CH", "torch", listOf("raise", "court")),
        PairCard("pairs:ck", "CK", "dreck", listOf("raise", "deter")),
        PairCard("pairs:ng", "NG", "thong", listOf("raise", "cloth")),
        PairCard("pairs:nt", "NT", "blunt", listOf("raise", "cloth")),
        PairCard("pairs:nk", "NK", "drunk", listOf("raise", "court", "gruff")),
        PairCard("pairs:nd", "ND", "blend", listOf("raise", "olden")),
        PairCard("pairs:st", "ST", "angst", listOf("raise", "stash")),
        PairCard("pairs:sh", "SH", "awash", listOf("raise", "amass")),
        PairCard("pairs:ss", "SS", "abyss", listOf("raise", "blast")),
        PairCard("pairs:th", "TH", "berth", listOf("raise", "deter")),
        PairCard("pairs:ll", "LL", "atoll", listOf("raise", "float")),
        PairCard("pairs:lt", "LT", "fault", listOf("raise", "tangy", "fatal")),
        PairCard("pairs:ld", "LD", "guild", listOf("raise", "glint")),
        PairCard("pairs:rt", "RT", "abort", listOf("raise", "adorn")),
        PairCard("pairs:rd", "RD", "award", listOf("raise", "adorn")),
        PairCard("pairs:rn", "RN", "churn", listOf("raise", "court")),
        PairCard("pairs:rk", "RK", "clerk", listOf("raise", "deter", "query")),
        PairCard("pairs:mp", "MP", "champ", listOf("raise", "float", "aback")),
        PairCard("pairs:wn", "WN", "blown", listOf("raise", "cloth", "blond")),
        PairCard("pairs:ff", "FF", "snuff", listOf("raise", "stunk")),
        PairCard("pairs:ft", "FT", "cleft", listOf("raise", "olden", "fleck")),
        PairCard("pairs:ht", "HT", "yacht", listOf("raise", "tangy")),
        PairCard("pairs:pt", "PT", "adapt", listOf("raise", "float", "chant")),
        PairCard("pairs:gh", "GH", "thigh", listOf("raise", "glint")),
    )

    for ((role, pair, answer, guesses) in pairCards) {
        val sAt4Exception = pair in listOf("ST", "SH", "SS")
        if (!answer.endsWith(pair.lowercase())) {
            fail(
                "error: $role: ${answer.uppercase()} does not " +
                    "end in $pair"
            )
        }
        if (answer !in pool) {
            fail("error: $role: '$answer' is not in the candidate pool")
        }
        if (guesses[0] != "raise") {
            fail("error: $role: first guess is not RAISE")
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
        val pattern = feedbackString("raise", answer)
        if (pattern in table) {
            if (guesses[1] != table[pattern]) {
                fail(
                    "error: $role: guess 2 is '${guesses[1]}', " +
                        "but the table word for $pattern is " +
                        "'${table[pattern]}'"
                )
            }
        } else if (!sAt4Exception ||
            feedbackDigits("raise", answer)[3] != 2
        ) {
            fail(
                "error: $role: RAISE pattern $pattern is " +
                    "untabled but this is not an ST/SH/SS board " +
                    "with S green at 4"
            )
        }
        val candidates = pool.filter { w ->
            guesses.all {
                feedbackString(it, w) == feedbackString(it, answer)
            }
        }.toSet()
        if (candidates != setOf(answer)) {
            fail(
                "error: $role: board leaves " +
                    pyList(candidates.sorted().map { it.uppercase() }) +
                    ", not just ${answer.uppercase()}"
            )
        }
        val rows = guesses.map { feedbackDigits(it, answer) }
        val greens = rows.sumOf { row -> row.count { it == 2 } }
        val yellows = rows.sumOf { row -> row.count { it == 1 } }
        if (greens < 1 || yellows < 1) {
            fail(
                "error: $role: board has $greens greens and " +
                    "$yellows yellows -- every drill board needs " +
                    "at least one of each"
            )
        }
        val green45 = guesses.indices.flatMap { gi ->
            listOf(3, 4).filter { pos -> rows[gi][pos] == 2 }
                .map { pos -> guesses[gi][pos] }
        }.toSet()
        if (green45.size > 1 ||
            (green45.isNotEmpty() &&
                green45.first() !in pair.lowercase())
        ) {
            fail(
                "error: $role: greens at slots 4-5 are " +
                    pyList(green45.sorted().map { it.toString() }) +
                    " -- at most one letter of the pair may be " +
                    "green there, and only where the system's " +
                    "own line pins it"
            )
        }
        add(
            role,
            boardFront(answer, guesses, "What's the next guess?"),
            wrap(bodyDiv("<b>$pair</b> &mdash; ${answer.uppercase()}")),
        )
    }
}
