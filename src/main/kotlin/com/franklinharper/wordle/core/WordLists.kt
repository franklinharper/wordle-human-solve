package com.franklinharper.wordle.core

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonPrimitive
import java.nio.file.Files
import java.nio.file.Path

/** The two canonical word lists. */
data class WordLists(
    val answers: List<Word>,
    val guesses: List<Word>,
)

object RepoRoot {
    /**
     * The repo root holds the word lists, the deck, strategy.md and
     * games.csv. It is the process working directory in every
     * supported run (run.sh cd's to its own directory first; the
     * Gradle test task sets it explicitly); WORDLE_REPO_ROOT
     * overrides it.
     */
    fun resolve(): Path {
        val override = System.getenv("WORDLE_REPO_ROOT")
        if (!override.isNullOrBlank()) return Path.of(override)
        return Path.of(System.getProperty("user.dir"))
    }
}

fun loadAnswers(repoRoot: Path): List<Word> =
    Files.readAllLines(repoRoot.resolve("answers.txt"))
        .map { it.trim() }
        .filter { it.isNotEmpty() }
        .map { Word(it) }

fun loadAllGuesses(repoRoot: Path): List<Word> {
    val text = Files.readString(repoRoot.resolve("wordle_valid_guesses.json"))
    val array = Json.parseToJsonElement(text).jsonArray
    return array.map { Word(it.jsonPrimitive.content) }
}

fun loadWordLists(repoRoot: Path): WordLists =
    WordLists(loadAnswers(repoRoot), loadAllGuesses(repoRoot))
