"""
Find the best opening word from the FULL guess pool (14,855 words).

In hard mode, your first guess can be anything. A word from the answer list
has the bonus of potentially being correct, but a non-answer word might
partition the space better.

We filter to words with 5 distinct letters (no duplicates) since duplicates
waste information on the opening guess.
"""

from analysis import (
    load_answers, load_all_guesses,
    expected_information, expected_remaining, worst_case_remaining
)

answers = load_answers()
all_guesses = load_all_guesses()
n = len(answers)

print(f"Answer pool: {n} words")
print(f"Full guess pool: {len(all_guesses)} words")

# Filter to 5-distinct-letter words only
distinct_guesses = [w for w in all_guesses if len(set(w)) == 5]
print(f"Guesses with 5 distinct letters: {len(distinct_guesses)}")

# Evaluate all of them
print("\nEvaluating all distinct-letter guesses... (this will take a while)")
results = []
total = len(distinct_guesses)
for i, word in enumerate(distinct_guesses):
    if (i + 1) % 1000 == 0:
        print(f"  {i+1}/{total}...")
    info = expected_information(word, answers)
    results.append((word, info))

results.sort(key=lambda x: -x[1])

# Show top 30, with expected remaining and worst case for the top ones
print(f"\n{'Word':<8} {'Info (bits)':>11} {'E[remaining]':>13} {'Worst case':>11} {'Is answer?':>11}")
for word, info in results[:30]:
    exp_rem = expected_remaining(word, answers)
    worst = worst_case_remaining(word, answers)
    is_answer = "YES" if word in set(answers) else "no"
    print(f"  {word:<8} {info:>11.4f} {exp_rem:>13.2f} {worst:>11d} {is_answer:>11}")
