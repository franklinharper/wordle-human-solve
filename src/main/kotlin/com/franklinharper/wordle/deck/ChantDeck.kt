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
                "Every letter, in the order answers use " +
                    "them &mdash; RAISE's five sit at their " +
                    "frequency places, already tested by the " +
                    "time the chant runs. Groups of " +
                    "4-4-4-4-3-3-4."
            )
        ),
    )
}
