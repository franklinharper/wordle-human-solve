"""
Generate all 5-slot Wordle feedback patterns whose non-gray tile count is < 3.

Encoding:
- 0 = gray
- 1 = yellow
- 2 = green
"""

from itertools import product


def feedback_to_emoji(pattern):
    symbols = {0: "⬛", 1: "🟨", 2: "🟩"}
    return "".join(symbols[x] for x in pattern)


def non_gray_count(pattern):
    return sum(1 for x in pattern if x in (1, 2))


def main(output_path="patterns_sum_lt3.txt"):
    patterns = [p for p in product((0, 1, 2), repeat=5) if non_gray_count(p) < 3]
    patterns.sort()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Wordle feedback patterns with count(yellow + green) < 3\n")
        f.write("# Format: codes emoji count\n")
        f.write(f"# Count: {len(patterns)}\n\n")
        for p in patterns:
            codes = "".join(str(x) for x in p)
            emoji = feedback_to_emoji(p)
            f.write(f"{codes} {emoji} {non_gray_count(p)}\n")

    print(f"Wrote {len(patterns)} patterns to {output_path}")


if __name__ == "__main__":
    main()
