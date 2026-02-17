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

# The lookup-table entries: (colors for R-A-I-S-E, answer)
entries = [
    ([GRAY, GRAY, GRAY, GRAY, GRAY],            "CLOTH"),
    ([GRAY, GRAY, GRAY, GRAY, YELLOW],          "OLDEN"),
    ([GRAY, GRAY, YELLOW, GRAY, GRAY],          "PILOT"),
    ([YELLOW, GRAY, GRAY, GRAY, GRAY],          "COURT"),
    ([GRAY, YELLOW, GRAY, GRAY, GRAY],          "FLOAT"),
    ([GRAY, GREEN, GRAY, GRAY, GRAY],           "TANGY"),
    ([GRAY, GRAY, GRAY, YELLOW, GRAY],          "STUNK"),
    ([GRAY, GRAY, GRAY, GRAY, GREEN],           "LUNGE"),
    ([GRAY, GRAY, GREEN, GRAY, GRAY],           "GLINT"),
    # Two yellows (sorted by number of candidate words, descending)
    ([YELLOW, GRAY, GRAY, GRAY, YELLOW],        "DETER"),   # R+E, 102 cands
    ([YELLOW, YELLOW, GRAY, GRAY, GRAY],        "ADORN"),   # R+A,  77 cands
    ([GRAY, YELLOW, GRAY, GRAY, YELLOW],        "CLEAT"),   # A+E,  69 cands
    ([GRAY, YELLOW, GRAY, YELLOW, GRAY],        "STALK"),   # A+S,  43 cands
    ([GRAY, GRAY, GRAY, YELLOW, YELLOW],        "SPELT"),   # S+E,  41 cands
    ([GRAY, GRAY, YELLOW, GRAY, YELLOW],        "LINEN"),   # I+E,  35 cands
    ([GRAY, YELLOW, YELLOW, GRAY, GRAY],        "TIDAL"),   # A+I,  34 cands
    ([YELLOW, GRAY, GRAY, YELLOW, GRAY],        "SHORT"),   # R+S,  24 cands
    ([YELLOW, GRAY, YELLOW, GRAY, GRAY],        "DROIT"),   # R+I,  23 cands
    ([GRAY, GRAY, YELLOW, YELLOW, GRAY],        "STOIC"),   # I+S,  21 cands
    ([GRAY, YELLOW, GRAY, YELLOW, GREEN],       "SKATE"),   # A+S+e, 19 cands
    ([YELLOW, GREEN, GRAY, GRAY, YELLOW],       "TAPER"),   # R+E+a, 28 cands
    ([YELLOW, YELLOW, GRAY, GRAY, GREEN],       "GRACE"),   # R+A+e, 26 cands
    ([GREEN, YELLOW, GRAY, GRAY, YELLOW],       "RELAY"),   # A+E+r, 13 cands
    ([YELLOW, GRAY, GREEN, GRAY, YELLOW],       "FRIED"),   # R+E+i, 12 cands
    ([YELLOW, GRAY, GRAY, YELLOW, GREEN],       "SCREE"),   # R+S+e, 10 cands
    ([YELLOW, YELLOW, GRAY, GREEN, GRAY],       "BRASH"),   # R+A+s,  8 cands
    ([GREEN, GRAY, YELLOW, GRAY, YELLOW],       "RIPER"),   # I+E+r,  8 cands
    ([YELLOW, GRAY, GRAY, GREEN, YELLOW],       "CRESS"),   # R+E+s,  7 cands
    ([GRAY, GREEN, YELLOW, YELLOW, GRAY],       "BASIC"),   # I+S yellow, A green, 5 cands
    ([GRAY, YELLOW, GRAY, GREEN, YELLOW],       "BEAST"),   # A+E yellow, S green, 5 cands
    ([GRAY, GRAY, YELLOW, YELLOW, GREEN],       "SIEGE"),   # I+S yellow, E green, 5 cands
    ([YELLOW, GRAY, GREEN, YELLOW, GRAY],       "SHIRK"),   # R+S yellow, I green, 5 cands
    ([YELLOW, YELLOW, GREEN, GRAY, GRAY],       "BRIAR"),   # R+A yellow, I green, 4 cands
    ([GRAY, GRAY, GREEN, YELLOW, YELLOW],       "SHIED"),   # S+E yellow, I green, 3 cands
    ([YELLOW, YELLOW, GRAY, GREEN, GREEN],      "AROSE"),   # R+A+se, 2 cands
    ([YELLOW, GRAY, YELLOW, GRAY, GREEN],       "DIRGE"),   # R+I+e,  2 cands
    ([GRAY, YELLOW, YELLOW, GRAY, GREEN],       "IMAGE"),   # A+I+e,  2 cands
    ([YELLOW, GREEN, YELLOW, GRAY, GRAY],       "NADIR"),   # R+I+a,  2 cands
    ([GREEN, GRAY, GRAY, YELLOW, YELLOW],       "REBUS"),   # S+E+r,  2 cands
    ([YELLOW, GREEN, GRAY, YELLOW, GRAY],       "SATYR"),   # R+S+a,  2 cands
    ([YELLOW, GRAY, GREEN, YELLOW, GREEN],      "SHIRE"),   # R+I+e,  2 cands
    ([YELLOW, YELLOW, GREEN, GRAY, GREEN],      "AFIRE"),   # R+A+ie, 1 cand
    ([GRAY, YELLOW, GREEN, GRAY, YELLOW],       "ALIEN"),   # A+E+i,  1 cand
    ([YELLOW, YELLOW, GREEN, GREEN, GREEN],     "ARISE"),   # R+A+ise,1 cand
    ([GRAY, YELLOW, GREEN, YELLOW, GREEN],      "ASIDE"),   # A+I+se, 1 cand
    ([GRAY, GREEN, GRAY, YELLOW, YELLOW],       "EASEL"),   # S+E+a,  1 cand
    ([YELLOW, GRAY, YELLOW, GREEN, GRAY],       "FIRST"),   # R+I+s,  1 cand
    ([GRAY, YELLOW, YELLOW, GREEN, GRAY],       "QUASI"),   # A+I+s,  1 cand
    ([GREEN, GRAY, YELLOW, YELLOW, GRAY],       "RISKY"),   # I+S+r,  1 cand
    ([GREEN, YELLOW, YELLOW, GRAY, GRAY],       "RIVAL"),   # A+I+r,  1 cand
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
