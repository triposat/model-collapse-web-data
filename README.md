# GPT-2 model collapse test

Code and results for the test in the Apify blog article "Model collapse: why AI models degrade and how to prevent it". You don't need this repository to follow the article. It's here so that you can check the test's numbers, or run the test yourself.

The test is a small version of the recursive-training setup from Shumailov et al. (Nature, 2024). GPT-2 small learns from its own output for 4 rounds, with 4 mixes of model output and real text. Website Content Crawler collected 480 Wikipedia featured articles, and the test used the 478 that kept more than 2,000 characters after its own text preparation.

## Files

- `collapse_exp.py` is the test. `python collapse_exp.py --help` lists its settings.
- `run_seeds.sh` runs seeds 0, 1, and 2 with the settings from the article.
- `seed0/`, `seed1/`, and `seed2/` hold each seed's results. `results.json` has the scores and sample outputs of every round, `log.txt` is the run log, and `split_urls.json` shows which articles went into training, the test set, and the new real text.
- `summarize_for_article.py` prints every number that the article states about the test. `summary_3seeds.json` is its output.
- `aggregate_seeds.py` draws the perplexity chart from the article, and `aggregate_3seeds.json` holds its numbers.
- `apify_run.py`, `wcc_input.json`, and `wcc_wiki_items_runmeta.json` are the Website Content Crawler run that collected the articles. It took 3 minutes and 10 seconds and cost $0.09.

## Check the numbers

```bash
python summarize_for_article.py seed0/results.json seed1/results.json seed2/results.json
```

The output is JSON. Each value is a list of the mean, the minimum, and the maximum across the 3 seeds. Values that start with `chg_` are changes since round 0 as fractions, so `0.52` means 52% higher. For example, `replace.chg_test_ppl` is the 52% perplexity rise with 100% model output.

## Run the test yourself

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install torch transformers requests matplotlib
export APIFY_TOKEN="your-apify-token"
python apify_run.py apify/website-content-crawler wcc_input.json wcc_wiki_items.json
./run_seeds.sh
python summarize_for_article.py rerun/seed0/results.json rerun/seed1/results.json rerun/seed2/results.json
python aggregate_seeds.py rerun/seed0/results.json rerun/seed1/results.json rerun/seed2/results.json chart.png
```

`run_seeds.sh` writes to `rerun/`, so you can compare your numbers with the published results in `seed0/` to `seed2/`.

Each seed took about an hour on a 16 GB Apple M3 laptop. `collapse_exp.py` uses Apple's MPS by default, so add `--device cuda` or `--device cpu` in `run_seeds.sh` on other hardware. The crawl downloads the current version of each article, so a new run gives slightly different numbers.

## License

The code is under the MIT license. `wcc_wiki_items.json` holds Wikipedia text under CC BY-SA, so it isn't in this repository.
