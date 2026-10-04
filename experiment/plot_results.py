"""Render the pilot results as a static PNG for the brief and the article."""
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

res = json.load(open(sys.argv[1]))
out = sys.argv[2]
metric = sys.argv[3] if len(sys.argv) > 3 else "test_ppl"

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = [  # fixed categorical order from the reference palette
    ("replace", "100% model output", "#2a78d6"),
    ("orig10", "90% output + 10% original real data", "#eb6834"),
    ("fresh10", "90% output + 10% fresh real data", "#1baf7a"),
    ("fresh50", "50% output + 50% fresh real data", "#eda100"),
]
LABELS = {
    "test_ppl": ("Perplexity on held-out human text (lower is better)", "{:.1f}"),
    "rare_words_kept": ("Share of rare words the model still writes", "{:.0%}"),
    "distinct2": ("Distinct word pairs in generated text", "{:.2f}"),
}
ylabel, fmt = LABELS[metric]

gen0 = next(r for r in res if r["gen"] == 0)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

ends = []
for key, label, color in SERIES:
    rows = sorted([gen0] + [r for r in res if r["regime"] == key], key=lambda r: r["gen"])
    if len(rows) < 2:
        continue
    xs = [r["gen"] for r in rows]
    ys = [r[metric] for r in rows]
    ax.plot(xs, ys, color=color, linewidth=2, marker="o", markersize=6,
            markeredgecolor=SURFACE, markeredgewidth=1.5, label=label, zorder=3)
    ends.append((ys[-1], xs[-1], label, color))

# direct labels at line ends, nudged apart so they don't collide
ends.sort()
ymin, ymax = ax.get_ylim()
min_gap = (ymax - ymin) * 0.06
placed = []
for y, x, label, color in ends:
    ly = y if not placed or y - placed[-1] >= min_gap else placed[-1] + min_gap
    placed.append(ly)
    ax.annotate(fmt.format(y), xy=(x, y), xytext=(x + 0.12, ly), color=INK, fontsize=10,
                va="center", ha="left")

ax.set_xticks(range(0, max(r["gen"] for r in res) + 1))
ax.set_xticklabels(["0\n(real data)"] + [str(i) for i in range(1, max(r["gen"] for r in res) + 1)])
ax.set_xlabel("Training round", color=INK2)
ax.set_ylabel(ylabel, color=INK2)
ax.tick_params(colors=INK2, length=0)
ax.grid(axis="y", color=GRID, linewidth=0.8)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.set_xlim(-0.2, max(r["gen"] for r in res) + 0.6)
leg = ax.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK)
title = sys.argv[4] if len(sys.argv) > 4 else ""
if title:
    fig.suptitle(title, x=0.075, ha="left", fontsize=13, color=INK, fontweight="bold")
fig.text(0.075, 0.01, "GPT-2 small, fine-tuned each round on 32k tokens. Data: 480 Wikipedia featured articles "
         "scraped with Website Content Crawler. Sampling: top-p 0.9.", fontsize=8, color=INK2, ha="left")
fig.tight_layout(rect=(0, 0.03, 1, 0.95))
fig.savefig(out, facecolor=SURFACE)
print("saved", out)
