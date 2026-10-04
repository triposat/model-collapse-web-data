# Experiments behind the model collapse article

This folder holds the code and the results for the tests in the Apify blog article "Model collapse: why AI models degrade and how to prevent it".

## GPT-2 trained on its own output

`collapse_exp.py` runs a small version of the recursive-training setup from Shumailov et al. (Nature, 2024). It uses GPT-2 small and 478 Wikipedia featured articles that Website Content Crawler collected.

- `run_seeds.sh` holds the exact settings for seeds 1 and 2. Seed 0 used the same settings.
- `pilot_results.json` (seed 0), `seed1/`, and `seed2/` hold the per-round results and the logs.
- `summarize_for_article.py` prints every number that the article states. `summary_3seeds.json` is its output. This includes the rare words, which are the words that appear at most twice in the round-0 training data, the run time per seed, and the per-round trends of the two perplexity scores.
- `aggregate_seeds.py` draws the perplexity chart in `../images/model-collapse-perplexity.png`.

The script needs `torch` and `transformers`. It ran on a 16 GB Apple M3 laptop, with `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.5` and `PYTORCH_MPS_LOW_WATERMARK_RATIO=0.4`.

## Publish dates against text changes

The scripts are in `dates/`:

- `wiki_revisions.py` compares the current revision of each featured article with its last revision before November 30, 2022, through the MediaWiki API.
- `analyze_dates.py` and `page_dates.py` read the claimed publish and last-edit dates of the Google-ranking pages.
- `fetch_pairs.py` and `analyze_pairs.py` compare those pages with their last Internet Archive capture from before ChatGPT.
- `scan_signals.py` and `scan_block.py` check the AI-use signals in each site's robots.txt.
- `archive_redirects.py` shows how far the archive moves a request with a fixed date. `wayback40_served.json` holds the requested and the served URL of 40 Wikipedia articles from one Website Content Crawler run.
- `time_cdx.py` times `last_capture()` from `baseline.py` on 12 pages. `cdx_timing_output.txt` is our run.
- `moved_page.py` checks the old and the current URL of a GeeksforGeeks tutorial that moved. `moved_page_output.txt` is our run.

`plot_dates.py` draws `../images/publish-vs-edit-dates.png`.

## Overlap between the versions of a page

`overlap_13grams.py` measures how many 13-word sequences of each archive row in `../article-code/rows.jsonl` also appear in the live row of the same page. `overlap_13grams_output.txt` is its output.

## Diversity metrics on WildAI

`wildai/sample.py` takes a sample of the WildAI dataset (Russell et al., 2026). `wildai/measure.py` compares the human-labeled and AI-labeled pages. `wildai/noise_floor.py` measures how much the metrics vary between random groups of human-labeled pages, and between page types. WildAI is licensed CC BY-NC-SA 4.0, so this folder doesn't include the sampled text. `sample.py` downloads it again.

## Clean run as a reader

`reader_run/run_as_reader.sh` follows only the article: a fresh virtual environment, its pip line, and the scripts in order. `reader_run/clean_run_log.txt` is our run. It includes the rerun of `rephrase.py` in which the number rule rejected one passage.

## Apify runs

`apify_run.py` starts an Actor run through the Apify API and downloads the dataset. Set `APIFY_TOKEN` before you run it.
