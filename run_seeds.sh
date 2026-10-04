#!/bin/bash
# The three seeds of the GPT-2 test, with the settings used for the article.
# Needs wcc_wiki_items.json, which apify_run.py downloads (see README.md).
cd "$(dirname "$0")" || exit 1
for SEED in 0 1 2; do
  PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.5 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.4 \
  python collapse_exp.py \
    --out "seed$SEED" --seed "$SEED" --train_tokens 32000 --test_tokens 19200 --per_doc 10 \
    --gens 4 --epochs 3 --bs 16 --gen_bs 32 --regimes replace,orig10,fresh10,fresh50
done
