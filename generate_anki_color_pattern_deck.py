#!/usr/bin/env python3
"""Generate an Anki deck where the front shows color-letter patterns as text.

Instead of visual Wordle tiles, the front of each card shows a compact
text description like "yellow e" or "yellow a green e", listing only
the non-gray letters from the RAISE feedback pattern.
"""

import genanki

# Color constants (matching generate_anki_deck.py)
GREEN = "#6aaa64"
YELLOW = "#c9b458"
GRAY = "#787c7e"

WORD = "RAISE"

# The 12 lookup-table entries: (colors for R-A-I-S-E, answer)
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


def color_name(hex_color):
    """Map hex color to its display name."""
    return {GREEN: "green", YELLOW: "yellow", GRAY: "gray"}[hex_color]


def pattern_text(colors):
    """Build a compact text description of the non-gray letters.

    Examples:
        All gray          -> "all gray"
        Only E yellow     -> "yellow e"
        R and E yellow    -> "yellow r, e"
        A yellow, E green -> "yellow a  green e"
    """
    color_letters = {}
    for letter, color in zip(WORD, colors):
        if color != GRAY:
            if color not in color_letters:
                color_letters[color] = []
            color_letters[color].append(letter.lower())
    if not color_letters:
        return "all gray"
    parts = []
    for color, letters in color_letters.items():
        parts.append(f"{color_name(color)} {', '.join(letters)}")
    return "  ".join(parts)


def colored_span(text, hex_color):
    """Wrap text in a colored span for the HTML card."""
    return f'<span style="color:{hex_color};font-weight:bold;">{text}</span>'


def make_front(colors):
    """Build the front HTML: color-letter pattern as styled text."""
    color_letters = {}
    for letter, color in zip(WORD, colors):
        if color != GRAY:
            if color not in color_letters:
                color_letters[color] = []
            color_letters[color].append(letter.lower())
    if not color_letters:
        description = "all gray"
    else:
        parts = []
        for color, letters in color_letters.items():
            name = color_name(color)
            parts.append(colored_span(f"{name} {', '.join(letters)}", color))
        description = "&nbsp;&nbsp;".join(parts)
    return (
        '<div style="text-align:center;padding:20px;'
        'font-family:Arial,sans-serif;">'
        f'<div style="font-size:36px;letter-spacing:2px;">'
        f"{description}</div></div>"
    )


def make_back(answer):
    """Build the back HTML: the answer word."""
    return (
        '<div style="text-align:center;padding:20px;">'
        '<span style="font-size:48px;font-weight:bold;'
        'font-family:Arial,sans-serif;letter-spacing:8px;">'
        f"{answer}</span></div>"
    )


# Use different IDs from the tile-based deck so both can coexist in Anki
model = genanki.Model(
    1607392320,
    "Wordle Color-Pattern Lookup",
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

deck = genanki.Deck(2059400111, "Wordle – RAISE Color Patterns")

for colors, answer in entries:
    front = make_front(colors)
    back = make_back(answer)
    note = genanki.Note(model=model, fields=[front, back])
    deck.add_note(note)

output_path = "wordle_raise_color_patterns.apkg"
genanki.Package(deck).write_to_file(output_path)
print(f"Created {output_path} with {len(entries)} cards.")
print()
print("Card previews:")
for colors, answer in entries:
    print(f"  {pattern_text(colors):30s} → {answer}")
