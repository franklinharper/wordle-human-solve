package com.franklinharper.wordle.core

import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class FeedbackTest {
    @Test
    fun knownBoards() {
        // RAISE against FIRST: the 2026-11-08 game, pattern 10120.
        assertEquals(
            "10120",
            computeFeedback(Word("raise"), Word("first")).digits,
        )
        // RAISE against LOAMY: the table-word pattern 01000.
        assertEquals(
            "01000",
            computeFeedback(Word("raise"), Word("loamy")).digits,
        )
        // RAISE against PRATE: 11002 (R and A yellow, E green).
        assertEquals(
            "11002",
            computeFeedback(Word("raise"), Word("prate")).digits,
        )
        // FLARE against PRATE: 00212 (A and E green, R yellow).
        assertEquals(
            "00212",
            computeFeedback(Word("flare"), Word("prate")).digits,
        )
    }

    @Test
    fun duplicatesConsumeTargetLetters() {
        // EERIE against EXPEL: one E green at 0... E count is capped
        // by the target's two E's: pos0 green, pos1 yellow, pos4 gray.
        assertEquals(
            "21000",
            computeFeedback(Word("eerie"), Word("expel")).digits,
        )
        // A gray copy caps the letter: SASSY against MESSY — S at 2,3
        // green; the pos-0 S is gray because both target S's are used.
        assertEquals(
            "00222",
            computeFeedback(Word("sassy"), Word("messy")).digits,
        )
    }

    @Test
    fun feedbackRoundTrips() {
        for (code in 0..242) {
            val feedback = Feedback(code)
            assertEquals(feedback, Feedback.parse(feedback.digits))
            assertEquals(feedback, Feedback.of(feedback.tiles))
        }
        assertEquals("🟩🟨⬛🟩⬛", Feedback.parse("21020").emoji())
    }

    @Test
    fun wordValidation() {
        assertFailsWith<IllegalArgumentException> { Word("RAISE") }
        assertFailsWith<IllegalArgumentException> { Word("rais") }
        assertFailsWith<IllegalArgumentException> { Word("ra1se") }
        assertEquals(Word("raise"), Word.parse(" RAISE "))
    }
}

class AnalysisTest {
    private val lists = loadWordLists(RepoRoot.resolve())

    @Test
    fun prateGameNarrowsToPrate() {
        // The 2026-11-07 loss: five lines against PRATE leave PRATE
        // as the only candidate. PRATE is a real NYT answer that is
        // missing from answers.txt (a known blind spot, like DRECK
        // and PARCH), so it is added to the candidate pool here.
        val target = Word("prate")
        var candidates = lists.answers + target
        for (guess in listOf("raise", "flare", "trace", "grate", "orate")) {
            val g = Word(guess)
            candidates = filterCandidates(candidates, g, computeFeedback(g, target))
        }
        assertEquals(listOf(Word("prate")), candidates)
    }

    @Test
    fun loamyLineLeavesFour() {
        // RAISE (01000) then FLOAT against LOAMY leaves the set the
        // placement drills were built from.
        var candidates = lists.answers
        val raise = Word("raise")
        candidates = filterCandidates(
            candidates, raise, computeFeedback(raise, Word("loamy")))
        val float = Word("float")
        candidates = filterCandidates(
            candidates, float, computeFeedback(float, Word("loamy")))
        assertEquals(
            setOf(Word("aglow"), Word("koala"), Word("loamy"), Word("polka")),
            candidates.toSet(),
        )
    }

    @Test
    fun expectedRemainingSanity() {
        val candidates = listOf(Word("crane"), Word("crate"), Word("crone"))
        // A candidate guess can never leave more than the set itself.
        val er = expectedRemaining(Word("crane"), candidates)
        assertTrue(er in 1.0..3.0, "expected remaining $er in 1..3")
        assertEquals(3, worstCaseRemaining(Word("zzzzz"), candidates))
    }
}

class PatternsTest {
    @Test
    fun matchOnSyntheticList() {
        val words = listOf("crane", "crate", "crone", "plane")
            .map { Word(it) }
        assertEquals(
            listOf(Word("crane"), Word("crate")),
            matchPattern(words, PositionalPattern.parse("cra_e")),
        )
        assertEquals(
            words,
            matchPattern(words, PositionalPattern.parse("_____")),
        )
        assertFailsWith<IllegalArgumentException> {
            PositionalPattern.parse("cra")
        }
        assertFailsWith<IllegalArgumentException> {
            PositionalPattern.parse("cr4ne")
        }
    }

    @Test
    fun bigramsCountedPerPosition() {
        val words = listOf(Word("crane"), Word("crate"))
        val counts = positionalBigramCounts(words)
        assertEquals(2, counts[0 to "cr"])
        assertEquals(1, counts[3 to "ne"])
        assertEquals(1, counts[3 to "te"])
    }
}

class WordListsTest {
    @Test
    fun realListsLoad() {
        val lists = loadWordLists(RepoRoot.resolve())
        assertTrue(lists.answers.size > 2000, "answers: ${lists.answers.size}")
        assertTrue(lists.guesses.size > 10000, "guesses: ${lists.guesses.size}")
        assertTrue(Word("raise") in lists.answers)
        assertTrue(lists.answers.all { it in lists.guesses })
    }
}
