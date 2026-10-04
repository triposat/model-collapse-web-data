"""How big must a monitor.py difference be to mean something? Uses monitor.py's own functions.

- Noise: two random groups of 300 human-labeled pages, 1k draws.
- Page type: human-labeled tutorials vs human-labeled nonfiction pages, 56 pages per group.
- AI text: AI-labeled vs human-labeled pages at the same group size.
Run sample.py first. Usage: python noise_floor.py
"""
import json
import random
import statistics
import sys

sys.path.insert(0, "../../article-code")
from monitor import LENGTH, diversity, words  # noqa: E402

KEYS = ("vocabulary", "repeated_phrase_share", "compression_ratio")
d = json.load(open("sample.json"))


def prep(rows):
    return [(words(r["text"])[:LENGTH], r.get("format")) for r in rows if len(words(r["text"])) >= LENGTH]


def change(g1, g2):
    """Percent change of each metric from group 1 to group 2."""
    a, b = diversity([w for w, _ in g1]), diversity([w for w, _ in g2])
    return {k: (b[k] - a[k]) / a[k] * 100 for k in KEYS}


human, ai = prep(d["human"]), prep(d["ai"])

rnd = random.Random(7)
noise = []
for _ in range(1000):
    s = rnd.sample(human, 600)
    noise.append(change(s[:300], s[300:]))
print("noise, 300 vs 300 human pages, 95th percentile of the absolute change:",
      {k: round(sorted(abs(g[k]) for g in noise)[949], 1) for k in KEYS})

rnd = random.Random(3)
tutorial = [x for x in human if x[1] == "Tutorial"]
nonfiction = [x for x in human if x[1] == "Nonfiction Writing"]
n = len(tutorial)
pages = [change(rnd.sample(nonfiction, n), rnd.sample(tutorial, n)) for _ in range(300)]
labels = [change(rnd.sample(human, n), rnd.sample(ai, n)) for _ in range(300)]
print(f"group size {n} (all human-labeled tutorials)")
print("human nonfiction -> human tutorials, median change:",
      {k: round(statistics.median(g[k] for g in pages), 1) for k in KEYS})
print("human -> AI-labeled, median change:",
      {k: round(statistics.median(g[k] for g in labels), 1) for k in KEYS})
