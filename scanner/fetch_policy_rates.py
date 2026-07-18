#!/usr/bin/env python3
"""
fetch_policy_rates.py
---------------------
Fetches current G10 central bank policy rates from the BIS SDMX Stats API
(dataflow WS_CBPOL, daily frequency). Stdlib only, no deps.

Note: the BIS *stats* API carries no speeches — it complements the feeds
by providing the policy-rate backdrop for the daily briefing.

Usage:
    python fetch_policy_rates.py            # markdown table to stdout
    python fetch_policy_rates.py --json     # JSON to stdout

Output columns: jurisdiction, current rate, as-of date, and the most
recent change visible in the lookback window (default 400 days).
"""

import argparse
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta

API = "https://stats.bis.org/api/v1/data/WS_CBPOL/D.{areas}/all?startPeriod={start}"

AREAS = {
    "US": "Federal Reserve (US)",
    "XM": "ECB (Euro area)",
    "JP": "Bank of Japan",
    "GB": "Bank of England",
    "CA": "Bank of Canada",
    "AU": "RBA (Australia)",
    "NZ": "RBNZ (New Zealand)",
    "CH": "SNB (Switzerland)",
    "SE": "Riksbank (Sweden)",
    "NO": "Norges Bank (Norway)",
}

LOOKBACK_DAYS = 400


def localname(tag):
    return tag.rsplit("}", 1)[-1]


def fetch_series():
    start = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()
    url = API.format(areas="+".join(AREAS), start=start)
    req = urllib.request.Request(url, headers={"User-Agent": "cb-speech-scanner/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        xml = r.read().decode("utf-8", errors="replace")

    root = ET.fromstring(xml)
    series = {}
    for el in root.iter():
        if localname(el.tag) != "Series":
            continue
        area = el.get("REF_AREA")
        obs = []
        for o in el:
            if localname(o.tag) != "Obs":
                continue
            val = o.get("OBS_VALUE")
            if val in (None, "", "NaN"):
                continue
            obs.append((o.get("TIME_PERIOD"), float(val)))
        obs.sort()
        if area and obs:
            series[area] = obs
    return series


def summarize(series):
    rows = []
    for area, name in AREAS.items():
        obs = series.get(area)
        if not obs:
            rows.append({"area": area, "institution": name, "rate": None,
                         "as_of": None, "last_change": None})
            continue
        as_of, rate = obs[-1]
        last_change = None
        for i in range(len(obs) - 1, 0, -1):
            if obs[i][1] != obs[i - 1][1]:
                delta_bp = round((obs[i][1] - obs[i - 1][1]) * 100)
                last_change = {"date": obs[i][0], "delta_bp": delta_bp}
                break
        rows.append({"area": area, "institution": name, "rate": rate,
                     "as_of": as_of, "last_change": last_change})
    return rows


def to_markdown(rows):
    lines = [
        "| Institution | Policy rate | As of | Last change |",
        "|---|---|---|---|",
    ]
    for r in rows:
        if r["rate"] is None:
            lines.append(f"| {r['institution']} | n/a | — | — |")
            continue
        chg = r["last_change"]
        if chg:
            sign = "+" if chg["delta_bp"] > 0 else ""
            chg_txt = f"{sign}{chg['delta_bp']} bp on {chg['date']}"
        else:
            chg_txt = f"none in last {LOOKBACK_DAYS} days"
        lines.append(f"| {r['institution']} | {r['rate']:.2f}% | {r['as_of']} | {chg_txt} |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        rows = summarize(fetch_series())
    except Exception as e:
        print(f"BIS stats API error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print(to_markdown(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
