"""Combine the result files of several seeds: mean and range per data mix and round, plus a chart."""
import json
import re
import statistics
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

files, out_png = sys.argv[1:-1], sys.argv[-1]
runs = [json.load(open(f)) for f in files]
pretrained = []
for f in files:
    log = open(f.replace("results.json", "log.txt").replace("pilot_results.json", "pilot_log.txt")).read()
    # a log can hold lines from an earlier, stopped run of the same seed, so take the last value
    pretrained.append(float(re.findall(r'"pretrained_gpt2_no_finetune", "test_ppl": ([\d.]+)', log)[-1]))

MIXES = [("replace", "100% model output", "#2a78d6"),
         ("orig10", "90% output + 10% original real data", "#eb6834"),
         ("fresh10", "90% output + 10% new real data", "#1baf7a"),
         ("fresh50", "50% output + 50% new real data", "#eda100")]
KEYS = ["test_ppl", "gen_vocab", "rep4_share", "distinct2", "rare_words_kept", "gen_ppl_under_gen0"]


def row(res, regime, gen):
    if gen == 0:
        return next(r for r in res if r["gen"] == 0)
    return next(r for r in res if r["regime"] == regime and r["gen"] == gen)


summary = {"seeds": len(runs), "pretrained_test_ppl": pretrained}
for regime, _, _ in MIXES:
    summary[regime] = {}
    for gen in range(5):
        vals = {k: [row(res, regime, gen)[k] for res in runs] for k in KEYS}
        summary[regime][gen] = {k: (round(statistics.mean(v), 3), round(min(v), 3), round(max(v), 3))
                                for k, v in vals.items()}
    # relative change from round 0 to round 4, per seed, then mean and range
    for k in ("test_ppl", "gen_vocab", "rep4_share"):
        ch = [row(res, regime, 4)[k] / row(res, regime, 0)[k] - 1 for res in runs]
        summary[regime][f"{k}_change"] = (round(statistics.mean(ch), 3), round(min(ch), 3), round(max(ch), 3))
print(json.dumps(summary, indent=1))

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
ends = []
for regime, label, color in MIXES:
    xs = list(range(5))
    mean = [summary[regime][g]["test_ppl"][0] for g in xs]
    lo = [summary[regime][g]["test_ppl"][1] for g in xs]
    hi = [summary[regime][g]["test_ppl"][2] for g in xs]
    ax.fill_between(xs, lo, hi, color=color, alpha=0.15, linewidth=0)
    ax.plot(xs, mean, color=color, linewidth=2, marker="o", markersize=6,
            markeredgecolor=SURFACE, markeredgewidth=1.5, label=label, zorder=3)
    ends.append(mean[-1])
# end labels, nudged apart so that close values don't overlap
ymin, ymax = ax.get_ylim()
gap, placed = (ymax - ymin) * 0.045, []
for y in sorted(ends):
    ly = y if not placed or y - placed[-1] >= gap else placed[-1] + gap
    placed.append(ly)
    ax.annotate(f"{y:.1f}", xy=(4, y), xytext=(4.12, ly), color=INK, fontsize=10, va="center")
pre = statistics.mean(pretrained)
ax.axhline(pre, color=INK2, linewidth=1, linestyle="--")
ax.annotate(f"GPT-2 before fine-tuning: {pre:.1f}", xy=(0.05, pre), xytext=(0.05, pre + 0.6),
            color=INK2, fontsize=9)
ax.set_xticks(range(5))
ax.set_xticklabels(["0\n(real data)", "1", "2", "3", "4"])
ax.set_xlabel("Training round", color=INK2)
ax.set_ylabel("Perplexity on held-out Wikipedia text (lower is better)", color=INK2)
ax.tick_params(colors=INK2, length=0)
ax.grid(axis="y", color=GRID, linewidth=0.8)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.set_xlim(-0.2, 4.6)
ax.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK)
fig.text(0.075, 0.01, f"Mean of {len(runs)} seeds, shaded band = range across seeds. GPT-2 small, fine-tuned each "
         "round on 32k tokens. Data: 478 Wikipedia featured articles.", fontsize=8, color=INK2, ha="left")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(out_png, facecolor=SURFACE)
