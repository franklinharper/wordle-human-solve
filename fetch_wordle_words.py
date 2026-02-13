#!/usr/bin/env python3
"""Fetch Wordle word lists from the NYT Wordle JavaScript bundle."""

import re
import json
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
    Returns a list of unique word-list candidates, largest first.
    """
    # Match JS array literals that contain only 5-letter lowercase words
    pattern = re.compile(r'\[("(?:[a-z]{5})",?\s*){20,}\]')
    candidates = []
    for match in pattern.finditer(js_text):
        words = re.findall(r'"([a-z]{5})"', match.group())
        if len(words) >= 20:
            candidates.append(words)
    # Deduplicate and sort largest first
    seen = set()
    unique = []
    for words in candidates:
        key = frozenset(words)
        if key not in seen:
            seen.add(key)
            unique.append(words)
    unique.sort(key=len, reverse=True)
    return unique


def main():
    print("Fetching Wordle page...")
    html = fetch(WORDLE_URL)

    parser = ScriptSrcParser()
    parser.feed(html)

    base = "https://www.nytimes.com"
    script_urls = [
        src if src.startswith("http") else base + src
        for src in parser.script_srcs
    ]

    if not script_urls:
        print("No <script src=...> tags found. The page structure may have changed.")
        return

    print(f"Found {len(script_urls)} script(s). Scanning for word lists...")

    all_candidates = []
    for url in script_urls:
        try:
            js = fetch(url)
            candidates = find_word_arrays(js)
            all_candidates.extend(candidates)
        except Exception as e:
            print(f"  Skipping {url}: {e}")

    if not all_candidates:
        print("No word lists found. The JS bundle format may have changed.")
        return

    # The two largest distinct arrays are typically:
    #   1. valid guesses (~14,000 words)
    #   2. answer list (~2,300 words)
    all_candidates.sort(key=len, reverse=True)

    print(f"\nFound {len(all_candidates)} candidate word list(s):\n")
    for i, words in enumerate(all_candidates):
        label = "valid_guesses" if i == 0 else "answers" if i == 1 else f"list_{i}"
        filename = f"wordle_{label}.json"
        with open(filename, "w") as f:
            json.dump(sorted(words), f, indent=2)
        print(f"  [{i+1}] {len(words):>6} words  ->  {filename}")


if __name__ == "__main__":
    main()
