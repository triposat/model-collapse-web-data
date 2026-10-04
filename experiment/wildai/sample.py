# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
import json, random, time, httpx
N = {"human": 58914075}
c = httpx.Client(timeout=60)
info = c.get("https://datasets-server.huggingface.co/info?dataset=pangram/WildAI").json()["dataset_info"]
out = {}
for cfg in ("human", "ai"):
    n = info[cfg]["splits"]["train"]["num_examples"]
    rnd = random.Random(0)
    rows = []
    for off in sorted(rnd.sample(range(n - 100), 12)):
        r = c.get("https://datasets-server.huggingface.co/rows", params={"dataset": "pangram/WildAI", "config": cfg, "split": "train", "offset": off, "length": 100})
        if r.status_code != 200: print(cfg, off, r.status_code, r.text[:200]); time.sleep(3); continue
        rows += [x["row"] for x in r.json()["rows"]]
        time.sleep(1)
    out[cfg] = [{k: x[k] for k in ("text", "url", "date", "dump", "topic", "format", "pangram_label", "token_count")} for x in rows]
    print(cfg, n, len(rows))
json.dump(out, open("sample.json", "w"))
