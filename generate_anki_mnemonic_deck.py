#!/usr/bin/env python3
"""Generate Frank's "Wordle" Anki deck.

The deck teaches the memorized parts of his hard-mode system as seven blocks:

1. The guess-2 mnemonic, as a ladder over its twelve words.
2. The after-RAISE chant (OTLN - UCY - HDPM - GBF), as a ladder.
3. The guess-2 lookup table: RAISE's feedback row -> the table word.
4. Chant drills on real boards. Every board shown is a legal line
   (RAISE, the table word for its pattern, then answer-list words)
   against a named answer, and each card asks for the first chant
   letter still untested -- and the rest of the chant from there.
   The chant holds exactly the fourteen letters such a board can
   leave first-untested; that is why it stops at F.
5. Doubles: the doubled-consonant-before-Y rule, and four
   boards that drill it.
6. The ending-pair scan over the two-consonant endings with a
   non-Y last letter (CH CK - NG NT NK ND - ST SH SS - TH -
   LL LT LD - RT RD RN RK - MP - WN - FF FT - HT - PT - GH),
   memorized in two stages: the twelve first letters in
   three chunks (CNST - LRMW - FHPG) as a ladder, then each
   first letter's second letters.
7. Ending-pair drills: boards whose only consistent completion
   ends in the card's pair; the back names the pair and the word.
8. Placement drills: boards holding three floating yellows after
   RAISE and the table word, with no green tile; the back names
   a next guess and every other consistent candidate.

Boards are rendered as Wordle tiles, and every board front also
carries the QWERTY keyboard under the board, each letter key in
the state the board gives it, as in the real game. The feedback colours are always
computed from the card's answer, never typed by hand, and every drill
card's answer is asserted against its board before the deck is
written -- a card whose board does not yield its answer fails loudly.

History: this deck replaced "Wordle – Mnemonic and Chant" on
2026-11-04 (Frank's call, as before: delete the old deck, import
this one fresh). New deck ID and GUID namespace.
"""

import genanki
from collections import Counter
from typing import NamedTuple

DECK_NAME = "Wordle"

# Shared by the card helpers below: the blank that stands in for a
# missing word or chunk, and the separator between the chant's chunks.
# Named constants because each is used in several places -- a card's
# front and back are built from them together, so the two sides can
# never drift apart.
BLANK = "________"
SEPARATOR = " – "


def feedback(guess, answer):
    """Wordle feedback for a guess against the answer, as a list of
    0 (gray), 1 (yellow), 2 (green) -- the standard two-pass rule."""
    result = [0] * 5
    pool = {}
    for i, (guess_ch, answer_ch) in enumerate(zip(guess, answer)):
        if guess_ch == answer_ch:
            result[i] = 2
        else:
            pool[answer_ch] = pool.get(answer_ch, 0) + 1
    for i, guess_ch in enumerate(guess):
        if result[i] == 0 and pool.get(guess_ch, 0) > 0:
            result[i] = 1
            pool[guess_ch] -= 1
    return result


class KnowledgeState(NamedTuple):
    greens: dict             # position -> letter pinned green there
    min_counts: Counter      # letter -> at least this many copies
    caps: dict               # letter -> exactly this many copies
    absent: set              # letters known not to be in the word
    yellow_forbidden: dict   # letter -> positions it cannot occupy


def knowledge(answer, guesses):
    """The hard-mode knowledge state after playing guesses at the
    answer: what the board has established, in one named bundle."""
    greens, min_counts, caps, yellow_forbidden = {}, Counter(), {}, {}
    for guess in guesses:
        result = feedback(guess, answer)
        guess_counts = Counter(guess)
        colored_counts = Counter()
        for i, (ch, value) in enumerate(zip(guess, result)):
            if value == 2:
                greens[i] = ch
                colored_counts[ch] += 1
            elif value == 1:
                colored_counts[ch] += 1
                yellow_forbidden.setdefault(ch, set()).add(i)
        for ch in guess_counts:
            min_counts[ch] = max(min_counts[ch], colored_counts[ch])
            if colored_counts[ch] < guess_counts[ch]:
                caps[ch] = colored_counts[ch]
    absent = {ch for ch, c in caps.items() if c == 0}
    for ch in caps:
        min_counts[ch] = caps[ch]
    return KnowledgeState(greens, min_counts, caps, absent,
                          yellow_forbidden)


def legal(word, state):
    """Is word a legal hard-mode guess given the knowledge state?
    Greens pinned, known-present letters included (and never where
    they showed yellow), absent letters never replayed, exact counts
    respected."""
    word_counts = Counter(word)
    for pos, ch in state.greens.items():
        if word[pos] != ch:
            return False
    for ch in state.absent:
        if word_counts.get(ch, 0):
            return False
    for ch, minimum in state.min_counts.items():
        if word_counts.get(ch, 0) < minimum:
            return False
    for ch, cap in state.caps.items():
        if word_counts.get(ch, 0) > cap:
            return False
    for ch, positions in state.yellow_forbidden.items():
        for pos in positions:
            if word[pos] == ch and state.greens.get(pos) != ch:
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
    rows = [tile_row(g, feedback(g, answer)) for g in guesses]
    return '<div style="margin: 6px 0;">' + "<br>".join(rows) + "</div>"


# The keyboard under every board (Frank's ask, 2026-11-07): the
# three QWERTY rows as the real game draws them, ENTER and
# backspace included as inert keys. Each letter key takes the
# best state the board gives it -- green beats yellow beats
# dead -- and a letter the board never tested keeps the game's
# light gray for unexplored keys.
KEYBOARD_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
# Wordle's own unexplored-key gray.
KEY_NEUTRAL = "#d3d6da"


def key_span(label, background, color, width):
    return (
        f'<span style="display: inline-block; width: {width}px; '
        f'height: 30px; line-height: 30px; text-align: center; '
        f'background: {background}; color: {color}; '
        f'font-weight: bold; font-size: 13px; margin: 1px; '
        f'border-radius: 3px;">{label}</span>')


def keyboard(answer, guesses):
    best = {}
    for g in guesses:
        for ch, v in zip(g, feedback(g, answer)):
            if v > best.get(ch, -1):
                best[ch] = v
    rows = []
    for row_letters in KEYBOARD_ROWS:
        keys = []
        if row_letters == "zxcvbnm":
            keys.append(key_span("ENTER", KEY_NEUTRAL, "#1a1a1b", 48))
        for ch in row_letters:
            v = best.get(ch)
            if v is None:
                keys.append(key_span(ch.upper(), KEY_NEUTRAL,
                                     "#1a1a1b", 24))
            else:
                keys.append(key_span(ch.upper(), TILE_COLORS[v],
                                     "#ffffff", 24))
        if row_letters == "zxcvbnm":
            keys.append(key_span("⌫", KEY_NEUTRAL, "#1a1a1b", 48))
        rows.append("".join(keys))
    return ('<div style="margin: 6px 0;">' + "<br>".join(rows)
            + "</div>")


def board_front(answer, guesses, question):
    # No front in the deck carries a header (Frank's rule,
    # settled 2026-11-06/07): a header either gives away what
    # the card tests or duplicates the question, and anything
    # worth saying belongs in the question itself.
    return wrap(board(answer, guesses)
                + keyboard(answer, guesses)
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
# blank for the next word; the back shows only the word to add,
# bolded (Frank's rule, 2026-11-09: a ladder back never repeats
# what the front already gave). The segments below carry each
# word's surrounding glue (articles, "and", "it,") and the
# punctuation that closes its sentence.
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
    if k == 0:
        # Rung 1 cannot be a prefix blank: the whole "text so far"
        # is the word "The", which cues nothing. Like the chant's
        # first rung, it is a question card instead -- the question
        # itself supplies the context (Frank's catch, 2026-11-04).
        front = wrap(body_div("What's the first word of the "
                              "mnemonic text?"))
        back = wrap(body_div(f"<b>{token}</b>"))
        add(f"mnemonic:ladder:{k + 1}", front, back)
        continue
    so_far = "".join(p + t for p, t, _ in SEGMENTS[:k])
    front = wrap(body_div(so_far + pre + BLANK)
                 + body_div("What's the next word of the "
                            "mnemonic text?"))
    back = wrap(body_div(f"<b>{token}</b>"))
    add(f"mnemonic:ladder:{k + 1}", front, back)

front = wrap(body_div("Recite the whole mnemonic text."))
back = wrap(body_div(TEXT.replace(". ", ".<br>")))
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


def ladder_pair(chunks, k, question):
    # The front shows the chunks before chunk k, then the blank,
    # then the question -- no header (Frank's rule, 2026-11-07:
    # anything worth saying belongs in the question). The back
    # shows only chunk k, bolded -- the one thing to add
    # (Frank's rule, 2026-11-09: a ladder back never repeats
    # what the front already gave). The join form keeps k=0
    # meaningful on the front: just the blank.
    front = wrap(
        body_div(SEPARATOR.join(chunks[:k] + [BLANK]))
        + body_div(question))
    back = wrap(body_div(f"<b>{chunks[k]}</b>"))
    return front, back


front = wrap(body_div("What's the first word of the after-RAISE "
                      "chant?"))
back = wrap(body_div(f"<b>{CHANT_CHUNKS[0]}</b>"))
add("chant:ladder:1", front, back)
for k in range(1, len(CHANT_CHUNKS)):
    front, back = ladder_pair(
        CHANT_CHUNKS, k,
        "What's the next word of the after-RAISE chant?")
    add(f"chant:ladder:{k + 1}", front, back)

front = wrap(body_div("Recite the whole chant."))
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
with open("answers.txt") as fh:
    ANSWERS = {w.strip() for w in fh if len(w.strip()) == 5}
if not ANSWERS:
    raise SystemExit("error: answers.txt contains no five-letter "
                     "words -- run this script from the "
                     "wordle-human-solve repo root")

# The candidate pool for the drill assertions below: the answer
# list plus the answers Frank has actually met that the fetched
# list still lacks -- it catalogues past answers and lags the
# newest (DRECK, #1966, was deduced as its board's unique
# completion precisely because the list did not contain it).
OBSERVED_ANSWERS = {"dreck", "parch"}
POOL = ANSWERS | OBSERVED_ANSWERS

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
    if not any("".join(map(str, feedback("raise", a))) == pattern
               for a in ANSWERS):
        raise SystemExit(f"error: no answer gives RAISE pattern "
                         f"{pattern}")
    front = wrap('<div style="margin: 6px 0;">'
                 + tile_row("raise", [int(d) for d in pattern])
                 + "</div>"
                 + body_div("What's the next guess?"))
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


SCAN_QUESTION = ("What's the first letter of the after-RAISE "
                 "chant still untested &mdash; and the rest of "
                 "the chant from there?")

def validate_line(role, answer, guesses):
    """The board checks every drill line shares: the answer and
    every guess are answer-list words, and every guess after the
    first is a legal hard-mode guess given the ones before it."""
    if answer not in ANSWERS:
        raise SystemExit(f"error: {role}: {answer!r} is not an answer")
    for i, g in enumerate(guesses):
        if g not in ANSWERS:
            raise SystemExit(f"error: {role}: {g!r} is not an answer")
        if i > 0 and not legal(g, knowledge(answer, guesses[:i])):
            raise SystemExit(
                f"error: {role}: guess {i + 1} ({g.upper()}) is not "
                f"a legal hard-mode guess on this board")


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
    validate_line(role, answer, guesses)
    if guesses[0] != "raise":
        raise SystemExit(f"error: {role}: first guess is not RAISE")
    pattern = "".join(map(str, feedback("raise", answer)))
    if pattern in TABLE and len(guesses) > 1 \
            and guesses[1] != TABLE[pattern]:
        raise SystemExit(
            f"error: {role}: guess 2 is {guesses[1]!r}, but the "
            f"table word for {pattern} is {TABLE[pattern]!r}")
    for i, g in enumerate(guesses):
        if g == answer:
            raise SystemExit(f"error: {role}: guess {i + 1} solves "
                             f"the board -- the drill would be over")
    if first_unguessed(guesses) != target:
        raise SystemExit(
            f"error: {role}: board leaves "
            f"{first_unguessed(guesses)} first, not {target}")
    front = board_front(answer, guesses, SCAN_QUESTION)
    back = wrap(chant_answer_divs(target))
    add(role, front, back)

# -------------------------------------------------------------------
# 5. Doubles: the before-Y rule and four boards that drill it.
#
# The CCY card's question is Frank's, verbatim. (The general
# gray-cap rule has no card -- Frank removed it 2026-11-06; it
# lives in strategy.md.) No doubles card carries a header: any
# header naming the doubles family would give away the very
# thing each card tests (Frank's rule, 2026-11-06).
# Each board's answer doubles its consonant at positions 3-4 before
# the Y -- asserted below, so an example that stops exemplifying
# fails the build. Each back names every word consistent with
# its board (Frank's Q64, 2026-11-07): the doubling family first,
# then the rest -- asserted against the board's computed
# candidate set, so a back that stops being complete fails too.
front = wrap(body_div("When a word ends in Y, what's the most "
                      "likely shape?"))
back = wrap(body_div("The consonant before the Y doubles "
                     "&mdash; _ _ CCY. 28% of Y-ending answers "
                     "(CANNY, TALLY, NUTTY)."))
add("doubles:rule", front, back)


def is_ccy(word):
    return (word[2] == word[3] and word[4] == "y"
            and word[2] not in "aeiou")


# (role, answer, guesses, headline, doubling family, other
# consistent words) -- family and others together with the
# answer must name the board's whole candidate set.
DOUBLES_CARDS = [
    ("doubles:canny", "canny", ["raise", "tangy"],
     "Extend the N into 4:",
     ["fanny", "nanny"],
     ["candy", "dandy", "fancy", "handy", "lanky", "manly"]),
    ("doubles:dizzy", "dizzy", ["raise", "pilot", "dingy"],
     "Double the Z:",
     [],
     []),
    ("doubles:tally", "tally", ["raise", "tangy", "tacky"],
     "Double the L:",
     ["tabby", "taffy", "tatty"],
     []),
    ("doubles:happy", "happy", ["raise", "tangy", "wacky"],
     "Double the P:",
     ["daddy", "dally", "jazzy", "mammy", "paddy"],
     ["badly", "balmy", "madly"]),
]

for role, answer, guesses, headline, family, others in DOUBLES_CARDS:
    validate_line(role, answer, guesses)
    if not is_ccy(answer):
        raise SystemExit(f"error: {role}: {answer.upper()} is not "
                         f"a _ _ CCY word")
    for w in family:
        if not is_ccy(w):
            raise SystemExit(f"error: {role}: family word "
                             f"{w.upper()} is not a _ _ CCY word")
    for w in others:
        if is_ccy(w):
            raise SystemExit(f"error: {role}: {w.upper()} doubles "
                             f"its consonant -- it belongs in the "
                             f"family, not the others")
    candidates = {w for w in POOL
                  if all(feedback(g, w) == feedback(g, answer)
                         for g in guesses)}
    named = {answer} | set(family) | set(others)
    if candidates != named:
        raise SystemExit(
            f"error: {role}: board's candidate set is "
            f"{sorted(w.upper() for w in candidates)} but the "
            f"back names {sorted(w.upper() for w in named)}")
    text = f"{headline} <b>{answer.upper()}</b>"
    if family:
        text += (" &mdash; also "
                 + ", ".join(w.upper() for w in family) + ".")
    else:
        text += "."
    if others:
        text += (" Also consistent: "
                 + ", ".join(w.upper() for w in others) + ".")
    front = board_front(answer, guesses,
                        "What's the next guess?")
    back = wrap(body_div(text))
    add(role, front, back)

# -------------------------------------------------------------------
# 6. The ending-pair scan, memorized in two stages.
#
# When slots 4-5 are both still open, the scan runs the common
# two-consonant endings grouped by first letter (strategy.md,
# Rule 2) instead of hunting letter by letter. PAIR_TEXT is an
# independent literal, tied to PAIR_CHUNKS the same way the
# chant's is, so the two can never drift apart.
#
# Frank's approach (2026-11-09): memorize the scan in two
# stages -- first the twelve first letters in order, then, for
# each first letter, its second letters. Both stages are
# derived from PAIR_CHUNKS, and the reconstruction check below
# ties them back to PAIR_TEXT, so the stages can never drift
# from the scan or from each other. The ladder roles are the
# ones the old group ladder used -- same ladder, same scan --
# so a re-import updates those cards in place.
PAIR_CHUNKS = ["CH CK", "NG NT NK ND", "ST SH SS", "TH",
               "LL LT LD", "RT RD RN RK", "MP", "WN", "FF FT",
               "HT", "PT", "GH"]
PAIR_TEXT = "CH CK – NG NT NK ND – ST SH SS – TH – LL LT LD – " \
            "RT RD RN RK – MP – WN – FF FT – HT – PT – GH"
if PAIR_TEXT != SEPARATOR.join(PAIR_CHUNKS):
    raise SystemExit(
        f"error: pair-scan text {PAIR_TEXT!r} does not match its "
        f"chunks {PAIR_CHUNKS!r}"
    )

PAIR_GROUPS = [chunk.split() for chunk in PAIR_CHUNKS]
FIRST_LETTERS = [group[0][0] for group in PAIR_GROUPS]
SECONDS = {group[0][0]: [pair[1] for pair in group]
           for group in PAIR_GROUPS}
rebuilt = SEPARATOR.join(
    " ".join(first + second for second in SECONDS[first])
    for first in FIRST_LETTERS)
if rebuilt != PAIR_TEXT:
    raise SystemExit(
        f"error: the two stages rebuild {rebuilt!r}, not the "
        f"scan {PAIR_TEXT!r}"
    )

# Stage 1: the first letters, chunked as a ladder (Frank,
# 2026-11-09). The chunks cut the twelve letters 4-4-4 on the
# scan's strength tiers: the four biggest groups, the middle
# four, the tail. FIRST_CHUNKS_TEXT is an independent literal,
# tied to the chunks the same way the chant's text is, and the
# chunks must reassemble into FIRST_LETTERS exactly.
FIRST_CHUNKS = ["CNST", "LRMW", "FHPG"]
FIRST_CHUNKS_TEXT = "CNST – LRMW – FHPG"
if FIRST_CHUNKS_TEXT != SEPARATOR.join(FIRST_CHUNKS):
    raise SystemExit(
        f"error: first-letters text {FIRST_CHUNKS_TEXT!r} does "
        f"not match its chunks {FIRST_CHUNKS!r}"
    )
if "".join(FIRST_CHUNKS) != "".join(FIRST_LETTERS):
    raise SystemExit(
        f"error: first-letter chunks {FIRST_CHUNKS!r} do not "
        f"reassemble into the first letters {FIRST_LETTERS!r}"
    )

front = wrap(body_div("What's the first of the ending-pair "
                      "scan?"))
back = wrap(body_div(f"<b>{FIRST_CHUNKS[0]}</b>"))
add("pairs:ladder:1", front, back)
for k in range(1, len(FIRST_CHUNKS)):
    front, back = ladder_pair(
        FIRST_CHUNKS, k,
        "What's the next chunk of the ending-pair scan?")
    add(f"pairs:ladder:{k + 1}", front, back)

front = wrap(body_div("Recite the ending-pair scan."))
back = wrap(body_div(FIRST_CHUNKS_TEXT))
add("pairs:first-full", front, back)

# Stage 2: for each first letter, its second letters.
for first in FIRST_LETTERS:
    front = wrap(body_div(f"<b>{first}</b>")
                 + body_div("Which second letters follow it in "
                            "the ending-pair scan?"))
    back = wrap(body_div(
        "<b>" + " ".join(SECONDS[first]) + "</b>"))
    add(f"pairs:seconds:{first.lower()}", front, back)

# -------------------------------------------------------------------
# 7. Ending-pair drills, one per pair.
#
# Each board's only consistent completion ends in the card's pair,
# so the front asks simply "What's the next guess?" The scan's
# scope (Frank's grill, 2026-11-07): the 24 most common
# two-consonant endings with a non-Y last letter -- 551 of the
# 633 such answers (87%); Y-endings are the doubles block's
# problem, not this one's. Construction rules, all asserted
# below: guess 2 is the mnemonic's table word; every board
# carries at least one green and one yellow somewhere; and at
# slots 4-5 at most one letter of the pair may be green, and
# only where the system's own line pins it (Frank's Q76 rule:
# where the system prevents a clean board, use the system and
# accept one green). The pinned boards: ST, SH and SS pin S at
# slot 4 from RAISE itself -- those patterns are untabled and
# no table word carries S at slot 4, so their guess 2 is an
# S-word probe; RT, RD, RN and RK pin R at slot 4 (ADORN's,
# COURT's or QUERY's R, played by the system); PT pins T at
# slot 5 (FLOAT's T). Seven boards need a third row before their
# pair is forced: NK, MP, LT, WN, RK, FT, PT. Candidate sets
# are computed against POOL (defined with the answer list,
# section 3).

PAIR_CARDS = [
    ("pairs:ch", "CH", "torch", ["raise", "court"]),
    ("pairs:ck", "CK", "dreck", ["raise", "deter"]),
    ("pairs:ng", "NG", "thong", ["raise", "cloth"]),
    ("pairs:nt", "NT", "blunt", ["raise", "cloth"]),
    ("pairs:nk", "NK", "drunk", ["raise", "court", "gruff"]),
    ("pairs:nd", "ND", "blend", ["raise", "olden"]),
    ("pairs:st", "ST", "angst", ["raise", "stash"]),
    ("pairs:sh", "SH", "awash", ["raise", "amass"]),
    ("pairs:ss", "SS", "abyss", ["raise", "blast"]),
    ("pairs:th", "TH", "berth", ["raise", "deter"]),
    ("pairs:ll", "LL", "atoll", ["raise", "float"]),
    ("pairs:lt", "LT", "fault", ["raise", "tangy", "fatal"]),
    ("pairs:ld", "LD", "guild", ["raise", "glint"]),
    ("pairs:rt", "RT", "abort", ["raise", "adorn"]),
    ("pairs:rd", "RD", "award", ["raise", "adorn"]),
    ("pairs:rn", "RN", "churn", ["raise", "court"]),
    ("pairs:rk", "RK", "clerk", ["raise", "deter", "query"]),
    ("pairs:mp", "MP", "champ", ["raise", "float", "aback"]),
    ("pairs:wn", "WN", "blown", ["raise", "cloth", "blond"]),
    ("pairs:ff", "FF", "snuff", ["raise", "stunk"]),
    ("pairs:ft", "FT", "cleft", ["raise", "olden", "fleck"]),
    ("pairs:ht", "HT", "yacht", ["raise", "tangy"]),
    ("pairs:pt", "PT", "adapt", ["raise", "float", "chant"]),
    ("pairs:gh", "GH", "thigh", ["raise", "glint"]),
]

for role, pair, answer, guesses in PAIR_CARDS:
    s_at_4_exception = pair in ("ST", "SH", "SS")
    if not answer.endswith(pair.lower()):
        raise SystemExit(f"error: {role}: {answer.upper()} does "
                         f"not end in {pair}")
    if answer not in POOL:
        raise SystemExit(f"error: {role}: {answer!r} is not in "
                         f"the candidate pool")
    if guesses[0] != "raise":
        raise SystemExit(f"error: {role}: first guess is not RAISE")
    for i, g in enumerate(guesses):
        if g not in POOL:
            raise SystemExit(f"error: {role}: {g!r} is not in "
                             f"the candidate pool")
        if g == answer:
            raise SystemExit(f"error: {role}: guess {i + 1} solves "
                             f"the board -- the drill would be over")
        if i > 0 and not legal(g, knowledge(answer, guesses[:i])):
            raise SystemExit(
                f"error: {role}: guess {i + 1} ({g.upper()}) is "
                f"not a legal hard-mode guess on this board")
    pattern = "".join(map(str, feedback("raise", answer)))
    if pattern in TABLE:
        if guesses[1] != TABLE[pattern]:
            raise SystemExit(
                f"error: {role}: guess 2 is {guesses[1]!r}, but "
                f"the table word for {pattern} is "
                f"{TABLE[pattern]!r}")
    elif not s_at_4_exception \
            or feedback("raise", answer)[3] != 2:
        raise SystemExit(
            f"error: {role}: RAISE pattern {pattern} is untabled "
            f"but this is not an ST/SH board with S green at 4")
    candidates = {w for w in POOL
                  if all(feedback(g, w) == feedback(g, answer)
                         for g in guesses)}
    if candidates != {answer}:
        raise SystemExit(
            f"error: {role}: board leaves "
            f"{sorted(w.upper() for w in candidates)}, "
            f"not just {answer.upper()}")
    rows = [feedback(g, answer) for g in guesses]
    greens = sum(r.count(2) for r in rows)
    yellows = sum(r.count(1) for r in rows)
    if greens < 1 or yellows < 1:
        raise SystemExit(
            f"error: {role}: board has {greens} greens and "
            f"{yellows} yellows -- every drill board needs at "
            f"least one of each")
    green45 = {g[pos] for g, r in zip(guesses, rows)
               for pos in (3, 4) if r[pos] == 2}
    if len(green45) > 1 or (green45
                            and next(iter(green45))
                            not in pair.lower()):
        raise SystemExit(
            f"error: {role}: greens at slots 4-5 are "
            f"{sorted(green45)} -- at most one letter of the "
            f"pair may be green there, and only where the "
            f"system's own line pins it")
    front = board_front(answer, guesses, "What's the next guess?")
    back = wrap(body_div(f"<b>{pair}</b> &mdash; "
                         f"{answer.upper()}"))
    add(role, front, back)

# -------------------------------------------------------------------
# 8. Placement drills: three floating yellows.
#
# Frank's bottleneck (his LOAMY game, 2026-11-09): after RAISE and
# the table word, three letters are yellow, none is placed, and
# generating the next guess means permuting them into legal slots
# -- the failure mode is grabbing a familiar word that parks a
# yellow in a banned slot. Each board below is frozen at that
# moment: three distinct yellow letters, no green tile anywhere,
# and a candidate set of two to five words over POOL, all named
# on the back so any of them grades as right. Construction rules,
# all asserted below: guess 2 is the mnemonic's table word; the
# board's candidate set is exactly the back's named set.

PLACEMENT_CARDS = [
    ("placement:loamy", "loamy", ["raise", "float"],
     ["aglow", "koala", "polka"]),
    ("placement:dwell", "dwell", ["raise", "olden"],
     ["dwelt"]),
    ("placement:erect", "erect", ["raise", "deter"],
     ["exert"]),
    ("placement:knelt", "knelt", ["raise", "olden"],
     ["newly"]),
    ("placement:logic", "logic", ["raise", "pilot"],
     ["login"]),
    ("placement:beach", "beach", ["raise", "cleat"],
     ["mecca", "peach"]),
    ("placement:dusky", "dusky", ["raise", "stunk"],
     ["husky", "musky"]),
    ("placement:draft", "draft", ["raise", "adorn"],
     ["drama", "drawl", "fraud"]),
]

for role, answer, guesses, others in PLACEMENT_CARDS:
    if answer not in POOL:
        raise SystemExit(f"error: {role}: {answer!r} is not in "
                         f"the candidate pool")
    if guesses[0] != "raise":
        raise SystemExit(f"error: {role}: first guess is not RAISE")
    pattern = "".join(map(str, feedback("raise", answer)))
    if pattern not in TABLE or guesses[1] != TABLE[pattern]:
        raise SystemExit(
            f"error: {role}: guess 2 is {guesses[1]!r}, but the "
            f"table word for {pattern} is "
            f"{TABLE.get(pattern)!r}")
    for i, g in enumerate(guesses):
        if g not in POOL:
            raise SystemExit(f"error: {role}: {g!r} is not in "
                             f"the candidate pool")
        if g == answer:
            raise SystemExit(f"error: {role}: guess {i + 1} solves "
                             f"the board -- the drill would be over")
        if i > 0 and not legal(g, knowledge(answer, guesses[:i])):
            raise SystemExit(
                f"error: {role}: guess {i + 1} ({g.upper()}) is "
                f"not a legal hard-mode guess on this board")
    rows = [feedback(g, answer) for g in guesses]
    if any(v == 2 for row in rows for v in row):
        raise SystemExit(
            f"error: {role}: board has a green tile -- placement "
            f"drills hold floating yellows only")
    yellow_letters = {ch for g, row in zip(guesses, rows)
                      for ch, v in zip(g, row) if v == 1}
    if len(yellow_letters) != 3:
        raise SystemExit(
            f"error: {role}: board floats "
            f"{sorted(yellow_letters)}, not three letters")
    candidates = {w for w in POOL
                  if all(feedback(g, w) == feedback(g, answer)
                         for g in guesses)}
    named = {answer} | set(others)
    if candidates != named:
        raise SystemExit(
            f"error: {role}: board's candidate set is "
            f"{sorted(w.upper() for w in candidates)} but the "
            f"back names {sorted(w.upper() for w in named)}")
    front = board_front(answer, guesses, "What's the next guess?")
    back = wrap(body_div(
        f"<b>{answer.upper()}</b> &mdash; also consistent: "
        + ", ".join(w.upper() for w in others) + "."))
    add(role, front, back)

# -------------------------------------------------------------------
# Assemble the deck.

# 100 cards: 13 mnemonic (12 ladder rungs + the full text),
# 5 chant (4 ladder rungs + full recall), 12 guess-2 table,
# 17 chant drills, 5 doubles (the before-Y rule card + 4 boards),
# 16 ending-pair scan (3 first-letter chunk rungs + the
# first-letters recall + 12 seconds cards), 24 ending-pair
# drills, 8 placement drills.
if len(notes) != 100:
    raise SystemExit(f"error: deck has {len(notes)} notes, "
                     f"expected 100")

# The model ID is arbitrary but permanent: changing it would make
# Anki treat these as a new note type on re-import.
model = genanki.Model(
    1473829057,
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

# The deck ID is arbitrary but permanent: it is this deck's
# identity across re-imports.
deck = genanki.Deck(2057711934, DECK_NAME)
deck.description = (
    "Memorized parts of Frank's hard-mode Wordle system: the "
    "guess-2 mnemonic ladder, the after-RAISE chant "
    "(OTLN - UCY - HDPM - GBF), the guess-2 table, chant drills on "
    "real boards, the doubled-consonant-before-Y rule, and the "
    "ending-pair scan over two-consonant, non-Y endings (ladder "
    "and drills), and placement drills for boards with three "
    "floating yellows."
)

for role, front, back in notes:
    deck.add_note(genanki.Note(
        model=model,
        fields=[front, back],
        # The "wordle" GUID namespace is permanent: it is what
        # makes a re-import update these notes, not duplicate them.
        guid=genanki.guid_for(f"wordle:{role}"),
    ))

genanki.Package(deck).write_to_file("wordle.apkg")
print(f"Wrote wordle.apkg: {len(notes)} cards in deck {DECK_NAME!r}")
