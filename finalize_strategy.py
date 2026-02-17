"""
Finalize the human-playable strategy.

For each of the top feedback patterns from RAISE, find the best
second-guess word that is:
1. A common, recognizable English word
2. Close to the information-theoretic optimal
3. Easy to remember

Then simulate the complete strategy.
"""

import time
from collections import Counter
from analysis import (
    load_answers, load_all_guesses,
    compute_feedback, feedback_to_str,
    partition_by_feedback, filter_candidates,
    expected_information, expected_remaining,
    letter_frequency, positional_letter_frequency,
)

answers = load_answers()
all_guesses = load_all_guesses()
answer_set = set(answers)
OPENER = "raise"

# The top 15 feedback patterns from RAISE by bucket size
buckets = partition_by_feedback(OPENER, answers)
sorted_patterns = sorted(buckets.keys(), key=lambda fb: -len(buckets[fb]))

# For each big pattern, show top 10 candidate second-guess words
# so we can pick human-friendly ones
print("TOP SECOND GUESSES PER PATTERN (for human selection)\n")
print("Looking for common, memorable words close to optimal...\n")

human_friendly_overrides = {}

for fb in sorted_patterns[:15]:
    cands = buckets[fb]
    fb_str = feedback_to_str(fb)
    codes = "".join(str(x) for x in fb)
    n = len(cands)

    # Compute info for all candidates
    scored = []
    for word in cands:
        info = expected_information(word, cands)
        exp_rem = expected_remaining(word, cands)
        scored.append((word, info, exp_rem))
    scored.sort(key=lambda x: -x[1])

    best_info = scored[0][1]

    # Describe the pattern in human terms
    greens = [OPENER[i] for i in range(5) if fb[i] == 2]
    yellows = [OPENER[i] for i in range(5) if fb[i] == 1]
    grays = [OPENER[i] for i in range(5) if fb[i] == 0]
    desc = ""
    if greens:
        desc += f"Green: {','.join(greens)}  "
    if yellows:
        desc += f"Yellow: {','.join(yellows)}  "
    desc += f"Gray: {','.join(grays)}"

    print(f"--- {fb_str} ({codes}) [{n} words] ---")
    print(f"  {desc}")
    print(f"  Top 10 words (info / E[rem] / gap from optimal):")
    for word, info, exp_rem in scored[:10]:
        gap = best_info - info
        print(f"    {word:<10} info={info:.3f}  E[rem]={exp_rem:.1f}  gap={gap:.3f}")
    print()

# Now let's define our human-friendly lookup table
print("\n" + "=" * 70)
print("PROPOSED HUMAN-FRIENDLY LOOKUP TABLE")
print("=" * 70)

# For each pattern, I'll pick the best word that's common and memorable
# Criteria: prefer answer words, prefer common English, acceptable info loss < 0.1 bits
lookup_table = {
    # All gray: MULCH, CLOTH, CLOUT are all good
    (0,0,0,0,0): "clout",    # C,L,O,U,T - top 5 untested letters!
    # Only E yellow (pos 5): BETEL is obscure, OLDEN/TOWEL/HOTEL are better
    (0,0,0,0,1): "towel",    # Tests T,O,W,L + repositions E
    # Only I yellow (pos 3): PILOT is great and common
    (0,0,1,0,0): "pilot",
    # Only R yellow (pos 1): COURT is great and common
    (1,0,0,0,0): "court",
    # R+E yellow: DETER is good and common enough
    (1,0,0,0,1): "outer",    # O,U,T + repositions R,E
    # A yellow (pos 2): FLOAT is perfect
    (0,1,0,0,0): "float",
    # A green (pos 2): TANGY is good, CANDY also
    (0,2,0,0,0): "tangy",
    # S yellow (pos 4): STUNK/STONY
    (0,0,0,1,0): "stony",    # Tests T,O,N,Y + repositions S
    # R+A yellow: ADORN is good
    (1,1,0,0,0): "adorn",
    # A+E yellow: CLEAT is good
    (0,1,0,0,1): "cleat",
    # E green (pos 5): LUNGE is okay, UNTIE?
    (0,0,0,0,2): "lunge",
    # I green (pos 3): GLINT is good
    (0,0,2,0,0): "glint",
}

for fb, word in lookup_table.items():
    cands = buckets[fb]
    info = expected_information(word, cands)
    exp_rem = expected_remaining(word, cands)

    # Find the optimal for comparison
    best_info = max(expected_information(w, cands) for w in cands)

    fb_str = feedback_to_str(fb)
    gap = best_info - info
    print(f"  {fb_str}: {word:<10} info={info:.3f} (optimal={best_info:.3f}, gap={gap:.3f})  "
          f"E[rem]={exp_rem:.1f}  [{len(cands)} candidates]")


# Simulate the strategy with this human-friendly table
print(f"\n{'='*70}")
print("SIMULATION: Human-friendly lookup table + improved heuristic")
print(f"{'='*70}")


def improved_guess(candidates, tested_letters):
    if len(candidates) <= 2:
        return candidates[0]

    # Check for single-position ambiguity
    varying = {}
    for pos in range(5):
        letters = set(w[pos] for w in candidates)
        if len(letters) > 1:
            varying[pos] = letters

    # Small candidate pool: use info-theoretic
    if len(candidates) <= 20:
        best_word = None
        best_info = -1
        for word in candidates:
            info = expected_information(word, candidates)
            if info > best_info:
                best_info = info
                best_word = word
        return best_word

    # Large pool: letter priority
    PRIORITY = list("earotilsnucyhdpgmbfkwvxzqj")
    untested = [ch for ch in PRIORITY if ch not in tested_letters]
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
                    idx = untested.index(ch)
                    untested_score += (len(untested) - idx)
                except ValueError:
                    pass
        pos_score = sum(pos_freq[i].get(ch, 0) / n for i, ch in enumerate(word))
        score = untested_score * 100 + pos_score
        if score > best_score:
            best_score = score
            best_word = word
    return best_word


results = []
failures = []
guess2_hits = 0
guess2_misses = 0
start = time.time()

for target in answers:
    candidates = list(answers)
    guesses_list = []
    tested = set()
    solved = False

    for turn in range(1, 7):
        if turn == 1:
            guess = OPENER
        elif turn == 2:
            prev_fb = guesses_list[-1][1]
            if prev_fb in lookup_table:
                guess = lookup_table[prev_fb]
                guess2_hits += 1
            else:
                guess = improved_guess(candidates, tested)
                guess2_misses += 1
        else:
            guess = improved_guess(candidates, tested)

        fb = compute_feedback(guess, target)
        guesses_list.append((guess, fb))
        for ch in guess:
            tested.add(ch)

        if fb == (2, 2, 2, 2, 2):
            results.append(turn)
            solved = True
            break

        candidates = filter_candidates(candidates, guess, fb)

    if not solved:
        results.append(6)
        failures.append((target, guesses_list))

elapsed = time.time() - start
counter = Counter(results)

print(f"\nSolved: {len(answers)-len(failures)}/{len(answers)} ({(1-len(failures)/len(answers))*100:.1f}%)")
print(f"Average guesses: {sum(results)/len(results):.4f}")
print(f"Lookup table hits: {guess2_hits} ({guess2_hits/(guess2_hits+guess2_misses)*100:.0f}%)")
print(f"Distribution:")
for k in sorted(counter.keys()):
    bar = "█" * (counter[k] // 5)
    print(f"  {k} guesses: {counter[k]:4d} ({counter[k]/len(answers)*100:5.1f}%) {bar}")
print(f"Time: {elapsed:.1f}s")

if failures:
    print(f"\nFailures ({len(failures)}):")
    for target, gl in failures[:20]:
        chain = " → ".join(f"{g}({feedback_to_str(fb)})" for g, fb in gl)
        print(f"  {target}: {chain}")
