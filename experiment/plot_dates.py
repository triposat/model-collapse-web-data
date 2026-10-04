"""Chart: pages that claim a publish date before ChatGPT, split by their claimed last-edit date."""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
ROWS = [  # label, edited after ChatGPT, last edit before ChatGPT, no last-edit date
    ("Wikipedia featured articles\ncreated before ChatGPT (460)", 454, 0, 6),
    ("Google-ranking pages with a publish\ndate before ChatGPT (53)", 28, 22, 3),
]
PARTS = [("Last edit after ChatGPT's release", "#2a78d6"),
         ("Last edit before ChatGPT's release", "#eda100"),
         ("No last-edit date", "#c9c8c3")]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
fig, ax = plt.subplots(figsize=(9, 3.6), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

for y, (label, *counts) in enumerate(reversed(ROWS)):
    total, left = sum(counts), 0.0
    for count, (name, color) in zip(counts, PARTS):
        share = count / total
        ax.barh(y, share, left=left, color=color, height=0.55,
                label=name if y == 0 else None, edgecolor=SURFACE, linewidth=1.5)
        if share >= 0.08:
            ax.text(left + share / 2, y, f"{count}", ha="center", va="center",
                    color="white" if color != "#c9c8c3" else INK, fontsize=10.5, fontweight="bold")
        left += share

ax.set_yticks(range(len(ROWS)))
ax.set_yticklabels([r[0] for r in reversed(ROWS)], color=INK, fontsize=10)
ax.set_xlim(0, 1)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.tick_params(colors=INK2, length=0)
ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
for side in ("top", "right", "left", "bottom"):
    ax.spines[side].set_visible(False)
ax.legend(loc="upper center", bbox_to_anchor=(0.40, 1.22), ncol=3, frameon=False,
          fontsize=9, labelcolor=INK)
fig.text(0.01, 0.01, "Dates as the pages state them in JSON-LD or Open Graph tags. "
         "Pages crawled with Website Content Crawler.", fontsize=8, color=INK2, ha="left")
fig.tight_layout(rect=(0, 0.04, 1, 0.98))
fig.savefig(sys.argv[1], facecolor=SURFACE)
print("saved", sys.argv[1])
