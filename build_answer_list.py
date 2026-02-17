"""Extract and save the Wordle answer list as a clean text file."""
import re

with open("/root/.claude/projects/-home-user-wordle-words/821c3ee8-326e-47f6-a921-8690ff1869aa/tool-results/toolu_01Mbk6q72u4XynDGC1eDuHDV.txt") as f:
    raw = f.read()

words = re.findall(r'"([a-z]{5})"', raw)
# Deduplicate preserving order
seen = set()
unique = []
for w in words:
    if w not in seen:
        seen.add(w)
        unique.append(w)

with open("/home/user/wordle-words/answers.txt", "w") as f:
    for w in sorted(unique):
        f.write(w + "\n")

print(f"Extracted {len(unique)} unique answer words")
