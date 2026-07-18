# G10 Central Bank Briefing — agent instructions

You are producing the daily BCA Research-style briefing of G10 central bank
communications. You run unattended in CI: never ask questions, never wait
for input. Work from the repository root.

## Step 0 — Establish the window and what's already covered

- The window is the last 2 calendar days (the fetch script is date-based,
  so 2 days is needed to cover "the last ~24 hours" without gaps).
- List `briefings/` and read the most recent briefing file. Anything
  already covered there must be EXCLUDED from today's briefing — today's
  product is incremental.

## Step 1 — Fetch from direct CB feeds

Run:

```bash
python3 scanner/fetch_window.py --days 2
```

This pulls formal speeches from the Fed, ECB (speeches/interviews), BoE,
BoC, and RBA, and prints structured JSON to stdout. Read it fully. Note
any per-feed FAIL lines on stderr for the Coverage Notes section.

Do NOT use the BIS feed for this briefing — its 1–5 day publication lag
makes it unsuitable (it remains in `scanner/scan.py` only for the separate
link-alert workflow).

## Step 1b — Policy rate backdrop (BIS SDMX Stats API)

Run:

```bash
python3 scanner/fetch_policy_rates.py
```

This prints a markdown table of current G10 policy rates (with the most
recent change per bank) from the BIS statistical API. Include it verbatim
in the briefing's "Policy rate backdrop" section. Use the last-change
column as context when judging speech signals (e.g. a "hawkish" read means
more when a bank just cut). If the script fails, note that in Coverage
Notes and continue without the table.

## Step 2 — Newswire search

Run targeted web searches to catch interviews, Q&A comments, and press
conference remarks not captured by formal speech feeds. These are often
more market-relevant than speeches. The G10 institutions without reliable
RSS — BoJ, SNB, Riksbank, Norges Bank, RBNZ — are covered ONLY by this
step, so search for them explicitly.

Query patterns (adapt dates to the window):
- `Fed ECB BoE BoJ RBA central bank remarks comments [date range] Reuters Bloomberg`
- `[policymaker name] interview remarks [date range]` — focus on governors
  and deputies from `briefing/policymakers.md`
- For the ECB specifically, search Governing Council members individually
  when activity is high

The roster in `briefing/policymakers.md` is a periodically-updated
snapshot. If a name looks stale (e.g. a term has ended), verify the
current officeholder with a quick search rather than trusting the file.

Sources to accept: Reuters, Bloomberg, Financial Times. Reject:
aggregators, retail FX blogs, social media.

Only include items where a named policymaker made on-the-record statements
about monetary policy, rates, or the economic outlook. Exclude: ceremonial
remarks, regulatory speeches with no policy content, attributed
paraphrases without direct quotes.

## Step 3 — Fetch full text

For each item from Steps 1–2, fetch the source page and extract the speech
body (skip nav, footers, boilerplate). If full text is unavailable
(paywalled, JS-rendered, or 403), work from the available
description/title/quotes and flag this explicitly in the briefing.

## Step 4 — Write the briefing

Write the briefing to `briefings/YYYY-MM-DD.md` (today's UTC date).

### Format

```
# BCA Research — G10 Central Bank Briefing
### [Date range covered]
*Sources: [feeds used] + Reuters/Bloomberg newswire search*

**[N] communications across [N] institutions**

## Policy rate backdrop
*Source: BIS SDMX Stats API (WS_CBPOL)*

[table from fetch_policy_rates.py]

---

## [Institution]

### [Speaker]: *[Title or topic]*
*[Date] · [Venue/context] · [Source URL]*

**Signal: [Hawkish / Dovish / Neutral / Data-dependent / Non-monetary policy] — [one-line characterisation]**

[3–5 sentence analytical summary: policy signal, key substantive points,
any shift in language, rates market relevance]

---

## Coverage Notes
[Anything material that may have been missed; feed failures this run;
feed lag caveats; upcoming events to watch]
```

### Analytical standards

- State only what the speaker actually said. Do not infer beyond the text.
- Flag if a speech is ceremonial or lacks policy content rather than
  forcing an analysis.
- Be precise on signal: avoid "mixed" unless genuinely so — identify the
  dominant direction.
- Note explicitly when a communication was reported via newswire rather
  than published as a formal speech.

### If nothing found

Still write the briefing file, stating clearly: "No G10 central bank
communications found in the window across monitored feeds and newswire
search." Include a brief note on pre-meeting blackout periods if relevant.

## Step 5 — Publish

1. Commit `briefings/YYYY-MM-DD.md` with message
   `Daily G10 briefing YYYY-MM-DD` and push to the current branch
   (`git push origin HEAD`). If the push is rejected, `git pull --rebase`
   and retry.
2. Post the full briefing text as a comment on the rolling briefing issue
   using the `gh` CLI (GH_TOKEN is set in the environment):
   - Ensure the label exists:
     `gh label create cb-briefings --color 0E8A16 --description "Daily G10 central bank briefings" --force`
   - Find the open issue labeled `cb-briefings`; if none exists, create it
     with title "Daily G10 central bank briefings" and a body inviting
     teammates to subscribe.
   - `gh issue comment <number> --body-file briefings/YYYY-MM-DD.md`
