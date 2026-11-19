package com.franklinharper.wordle.deck

import com.franklinharper.wordle.core.loadAllGuesses
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

    // Every word the game accepts as a guess, from the
    // fetched guess list: the list the game itself enforces
    // at entry, so it — unlike the answer list — is
    // authoritative for what can be played (Frank,
    // 2026-11-16).
    val allGuesses: Set<String> by lazy {
        loadAllGuesses(repoRoot).map { it.value }.toSet()
    }

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
     * The example check both scan decks share (Frank's
     * format, 2026-11-14; hoisted 2026-11-15, review F2):
     * a card's examples are distinct answers carrying its
     * pattern — exactly min(4, how many answers carry it)
     * of them, and the full set when fewer than four
     * answers carry it. [candidates] is every answer
     * carrying the pattern; [carries] tests one word;
     * [notCarrying] phrases the failure ("an answer ending
     * in CH", "an answer carrying TCH at that slot").
     */
    fun checkExamples(
        label: String,
        examples: List<String>,
        candidates: Collection<String>,
        carries: (String) -> Boolean,
        notCarrying: String,
    ) {
        val expected = minOf(4, candidates.size)
        if (examples.size != expected ||
            examples.toSet().size != expected
        ) {
            fail(
                "error: $label must carry $expected " +
                    "distinct examples"
            )
        }
        if (candidates.size < 4 &&
            examples.toSet() != candidates.toSet()
        ) {
            fail(
                "error: $label closes fewer than four " +
                    "answers, so its examples must be the " +
                    "full set"
            )
        }
        for (example in examples) {
            if (example !in answers || !carries(example)) {
                fail(
                    "error: $label: '$example' is not " +
                        notCarrying
                )
            }
        }
    }

    /**
     * A scan back in the agreed shape (Frank, 2026-11-14):
     * the recalled item, an "E.g" line, then one line per
     * example group. Shared by the pair scan's stage 2 and
     * the triple ladders, so the two cannot drift apart
     * (review F2, 2026-11-15).
     */
    fun examplesBack(
        headerHtml: String,
        exampleLines: List<String>,
    ): String = wrap(
        bodyDiv(headerHtml) + bodyDiv("E.g") +
            exampleLines.joinToString("") { bodyDiv(it) }
    )

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

    /**
     * A CCY word: the consonant before the final Y doubles
     * — slots 3-4 equal, slot 5 the Y, and the doubled
     * letter not a vowel. Shared by the doubles boards and
     * the pair-frame board, whose checks must agree on
     * what CCY means.
     */
    fun isCcy(word: String): Boolean =
        word[2] == word[3] && word[4] == 'y' && word[2] !in "aeiou"

    /**
     * The pair-frame decode (PairFrameDeck): the sentence
     * naming what each of the play's outcomes means, derived
     * from its actual feedback against the candidates —
     * every candidate but one shows a green in exactly one
     * pair slot (slots 3-4), naming the play's letter there;
     * the remaining candidate is the "neither" case. Fails
     * loudly when the feedback does not have that shape.
     */
    fun pairFrameDecode(
        role: String,
        play: String,
        candidates: Set<String>,
    ): String {
        val decode = mutableListOf<String>()
        var neither: String? = null
        for (w in candidates.sorted()) {
            val pattern = feedbackString(play, w)
            val greenSlots = (2..3).filter { pattern[it] == '2' }
            if (greenSlots.isEmpty()) {
                if (neither != null) {
                    fail(
                        "error: $role: two candidates " +
                            "show no pair-slot green against " +
                            "${play.uppercase()} -- the " +
                            "decode has no single 'neither' " +
                            "case"
                    )
                }
                neither = w
            } else {
                if (greenSlots.size != 1) {
                    fail(
                        "error: $role: ${w.uppercase()} " +
                            "shows pair-slot greens at " +
                            "$greenSlots against " +
                            "${play.uppercase()} -- the " +
                            "decode names one slot per word"
                    )
                }
                val slot = greenSlots.single()
                decode += "${play[slot].uppercase()} green " +
                    "at ${slot + 1} means ${w.uppercase()}"
            }
        }
        if (neither == null) {
            fail(
                "error: $role: every candidate shows a " +
                    "pair-slot green against " +
                    "${play.uppercase()} -- the decode " +
                    "needs a 'neither' case"
            )
        }
        return decode.joinToString("; ") +
            "; neither means ${neither.uppercase()}"
    }

    /**
     * The pair-frame foil checks (PairFrameDeck): the foil
     * is a playable word that fits the board and tests
     * several fresh letters, none of them a candidate
     * double, yet is no plausible answer — the pool check
     * below is the mechanical guard; the plausibility
     * itself is a property of the word, recorded on the
     * card — and it scores the same against every
     * candidate, so it splits nothing.
     */
    fun checkPairFrameFoil(
        role: String,
        foil: String,
        guesses: List<String>,
        boardAnswer: String,
        candidates: Set<String>,
    ) {
        if (foil !in allGuesses) {
            fail(
                "error: $role: foil ${foil.uppercase()} " +
                    "is not a valid guess"
            )
        }
        if (!guesses.all {
                feedbackString(it, foil) ==
                    feedbackString(it, boardAnswer)
            }
        ) {
            fail(
                "error: $role: foil ${foil.uppercase()} " +
                    "does not fit the board"
            )
        }
        if (foil in pool) {
            fail(
                "error: $role: foil ${foil.uppercase()} " +
                    "is in the candidate pool -- it could " +
                    "be the answer"
            )
        }
        if (candidates.map {
                feedbackString(foil, it)
            }.distinct().size != 1
        ) {
            fail(
                "error: $role: foil ${foil.uppercase()} " +
                    "does not score the same against " +
                    "every candidate -- it does split " +
                    "the family"
            )
        }
        val boardLetters = guesses.flatMap { it.toList() }
            .toSet()
        val fresh = foil.toList().distinct()
            .filter { it !in boardLetters }
        val doubles = candidates.map { it[2] }.toSet()
        if (fresh.size < 2 || fresh.any { it in doubles }) {
            fail(
                "error: $role: foil ${foil.uppercase()}: " +
                    "fresh letters $fresh -- the note needs " +
                    "several fresh letters, none of them " +
                    "a candidate double $doubles"
            )
        }
    }
}
