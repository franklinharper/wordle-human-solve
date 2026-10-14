#!/usr/bin/env python3
"""Fetch Wordle word lists.

The two lists come from two different NYT sources (as of Oct 2026 the NYT
serves them differently):

  valid guesses -- extracted from the NYT Wordle JavaScript bundle
                   (https://www.nytimes.com/games/wordle/index.html).
                   Still present in the bundle; re-downloaded on refresh.
  valid answers -- collected forward from the NYT daily solution endpoint
                   (https://www.nytimes.com/svc/wordle/v2/YYYY-MM-DD.json),
                   because the bundle no longer contains the answer list.
                   Each newly observed solution is inserted into answers.txt
                   (which stays a clean sorted word list) and its first-seen
                   date is recorded in answers_observed.json.

Update policy: fetched data is validated before anything is written.
The repo's canonical files are only replaced when every check passes.
Any failure keeps the old files byte-identical, prints a loud error,
and exits non-zero.

Environment overrides (mainly for testing):
  WORDLE_URL            page URL the guess-list bundle is scraped from
  WORDLE_SOLUTION_URL   template for the daily solution endpoint, with
                        {date} for YYYY-MM-DD
  WORDLE_BACKFILL_START first date collected when answers_observed.json
                        does not exist yet (default 2026-02-17)
"""

import datetime
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from zoneinfo import ZoneInfo


WORDLE_URL = os.environ.get(
    "WORDLE_URL", "https://www.nytimes.com/games/wordle/index.html"
)
SOLUTION_URL_TEMPLATE = os.environ.get(
    "WORDLE_SOLUTION_URL",
    "https://www.nytimes.com/svc/wordle/v2/{date}.json",
)
BACKFILL_START = os.environ.get("WORDLE_BACKFILL_START", "2026-02-17")

REQUEST_TIMEOUT = 20
POLITE_DELAY = 0.2  # seconds between daily-solution requests
LA_TZ = ZoneInfo("America/Los_Angeles")
MIN_GUESSES = 10000  # sanity floor for the guess list

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

GUESSES_FILE = "wordle_valid_guesses.json"
ANSWERS_FILE = "answers.txt"
OBSERVED_FILE = "answers_observed.json"
META_FILE = "wordlists.meta.json"


# --- Error types -----------------------------------------------------------

class WordleRefreshError(Exception):
    """Base class for refresh failures. Carries a one-line remediation hint."""

    hint = "set WORDLE_STALE_OK=1 to proceed on stale data anyway."

    def label(self):
        return "refresh failure"


class NetworkError(WordleRefreshError):
    hint = ("check the network/proxy, then retry; "
            "or set WORDLE_STALE_OK=1 to proceed on stale data anyway.")

    def label(self):
        return "network failure"


class BundleFormatError(WordleRefreshError):
    hint = ("the NYT changed their bundle format -- the guess-list extractor "
            "in fetch_wordle_words.py needs updating; "
            "or set WORDLE_STALE_OK=1 to proceed on stale data anyway.")

    def label(self):
        return "NYT bundle format change"


class ValidationError(WordleRefreshError):
    hint = ("fetched data failed sanity checks -- refusing to use it; "
            "inspect the fetched data manually, "
            "or set WORDLE_STALE_OK=1 to proceed on stale data anyway.")

    def label(self):
        return "validation failure"


# --- Fetch helpers ----------------------------------------------------------

def repo_path(repo_root, name):
    return os.path.join(repo_root, name)


def fetch(url, timeout=REQUEST_TIMEOUT):
    """Fetch a URL as text. Network problems -> NetworkError."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError:
        raise
    except Exception as e:
        raise NetworkError(f"could not fetch {url}: {e}")


def fetch_solution(date_iso):
    """Fetch one day's solution JSON.

    Returns (solution, days_since_launch), or (None, None) when the
    puzzle is not published yet (HTTP 404) -- that is expected, not
    a failure.
    """
    url = SOLUTION_URL_TEMPLATE.format(date=date_iso)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None
        raise NetworkError(f"solution endpoint returned HTTP {e.code} for {date_iso}")
    except Exception as e:
        raise NetworkError(f"could not fetch solution for {date_iso}: {e}")
    return data.get("solution"), data.get("days_since_launch")


class ScriptSrcParser(HTMLParser):
    """Extract src attributes from <script> tags."""

    def __init__(self):
        super().__init__()
        self.script_srcs = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            src = dict(attrs).get("src", "")
            if src:
                self.script_srcs.append(src)


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
            seen = set()
            unique = [w for w in words if not (w in seen or seen.add(w))]
            candidates.append(unique)
    seen = set()
    unique_lists = []
    for words in candidates:
        key = frozenset(words)
        if key not in seen:
            seen.add(key)
            unique_lists.append(words)
    unique_lists.sort(key=len, reverse=True)
    return unique_lists


def atomic_write_json(path, obj):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
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


def check(condition, label):
    """Print a check result line; return the condition."""
    print(f"    - {label} {'.' * (42 - len(label))} {'OK' if condition else 'FAIL'}")
    return condition


def load_current(repo_root):
    """Load the current canonical files; missing files -> empty sets/dicts."""
    guesses, answers, observed = set(), set(), {}
    gp = repo_path(repo_root, GUESSES_FILE)
    ap = repo_path(repo_root, ANSWERS_FILE)
    op = repo_path(repo_root, OBSERVED_FILE)
    if os.path.exists(gp):
        with open(gp) as f:
            guesses = set(json.load(f))
    if os.path.exists(ap):
        with open(ap) as f:
            answers = {line.strip() for line in f if line.strip()}
    if os.path.exists(op):
        with open(op) as f:
            observed = json.load(f)
    return guesses, answers, observed


# --- Refresh paths (importable) ---------------------------------------------

def refresh_guesses(repo_root):
    """Re-download the valid-guess list from the NYT JS bundle.

    Returns {"added": [...], "removed": [...], "changed": bool}.
    Raises NetworkError / BundleFormatError / ValidationError.
    """
    try:
        html = fetch(WORDLE_URL)
    except urllib.error.HTTPError as e:
        raise NetworkError(f"NYT Wordle page returned HTTP {e.code}")

    parser = ScriptSrcParser()
    parser.feed(html)
    base = "https://www.nytimes.com"
    script_urls = [
        src if src.startswith(("http://", "https://", "file://")) else base + src
        for src in parser.script_srcs
    ]
    if not script_urls:
        raise BundleFormatError(
            "no <script src=...> tags found on the NYT Wordle page; "
            "the page structure may have changed")

    candidates = []
    for url in script_urls:
        try:
            candidates.extend(find_word_arrays(fetch(url)))
        except Exception as e:
            # One bad script URL must not kill the refresh; the page
            # itself already fetched fine, so this is just a stale link.
            print(f"  (skipping script, fetch failed: {e})")

    if not candidates:
        raise BundleFormatError(
            "could not identify the valid-guess word array in the NYT bundle; "
            "the bundle format may have changed")

    guesses = max(candidates, key=len)

    ok_words = all(len(w) == 5 and w.isalpha() and w == w.lower() for w in guesses)
    if not ok_words:
        raise ValidationError("guess list contains malformed words")
    if len(guesses) < MIN_GUESSES:
        raise ValidationError(
            f"guess list has {len(guesses)} words, below sanity floor {MIN_GUESSES}")

    old_guesses, _, _ = load_current(repo_root)
    added = sorted(set(guesses) - old_guesses)
    removed = sorted(old_guesses - set(guesses))
    changed = bool(added or removed)
    if changed:
        atomic_write_json(repo_path(repo_root, GUESSES_FILE), sorted(guesses))
    return {"added": added, "removed": removed, "changed": changed,
            "count": len(guesses)}


def refresh_answers(repo_root):
    """Forward-collect daily solutions from the NYT solution endpoint.

    Walks every date from (last recorded date + 1) through today
    (America/Los_Angeles), so missed days self-heal. New solutions are
    inserted into answers.txt (kept sorted); first-seen dates go into
    answers_observed.json.

    Returns {"added": [(word, date)], "checked": n_days, "changed": bool}.
    Raises NetworkError / ValidationError.
    """
    _, answers, observed = load_current(repo_root)

    if observed:
        last = max(observed.values())
        start = (datetime.date.fromisoformat(last)
                 + datetime.timedelta(days=1)).isoformat()
    else:
        start = BACKFILL_START
    today = datetime.datetime.now(LA_TZ).date().isoformat()

    added = []
    checked = 0
    expected_n = None  # days_since_launch continuity tracker
    d = start
    while d <= today:
        solution, n = fetch_solution(d)
        if solution is None:
            print(f"  (no solution published yet for {d}; skipping)", file=sys.stderr)
            d = (datetime.date.fromisoformat(d)
                 + datetime.timedelta(days=1)).isoformat()
            continue
        checked += 1
        if not (isinstance(solution, str) and len(solution) == 5
                and solution.isalpha() and solution == solution.lower()):
            raise ValidationError(
                f"solution for {d} is malformed: {solution!r}")
        if expected_n is not None and n != expected_n:
            raise ValidationError(
                f"days_since_launch discontinuity at {d}: got {n}, "
                f"expected {expected_n}")
        expected_n = (n + 1) if isinstance(n, int) else None
        if solution not in answers:
            answers.add(solution)
            observed[solution] = d
            added.append((solution, d))
        time.sleep(POLITE_DELAY)
        d = (datetime.date.fromisoformat(d)
             + datetime.timedelta(days=1)).isoformat()

    changed = bool(added)
    if changed:
        atomic_write_txt(repo_path(repo_root, ANSWERS_FILE), answers)
        atomic_write_json(repo_path(repo_root, OBSERVED_FILE), observed)
    return {"added": added, "checked": checked, "changed": changed,
            "count": len(answers)}


def write_meta(repo_root):
    meta = {
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sources": {
            "guesses": WORDLE_URL,
            "answers": SOLUTION_URL_TEMPLATE,
        },
    }
    atomic_write_json(repo_path(repo_root, META_FILE), meta)
    return meta


def refresh_all(repo_root):
    """Run both refresh paths; write the meta file on success.

    Returns {"guesses": {...}, "answers": {...}, "changed": bool}.
    Raises WordleRefreshError on any failure (files left untouched).
    """
    g = refresh_guesses(repo_root)
    a = refresh_answers(repo_root)
    write_meta(repo_root)
    return {"guesses": g, "answers": a,
            "changed": g["changed"] or a["changed"]}


# --- CLI ---------------------------------------------------------------------

def fail(msg):
    print(f"  ERROR: {msg}", file=sys.stderr)
    print("  Keeping existing word lists unchanged.", file=sys.stderr)
    sys.exit(1)


def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    today = datetime.datetime.now(LA_TZ).date().isoformat()
    print(f"Wordle word lists, refreshed {today} (America/Los_Angeles):\n")

    try:
        summary = refresh_all(repo_root)
    except WordleRefreshError as e:
        fail(f"{e.label()}: {e}\n  Hint: {e.hint}")
    except Exception as e:  # fail closed on anything unexpected too
        fail(f"unexpected error: {e}\n  Hint: {WordleRefreshError.hint}")

    g, a = summary["guesses"], summary["answers"]
    print(f"  valid guesses: {g['count']:,} words "
          f"(+{len(g['added'])} added, -{len(g['removed'])} removed)")
    if g["added"]:
        print(f"    added: {', '.join(g['added'][:10])}"
              f"{'...' if len(g['added']) > 10 else ''}")
    if g["removed"]:
        print(f"    removed: {', '.join(g['removed'][:10])}"
              f"{'...' if len(g['removed']) > 10 else ''}")
    print(f"  valid answers: {a['count']:,} words "
          f"(+{len(a['added'])} newly observed, {a['checked']} days checked)")
    for word, date in a["added"][:20]:
        print(f"    + {word} (first seen {date})")
    if len(a["added"]) > 20:
        print(f"    ... and {len(a['added']) - 20} more")

    if not summary["changed"]:
        print("\n  lists unchanged; files left as-is (freshness clock reset).")
    else:
        print("\n  updated: word lists changed -- consider committing.")


if __name__ == "__main__":
    main()
