#!/usr/bin/env python3
"""Generate an Anki deck from patterns_sum_lt3.txt.

Front: description
Back: optimal_answer_guess
"""

try:
    import genanki
except ModuleNotFoundError:
    genanki = None

INPUT_PATH = "patterns_sum_lt3.txt"
OUTPUT_PATH = "wordle_patterns_sum_lt3.apkg"
FALLBACK_TSV_PATH = "wordle_patterns_sum_lt3.tsv"


def load_entries(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            description = parts[0].strip()
            optimal_guess = parts[1].strip()
            entries.append((description, optimal_guess))
    return entries


def make_front(description):
    return (
        '<div style="text-align:center;padding:24px;'
        'font-family:Arial,sans-serif;">'
        f'<div style="font-size:38px;font-weight:700;">{description}</div>'
        "</div>"
    )


def make_back(answer):
    return (
        '<div style="text-align:center;padding:24px;'
        'font-family:Arial,sans-serif;">'
        f'<div style="font-size:52px;font-weight:800;letter-spacing:4px;">{answer.upper()}</div>'
        "</div>"
    )


def main():
    entries = load_entries(INPUT_PATH)
    if not entries:
        raise SystemExit(f"No entries found in {INPUT_PATH}")

    if genanki is None:
        with open(FALLBACK_TSV_PATH, "w", encoding="utf-8") as f:
            for description, answer in entries:
                f.write(f"{description}\t{answer}\n")
        print(
            "genanki is not installed; wrote Anki-importable TSV instead: "
            f"{FALLBACK_TSV_PATH} ({len(entries)} cards)"
        )
        return

    model = genanki.Model(
        1607392321,
        "Wordle Pattern Description to Guess",
        fields=[{"name": "Front"}, {"name": "Back"}],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
            }
        ],
    )

    deck = genanki.Deck(2059400112, "Wordle – Pattern to Optimal Guess")

    for description, answer in entries:
        note = genanki.Note(
            model=model,
            fields=[make_front(description), make_back(answer)],
        )
        deck.add_note(note)

    genanki.Package(deck).write_to_file(OUTPUT_PATH)
    print(f"Created {OUTPUT_PATH} with {len(entries)} cards.")


if __name__ == "__main__":
    main()
