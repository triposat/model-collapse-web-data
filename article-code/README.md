# Collapse-safe web data pipeline

These scripts go with the Apify blog article "Model collapse: why AI models degrade and how to prevent it". They collect web pages with provenance, add pre-ChatGPT copies from the Internet Archive, remove near-duplicates, add checked synthetic rows, build a training round with a floor for real data, and compare the diversity of text groups.

## Setup

You need Python 3.11 or later and an Apify API token. `rephrase.py` also needs a model server with an OpenAI-compatible API, such as Ollama or vLLM. Set `LLM_BASE_URL`, and `LLM_API_KEY` for a hosted model.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install "apify-client>=3.2.1,<4" httpx datasketch
export APIFY_TOKEN="your-apify-token"
```

## Run

Run the scripts from this folder, in this order:

```bash
python signals.py
python collect.py
python baseline.py
python dedup.py
python rephrase.py
python build_round.py
python monitor.py rows.jsonl crawl_id
```

- `signals.py` reads AI-use signals (Content-Signal, Content-Usage, and AI-crawler blocks) from a site's robots.txt.
- `collect.py` crawls the allowed URLs with Website Content Crawler. It saves each row to a named Apify dataset and appends it to `rows.jsonl`.
- `baseline.py` adds the last Internet Archive capture from before November 30, 2022, for every live row.
- `dedup.py` removes near-duplicates and writes `deduped.jsonl`. It keeps archive rows first, then the newest live copy.
- `rephrase.py` rephrases passages of the archive rows with a model, rejects any passage with a number that its source doesn't contain, and appends the tagged rows to `synthetic.jsonl`.
- `build_round.py` keeps one version of each page, holds out whole pages for validation, drops rows that overlap them, and caps the synthetic share. It writes `train.jsonl`, `validation_real.jsonl`, and `validation_synthetic.jsonl`.
- `monitor.py` compares groups of rows by distinct words, repeated phrases, and gzip compression ratio.

The scripts write their data to `.jsonl` files in this folder. These files aren't in the repository, because they hold the text of crawled pages. Run the scripts to create them, which takes a few minutes and costs less than $0.01 of Apify usage. The article prints the output of each script.
