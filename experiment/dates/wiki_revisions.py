# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""For each Wikipedia featured article in the test: compare the last revision before ChatGPT's
release (2022-11-30) with the current revision. Same measure as the archive comparison: the share
of the current version's sentences that do not appear verbatim in the old version."""
import html
import json
import os
import re
import statistics
import sys
import time
from urllib.parse import unquote

import httpx

API = "https://en.wikipedia.org/w/api.php"
UA = "model-collapse-article-research/1.0 (dataset date check; https://blog.apify.com/)"
c = httpx.Client(headers={"User-Agent": UA}, timeout=60)
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")


def api(**params):
    params |= {"format": "json", "formatversion": "2", "maxlag": "5"}
    for i in range(5):
        r = c.get(API, params=params)
        if r.status_code == 200 and "error" not in r.json():
            return r.json()
        time.sleep(5 * (i + 1))
    raise RuntimeError(f"API failed: {params} {r.status_code} {r.text[:200]}")


def paragraphs(rev_id):
    """Body prose of one revision: the text of <p> elements, without reference marks."""
    page = api(action="parse", oldid=rev_id, prop="text", disableeditsection="1", disablelimitreport="1")
    h = page["parse"]["text"]
    h = re.sub(r"<sup[^>]*class=\"[^\"]*reference[^\"]*\"[^>]*>.*?</sup>", "", h, flags=re.S)
    h = re.sub(r"<style.*?</style>", "", h, flags=re.S)
    out = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", h, flags=re.S):
        t = html.unescape(re.sub(r"<[^>]+>", "", p))
        t = re.sub(r"\[\d+\]|\[[a-z]\]|\[citation needed\]", "", t)
        out.append(re.sub(r"\s+", " ", t).strip())
    return out


def sents(paras):
    s = []
    for para in paras:
        s += [x.strip() for x in SPLIT.split(para) if len(x.strip()) > 25]
    return s


if __name__ == "__main__":
    items = json.load(open(sys.argv[1]))  # Website Content Crawler items of the 480 articles
    out_path = sys.argv[2]
    titles = [unquote(it["url"].rsplit("/wiki/", 1)[1]).replace("_", " ") for it in items]
    done = {r["title"]: r for r in json.load(open(out_path))} if os.path.exists(out_path) else {}
    rows = list(done.values())
    def one(title):
        rec = {"title": title}
        try:
            old = api(action="query", prop="revisions", titles=title, rvlimit="1",
                      rvstart="2022-11-30T00:00:00Z", rvdir="older", rvprop="ids|timestamp", redirects="1")
            cur = api(action="query", prop="revisions", titles=title, rvlimit="1",
                      rvprop="ids|timestamp", redirects="1")
            old_rev = old["query"]["pages"][0]["revisions"][0]
            cur_rev = cur["query"]["pages"][0]["revisions"][0]
            rec.update({"old_rev": old_rev["revid"], "old_ts": old_rev["timestamp"],
                        "cur_rev": cur_rev["revid"], "cur_ts": cur_rev["timestamp"]})
            if old_rev["revid"] == cur_rev["revid"]:
                rec.update({"changed_share": 0.0, "same_revision": True})
            else:
                old_s, new_s = set(sents(paragraphs(old_rev["revid"]))), sents(paragraphs(cur_rev["revid"]))
                rec.update({"n_new": len(new_s), "n_old": len(old_s),
                            "changed_share": sum(1 for x in new_s if x not in old_s) / max(1, len(new_s)),
                            "word_growth": len(" ".join(new_s).split()) / max(1, len(" ".join(old_s).split())) - 1})
        except (KeyError, IndexError, RuntimeError) as e:
            rec["error"] = repr(e)[:200]
        return rec

    from concurrent.futures import ThreadPoolExecutor
    todo = [t for t in titles if t not in done]
    with ThreadPoolExecutor(4) as ex:
        for rec in ex.map(one, todo):
            rows.append(rec)
            json.dump(rows, open(out_path, "w"), indent=1)
    ok = [r for r in rows if "changed_share" in r and (r.get("same_revision") or r.get("n_new", 0) >= 20)]
    ch = sorted(r["changed_share"] for r in ok)
    print(f"usable {len(ok)} of {len(rows)}")
    print(f"median changed share {statistics.median(ch):.3f}, mean {statistics.mean(ch):.3f}")
    print(f"unchanged (0%): {sum(1 for v in ch if v == 0)}; >=10%: {sum(1 for v in ch if v >= 0.1)}; "
          f">=20%: {sum(1 for v in ch if v >= 0.2)}; >=50%: {sum(1 for v in ch if v >= 0.5)}")
    q = [ch[int(p * (len(ch) - 1))] for p in (0.1, 0.25, 0.5, 0.75, 0.9)]
    print("p10 p25 p50 p75 p90:", [round(x, 3) for x in q])
