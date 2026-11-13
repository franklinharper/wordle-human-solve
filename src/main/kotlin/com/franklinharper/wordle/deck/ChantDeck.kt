package com.franklinharper.wordle.deck

internal fun DeckBuild.buildChant() {
    // -------------------------------------------------------
    // 2. The after-RAISE chant as a ladder.
    //

    add(
        "chant:ladder:1",
        wrap(bodyDiv("What's the first word of the after-RAISE chant?")),
        wrap(bodyDiv("<b>${chantChunks[0]}</b>")),
    )
    for (k in 1 until chantChunks.size) {
        val (front, back) = ladderPair(
            chantChunks, k,
            "What's the next word of the after-RAISE chant?",
        )
        add("chant:ladder:${k + 1}", front, back)
    }
    add(
        "chant:full",
        wrap(bodyDiv("Recite the whole chant.")),
        wrap(
            bodyDiv(chantText) + promptDiv(
                "The letters RAISE doesn't test, in the order " +
                    "answers use them. Groups of 4-3-4-3."
            )
        ),
    )
}
