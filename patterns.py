"""
Positional pattern analysis for Wordle answers.

Answers questions like "how many answers end in ER?" or
"how many have RE in positions 3-4?" — fast and exact, no hand counting.

Pattern syntax: 5 characters, '_' is a wildcard, a letter must match
that exact position (case-insensitive). Examples:
    "___er"  -> words ending in ER
    "__re_"  -> RE in positions 3 and 4
    "s____"  -> words starting with S
    "_a_e_"  -> A in position 2 and E in position 4

Every query reports counts over BOTH word lists: the answer list
(words that can actually be the day's answer) and the valid-guess list
(everything Wordle accepts as a guess).

Usage:
    python3 patterns.py "__re_" "___er"
    python3 patterns.py --top-bigrams
"""

import sys
from collections import Counter

from analysis import load_answers, load_all_guesses


def match_pattern(words: list[str], pattern: str) -> list[str]:
    """Return the words matching a 5-char pattern ('_' = wildcard)."""
    pattern = pattern.lower()
    if len(pattern) != 5 or any(c != "_" and not c.isalpha() for c in pattern):
        raise ValueError(f"Pattern must be 5 chars of letters/_: {pattern!r}")
    return [w for w in words
            if all(p == "_" or w[i] == p for i, p in enumerate(pattern))]


def count_pattern(words: list[str], pattern: str) -> int:
    """Count words matching a positional pattern."""
    return len(match_pattern(words, pattern))


def report(patterns: list[str], show_examples: int = 6) -> None:
    """Print a count table for patterns over both the answer and guess lists."""
    answers = load_answers()
    guesses = load_all_guesses()
    na, ng = len(answers), len(guesses)
    print(f"Valid answers: {na} words | Valid guesses: {ng} words\n")
    print(f"  {'Pattern':<10}{'Valid answers':>20}{'Valid guesses':>18}")
    for pat in patterns:
        ma = match_pattern(answers, pat)
        mg = match_pattern(guesses, pat)
        print(f"  {pat:<10}{len(ma):>12} ({len(ma) / na * 100:4.1f}%)"
              f"{len(mg):>9} ({len(mg) / ng * 100:4.1f}%)")
    print()
    for pat in patterns:
        ma = match_pattern(answers, pat)
        mg = match_pattern(guesses, pat)
        ea = ", ".join(ma[:show_examples])
        eg = ", ".join(mg[:show_examples])
        if len(ma) > show_examples:
            ea += ", ..."
        if len(mg) > show_examples:
            eg += ", ..."
        print(f"  {pat} valid answers: {ea}")
        print(f"  {pat} valid guesses: {eg}")


def positional_bigram_counts(words: list[str]) -> dict[tuple[int, str], int]:
    """Count every 2-letter combo at each adjacent position pair.

    Returns {(start_pos_0based, bigram): count}. E.g. (3, 'er') is the
    count of answers ending in ER; (2, 're') is RE in positions 3-4.
    """
    counts: Counter = Counter()
    for w in words:
        for i in range(4):
            counts[(i, w[i:i + 2])] += 1
    return counts


def top_bigrams(words: list[str], top_n: int = 10) -> None:
    """Print the most common 2-letter combos per position pair."""
    counts = positional_bigram_counts(words)
    n = len(words)
    for i in range(4):
        pairs = sorted(((bg, c) for (pos, bg), c in counts.items() if pos == i),
                       key=lambda x: -x[1])[:top_n]
        cells = "  ".join(f"{bg}:{c}" for bg, c in pairs)
        print(f"  Positions {i + 1}-{i + 2}: {cells}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--top-bigrams" in sys.argv:
        print("=== MOST COMMON 2-LETTER COMBOS BY POSITION: ANSWERS ===")
        top_bigrams(load_answers())
        print()
        print("=== MOST COMMON 2-LETTER COMBOS BY POSITION: VALID GUESSES ===")
        top_bigrams(load_all_guesses())
    elif args:
        report(args)
    else:
        # Default demo: the question that started this file.
        report(["___er", "__re_"])
