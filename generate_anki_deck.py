#!/usr/bin/env python3
"""Generate an Anki deck for the Wordle RAISE lookup table."""

import genanki

# Colors matching Wordle tiles
GREEN = "#6aaa64"
YELLOW = "#c9b458"
GRAY = "#787c7e"

def tile_html(letter, color):
    """Render a single Wordle tile as HTML."""
    return (
        f'<span style="display:inline-block;width:62px;height:62px;'
        f"background-color:{color};color:white;font-weight:bold;"
        f'font-size:32px;line-height:62px;text-align:center;'
        f'margin:2px;border-radius:4px;font-family:Arial,sans-serif;">'
        f"{letter}</span>"
    )

def make_front(word, colors):
    """Build the front HTML: the word RAISE with colored tiles."""
    tiles = "".join(tile_html(ch, c) for ch, c in zip(word, colors))
    return (
        f'<div style="text-align:center;padding:20px;">'
        f'<div style="font-size:16px;color:#555;margin-bottom:12px;">'
        f"What's your next guess?</div>"
        f"{tiles}</div>"
    )

def make_back(answer):
    """Build the back HTML: the answer word."""
    return (
        f'<div style="text-align:center;padding:20px;">'
        f'<span style="font-size:48px;font-weight:bold;'
        f'font-family:Arial,sans-serif;letter-spacing:8px;">'
        f"{answer}</span></div>"
    )

# Define the 12 lookup-table entries: (colors for R-A-I-S-E, answer)
entries = [
    ([GRAY, GRAY, GRAY, GRAY, GRAY],    "CLOTH"),
    ([GRAY, GRAY, GRAY, GRAY, YELLOW],  "OLDEN"),
    ([GRAY, GRAY, YELLOW, GRAY, GRAY],  "PILOT"),
    ([YELLOW, GRAY, GRAY, GRAY, GRAY],  "COURT"),
    ([YELLOW, GRAY, GRAY, GRAY, YELLOW],"DETER"),
    ([GRAY, YELLOW, GRAY, GRAY, GRAY],  "FLOAT"),
    ([GRAY, GREEN, GRAY, GRAY, GRAY],   "TANGY"),
    ([GRAY, GRAY, GRAY, YELLOW, GRAY],  "STUNK"),
    ([YELLOW, YELLOW, GRAY, GRAY, GRAY],"ADORN"),
    ([GRAY, YELLOW, GRAY, GRAY, YELLOW],"CLEAT"),
    ([GRAY, GRAY, GRAY, GRAY, GREEN],   "LUNGE"),
    ([GRAY, GRAY, GREEN, GRAY, GRAY],   "GLINT"),
]

# Stable random IDs for the model and deck
model = genanki.Model(
    1607392319,
    "Wordle Lookup Table",
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

deck = genanki.Deck(2059400110, "Wordle – RAISE Lookup Table")

for colors, answer in entries:
    front = make_front("RAISE", colors)
    back = make_back(answer)
    note = genanki.Note(model=model, fields=[front, back])
    deck.add_note(note)

output_path = "wordle_raise_lookup.apkg"
genanki.Package(deck).write_to_file(output_path)
print(f"Created {output_path} with {len(entries)} cards.")
