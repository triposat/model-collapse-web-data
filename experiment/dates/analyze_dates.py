import json, statistics
from datetime import datetime, timezone
from urllib.parse import urlparse
from page_dates import page_dates
CUT = datetime(2022, 11, 30, tzinfo=timezone.utc)
items = json.load(open("wcc_live_items.json"))
rows = []
for it in items:
    pub, mod = page_dates(it)
    rows.append({"url": it["url"], "host": urlparse(it["url"]).netloc, "pub": pub.isoformat() if pub else None,
                 "mod": mod.isoformat() if mod else None, "words": len((it.get("text") or "").split())})
n = len(rows)
withpub = [r for r in rows if r["pub"]]
withmod = [r for r in rows if r["mod"]]
both = [r for r in rows if r["pub"] and r["mod"]]
pre = [r for r in withpub if datetime.fromisoformat(r["pub"]) < CUT]
pre_both = [r for r in both if datetime.fromisoformat(r["pub"]) < CUT]
pre_mod_after = [r for r in pre_both if datetime.fromisoformat(r["mod"]) >= CUT]
nodate = [r for r in rows if not r["pub"] and not r["mod"]]
mod_after_all = [r for r in withmod if datetime.fromisoformat(r["mod"]) >= CUT]
print(f"pages={n} hosts={len({r['host'] for r in rows})}")
print(f"with publish date={len(withpub)} ({len(withpub)/n:.0%}); with modified={len(withmod)}; both={len(both)}; no date at all={len(nodate)}")
print(f"publish < 2022-11-30: {len(pre)}/{len(withpub)} ({len(pre)/len(withpub):.0%})")
print(f"pre-ChatGPT publish with a modified date: {len(pre_both)}; modified after ChatGPT: {len(pre_mod_after)}")
print(f"modified after ChatGPT among all with modified: {len(mod_after_all)}/{len(withmod)}")
years = sorted(datetime.fromisoformat(r['pub']).year for r in withpub)
print("publish year median", statistics.median(years), "min", years[0], "max", years[-1])
from collections import Counter
print("publish years", sorted(Counter(years).items()))
mods = sorted(datetime.fromisoformat(r['mod']) for r in withmod)
print("modified median", mods[len(mods)//2].date())
json.dump(rows, open("page_dates_rows.json", "w"), indent=1)
