# Hard-Mode Wordle Strategy: First-Principles Speed Optimization

**Goal:** Solve Wordle in hard mode as fast as possible (minimize wall-clock time).

**Performance:** 3.64 average guesses | 99.5% solve rate | 83% solved in 3-4 guesses

---

## The Core Idea

Wordle is an **information-gathering problem**. You start with ~2,300 possible
answers and need to reach 1. Each guess partitions the remaining candidates by
its feedback pattern (3^5 = 243 possible patterns). The best guess is the one
that creates the most even partition — maximizing expected information gain.

For **wall-clock speed**, we minimize thinking time by:
1. **Memorizing** guess 1 (zero thinking)
2. **Looking up** guess 2 from a small table (near-zero thinking)
3. Using simple **heuristic rules** for guesses 3-6 (fast pattern matching)

---

## Guess 1: RAISE (memorized)

Always open with **RAISE**. No thinking required.

Why RAISE:
- Tests the 5 most informative letters (R, A, I, S, E)
- Highest expected information gain (5.88 bits) among common answer words
- Best worst-case partition (167) of any top opener
- It's an answer word itself (~0.04% instant win)

---

## Guess 2: Lookup Table (12 entries, covers 48% of games)

After RAISE, look at the feedback and use this table:

| RAISE Feedback       | What You See                  | Play     | New Letters Tested |
|----------------------|-------------------------------|----------|--------------------|
| ⬛⬛⬛⬛⬛          | All gray                      | **CLOTH**| C, L, O, T, H     |
| ⬛⬛⬛⬛🟨          | Only E is yellow              | **OLDEN**| O, L, D, N         |
| ⬛⬛🟨⬛⬛          | Only I is yellow              | **PILOT**| P, L, O, T         |
| 🟨⬛⬛⬛⬛          | Only R is yellow              | **COURT**| C, O, U, T         |
| 🟨⬛⬛⬛🟨          | R and E are yellow            | **DETER**| D, T               |
| ⬛🟨⬛⬛⬛          | Only A is yellow (wrong spot) | **FLOAT**| F, L, O, T         |
| ⬛🟩⬛⬛⬛          | A is green (right spot)       | **TANGY**| T, N, G, Y         |
| ⬛⬛⬛🟨⬛          | Only S is yellow              | **STUNK**| T, U, N, K         |
| 🟨🟨⬛⬛⬛          | R and A are yellow            | **ADORN**| D, O, N            |
| ⬛🟨⬛⬛🟨          | A and E are yellow            | **CLEAT**| C, L, T            |
| ⬛⬛⬛⬛🟩          | E is green (right spot)       | **LUNGE**| L, U, N, G         |
| ⬛⬛🟩⬛⬛          | I is green (right spot)       | **GLINT**| G, L, N, T         |

**If your pattern isn't in the table** (52% of games — you got multiple hits):
skip to the Guess 3+ heuristic below.

### How to memorize this

The table has a simple structure. After RAISE, look at your hits:

- **No hits:** CLOTH (the 5 most common untested letters)
- **One yellow letter:** The table word tests O, T, L, N plus places your yellow letter
  - E→OLDEN, I→PILOT, R→COURT, A→FLOAT, S→STUNK
- **A is green (pos 2):** TANGY
- **Two yellows:** DETER (R+E), ADORN (R+A), CLEAT (A+E)
- **E is green (pos 5):** LUNGE
- **I is green (pos 3):** GLINT

---

## Guesses 3-6: The Narrowing Heuristic

After guesses 1-2, you typically have fewer than 10 candidates left. Use these
principles in order:

### Rule 1: If you can think of only 1-2 possible words, just guess one.

### Rule 2: Test untested common letters.

The letter priority order (after RAISE already tested R, A, I, S, E):

> **O, T, L, N, U, C, Y, H, D, P, G, M, B**

Think of a valid word that satisfies your constraints AND contains as many
high-priority untested letters as possible.

### Rule 3: Beware the one-position trap.

If you know 4 of 5 letters (e.g., _OUND, _IGHT, _ATCH), **you're stuck** — hard
mode forces you to guess one candidate at a time. This is unavoidable. When you
recognize this pattern:

- **Count your remaining candidates.** If you have N candidates and only
  (6 - current_guess) guesses left, and N > guesses remaining, you might not
  solve it. This is rare (happens in ~0.5% of games).
- **Guess the most common candidate first** to maximize your odds.

### Rule 4: When stuck between many candidates, prefer words that would produce diverse feedback.

Pick the word where you'd expect the most *different* outcomes. A word that would
give you green-yellow-gray patterns against different candidates is better than
one that gives the same result against all of them.

---

## What to Expect

Based on simulation against all 2,309 Wordle answers:

| Guesses | % of Games |
|---------|-----------|
| 1       | 0.04%     |
| 2       | 5.7%      |
| 3       | 40.5%     |
| 4       | 40.8%     |
| 5       | 10.5%     |
| 6       | 2.5%      |
| Fail    | 0.5%      |

**Average: 3.64 guesses**

The ~0.5% failure rate comes from inherent hard-mode traps where many words
differ in exactly one position (_ATCH, _OUND, _IGHT, _OLLY, _ILLY, etc.).
No strategy can eliminate these in hard mode.

---

## Key Principles (the "why" behind the strategy)

1. **The 50% Principle:** A letter gives maximum information when it appears in
   ~50% of remaining candidates. E (45.6%) and A (39.2%) are closest to 50%
   across all answers — that's why they're in RAISE.

2. **Position matters more than presence:** A green result (correct position)
   eliminates far more candidates than a yellow. Testing common letters in their
   most frequent positions amplifies information gain.

3. **Distinct letters beat duplicates:** Each unique letter in a guess is a
   separate binary test (present/absent). Duplicate letters waste a slot.

4. **Information then exploitation:** Early guesses should maximize information
   (test many untested letters). Later guesses should exploit constraints to
   narrow to the answer.

5. **Hard mode's fundamental limit:** Once you lock in 4 greens with multiple
   valid completions, you can only try one per turn. The strategy minimizes how
   often you enter this state, but can't prevent it entirely.
