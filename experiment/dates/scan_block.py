# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
import json, re
from concurrent.futures import ThreadPoolExecutor
import httpx
from urllib.robotparser import RobotFileParser
res = json.load(open("signals_scan.json"))
ok = [r[0] for r in res if r[1] == 200]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
BOTS = ["GPTBot", "ClaudeBot", "CCBot", "Google-Extended", "Applebot-Extended", "meta-externalagent", "Bytespider"]
def check(h):
    t = httpx.get(f"https://{h}/robots.txt", headers={"User-Agent": UA}, timeout=20, follow_redirects=True).text
    rp = RobotFileParser(); rp.parse(t.splitlines())
    blocked = [b for b in BOTS if not rp.can_fetch(b, f"https://{h}/")]
    generic_ok = rp.can_fetch("my-training-crawler", f"https://{h}/")
    return h, blocked, generic_ok
with ThreadPoolExecutor(16) as ex:
    out = list(ex.map(check, ok))
any_block = [o for o in out if o[1]]
both = [o for o in any_block if o[2]]
print(f"robots ok={len(ok)} block >=1 AI training crawler at / = {len(any_block)}; of these, a generic crawler name is still allowed at / = {len(both)}")
from collections import Counter
print(Counter(b for o in out for b in o[1]))
no_sig = {r[0] for r in res if r[1] == 200 and any(re.search(r"ai-train\s*=\s*no", l, re.I) for l in r[2])}
blockers = {o[0] for o in any_block}
union = no_sig | blockers
generic_allowed = {o[0] for o in out if o[2]}
print("no-train via signal:", len(no_sig), "via AI-bot block:", len(blockers), "union:", len(union), "union still allowed for generic UA:", len(union & generic_allowed))
