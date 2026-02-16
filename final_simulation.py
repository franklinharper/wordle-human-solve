"""
Final strategy simulation with optimized human-friendly word choices.

Tests a few variants of the lookup table to find the best combination.
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


def improved_guess(candidates, tested_letters):
    if len(candidates) <= 2:
        return candidates[0]
    if len(candidates) <= 20:
        best_word = None
        best_info = -1
        for word in candidates:
            info = expected_information(word, candidates)
            if info > best_info:
                best_info = info
                best_word = word
        return best_word

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


def simulate(table, label, verbose_failures=True):
    results = []
    failures = []
    start = time.time()

    for target in answers:
        candidates = list(answers)
        guesses_list = []
        tested = set()
        solved = False

        for turn in range(1, 7):
            if turn == 1:
                guess = "raise"
            elif turn == 2:
                prev_fb = guesses_list[-1][1]
                if prev_fb in table:
                    guess = table[prev_fb]
                else:
                    guess = improved_guess(candidates, tested)
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

    print(f"\n--- {label} ---")
    print(f"Solved: {len(answers)-len(failures)}/{len(answers)} ({(1-len(failures)/len(answers))*100:.1f}%)")
    print(f"Average: {sum(results)/len(results):.4f}")
    for k in sorted(counter.keys()):
        print(f"  {k}: {counter[k]:4d} ({counter[k]/len(answers)*100:5.1f}%)")
    print(f"Time: {elapsed:.1f}s")
    if verbose_failures and failures:
        print(f"Failures ({len(failures)}):")
        for target, gl in failures:
            chain = " → ".join(f"{g}" for g, fb in gl)
            print(f"  {target}: {chain}")

    return sum(results)/len(results), len(failures)


# Test several variants

# Variant A: Original (CLOUT, TOWEL, OUTER)
table_a = {
    (0,0,0,0,0): "clout",
    (0,0,0,0,1): "towel",
    (0,0,1,0,0): "pilot",
    (1,0,0,0,0): "court",
    (1,0,0,0,1): "outer",
    (0,1,0,0,0): "float",
    (0,2,0,0,0): "tangy",
    (0,0,0,1,0): "stony",
    (1,1,0,0,0): "adorn",
    (0,1,0,0,1): "cleat",
    (0,0,0,0,2): "lunge",
    (0,0,2,0,0): "glint",
}

# Variant B: Better info words (CLOTH, OLDEN, DETER)
table_b = {
    (0,0,0,0,0): "cloth",
    (0,0,0,0,1): "olden",
    (0,0,1,0,0): "pilot",
    (1,0,0,0,0): "court",
    (1,0,0,0,1): "deter",
    (0,1,0,0,0): "float",
    (0,2,0,0,0): "tangy",
    (0,0,0,1,0): "stunk",
    (1,1,0,0,0): "adorn",
    (0,1,0,0,1): "cleat",
    (0,0,0,0,2): "lunge",
    (0,0,2,0,0): "glint",
}

# Variant C: Near-optimal info words (MULCH, OLDEN, DETER, STUNK)
table_c = {
    (0,0,0,0,0): "mulch",
    (0,0,0,0,1): "olden",
    (0,0,1,0,0): "pilot",
    (1,0,0,0,0): "court",
    (1,0,0,0,1): "deter",
    (0,1,0,0,0): "float",
    (0,2,0,0,0): "tangy",
    (0,0,0,1,0): "stunk",
    (1,1,0,0,0): "adorn",
    (0,1,0,0,1): "cleat",
    (0,0,0,0,2): "lunge",
    (0,0,2,0,0): "glint",
}

# Variant D: Mixed - best info where words are still memorable
table_d = {
    (0,0,0,0,0): "cloth",     # 5.162 - very common, tests C,L,O,T,H
    (0,0,0,0,1): "olden",     # 4.946 - common, tests O,L,D,N + E
    (0,0,1,0,0): "pilot",     # 4.693 - optimal & common
    (1,0,0,0,0): "court",     # 4.706 - optimal & common
    (1,0,0,0,1): "deter",     # 4.370 - optimal & common
    (0,1,0,0,0): "float",     # 4.851 - optimal & common
    (0,2,0,0,0): "tangy",     # 4.031 - optimal & fairly common
    (0,0,0,1,0): "stony",     # 4.370 - common, tests T,O,N,Y
    (1,1,0,0,0): "adorn",     # 4.144 - optimal & common
    (0,1,0,0,1): "cleat",     # 4.637 - optimal & common
    (0,0,0,0,2): "lunge",     # 4.230 - optimal & common
    (0,0,2,0,0): "glint",     # 4.145 - optimal & common
}


print("=" * 70)
print("COMPARING LOOKUP TABLE VARIANTS")
print("=" * 70)

results = {}
for name, table in [("A: clout/towel/outer", table_a),
                     ("B: cloth/olden/deter", table_b),
                     ("C: mulch/olden/deter", table_c),
                     ("D: cloth/olden/deter/stony", table_d)]:
    avg, fails = simulate(table, name, verbose_failures=(name.startswith("D")))
    results[name] = (avg, fails)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
for name, (avg, fails) in results.items():
    print(f"  {name}: avg={avg:.4f}, failures={fails}")
