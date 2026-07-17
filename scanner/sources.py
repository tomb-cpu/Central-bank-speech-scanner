"""Registry of central bank speech feeds.

BIS aggregates speeches from ~60 member central banks in one feed, so it's
the primary source. The direct bank feeds are included on top because BIS
can lag a few days behind a bank's own site, and because BIS's feed is
capped at ~25 items so a busy stretch can push older speeches out before
the scanner's next run.
"""

SOURCES = [
    {
        "id": "bis",
        "name": "BIS (aggregates ~60 central banks)",
        "url": "https://www.bis.org/doclist/cbspeeches.rss?paging_length=100",
        "kind": "rss",
    },
    {
        "id": "fed",
        "name": "Federal Reserve",
        "url": "https://www.federalreserve.gov/feeds/speeches.xml",
        "kind": "rss",
    },
    {
        "id": "ecb",
        "name": "European Central Bank",
        "url": "https://www.ecb.europa.eu/rss/press.html",
        "kind": "rss",
        # ECB doesn't publish a speeches-only feed; this feed mixes press
        # releases, speeches, and interviews, so filter on title/type.
        "filter_keywords": ["speech", "interview", "remarks", "lecture"],
    },
    {
        "id": "boe",
        "name": "Bank of England",
        "url": "https://www.bankofengland.co.uk/rss/speeches",
        "kind": "rss",
    },
    {
        "id": "boj",
        "name": "Bank of Japan",
        "url": "https://www.boj.or.jp/en/rss/whatsnew.xml",
        "kind": "rss",
        "filter_keywords": ["speech", "speeches", "remarks"],
    },
    {
        "id": "rba",
        "name": "Reserve Bank of Australia",
        "url": "https://www.rba.gov.au/rss/rss-cb-speeches.xml",
        "kind": "rss",
    },
    {
        "id": "boc",
        "name": "Bank of Canada",
        "url": "https://www.bankofcanada.ca/content_type/speeches/feed/",
        "kind": "rss",
    },
]
