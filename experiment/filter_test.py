"""Does a perplexity-based "quality" filter prefer AI text?

Human text: the real next block of held-out Wikipedia articles.
AI text: the continuation written by GPT-2 fine-tuned on Wikipedia (round 0 of the pilot), top-p 0.9.
Both are continuations of the same 64-token prompts, so topics match.
Scorers: pretrained GPT-2 and Qwen2.5-0.5B (a different model family).
Filter: keep the 50% of all texts with the lowest perplexity, as perplexity-based
quality filters do, and count how much of the kept half is AI text.
"""
import json
import math
import random
import sys

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer
import importlib.util

spec = importlib.util.spec_from_file_location("ce", "collapse_exp.py")
ce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ce)

DEV = "mps"
SEED = 0
tok = AutoTokenizer.from_pretrained("gpt2")

# Rebuild the pilot's split (same seed and rules), keeping document boundaries for the test set.
items = json.load(open("wcc_wiki_items.json"))
docs = [{"url": it["url"], "text": ce.clean_markdown(it.get("markdown") or "")} for it in items]
docs = [d for d in docs if len(d["text"]) > 2000]
random.Random(SEED).shuffle(docs)


def blocks(text):
    ids = tok(text + "\n\n")["input_ids"]
    return [ids[i : i + 64] for i in range(0, len(ids) - 63, 64)]


test_docs, pool0 = [], []
n_test, n_train, per_doc = 300, 500, 10
count = 0
for d in docs:
    b = blocks(d["text"])
    if count < n_test:
        test_docs.append(b[:per_doc]); count += len(b[:per_doc])
    elif len(pool0) < n_train:
        pool0 += b[:per_doc]
    else:
        break
pool0 = pool0[:n_train]
pairs = [(db[i], db[i + 1]) for db in test_docs for i in range(len(db) - 1)]
print("pairs:", len(pairs), flush=True)

model = ce.train(pool0, 3, DEV, 5e-5, 16, SEED)
ai = ce.generate(model, [p for p, _ in pairs], DEV, "sample", 32, 0.9, SEED)
human_txt = [tok.decode(h) for _, h in pairs]
ai_txt = [tok.decode(a) for a in ai]
del model
torch.mps.empty_cache()


@torch.no_grad()
def ppl_scores(name, texts):
    t = AutoTokenizer.from_pretrained(name)
    m = AutoModelForCausalLM.from_pretrained(name, torch_dtype=torch.float32).to(DEV).eval()
    out = []
    for s in texts:
        ids = t(s, return_tensors="pt")["input_ids"].to(DEV)
        if ids.size(1) < 2:
            out.append(float("inf")); continue
        logits = m(input_ids=ids).logits[:, :-1].float()
        nll = F.cross_entropy(logits.reshape(-1, logits.size(-1)), ids[:, 1:].reshape(-1))
        out.append(math.exp(nll.item()))
    del m
    torch.mps.empty_cache()
    return out


report = {"pairs": len(pairs), "scorers": {}}
for name in ["gpt2", "Qwen/Qwen2.5-0.5B"]:
    h = ppl_scores(name, human_txt)
    a = ppl_scores(name, ai_txt)
    pooled = sorted([(v, "human") for v in h] + [(v, "ai") for v in a])
    keep = pooled[: len(pooled) // 2]
    ai_kept = sum(1 for _, k in keep if k == "ai")
    hum_kept = len(keep) - ai_kept
    lower = sum(1 for x, y in zip(a, h) if x < y) / len(h)
    r = {
        "median_ppl_human": round(sorted(h)[len(h) // 2], 2),
        "median_ppl_ai": round(sorted(a)[len(a) // 2], 2),
        "ai_share_of_kept_half": round(ai_kept / len(keep), 3),
        "ai_kept_rate": round(ai_kept / len(a), 3),
        "human_kept_rate": round(hum_kept / len(h), 3),
        "pairs_where_ai_scores_more_fluent": round(lower, 3),
    }
    report["scorers"][name] = r
    print(name, json.dumps(r), flush=True)

report["examples"] = [{"human": human_txt[i], "ai": ai_txt[i]} for i in (0, 100, 200)]
json.dump(report, open("filter_test_results.json", "w"), indent=1)
print("DONE", flush=True)
