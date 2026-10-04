"""Read a site's AI-training preferences from its robots.txt before you crawl it."""
from urllib.robotparser import RobotFileParser

import httpx

# Name your crawler and give a contact URL. Some sites refuse anonymous clients.
USER_AGENT = "my-dataset-builder/1.0 (+https://example.com/crawler)"
AI_TRAINING_BOTS = ["GPTBot", "ClaudeBot", "CCBot", "Google-Extended",
                    "Applebot-Extended", "meta-externalagent", "Bytespider"]


def ai_signals(host: str) -> dict:
    try:
        resp = httpx.get(f"https://{host}/robots.txt", headers={"User-Agent": USER_AGENT},
                         follow_redirects=True, timeout=20)
    except httpx.HTTPError:  # timeout, DNS, or TLS error: the answer is unknown
        return {"robots": None, "signals": {}, "blocks_ai_bots": [], "no_train": None}
    if resp.status_code in (404, 410):
        return {"robots": resp.status_code, "signals": {}, "blocks_ai_bots": [],
                "no_train": False}
    if resp.status_code != 200:
        # A blocked or failed robots.txt request tells you nothing, so skip the site
        return {"robots": resp.status_code, "signals": {}, "blocks_ai_bots": [],
                "no_train": None}

    # Content-Signal (Cloudflare) and Content-Usage (IETF draft) lines.
    # Standard robots.txt parsers skip both, so read them here.
    signals = {}
    for line in resp.text.splitlines():
        key, _, value = line.split("#", 1)[0].partition(":")
        if key.strip().lower() not in ("content-signal", "content-usage"):
            continue
        for pair in value.split(","):
            name, _, setting = pair.partition("=")
            if not name.strip():
                continue
            name = name.split()[-1].lower()  # drops a path prefix, as in "/docs/ train-ai=n"
            if signals.get(name) not in ("no", "n"):  # a "no" in any group wins
                signals[name] = setting.strip().lower()

    # A site that blocks the known AI training crawlers has also answered the question
    robots = RobotFileParser()
    robots.parse(resp.text.splitlines())
    blocked = [bot for bot in AI_TRAINING_BOTS
               if not robots.can_fetch(bot, f"https://{host}/")]

    # The signal vocabularies are still drafts, so any training key set to no counts
    no_train = bool(blocked) or any(
        "train" in name and setting in ("no", "n") for name, setting in signals.items()
    )
    return {"robots": 200, "signals": signals, "blocks_ai_bots": blocked,
            "no_train": no_train}


if __name__ == "__main__":
    for host in ["en.wikipedia.org", "www.pewresearch.org",
                 "www.bbcgoodfood.com", "stackoverflow.com"]:
        print(host, ai_signals(host))
