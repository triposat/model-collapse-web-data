"""Minimal Apify REST helper: start an Actor run, wait, download dataset items to a file."""
import json, os, sys, time, requests

def headers():
    # Send the token in a header, not in the URL, so it never lands in logs
    return {"Authorization": f"Bearer {os.environ['APIFY_TOKEN']}"}

API = "https://api.apify.com/v2"

def run(actor, inp, out_path, memory=None, timeout_s=3600):
    params = {}
    if memory: params["memory"] = memory
    r = requests.post(f"{API}/acts/{actor.replace('/','~')}/runs", params=params, headers=headers(), json=inp, timeout=60)
    r.raise_for_status(); d = r.json()["data"]; rid = d["id"]
    print("run", rid, "started", flush=True)
    t0 = time.time()
    while True:
        s = requests.get(f"{API}/actor-runs/{rid}", headers=headers(), timeout=60).json()["data"]
        if s["status"] in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"): break
        if time.time() - t0 > timeout_s: print("timeout waiting"); break
        time.sleep(10)
    ds = s["defaultDatasetId"]
    items = requests.get(f"{API}/datasets/{ds}/items", params={"format": "json", "clean": "true"}, headers=headers(), timeout=300).json()
    json.dump(items, open(out_path, "w"))
    meta = {k: s.get(k) for k in ("id", "status", "startedAt", "finishedAt", "usageTotalUsd", "stats", "options", "defaultDatasetId", "chargedEventCounts", "pricingInfo")}
    json.dump(meta, open(out_path.replace(".json", "_runmeta.json"), "w"), indent=1)
    print("status", s["status"], "items", len(items), "usd", s.get("usageTotalUsd"), "secs", s.get("stats", {}).get("runTimeSecs"), flush=True)
    return items, meta

if __name__ == "__main__":
    actor, inp_file, out = sys.argv[1], sys.argv[2], sys.argv[3]
    run(actor, json.load(open(inp_file)), out)
