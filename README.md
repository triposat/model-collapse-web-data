# Evidence for the Apify article on model collapse

This repository lets you check the numbers that we measured for the Apify blog article "Model collapse: why AI models degrade and how to prevent it". You don't need it to follow the article, because the article contains all of its code.

- `experiment/` holds the GPT-2 test with 3 seeds, and the scripts behind the other numbers that we measured: publish dates against text changes, archive lookups, AI-use signals, and diversity metrics on WildAI. Its README maps each script to its result.
- `article-code/` holds the scripts from the article. The measurements import them, so each number comes from the published code.

## License

The code is under the MIT license. WildAI is licensed CC BY-NC-SA 4.0, so `experiment/wildai/` doesn't include the sampled text, and `sample.py` downloads it again. The scripts in `article-code/` write crawled page text to `.jsonl` files, which aren't in this repository.
