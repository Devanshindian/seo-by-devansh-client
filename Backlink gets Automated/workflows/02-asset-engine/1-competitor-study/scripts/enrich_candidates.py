#!/usr/bin/env python3
"""Step A1b — tell the shortlister WHAT each candidate actually is.

Why this exists: the discovery API returns only `domain · keywords · etv`. Asked to shortlist from
that, the model is guessing a company's business from its NAME. Measured 2026-07-20 on Testlify — it
missed vervoe.com, criteriacorp.com, eskill.com and testdome.com, all four genuine direct rivals that
were sitting in the candidate list it read. Nothing was wrong with the data; the model simply could
not tell what those companies do.

So: fetch each candidate's homepage and lift its <title> + meta description — what the company says it
is, in its own words. FREE (plain HTTP, no API), cached, throttled, and never fatal: a candidate that
won't load simply goes to the model with no description, exactly as before.

Reads:  _work/candidates.json
Writes: _work/candidates-enriched.json   (same rows + title/description)
"""
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error
import config as c

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
TIMEOUT = int(os.environ.get("CS_ENRICH_TIMEOUT", "12"))
WORKERS = int(os.environ.get("CS_ENRICH_WORKERS", "8"))
TOP_N = int(os.environ.get("CS_ENRICH_TOP", "80"))     # enrich the top N by keyword overlap

_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_DESC = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\'](.*?)["\']',
    re.I | re.S)
_ALT = re.compile(
    r'<meta[^>]+content=["\'](.*?)["\'][^>]*(?:name|property)=["\'](?:description|og:description)["\']',
    re.I | re.S)
_TAG = re.compile(r"<[^>]+>")


def _clean(s):
    s = _TAG.sub(" ", s or "")
    s = (s.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
          .replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">"))
    return re.sub(r"\s+", " ", s).strip()[:220]


def fetch_one(domain):
    """Best-effort. A failure is fine — the model just sees no description for that row."""
    for scheme in ("https://", "https://www."):
        try:
            req = urllib.request.Request(scheme + domain, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                html = r.read(180_000).decode("utf-8", "ignore")
            t = _TITLE.search(html)
            d = _DESC.search(html) or _ALT.search(html)
            title, desc = _clean(t.group(1) if t else ""), _clean(d.group(1) if d else "")
            if title or desc:
                return {"title": title, "description": desc}
        except Exception:
            continue
    return {"title": "", "description": ""}


def run(redo=False):
    src = os.path.join(c.WORK, "candidates.json")
    out_path = os.path.join(c.WORK, "candidates-enriched.json")
    if not os.path.exists(src):
        sys.exit("!! no candidates.json — run step_a_competitors.py first")
    cands = json.load(open(src))
    done = {}
    if os.path.exists(out_path) and not redo:
        done = {x["domain"]: x for x in json.load(open(out_path))}

    todo = [x for x in cands[:TOP_N] if x["domain"] not in done]
    print(f"   {len(done)} cached · {len(todo)} homepages to read ({WORKERS} at a time, free)")
    if todo:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(fetch_one, x["domain"]): x for x in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                x = futs[fut]
                try:
                    x.update(fut.result())
                except Exception:
                    x.update({"title": "", "description": ""})
                done[x["domain"]] = x
                if i % 20 == 0:
                    print(f"   .. {i}/{len(todo)}")
                time.sleep(0.05)
    # keep original order; rows past TOP_N carry no description
    merged = [done.get(x["domain"], x) for x in cands]
    c.write_json(out_path, merged)
    got = sum(1 for x in merged if x.get("title") or x.get("description"))
    print(f"   {got}/{len(merged)} candidates now carry a real description -> {c.rel(out_path)}")
    return merged


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
