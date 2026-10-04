"""Print every number the article states about the GPT-2 test, from the per-seed result files."""
import json
import re
import statistics
import sys

files = sys.argv[1:]
runs = [json.load(open(f)) for f in files]
pre, rare_n = [], []
for f in files:
    log = open(f.replace("results.json", "log.txt").replace("pilot_results.json", "pilot_log.txt")).read()
    pre.append(float(re.findall(r'"pretrained_gpt2_no_finetune", "test_ppl": ([\d.]+)', log)[-1]))
    # words that appear at most twice in the round-0 training data
    rare_n.append(int(re.findall(r"rare types \(freq<=2\)=(\d+)", log)[-1]))


def get(res, regime, gen, key):
    r = next(r for r in res if r["gen"] == 0) if gen == 0 else \
        next(r for r in res if r["regime"] == regime and r["gen"] == gen)
    return r[key]


def stat(vals):
    return statistics.mean(vals), min(vals), max(vals)


out = {"seeds": len(runs), "pretrained": stat(pre), "rare_types": stat(rare_n),
       "train_and_generate_hours_per_seed": stat([sum(r["secs"] for r in res) / 3600 for res in runs])}
for key in ("test_ppl", "rep4_share", "gen_vocab", "gen_ppl_under_gen0"):
    out[f"r0_{key}"] = stat([get(r, None, 0, key) for r in runs])
for reg in ("replace", "orig10", "fresh10", "fresh50"):
    d = {}
    for key in ("test_ppl", "rep4_share", "gen_vocab", "gen_ppl_under_gen0"):
        d[f"r4_{key}"] = stat([get(r, reg, 4, key) for r in runs])
        d[f"chg_{key}"] = stat([get(r, reg, 4, key) / get(r, reg, 0, key) - 1 for r in runs])
    d["ppl_by_round"] = [statistics.mean(get(r, reg, g, "test_ppl") for r in runs) for g in range(5)]
    # Rare words in the output: the share of the rare round-0 words that the output uses
    rare0 = [get(r, reg, 0, "rare_words_kept") * n for r, n in zip(runs, rare_n)]
    rare4 = [get(r, reg, 4, "rare_words_kept") * n for r, n in zip(runs, rare_n)]
    other0 = [get(r, reg, 0, "gen_vocab") - x for r, x in zip(runs, rare0)]
    other4 = [get(r, reg, 4, "gen_vocab") - x for r, x in zip(runs, rare4)]
    d["rare_words_in_output_r0"], d["rare_words_in_output_r4"] = stat(rare0), stat(rare4)
    d["chg_rare_words"] = stat([b / a - 1 for a, b in zip(rare0, rare4)])
    d["chg_other_words"] = stat([b / a - 1 for a, b in zip(other0, other4)])
    d["rare_fell_faster_every_seed"] = all(b / a < d2 / c for a, b, c, d2 in zip(rare0, rare4, other0, other4))
    # The warning signs in Step 6: human-text perplexity rises and output perplexity falls, every round
    trend = lambda key, r: [get(r, reg, g, key) for g in range(5)]
    d["test_ppl_rises_every_round_every_seed"] = all(
        all(b > a for a, b in zip(t, t[1:])) for t in (trend("test_ppl", r) for r in runs))
    d["output_ppl_falls_every_round_every_seed"] = all(
        all(b < a for a, b in zip(t, t[1:])) for t in (trend("gen_ppl_under_gen0", r) for r in runs))
    out[reg] = d
print(json.dumps(out, indent=1))
