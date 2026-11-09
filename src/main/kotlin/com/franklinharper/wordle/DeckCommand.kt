package com.franklinharper.wordle

import com.franklinharper.wordle.core.RepoRoot
import com.franklinharper.wordle.deck.DeckError
import com.franklinharper.wordle.deck.DeckGenerator
import com.franklinharper.wordle.deck.writeApkg
import com.github.ajalt.clikt.command.SuspendingCliktCommand
import com.github.ajalt.clikt.core.Context
import kotlin.system.exitProcess

/** Build the Wordle Anki deck (wordle.apkg) in the repo root. */
class DeckCommand : SuspendingCliktCommand(name = "deck") {
    override fun help(context: Context): String =
        "Generate the Wordle Anki deck (wordle.apkg)."

    override suspend fun run() {
        val repoRoot = RepoRoot.resolve()
        val notes = try {
            DeckGenerator.build(repoRoot)
        } catch (e: DeckError) {
            System.err.println(e.message)
            exitProcess(1)
        }
        writeApkg(notes, repoRoot.resolve("wordle.apkg"))
        println("Wrote wordle.apkg: ${notes.size} cards in deck 'Wordle'")
    }
}
