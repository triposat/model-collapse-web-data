# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "trafilatura"]
# ///
"""For pages with a pre-ChatGPT publish date: last Wayback capture before 2022-11-30, plus the live page."""
import json, time
from datetime import datetime, timezone
import httpx, trafilatura

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
ARCH_UA = "research-dataset-check/1.0"
CUT = datetime(2022, 11, 30, tzinfo=timezone.utc)
rows = json.load(open("page_dates_rows.json"))
pre = [r for r in rows if r["pub"] and datetime.fromisoformat(r["pub"]) < CUT]
c = httpx.Client(headers={"User-Agent": UA}, follow_redirects=True, timeout=60)

def get(url, tries=4, ua=UA):
    for i in range(tries):
        try:
            r = c.get(url, headers={"User-Agent": ua}, timeout=45)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(10 * (i + 1)); continue
            return r
        except httpx.HTTPError:
            time.sleep(5 * (i + 1))
    return None

import os
out = json.load(open("pairs.json")) if os.path.exists("pairs.json") else []
done = {o["url"] for o in out}
for r in pre:
    if r["url"] in done: continue
    rec = dict(r)
    q = httpx.QueryParams({"url": r["url"], "to": "20221129", "filter": ["statuscode:200", "mimetype:text/html"],
                           "output": "json", "fl": "timestamp,original", "limit": "-1"})
    resp = get(f"https://web.archive.org/cdx/search/cdx?{q}", ua=ARCH_UA)
    time.sleep(2.5)
    snap = None
    if resp is not None and resp.status_code == 200 and resp.text.strip():
        data = resp.json()
        if len(data) > 1:
            snap = data[-1]
    rec["snapshot_ts"] = snap[0] if snap else None
    if snap:
        a = get(f"https://web.archive.org/web/{snap[0]}id_/{snap[1]}", ua=ARCH_UA)
        time.sleep(2.5)
        rec["old_text"] = trafilatura.extract(a.text) if a is not None and a.status_code == 200 else None
    live = get(r["url"])
    rec["live_status"] = live.status_code if live is not None else None
    rec["new_text"] = trafilatura.extract(live.text) if live is not None and live.status_code == 200 else None
    print(r["url"], rec["snapshot_ts"], bool(rec.get("old_text")), rec["live_status"], flush=True)
    out.append(rec)
    json.dump(out, open("pairs.json", "w"), indent=1)
print("done", len(out))
