#!/usr/bin/env python3
"""Poll central bank speech feeds and report anything new since the last run.

State (which entries have already been seen) is persisted to state.json
next to this script, so consecutive runs -- including ones from a fresh
scheduled session that only has the repo, not this conversation's memory --
only report genuinely new speeches.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

from sources import SOURCES

STATE_PATH = Path(__file__).parent / "state.json"
MAX_SEEN_PER_SOURCE = 500
REQUEST_TIMEOUT = 20
USER_AGENT = "central-bank-speech-scanner/1.0 (+https://github.com/tomb-cpu/central-bank-speech-scanner)"


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def entry_id(entry):
    return entry.get("id") or entry.get("link")


def matches_filter(entry, keywords):
    if not keywords:
        return True
    haystack = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
    return any(kw in haystack for kw in keywords)


def fetch_source(source):
    resp = requests.get(source["url"], headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)
    return parsed.entries


def scan():
    state = load_state()
    new_items = []
    errors = []

    for source in SOURCES:
        sid = source["id"]
        first_run_for_source = sid not in state
        seen = set(state.get(sid, []))
        try:
            entries = fetch_source(source)
        except Exception as exc:  # network/parse errors shouldn't kill the whole run
            errors.append(f"{source['name']}: {exc}")
            continue

        keywords = source.get("filter_keywords")
        fresh_ids = []
        for entry in entries:
            eid = entry_id(entry)
            if not eid or eid in seen:
                continue
            if not matches_filter(entry, keywords):
                continue
            if not first_run_for_source:
                new_items.append({
                    "source": source["name"],
                    "title": entry.get("title", "(untitled)"),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                })
            fresh_ids.append(eid)

        all_ids = fresh_ids + [i for i in seen]
        state[sid] = all_ids[:MAX_SEEN_PER_SOURCE]

    save_state(state)
    return new_items, errors


def main():
    new_items, errors = scan()
    timestamp = datetime.now(timezone.utc).isoformat()

    if new_items:
        print(f"[{timestamp}] {len(new_items)} new speech(es):\n")
        for item in new_items:
            print(f"- [{item['source']}] {item['title']}")
            print(f"  {item['link']}")
            if item["published"]:
                print(f"  published: {item['published']}")
    else:
        print(f"[{timestamp}] No new speeches.")

    if errors:
        print("\nSource errors (non-fatal):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
