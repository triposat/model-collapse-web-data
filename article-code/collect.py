"""Crawl pages with Website Content Crawler and keep provenance with every row."""
import hashlib
import json
import os
from datetime import timedelta
from urllib.parse import urlsplit

from apify_client import ApifyClient

from signals import ai_signals

START_URLS = [
    "https://en.wikipedia.org/wiki/Laika",
    "https://en.wikipedia.org/wiki/Sourdough",
    "https://www.pewresearch.org/data-labs/2026/08/20/how-much-of-the-internet-is-written-with-ai/",
    "https://www.bbcgoodfood.com/recipes/sourdough-bread",
    "https://stackoverflow.com/questions/11227809/why-is-processing-a-sorted-array-faster-than-processing-an-unsorted-array",
]
DATASET = "web-text"

client = ApifyClient(os.environ["APIFY_TOKEN"])


def crawl(urls: list[str]) -> tuple[str, list[dict]]:
    run = client.actor("apify/website-content-crawler").call(
        run_input={
            "startUrls": [{"url": url} for url in urls],
            "crawlerType": "cheerio",
            "maxCrawlDepth": 0,
            "maxCrawlPages": len(urls),
            "respectRobotsTxtFile": True,
        },
        memory_mbytes=2048,
        run_timeout=timedelta(minutes=30),
        logger=None,
    )
    if run is None or run.status != "SUCCEEDED":
        raise RuntimeError(f"Crawl ended as {run and run.status}, nothing saved")
    return run.id, list(client.dataset(run.default_dataset_id).iterate_items(clean=True))


def page_dates(meta: dict) -> tuple[str | None, str | None]:
    """The publish and last-edit dates that the page claims, from JSON-LD or Open Graph."""
    nodes = [n for n in meta.get("jsonLd") or [] if isinstance(n, dict)]
    nodes += [g for n in nodes for g in n.get("@graph", []) if isinstance(g, dict)]
    og = {t.get("property"): t.get("content") for t in meta.get("openGraph") or []}
    published = next((n["datePublished"] for n in nodes if n.get("datePublished")), None)
    modified = next((n["dateModified"] for n in nodes if n.get("dateModified")), None)
    return (published or og.get("article:published_time"),
            modified or og.get("article:modified_time"))


def to_row(item: dict, signals: dict, source: str, crawl_id: str,
           existed_by: str | None = None) -> dict:
    meta = item.get("metadata") or {}
    published, modified = page_dates(meta)
    return {
        "id": hashlib.sha256(item["text"].encode()).hexdigest()[:16],
        "text": item["text"],
        "url": meta.get("canonicalUrl") or item["url"],
        "source": source,
        "crawl_id": crawl_id,
        "crawled_at": item["crawl"]["loadedTime"],
        "published_claimed": published,
        "modified_claimed": modified,
        "existed_by": existed_by,
        "ai_signals": signals,
        "is_synthetic": False,
    }


def save(rows: list[dict], path: str) -> None:
    dataset = client.dataset(client.datasets().get_or_create(name=DATASET).id)
    batch, size = [], 0
    for row in rows:
        row_size = len(json.dumps(row).encode())
        if batch and size + row_size > 4_000_000:  # one request must stay under 5 MB
            dataset.push_items(batch)
            batch, size = [], 0
        batch.append(row)
        size += row_size
    if batch:
        dataset.push_items(batch)
    with open(path, "a") as f:
        f.writelines(json.dumps(row) + "\n" for row in rows)


if __name__ == "__main__":
    signals = {urlsplit(u).hostname: ai_signals(urlsplit(u).hostname) for u in START_URLS}
    allowed = [u for u in START_URLS if signals[urlsplit(u).hostname]["no_train"] is False]
    print(f"{len(allowed)} of {len(START_URLS)} URLs allowed for training")

    crawl_id, items = crawl(allowed)
    rows = [
        to_row(item, signals[urlsplit(item["url"]).hostname]["signals"], "live", crawl_id)
        for item in items
    ]
    save(rows, "rows.jsonl")
    for row in rows:
        print(row["url"], row["published_claimed"], row["modified_claimed"])
