#!/bin/bash
# Seeds 1 and 2 of the pilot (seed 0 already done), same settings as the pilot.
cd "$(dirname "$0")" || exit 1
for SEED in 1 2; do
  PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.5 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.4 \
  uv run --no-project --python /opt/homebrew/bin/python3.13 python collapse_exp.py \
    --out "seed$SEED" --seed "$SEED" --train_tokens 32000 --test_tokens 19200 --per_doc 10 \
    --gens 4 --epochs 3 --bs 16 --gen_bs 32 --regimes replace,orig10,fresh10,fresh50 \
    > "seed${SEED}_stdout.txt" 2>&1
  echo "SEED $SEED EXIT $?" >> seeds_done.txt
done
