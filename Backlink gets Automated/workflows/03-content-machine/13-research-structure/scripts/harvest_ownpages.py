"""Step 1 (own pages) — turn OUR relevant pages into cards, with their REAL headings.
Pull the asset's RAG + Topic-pages URLs from clubbed-ideas.csv, read each page's body from the
SITE CATALOGUE (config.CONTENT_DB — its `Full content` already carries the real #/##/### heading
markers, so no fetching and no HTML conversion), and run one call per page to card-ify it.
A URL the catalogue lacks falls back to the old live-fetch + convert path.

Card: { gloss, verbatim, source_urls=[url], internal_link=url, tag="ownpage", heading, origin }
"""
import os, re, sys, csv, json, html, urllib.request
from concurrent.futures import ThreadPoolExecutor
import config, llm

csv.field_size_limit(sys.maxsize)
TEMPLATE = llm.load_prompt("harvest-ownpage.md")
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
_URL_RE = re.compile(r"https?://[^\s;()]+")


def _pull_urls(clubbed_csv, asset):
    want = asset.strip().lower()
    row = None
    with open(clubbed_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r.get("Asset", "") or "").strip().lower() == want:
                row = r
                break
    if not row:
        # A MINTED SPOKE (or any asset not in clubbed-ideas.csv) has no clubbed row — and clubbed own-pages are
        # ENRICHMENT (internal-link candidates), not a hard input (the structure's real content is STORM cards).
        # So degrade gracefully instead of killing the whole build: no clubbed own-pages, carry on. [Issue 5]
        print(f"  · asset not in clubbed ({asset!r}) — no clubbed own-pages (fine for spokes); continuing", file=sys.stderr)
        return []
    urls, seen = [], set()
    for col in ("RAG candidates", "Topic pages we own"):
        for chunk in (row.get(col, "") or "").split(";"):
            m = _URL_RE.search(chunk)
            if not m:
                continue
            url = m.group(0).rstrip(".,")
            key = url.rstrip("/").lower()
            if key not in seen:
                seen.add(key)
                title = chunk[:m.start()].strip().rstrip("—-").strip()
                urls.append({"title": title, "url": url})
    return urls


def _fetch(url):
    for _ in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception:
            continue
    return None


def _html_to_md(h):
    """Cheap HTML -> markdown-ish: drop script/style/head, mark h1-3, keep list/paragraph breaks."""
    h = re.sub(r"(?is)<(script|style|head|nav|footer)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<!--.*?-->", " ", h)
    for tag, mark in (("h1", "\n# "), ("h2", "\n## "), ("h3", "\n### ")):
        h = re.sub(rf"(?is)<{tag}[^>]*>", mark, h)
        h = re.sub(rf"(?is)</{tag}>", "\n", h)
    h = re.sub(r"(?is)<li[^>]*>", "\n- ", h)
    h = re.sub(r"(?is)<(p|br|/p|div|/div|tr)[^>]*>", "\n", h)
    h = re.sub(r"(?is)<[^>]+>", " ", h)           # strip remaining tags
    h = html.unescape(h)
    h = re.sub(r"[ \t]+", " ", h)
    h = re.sub(r"\n\s*\n\s*\n+", "\n\n", h)
    return h.strip()


def _split_sections(md):
    """Split the markdown-ish page into heading-sections (code). Each = heading + its FULL text until the next
    heading. A leading pre-heading block is kept as an intro. This is the verbatim — 100% faithful, complete."""
    secs, head, buf = [], None, []
    for ln in md.splitlines():
        m = re.match(r"^#{1,6}\s+(.*)", ln.strip())
        if m:
            if (head is not None) or buf:
                secs.append({"heading": head or "(intro)", "text": "\n".join(buf).strip()})
            head, buf = m.group(1).strip(), []
        else:
            buf.append(ln)
    if head is not None or buf:
        secs.append({"heading": head or "(intro)", "text": "\n".join(buf).strip()})
    return [s for s in secs if len(s["text"]) > 40]        # drop empty / near-empty sections


_CATALOGUE = None

def _catalogue_body(url):
    """The page's body from the site catalogue (heading markers already inline). Lazy-loaded once."""
    global _CATALOGUE
    if _CATALOGUE is None:
        _CATALOGUE = {}
        if os.path.exists(config.CONTENT_DB):
            with open(config.CONTENT_DB, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    _CATALOGUE[r["URL"].rstrip("/").lower()] = r.get("Full content", "")
        else:
            print(f"    !! no site catalogue at {config.CONTENT_DB} — every page falls back to live fetch")
    return _CATALOGUE.get(url.rstrip("/").lower(), "")


def _extract_page(page):
    """Card-ify one page: catalogue body first (no fetch, markers inline); live-fetch fallback for
    URLs the catalogue lacks. Re-runs the extraction up to HARVEST_RETRIES extra times if empty.
    Returns [] on genuine failure (fetch dead / no real sections after retries)."""
    body = _catalogue_body(page["url"])
    if body and re.search(r"(?m)^#{1,3} ", body):          # the harvest contract NEEDS the markers
        secs = _split_sections(body[:60000])
    else:
        raw = _fetch(page["url"])                          # _fetch already retries the network twice
        if not raw:
            print(f"    !! not in catalogue and fetch failed: {page['url']}")
            return []
        secs = _split_sections(_html_to_md(raw)[:60000])
    if not secs:
        print(f"    !! no content sections found: {page['url']}")
        return []
    listing = "\n\n".join(f"[{i}] {s['heading']}\n{s['text'][:1500]}" for i, s in enumerate(secs))
    prompt = TEMPLATE.replace("{{SECTIONS}}", listing)
    for _ in range(config.HARVEST_RETRIES + 1):
        try:
            out = llm.call_json(prompt)
        except Exception:
            out = []
        cards = []
        for it in out:
            i, gloss = it.get("index"), (it.get("gloss") or "").strip()
            if not isinstance(i, int) or not (0 <= i < len(secs)) or not gloss:
                continue
            s = secs[i]                                    # verbatim = the FULL section text (code, exact)
            cards.append({"gloss": gloss, "verbatim": s["text"], "source_urls": [page["url"]],
                          "internal_link": page["url"], "tag": "ownpage",
                          "heading": s["heading"], "origin": f"ownpage/{page['url']}"})
        if cards:
            return cards
    print(f"    !! produced NO cards after {config.HARVEST_RETRIES + 1} tries: {page['url']}")
    return []


def harvest(asset, clubbed_csv=None):
    urls = _pull_urls(clubbed_csv or config.CLUBBED_CSV, asset)
    print(f"  own pages: {len(urls)} relevant pages")
    cards, failed = [], []
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        for page, res in zip(urls, ex.map(_extract_page, urls)):
            cards += res
            if not res:
                failed.append(page["url"])
    print(f"  own pages: {len(cards)} cards from {len(urls) - len(failed)}/{len(urls)} pages")
    if failed:
        print(f"  !! own pages: {len(failed)} page(s) produced NO cards after retries: {failed}")
    return cards


if __name__ == "__main__":
    asset, out_path = sys.argv[1], sys.argv[2]
    cards = harvest(asset)
    config.write_json(out_path, cards)
    print(f"-> {out_path}")
    for c in cards[:6]:
        print(f"  {c['heading'][:40]} :: {c['gloss'][:55]}")
