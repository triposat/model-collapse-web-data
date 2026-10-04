# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
import json, re
from concurrent.futures import ThreadPoolExecutor
import httpx
rows = json.load(open("page_dates_rows.json"))
hosts = sorted({r["host"] for r in rows})
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
def get(h):
    try:
        r = httpx.get(f"https://{h}/robots.txt", headers={"User-Agent": UA}, timeout=20, follow_redirects=True)
        if r.status_code != 200: return h, r.status_code, []
        lines = [l.strip() for l in r.text.splitlines() if re.match(r"\s*(content-signal|content-usage|license)\s*:", l, re.I)]
        ai_bots = len(re.findall(r"(?im)^\s*user-agent:\s*(GPTBot|ClaudeBot|CCBot|Google-Extended|anthropic-ai|PerplexityBot|Bytespider|Applebot-Extended|meta-externalagent)\s*$", r.text))
        return h, r.status_code, lines, ai_bots
    except Exception as e:
        return h, str(type(e).__name__), [], 0
with ThreadPoolExecutor(16) as ex:
    res = list(ex.map(get, hosts))
json.dump(res, open("signals_scan.json", "w"), indent=1)
ok = [r for r in res if r[1] == 200]
cs = [r for r in ok if any(l.lower().startswith("content-signal") for l in r[2])]
cu = [r for r in ok if any(l.lower().startswith("content-usage") for l in r[2])]
lic = [r for r in ok if any(l.lower().startswith("license") for l in r[2])]
trainno = [r for r in cs if any(re.search(r"ai-train\s*=\s*no", l, re.I) for l in r[2])]
trainyes = [r for r in cs if any(re.search(r"ai-train\s*=\s*yes", l, re.I) for l in r[2])]
named = [r for r in ok if len(r) > 3 and r[3] > 0]
print(f"hosts={len(hosts)} robots_ok={len(ok)} content-signal={len(cs)} (ai-train=no {len(trainno)}, yes {len(trainyes)}) content-usage={len(cu)} license={len(lic)} name_ai_crawler={len(named)}")
for r in cs + cu + lic: print(r[0], r[2][:3])
