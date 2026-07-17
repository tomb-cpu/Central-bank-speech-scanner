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

## Scheduling & notifications

A GitHub Actions workflow (`.github/workflows/scan.yml`) runs the scanner
every 6 hours (and on demand via "Run workflow" on the Actions tab). When
new speeches are found it:

1. Commits the updated `scanner/state.json`.
2. Posts the list of new speeches as a comment on the rolling
   **"Central bank speech alerts"** issue (label: `speech-alerts`).

**To get notified:** subscribe to that issue (or Watch → All activity on
the repo). GitHub then delivers each alert to you by email and/or the
GitHub mobile app, per your own notification settings — this works for any
collaborator, so teammates just need repo access plus a subscription to
the issue.

To switch to Slack/Teams/direct email later, replace the "Notify via issue
comment" step with a webhook or SMTP action using a repo secret.

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
