"""A page that moved has no archive captures under its new URL.

Checks the old and the current URL of a GeeksforGeeks tutorial with last_capture() from baseline.py,
and shows that the old URL redirects to the current one. moved_page_output.txt is our run.
Usage: python moved_page.py
"""
import os
import sys

import httpx

os.environ.setdefault("APIFY_TOKEN", "unused")  # baseline.py imports collect.py, which reads it
sys.path.insert(0, "../../article-code")
from baseline import last_capture  # noqa: E402
from signals import USER_AGENT  # noqa: E402

OLD = "https://www.geeksforgeeks.org/closure-in-javascript/"
NEW = "https://www.geeksforgeeks.org/javascript/closure-in-javascript/"
resp = httpx.head(OLD, headers={"User-Agent": USER_AGENT}, follow_redirects=False, timeout=30)
print(f"old URL: HTTP {resp.status_code} -> {resp.headers.get('location')}")
print(f"old URL, last capture before the cutoff: {last_capture(OLD)}")
print(f"current URL, last capture before the cutoff: {last_capture(NEW)}")
