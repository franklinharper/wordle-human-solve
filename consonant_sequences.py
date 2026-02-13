#!/usr/bin/env python3
"""Find all three-consonant sequences in the Wordle word list and rank by frequency."""

import json

VOWELS = set("aeiou")
WORD_LIST = "wordle_valid_guesses.json"
OUTPUT_FILE = "three_consonant_sequences.txt"


def is_consonant(ch):
    return ch.isalpha() and ch not in VOWELS


def find_three_consonant_sequences(word):
    """Yield every 3-letter consonant substring found in *word*."""
    seq = []
    for ch in word:
        if is_consonant(ch):
            seq.append(ch)
            if len(seq) >= 3:
                yield "".join(seq[-3:])
        else:
            seq = []


def main():
    with open(WORD_LIST) as f:
        words = json.load(f)

    counts: dict[str, int] = {}
    for word in words:
        for seq in find_three_consonant_sequences(word.lower()):
            counts[seq] = counts.get(seq, 0) + 1

    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)

    with open(OUTPUT_FILE, "w") as f:
        f.write(f"{'Sequence':<12}{'Count':>6}\n")
        f.write(f"{'-' * 12}{'-' * 6}\n")
        for seq, count in ranked:
            f.write(f"{seq:<12}{count:>6}\n")

    print(f"Found {len(ranked)} unique three-consonant sequences across {len(words)} words.")
    print(f"Output written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
