"""
Positional pattern analysis for Wordle answers.

Answers questions like "how many answers end in ER?" or
"how many have RE in positions 3-4?" — fast and exact, no hand counting.

Pattern syntax: 5 characters, '_' is a wildcard, a letter must match
that exact position (case-insensitive). Examples:
    "___er"  -> words ending in ER          (141 answers)
    "__re_"  -> RE in positions 3 and 4     (17 answers)
    "s____"  -> words starting with S
    "_a_e_"  -> A in position 2 and E in position 4

Usage:
    python3 patterns.py "__re_" "___er"
    python3 patterns.py --top-bigrams
"""

import sys
from collections import Counter

from analysis import load_answers


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


def report(words: list[str], patterns: list[str], show_examples: int = 8) -> None:
    """Print a count table for several patterns, with example matches."""
    n = len(words)
    print(f"Answer list: {n} words\n")
    print(f"  {'Pattern':<10} {'Count':>6} {'Share':>7}  Examples")
    for pat in patterns:
        matches = match_pattern(words, pat)
        pct = len(matches) / n * 100
        ex = ", ".join(matches[:show_examples])
        if len(matches) > show_examples:
            ex += ", ..."
        print(f"  {pat:<10} {len(matches):>6} {pct:>6.1f}%  {ex}")


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
    answers = load_answers()
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--top-bigrams" in sys.argv:
        print("=== MOST COMMON 2-LETTER COMBOS BY POSITION ===")
        top_bigrams(answers)
    elif args:
        report(answers, args)
    else:
        # Default demo: the question that started this file.
        report(answers, ["___er", "__re_"])
