package com.franklinharper.wordle.deck

internal data class ApplyCard(
    val role: String,
    val answer: String,
    val guesses: List<String>,
    val target: String,
)

internal fun DeckBuild.buildApply() {
    // -------------------------------------------------------
    // 4. Chant drills on real boards.
    fun firstUnguessed(guesses: List<String>): String? {
        val guessed = guesses.joinToString("").toSet()
        for (ch in chant.lowercase()) {
            if (ch !in guessed) return ch.uppercase()
        }
        return null
    }

    fun remainder(letter: String): String? {
        // The chant after letter, regrouped by chunk
        // boundaries and joined the way the chant is written;
        // null if letter is last.
        val i = chant.indexOf(letter)
        if (i == chant.length - 1) return null
        val parts = mutableListOf<String>()
        var pos = 0
        for (chunk in chantChunks) {
            val nxt = pos + chunk.length
            if (nxt > i + 1) {
                parts.add(chant.substring(maxOf(pos, i + 1), nxt))
            }
            pos = nxt
        }
        return parts.joinToString(SEPARATOR)
    }

    fun chantAnswerDivs(letter: String): String {
        val rest = remainder(letter)
        return if (rest == null) {
            bodyDiv("<b>$letter</b>") + promptDiv(
                "The last letter of the chant &mdash; nothing " +
                    "follows it."
            )
        } else {
            bodyDiv("<b>$letter</b> &mdash; then $rest")
        }
    }

    val scanQuestion = "What's the first letter of the " +
        "after-RAISE chant still untested &mdash; and the " +
        "rest of the chant from there?"

    val applyCards = listOf(
        ApplyCard("apply:cloth-gray", "fuzzy", listOf("raise", "cloth"), "N"),
        ApplyCard("apply:court", "dryly", listOf("raise", "court"), "L"),
        ApplyCard("apply:adorn", "mural", listOf("raise", "adorn"), "T"),
        ApplyCard("apply:tangy", "havoc", listOf("raise", "tangy"), "O"),
        ApplyCard("apply:pilot", "civil", listOf("raise", "pilot"), "N"),
        ApplyCard("apply:cleat", "hyena", listOf("raise", "cleat"), "O"),
        ApplyCard("apply:deter", "error", listOf("raise", "deter"), "O"),
        ApplyCard(
            "apply:fuzzy-p", "fuzzy",
            listOf("raise", "cloth", "bunny", "muddy"), "P"),
        ApplyCard(
            "apply:beefy-u", "beefy",
            listOf("raise", "olden", "fetch"), "U"),
        ApplyCard(
            "apply:aloha-c", "aloha",
            listOf("raise", "float", "along", "aloud"), "C"),
        ApplyCard(
            "apply:aback-y", "aback",
            listOf("raise", "float", "champ", "quack", "knack"), "Y"),
        ApplyCard(
            "apply:droll-h", "droll",
            listOf("raise", "court", "brown", "proxy", "drool"), "H"),
        ApplyCard(
            "apply:buddy-d", "buddy",
            listOf("raise", "cloth", "bumpy", "buggy", "bunny"), "D"),
        ApplyCard(
            "apply:foggy-m", "foggy",
            listOf("raise", "cloth", "bound", "poppy"), "M"),
        ApplyCard(
            "apply:buggy-g", "buggy",
            listOf("raise", "cloth", "bumpy", "buddy", "bunny"), "G"),
        ApplyCard(
            "apply:bobby-b", "bobby",
            listOf("raise", "cloth", "mound", "foggy", "poppy"), "B"),
        ApplyCard(
            "apply:fuzzy-f", "fuzzy",
            listOf("raise", "cloth", "pudgy", "bunny", "mummy"), "F"),
    )

    for ((role, answer, guesses, target) in applyCards) {
        validateLine(role, answer, guesses)
        if (guesses[0] != "raise") {
            fail("error: $role: first guess is not RAISE")
        }
        val pattern = feedbackString("raise", answer)
        if (pattern in table && guesses.size > 1 &&
            guesses[1] != table[pattern]
        ) {
            fail(
                "error: $role: guess 2 is '${guesses[1]}', but " +
                    "the table word for $pattern is '${table[pattern]}'"
            )
        }
        for ((i, g) in guesses.withIndex()) {
            if (g == answer) {
                fail(
                    "error: $role: guess ${i + 1} solves the " +
                        "board -- the drill would be over"
                )
            }
        }
        if (firstUnguessed(guesses) != target) {
            fail(
                "error: $role: board leaves " +
                    "${firstUnguessed(guesses) ?: "None"} first, not $target"
            )
        }
        add(
            role,
            boardFront(answer, guesses, scanQuestion),
            wrap(chantAnswerDivs(target)),
        )
    }
}
