"""How much of an archive row's text is also in the live row of the same page?

Uses shingles() from dedup.py on ../article-code/rows.jsonl. Needs datasketch, because dedup.py imports it.
Usage: python overlap_13grams.py
"""
import json
import sys

sys.path.insert(0, "../article-code")
from dedup import shingles  # noqa: E402

rows = [json.loads(line) for line in open("../article-code/rows.jsonl")]
archive = {row["url"]: row for row in rows if row["source"] == "archive"}
for row in rows:
    if row["source"] == "live" and row["url"] in archive:
        old, new = shingles(archive[row["url"]]["text"], n=13), shingles(row["text"], n=13)
        print(f"{row['url']}: {len(old & new) / len(old):.0%} of the archive row's 13-word sequences "
              f"are also in the live row")
