package com.franklinharper.wordle.deck

import java.math.BigInteger
import java.nio.file.Files
import java.nio.file.Path
import java.security.MessageDigest
import java.sql.DriverManager
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

/**
 * A minimal .apkg writer replicating genanki's output exactly
 * (verified by the equivalence gate against the Python build):
 * the same SQLite schema and col row, the same note GUIDs, the
 * same models/decks JSON. There is no maintained Java/Kotlin
 * genanki equivalent (checked 2026-11-09); this is the port of
 * the parts of genanki this deck uses.
 */

// genanki's base91 table (Anki's own GUID alphabet).
private const val BASE91_TABLE =
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" +
        "!#\$%&()*+,-./:;<=>?@[]^_`{|}~"

/**
 * genanki's guid_for: SHA-256 of the values joined with "__",
 * the first 8 bytes as a big-endian integer, rendered in base91.
 */
fun guidFor(vararg values: String): String {
    val hashStr = values.joinToString("__")
    val digest = MessageDigest.getInstance("SHA-256")
        .digest(hashStr.toByteArray(Charsets.UTF_8))
    var hashInt = BigInteger.ZERO
    for (i in 0..7) {
        hashInt = hashInt.shiftLeft(8)
            .add(BigInteger.valueOf(digest[i].toLong() and 0xFF))
    }
    val base = BigInteger.valueOf(BASE91_TABLE.length.toLong())
    val reversed = StringBuilder()
    var rest = hashInt
    while (rest > BigInteger.ZERO) {
        val (quotient, remainder) = rest.divideAndRemainder(base)
        reversed.append(BASE91_TABLE[remainder.toInt()])
        rest = quotient
    }
    return reversed.reverse().toString()
}

// --- A tiny ordered JSON model, dumped the way Python's
// json.dumps dumps by default (", " and ": " separators,
// ensure_ascii escaping) so the col row's models/decks strings
// match genanki's byte-for-byte.

sealed interface JVal
data class JObj(val entries: List<Pair<String, JVal>>) : JVal
data class JArr(val items: List<JVal>) : JVal
data class JStr(val value: String) : JVal
data class JNum(val value: Long) : JVal
data class JBool(val value: Boolean) : JVal
data object JNull : JVal

fun dumpJson(value: JVal): String {
    val out = StringBuilder()
    writeJson(value, out)
    return out.toString()
}

private fun writeJson(value: JVal, out: StringBuilder) {
    when (value) {
        is JObj -> {
            out.append('{')
            value.entries.forEachIndexed { i, (key, v) ->
                if (i > 0) out.append(", ")
                writeJsonString(key, out)
                out.append(": ")
                writeJson(v, out)
            }
            out.append('}')
        }
        is JArr -> {
            out.append('[')
            value.items.forEachIndexed { i, v ->
                if (i > 0) out.append(", ")
                writeJson(v, out)
            }
            out.append(']')
        }
        is JStr -> writeJsonString(value.value, out)
        is JNum -> out.append(value.value)
        is JBool -> out.append(if (value.value) "true" else "false")
        JNull -> out.append("null")
    }
}

private fun writeJsonString(s: String, out: StringBuilder) {
    out.append('"')
    for (ch in s) {
        when {
            ch == '"' -> out.append("\\\"")
            ch == '\\' -> out.append("\\\\")
            ch == '\n' -> out.append("\\n")
            ch == '\r' -> out.append("\\r")
            ch == '\t' -> out.append("\\t")
            ch == '\b' -> out.append("\\b")
            ch == '\u000C' -> out.append("\\f")
            ch < ' ' || ch > '~' ->
                out.append("\\u%04x".format(ch.code))
            else -> out.append(ch)
        }
    }
    out.append('"')
}

// genanki's fixed collection schema (apkg_schema.py), verbatim.
private val APKG_SCHEMA = """
CREATE TABLE col (
    id              integer primary key,
    crt             integer not null,
    mod             integer not null,
    scm             integer not null,
    ver             integer not null,
    dty             integer not null,
    usn             integer not null,
    ls              integer not null,
    conf            text not null,
    models          text not null,
    decks           text not null,
    dconf           text not null,
    tags            text not null
);
CREATE TABLE notes (
    id              integer primary key,
    guid            text not null,
    mid             integer not null,
    mod             integer not null,
    usn             integer not null,
    tags            text not null,
    flds            text not null,
    sfld            integer not null,
    csum            integer not null,
    flags           integer not null,
    data            text not null
);
CREATE TABLE cards (
    id              integer primary key,
    nid             integer not null,
    did             integer not null,
    ord             integer not null,
    mod             integer not null,
    usn             integer not null,
    type            integer not null,
    queue           integer not null,
    due             integer not null,
    ivl             integer not null,
    factor          integer not null,
    reps            integer not null,
    lapses          integer not null,
    left            integer not null,
    odue            integer not null,
    odid            integer not null,
    flags           integer not null,
    data            text not null
);
CREATE TABLE revlog (
    id              integer primary key,
    cid             integer not null,
    usn             integer not null,
    ease            integer not null,
    ivl             integer not null,
    lastIvl         integer not null,
    factor          integer not null,
    time            integer not null,
    type            integer not null
);
CREATE TABLE graves (
    usn             integer not null,
    oid             integer not null,
    type            integer not null
);
CREATE INDEX ix_notes_usn on notes (usn);
CREATE INDEX ix_cards_usn on cards (usn);
CREATE INDEX ix_revlog_usn on revlog (usn);
CREATE INDEX ix_cards_nid on cards (nid);
CREATE INDEX ix_cards_sched on cards (did, queue, due);
CREATE INDEX ix_revlog_cid on revlog (cid);
CREATE INDEX ix_notes_csum on notes (csum);
"""

// genanki's fixed col row (apkg_col.py), verbatim; the models
// and decks columns start as '{}' and the placeholder deck, and
// are replaced by the updates below, exactly as genanki does.
private val APKG_COL = """
INSERT INTO col VALUES(
    null,
    1411124400,
    1425279151694,
    1425279151690,
    11,
    0,
    0,
    0,
    '{
        "activeDecks": [
            1
        ],
        "addToCur": true,
        "collapseTime": 1200,
        "curDeck": 1,
        "curModel": "1425279151691",
        "dueCounts": true,
        "estTimes": true,
        "newBury": true,
        "newSpread": 0,
        "nextPos": 1,
        "sortBackwards": false,
        "sortType": "noteFld",
        "timeLim": 0
    }',
    '{}',
    '{
        "1": {
            "collapsed": false,
            "conf": 1,
            "desc": "",
            "dyn": 0,
            "extendNew": 10,
            "extendRev": 50,
            "id": 1,
            "lrnToday": [
                0,
                0
            ],
            "mod": 1425279151,
            "name": "Default",
            "newToday": [
                0,
                0
            ],
            "revToday": [
                0,
                0
            ],
            "timeToday": [
                0,
                0
            ],
            "usn": 0
        }
    }',
    '{
        "1": {
            "autoplay": true,
            "id": 1,
            "lapse": {
                "delays": [
                    10
                ],
                "leechAction": 0,
                "leechFails": 8,
                "minInt": 1,
                "mult": 0
            },
            "maxTaken": 60,
            "mod": 0,
            "name": "Default",
            "new": {
                "bury": true,
                "delays": [
                    1,
                    10
                ],
                "initialFactor": 2500,
                "ints": [
                    1,
                    4,
                    7
                ],
                "order": 1,
                "perDay": 20,
                "separate": true
            },
            "replayq": true,
            "rev": {
                "bury": true,
                "ease4": 1.3,
                "fuzz": 0.05,
                "ivlFct": 1,
                "maxIvl": 36500,
                "minSpace": 1,
                "perDay": 100
            },
            "timer": 0,
            "usn": 0
        }
    }',
    '{}'
);
"""

// The model/deck identities are arbitrary but permanent: changing
// them would make Anki treat the package as new on re-import.
const val MODEL_ID = 1473829057L
const val DECK_ID = 2057711934L
const val MODEL_NAME = "Wordle Card"
const val DECK_NAME = "Wordle"

// genanki's Model defaults (DEFAULT_LATEX_PRE / DEFAULT_LATEX_POST).
private const val LATEX_PRE =
    "\\documentclass[12pt]{article}\n" +
        "\\special{papersize=3in,5in}\n" +
        "\\usepackage[utf8]{inputenc}\n" +
        "\\usepackage{amssymb,amsmath}\n" +
        "\\pagestyle{empty}\n" +
        "\\setlength{\\parindent}{0in}\n" +
        "\\begin{document}\n"
private const val LATEX_POST = "\\end{document}"

private const val MODEL_CSS =
    ".card { font-family: arial; font-size: 20px; text-align: center; " +
        "color: black; background-color: white; }"

private const val DECK_DESCRIPTION =
    "Memorized parts of Frank's hard-mode Wordle system: the " +
        "guess-2 mnemonic ladder, the after-RAISE chant " +
        "(OTLN - UCY - HDPM - GBF), the guess-2 table, chant drills on " +
        "real boards, the doubled-consonant-before-Y rule, and the " +
        "ending-pair scan over two-consonant, non-Y endings (ladder " +
        "and drills), and placement drills for boards with three " +
        "floating yellows."

private fun modelJson(timestampSec: Long): JObj = JObj(
    listOf(
        "css" to JStr(MODEL_CSS),
        "did" to JNum(DECK_ID),
        "flds" to JArr(
            listOf("Front", "Back").mapIndexed { ord, name ->
                JObj(
                    listOf(
                        "name" to JStr(name),
                        "ord" to JNum(ord.toLong()),
                        "font" to JStr("Liberation Sans"),
                        "media" to JArr(emptyList()),
                        "rtl" to JBool(false),
                        "size" to JNum(20),
                        "sticky" to JBool(false),
                    )
                )
            }
        ),
        "id" to JStr(MODEL_ID.toString()),
        "latexPost" to JStr(LATEX_POST),
        "latexPre" to JStr(LATEX_PRE),
        "latexsvg" to JBool(false),
        "mod" to JNum(timestampSec),
        "name" to JStr(MODEL_NAME),
        "req" to JArr(
            listOf(
                JArr(
                    listOf(
                        JNum(0), JStr("all"),
                        JArr(listOf(JNum(0))),
                    )
                )
            )
        ),
        "sortf" to JNum(0),
        "tags" to JArr(emptyList()),
        "tmpls" to JArr(
            listOf(
                JObj(
                    listOf(
                        "name" to JStr("Card 1"),
                        "qfmt" to JStr("{{Front}}"),
                        "afmt" to JStr(
                            "{{FrontSide}}<hr id=\"answer\">{{Back}}"),
                        "ord" to JNum(0),
                        "bafmt" to JStr(""),
                        "bqfmt" to JStr(""),
                        "bfont" to JStr(""),
                        "bsize" to JNum(0),
                        "did" to JNull,
                    )
                )
            )
        ),
        "type" to JNum(0),
        "usn" to JNum(-1),
        "vers" to JArr(emptyList()),
    )
)

private fun defaultDeckJson(): JObj = JObj(
    listOf(
        "collapsed" to JBool(false),
        "conf" to JNum(1),
        "desc" to JStr(""),
        "dyn" to JNum(0),
        "extendNew" to JNum(10),
        "extendRev" to JNum(50),
        "id" to JNum(1),
        "lrnToday" to JArr(listOf(JNum(0), JNum(0))),
        "mod" to JNum(1425279151),
        "name" to JStr("Default"),
        "newToday" to JArr(listOf(JNum(0), JNum(0))),
        "revToday" to JArr(listOf(JNum(0), JNum(0))),
        "timeToday" to JArr(listOf(JNum(0), JNum(0))),
        "usn" to JNum(0),
    )
)

private fun deckJson(): JObj = JObj(
    listOf(
        "collapsed" to JBool(false),
        "conf" to JNum(1),
        "desc" to JStr(DECK_DESCRIPTION),
        "dyn" to JNum(0),
        "extendNew" to JNum(0),
        "extendRev" to JNum(50),
        "id" to JNum(DECK_ID),
        "lrnToday" to JArr(listOf(JNum(163), JNum(2))),
        "mod" to JNum(1425278051),
        "name" to JStr(DECK_NAME),
        "newToday" to JArr(listOf(JNum(163), JNum(2))),
        "revToday" to JArr(listOf(JNum(163), JNum(0))),
        "timeToday" to JArr(listOf(JNum(163), JNum(23598))),
        "usn" to JNum(-1),
    )
)

/** One note to write: its role (GUID seed), front and back HTML. */
data class DeckNote(val role: String, val front: String, val back: String)

/** Write the notes as a genanki-identical .apkg at [outFile]. */
fun writeApkg(notes: List<DeckNote>, outFile: Path) {
    val timestampMs = System.currentTimeMillis()
    val timestampSec = timestampMs / 1000
    var nextId = timestampMs

    val dbFile = Files.createTempFile("wordle-deck", ".anki2")
    try {
        DriverManager.getConnection("jdbc:sqlite:${dbFile.toAbsolutePath()}")
            .use { conn ->
                conn.createStatement().use { st ->
                    // JDBC executes one statement per call (unlike
                    // sqlite3's executescript), so run the schema's
                    // statements one by one. The schema is pure DDL
                    // with no semicolons inside literals.
                    for (part in APKG_SCHEMA.split(";")) {
                        if (part.isNotBlank()) st.execute(part)
                    }
                    st.execute(APKG_COL)
                }
                val decksJson = dumpJson(
                    JObj(
                        listOf(
                            "1" to defaultDeckJson(),
                            DECK_ID.toString() to deckJson(),
                        )
                    )
                )
                val modelsJson = dumpJson(
                    JObj(listOf(MODEL_ID.toString() to modelJson(timestampSec)))
                )
                conn.prepareStatement("UPDATE col SET decks = ?")
                    .use { ps ->
                        ps.setString(1, decksJson)
                        ps.executeUpdate()
                    }
                conn.prepareStatement("UPDATE col SET models = ?")
                    .use { ps ->
                        ps.setString(1, modelsJson)
                        ps.executeUpdate()
                    }
                conn.prepareStatement(
                    "INSERT INTO notes VALUES(?,?,?,?,?,?,?,?,?,?,?)"
                ).use { ps ->
                    conn.prepareStatement(
                        "INSERT INTO cards VALUES(?,?,?,?,?,?,?,?,?," +
                            "?,?,?,?,?,?,?,?,?)"
                    ).use { cardPs ->
                        for (note in notes) {
                            val noteId = nextId++
                            ps.setLong(1, noteId)
                            ps.setString(2, guidFor("wordle:${note.role}"))
                            ps.setLong(3, MODEL_ID)
                            ps.setLong(4, timestampSec)
                            ps.setLong(5, -1)
                            ps.setString(6, "  ")
                            ps.setString(
                                7, note.front + "\u001F" + note.back)
                            ps.setString(8, note.front)
                            ps.setLong(9, 0)
                            ps.setLong(10, 0)
                            ps.setString(11, "")
                            ps.executeUpdate()

                            cardPs.setLong(1, nextId++)
                            cardPs.setLong(2, noteId)
                            cardPs.setLong(3, DECK_ID)
                            cardPs.setLong(4, 0)
                            cardPs.setLong(5, timestampSec)
                            cardPs.setLong(6, -1)
                            cardPs.setLong(7, 0)
                            cardPs.setLong(8, 0)
                            cardPs.setLong(9, 0)
                            cardPs.setLong(10, 0)
                            cardPs.setLong(11, 0)
                            cardPs.setLong(12, 0)
                            cardPs.setLong(13, 0)
                            cardPs.setLong(14, 0)
                            cardPs.setLong(15, 0)
                            cardPs.setLong(16, 0)
                            cardPs.setLong(17, 0)
                            cardPs.setString(18, "")
                            cardPs.executeUpdate()
                        }
                    }
                }
            }
        ZipOutputStream(Files.newOutputStream(outFile)).use { zip ->
            zip.putNextEntry(ZipEntry("collection.anki2"))
            Files.copy(dbFile, zip)
            zip.closeEntry()
            zip.putNextEntry(ZipEntry("media"))
            zip.write("{}".toByteArray(Charsets.UTF_8))
            zip.closeEntry()
        }
    } finally {
        Files.deleteIfExists(dbFile)
    }
}
