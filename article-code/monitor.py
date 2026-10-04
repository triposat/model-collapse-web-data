"""Compare the diversity of text groups, for example a new crawl and the human baseline."""
import gzip
import json
import random
import re
import sys
from collections import defaultdict

LENGTH = 300  # compare every text at the same length, because the metrics depend on it


def words(text: str) -> list[str]:
    return re.findall(r"[a-z][a-z'\-]*", text.lower())


def diversity(texts: list[list[str]]) -> dict:
    vocab = {w for ws in texts for w in ws}
    repeats = sum(len(set(zip(ws, ws[1:], ws[2:], ws[3:]))) < len(ws) - 3 for ws in texts)
    raw = "\n".join(" ".join(ws) for ws in texts).encode()
    return {
        "texts": len(texts),
        "vocabulary": len(vocab),
        "repeated_phrase_share": round(repeats / len(texts), 3),
        "compression_ratio": round(len(raw) / len(gzip.compress(raw)), 3),
    }


if __name__ == "__main__":
    path, field = sys.argv[1:3]  # for example: rows.jsonl crawl_id
    groups = defaultdict(list)
    for line in open(path):
        row = json.loads(line)
        ws = words(row["text"])
        if len(ws) >= LENGTH:
            groups[str(row.get(field))].append(ws[:LENGTH])

    size = min(len(texts) for texts in groups.values())
    if size < 100:
        print(f"Only {size} texts in the smallest group, so the differences are mostly noise")
    groups = {name: random.Random(0).sample(texts, size) for name, texts in groups.items()}
    for name, texts in groups.items():
        print(name, diversity(texts))
