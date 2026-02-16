"""
Analyze the decision landscape after guessing RAISE.

For each possible feedback pattern from RAISE, we want to know:
1. How many candidates remain?
2. What's the best second guess (from the hard-mode-valid pool)?
3. Can a human recognize patterns to speed up the decision?
"""

from analysis import (
    load_answers, load_all_guesses,
    compute_feedback, feedback_to_str,
    partition_by_feedback, filter_candidates,
    expected_information, expected_remaining,
    letter_frequency, positional_letter_frequency,
    score_word_by_frequency
)

answers = load_answers()
all_guesses = load_all_guesses()
answer_set = set(answers)

OPENER = "raise"

# Partition all answers by feedback from RAISE
buckets = partition_by_feedback(OPENER, answers)

# Sort by bucket size descending
sorted_buckets = sorted(buckets.items(), key=lambda x: -len(x[1]))

print(f"RAISE produces {len(buckets)} distinct feedback patterns")
print(f"Theoretical max: 243 (3^5)")
print()

# Show distribution
sizes = [len(b) for b in buckets.values()]
print(f"Bucket size stats:")
print(f"  Min: {min(sizes)}, Max: {max(sizes)}, Mean: {sum(sizes)/len(sizes):.1f}")
print(f"  Buckets with 1 word: {sum(1 for s in sizes if s == 1)}")
print(f"  Buckets with <=5 words: {sum(1 for s in sizes if s <= 5)}")
print(f"  Buckets with <=20 words: {sum(1 for s in sizes if s <= 20)}")
print(f"  Buckets with >50 words: {sum(1 for s in sizes if s > 50)}")
print()

# Detailed analysis of the largest buckets (these are where the strategy matters most)
print("=" * 80)
print("LARGEST BUCKETS (where strategy matters most)")
print("=" * 80)

for fb, words in sorted_buckets[:15]:
    n_cands = len(words)
    fb_str = feedback_to_str(fb)
    fb_codes = "".join(str(x) for x in fb)

    print(f"\n--- {fb_str} ({fb_codes}) --- {n_cands} candidates ---")

    if n_cands <= 10:
        print(f"  Candidates: {', '.join(sorted(words))}")
    else:
        print(f"  Sample: {', '.join(sorted(words)[:8])}...")

    if n_cands <= 1:
        continue

    # Find best second guess from hard-mode-valid words
    # In hard mode, guess must be consistent with the feedback
    valid_guesses = filter_candidates(all_guesses, OPENER, fb)
    valid_answers_in_pool = [w for w in valid_guesses if w in answer_set]

    print(f"  Valid guesses (hard mode): {len(valid_guesses)}")
    print(f"  Valid answer-guesses: {len(valid_answers_in_pool)}")

    # Evaluate top second guesses (limit to answer words for speed, they're usually best)
    best = []
    pool_to_eval = valid_answers_in_pool if len(valid_answers_in_pool) > 20 else valid_guesses
    # For large pools, sample
    if len(pool_to_eval) > 500:
        # Evaluate answer words first, then top non-answers
        pool_to_eval = valid_answers_in_pool

    for guess in pool_to_eval:
        info = expected_information(guess, words)
        exp_rem = expected_remaining(guess, words)
        best.append((guess, info, exp_rem))

    best.sort(key=lambda x: -x[1])

    print(f"  Top 5 second guesses:")
    for word, info, exp_rem in best[:5]:
        print(f"    {word}: {info:.3f} bits, E[rem]={exp_rem:.1f}")

    # What letters are most informative for this bucket?
    freq = letter_frequency(words)
    tested = set(OPENER)
    print(f"  Most informative untested letters (closest to 50%):")
    by_dist = sorted(freq.items(), key=lambda x: abs(x[1]/n_cands - 0.5))
    untested = [(ch, cnt) for ch, cnt in by_dist if ch not in tested]
    for ch, cnt in untested[:5]:
        print(f"    {ch}: {cnt/n_cands*100:.0f}%")
