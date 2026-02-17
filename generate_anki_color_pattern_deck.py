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
    ([GREEN, GRAY, GRAY, GRAY, GRAY],           "RUDDY"),
    ([GRAY, GREEN, GRAY, GRAY, GRAY],           "TANGY"),
    ([GRAY, GRAY, GRAY, GREEN, GRAY],           "FLOSS"),
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
    # Remaining patterns (sorted by number of candidate words, descending)
    ([GRAY, YELLOW, GRAY, GRAY, GREEN],         "BLADE"),   # 01002  41 cands
    ([YELLOW, GRAY, GRAY, GRAY, GREEN],         "TROPE"),   # 10002  40 cands
    ([YELLOW, YELLOW, GRAY, GRAY, YELLOW],      "ALERT"),   # 11001  34 cands
    ([GRAY, GRAY, GREEN, YELLOW, GRAY],         "STINK"),   # 00210  29 cands
    ([YELLOW, GREEN, GRAY, GRAY, YELLOW],       "TAPER"),   # 12001  28 cands
    ([YELLOW, GRAY, GREEN, GRAY, GRAY],         "PRINT"),   # 10200  28 cands
    ([YELLOW, YELLOW, GRAY, GRAY, GREEN],       "GRACE"),   # 11002  26 cands
    ([GRAY, GREEN, GRAY, GRAY, GREEN],          "CABLE"),   # 02002  26 cands
    ([YELLOW, GREEN, GRAY, GRAY, GRAY],         "PARTY"),   # 12000  26 cands
    ([YELLOW, GRAY, YELLOW, GRAY, YELLOW],      "DINER"),   # 10101  26 cands
    ([GRAY, GRAY, YELLOW, GRAY, GREEN],         "BINGE"),   # 00102  25 cands
    ([GRAY, GRAY, GREEN, GRAY, GREEN],          "UTILE"),   # 00202  23 cands
    ([GRAY, YELLOW, GRAY, GREEN, GRAY],         "SLASH"),   # 01020  22 cands
    ([YELLOW, YELLOW, GRAY, YELLOW, GRAY],      "STRAP"),   # 11010  21 cands
    ([GRAY, GREEN, GRAY, GRAY, YELLOW],         "NAVEL"),   # 02001  20 cands
    ([GRAY, GREEN, GRAY, YELLOW, GRAY],         "SALON"),   # 02010  20 cands
    ([GRAY, GRAY, GRAY, GREEN, GREEN],          "LOOSE"),   # 00022  20 cands
    ([GREEN, GRAY, GRAY, GRAY, YELLOW],         "RULER"),   # 20001  20 cands
    ([GRAY, YELLOW, GRAY, YELLOW, GREEN],       "SKATE"),   # 01012  19 cands
    ([YELLOW, YELLOW, YELLOW, GRAY, GRAY],      "TRAIL"),   # 11100  18 cands
    ([YELLOW, GRAY, GRAY, YELLOW, YELLOW],      "SHEER"),   # 10011  18 cands
    ([YELLOW, GRAY, GREEN, GRAY, GREEN],        "TRIPE"),   # 10202  17 cands
    ([GRAY, GRAY, GRAY, YELLOW, GREEN],         "STONE"),   # 00012  17 cands
    ([GRAY, GRAY, GREEN, GRAY, YELLOW],         "EDICT"),   # 00201  15 cands
    ([GRAY, GRAY, GREEN, YELLOW, GREEN],        "SNIPE"),   # 00212  15 cands
    ([GRAY, GREEN, YELLOW, GRAY, GRAY],         "PANIC"),   # 02100  14 cands
    ([YELLOW, GRAY, GRAY, GREEN, GRAY],         "CRUST"),   # 10020  13 cands
    ([GREEN, YELLOW, GRAY, GRAY, YELLOW],       "RELAY"),   # 21001  13 cands
    ([GRAY, YELLOW, GREEN, GRAY, GRAY],         "AXION"),   # 01200  12 cands
    ([GRAY, YELLOW, GRAY, YELLOW, YELLOW],      "STEAK"),   # 01011  12 cands
    ([YELLOW, GRAY, GREEN, GRAY, YELLOW],       "FRIED"),   # 10201  12 cands
    ([YELLOW, GRAY, GRAY, YELLOW, GREEN],       "SCREE"),   # 10012  10 cands
    ([GRAY, GREEN, GRAY, YELLOW, GREEN],        "CASTE"),   # 02012   9 cands
    ([GRAY, GRAY, GRAY, GREEN, YELLOW],         "CHESS"),   # 00021   9 cands
    ([GRAY, GRAY, GREEN, GREEN, GRAY],          "HOIST"),   # 00220   9 cands
    ([GREEN, GREEN, GRAY, GRAY, GRAY],          "RANDY"),   # 22000   9 cands
    ([GRAY, YELLOW, GRAY, GREEN, GREEN],        "CEASE"),   # 01022   8 cands
    ([YELLOW, YELLOW, GRAY, GREEN, GRAY],       "BRASH"),   # 11020   8 cands
    ([YELLOW, GRAY, GRAY, GREEN, GREEN],        "CURSE"),   # 10022   8 cands
    ([GREEN, GRAY, YELLOW, GRAY, YELLOW],       "RIPER"),   # 20101   8 cands
    ([YELLOW, GRAY, GRAY, GREEN, YELLOW],       "CRESS"),   # 10021   7 cands
    ([GRAY, GREEN, GRAY, GREEN, GRAY],          "SALSA"),   # 02020   7 cands
    ([GRAY, YELLOW, YELLOW, YELLOW, GRAY],      "SLAIN"),   # 01110   7 cands
    ([GRAY, GREEN, GREEN, GRAY, GRAY],          "FAINT"),   # 02200   6 cands
    ([GRAY, GRAY, YELLOW, GREEN, GRAY],         "TIPSY"),   # 00120   6 cands
    ([GREEN, GREEN, YELLOW, GRAY, GRAY],        "RABID"),   # 22100   6 cands
    ([GREEN, GRAY, GRAY, GRAY, GREEN],          "ROGUE"),   # 20002   6 cands
    ([GRAY, YELLOW, GREEN, GRAY, GREEN],        "ALIKE"),   # 01202   5 cands
    ([GRAY, GREEN, YELLOW, YELLOW, GRAY],       "BASIC"),   # 02110   5 cands
    ([GRAY, YELLOW, GRAY, GREEN, YELLOW],       "BEAST"),   # 01021   5 cands
    ([YELLOW, GRAY, GREEN, GREEN, GRAY],        "BRISK"),   # 10220   5 cands
    ([GRAY, GREEN, GRAY, GREEN, GREEN],         "LAPSE"),   # 02022   5 cands
    ([GRAY, GRAY, YELLOW, YELLOW, GREEN],       "SIEGE"),   # 00112   5 cands
    ([YELLOW, YELLOW, GRAY, YELLOW, GREEN],     "SCARE"),   # 11012   5 cands
    ([YELLOW, GRAY, GREEN, YELLOW, GRAY],       "SHIRK"),   # 10210   5 cands
    ([YELLOW, GREEN, GRAY, GRAY, GREEN],        "BARGE"),   # 12002   4 cands
    ([YELLOW, YELLOW, GREEN, GRAY, GRAY],       "BRIAR"),   # 11200   4 cands
    ([YELLOW, GREEN, GREEN, GRAY, GRAY],        "DAIRY"),   # 12200   4 cands
    ([GRAY, GRAY, YELLOW, YELLOW, YELLOW],      "ISLET"),   # 00111   4 cands
    ([YELLOW, GRAY, YELLOW, YELLOW, YELLOW],    "MISER"),   # 10111   4 cands
    ([GREEN, GREEN, GRAY, GRAY, YELLOW],        "RACER"),   # 22001   4 cands
    ([GREEN, GRAY, YELLOW, GRAY, GRAY],         "ROBIN"),   # 20100   4 cands
    ([GREEN, YELLOW, GRAY, GRAY, GRAY],         "ROYAL"),   # 21000   4 cands
    ([YELLOW, YELLOW, GRAY, YELLOW, YELLOW],    "SHEAR"),   # 11011   4 cands
    ([YELLOW, GRAY, YELLOW, YELLOW, GRAY],      "SPRIG"),   # 10110   4 cands
    ([GRAY, YELLOW, YELLOW, GRAY, YELLOW],      "EMAIL"),   # 01101   3 cands
    ([GRAY, GRAY, GREEN, GREEN, GREEN],         "NOISE"),   # 00222   3 cands
    ([GRAY, GREEN, GREEN, GRAY, GREEN],         "NAIVE"),   # 02202   3 cands
    ([GREEN, GRAY, YELLOW, YELLOW, YELLOW],     "RESIN"),   # 20111   3 cands
    ([GRAY, GRAY, GREEN, YELLOW, YELLOW],       "SHIED"),   # 00211   3 cands
    ([YELLOW, YELLOW, GRAY, GREEN, GREEN],      "AROSE"),   # 11022   2 cands
    ([GRAY, GREEN, GREEN, GREEN, GRAY],         "DAISY"),   # 02220   2 cands
    ([YELLOW, GRAY, YELLOW, GRAY, GREEN],       "DIRGE"),   # 10102   2 cands
    ([GRAY, GRAY, GREEN, GREEN, YELLOW],        "EXIST"),   # 00221   2 cands
    ([YELLOW, GREEN, GRAY, GREEN, GRAY],        "HARSH"),   # 12020   2 cands
    ([GRAY, YELLOW, YELLOW, GRAY, GREEN],       "IMAGE"),   # 01102   2 cands
    ([YELLOW, GREEN, YELLOW, GRAY, GRAY],       "NADIR"),   # 12100   2 cands
    ([GREEN, GRAY, GRAY, YELLOW, YELLOW],       "REBUS"),   # 20011   2 cands
    ([GREEN, GRAY, GRAY, GREEN, GREEN],         "REUSE"),   # 20022   2 cands
    ([GREEN, GRAY, YELLOW, GRAY, GREEN],        "RIDGE"),   # 20102   2 cands
    ([YELLOW, GREEN, GRAY, YELLOW, YELLOW],     "SAFER"),   # 12011   2 cands
    ([YELLOW, GREEN, GRAY, YELLOW, GRAY],       "SATYR"),   # 12010   2 cands
    ([YELLOW, GRAY, GREEN, YELLOW, GREEN],      "SHIRE"),   # 10212   2 cands
    ([YELLOW, YELLOW, GREEN, GRAY, GREEN],      "AFIRE"),   # 11202   1 cand
    ([YELLOW, YELLOW, YELLOW, GRAY, YELLOW],    "AIDER"),   # 11101   1 cand
    ([GRAY, YELLOW, YELLOW, YELLOW, GREEN],     "AISLE"),   # 01112   1 cand
    ([GRAY, YELLOW, GREEN, GRAY, YELLOW],       "ALIEN"),   # 01201   1 cand
    ([GRAY, YELLOW, GREEN, GREEN, GRAY],        "AMISS"),   # 01220   1 cand
    ([YELLOW, YELLOW, GREEN, GREEN, GREEN],     "ARISE"),   # 11222   1 cand
    ([GRAY, YELLOW, GREEN, YELLOW, GREEN],      "ASIDE"),   # 01212   1 cand
    ([GRAY, GREEN, GRAY, YELLOW, YELLOW],       "EASEL"),   # 02011   1 cand
    ([YELLOW, GRAY, YELLOW, GREEN, GRAY],       "FIRST"),   # 10120   1 cand
    ([YELLOW, YELLOW, YELLOW, GRAY, GREEN],     "IRATE"),   # 11102   1 cand
    ([YELLOW, GREEN, GRAY, GREEN, GREEN],       "PARSE"),   # 12022   1 cand
    ([GRAY, YELLOW, YELLOW, GREEN, GRAY],       "QUASI"),   # 01120   1 cand
    ([GREEN, GREEN, GREEN, GRAY, GRAY],         "RAINY"),   # 22200   1 cand
    ([GREEN, GREEN, GREEN, GREEN, GREEN],       "RAISE"),   # 22222   1 cand
    ([GREEN, GREEN, GRAY, GRAY, GREEN],         "RANGE"),   # 22002   1 cand
    ([GREEN, GREEN, GRAY, YELLOW, GRAY],        "RASPY"),   # 22010   1 cand
    ([GREEN, GRAY, GREEN, GRAY, YELLOW],        "REIGN"),   # 20201   1 cand
    ([GREEN, GRAY, GREEN, GRAY, GRAY],          "RHINO"),   # 20200   1 cand
    ([GREEN, GRAY, YELLOW, GREEN, GREEN],       "RINSE"),   # 20122   1 cand
    ([GREEN, GRAY, YELLOW, YELLOW, GRAY],       "RISKY"),   # 20110   1 cand
    ([GREEN, YELLOW, YELLOW, GRAY, GRAY],       "RIVAL"),   # 21100   1 cand
    ([GREEN, YELLOW, GRAY, GREEN, GRAY],        "ROAST"),   # 21020   1 cand
    ([GREEN, GRAY, GRAY, GREEN, GRAY],          "ROOST"),   # 20020   1 cand
    ([GREEN, GRAY, GRAY, YELLOW, GRAY],         "RUSTY"),   # 20010   1 cand
    ([GRAY, GREEN, GREEN, YELLOW, GRAY],        "SAINT"),   # 02210   1 cand
    ([GRAY, YELLOW, YELLOW, YELLOW, YELLOW],    "SEPIA"),   # 01111   1 cand
    ([YELLOW, GRAY, GREEN, YELLOW, YELLOW],     "SKIER"),   # 10211   1 cand
    ([YELLOW, YELLOW, YELLOW, YELLOW, GRAY],    "STAIR"),   # 11110   1 cand
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
