package com.franklinharper.wordle.deck

import com.franklinharper.wordle.core.RepoRoot
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class GuidTest {
    @Test
    fun guidForMatchesGenanki() {
        // Vectors produced by the Python genanki library itself.
        assertEquals("NH23#kXToz", guidFor("wordle:mnemonic:ladder:1"))
        assertEquals("gqPp~IY7)H", guidFor("wordle:chant:full"))
        assertEquals("l~;[1G75mz", guidFor("wordle:pairs:seconds:n"))
        assertEquals("B0{y<>Ao?", guidFor("wordle:placement:loamy"))
    }

    @Test
    fun jsonDumpMatchesPython() {
        val value = JObj(
            listOf(
                "a" to JArr(listOf(JNum(1), JNum(2))),
                "b" to JStr("x\né"),
                "c" to JBool(true),
                "d" to JNull,
            )
        )
        // Python's json.dumps with ensure_ascii: the newline
        // renders as \n and the é as é, separators ", " / ": ".
        val expected =
            "{\"a\": [1, 2], \"b\": \"x\\n\\u00e9\", " +
                "\"c\": true, \"d\": null}"
        assertEquals(expected, dumpJson(value))
    }
}

class KnowledgeTest {
    @Test
    fun loamyBoardState() {
        // The 2026-11-09 LOAMY board after RAISE + FLOAT: A, L, O
        // yellow; ALOHA parks L and O in banned slots (illegal),
        // while LOAMY, COALY, KOALA are legal.
        val state = knowledge("loamy", listOf("raise", "float"))
        assertTrue(legal("loamy", state))
        assertTrue(legal("coaly", state))
        assertTrue(legal("koala", state))
        assertFalse(legal("aloha", state))
        // FLOAT itself replays F, T — both capped at zero by the board.
        assertFalse(legal("float", state))
    }

    @Test
    fun prateBoardPinsGreens() {
        val state = knowledge("prate", listOf("raise"))
        assertEquals(mapOf(4 to 'e'), state.greens)
        assertTrue(legal("orate", state))
        assertFalse(legal("irate", state)) // I is capped at zero
    }
}

class DeckGeneratorTest {
    @Test
    fun buildsAllNotes() {
        val notes = DeckGenerator.build(RepoRoot.resolve())
        assertEquals(103, notes.size)
        assertEquals(103, notes.map { it.role }.toSet().size)
        val byRole = notes.associateBy { it.role }
        assertTrue(byRole.getValue("frame:truce").back.contains("TROPE"))
        assertTrue(byRole.getValue("principle:dicky").back.contains("DICKY"))
        assertFalse(byRole.containsKey("doubles:dizzy"))
        assertTrue(byRole.getValue("placement:loamy").back.contains("LOAMY"))
        assertTrue(byRole.getValue("pairs:seconds:n").back.contains("G T K D"))
        assertTrue(notes.all { it.front.startsWith("<div") })
    }
}
