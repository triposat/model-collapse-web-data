"""Remove near-duplicate rows, and keep the copy with date proof or the newest copy."""
import hashlib
import json
import re

from datasketch import MinHash, MinHashLSH

NUM_PERM = 128
LSH_THRESHOLD = 0.5  # loose, to find candidates
DUP_THRESHOLD = 0.7  # strict, checked with the exact Jaccard similarity


def shingles(text: str, n: int = 5) -> set[bytes]:
    words = re.findall(r"\w+", text.lower())
    grams = (" ".join(words[i : i + n]) for i in range(max(1, len(words) - n + 1)))
    return {hashlib.blake2b(g.encode(), digest_size=8).digest() for g in grams}


if __name__ == "__main__":
    rows = [json.loads(line) for line in open("rows.jsonl")]
    # Archive rows first, because they have date proof. Then the newest live rows,
    # so that a new crawl of an edited page replaces the older copy.
    rows.sort(key=lambda row: row["crawled_at"], reverse=True)
    rows.sort(key=lambda row: row["source"] != "archive")

    lsh = MinHashLSH(threshold=LSH_THRESHOLD, num_perm=NUM_PERM)
    kept = {}
    for i, row in enumerate(rows):
        sh = shingles(row["text"])
        mh = MinHash(num_perm=NUM_PERM, seed=1)
        mh.update_batch(sh)
        best = max((len(sh & kept[k][1]) / len(sh | kept[k][1]) for k in lsh.query(mh)),
                   default=0.0)
        if best >= DUP_THRESHOLD:
            print(f"drop {row['source']} {row['url']} (similarity {best:.2f})")
            continue
        lsh.insert(str(i), mh)
        kept[str(i)] = (row, sh)
        print(f"keep {row['source']} {row['url']} (closest kept row {best:.2f})")

    with open("deduped.jsonl", "w") as f:
        f.writelines(json.dumps(row) + "\n" for row, _ in kept.values())
