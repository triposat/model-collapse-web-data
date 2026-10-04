# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Sites in the ranking-page sample that block CCBot (Common Crawl) but allow a generic crawler name."""
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.robotparser import RobotFileParser

import httpx

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
hosts = [r[0] for r in json.load(open("signals_scan.json")) if r[1] == 200]


def check(host):
    try:
        text = httpx.get(f"https://{host}/robots.txt", headers={"User-Agent": UA}, timeout=20, follow_redirects=True).text
    except httpx.HTTPError:
        return host, None, None
    rp = RobotFileParser()
    rp.parse(text.splitlines())
    return host, not rp.can_fetch("CCBot", f"https://{host}/"), rp.can_fetch("my-training-crawler", f"https://{host}/")


with ThreadPoolExecutor(16) as ex:
    res = list(ex.map(check, hosts))
cc = [r for r in res if r[1]]
print(f"hosts={len(hosts)} block CCBot={len(cc)} of which generic name allowed={sum(1 for r in cc if r[2])} errors={sum(1 for r in res if r[1] is None)}")
print("generic allowed:", [r[0] for r in cc if r[2]])
print("generic blocked too:", [r[0] for r in cc if not r[2]])
