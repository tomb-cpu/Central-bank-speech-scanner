#!/usr/bin/env python3
"""
fetch_window.py
---------------
Fetches G10 central bank speeches from direct CB RSS feeds for a given
time window. Used by the daily briefing workflow (stdlib only, no deps).

Excludes BIS: its 1-5 day publication lag makes it unsuitable for a daily
briefing (it stays in scan.py for the broad-coverage link alerts instead).

Usage:
    python fetch_window.py --days 1
    python fetch_window.py --days 7
    python fetch_window.py --date 2026-04-09

Output: JSON list to stdout. Per-feed status goes to stderr.
"""

import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime

FEEDS = {
    "Federal Reserve (US)": {
        "url": "https://www.federalreserve.gov/feeds/speeches.xml",
        "parser": "rss2",
    },
    "ECB (Euro Area)": {
        "url": "https://www.ecb.europa.eu/rss/press.html",
        "parser": "rss2",
        "filter_url": "/sp",  # ECB speeches only
    },
    "Bank of England (UK)": {
        "url": "https://www.bankofengland.co.uk/rss/speeches",
        "parser": "rss2_ns",  # has default namespace
    },
    "Bank of Canada (Canada)": {
        "url": "https://www.bankofcanada.ca/content_type/speeches/feed/",
        "parser": "rss1",  # RSS 1.0 / RDF: items sit outside <channel>
    },
    "RBA (Australia)": {
        "url": "https://www.rba.gov.au/rss/rss-cb-speeches.xml",
        "parser": "rss1",
    },
}


def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible)"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        return parsedate_to_datetime(s).date()
    except Exception:
        pass
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        return None


def parse_rss2(xml, institution, filter_url=None):
    root = ET.fromstring(xml)
    channel = root.find("channel")
    if channel is None:
        return []
    results = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        if filter_url and filter_url not in link:
            # ECB: also accept "Speaker: Title" pattern even without /sp
            if not re.match(r"^[A-Z][a-zA-Zéàü'\s\-]+:\s", title):
                continue
        d = parse_date(pub)
        # Extract speaker from "LastName, Title" (Fed) or "Speaker: Title" (ECB)
        speaker, speech_title = "", title
        if institution.startswith("Federal") and "," in title:
            parts = title.split(",", 1)
            speaker, speech_title = parts[0].strip(), parts[1].strip()
        elif ":" in title and re.match(r"^[A-Z][a-zA-Zéàü'\s\-]+:", title):
            parts = title.split(":", 1)
            speaker, speech_title = parts[0].strip(), parts[1].strip()
        elif institution.startswith("Bank of England"):
            m = re.search(r"(?:speech|remarks?|address)\s+by\s+(.+?)(?:\s*[-–]|$)", title, re.I)
            if m:
                speaker = m.group(1).strip()
                speech_title = re.sub(r"\s*[-–]\s*(?:speech|remarks?|address)\s+by\s+.+$", "", title, flags=re.I).strip()
        results.append({
            "speaker": speaker,
            "title": speech_title,
            "institution": institution,
            "date": str(d) if d else "",
            "description": desc,
            "url": link,
        })
    return results


def localname(tag):
    return tag.rsplit("}", 1)[-1]


def parse_rss1(xml, institution):
    """RSS 1.0 / RDF (BoC, RBA): namespaced <item> elements outside <channel>,
    dates in dc:date rather than pubDate."""
    root = ET.fromstring(xml)
    results = []
    for item in root.iter():
        if localname(item.tag) != "item":
            continue
        fields = {}
        for child in item:
            fields.setdefault(localname(child.tag), (child.text or "").strip())
        title = fields.get("title", "")
        d = parse_date(fields.get("date") or fields.get("pubDate"))
        speaker, speech_title = "", title
        if ":" in title and re.match(r"^[A-Z][a-zA-Zéàü'\s\-]+:", title):
            parts = title.split(":", 1)
            speaker, speech_title = parts[0].strip(), parts[1].strip()
        results.append({
            "speaker": speaker or fields.get("creator", ""),
            "title": speech_title,
            "institution": institution,
            "date": str(d) if d else "",
            "description": fields.get("description", ""),
            "url": fields.get("link", ""),
        })
    return results


def parse_rss2_ns(xml, institution):
    """RSS2 with default namespace (BoE)."""
    xml_clean = re.sub(r'\sxmlns="[^"]+"', "", xml, count=1)
    return parse_rss2(xml_clean, institution)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--date", type=str)
    args = parser.parse_args()

    if args.date:
        target = date.fromisoformat(args.date)
        start = target
    else:
        target = date.today()
        start = target - timedelta(days=args.days - 1)

    all_speeches = []
    errors = []

    for institution, cfg in FEEDS.items():
        try:
            xml = fetch_url(cfg["url"])
            if cfg["parser"] == "rss2_ns":
                items = parse_rss2_ns(xml, institution)
            elif cfg["parser"] == "rss1":
                items = parse_rss1(xml, institution)
            else:
                items = parse_rss2(xml, institution, cfg.get("filter_url"))

            filtered = [
                s for s in items
                if s["date"] and start <= date.fromisoformat(s["date"]) <= target
            ]
            all_speeches.extend(filtered)
            print(f"  OK {institution}: {len(filtered)} in window ({len(items)} in feed)", file=sys.stderr)
        except Exception as e:
            errors.append(f"{institution}: {e}")
            print(f"  FAIL {institution}: {e}", file=sys.stderr)

    if errors:
        print(f"\nFeed errors: {'; '.join(errors)}", file=sys.stderr)

    print(json.dumps(all_speeches, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
