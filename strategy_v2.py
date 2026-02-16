"""
Strategy V2: Memorized guess-2 lookup + improved heuristic for guess 3+.

The idea: guess 1 (RAISE) is memorized. Guess 2 is from a small lookup table
indexed by the RAISE feedback pattern. Guesses 3+ use an improved heuristic.

This measures the VALUE of a lookup table for guess 2 at various sizes.
"""

import time
from collections import Counter, defaultdict
from analysis import (
    load_answers, load_all_guesses,
    compute_feedback, feedback_to_str,
    partition_by_feedback, filter_candidates,
    expected_information, expected_remaining,
    letter_frequency, positional_letter_frequency,
)


# --- Build the guess-2 lookup table ---

def build_guess2_table(answers, opener="raise"):
    """For each feedback pattern from opener, find the optimal 2nd guess."""
    buckets = partition_by_feedback(opener, answers)
    table = {}
    for fb, candidates in buckets.items():
        if len(candidates) <= 1:
            table[fb] = candidates[0] if candidates else None
            continue
        # Find best guess from candidates (hard mode: guess must be a candidate)
        best_word = None
        best_info = -1
        for word in candidates:
            info = expected_information(word, candidates)
            if info > best_info:
                best_info = info
                best_word = word
        table[fb] = best_word
    return table


# --- Improved guess 3+ heuristic ---

LETTER_PRIORITY = list("earotilsnucyhdpgmbfkwvxzqj")


def improved_guess(candidates, tested_letters):
    """Smart heuristic for guesses 3+.

    Key improvements:
    1. Detect single-position ambiguity and pick discriminating words
    2. When few candidates remain, maximize discrimination
    3. Otherwise, maximize untested letter coverage
    """
    if len(candidates) <= 2:
        return candidates[0]

    # Detect: do candidates mostly differ in one position?
    varying = {}
    for pos in range(5):
        letters = set(w[pos] for w in candidates)
        if len(letters) > 1:
            varying[pos] = letters

    # If only 1-2 positions vary and we have many candidates,
    # score by how many varying-position letters the word covers
    if len(varying) <= 2 and len(candidates) >= 4:
        best_word = None
        best_score = -1
        for word in candidates:
            score = 0
            for pos, letters in varying.items():
                # How many of the ambiguous letters does this word "test"?
                # Direct test: the word's letter in this position
                if word[pos] in letters:
                    score += 1
                # Indirect: does the word contain OTHER ambiguous letters?
                # (They might appear as yellows and give info)
                for ch in set(word):
                    if ch in letters:
                        score += 0.3
            if score > best_score:
                best_score = score
                best_word = word
        return best_word

    # General case: maximize info via expected_information if small enough
    if len(candidates) <= 20:
        best_word = None
        best_info = -1
        for word in candidates:
            info = expected_information(word, candidates)
            if info > best_info:
                best_info = info
                best_word = word
        return best_word

    # Large candidate pool: use letter-priority heuristic
    untested_priority = [ch for ch in LETTER_PRIORITY if ch not in tested_letters]
    pos_freq = positional_letter_frequency(candidates)
    n = len(candidates)

    best_word = None
    best_score = -1.0
    for word in candidates:
        untested_score = 0
        seen = set()
        for ch in word:
            if ch in seen:
                continue
            seen.add(ch)
            if ch not in tested_letters:
                try:
                    idx = untested_priority.index(ch)
                    untested_score += (len(untested_priority) - idx)
                except ValueError:
                    pass
        pos_score = sum(pos_freq[i].get(ch, 0) / n for i, ch in enumerate(word))
        score = untested_score * 100 + pos_score
        if score > best_score:
            best_score = score
            best_word = word

    return best_word


def play_game_v2(target, answers, all_guesses, guess2_table, opener="raise", max_guesses=6, verbose=False):
    """Play hard-mode Wordle with the V2 strategy."""
    candidates = list(answers)
    guesses = []
    tested_letters = set()

    for turn in range(1, max_guesses + 1):
        if turn == 1:
            guess = opener
        elif turn == 2:
            # Use lookup table
            prev_fb = guesses[-1][1]
            guess = guess2_table.get(prev_fb)
            if guess is None or guess not in candidates:
                # Fallback to heuristic
                guess = improved_guess(candidates, tested_letters)
        else:
            guess = improved_guess(candidates, tested_letters)

        feedback = compute_feedback(guess, target)
        guesses.append((guess, feedback))

        if verbose:
            n_cands = len(candidates)
            print(f"  G{turn}: {guess} → {feedback_to_str(feedback)} ({n_cands} candidates)")

        for ch in guess:
            tested_letters.add(ch)

        if feedback == (2, 2, 2, 2, 2):
            return turn, guesses, True

        candidates = filter_candidates(candidates, guess, feedback)
        if not candidates:
            return turn, guesses, False

    return max_guesses, guesses, False


def run_simulation(answers, all_guesses, guess2_table, opener="raise"):
    results = []
    failures = []
    start = time.time()

    for i, target in enumerate(answers):
        if (i + 1) % 500 == 0:
            print(f"  {i+1}/{len(answers)} ({time.time()-start:.1f}s)")
        n, guesses, solved = play_game_v2(target, answers, all_guesses, guess2_table, opener)
        results.append(n)
        if not solved:
            failures.append((target, guesses))

    elapsed = time.time() - start
    counter = Counter(results)

    print(f"\n{'='*60}")
    print(f"Strategy V2: Lookup + Improved Heuristic")
    print(f"{'='*60}")
    print(f"Solved: {len(answers)-len(failures)}/{len(answers)} ({(1-len(failures)/len(answers))*100:.1f}%)")
    print(f"Average guesses: {sum(results)/len(results):.4f}")
    print(f"Distribution:")
    for k in sorted(counter.keys()):
        bar = "█" * (counter[k] // 5)
        print(f"  {k} guesses: {counter[k]:4d} ({counter[k]/len(answers)*100:5.1f}%) {bar}")
    print(f"Time: {elapsed:.1f}s")

    if failures:
        print(f"\nFailures ({len(failures)}):")
        for target, guesses in failures[:15]:
            chain = " → ".join(f"{g}({feedback_to_str(fb)})" for g, fb in guesses)
            print(f"  {target}: {chain}")

    return results, failures


if __name__ == "__main__":
    answers = load_answers()
    all_guesses = load_all_guesses()

    print("Building optimal guess-2 lookup table for RAISE...")
    table = build_guess2_table(answers)
    print(f"Table size: {len(table)} entries\n")

    print("Running V2 simulation (full lookup table)...")
    results, failures = run_simulation(answers, all_guesses, table)

    # Now test: what if we only memorize the top N patterns?
    print("\n\n" + "=" * 60)
    print("ABLATION: How many patterns do you need to memorize?")
    print("=" * 60)

    buckets = partition_by_feedback("raise", answers)
    sorted_patterns = sorted(buckets.keys(), key=lambda fb: -len(buckets[fb]))

    for n_memorized in [5, 10, 15, 20, 37]:
        # Build a partial table with only the top N patterns
        partial_table = {}
        for fb in sorted_patterns[:n_memorized]:
            partial_table[fb] = table[fb]

        results2 = []
        failures2 = []
        for target in answers:
            n, guesses, solved = play_game_v2(
                target, answers, all_guesses, partial_table
            )
            results2.append(n)
            if not solved:
                failures2.append(target)

        avg = sum(results2) / len(results2)
        n_fail = len(failures2)
        coverage = sum(len(buckets[fb]) for fb in sorted_patterns[:n_memorized])
        print(f"  Top {n_memorized:>2} patterns ({coverage:>4} words covered): "
              f"avg={avg:.4f}, failures={n_fail}")
