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

### Rule 2: Test untested common letters — scan by the chant, not the keyboard.

**The after-RAISE chant: OTLN – UCY – HDPM – GBF** — the letters RAISE
doesn't test, ordered by how many answers contain them (O and T each
appear in 29% of answers, L in 28%, N in 24%). Since RAISE is always
guess 1, this is the scan every letter hunt uses:

- Run the chant from the top and take the first letter that is still
  untested and fits the frame.
- The on-screen keyboard shows which letters are still alive — use it
  only as that liveness check, never as the scan order. Keyboard order
  is geography, not usefulness: it gives Q and W the first auditions,
  and they are among the rarest letters in answers.
- If every chant letter is already known or dead, the chant is
  exhausted — what remains is K, W, V, and then the rarest letters
  of all — Z, X, Q, J, each in under 2% of answers. From there, work
  from the candidates themselves.
- Prefer a word that smuggles in **two** high chant letters over one
  that tests a single letter — e.g. after RAISE came back with R, I, E
  yellow, OILER (new: O, L) over WIRER (new: only W).

Where the chant comes from: the 12 most common letters across all
answers are E, A, R, O, T, L, I, S, N, C, U, Y (~74% of all letter
slots). Strike out the five letters RAISE already tests and rank
everything that remains by answers containing the letter (which
swaps two near-ties: U before C, M before G): O, T, L, N, U, C, Y,
H, D, P, M, G, B, F, K, W, V, Z, X, Q, J. The chant takes the first
fourteen, through F. The cut is reachability, not frequency: each
of the fourteen can be the first untested letter on a real board
played by this system — RAISE, the table word, then answer words
(the deck's drills are those boards) — and K, W, V and the rarest
four have no such board, so they are not in the chant.

**The ending-pair scan.** When slots 4–5 are both still open and
the word doesn't end in Y, don't scan letter by letter — scan the
common two-consonant endings, grouped by first letter: **CH CK –
NG NT NK ND – ST SH SS – TH – LL LT LD – RT RD RN RK – MP – WN –
FF FT – HT – PT – GH**. Those 24 pairs cover 87% of answers that
end in two consonants with a non-Y last letter. Work group by
group, pair by pair, generating whole words and testing each for
recognition; the pair is the unit — K is never tested alone, it
rides in on CK, NK and RK. Skip any pair containing a letter
already known dead. If the system's own guesses have already
pinned one letter of a pair green at slot 4 or 5, the scan's job
is just the other letter. If no pair produces a word, fall back
to the chant, slot by slot. Endings in Y are a different problem —
see the doubles paragraph below. One structural exception: ST,
SH and SS endings pin S green at slot 4 from RAISE itself, and
no table word carries S at slot 4, so those games have no
mnemonic guess 2 — probe with an S-word instead (STASH, AMASS,
BLAST).

The deck's pair drills add two rules of their own. A drill board
must cue the pair it trains: at least one letter of the pair
shows yellow or green on the board — an ending reachable only by
exhaustive elimination trains nothing. And while a drill's
answer is the board's only completion over the candidate pool,
the board can admit other words from the guess list; the drill
names them on its back ("— also …"), because from the seat they
are possible solutions too — the guess list is what the game
enforces, and the answer list is a snapshot, not a boundary.

**The triple scans.** When three slots in a row are all
consonants — the shape that stalls generation — don't
free-associate; run the triple scan for that end of the word.
Endings (slots 3–5): **TCH · NCH · RCH · LCH · GHT · RTH ·
NTH · RST · MPH · RSH** — ten triples covering about
four-fifths of answers that end in three consonants. Most
are the pair scan's pairs with one letter in front: CH takes
T, N, R, L; HT takes G; TH takes R, N. Openings (slots 1–3):
**STR · SCR · THR · SHR · SPR · SPL**. Skip any triple
containing a letter already known dead; if no triple
produces a word, fall back to the chant, slot by slot.
Triples in the middle (slots 2–4) are a long tail — search
them, don't scan them.

**The one-gap scan.** When exactly one slot is open and no
word surfaces, don't free-associate and don't scan the
keyboard — slot letters through the gap one at a time and
pronounce each skeleton, the way Floating Yellows does. The
order is the chant — OTLN – UCY – HDPM – GBF, then its tail
(K, W, V, then Z, X, Q, J): no new order to learn, and after
RAISE the only vowels a gap can hide are O and U, which the
chant reaches first and fifth (A, I and E are settled by the
opener in every game — placed, yellow, or dead). Skip only
letters the board has killed; never skip a letter for
already being on the board — the gap may be its double.
Recognition is the filter: a skeleton that sounds like a
word is the candidate; one that doesn't is discarded and
the scan moves on.

**Floating yellows.** When three letters are yellow and none is
placed, don't hunt for a word that merely contains them — a
familiar word will happily park one in a slot the board already
ruled out (ALOHA after FLOAT, in the LOAMY game). Place them by
slots instead: anchor the most constrained yellow first (the one
with the fewest legal slots), fit the others around it, and
pronounce each skeleton — words surface by sound (_ _ A _ _ with
O at 2 sounds out LOA—, and LOAMY is there). Fill the remaining
slots from the chant, in order. Before playing, check: every
yellow present, and no yellow sitting in a slot where it already
showed yellow.

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

Exception at two: when exactly two candidates remain, guess one of them. A probe
that cannot itself be the answer extracts the same information as picking a
candidate, but it can never end the game — on the clock it is strictly worse. A
discriminator earns its slot only when it is itself one of the candidates
(SHOOT, in the SCOOT game) or when the set is bigger than two.

**Buy information with fresh letters.** From the seat you never know how many
candidates remain — you are searching, not counting. A guess that tests two
fresh letters rules on more of the unsearched space than one that spends the
guess doubling a single unconfirmed letter. (After RAISE / PILOT / DINGY:
DICKY tests C and K; DIZZY spends the whole guess on Z, twice.)

**Doubles are always in play.** Nothing on the board rules out a second copy
of a letter unless a gray copy caps its count — a green or yellow letter can
always appear again in another slot. 15% of answers contain a doubled letter,
and 226 double a consonant (NUTTY's TT; SCOOT's and YAHOO's OO). When a frame
feels exhausted, try doubling a letter already on the board before scanning
further afield.

The sharpest case is a word ending in Y: 28% of Y-ending answers are
_ _ CCY — the consonant before the Y doubles (CANNY, TALLY, NUTTY).
With Y pinned at 5, reach for that shape early.

But the two slots before the Y are a pair in their own right,
scanned the way the ending-pair scan scans slots 4–5 — and the
pair is usually mixed: 72% of Y-ending answers carry two
different consonants there, not a double. On an open Y-frame,
default to two different consonants in those slots: the play
tests two letters instead of one and can solve just as well.
Play the double when it is a live candidate, not by default.
The limiting case is the old HAPPY board (RAISE / TANGY /
BAWDY): its completions over the answer list are all doubles —
HAPPY, JAZZY, MAMMY — yet its best play is CAMPY, a mixed pair
that can itself be the answer and whose feedback names every
double. And a board that drills the CCY shape must admit no
plausible mixed-pair word: purity is judged over the guess
list, not the answer list alone.

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
