"""Rephrase archive rows with a model, check each result against its source, and tag it."""
import hashlib
import json
import os
import random
import re

import httpx

# Any server with an OpenAI-compatible API, such as Ollama, vLLM, or a hosted model
BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
MODEL = "qwen3:4b"
ROUND = 1
PASSAGES_PER_ROW = 5  # a small demo, so remove this limit for a real run
PROMPT = ("Rewrite this passage in the style of a textbook. Keep every fact, and don't add "
          "facts. Reply with the passage only.\n\n{passage}")


def passages(text: str, size: int = 150) -> list[str]:
    """Group the prose lines of a page into passages of about `size` words."""
    out, lines = [], []
    for line in text.splitlines():
        plain = re.sub(r"\[\d+\]", "", line).strip()  # without citation marks such as [5]
        if len(plain.split()) < 20 and not plain.endswith(":"):
            continue  # skip headings, captions, and table cells, but keep the line before a quote
        lines.append(line)
        if len(" ".join(lines).split()) >= size:
            out.append("\n".join(lines))
            lines = []
    return out


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", text.replace(",", "")))


def rephrase(passage: str, seed: int) -> str:
    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {os.environ.get('LLM_API_KEY', 'none')}"},
        json={"model": MODEL, "seed": seed, "temperature": 0.7,
              "messages": [{"role": "user", "content": PROMPT.format(passage=passage)}]},
        timeout=600,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    rows = [json.loads(line) for line in open("deduped.jsonl")]
    kept = []
    for row in rows:
        if row["source"] != "archive":
            continue  # rephrase only text that is proven to predate ChatGPT
        for passage in passages(row["text"])[:PASSAGES_PER_ROW]:
            seed = random.SystemRandom().randrange(2**31)  # a new seed for every request
            text = rephrase(passage, seed)
            new_numbers = numbers(text) - numbers(passage)
            if not text or new_numbers:
                print(f"reject {row['url']}: {sorted(new_numbers) or 'empty reply'}")
                continue
            kept.append({
                "id": hashlib.sha256(text.encode()).hexdigest()[:16],
                "text": text,
                "source": "synthetic",
                "is_synthetic": True,
                "derived_from": row["id"],
                "generator": MODEL,
                "generator_seed": seed,
                "round": ROUND,
            })
    with open("synthetic.jsonl", "a") as f:
        f.writelines(json.dumps(row) + "\n" for row in kept)
    print(f"kept {len(kept)} rephrased passages")
