"""
First-principles Wordle analysis toolkit.

Core idea: Wordle is an information-gathering problem. Each guess partitions
the remaining candidates by the feedback pattern it produces. The best guess
is the one whose partition is most uniform (maximizes expected information gain).

In hard mode, every guess must be consistent with all prior feedback, so the
guess pool shrinks along with the candidate pool.
"""

import json
import math
from collections import Counter
from typing import Optional


def load_answers(path="answers.txt"):
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


def load_all_guesses(path="wordle_valid_guesses.json"):
    with open(path) as f:
        return json.load(f)


# --- Feedback computation ---
# Encode feedback as a tuple of (0=gray, 1=yellow, 2=green) for each position.
# This is the "pattern" that a guess produces against a target.

def compute_feedback(guess: str, target: str) -> tuple:
    """Compute Wordle feedback for a guess against a target word.

    Returns a tuple of 5 ints: 0=gray, 1=yellow, 2=green.
    Handles duplicate letters correctly per Wordle rules.
    """
    result = [0] * 5
    target_remaining = list(target)

    # Pass 1: find greens
    for i in range(5):
        if guess[i] == target[i]:
            result[i] = 2
            target_remaining[i] = None  # consumed

    # Pass 2: find yellows
    for i in range(5):
        if result[i] == 2:
            continue
        if guess[i] in target_remaining:
            result[i] = 1
            target_remaining[target_remaining.index(guess[i])] = None  # consumed

    return tuple(result)


def feedback_to_str(fb: tuple) -> str:
    """Convert feedback tuple to emoji string for display."""
    symbols = {0: "⬛", 1: "🟨", 2: "🟩"}
    return "".join(symbols[x] for x in fb)


# --- Information theory ---

def partition_by_feedback(guess: str, candidates: list[str]) -> dict[tuple, list[str]]:
    """Partition candidates by the feedback pattern they'd produce for a guess."""
    buckets = {}
    for target in candidates:
        fb = compute_feedback(guess, target)
        if fb not in buckets:
            buckets[fb] = []
        buckets[fb].append(target)
    return buckets


def expected_information(guess: str, candidates: list[str]) -> float:
    """Calculate expected information gain (Shannon entropy) of a guess.

    Higher = better. This measures how evenly the guess splits the candidates.
    """
    n = len(candidates)
    if n <= 1:
        return 0.0

    buckets = partition_by_feedback(guess, candidates)
    entropy = 0.0
    for bucket in buckets.values():
        p = len(bucket) / n
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def expected_remaining(guess: str, candidates: list[str]) -> float:
    """Expected number of remaining candidates after guessing.

    Lower = better. More intuitive than entropy for humans.
    """
    n = len(candidates)
    if n <= 1:
        return 0.0

    buckets = partition_by_feedback(guess, candidates)
    return sum(len(b) * len(b) for b in buckets.values()) / n


def worst_case_remaining(guess: str, candidates: list[str]) -> int:
    """Worst-case (largest) bucket size after guessing."""
    buckets = partition_by_feedback(guess, candidates)
    return max(len(b) for b in buckets.values())


# --- Letter frequency analysis ---

def letter_frequency(words: list[str]) -> Counter:
    """Count letter frequency across all words (each letter counted once per word)."""
    c = Counter()
    for w in words:
        for ch in set(w):  # unique letters per word
            c[ch] += 1
    return c


def positional_letter_frequency(words: list[str]) -> list[Counter]:
    """Count letter frequency at each position (0-4)."""
    pos_counts = [Counter() for _ in range(5)]
    for w in words:
        for i, ch in enumerate(w):
            pos_counts[i][ch] += 1
    return pos_counts


# --- Scoring words ---

def score_word_by_frequency(word: str, freq: Counter, n_words: int) -> float:
    """Score a word by how close its unique letters are to 50% frequency.

    The 50% principle: a letter appearing in 50% of candidates gives maximum
    information (1 bit per letter). Score penalizes deviation from 50%.
    """
    score = 0.0
    seen = set()
    for ch in word:
        if ch in seen:
            continue  # duplicate letters in guess are wasteful for info gathering
        seen.add(ch)
        p = freq[ch] / n_words
        # Information from a binary test (present/absent):
        # H = -p*log2(p) - (1-p)*log2(1-p), maximized at p=0.5
        if 0 < p < 1:
            score += -p * math.log2(p) - (1 - p) * math.log2(1 - p)
    return score


def score_word_positional(word: str, pos_freq: list[Counter], n_words: int) -> float:
    """Score a word using position-specific letter frequencies.

    This accounts for the fact that green feedback (correct position) is
    more constraining than yellow.
    """
    score = 0.0
    for i, ch in enumerate(word):
        p = pos_freq[i][ch] / n_words
        if 0 < p < 1:
            score += -p * math.log2(p) - (1 - p) * math.log2(1 - p)
    return score


# --- Filtering candidates (hard mode) ---

def filter_candidates(candidates: list[str], guess: str, feedback: tuple) -> list[str]:
    """Filter candidates to those consistent with observed feedback.

    This enforces hard mode: the returned list only contains words that
    could still be the answer given the guess and its feedback.
    """
    result = []
    for word in candidates:
        if compute_feedback(guess, word) == feedback:
            result.append(word)
    return result


# --- Top-level analysis ---

def rank_opening_words(answers: list[str], top_n: int = 20,
                       guess_pool: Optional[list[str]] = None) -> list[tuple]:
    """Rank words by expected information gain as opening guess.

    In hard mode, the guess must come from the valid guess pool but we
    evaluate against the answer list.
    """
    if guess_pool is None:
        guess_pool = answers

    results = []
    total = len(guess_pool)
    for i, word in enumerate(guess_pool):
        if (i + 1) % 500 == 0:
            print(f"  Evaluated {i+1}/{total}...")
        info = expected_information(word, answers)
        exp_rem = expected_remaining(word, answers)
        worst = worst_case_remaining(word, answers)
        results.append((word, info, exp_rem, worst))

    results.sort(key=lambda x: -x[1])  # sort by info descending
    return results[:top_n]


if __name__ == "__main__":
    answers = load_answers()
    n = len(answers)
    print(f"Answer list: {n} words")
    print(f"Theoretical minimum info needed: {math.log2(n):.2f} bits")
    print(f"Max info per guess: {math.log2(243):.2f} bits")
    print()

    # Letter frequency analysis
    freq = letter_frequency(answers)
    pos_freq = positional_letter_frequency(answers)

    print("=== LETTER FREQUENCY (% of answer words containing each letter) ===")
    for ch, count in freq.most_common():
        pct = count / n * 100
        bar = "█" * int(pct / 2)
        print(f"  {ch}: {pct:5.1f}% ({count:4d}) {bar}")

    print()
    print("=== POSITIONAL FREQUENCY (top 5 letters per position) ===")
    for i in range(5):
        top5 = pos_freq[i].most_common(5)
        parts = [f"{ch}:{count/n*100:.0f}%" for ch, count in top5]
        print(f"  Position {i+1}: {', '.join(parts)}")

    print()
    print("=== 50% PRINCIPLE: Letters closest to 50% frequency ===")
    print("  (These give maximum information per letter test)")
    by_distance_from_50 = sorted(freq.items(), key=lambda x: abs(x[1]/n - 0.5))
    for ch, count in by_distance_from_50[:10]:
        print(f"  {ch}: {count/n*100:.1f}%")

    print()
    print("=== TOP OPENING WORDS (by expected information, answer-list only) ===")
    print("  Computing... (evaluating all 2309 answer words)")
    top = rank_opening_words(answers, top_n=25)
    print(f"  {'Word':<8} {'Info (bits)':>11} {'E[remaining]':>13} {'Worst case':>11}")
    for word, info, exp_rem, worst in top:
        print(f"  {word:<8} {info:>11.4f} {exp_rem:>13.2f} {worst:>11d}")
