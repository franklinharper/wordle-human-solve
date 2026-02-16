"""
Improved human-playable hard-mode strategy.

Key improvement over naive heuristic: detect the "one-position trap"
where many candidates differ in just one slot, and handle it by picking
a word that tests multiple candidate letters for that slot.

Also: find optimal second-word lookup table for common RAISE feedback categories.
"""

from collections import Counter, defaultdict
from analysis import (
    load_answers, load_all_guesses,
    compute_feedback, feedback_to_str,
    partition_by_feedback, filter_candidates,
    expected_information, expected_remaining,
    letter_frequency, positional_letter_frequency
)


def find_varying_positions(candidates):
    """Find which positions vary across candidates.

    Returns dict: position -> set of letters seen there.
    Only includes positions where more than one letter appears.
    """
    varying = {}
    for pos in range(5):
        letters = set(w[pos] for w in candidates)
        if len(letters) > 1:
            varying[pos] = letters
    return varying


def detect_one_position_trap(candidates):
    """Detect if candidates mostly differ in a single position.

    Returns (True, position, letters) or (False, None, None).
    """
    varying = find_varying_positions(candidates)
    if len(varying) == 1:
        pos = list(varying.keys())[0]
        return True, pos, varying[pos]
    # Also detect "near-trap": 2 positions vary but one dominates
    if len(varying) == 2:
        positions = list(varying.keys())
        sizes = [len(varying[p]) for p in positions]
        if sizes[0] >= 3 and sizes[1] <= 2:
            return True, positions[0], varying[positions[0]]
        if sizes[1] >= 3 and sizes[0] <= 2:
            return True, positions[1], varying[positions[1]]
    return False, None, None


def find_discriminator(candidates, all_valid_guesses, target_pos, target_letters):
    """Find a hard-mode-valid word that tests the most candidate letters
    for the disputed position.

    Strategy: pick a word containing the maximum number of letters from
    target_letters, ideally in positions where they're most common.
    """
    candidate_set = set(candidates)
    best_word = None
    best_coverage = 0
    best_is_candidate = False

    for word in candidates:
        # Count how many target letters appear in this word
        coverage = len(target_letters & set(word))
        is_cand = word in candidate_set
        if coverage > best_coverage or (coverage == best_coverage and is_cand and not best_is_candidate):
            best_coverage = coverage
            best_word = word
            best_is_candidate = is_cand

    return best_word


LETTER_PRIORITY = list("earotilsnucyhdpgmbfkwvxzqj")


def improved_human_guess(candidates, all_guesses, tested_letters):
    """
    Improved human heuristic:
    1. If <=2 candidates, guess first one
    2. If "one-position trap" detected, use discriminator logic
    3. Otherwise, use letter-priority heuristic
    """
    if len(candidates) <= 2:
        return candidates[0]

    # Check for one-position trap
    is_trap, trap_pos, trap_letters = detect_one_position_trap(candidates)
    if is_trap and len(candidates) >= 4:
        # Try to find a word containing multiple trap letters
        disc = find_discriminator(candidates, all_guesses, trap_pos, trap_letters)
        if disc:
            return disc

    # Standard heuristic: maximize untested high-priority letters
    untested_priority = [ch for ch in LETTER_PRIORITY if ch not in tested_letters]
    pos_freq = positional_letter_frequency(candidates)
    n = len(candidates)

    best_word = None
    best_score = -1

    for word in candidates:
        untested_score = 0
        seen = set()
        for ch in word:
            if ch in seen:
                continue
            seen.add(ch)
            if ch in tested_letters:
                continue
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


def play_game_improved(target, all_answers, all_guesses, opener="raise", max_guesses=6, verbose=False):
    """Play a game using the improved human heuristic."""
    candidates = list(all_answers)
    guesses = []
    tested_letters = set()

    for turn in range(1, max_guesses + 1):
        if turn == 1:
            guess = opener
        else:
            guess = improved_human_guess(candidates, all_guesses, tested_letters)

        feedback = compute_feedback(guess, target)
        guesses.append((guess, feedback))

        if verbose:
            print(f"  Guess {turn}: {guess} → {feedback_to_str(feedback)} (candidates: {len(candidates)})")

        for ch in guess:
            tested_letters.add(ch)

        if feedback == (2, 2, 2, 2, 2):
            return turn, guesses, True

        candidates = filter_candidates(candidates, guess, feedback)
        if len(candidates) == 0:
            return turn, guesses, False

    return max_guesses, guesses, False


if __name__ == "__main__":
    import time
    answers = load_answers()
    all_guesses = load_all_guesses()

    print("Running improved human heuristic simulation...")
    print(f"Answer pool: {len(answers)} words\n")

    results = []
    failures = []
    start = time.time()

    for i, target in enumerate(answers):
        if (i + 1) % 500 == 0:
            elapsed = time.time() - start
            print(f"  {i+1}/{len(answers)} ({elapsed:.1f}s)")
        n, guesses, solved = play_game_improved(target, answers, all_guesses)
        results.append(n)
        if not solved:
            failures.append((target, guesses))

    elapsed = time.time() - start
    counter = Counter(results)

    print(f"\n{'='*60}")
    print(f"Improved Human Heuristic, Opener: raise")
    print(f"{'='*60}")
    print(f"Solved: {len(answers) - len(failures)}/{len(answers)} ({(1 - len(failures)/len(answers))*100:.1f}%)")
    print(f"Average guesses: {sum(results)/len(results):.4f}")
    print(f"Distribution:")
    for k in sorted(counter.keys()):
        bar = "█" * (counter[k] // 5)
        print(f"  {k} guesses: {counter[k]:4d} ({counter[k]/len(answers)*100:5.1f}%) {bar}")
    print(f"Time: {elapsed:.1f}s")

    if failures:
        print(f"\nFailures ({len(failures)}):")
        for target, guesses in failures[:20]:
            chain = " → ".join(f"{g}({feedback_to_str(fb)})" for g, fb in guesses)
            print(f"  {target}: {chain}")
