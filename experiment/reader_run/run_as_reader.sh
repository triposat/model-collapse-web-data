#!/bin/bash
# Follow the article only: fresh venv, its pip line, its scripts in order. Log time and output.
# shellcheck disable=SC1091,SC2086  # activate is created at run time, and $cmd splits into script + args on purpose
cd "$(dirname "$0")" || exit 1
step() { echo "=== $1  ($(date +%H:%M:%S))"; }
step "python version"; python3 --version
step "venv + install (article's pip line)"
python3 -m venv .venv && . .venv/bin/activate
export PIP_CONFIG_FILE=/dev/null; start=$(date +%s); pip install -q "apify-client>=3.2.1,<4" httpx datasketch 2>&1 | tail -2; echo "install took $(( $(date +%s) - start ))s"
APIFY_TOKEN=$(grep -h APIFY_TOKEN ".env" | cut -d= -f2 | tr -d '"')
export APIFY_TOKEN
for cmd in "signals.py" "collect.py" "baseline.py" "dedup.py" "rephrase.py" "build_round.py" "monitor.py rows.jsonl crawl_id"; do
  step "python $cmd"; t=$(date +%s)
  python $cmd 2>&1 | tail -15; echo "exit ${PIPESTATUS[0]}, took $(( $(date +%s) - t ))s"
done
