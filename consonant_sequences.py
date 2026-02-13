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

    seq_words: dict[str, list[str]] = {}
    for word in words:
        seen = set()
        for seq in find_three_consonant_sequences(word.lower()):
            if seq not in seen:
                seen.add(seq)
                seq_words.setdefault(seq, []).append(word)

    ranked = sorted(seq_words.items(), key=lambda item: len(item[1]), reverse=True)

    with open(OUTPUT_FILE, "w") as f:
        f.write(f"{'Sequence':<12}{'Count':>6}  {'Words'}\n")
        f.write(f"{'-' * 12}{'-' * 6}  {'-' * 40}\n")
        for seq, word_list in ranked:
            f.write(f"{seq:<12}{len(word_list):>6}  {', '.join(word_list)}\n")

    total = sum(len(wl) for _, wl in ranked)
    print(f"Found {len(ranked)} unique three-consonant sequences across {len(words)} words.")
    print(f"Output written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
