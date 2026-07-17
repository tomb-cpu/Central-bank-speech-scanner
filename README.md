# Central Bank Speech Scanner

Polls speech feeds from the BIS (which aggregates ~60 member central banks)
plus direct feeds from the Fed, ECB, BoE, BoJ, RBA, and BoC, and reports
anything not seen before.

## How it works

- `scanner/sources.py` — the list of feeds polled.
- `scanner/scan.py` — fetches each feed, diffs against `scanner/state.json`
  (which entries have already been reported), prints new ones, and updates
  the state file.
- `scanner/state.json` is committed to the repo so state survives across
  runs, including runs from a fresh scheduled session that has no memory of
  previous ones.

The first run for any given source only seeds state — it doesn't report a
flood of everything currently in that feed as "new."

## Running it manually

```bash
cd scanner
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scan.py
```

## Scheduling

This repo is scanned automatically by a Claude Code Routine: on a cron
schedule, a fresh session clones the repo, runs `scan.py`, and if new
speeches were found, pushes a phone notification and commits the updated
`state.json` back to this branch. No manual triggering needed.

## Adding a central bank

Add an entry to `SOURCES` in `scanner/sources.py`:

```python
{
    "id": "unique_short_id",
    "name": "Human-readable name",
    "url": "https://.../feed.xml",
    "kind": "rss",
    "filter_keywords": ["speech"],  # optional: only keep entries whose
                                     # title/summary contains one of these
}
```
