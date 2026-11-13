package com.franklinharper.wordle.deck

import java.nio.file.Files
import java.nio.file.Path

/**
 * The state one deck build accumulates into: the notes sink
 * every card family adds to, the shared data the families
 * consult (the answer list and candidate pool, the guess-2
 * table, the after-RAISE chant), and the board checks they
 * share. Each card family is a builder function on this class
 * in its own file; [DeckGenerator] orchestrates them.
 */
internal class DeckBuild(val repoRoot: Path) {
    val notes = mutableListOf<DeckNote>()

    fun add(role: String, front: String, back: String) {
        notes.add(DeckNote(role, front, back))
    }

    val answers: Set<String> by lazy {
        val loaded =
            Files.readAllLines(repoRoot.resolve("answers.txt"))
                .map { it.trim() }
                .filter { it.length == 5 }
                .toSet()
        if (loaded.isEmpty()) {
            fail(
                "error: answers.txt contains no five-letter words " +
                    "-- run this from the wordle-human-solve repo root"
            )
        }
        loaded
    }

    // The candidate pool for the drill assertions: the answer
    // list plus the answers Frank has actually met that the
    // fetched list still lacks (DRECK, #1966, was deduced as
    // its board's unique completion precisely because the
    // list did not contain it).
    val pool: Set<String> by lazy { answers + setOf("dreck", "parch") }

    val tableRows = listOf(
        Triple("00000", "cloth", "C, L, O, T, H"),
        Triple("00001", "olden", "O, L, D, N"),
        Triple("00100", "pilot", "P, L, O, T"),
        Triple("10000", "court", "C, O, U, T"),
        Triple("10001", "deter", "D, T"),
        Triple("01000", "float", "F, L, O, T"),
        Triple("02000", "tangy", "T, N, G, Y"),
        Triple("00010", "stunk", "T, U, N, K"),
        Triple("11000", "adorn", "D, O, N"),
        Triple("01001", "cleat", "C, L, T"),
        Triple("00002", "lunge", "L, U, N, G"),
        Triple("00200", "glint", "G, L, N, T"),
    )

    val table: Map<String, String> =
        tableRows.associate { (pattern, word, _) -> pattern to word }

    // The chant is the letters RAISE doesn't test, ranked by
    // how many answers contain them, cut at F: K, W, V and the
    // sub-2% tail have no system board that leaves them
    // first-untested, so they are not in the chant (Frank's
    // rule, 2026-11-04). CHANT_TEXT is an independent literal;
    // the equality check ties it to CHANT_CHUNKS, so editing
    // either one alone fails loudly.
    val chantChunks = listOf("OTLN", "UCY", "HDPM", "GBF")
    val chantText = "OTLN – UCY – HDPM – GBF"

    init {
        if (chantText != chantChunks.joinToString(SEPARATOR)) {
            fail(
                "error: chant text '$chantText' does not match its " +
                    "chunks $chantChunks"
            )
        }
    }

    val chant: String = chantChunks.joinToString("")

    /**
     * One ladder rung for a chunked text (the chant, the pair
     * scan's first letters): the front shows the chunks before
     * chunk k, then the blank, then the question — no header
     * (Frank's rule, 2026-11-07). The back shows only chunk k,
     * bolded — the one thing to add (Frank's rule, 2026-11-09).
     */
    fun ladderPair(
        chunks: List<String>,
        k: Int,
        question: String,
    ): Pair<String, String> {
        val front = wrap(
            bodyDiv(
                (chunks.take(k) + BLANK).joinToString(SEPARATOR)
            ) + bodyDiv(question)
        )
        val back = wrap(bodyDiv("<b>${chunks[k]}</b>"))
        return front to back
    }

    /**
     * The board checks every drill line shares: the answer
     * and every guess are answer-list words, and every
     * guess after the first is a legal hard-mode guess
     * given the ones before it.
     */
    fun validateLine(
        role: String,
        answer: String,
        guesses: List<String>,
    ) {
        if (answer !in answers) {
            fail("error: $role: '$answer' is not an answer")
        }
        for ((i, g) in guesses.withIndex()) {
            if (g !in answers) {
                fail("error: $role: '$g' is not an answer")
            }
            if (i > 0 && !legal(g, knowledge(answer, guesses.take(i)))) {
                fail(
                    "error: $role: guess ${i + 1} (${g.uppercase()}) " +
                        "is not a legal hard-mode guess on this board"
                )
            }
        }
    }
}
