#!/usr/bin/env python3
"""Generate an Anki deck for memorizing the Wordle guess-2 mnemonic text.

Frank's mnemonic packs the 12 guess-2 lookup words into three sentences.
The deck teaches the text itself as a ladder (daily play already drills
applying the words, so there are deliberately no pattern->word cards):

  1. Cloze cards scoped to one sentence -- one word blanked per card;
     the back is that complete sentence with the word bolded.
  2. Whole-sentence recall cards ("Sentence N of the mnemonic").
  3. One full-text recall card.
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
