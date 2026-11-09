package com.franklinharper.wordle

import com.github.ajalt.clikt.command.SuspendingCliktCommand
import com.github.ajalt.clikt.command.main
import com.github.ajalt.clikt.core.Context
import com.github.ajalt.clikt.core.subcommands

/** Root command: `wordle <subcommand>`. */
class WordleCommand : SuspendingCliktCommand(name = "wordle") {
    override fun help(context: Context): String =
        "Wordle analysis tools: pattern queries, word-list refresh, " +
            "letter/opening analysis, and the Anki deck generator."

    override suspend fun run() = Unit
}

suspend fun main(args: Array<String>) {
    // Print in UTF-8 on every platform: the reports use block/emoji
    // glyphs, and the JVM's default charset follows the OS locale
    // (US-ASCII under a POSIX locale would mangle them to '?').
    System.setOut(java.io.PrintStream(
        java.io.FileOutputStream(java.io.FileDescriptor.out), true,
        Charsets.UTF_8))
    return WordleCommand()
        .subcommands(PatternsCommand(), AnalysisCommand(), FetchCommand(), DeckCommand())
        .main(args)
}
