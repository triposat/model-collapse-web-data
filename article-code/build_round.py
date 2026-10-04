"""Build one training round: every real row, a capped share of synthetic rows,
and validation sets that no round trains on."""
import json
import random

from dedup import shingles

MIN_REAL_SHARE = 0.5  # real words as a share of all training words in the round
VALIDATION_SHARE = 0.1  # share of pages, and of synthetic rows, that no round trains on


def words(row: dict) -> int:
    return len(row["text"].split())


def write(path: str, rows: list[dict]) -> None:
    with open(path, "w") as f:
        f.writelines(json.dumps(row) + "\n" for row in rows)


if __name__ == "__main__":
    rows = [json.loads(line) for line in open("deduped.jsonl")]
    synthetic = [json.loads(line) for line in open("synthetic.jsonl")]
    rng = random.Random(0)

    # One version per page: the archive copy if there is one, otherwise the newest copy
    pages = {}
    for row in sorted(rows, key=lambda row: (row["source"] == "archive", row["crawled_at"])):
        pages[row["url"]] = row

    # Hold out whole pages with an archive copy, so that no version of them trains
    urls = sorted(pages)
    rng.shuffle(urls)
    proven = [url for url in urls if pages[url]["source"] == "archive"]
    held = set(proven[: max(1, round(len(urls) * VALIDATION_SHARE))])
    validation = [pages[url] for url in held]
    held_grams = set().union(*(shingles(row["text"], n=13) for row in validation))

    def leaks(row: dict) -> bool:
        """True if the row shares a 13-word sequence with the validation pages."""
        return bool(shingles(row["text"], n=13) & held_grams)

    # Drop real rows that overlap validation, such as a copy of a held-out page on another URL
    real = [pages[url] for url in urls if url not in held]
    clean = [row for row in real if not leaks(row)]

    # Drop synthetic rows that come from a held-out page, then hold out some for validation
    page_of = {row["id"]: row["url"] for row in rows}
    usable = [row for row in synthetic
              if page_of.get(row["derived_from"]) not in held and not leaks(row)]
    rng.shuffle(usable)
    n_held = min(len(usable), max(1, round(len(usable) * VALIDATION_SHARE)))
    synthetic_validation, usable = usable[:n_held], usable[n_held:]

    # Keep every real row, and add synthetic rows only while the real share stays above the floor
    real_words = sum(words(row) for row in clean)
    budget = real_words * (1 - MIN_REAL_SHARE) / MIN_REAL_SHARE
    added, used = [], 0
    for row in usable:
        if used + words(row) <= budget:
            added.append(row)
            used += words(row)

    train = clean + added
    rng.shuffle(train)
    write("train.jsonl", train)
    write("validation_real.jsonl", validation)
    write("validation_synthetic.jsonl", synthetic_validation)
    print(f"training: {len(clean)} real rows ({real_words:,} words) and {len(added)} synthetic "
          f"rows ({used:,} words), real share {real_words / max(1, real_words + used):.0%}")
    print(f"validation: {len(validation)} real and {len(synthetic_validation)} synthetic rows")
    print(f"dropped: {len(real) - len(clean)} real and {len(synthetic) - len(usable) - n_held} "
          f"synthetic rows that repeat validation text, {len(usable) - len(added)} over the cap")
