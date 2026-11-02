#!/usr/bin/env python3
"""Generate the Anki deck "Wordle – Mnemonic and Chant".

Two blocks:

  1. The guess-2 mnemonic (Frank's three sentences packing the 12
     lookup words): cloze cards scoped to one sentence, whole-sentence
     recall cards, one full-text recall card. Daily play drills
     applying the words, so there are deliberately no pattern->word
     cards.
  2. The after-RAISE chant (strategy.md Rule 2): a purpose card, a
     cumulative ladder that builds the chant chunk by chunk (each
     card asks only for the next chunk), a full-chant recall card, a
     beyond-the-chant card, and one application card.

History: this deck replaced "Wordle – Guess-2 Mnemonic" on 2026-11-02
(Frank's call: delete the old deck and start fresh). The general
frequency chant's cards were retired at the same time — the
after-RAISE chant is the scan actually used in games. New deck ID and
GUID namespace, so nothing collides with the old deck.
"""

import genanki

# The mnemonic, verbatim as Frank settled it (2026-10-29). Tokens are the
# words exactly as written in the text (hence "pilot's" and "cleats").
TEXT = [
    ("The tangy olden cloth stunk.",
     ["tangy", "olden", "cloth", "stunk"]),
    ("The court pilot's cleats glint and float.",
     ["court", "pilot's", "cleats", "glint", "float"]),
    ("Adorn it, deter it, lunge!",
     ["Adorn", "deter", "lunge"]),
]


def assert_exactly_once(text, token):
    # Fail loudly if a token ever diverges from its text: str.replace
    # would otherwise no-op silently and produce an unblanked cloze card.
    occurrences = text.count(token)
    if occurrences != 1:
        raise SystemExit(
            f"error: token {token!r} occurs {occurrences} times in "
            f"{text!r}; expected exactly once"
        )


for sentence_text, tokens in TEXT:
    for token in tokens:
        assert_exactly_once(sentence_text, token)


def wrap(inner):
    return (
        '<div style="text-align:center;padding:20px;'
        f'font-family:Arial,sans-serif;">{inner}</div>'
    )


def prompt_div(text):
    return (
        f'<div style="font-size:16px;color:#555;margin-bottom:12px;">'
        f"{text}</div>"
    )


def body_div(text):
    return f'<div style="font-size:28px;line-height:1.5;">{text}</div>'


def cloze_pair(text, token, prompt):
    # "________" is the blank that stands in for the missing word.
    blanked = text.replace(token, "________", 1)
    front = wrap(prompt_div(prompt) + body_div(blanked))
    back = wrap(body_div(text.replace(token, f"<b>{token}</b>", 1)))
    return front, back


notes = []

# 1. Cloze cards, interleaved round-robin across the three sentences
# (1st word of each sentence, then 2nd word of each, ...). Grouping one
# sentence's cards together made each too easy -- the neighbouring cards
# give the sentence away -- so consecutive cards always come from
# different sentences. Each note carries a stable key (used for its GUID
# below) naming the card's role, not its wording.
for i in range(max(len(tokens) for _, tokens in TEXT)):
    for sentence_text, tokens in TEXT:
        if i < len(tokens):
            token = tokens[i]
            front, back = cloze_pair(
                sentence_text, token, "Mnemonic &mdash; fill in the blank")
            notes.append((f"cloze:{token}", front, back))

# 2. Whole-sentence recall cards.
for i, (sentence_text, _) in enumerate(TEXT, start=1):
    front = wrap(prompt_div(f"Mnemonic &mdash; sentence {i} of {len(TEXT)}")
                 + body_div("Recite it."))
    back = wrap(body_div(sentence_text))
    notes.append((f"sentence:{i}", front, back))

# 3. Full-text recall card.
full_text = " ".join(s for s, _ in TEXT)
front = wrap(prompt_div("Wordle guess-2 mnemonic")
             + body_div("Recite the whole text."))
back = wrap(body_div(full_text.replace(". ", ".<br>")))
notes.append(("full-text", front, back))

# 4. After-RAISE chant cards. The chant is the letters RAISE doesn't
# test, ordered by how many answers contain them, grouped 4-3-3-3.
# AFTER_TEXT is an independent literal (the same text strategy.md
# carries); the chunks are checked against it with the shared guard,
# so a chunk edited away from the chant fails loudly instead of
# blanking nothing.
AFTER_CHUNKS = ["OTLN", "UCY", "HDP", "MGB"]
AFTER_TEXT = "OTLN – UCY – HDP – MGB"
for chunk in AFTER_CHUNKS:
    assert_exactly_once(AFTER_TEXT, chunk)

# Purpose: what the chant is for, and what the keyboard is for.
front = wrap(prompt_div("After-RAISE chant")
             + body_div("What is the after-RAISE chant for &mdash; and "
                        "what is the keyboard for?"))
back = wrap(body_div("Chant: after RAISE, the order to try untested "
                     "letters in.<br>"
                     "Keyboard: only to check which letters are still "
                     "alive &mdash; unless every chant letter is known "
                     "or dead; then scan the keyboard."))
notes.append(("after:purpose", front, back))

# The ladder. Card 1 asks for the first chunk from nothing; each later
# card shows the chunks so far and blanks only the next one, so the
# learner only ever recalls one new chunk at a time.
front = wrap(prompt_div("After-RAISE chant")
             + body_div("What's the first word of the after-RAISE "
                        "chant?"))
back = wrap(body_div(AFTER_CHUNKS[0]))
notes.append(("after:ladder:1", front, back))


def ladder_pair(chunks, k):
    # Front: the chunks before chunk k, then a blank. Back: the chunks
    # through k, with chunk k bolded. Later chunks stay hidden.
    front = wrap(
        prompt_div("After-RAISE chant &mdash; fill in the blank")
        + body_div(" – ".join(chunks[:k] + ["________"])))
    back = wrap(body_div(" – ".join(
        chunks[:k] + [f"<b>{chunks[k]}</b>"])))
    return front, back


for k in range(1, len(AFTER_CHUNKS)):
    front, back = ladder_pair(AFTER_CHUNKS, k)
    notes.append((f"after:ladder:{k + 1}", front, back))

# Full-chant recall, no scaffold.
front = wrap(prompt_div("After-RAISE chant")
             + body_div("Recite the whole chant."))
back = wrap(body_div(AFTER_TEXT)
            + prompt_div("The letters RAISE doesn't test, ordered by "
                         "how many answers contain them. Groups of "
                         "4, 3, 3, 3."))
notes.append(("after:full", front, back))

# Beyond the chant: what remains once every chant letter is used up.
front = wrap(prompt_div("After-RAISE chant &mdash; beyond the chant")
             + body_div("The chant is exhausted. What remains?"))
back = wrap(body_div("F, K, W, V &mdash; then X, Z, Q, J")
            + prompt_div("X, Z, Q, J are the rarest of all &mdash; "
                         "each in under 2% of answers."))
notes.append(("after:beyond", front, back))

# Application: RAISE, then the guess-2 table's all-gray word CLOTH --
# the chant's first letters die with it, so the drill is skipping
# ahead to the first survivor.
front = wrap(prompt_div("After-RAISE chant &mdash; apply it")
             + body_div("RAISE, then CLOTH &mdash; all gray. Running "
                        "the chant, what's the first letter still "
                        "alive?"))
back = wrap(body_div("N")
            + prompt_div("CLOTH kills O, T, L, C, H &mdash; N is the "
                         "chant's first survivor."))
notes.append(("after:apply", front, back))

# Stable IDs (fixed literals) so re-running this generator and
# re-importing updates the same model/deck in Anki instead of
# duplicating them. Notes likewise get stable GUIDs derived from their
# role keys, so editing a card's text later updates the existing card
# in place (genanki's default GUID hashes the field text, which would
# orphan the old cards).
model = genanki.Model(
    1473829056,
    "Wordle Mnemonic",
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
)

deck = genanki.Deck(2047119305, "Wordle – Mnemonic and Chant")

for key, front, back in notes:
    deck.add_note(genanki.Note(
        model=model,
        fields=[front, back],
        guid=genanki.guid_for("wordle-mnemonic-and-chant", key),
    ))

genanki.Package(deck).write_to_file("wordle_mnemonic_chant.apkg")
print(f"Wrote wordle_mnemonic_chant.apkg with {len(notes)} cards")
