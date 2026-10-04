"""Add the last Internet Archive copy from before ChatGPT for every live page."""
import json
import time
from email.utils import parsedate_to_datetime

import httpx

from collect import crawl, save, to_row
from signals import USER_AGENT

CUTOFF = "20221129"  # the last day before ChatGPT's release on November 30, 2022


def last_capture(url: str) -> str | None:
    params = {"url": url, "to": CUTOFF, "output": "json", "fl": "timestamp",
              "filter": ["statuscode:200", "mimetype:text/html"], "limit": "-1"}
    for attempt in range(5):
        try:
            resp = httpx.get("https://web.archive.org/cdx/search/cdx", params=params,
                             headers={"User-Agent": USER_AGENT}, timeout=120)
            if resp.status_code not in (429, 502, 503, 504):
                break
        except httpx.TimeoutException:
            pass
        time.sleep(10 * 2**attempt)  # the CDX server is often busy, so wait longer each time
    else:
        raise RuntimeError(f"CDX lookup failed for {url}")
    resp.raise_for_status()
    time.sleep(2.5)  # one query at a time, to stay under the CDX rate limit
    captures = resp.json() if resp.text.strip() else []
    return captures[1][0] if len(captures) > 1 else None  # row 0 is the header


if __name__ == "__main__":
    rows = [json.loads(line) for line in open("rows.jsonl")]
    archived = {row["url"] for row in rows if row["source"] == "archive"}

    snapshots = {}
    for row in rows:
        if row["source"] != "live" or row["url"] in archived:
            continue
        timestamp = last_capture(row["url"])
        if timestamp:
            # id_ returns the original HTML, without the archive's toolbar and links
            snapshots[f"https://web.archive.org/web/{timestamp}id_/{row['url']}"] = row
    if not snapshots:
        print("No new pages with a capture from before ChatGPT")
        raise SystemExit(0)

    crawl_id, items = crawl(list(snapshots))
    new_rows = []
    for item in items:
        live_row = snapshots[item["url"]]
        captured = parsedate_to_datetime(item["metadata"]["headers"]["memento-datetime"])
        if captured.strftime("%Y%m%d") > CUTOFF:
            continue  # the archive served a newer capture than the one requested
        row = to_row(item, live_row["ai_signals"], "archive", crawl_id,
                     existed_by=captured.isoformat())
        row["url"] = live_row["url"]
        new_rows.append(row)

    save(new_rows, "rows.jsonl")
    for row in new_rows:
        print(row["url"], "existed by", row["existed_by"])
