"""Read publish and last-edit dates from a Website Content Crawler item (JSON-LD and Open Graph)."""
from datetime import datetime, timezone

ARTICLE_TYPES = {"article", "blogposting", "newsarticle", "techarticle", "webpage", "howto", "recipe",
                 "medicalwebpage", "report", "scholarlyarticle", "faqpage", "qapage", "itempage", "collectionpage"}


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _parse(value):
    if not value or not isinstance(value, str):
        return None
    s = value.strip().replace("Z", "+00:00")
    candidates = [s, s[:19], s[:10]]
    for c in candidates:
        try:
            d = datetime.fromisoformat(c)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def page_dates(item):
    """Return (published, modified) as aware datetimes or None. JSON-LD wins over Open Graph."""
    meta = item.get("metadata") or {}
    pub = mod = None
    for node in _walk(meta.get("jsonLd") or []):
        types = node.get("@type")
        types = [types] if isinstance(types, str) else (types or [])
        if types and not any(str(t).lower() in ARTICLE_TYPES for t in types):
            continue
        pub = pub or _parse(node.get("datePublished"))
        mod = mod or _parse(node.get("dateModified"))
    og = {t.get("property"): t.get("content") for t in (meta.get("openGraph") or []) if isinstance(t, dict)}
    pub = pub or _parse(og.get("article:published_time"))
    mod = mod or _parse(og.get("article:modified_time")) or _parse(og.get("og:updated_time"))
    return pub, mod
