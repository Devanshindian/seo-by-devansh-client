#!/usr/bin/env python3
"""Step 5 — read the top ranking pages with a FREE fetch (no DataForSEO). Extract h1-h3 + word count.
Reads the vetted read-list `04-pages-to-read.txt`, falling back to Step 4's extract. Skips (and notes) any page that blocks or errors.
Usage: python3 s5_pages.py <run_dir>
"""
import os, sys, json, re, ssl, urllib.request

CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
H = re.compile(r"<h([1-3])[^>]*>(.*?)</h\1>", re.I | re.S)
TAG = re.compile(r"<[^>]+>")
import config

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    return urllib.request.urlopen(req, timeout=25, context=CTX).read().decode("utf-8", "ignore")

def fetch(url, tries=3):
    # retry transient blocks at least twice before giving up (total `tries` attempts)
    last = None
    for attempt in range(tries):
        try:
            html = _get(url)
            heads = [TAG.sub("", h[1]).strip()[:80] for h in H.findall(html)]
            heads = [h for h in heads if h][:15]
            wc = len(TAG.sub(" ", html).split())
            if wc > 0:
                return {"word_count": wc, "headings": heads, "attempts": attempt + 1}
            last = "empty body"
        except Exception as e:
            last = str(e)[:80]
    raise RuntimeError(f"failed after {tries} tries: {last}")

def main():
    run = sys.argv[1]
    proof = os.path.join(run, "proof")
    # Prefer the relevance-vetted read-list from Step 4; fall back to raw top-N by rank.
    readlist = os.path.join(proof, "04-pages-to-read.txt")
    if os.path.exists(readlist):
        urls = [l.strip() for l in open(readlist) if l.strip() and not l.startswith("#")][:config.PAGES_TO_READ]
        print(f"read-list: {len(urls)} vetted URLs from 04-pages-to-read.txt")
    else:
        extract = json.load(open(f"{proof}/04-serp-extract.json"))
        urls = [r["url"] for r in extract.get("top_organic", []) if r.get("url")][:config.PAGES_TO_READ]
        print("read-list: none found — falling back to raw top-N from the extract")
    out = {}
    for u in urls:
        try:
            out[u] = fetch(u)
            print(f"\n{u[:64]}  (~{out[u]['word_count']} words)")
            for h in out[u]["headings"][:10]:
                print("   -", h)
        except Exception as e:
            out[u] = {"error": str(e)[:80]}
            print(f"\n{u[:64]}  SKIPPED: {str(e)[:60]}")
    config.write_json(f"{proof}/05-pages.json", out)
    print(f"\nsaved -> {proof}/05-pages.json")

if __name__ == "__main__":
    main()
