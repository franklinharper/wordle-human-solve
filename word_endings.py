#!/usr/bin/env python3
"""Find all 2-letter sequences that occur at the end of words in the Wordle word list."""

import json

WORD_LIST = "wordle_valid_guesses.json"
OUTPUT_FILE = "word_endings.txt"


def main():
    with open(WORD_LIST) as f:
        words = json.load(f)

    endings: dict[str, list[str]] = {}
    for word in words:
        suffix = word[-2:].upper()
        endings.setdefault(suffix, []).append(word.upper())

    ranked = sorted(endings.items(), key=lambda item: len(item[1]), reverse=True)

    with open(OUTPUT_FILE, "w") as f:
        f.write(f"{'Ending':<10}{'Count':>6}  {'Words'}\n")
        f.write(f"{'-' * 10}{'-' * 6}  {'-' * 40}\n")
        for suffix, word_list in ranked:
            f.write(f"{suffix:<10}{len(word_list):>6}  {', '.join(sorted(word_list))}\n")

    print(f"Found {len(ranked)} unique 2-letter endings across {len(words)} words.")
    print(f"Output written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
