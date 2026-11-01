#!/usr/bin/env python3
"""Generate an Anki deck for memorizing the Wordle guess-2 mnemonic text.

Frank's mnemonic packs the 12 guess-2 lookup words into three sentences.
The deck teaches the text itself as a ladder (daily play already drills
applying the words, so there are deliberately no pattern->word cards):

  1. Cloze cards scoped to one sentence -- one word blanked per card;
     the back is that complete sentence with the word bolded.
  2. Whole-sentence recall cards ("Sentence N of the mnemonic").
  3. One full-text recall card.
  4. Letter-chant cards for the frequency chant in strategy.md
     (EAROT-LISN-CUY): one cloze per chunk, a full-chant recall card,
     a purpose card, and one application card.
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

# Fail loudly if a token ever diverges from its sentence: str.replace
# would otherwise no-op silently and produce an unblanked cloze card.
for sentence_text, tokens in TEXT:
    for token in tokens:
        occurrences = sentence_text.count(token)
        if occurrences != 1:
            raise SystemExit(
                f"error: token {token!r} occurs {occurrences} times in "
                f"{sentence_text!r}; expected exactly once"
            )


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


def cloze_pair(sentence_text, token):
    # "________" is the blank that stands in for the missing word.
    blanked = sentence_text.replace(token, "________", 1)
    front = wrap(
        prompt_div("Mnemonic &mdash; fill in the blank")
        + body_div(blanked)
    )
    back = wrap(body_div(sentence_text.replace(
        token, f"<b>{token}</b>", 1)))
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
            front, back = cloze_pair(sentence_text, token)
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

# 4. Letter-chant cards. The chant is the 12 most common letters across
# all Wordle answers, in frequency order, grouped 5-4-3 so the chunks
# themselves are easy to hold. Same guard as the mnemonic tokens: a
# chunk that diverges from the chant text must fail loudly, not blank
# nothing.
CHANT_CHUNKS = ["EAROT", "LISN", "CUY"]
CHANT_TEXT = " – ".join(CHANT_CHUNKS)
for chunk in CHANT_CHUNKS:
    occurrences = CHANT_TEXT.count(chunk)
    if occurrences != 1:
        raise SystemExit(
            f"error: chunk {chunk!r} occurs {occurrences} times in "
            f"{CHANT_TEXT!r}; expected exactly once"
        )


def chant_cloze_pair(chunk):
    blanked = CHANT_TEXT.replace(chunk, "________", 1)
    front = wrap(
        prompt_div("Letter chant &mdash; fill in the blank")
        + body_div(blanked)
    )
    back = wrap(body_div(CHANT_TEXT.replace(
        chunk, f"<b>{chunk}</b>", 1)))
    return front, back


for chunk in CHANT_CHUNKS:
    front, back = chant_cloze_pair(chunk)
    notes.append((f"chant:cloze:{chunk}", front, back))

# Full-chant recall.
front = wrap(prompt_div("Wordle letter chant")
             + body_div("Recite all 12 letters."))
back = wrap(body_div(CHANT_TEXT)
            + prompt_div("The 12 most common letters in Wordle answers, "
                         "in order. Groups of 5, 4, 3."))
notes.append(("chant:full", front, back))

# Purpose: what the chant is for, and what the keyboard is for.
front = wrap(prompt_div("Wordle letter chant")
             + body_div("What is the chant for &mdash; and what is the "
                        "keyboard for?"))
back = wrap(body_div("Chant: the order to try untested letters in.<br>"
                     "Keyboard: only to check which letters are still "
                     "alive."))
notes.append(("chant:purpose", front, back))

# Application, from a real game (2026-11-01, VIPER): RAISE returned
# R, I, E yellow with A and S dead.
front = wrap(prompt_div("Letter chant &mdash; apply it")
             + body_div("RAISE: R, I, E yellow; A, S dead. Running the "
                        "chant, what are the first four NEW letters to "
                        "try?"))
back = wrap(body_div("O, T, L, N")
            + prompt_div("As in LITER or TILER &mdash; two new letters "
                         "per guess."))
notes.append(("chant:apply", front, back))

# Stable IDs (fixed literals) so re-running this generator and re-importing
# updates the same model/deck in Anki instead of duplicating them. Notes
# likewise get stable GUIDs derived from their role keys, so editing the
# mnemonic text later updates the existing cards in place (genanki's
# default GUID hashes the field text, which would orphan the old cards).
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

deck = genanki.Deck(1903847562, "Wordle – Guess-2 Mnemonic")

for key, front, back in notes:
    deck.add_note(genanki.Note(
        model=model,
        fields=[front, back],
        guid=genanki.guid_for("wordle-guess2-mnemonic", key),
    ))

genanki.Package(deck).write_to_file("wordle_guess2_mnemonic.apkg")
print(f"Wrote wordle_guess2_mnemonic.apkg with {len(notes)} cards")
