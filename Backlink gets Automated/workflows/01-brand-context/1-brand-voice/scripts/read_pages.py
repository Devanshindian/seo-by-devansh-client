#!/usr/bin/env python3
"""Step 1 — read each shortlisted page into one evidence row (the recipe's one-sub-agent-per-page).

Reads:  SHORTLIST_MD (file+URL per page) + PAGES_DIR bodies. A thin saved page (< THIN_WORDS) falls back
        to the catalogue's Full content for the same URL (offline; never classify a page we couldn't read —
        a page thin in BOTH is recorded as thin, not guessed at).
Writes: WORK/evidence.json — the page-evidence table, one row per page, fields per the recipe's Step-1
        columns. Resumable: rows already present are kept; only missing pages are read.
"""
import csv, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config, llm

csv.field_size_limit(sys.maxsize)
PROMPT = llm.load_prompt("extract-evidence.md")
_URL_RE = re.compile(r"https?://[^\s)·]+")


def _pages():
    """(file, url) pairs: every _pages/ file matched to a shortlist URL by order of appearance."""
    urls = _URL_RE.findall(open(config.SHORTLIST_MD).read())
    urls = [u.rstrip(".,)") for u in urls if config.DOMAIN in u]
    files = sorted(f for f in os.listdir(config.PAGES_DIR) if f.endswith(".md"))
    pairs = []
    for i, f in enumerate(files):
        pairs.append((f, urls[i] if i < len(urls) else ""))
    return pairs


def _body(fname, url, cat):
    text = open(os.path.join(config.PAGES_DIR, fname), encoding="utf-8", errors="replace").read()
    if len(text.split()) >= config.THIN_WORDS:
        return text, False
    row = cat.get(url) or cat.get(url.rstrip("/") + "/")
    alt = (row or {}).get("Full content", "")
    if len(alt.split()) >= config.THIN_WORDS:
        return alt, False
    return (alt if len(alt) > len(text) else text), True     # thin in both — recorded, never guessed


def _extract(fname, url, cat):
    body, thin = _body(fname, url, cat)
    p = (PROMPT.replace("{{BRAND}}", config.BRAND).replace("{{URL}}", url)
         .replace("{{BODY}}", body[:config.BODY_CHAR_CAP]))
    row = llm.call_json(p)
    row.update(page=fname, url=url, thin=thin)
    return row


def run():
    out_path = os.path.join(config.WORK, "evidence.json")
    done = {}
    if os.path.exists(out_path):
        done = {r["page"]: r for r in json.load(open(out_path))}
    with open(config.CATALOGUE_CSV, newline="", encoding="utf-8", errors="replace") as f:
        cat = {r["URL"]: r for r in csv.DictReader(f)}
    todo = [(f, u) for f, u in _pages() if f not in done]
    print(f"   {len(done)} rows cached, {len(todo)} pages to read ({config.WORKERS} at a time)")
    with ThreadPoolExecutor(max_workers=config.WORKERS) as ex:
        futs = {ex.submit(_extract, f, u, cat): f for f, u in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                r = fut.result()
                done[r["page"]] = r
            except Exception as e:
                print(f"   !! {futs[fut]}: {str(e)[:90]}")
            if i % 5 == 0 or i == len(todo):
                config.write_json(out_path, list(done.values()))   # checkpoint as we go
                print(f"   .. {i}/{len(todo)} pages read")
    rows = list(done.values())
    config.write_json(out_path, rows)
    thin = sum(1 for r in rows if r.get("thin"))
    print(f"   evidence table: {len(rows)} rows ({thin} thin pages flagged) -> {out_path}")
    return out_path


if __name__ == "__main__":
    run()
