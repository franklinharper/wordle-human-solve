package com.franklinharper.wordle.core

/**
 * A Wordle word: exactly five lowercase letters. The type exists so a
 * raw string can never be silently compared against a word, and a
 * pattern digit can never be compared against a tile — the mixups the
 * Python code allowed are compile errors here.
 */
@JvmInline
value class Word(val value: String) {
    init {
        require(value.length == 5 && value.all { it in 'a'..'z' }) {
            "not a wordle word: '$value'"
        }
    }

    operator fun get(index: Int): Char = value[index]

    override fun toString(): String = value

    companion object {
        /** Parse a word from external text (a file line, a CLI argument). */
        fun parse(raw: String): Word = Word(raw.trim().lowercase())
    }
}
