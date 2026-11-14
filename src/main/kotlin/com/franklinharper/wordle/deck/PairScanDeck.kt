package com.franklinharper.wordle.deck

internal fun DeckBuild.buildPairScan() {
    // -------------------------------------------------------
    // 6. The ending-pair scan, memorized in two stages.
    //
    // PAIR_TEXT is an independent literal, tied to PAIR_CHUNKS
    // the same way the chant's is. Frank's approach
    // (2026-11-09): stage 1 is the twelve first letters,
    // stage 2 is each first letter's second letters; both
    // stages derive from PAIR_CHUNKS, and the reconstruction
    // check ties them back to PAIR_TEXT. The ladder roles are
    // the ones the old group ladder used — same ladder, same
    // scan — so a re-import updates those cards in place.
    val pairChunks = listOf(
        "CH CK", "NG NT NK ND", "ST SH SS", "TH",
        "LL LT LD", "RT RD RN RK", "MP", "WN", "FF FT",
        "HT", "PT", "GH",
    )
    val pairText = "CH CK – NG NT NK ND – ST SH SS – TH – " +
        "LL LT LD – RT RD RN RK – MP – WN – FF FT – HT – PT – GH"
    if (pairText != pairChunks.joinToString(SEPARATOR)) {
        fail(
            "error: pair-scan text '$pairText' does not match " +
                "its chunks $pairChunks"
        )
    }
    val pairGroups = pairChunks.map { it.split(" ") }
    val firstLetters = pairGroups.map { it[0][0] }
    val seconds: Map<Char, List<Char>> = pairGroups.associate {
        it[0][0] to it.map { pair -> pair[1] }
    }
    val rebuilt = firstLetters.joinToString(SEPARATOR) { first ->
        seconds.getValue(first).joinToString(" ") { "$first$it" }
    }
    if (rebuilt != pairText) {
        fail(
            "error: the two stages rebuild '$rebuilt', not " +
                "the scan '$pairText'"
        )
    }

    // Stage 1: the first letters, chunked as a ladder (Frank,
    // 2026-11-09). The chunks cut the twelve letters 4-4-4 on
    // the scan's strength tiers. FIRST_CHUNKS_TEXT is an
    // independent literal, tied the same way, and the chunks
    // must reassemble into the first letters exactly.
    val firstChunks = listOf("CNST", "LRMW", "FHPG")
    val firstChunksText = "CNST – LRMW – FHPG"
    if (firstChunksText != firstChunks.joinToString(SEPARATOR)) {
        fail(
            "error: first-letters text '$firstChunksText' does " +
                "not match its chunks $firstChunks"
        )
    }
    if (firstChunks.joinToString("") !=
        firstLetters.joinToString("")
    ) {
        fail(
            "error: first-letter chunks $firstChunks do not " +
                "reassemble into the first letters $firstLetters"
        )
    }

    add(
        "pairs:ladder:1",
        wrap(bodyDiv("What's the first pair of the ending-pair scan?")),
        wrap(bodyDiv("<b>${firstChunks[0]}</b>")),
    )
    for (k in 1 until firstChunks.size) {
        val (front, back) = ladderPair(
            firstChunks, k,
            "What's the next chunk of the ending-pair scan?",
        )
        add("pairs:ladder:${k + 1}", front, back)
    }
    add(
        "pairs:first-full",
        wrap(bodyDiv("Recite the ending-pair scan.")),
        wrap(bodyDiv(firstChunksText)),
    )

    // Stage 2: for each first letter, its second letters.
    for (first in firstLetters) {
        val front = wrap(
            bodyDiv("<b>$first</b>") + bodyDiv(
                "Which second letters follow it in the " +
                    "ending-pair scan?"
            )
        )
        val back = wrap(
            bodyDiv(
                "<b>" + seconds.getValue(first)
                    .joinToString(" ") + "</b>"
            )
        )
        add("pairs:seconds:${first.lowercaseChar()}", front, back)
    }
}
