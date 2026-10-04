"""Draft code snippet for the article: collect pages with Website Content Crawler
and keep provenance fields next to the text, so every training row can be traced."""
import json
import os

from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_TOKEN"])

run = client.actor("apify/website-content-crawler").call(
    run_input={
        "startUrls": [
            # a pre-ChatGPT snapshot from the Internet Archive ("id_" returns the original HTML)
            {"url": "https://web.archive.org/web/20210615000000id_/https://en.wikipedia.org/wiki/Laika"},
            {"url": "https://blog.apify.com/improve-ai-models-web-scraping-data-augmentation/"},
        ],
        "crawlerType": "cheerio",
        "maxCrawlDepth": 0,
        "ignoreCanonicalUrl": True,  # keep archive snapshots and live pages as separate rows
        "respectRobotsTxtFile": True,
    }
)


def published_at(meta):
    """Publish date from Open Graph or JSON-LD, if the page has one."""
    for tag in meta.get("openGraph") or []:
        if tag.get("property") == "article:published_time":
            return tag.get("content")
    for block in meta.get("jsonLd") or []:
        if isinstance(block, dict) and block.get("datePublished"):
            return block["datePublished"]
    return None


with open("training_rows.jsonl", "w") as f:
    for item in client.dataset(run.default_dataset_id).iterate_items():
        meta = item["metadata"]
        row = {
            "text": item["text"],
            "url": item["url"],
            "crawled_at": item["crawl"]["loadedTime"],
            "published_at": published_at(meta),
            "archived_at": (meta.get("headers") or {}).get("memento-datetime"),
            "language": meta.get("languageCode"),
            "is_synthetic": False,
        }
        f.write(json.dumps(row) + "\n")
        print({k: v for k, v in row.items() if k != "text"})
