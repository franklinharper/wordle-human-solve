"""
Generate optimal hard-mode second guesses after opener RAISE for feedback
patterns with 0, 1, or 2 total non-gray tiles (green + yellow).
"""

import argparse
from collections import Counter, defaultdict

from analysis import (
    expected_information,
    expected_remaining,
    feedback_to_str,
    filter_candidates,
    load_all_guesses,
    load_answers,
    partition_by_feedback,
)


OPENER = "raise"
TARGET_HIT_COUNTS = {0, 1, 2}


def best_second_guess(candidates, valid_guesses):
    """Pick the guess minimizing expected remaining candidates."""
    best_word = None
    best_exp_rem = float("inf")
    best_info = -1.0
    best_is_candidate = False
    candidate_set = set(candidates)

    for guess in valid_guesses:
        exp_rem = expected_remaining(guess, candidates)
        info = expected_information(guess, candidates)
        is_candidate = guess in candidate_set

        if exp_rem < best_exp_rem:
            best_word = guess
            best_exp_rem = exp_rem
            best_info = info
            best_is_candidate = is_candidate
            continue

        if exp_rem == best_exp_rem:
            if info > best_info:
                best_word = guess
                best_info = info
                best_is_candidate = is_candidate
                continue
            if info == best_info:
                if is_candidate and not best_is_candidate:
                    best_word = guess
                    best_is_candidate = True
                    continue
                if is_candidate == best_is_candidate and guess < best_word:
                    best_word = guess

    return best_word, best_exp_rem, best_info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--guess-pool",
        choices=["all", "answers"],
        default="all",
        help="Second-guess search pool: all valid guesses (default) or answer words only.",
    )
    args = parser.parse_args()

    answers = load_answers()
    all_guesses = load_all_guesses()
    buckets = partition_by_feedback(OPENER, answers)
    guess_pool = all_guesses if args.guess_pool == "all" else answers

    target_patterns = [
        fb
        for fb in buckets
        if sum(fb) in TARGET_HIT_COUNTS and len(buckets[fb]) > 1
    ]
    target_patterns.sort(key=lambda fb: (-len(buckets[fb]), fb))

    print(
        f"Opener: {OPENER.upper()} | Patterns with green+yellow in {sorted(TARGET_HIT_COUNTS)}: "
        f"{len(target_patterns)} | Guess pool: {args.guess_pool}"
    )
    print()

    results = []
    for i, fb in enumerate(target_patterns, start=1):
        candidates = buckets[fb]
        valid_guesses = filter_candidates(guess_pool, OPENER, fb)
        best_word, exp_rem, info = best_second_guess(candidates, valid_guesses)
        results.append((fb, len(candidates), best_word, exp_rem, info))
        print(
            f"[{i:02d}/{len(target_patterns)}] {feedback_to_str(fb)} "
            f"({''.join(str(x) for x in fb)}) "
            f"cands={len(candidates):>3} -> {best_word}"
        )

    print()
    print("Per-pattern optimal second guess:")
    print(
        f"{'Pattern':<8} {'Codes':<6} {'#Cands':>6} {'Best G2':<8} "
        f"{'E[rem]':>7} {'Info':>7}"
    )
    print("-" * 52)
    for fb, n_cands, word, exp_rem, info in results:
        print(
            f"{feedback_to_str(fb):<8} {''.join(str(x) for x in fb):<6} {n_cands:>6} "
            f"{word:<8} {exp_rem:>7.2f} {info:>7.3f}"
        )

    usage = Counter(word for _, _, word, _, _ in results)
    covered_words = defaultdict(int)
    for _, n_cands, word, _, _ in results:
        covered_words[word] += n_cands

    print()
    print("Optimal word list (deduplicated):")
    for word, count in usage.most_common():
        print(f"  {word}: used by {count:>2} patterns, covers {covered_words[word]:>3} answers")


if __name__ == "__main__":
    main()
