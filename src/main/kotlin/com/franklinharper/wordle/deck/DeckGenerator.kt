package com.franklinharper.wordle.deck

import java.nio.file.Files
import java.nio.file.Path

/**
 * Generate Frank's "Wordle" Anki deck (port of
 * generate_anki_mnemonic_deck.py).
 *
 * The deck teaches the memorized parts of his hard-mode system:
 * 1. The guess-2 mnemonic, as a ladder over its twelve words.
 * 2. The after-RAISE chant (OTLN - UCY - HDPM - GBF), as a ladder.
 * 3. The guess-2 lookup table: RAISE's feedback row -> the table word.
 * 4. Chant drills on real boards: legal lines (RAISE, the table
 *    word, then answer-list words) asking for the first chant
 *    letter still untested, and the rest of the chant from there.
 * 5. Doubles: the doubled-consonant-before-Y rule and its boards.
 * 6. The ending-pair scan, memorized in two stages: the twelve
 *    first letters in three chunks (CNST - LRMW - FHPG) as a
 *    ladder, then each first letter's second letters.
 * 7. Ending-pair drills: boards whose only consistent completion
 *    ends in the card's pair.
 * 8. Placement drills: boards holding three floating yellows
 *    after RAISE and the table word, with no green tile.
 *
 * Every drill card's answer is asserted against its board before
 * the deck is written — a card whose board does not yield its
 * answer fails loudly (DeckError, exit 1).
 */

/** A deck build failure: the message is the whole report. */
class DeckError(message: String) : Exception(message)

private fun fail(message: String): Nothing = throw DeckError(message)

/** A Python-style list repr of uppercase words, for error messages. */
private fun pyList(items: Collection<String>): String =
    items.joinToString("', '", "['", "']")

private data class ApplyCard(
    val role: String,
    val answer: String,
    val guesses: List<String>,
    val target: String,
)

private data class DoublesCard(
    val role: String,
    val answer: String,
    val guesses: List<String>,
    val headline: String,
    val family: List<String>,
    val others: List<String>,
)

private data class PairCard(
    val role: String,
    val pair: String,
    val answer: String,
    val guesses: List<String>,
)

private data class PlacementCard(
    val role: String,
    val answer: String,
    val guesses: List<String>,
    val others: List<String>,
)

object DeckGenerator {

    fun build(repoRoot: Path): List<DeckNote> {
        val notes = mutableListOf<DeckNote>()
        fun add(role: String, front: String, back: String) {
            notes.add(DeckNote(role, front, back))
        }

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

        // -------------------------------------------------------
        // 2. The after-RAISE chant as a ladder.
        //
        // The chant is the letters RAISE doesn't test, ranked by
        // how many answers contain them, cut at F: K, W, V and the
        // sub-2% tail have no system board that leaves them
        // first-untested, so they are not in the chant (Frank's
        // rule, 2026-11-04). CHANT_TEXT is an independent literal;
        // the equality check ties it to CHANT_CHUNKS, so editing
        // either one alone fails loudly.
        val chantChunks = listOf("OTLN", "UCY", "HDPM", "GBF")
        val chantText = "OTLN – UCY – HDPM – GBF"
        if (chantText != chantChunks.joinToString(SEPARATOR)) {
            fail(
                "error: chant text '$chantText' does not match its " +
                    "chunks $chantChunks"
            )
        }
        val chant = chantChunks.joinToString("")

        fun ladderPair(
            chunks: List<String>,
            k: Int,
            question: String,
        ): Pair<String, String> {
            // The front shows the chunks before chunk k, then the
            // blank, then the question — no header (Frank's rule,
            // 2026-11-07). The back shows only chunk k, bolded —
            // the one thing to add (Frank's rule, 2026-11-09).
            val front = wrap(
                bodyDiv(
                    (chunks.take(k) + BLANK).joinToString(SEPARATOR)
                ) + bodyDiv(question)
            )
            val back = wrap(bodyDiv("<b>${chunks[k]}</b>"))
            return front to back
        }

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

        // -------------------------------------------------------
        // 3. The guess-2 lookup table.
        val answers: Set<String> =
            Files.readAllLines(repoRoot.resolve("answers.txt"))
                .map { it.trim() }
                .filter { it.length == 5 }
                .toSet()
        if (answers.isEmpty()) {
            fail(
                "error: answers.txt contains no five-letter words " +
                    "-- run this from the wordle-human-solve repo root"
            )
        }

        // The candidate pool for the drill assertions: the answer
        // list plus the answers Frank has actually met that the
        // fetched list still lacks (DRECK, #1966, was deduced as
        // its board's unique completion precisely because the
        // list did not contain it).
        val pool: Set<String> = answers + setOf("dreck", "parch")

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

        for ((pattern, word, letters) in tableRows) {
            if (word !in answers) {
                fail("error: table word '$word' is not an answer")
            }
            if (answers.none { feedbackString("raise", it) == pattern }) {
                fail("error: no answer gives RAISE pattern $pattern")
            }
            val front = wrap(
                """<div style="margin: 6px 0;">""" +
                    tileRow("raise", pattern.map { it.digitToInt() }) +
                    "</div>" +
                    bodyDiv("What's the next guess?")
            )
            val back = wrap(
                bodyDiv("<b>${word.uppercase()}</b>") +
                    promptDiv("Tests $letters")
            )
            add("guess2:$pattern", front, back)
        }

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

        fun validateLine(role: String, answer: String, guesses: List<String>) {
            // The board checks every drill line shares: the answer
            // and every guess are answer-list words, and every
            // guess after the first is a legal hard-mode guess
            // given the ones before it.
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

        // -------------------------------------------------------
        // 5. Doubles: the before-Y rule and four boards.
        //
        // Each board's answer doubles its consonant at positions
        // 3-4 before the Y — asserted below. Each back names every
        // word consistent with its board: the doubling family
        // first, then the rest — asserted against the board's
        // computed candidate set.
        add(
            "doubles:rule",
            wrap(bodyDiv("When a word ends in Y, what's the most likely shape?")),
            wrap(
                bodyDiv(
                    "The consonant before the Y doubles &mdash; " +
                        "_ _ CCY. 28% of Y-ending answers " +
                        "(CANNY, TALLY, NUTTY)."
                )
            ),
        )

        fun isCcy(word: String): Boolean =
            word[2] == word[3] && word[4] == 'y' && word[2] !in "aeiou"

        val doublesCards = listOf(
            DoublesCard(
                "doubles:canny", "canny", listOf("raise", "tangy"),
                "Extend the N into 4:",
                listOf("fanny", "nanny"),
                listOf("candy", "dandy", "fancy", "handy", "lanky", "manly"),
            ),
            DoublesCard(
                "doubles:dizzy", "dizzy",
                listOf("raise", "pilot", "dingy"),
                "Double the Z:", emptyList(), emptyList(),
            ),
            DoublesCard(
                "doubles:tally", "tally",
                listOf("raise", "tangy", "tacky"),
                "Double the L:",
                listOf("tabby", "taffy", "tatty"),
                emptyList(),
            ),
            DoublesCard(
                "doubles:happy", "happy",
                listOf("raise", "tangy", "wacky"),
                "Double the P:",
                listOf("daddy", "dally", "jazzy", "mammy", "paddy"),
                listOf("badly", "balmy", "madly"),
            ),
        )

        for ((role, answer, guesses, headline, family, others)
            in doublesCards) {
            validateLine(role, answer, guesses)
            if (!isCcy(answer)) {
                fail(
                    "error: $role: ${answer.uppercase()} is not a " +
                        "_ _ CCY word"
                )
            }
            for (w in family) {
                if (!isCcy(w)) {
                    fail(
                        "error: $role: family word ${w.uppercase()} " +
                            "is not a _ _ CCY word"
                    )
                }
            }
            for (w in others) {
                if (isCcy(w)) {
                    fail(
                        "error: $role: ${w.uppercase()} doubles its " +
                            "consonant -- it belongs in the family, " +
                            "not the others"
                    )
                }
            }
            val candidates = pool.filter { w ->
                guesses.all {
                    feedbackString(it, w) == feedbackString(it, answer)
                }
            }.toSet()
            val named = setOf(answer) + family + others
            if (candidates != named) {
                fail(
                    "error: $role: board's candidate set is " +
                        pyList(candidates.sorted().map { it.uppercase() }) +
                        " but the back names " +
                        pyList(named.sorted().map { it.uppercase() })
                )
            }
            var cardText = "$headline <b>${answer.uppercase()}</b>"
            cardText += if (family.isNotEmpty()) {
                " &mdash; also " +
                    family.joinToString(", ") { it.uppercase() } + "."
            } else {
                "."
            }
            if (others.isNotEmpty()) {
                cardText += " Also consistent: " +
                    others.joinToString(", ") { it.uppercase() } + "."
            }
            add(
                role,
                boardFront(answer, guesses, "What's the next guess?"),
                wrap(bodyDiv(cardText)),
            )
        }

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
            wrap(bodyDiv("What's the first of the ending-pair scan?")),
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

        // -------------------------------------------------------
        // 8. Placement drills: three floating yellows.
        //
        // Each board is frozen at the LOAMY moment: three distinct
        // yellow letters, no green tile anywhere, and a candidate
        // set of two to five words over the pool, all named on
        // the back. Construction rules, all asserted: guess 2 is
        // the mnemonic's table word; the board's candidate set is
        // exactly the back's named set.
        val placementCards = listOf(
            PlacementCard(
                "placement:loamy", "loamy", listOf("raise", "float"),
                listOf("aglow", "koala", "polka")),
            PlacementCard(
                "placement:dwell", "dwell", listOf("raise", "olden"),
                listOf("dwelt")),
            PlacementCard(
                "placement:erect", "erect", listOf("raise", "deter"),
                listOf("exert")),
            PlacementCard(
                "placement:knelt", "knelt", listOf("raise", "olden"),
                listOf("newly")),
            PlacementCard(
                "placement:logic", "logic", listOf("raise", "pilot"),
                listOf("login")),
            PlacementCard(
                "placement:beach", "beach", listOf("raise", "cleat"),
                listOf("mecca", "peach")),
            PlacementCard(
                "placement:dusky", "dusky", listOf("raise", "stunk"),
                listOf("husky", "musky")),
            PlacementCard(
                "placement:draft", "draft", listOf("raise", "adorn"),
                listOf("drama", "drawl", "fraud")),
        )

        for ((role, answer, guesses, others) in placementCards) {
            if (answer !in pool) {
                fail("error: $role: '$answer' is not in the candidate pool")
            }
            if (guesses[0] != "raise") {
                fail("error: $role: first guess is not RAISE")
            }
            val pattern = feedbackString("raise", answer)
            if (pattern !in table || guesses[1] != table[pattern]) {
                fail(
                    "error: $role: guess 2 is '${guesses[1]}', but " +
                        "the table word for $pattern is " +
                        "'${table[pattern] ?: "None"}'"
                )
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
            val rows = guesses.map { feedbackDigits(it, answer) }
            if (rows.any { row -> row.any { it == 2 } }) {
                fail(
                    "error: $role: board has a green tile -- " +
                        "placement drills hold floating yellows only"
                )
            }
            val yellowLetters = guesses.indices.flatMap { gi ->
                (0..4).filter { pos -> rows[gi][pos] == 1 }
                    .map { pos -> guesses[gi][pos] }
            }.toSet()
            if (yellowLetters.size != 3) {
                fail(
                    "error: $role: board floats " +
                        pyList(yellowLetters.sorted().map { it.toString() }) +
                        ", not three letters"
                )
            }
            val candidates = pool.filter { w ->
                guesses.all {
                    feedbackString(it, w) == feedbackString(it, answer)
                }
            }.toSet()
            val named = setOf(answer) + others
            if (candidates != named) {
                fail(
                    "error: $role: board's candidate set is " +
                        pyList(candidates.sorted().map { it.uppercase() }) +
                        " but the back names " +
                        pyList(named.sorted().map { it.uppercase() })
                )
            }
            add(
                role,
                boardFront(answer, guesses, "What's the next guess?"),
                wrap(
                    bodyDiv(
                        "<b>${answer.uppercase()}</b> &mdash; also " +
                            "consistent: " +
                            others.joinToString(", ") { it.uppercase() } +
                            "."
                    )
                ),
            )
        }

        // -------------------------------------------------------
        // Assemble.
        //
        // 100 cards: 13 mnemonic (12 ladder rungs + the full
        // text), 5 chant (4 ladder rungs + full recall), 12
        // guess-2 table, 17 chant drills, 5 doubles (the before-Y
        // rule card + 4 boards), 16 ending-pair scan (3
        // first-letter chunk rungs + the first-letters recall +
        // 12 seconds cards), 24 ending-pair drills, 8 placement
        // drills.
        if (notes.size != 100) {
            fail("error: deck has ${notes.size} notes, expected 100")
        }
        return notes
    }
}
