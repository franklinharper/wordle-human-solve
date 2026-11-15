package com.franklinharper.wordle.deck

internal fun DeckBuild.buildTripleScan() {
    // -------------------------------------------------------
    // 11. The triple scans (Frank's grill, 2026-11-14).
    //
    // Three consonants in a row are where Frank's generation
    // stalls, so the scan turns that shape into a procedure,
    // the way the pair scan did for two. Two scans: endings
    // (slots 3-5) and openings (slots 1-3). Middles (slots
    // 2-4) are a long tail — 18 triples across 23 answers —
    // and stay search territory. A "triple" is three true
    // consonants: Y never counts (it is the vowel in LYMPH
    // and NYMPH, and CCY/Y endings have their own machinery
    // in the doubles family).
    //
    // The scan orders are curated literals — endings group
    // by the pair they extend (CH takes T, N, R, L in front;
    // HT takes G; TH takes R, N; then the three that extend
    // no scanned pair) — and the assertions tie them to the
    // answer list: every listed triple must close at least
    // two answers at its slot, and every answer-list triple
    // that does must be listed. Each card's examples are
    // answers carrying the triple at the slot: four where
    // four exist, otherwise the triple's full set (NTH, RST
    // and MPH close three answers each; RSH and SPL two).
    data class TripleCard(
        val triple: String,
        val examples: List<String>,
    )

    val endingTriples = listOf(
        TripleCard("TCH", listOf("batch", "catch", "ditch", "watch")),
        TripleCard("NCH", listOf("bench", "lunch", "pinch", "ranch")),
        TripleCard("RCH", listOf("birch", "march", "porch", "torch")),
        TripleCard("LCH", listOf("belch", "gulch", "mulch", "welch")),
        TripleCard("GHT", listOf("eight", "light", "night", "ought")),
        TripleCard("RTH", listOf("birth", "earth", "north", "worth")),
        TripleCard("NTH", listOf("month", "ninth", "tenth")),
        TripleCard("RST", listOf("burst", "first", "worst")),
        TripleCard("MPH", listOf("humph", "lymph", "nymph")),
        TripleCard("RSH", listOf("harsh", "marsh")),
    )
    val openingTriples = listOf(
        TripleCard("STR", listOf("strap", "straw", "strip", "strut")),
        TripleCard("SCR", listOf("scrap", "screw", "scrub", "scrum")),
        TripleCard("THR", listOf("three", "threw", "throw", "thrum")),
        TripleCard("SHR", listOf("shred", "shrew", "shrub", "shrug")),
        TripleCard("SPR", listOf("spray", "spree", "sprig")),
        TripleCard("SPL", listOf("splat", "split")),
    )

    fun checkScan(
        name: String,
        cards: List<TripleCard>,
        start: Int,
    ) {
        val byTriple = answers
            .groupBy { it.substring(start, start + 3) }
            .filterKeys { triple ->
                triple.all { it !in "aeiou" && it != 'y' }
            }
        val covered = byTriple
            .filterValues { it.size >= 2 }.keys
            .map { it.uppercase() }.toSet()
        val listed = cards.map { it.triple }.toSet()
        if (listed != covered) {
            fail(
                "error: the $name triple scan lists $listed, " +
                    "but the answer list's triples with two " +
                    "or more answers at that slot are $covered"
            )
        }
        for (card in cards) {
            val words = byTriple[card.triple.lowercase()]
            if (words == null || words.size < 2) {
                fail(
                    "error: triples:$name: ${card.triple} " +
                        "closes fewer than two answers"
                )
            }
            val expected = minOf(4, words.size)
            if (card.examples.size != expected ||
                card.examples.toSet().size != expected
            ) {
                fail(
                    "error: triples:$name: ${card.triple} " +
                        "must carry $expected distinct examples"
                )
            }
            if (words.size < 4 &&
                card.examples.toSet() != words.toSet()
            ) {
                fail(
                    "error: triples:$name: ${card.triple} " +
                        "closes fewer than four answers, so " +
                        "its examples must be the full set"
                )
            }
            for (example in card.examples) {
                if (example !in answers ||
                    example.substring(start, start + 3) !=
                    card.triple.lowercase()
                ) {
                    fail(
                        "error: triples:$name: '$example' is " +
                            "not an answer carrying ${card.triple} " +
                            "at that slot"
                    )
                }
            }
        }
    }
    checkScan("end", endingTriples, 2)
    checkScan("open", openingTriples, 0)

    fun ladder(
        rolePrefix: String,
        scanName: String,
        cards: List<TripleCard>,
    ) {
        fun back(card: TripleCard) = wrap(
            bodyDiv("<b>${card.triple}</b>") +
                bodyDiv("E.g") +
                bodyDiv(
                    card.examples.joinToString(", ") {
                        it.uppercase()
                    }
                )
        )
        add(
            "$rolePrefix:ladder:1",
            wrap(
                bodyDiv(
                    "What's the first group of the $scanName scan?"
                )
            ),
            back(cards[0]),
        )
        for (k in 1 until cards.size) {
            val shown = cards.take(k)
                .joinToString(" · ") { it.triple }
            val front = wrap(
                bodyDiv("$shown$SEPARATOR$BLANK") + bodyDiv(
                    "What's the next group of the $scanName scan?"
                )
            )
            add("$rolePrefix:ladder:${k + 1}", front, back(cards[k]))
        }
        add(
            "$rolePrefix:recite",
            wrap(bodyDiv("Recite the $scanName scan.")),
            wrap(
                bodyDiv(
                    cards.joinToString(" · ") { it.triple }
                )
            ),
        )
    }
    ladder("triples:end", "ending-triple", endingTriples)
    ladder("triples:open", "opening-triple", openingTriples)

    add(
        "triples:end:trigger",
        wrap(
            bodyDiv(
                "The last three slots are all consonants. " +
                    "What do you run?"
            )
        ),
        wrap(
            bodyDiv(
                "The ending-triple scan — " +
                    endingTriples.joinToString(", ") { it.triple } +
                    ". Skip any triple holding a dead letter."
            )
        ),
    )
    add(
        "triples:open:trigger",
        wrap(
            bodyDiv(
                "The first three slots are all consonants. " +
                    "What do you run?"
            )
        ),
        wrap(
            bodyDiv(
                "The opening-triple scan — " +
                    openingTriples.joinToString(", ") { it.triple } +
                    "."
            )
        ),
    )
}
