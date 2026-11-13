package com.franklinharper.wordle.deck

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
 * 9. Frame drills: an untabled RAISE board whose lesson is a
 *    derivation, not a unique completion — float the yellow,
 *    take the chant's head, build round the green; the back
 *    walks that derivation to the recommended guess.
 * 10. Principle drills: a board whose lesson is a general
 *    decision principle — the back names the play the
 *    principle picks, not a unique completion.
 *
 * Each family is built by a builder function on [DeckBuild] in
 * its own file, adding notes to the shared sink; this object
 * only orchestrates them in order.
 *
 * Every drill card's answer is asserted against its board before
 * the deck is written — a card whose board does not yield its
 * answer fails loudly (DeckError, exit 1).
 */

/** A deck build failure: the message is the whole report. */
class DeckError(message: String) : Exception(message)

internal fun fail(message: String): Nothing = throw DeckError(message)

/** A Python-style list repr of uppercase words, for error messages. */
internal fun pyList(items: Collection<String>): String =
    items.joinToString("', '", "['", "']")

object DeckGenerator {

    fun build(repoRoot: Path): List<DeckNote> {
        val b = DeckBuild(repoRoot)
        b.buildMnemonic()
        b.buildChant()
        b.buildTable()
        b.buildApply()
        b.buildDoubles()
        b.buildPairScan()
        b.buildPairDrills()
        b.buildPlacement()
        b.buildFrame()
        b.buildPrinciple()

        // -------------------------------------------------------
        // Assemble.
        //
        // 101 cards: 13 mnemonic (12 ladder rungs + the full
        // text), 5 chant (4 ladder rungs + full recall), 12
        // guess-2 table, 17 chant drills, 4 doubles (the before-Y
        // rule card + 3 boards), 16 ending-pair scan (3
        // first-letter chunk rungs + the first-letters recall +
        // 12 seconds cards), 24 ending-pair drills, 8 placement
        // drills, 1 frame drill, 1 principle drill.
        if (b.notes.size != 101) {
            fail("error: deck has ${b.notes.size} notes, expected 101")
        }
        return b.notes
    }
}
