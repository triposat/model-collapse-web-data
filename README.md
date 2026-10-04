# Model collapse: a collapse-safe web data pipeline

Code and test results for the Apify blog article "Model collapse: why AI models degrade and how to prevent it".

- `article-code/` holds the seven-step pipeline from the article: AI-use signal checks, collection with Website Content Crawler, a pre-ChatGPT baseline from the Internet Archive, deduplication, checked synthetic rows, building a training round with a floor for real data, and diversity monitoring.
- `experiment/` holds the tests behind the article's numbers: GPT-2 trained on its own output (3 seeds), publish dates against text changes, archive lookups, and diversity metrics on WildAI.
- `images/` holds the article's charts and diagrams. `diagram-generator.py` draws the diagrams, and `experiment/aggregate_seeds.py` and `experiment/plot_dates.py` draw the charts.

Each folder has its own README with setup and run instructions.

## License

The code is under the MIT license. WildAI is licensed CC BY-NC-SA 4.0, so `experiment/wildai/` doesn't include the sampled text, and `sample.py` downloads it again.
