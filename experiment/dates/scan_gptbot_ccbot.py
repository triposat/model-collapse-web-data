# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Sites that block GPTBot but not CCBot, so their pages can still reach AI training through Common Crawl."""
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.robotparser import RobotFileParser
import httpx
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
hosts = [r[0] for r in json.load(open("signals_scan.json")) if r[1] == 200]
def check(h):
    try:
        t = httpx.get(f"https://{h}/robots.txt", headers={"User-Agent": UA}, timeout=20, follow_redirects=True).text
    except httpx.HTTPError:
        return h, None, None
    rp = RobotFileParser(); rp.parse(t.splitlines())
    return h, not rp.can_fetch("GPTBot", f"https://{h}/"), not rp.can_fetch("CCBot", f"https://{h}/")
with ThreadPoolExecutor(16) as ex:
    res = list(ex.map(check, hosts))
g = [r for r in res if r[1]]
print(f"hosts={len(hosts)} block GPTBot={len(g)} | of these also block CCBot={sum(1 for r in g if r[2])} | GPTBot only={[r[0] for r in g if not r[2]]}")
print(f"block CCBot={sum(1 for r in res if r[2])} | CCBot but not GPTBot={[r[0] for r in res if r[2] and not r[1]]}")
