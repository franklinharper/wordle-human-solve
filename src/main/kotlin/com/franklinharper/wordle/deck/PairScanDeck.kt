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
        wrap(bodyDiv("What's the first group of the ending-pair scan?")),
        wrap(bodyDiv("<b>${firstChunks[0]}</b>")),
    )
    for (k in 1 until firstChunks.size) {
        val (front, back) = ladderPair(
            firstChunks, k,
            "What's the next group of the ending-pair scan?",
        )
        add("pairs:ladder:${k + 1}", front, back)
    }
    add(
        "pairs:first-full",
        wrap(bodyDiv("Recite the first-letter groups of the ending-pair scan.")),
        wrap(bodyDiv(firstChunksText)),
    )

    // Stage 2: for each first letter, its second letters.
    // The back also carries examples (Frank, 2026-11-14):
    // an "E.g" line, then one line per pair with four
    // example answers — the same format as the triple
    // scans' backs, so bare letters never sit without
    // words behind them. The assertions tie the examples
    // to the answer list: every scanned pair has exactly
    // four distinct examples, each an answer ending in
    // that pair, and no pair outside the scan has any.
    val pairExamples: Map<String, List<String>> = mapOf(
        "CH" to listOf("batch", "catch", "lunch", "march"),
        "CK" to listOf("black", "check", "quick", "truck"),
        "NG" to listOf("along", "bring", "sting", "young"),
        "NT" to listOf("agent", "count", "front", "plant"),
        "NK" to listOf("blank", "chunk", "drink", "think"),
        "ND" to listOf("blind", "found", "grand", "sound"),
        "ST" to listOf("blast", "first", "ghost", "trust"),
        "SH" to listOf("brush", "clash", "fresh", "trash"),
        "SS" to listOf("bless", "class", "dress", "glass"),
        "TH" to listOf("birth", "cloth", "earth", "month"),
        "LL" to listOf("chill", "drill", "skill", "still"),
        "LT" to listOf("adult", "built", "fault", "vault"),
        "LD" to listOf("build", "child", "field", "world"),
        "RT" to listOf("alert", "chart", "heart", "sport"),
        "RD" to listOf("award", "board", "guard", "sword"),
        "RN" to listOf("acorn", "learn", "mourn", "thorn"),
        "RK" to listOf("clerk", "quark", "shark", "stork"),
        "MP" to listOf("blimp", "champ", "stamp", "trump"),
        "WN" to listOf("brown", "clown", "drown", "grown"),
        "FF" to listOf("bluff", "cliff", "fluff", "stuff"),
        "FT" to listOf("craft", "drift", "shift", "swift"),
        "HT" to listOf("eight", "light", "night", "right"),
        "PT" to listOf("adept", "crept", "erupt", "slept"),
        "GH" to listOf("cough", "dough", "laugh", "tough"),
    )
    val scannedPairs = pairGroups.flatten().toSet()
    if (pairExamples.keys != scannedPairs) {
        fail(
            "error: pair examples cover ${pairExamples.keys}, " +
                "but the scan's pairs are $scannedPairs"
        )
    }
    for ((pair, examples) in pairExamples) {
        checkExamples(
            "pairs:seconds: $pair",
            examples,
            answers.filter { it.endsWith(pair.lowercase()) },
            { it.endsWith(pair.lowercase()) },
            "an answer ending in $pair",
        )
    }
    for ((index, first) in firstLetters.withIndex()) {
        val front = wrap(
            bodyDiv("<b>$first</b>") + bodyDiv(
                "Which second letters follow it in the " +
                    "ending-pair scan?"
            )
        )
        val back = examplesBack(
            "<b>" + seconds.getValue(first)
                .joinToString(" ") + "</b>",
            pairGroups[index].map { pair ->
                "$pair: " + pairExamples.getValue(pair)
                    .joinToString(", ") { it.uppercase() }
            },
        )
        add("pairs:seconds:${first.lowercaseChar()}", front, back)
    }
}
