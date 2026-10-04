import json, re, statistics
from datetime import datetime, timezone
CUT = datetime(2022, 11, 30, tzinfo=timezone.utc)
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")
def sents(t):
    out = []
    for line in (t or "").split("\n"):
        out += [re.sub(r"\s+", " ", x).strip() for x in SPLIT.split(line) if len(x.strip()) > 25]
    return out
d = json.load(open("pairs.json"))
rows = []
for r in d:
    if not (r.get("old_text") and r.get("new_text")):
        continue
    old, new = set(sents(r["old_text"])), sents(r["new_text"])
    if len(old) < 5 or len(new) < 5:
        continue
    ch = sum(1 for x in new if x not in old) / len(new)
    mod = datetime.fromisoformat(r["mod"]) if r.get("mod") else None
    rows.append({"url": r["url"], "snap": r["snapshot_ts"], "changed": ch, "n_new": len(new), "n_old": len(old),
                 "mod_after": (mod >= CUT) if mod else None})
print("pages with pre-ChatGPT publish date:", len(d), "| with archive copy:", sum(1 for x in d if x.get("snapshot_ts")),
      "| usable pairs (>=5 sentences both):", len(rows))
ch = sorted(x["changed"] for x in rows)
print("median changed:", round(statistics.median(ch), 3), "| unchanged:", sum(1 for v in ch if v == 0),
      "| >=20%:", sum(1 for v in ch if v >= 0.2), "| >=50%:", sum(1 for v in ch if v >= 0.5))
for k in (True, False, None):
    g = sorted(x["changed"] for x in rows if x["mod_after"] is k)
    if g: print(f"mod_after={k}: n={len(g)} median={statistics.median(g):.3f} unchanged={sum(1 for v in g if v==0)} >=20%={sum(1 for v in g if v>=0.2)}")
json.dump(rows, open("pairs_analysis.json", "w"), indent=1)
