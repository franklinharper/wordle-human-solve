#!/usr/bin/env python3
"""Generate Frank's "Wordle" Anki deck.

The deck teaches his whole hard-mode system as five blocks:

1. The guess-2 mnemonic, as a ladder over its twelve words.
2. The after-RAISE chant (OTLN - UCY - HDPM - GBF), as a ladder.
3. The guess-2 lookup table: RAISE's feedback row -> the table word.
4. Chant drills on real boards. Every board shown is a legal line
   (RAISE, the table word for its pattern, then answer-list words)
   against a named answer, and each card asks for the first chant
   letter still untested -- and the rest of the chant from there.
   The chant holds exactly the fourteen letters such a board can
   leave first-untested; that is why it stops at F.
5. The doubled-consonant-before-Y rule and four boards that drill it.

Boards are rendered as Wordle tiles. The feedback colours are always
computed from the card's answer, never typed by hand, and every drill
card's answer is asserted against its board before the deck is
written -- a card whose board does not yield its answer fails loudly.

History: this deck replaced "Wordle – Mnemonic and Chant" on
2026-11-04 (Frank's call, as before: delete the old deck, import
this one fresh). New deck ID and GUID namespace.
"""

import genanki
from collections import Counter

DECK_ID = 2057711934
DECK_NAME = "Wordle"
MODEL_ID = 1473829057
GUID_NAMESPACE = "wordle"

# Shared by the card helpers below: the blank that stands in for a
# missing word or chunk, and the separator between the chant's chunks.
# Named constants because each is used in several places -- a card's
# front and back are built from them together, so the two sides can
# never drift apart.
BLANK = "________"
SEPARATOR = " – "


def fb(g, a):
    """Wordle feedback for guess g against answer a, as a list of
    0 (gray), 1 (yellow), 2 (green) -- the standard two-pass rule."""
    r = [0] * 5
    pool = {}
    for i, (x, y) in enumerate(zip(g, a)):
        if x == y:
            r[i] = 2
        else:
            pool[y] = pool.get(y, 0) + 1
    for i, x in enumerate(g):
        if r[i] == 0 and pool.get(x, 0) > 0:
            r[i] = 1
            pool[x] -= 1
    return r


def knowledge(answer, guesses):
    """Hard-mode knowledge state after playing guesses at answer:
    green positions, per-letter minimum counts, exact caps, absent
    letters, and positions each yellow letter is known not to occupy."""
    greens, minc, cap, yf = {}, Counter(), {}, {}
    for g in guesses:
        r = fb(g, answer)
        gc = Counter(g)
        colored = Counter()
        for i, (ch, v) in enumerate(zip(g, r)):
            if v == 2:
                greens[i] = ch
                colored[ch] += 1
            elif v == 1:
                colored[ch] += 1
                yf.setdefault(ch, set()).add(i)
        for ch in gc:
            minc[ch] = max(minc[ch], colored[ch])
            if colored[ch] < gc[ch]:
                cap[ch] = colored[ch]
    absent = {ch for ch, c in cap.items() if c == 0}
    for ch in cap:
        minc[ch] = cap[ch]
    return greens, minc, cap, absent, yf


def legal(word, state):
    """Is word a legal hard-mode guess given the knowledge state?
    Greens pinned, known-present letters included (and never where
    they showed yellow), absent letters never replayed, exact counts
    respected."""
    greens, minc, cap, absent, yf = state
    wc = Counter(word)
    for p, ch in greens.items():
        if word[p] != ch:
            return False
    for ch in absent:
        if wc.get(ch, 0):
            return False
    for ch, mn in minc.items():
        if wc.get(ch, 0) < mn:
            return False
    for ch, cp in cap.items():
        if wc.get(ch, 0) > cp:
            return False
    for ch, positions in yf.items():
        for p in positions:
            if word[p] == ch and greens.get(p) != ch:
                return False
    return True


def wrap(inner):
    return f'<div style="text-align: center;">{inner}</div>'


def prompt_div(text):
    return (f'<div style="font-size: 16px; color: #555; '
            f'margin-bottom: 6px;">{text}</div>')


def body_div(html):
    return f'<div style="font-size: 20px; margin: 4px 0;">{html}</div>'


# Wordle's own tile colours.
TILE_COLORS = {2: "#6aaa64", 1: "#c9b458", 0: "#787c7e"}


def tile_row(word, pattern):
    tiles = []
    for ch, v in zip(word, pattern):
        tiles.append(
            f'<span style="display: inline-block; width: 32px; '
            f'height: 32px; line-height: 32px; text-align: center; '
            f'background: {TILE_COLORS[v]}; color: #ffffff; '
            f'font-weight: bold; font-size: 19px; margin: 1px; '
            f'border-radius: 3px;">{ch.upper()}</span>')
    return "".join(tiles)


def board(answer, guesses):
    """The board for a line of guesses against answer, as tile rows.
    Patterns are computed, never typed."""
    rows = [tile_row(g, fb(g, answer)) for g in guesses]
    return '<div style="margin: 6px 0;">' + "<br>".join(rows) + "</div>"


def board_front(label, answer, guesses, question):
    return wrap(prompt_div(label)
                + board(answer, guesses)
                + body_div(question))


def assert_exactly_once(text, token):
    n = text.count(token)
    if n != 1:
        raise SystemExit(
            f"error: token {token!r} occurs {n} times in the text "
            f"(expected exactly 1)"
        )


notes = []  # (role key, front, back); the role key seeds the note GUID


def add(role, front, back):
    notes.append((role, front, back))


# -------------------------------------------------------------------
# 1. The guess-2 mnemonic as a ladder.
#
# The text: three sentences whose content words are the twelve table
# words, in table order. Each ladder rung shows the text so far and a
# blank for the next word; the back reveals that word, bolded. The
# segments below carry each word's surrounding glue (articles, "and",
# "it,") and the punctuation that closes its sentence.
TEXT = "The tangy olden cloth stunk. The court pilot's cleats glint " \
       "and float. Adorn it, deter it, lunge!"
SEGMENTS = [
    ("The ", "tangy", ""),
    (" ", "olden", ""),
    (" ", "cloth", ""),
    (" ", "stunk", "."),
    (". The ", "court", ""),
    (" ", "pilot's", ""),
    (" ", "cleats", ""),
    (" ", "glint", ""),
    (" and ", "float", "."),
    (". ", "Adorn", ""),
    (" it, ", "deter", ""),
    (" it, ", "lunge", "!"),
]
for _, token, _ in SEGMENTS:
    assert_exactly_once(TEXT, token)

for k, (pre, token, post) in enumerate(SEGMENTS):
    so_far = "".join(p + t for p, t, _ in SEGMENTS[:k])
    front = wrap(prompt_div("Mnemonic &mdash; fill in the blank")
                 + body_div(so_far + pre + BLANK))
    back = wrap(body_div(so_far + pre + f"<b>{token}</b>" + post))
    add(f"mnemonic:ladder:{k + 1}", front, back)

front = wrap(prompt_div("Wordle guess-2 mnemonic")
             + body_div("Recite the whole text."))
back = wrap(body_div("The tangy olden cloth stunk.<br>"
                     "The court pilot's cleats glint and float.<br>"
                     "Adorn it, deter it, lunge!"))
add("mnemonic:full-text", front, back)

# -------------------------------------------------------------------
# 2. The after-RAISE chant as a ladder.
#
# The chant is the letters RAISE doesn't test, ranked by how many
# answers contain them, cut at F: K, W, V and the sub-2% tail have no
# system board that leaves them first-untested, so they are not in
# the chant (Frank's rule, 2026-11-04). CHANT_TEXT is an independent
# literal; the equality check ties it to CHANT_CHUNKS, so editing
# either one alone fails loudly instead of teaching two chants.
CHANT_CHUNKS = ["OTLN", "UCY", "HDPM", "GBF"]
CHANT_TEXT = "OTLN – UCY – HDPM – GBF"
if CHANT_TEXT != SEPARATOR.join(CHANT_CHUNKS):
    raise SystemExit(
        f"error: chant text {CHANT_TEXT!r} does not match its chunks "
        f"{CHANT_CHUNKS!r}"
    )
CHANT = "".join(CHANT_CHUNKS)


def ladder_pair(chunks, k):
    # The front shows the chunks before chunk k, then the blank; the
    # back shows the same chunks plus chunk k, bolded. Later chunks
    # stay hidden -- the ladder only ever asks for the next chunk. The
    # join form keeps k=0 meaningful: just the blank, just the chunk.
    front = wrap(
        prompt_div("After-RAISE chant &mdash; fill in the blank")
        + body_div(SEPARATOR.join(chunks[:k] + [BLANK])))
    back = wrap(body_div(SEPARATOR.join(
        chunks[:k] + [f"<b>{chunks[k]}</b>"])))
    return front, back


front = wrap(prompt_div("After-RAISE chant")
             + body_div("What's the first word of the after-RAISE "
                        "chant?"))
back = wrap(body_div(f"<b>{CHANT_CHUNKS[0]}</b>"))
add("chant:ladder:1", front, back)
for k in range(1, len(CHANT_CHUNKS)):
    front, back = ladder_pair(CHANT_CHUNKS, k)
    add(f"chant:ladder:{k + 1}", front, back)

front = wrap(prompt_div("After-RAISE chant")
             + body_div("Recite the whole chant."))
back = wrap(body_div(CHANT_TEXT)
            + prompt_div("The letters RAISE doesn't test, in the "
                         "order answers use them. Groups of 4-3-4-3."))
add("chant:full", front, back)

# -------------------------------------------------------------------
# 3. The guess-2 lookup table.
#
# Each card shows RAISE's feedback as a tile row and asks for the
# table word; the back names the word and the new letters it tests
# (strategy.md's table, verbatim). The patterns are the digits of
# RAISE's feedback: 0 gray, 1 yellow, 2 green.
ANSWERS = set()
try:
    with open("answers.txt") as fh:
        ANSWERS = {w.strip() for w in fh if len(w.strip()) == 5}
except FileNotFoundError:
    pass
if not ANSWERS:
    raise SystemExit("error: answers.txt not found -- run this "
                     "script from the wordle-human-solve repo root")

TABLE_ROWS = [
    ("00000", "cloth", "C, L, O, T, H"),
    ("00001", "olden", "O, L, D, N"),
    ("00100", "pilot", "P, L, O, T"),
    ("10000", "court", "C, O, U, T"),
    ("10001", "deter", "D, T"),
    ("01000", "float", "F, L, O, T"),
    ("02000", "tangy", "T, N, G, Y"),
    ("00010", "stunk", "T, U, N, K"),
    ("11000", "adorn", "D, O, N"),
    ("01001", "cleat", "C, L, T"),
    ("00002", "lunge", "L, U, N, G"),
    ("00200", "glint", "G, L, N, T"),
]
TABLE = {pattern: word for pattern, word, _ in TABLE_ROWS}

for pattern, word, letters in TABLE_ROWS:
    if word not in ANSWERS:
        raise SystemExit(f"error: table word {word!r} is not an answer")
    if not any("".join(map(str, fb("raise", a))) == pattern
               for a in ANSWERS):
        raise SystemExit(f"error: no answer gives RAISE pattern "
                         f"{pattern}")
    front = wrap(prompt_div("Guess 2")
                 + '<div style="margin: 6px 0;">'
                 + tile_row("raise", [int(d) for d in pattern])
                 + "</div>"
                 + body_div("What's guess 2?"))
    back = wrap(body_div(f"<b>{word.upper()}</b>")
                + prompt_div(f"Tests {letters}"))
    add(f"guess2:{pattern}", front, back)

# -------------------------------------------------------------------
# 4. Chant drills on real boards.
#
# Every board below is a verified system line: RAISE, the table word
# for RAISE's pattern against the answer, then answer-list words,
# each a legal hard-mode guess. The answer to each card is the first
# chant letter the line leaves untested, plus the rest of the chant
# from there (Frank's Q34: drill the run, not the point). One card
# per chant letter: eight designed boards, nine witness boards found
# by the 2026-11-04 system-constrained search.
#
# The CLEAT board differs from the front first designed for it: as
# drafted (E green at 3, A and L both yellow) no answer exists --
# verified by exhaustive filter. The board below keeps everything
# else and has L out instead of yellow.


def first_unguessed(guesses):
    guessed = set("".join(guesses))
    for ch in CHANT.lower():
        if ch not in guessed:
            return ch.upper()
    return None


def remainder(letter):
    """The chant after letter, regrouped by chunk boundaries and
    joined the way the chant is written; None if letter is last."""
    i = CHANT.index(letter)
    if i == len(CHANT) - 1:
        return None
    parts = []
    pos = 0
    for chunk in CHANT_CHUNKS:
        nxt = pos + len(chunk)
        if nxt > i + 1:
            parts.append(CHANT[max(pos, i + 1):nxt])
        pos = nxt
    return SEPARATOR.join(parts)


def chant_answer_divs(letter):
    rest = remainder(letter)
    if rest is None:
        return (body_div(f"<b>{letter}</b>")
                + prompt_div("The last letter of the chant &mdash; "
                             "nothing follows it."))
    return body_div(f"<b>{letter}</b> &mdash; then {rest}")


SCAN_QUESTION = ("What's the first chant letter still alive "
                 "&mdash; and the rest of the chant from there?")

# (role, answer, guesses, target letter)
APPLY_CARDS = [
    ("apply:cloth-gray", "fuzzy", ["raise", "cloth"], "N"),
    ("apply:court", "dryly", ["raise", "court"], "L"),
    ("apply:adorn", "mural", ["raise", "adorn"], "T"),
    ("apply:tangy", "havoc", ["raise", "tangy"], "O"),
    ("apply:pilot", "civil", ["raise", "pilot"], "N"),
    ("apply:cleat", "hyena", ["raise", "cleat"], "O"),
    ("apply:deter", "error", ["raise", "deter"], "O"),
    ("apply:fuzzy-p", "fuzzy", ["raise", "cloth", "bunny", "muddy"],
     "P"),
    ("apply:beefy-u", "beefy", ["raise", "olden", "fetch"], "U"),
    ("apply:aloha-c", "aloha",
     ["raise", "float", "along", "aloud"], "C"),
    ("apply:aback-y", "aback",
     ["raise", "float", "champ", "quack", "knack"], "Y"),
    ("apply:droll-h", "droll",
     ["raise", "court", "brown", "proxy", "drool"], "H"),
    ("apply:buddy-d", "buddy",
     ["raise", "cloth", "bumpy", "buggy", "bunny"], "D"),
    ("apply:foggy-m", "foggy",
     ["raise", "cloth", "bound", "poppy"], "M"),
    ("apply:buggy-g", "buggy",
     ["raise", "cloth", "bumpy", "buddy", "bunny"], "G"),
    ("apply:bobby-b", "bobby",
     ["raise", "cloth", "mound", "foggy", "poppy"], "B"),
    ("apply:fuzzy-f", "fuzzy",
     ["raise", "cloth", "pudgy", "bunny", "mummy"], "F"),
]

for role, answer, guesses, target in APPLY_CARDS:
    if answer not in ANSWERS:
        raise SystemExit(f"error: {role}: {answer!r} is not an answer")
    if guesses[0] != "raise":
        raise SystemExit(f"error: {role}: first guess is not RAISE")
    pattern = "".join(map(str, fb("raise", answer)))
    if pattern in TABLE and len(guesses) > 1 \
            and guesses[1] != TABLE[pattern]:
        raise SystemExit(
            f"error: {role}: guess 2 is {guesses[1]!r}, but the "
            f"table word for {pattern} is {TABLE[pattern]!r}")
    for i, g in enumerate(guesses):
        if g not in ANSWERS:
            raise SystemExit(f"error: {role}: {g!r} is not an answer")
        if g == answer:
            raise SystemExit(f"error: {role}: guess {i + 1} solves "
                             f"the board -- the drill would be over")
        if i > 0 and not legal(g, knowledge(answer, guesses[:i])):
            raise SystemExit(f"error: {role}: guess {i + 1} "
                             f"({g.upper()}) is not a legal hard-mode "
                             f"guess on this board")
    if first_unguessed(guesses) != target:
        raise SystemExit(
            f"error: {role}: board leaves "
            f"{first_unguessed(guesses)} first, not {target}")
    front = board_front("After-RAISE chant &mdash; apply it",
                        answer, guesses, SCAN_QUESTION)
    back = wrap(chant_answer_divs(target))
    add(role, front, back)

# -------------------------------------------------------------------
# 5. The doubled-consonant-before-Y rule.
#
# Frank's rule card text, verbatim, and four boards that drill it.
# Each board's answer doubles its consonant at positions 3-4 before
# the Y -- asserted below, so an example that stops exemplifying
# fails the build.
front = wrap(prompt_div("Doubled consonant before Y")
             + body_div("A word ends in Y. What's the most likely "
                        "shape?"))
back = wrap(body_div("The letter before the Y doubles &mdash; "
                     "_ _ CCY. 28% of Y-ending answers "
                     "(CANNY, TALLY, NUTTY)."))
add("doubles:rule", front, back)

DOUBLES_CARDS = [
    ("doubles:canny", "canny", ["raise", "tangy"],
     "Extend the N into 4: <b>CANNY</b> &mdash; also FANNY, NANNY. "
     "The consonant doubles before Y."),
    ("doubles:dizzy", "dizzy", ["raise", "pilot", "dingy"],
     "Double the Z: <b>DIZZY</b>."),
    ("doubles:tally", "tally", ["raise", "tangy", "tacky"],
     "Double the L: <b>TALLY</b>."),
    ("doubles:happy", "happy", ["raise", "tangy", "wacky"],
     "Double the P: <b>HAPPY</b>."),
]

for role, answer, guesses, back_text in DOUBLES_CARDS:
    if answer not in ANSWERS:
        raise SystemExit(f"error: {role}: {answer!r} is not an answer")
    if not (answer[2] == answer[3] and answer[4] == "y"
            and answer[2] not in "aeiou"):
        raise SystemExit(f"error: {role}: {answer.upper()} is not "
                         f"a _ _ CCY word")
    for i, g in enumerate(guesses):
        if g not in ANSWERS:
            raise SystemExit(f"error: {role}: {g!r} is not an answer")
        if i > 0 and not legal(g, knowledge(answer, guesses[:i])):
            raise SystemExit(f"error: {role}: guess {i + 1} "
                             f"({g.upper()}) is not a legal hard-mode "
                             f"guess on this board")
    front = board_front("Doubled consonant &mdash; apply the rule",
                        answer, guesses,
                        f"What's guess {len(guesses) + 1}?")
    back = wrap(body_div(back_text))
    add(role, front, back)

# -------------------------------------------------------------------
# Assemble the deck.

if len(notes) != 52:
    raise SystemExit(f"error: deck has {len(notes)} notes, "
                     f"expected 52")

model = genanki.Model(
    MODEL_ID,
    "Wordle Card",
    fields=[
        {"name": "Front"},
        {"name": "Back"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Front}}",
            "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
        },
    ],
    css=".card { font-family: arial; font-size: 20px; "
        "text-align: center; color: black; background-color: white; }",
)

deck = genanki.Deck(DECK_ID, DECK_NAME)
deck.description = (
    "Frank's hard-mode Wordle system: the guess-2 mnemonic ladder, "
    "the after-RAISE chant (OTLN - UCY - HDPM - GBF), the guess-2 "
    "table, chant drills on real boards, and the "
    "doubled-consonant-before-Y rule."
)

for role, front, back in notes:
    deck.add_note(genanki.Note(
        model=model,
        fields=[front, back],
        guid=genanki.guid_for(f"{GUID_NAMESPACE}:{role}"),
    ))

genanki.Package(deck).write_to_file("wordle.apkg")
print(f"Wrote wordle.apkg: {len(notes)} cards in deck {DECK_NAME!r}")
