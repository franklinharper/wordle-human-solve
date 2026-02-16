"""
Analyze the info-theoretic optimal's second guess choices.

Goal: Find a small set of memorizable second-guess words that cover
most feedback patterns from RAISE, approximating optimal play.
"""

from collections import Counter, defaultdict
from analysis import (
    load_answers, load_all_guesses,
    compute_feedback, feedback_to_str,
    partition_by_feedback, filter_candidates,
    expected_information, expected_remaining,
)


def best_guess_by_info(candidates):
    if len(candidates) <= 2:
        return candidates[0]
    candidate_set = set(candidates)
    best_word = None
    best_info = -1
    best_is_candidate = False
    for word in candidates:
        info = expected_information(word, candidates)
        is_cand = word in candidate_set
        if info > best_info or (info == best_info and is_cand and not best_is_candidate):
            best_info = info
            best_word = word
            best_is_candidate = is_cand
    return best_word


answers = load_answers()
OPENER = "raise"

# Partition by RAISE feedback
buckets = partition_by_feedback(OPENER, answers)
sorted_buckets = sorted(buckets.items(), key=lambda x: -len(x[1]))

print("Finding optimal second guess for each RAISE feedback pattern...\n")

# For each bucket, find the optimal second guess
optimal_guess2 = {}
for fb, candidates in sorted_buckets:
    if len(candidates) <= 1:
        optimal_guess2[fb] = (candidates[0] if candidates else None, 0, len(candidates))
        continue
    g2 = best_guess_by_info(candidates)
    info = expected_information(g2, candidates)
    exp_rem = expected_remaining(g2, candidates)
    optimal_guess2[fb] = (g2, info, exp_rem)

# Display results grouped by bucket size
print(f"{'Pattern':<12} {'Codes':<8} {'#Cands':>6} {'Optimal G2':<10} {'Info':>6} {'E[rem]':>7}")
print("-" * 60)
for fb, candidates in sorted_buckets:
    g2, info, exp_rem = optimal_guess2[fb]
    fb_str = feedback_to_str(fb)
    codes = "".join(str(x) for x in fb)
    print(f"  {fb_str} {codes:<8} {len(candidates):>4}   {g2 or '-':<10} {info:>6.3f} {exp_rem:>7.1f}")

# Now analyze: how many distinct second-guess words does the optimal use?
print(f"\n{'='*60}")
print("DISTINCT OPTIMAL SECOND GUESSES")
print(f"{'='*60}")
guess2_words = Counter()
guess2_coverage = defaultdict(list)  # word -> list of (feedback, n_candidates)
for fb, (g2, info, exp_rem) in optimal_guess2.items():
    if g2 and len(buckets[fb]) > 1:
        guess2_words[g2] += 1
        guess2_coverage[g2].append((fb, len(buckets[fb])))

print(f"Total distinct feedback patterns needing a 2nd guess: {len([v for v in guess2_words.values()])}")
print(f"Distinct 2nd-guess words used: {len(guess2_words)}")

print(f"\nMost common 2nd-guess words:")
for word, count in guess2_words.most_common(20):
    total_cands = sum(n for _, n in guess2_coverage[word])
    print(f"  {word}: used for {count} patterns, covering {total_cands} total candidates")

# KEY ANALYSIS: How many words do we need to cover the big buckets?
print(f"\n{'='*60}")
print("COVERAGE ANALYSIS: Minimum words to cover large buckets")
print(f"{'='*60}")

# For buckets with >= 20 candidates, what's the optimal g2?
big_buckets = [(fb, cands) for fb, cands in sorted_buckets if len(cands) >= 20]
print(f"\nBuckets with >= 20 candidates: {len(big_buckets)}")
print(f"These cover {sum(len(c) for _, c in big_buckets)} of {len(answers)} total answer words")

big_bucket_words = {}
for fb, cands in big_buckets:
    g2, info, exp_rem = optimal_guess2[fb]
    big_bucket_words[fb] = g2
    fb_str = feedback_to_str(fb)
    codes = "".join(str(x) for x in fb)
    print(f"  {fb_str} ({codes}): {len(cands):>3} cands → {g2}")

# How many distinct words for big buckets?
unique_big = set(big_bucket_words.values())
print(f"\nDistinct words needed for big buckets: {len(unique_big)}")
print(f"Words: {sorted(unique_big)}")

# Can we find a smaller set of words that works nearly as well?
print(f"\n{'='*60}")
print("GREEDY SET COVER: Find minimal word set for big buckets")
print(f"{'='*60}")

# For each big bucket, evaluate all candidate words and find top 5
print("\nTop 5 words per big bucket:")
for fb, cands in big_buckets:
    fb_str = feedback_to_str(fb)
    top = []
    for word in cands:
        info = expected_information(word, cands)
        top.append((word, info))
    top.sort(key=lambda x: -x[1])
    optimal_word = big_bucket_words[fb]
    top_words = [f"{w}({i:.2f})" for w, i in top[:5]]
    print(f"  {fb_str} [{len(cands):>3}]: {', '.join(top_words)}  [optimal: {optimal_word}]")
