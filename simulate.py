"""
Hard-mode Wordle strategy simulator.

Simulates playing every possible answer word and measures performance.
Supports pluggable strategies for choosing guesses.
"""

import sys
import time
from collections import Counter
from analysis import (
    load_answers, load_all_guesses,
    compute_feedback, feedback_to_str,
    filter_candidates, partition_by_feedback,
    expected_information, expected_remaining,
    letter_frequency, positional_letter_frequency,
    score_word_by_frequency, score_word_positional
)


def best_guess_by_info(candidates, valid_guesses=None):
    """Pick the guess that maximizes expected information gain.

    In hard mode, valid_guesses are pre-filtered to hard-mode-compatible words.
    If a candidate word ties with a non-candidate, prefer the candidate
    (it might actually be the answer).
    """
    if len(candidates) <= 2:
        return candidates[0]

    pool = valid_guesses if valid_guesses else candidates
    candidate_set = set(candidates)

    best_word = None
    best_info = -1
    best_is_candidate = False

    for word in pool:
        info = expected_information(word, candidates)
        is_cand = word in candidate_set
        # Prefer candidate words at equal info (they could be the answer)
        if info > best_info or (info == best_info and is_cand and not best_is_candidate):
            best_info = info
            best_word = word
            best_is_candidate = is_cand

    return best_word


def best_guess_by_expected_remaining(candidates, valid_guesses=None):
    """Pick the guess that minimizes expected remaining candidates."""
    if len(candidates) <= 2:
        return candidates[0]

    pool = valid_guesses if valid_guesses else candidates
    candidate_set = set(candidates)

    best_word = None
    best_rem = float('inf')

    for word in pool:
        rem = expected_remaining(word, candidates)
        is_cand = word in candidate_set
        if rem < best_rem or (rem == best_rem and is_cand):
            best_rem = rem
            best_word = word

    return best_word


# --- Human-playable heuristic ---

# The key insight: after testing R,A,I,S,E the next most informative
# untested letters are O,T,L,N,U,C,Y,H,D. A human should try to pack
# as many of these into each guess as possible while respecting hard mode.

LETTER_PRIORITY = list("earotilsnucyhdpgmbfkwvxzqj")

def human_heuristic_guess(candidates, all_guesses, tested_letters, green_known, yellow_known):
    """
    Human-simulable heuristic for picking a guess.

    Strategy:
    1. If <=2 candidates, just guess one.
    2. Score each valid candidate by how many high-priority untested letters it contains.
    3. Tiebreak by positional frequency.
    """
    if len(candidates) <= 2:
        return candidates[0]

    # Determine untested letters in priority order
    untested_priority = [ch for ch in LETTER_PRIORITY if ch not in tested_letters]

    # Score each candidate
    n = len(candidates)
    pos_freq = positional_letter_frequency(candidates)

    best_word = None
    best_score = -1

    for word in candidates:  # In hard mode, guess from candidates
        # Count untested high-priority letters (weighted by priority position)
        untested_score = 0
        seen = set()
        for ch in word:
            if ch in seen:
                continue
            seen.add(ch)
            if ch in tested_letters:
                continue
            # Higher priority = lower index = higher score
            try:
                idx = untested_priority.index(ch)
                untested_score += (len(untested_priority) - idx)
            except ValueError:
                pass

        # Add positional frequency bonus
        pos_score = 0
        for i, ch in enumerate(word):
            pos_score += pos_freq[i].get(ch, 0) / n

        # Combined score: untested coverage is primary, positional is tiebreaker
        score = untested_score * 100 + pos_score

        if score > best_score:
            best_score = score
            best_word = word

    return best_word


def play_game(target, strategy, all_answers, all_guesses, opener="raise", max_guesses=6, verbose=False):
    """
    Play a single game of hard-mode Wordle.

    Returns: (n_guesses, guesses_list, solved)
    """
    candidates = list(all_answers)
    guesses = []
    tested_letters = set()
    green_known = [None] * 5
    yellow_known = [set() for _ in range(5)]  # yellow_known[i] = letters known to NOT be at position i

    for turn in range(1, max_guesses + 1):
        if turn == 1:
            guess = opener
        else:
            if strategy == "info":
                # Use candidates as both guess pool and answer pool (hard mode)
                guess = best_guess_by_info(candidates)
            elif strategy == "expected_remaining":
                guess = best_guess_by_expected_remaining(candidates)
            elif strategy == "human":
                guess = human_heuristic_guess(
                    candidates, all_guesses, tested_letters,
                    green_known, yellow_known
                )
            else:
                raise ValueError(f"Unknown strategy: {strategy}")

        feedback = compute_feedback(guess, target)
        guesses.append((guess, feedback))

        if verbose:
            print(f"  Guess {turn}: {guess} → {feedback_to_str(feedback)}")

        # Update tested letters
        for ch in guess:
            tested_letters.add(ch)

        # Update green/yellow knowledge
        for i, (ch, fb) in enumerate(zip(guess, feedback)):
            if fb == 2:
                green_known[i] = ch
            elif fb == 1:
                yellow_known[i].add(ch)

        if feedback == (2, 2, 2, 2, 2):
            return turn, guesses, True

        # Filter candidates
        candidates = filter_candidates(candidates, guess, feedback)

        if len(candidates) == 0:
            if verbose:
                print(f"  ERROR: No candidates remain!")
            return turn, guesses, False

    return max_guesses, guesses, False


def run_simulation(strategy, answers, all_guesses, opener="raise", max_guesses=6, verbose_failures=True):
    """Run the strategy against all answer words."""
    results = []
    failures = []
    start = time.time()

    for i, target in enumerate(answers):
        if (i + 1) % 200 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            eta = (len(answers) - i - 1) / rate
            print(f"  {i+1}/{len(answers)} ({rate:.0f} words/sec, ETA {eta:.0f}s)")

        n_guesses, guesses, solved = play_game(
            target, strategy, answers, all_guesses, opener, max_guesses
        )
        results.append(n_guesses)
        if not solved:
            failures.append((target, guesses))

    elapsed = time.time() - start

    # Statistics
    counter = Counter(results)
    print(f"\n{'='*60}")
    print(f"Strategy: {strategy}, Opener: {opener}")
    print(f"{'='*60}")
    print(f"Total words: {len(answers)}")
    print(f"Solved: {len(answers) - len(failures)}/{len(answers)} ({(1-len(failures)/len(answers))*100:.1f}%)")
    print(f"Average guesses: {sum(results)/len(results):.4f}")
    print(f"Distribution:")
    for k in sorted(counter.keys()):
        bar = "█" * (counter[k] // 5)
        print(f"  {k} guesses: {counter[k]:4d} ({counter[k]/len(answers)*100:5.1f}%) {bar}")
    print(f"Time: {elapsed:.1f}s")

    if failures and verbose_failures:
        print(f"\nFailures ({len(failures)}):")
        for target, guesses in failures[:10]:
            print(f"  {target}: {' → '.join(g for g,_ in guesses)}")

    return results, failures


if __name__ == "__main__":
    answers = load_answers()
    all_guesses = load_all_guesses()

    strategy = sys.argv[1] if len(sys.argv) > 1 else "human"
    opener = sys.argv[2] if len(sys.argv) > 2 else "raise"

    print(f"Running simulation: strategy={strategy}, opener={opener}")
    print(f"Answer pool: {len(answers)} words")
    print()

    run_simulation(strategy, answers, all_guesses, opener)
