#!/usr/bin/env python3
"""Fetch Wordle word lists from the NYT Wordle JavaScript bundle.

The two lists, unambiguously:
  valid guesses -- Every word the game accepts as a guess. Includes all answers.
  answers       -- Words that can be the day's solution.

Update policy: the fetched lists are validated before anything is written.
The repo's canonical files (wordle_valid_guesses.json, answers.txt) are only
replaced when every check passes. Any failure keeps the old files
byte-identical, prints a loud error, and exits non-zero.
"""

import datetime
import json
import os
import re
import sys
import tempfile
import urllib.request
from html.parser import HTMLParser


WORDLE_URL = "https://www.nytimes.com/games/wordle/index.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

GUESSES_FILE = "wordle_valid_guesses.json"
ANSWERS_FILE = "answers.txt"

DESC_GUESSES = "Every word the game accepts as a guess. Includes all answers."
DESC_ANSWERS = "Words that can be the day's solution."


class ScriptSrcParser(HTMLParser):
    """Extract src attributes from <script> tags."""

    def __init__(self):
        super().__init__()
        self.script_srcs = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attrs_dict = dict(attrs)
            src = attrs_dict.get("src", "")
            if src:
                self.script_srcs.append(src)


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def find_word_arrays(js_text):
    """
    Search for arrays of 5-letter lowercase words in the JS bundle.
    Returns unique word-list candidates, largest first.
    """
    pattern = re.compile(r'\[("(?:[a-z]{5})",?\s*){20,}\]')
    candidates = []
    for match in pattern.finditer(js_text):
        words = re.findall(r'"([a-z]{5})"', match.group())
        if len(words) >= 20:
            # Deduplicate preserving order
            seen = set()
            unique = [w for w in words if not (w in seen or seen.add(w))]
            candidates.append(unique)
    # Deduplicate whole lists, largest first
    seen = set()
    unique_lists = []
    for words in candidates:
        key = frozenset(words)
        if key not in seen:
            seen.add(key)
            unique_lists.append(words)
    unique_lists.sort(key=len, reverse=True)
    return unique_lists


def identify_lists(candidates):
    """Identify (guesses, answers) from candidate arrays.

    The guess list is the largest array; the answer list is the largest
    remaining array that is a subset of it. Identifies by content, not
    by position, so a reordered bundle can't silently mislabel the lists.
    """
    if not candidates:
        return None, None
    by_size = sorted(candidates, key=len, reverse=True)
    guesses = by_size[0]
    guess_set = set(guesses)
    for words in by_size[1:]:
        if set(words) <= guess_set:
            return guesses, words
    return None, None


def check(condition, label):
    """Print a check result line; return the condition."""
    print(f"    - {label} {'.' * (42 - len(label))} {'OK' if condition else 'FAIL'}")
    return condition


def fail(msg):
    print(f"  ERROR: {msg}")
    print("  Keeping existing word lists unchanged.")
    sys.exit(1)


def load_current():
    """Load the current canonical files; missing files -> empty sets."""
    guesses, answers = set(), set()
    if os.path.exists(GUESSES_FILE):
        with open(GUESSES_FILE) as f:
            guesses = set(json.load(f))
    if os.path.exists(ANSWERS_FILE):
        with open(ANSWERS_FILE) as f:
            answers = {line.strip() for line in f if line.strip()}
    return guesses, answers


def atomic_write_json(path, words):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(sorted(words), f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_txt(path, words):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            for w in sorted(words):
                f.write(w + "\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main():
    today = datetime.date.today().isoformat()
    print(f"Wordle word lists, fetched {today} from nytimes.com/games/wordle:\n")

    try:
        html = fetch(WORDLE_URL)
    except Exception as e:
        fail(f"could not fetch NYT Wordle page: {e}")

    parser = ScriptSrcParser()
    parser.feed(html)
    base = "https://www.nytimes.com"
    script_urls = [
        src if src.startswith("http") else base + src
        for src in parser.script_srcs
    ]
    if not script_urls:
        fail("no <script src=...> tags found; the NYT page structure may have changed")

    candidates = []
    for url in script_urls:
        try:
            candidates.extend(find_word_arrays(fetch(url)))
        except Exception as e:
            print(f"  (skipping script, fetch failed: {e})")
    # Re-sort after merging across scripts
    seen = set()
    merged = []
    for words in sorted(candidates, key=len, reverse=True):
        key = frozenset(words)
        if key not in seen:
            seen.add(key)
            merged.append(words)

    guesses, answers = identify_lists(merged)
    if guesses is None or answers is None:
        fail("could not identify guess/answer lists in the NYT bundle; "
             "the bundle format may have changed")

    print(f"  valid guesses: {len(guesses):,} words -> {GUESSES_FILE}")
    print(f"      {DESC_GUESSES}")
    print(f"  answers:        {len(answers):,} words -> {ANSWERS_FILE}")
    print(f"      {DESC_ANSWERS}")
    print("\n  checks against the NYT data:")

    ok = True
    ok &= check(all(len(w) == 5 and w.isalpha() and w == w.lower()
                    for w in guesses + answers),
                "all words 5 letters, lowercase")
    ok &= check(set(answers) <= set(guesses), "every answer is a valid guess")
    if not ok:
        fail("sanity check failed; refusing to overwrite the word lists")

    old_guesses, old_answers = load_current()
    g_added = sorted(set(guesses) - old_guesses)
    g_removed = sorted(old_guesses - set(guesses))
    a_added = sorted(set(answers) - old_answers)
    a_removed = sorted(old_answers - set(answers))

    print("\n  diff vs current files:")
    print(f"    - valid guesses: +{len(g_added)} added, -{len(g_removed)} removed"
          + (f" ({', '.join(g_added[:10])}{'...' if len(g_added) > 10 else ''}"
             if g_added else "")
          + (f" | removed: {', '.join(g_removed[:10])}"
             f"{'...' if len(g_removed) > 10 else ''}" if g_removed else ""))
    print(f"    - answers:       +{len(a_added)} added, -{len(a_removed)} removed"
          + (f" ({', '.join(a_added[:10])}{'...' if len(a_added) > 10 else ''}"
             if a_added else "")
          + (f" | removed: {', '.join(a_removed[:10])}"
             f"{'...' if len(a_removed) > 10 else ''}" if a_removed else ""))

    if not g_added and not g_removed and not a_added and not a_removed:
        print("\n  lists unchanged; files left as-is.")
        return

    atomic_write_json(GUESSES_FILE, guesses)
    atomic_write_txt(ANSWERS_FILE, answers)
    print(f"\n  updated: {GUESSES_FILE}, {ANSWERS_FILE}")


if __name__ == "__main__":
    main()
