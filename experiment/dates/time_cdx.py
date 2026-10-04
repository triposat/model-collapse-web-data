"""Time last_capture() from baseline.py on real pages, with its waits and retries.

cdx_timing_urls.json holds 12 Google-ranking pages from page_dates_rows.json that claim a publish date
from 2016 to 2021. cdx_timing_output.txt is the output of our run.
Usage: python time_cdx.py cdx_timing_urls.json
"""
import json
import os
import sys
import time

os.environ.setdefault("APIFY_TOKEN", "unused")  # baseline.py imports collect.py, which reads it
sys.path.insert(0, "../../article-code")
from baseline import last_capture  # noqa: E402

urls = json.load(open(sys.argv[1]))
times, found = [], 0
for url in urls:
    start = time.time()
    timestamp = last_capture(url)
    times.append(time.time() - start)
    found += timestamp is not None
    print(f"{times[-1]:5.1f}s {timestamp} {url[:80]}", flush=True)
mean = sum(times) / len(times)
print(f"{len(urls)} URLs, {found} with a capture, mean {mean:.1f}s per URL, {3600 / mean:.0f} URLs per hour")
