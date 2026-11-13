package com.franklinharper.wordle.deck

internal fun DeckBuild.buildMnemonic() {
    // -------------------------------------------------------
    // 1. The guess-2 mnemonic as a ladder.
    //
    // The text: three sentences whose content words are the
    // twelve table words, in table order. Each ladder rung
    // shows the text so far and a blank for the next word; the
    // back shows only the word to add, bolded (Frank's rule,
    // 2026-11-09: a ladder back never repeats what the front
    // already gave). The segments carry each word's glue
    // (articles, "and", "it,") and closing punctuation.
    val text = "The tangy olden cloth stunk. The court pilot's " +
        "cleats glint and float. Adorn it, deter it, lunge!"
    val segments = listOf(
        Triple("The ", "tangy", ""),
        Triple(" ", "olden", ""),
        Triple(" ", "cloth", ""),
        Triple(" ", "stunk", "."),
        Triple(". The ", "court", ""),
        Triple(" ", "pilot's", ""),
        Triple(" ", "cleats", ""),
        Triple(" ", "glint", ""),
        Triple(" and ", "float", "."),
        Triple(". ", "Adorn", ""),
        Triple(" it, ", "deter", ""),
        Triple(" it, ", "lunge", "!"),
    )
    for ((_, token, _) in segments) {
        val n = text.split(token).size - 1
        if (n != 1) {
            fail(
                "error: token '$token' occurs $n times in the " +
                    "text (expected exactly 1)"
            )
        }
    }
    for ((k, segment) in segments.withIndex()) {
        val (pre, token, _) = segment
        if (k == 0) {
            // Rung 1 cannot be a prefix blank: the whole "text
            // so far" is the word "The", which cues nothing. It
            // is a question card instead — the question itself
            // supplies the context (Frank's catch, 2026-11-04).
            val front = wrap(
                bodyDiv("What's the first word of the mnemonic text?")
            )
            val back = wrap(bodyDiv("<b>$token</b>"))
            add("mnemonic:ladder:${k + 1}", front, back)
            continue
        }
        val soFar = segments.take(k)
            .joinToString("") { (p, t, _) -> p + t }
        val front = wrap(
            bodyDiv(soFar + pre + BLANK) +
                bodyDiv("What's the next word of the mnemonic text?")
        )
        val back = wrap(bodyDiv("<b>$token</b>"))
        add("mnemonic:ladder:${k + 1}", front, back)
    }
    add(
        "mnemonic:full-text",
        wrap(bodyDiv("Recite the whole mnemonic text.")),
        wrap(bodyDiv(text.replace(". ", ".<br>"))),
    )
}
