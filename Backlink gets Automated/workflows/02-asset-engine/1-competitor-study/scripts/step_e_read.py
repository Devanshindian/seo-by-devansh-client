#!/usr/bin/env python3
"""Step E — read EVERY kept page in full. The step the recipe says gets skipped.

The recipe's own words (L60, L288-293): "It exists because steps get silently skipped (Step E was once
faked with page titles)" and "⛔ HARD RULES — this is the step that gets silently skipped. Do not.
1. Read all kept rows. 2. A page that won't load is marked FETCH FAILED, never '(from title)'.
3. At the end, print a tally."

REUSES LAYER 00'S FETCHER AND EXTRACTOR (Devansh, 2026-07-20 — "is it something we have built already
in the site catalogue? would that not be useful?"). It is strictly better than the extractor this
engine inherited:
    site catalogue : 4 extractors (dom / trafilatura / resiliparse / html2txt), keeps the LONGEST,
                     robots.txt-aware polite fetch, token-bucket rate limiting, raw disk cache,
                     block detection, SIGALRM wall-clock cap — proven on ~10,000 pages
    the old one    : cheerio+turndown, single attempt, returns null under 100 words, and its import
                     path is broken today (points at a dist/ directory that does not exist)
Nothing here re-implements fetching or extraction; it calls Layer 00's.

SOFT-404 DETECTION — the recipe never specifies it, but the real run needed it: 70 rows returned HTTP
200 with a "Page Not Found" body and had to be reclassified BY HAND after the fact. Detected here two
ways: a body-signature check, and a repeated-body check (N pages sharing one byte-identical body is a
template, not content — the same signature trick Layer 00 uses for soft-404s).

Reads:  _work/formats/<domain>.json
Writes: _work/read/<domain>.json          (rows + body/read_status/read_method)
        _work/master.json                 THE MASTER SHEET — every competitor, every kept page
        _work/read-report.json            the tally the recipe demands
"""
import argparse, hashlib, json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c

# Layer 00's fetch + extract, CALLED not copied — one implementation, so a fix there reaches here (F1/F5).
# Layer 00 runs in its own Python 3.11 venv (httpx / protego / trafilatura / resiliparse), so if this
# interpreter cannot import them we RE-EXECUTE this script with Layer 00's interpreter. Generalized:
# the venv path is derived from the same anchor as everything else, so it holds on any machine and for
# any company; if the venv is missing we say exactly how to create it rather than failing obscurely.
_CAT_DIR = os.path.join(c.WORKFLOWS, "00-foundation", "1-site-catalogue")
_CAT = os.path.join(_CAT_DIR, "scripts")
_CAT_PY = os.path.join(_CAT_DIR, "venv", "bin", "python")
sys.path.insert(0, _CAT)

def _ensure_layer00_runtime():
    """Import Layer 00's deps, or hand off to the interpreter that has them."""
    try:
        import httpx, protego, trafilatura      # noqa: F401 — the probe IS the check
        return
    except ImportError:
        pass
    if os.environ.get("_CS_RELAUNCHED"):
        sys.exit("!! Layer 00's venv is missing its dependencies — recreate it:\n"
                 f"   cd {c.rel(_CAT_DIR)} && uv venv --python 3.11 venv && "
                 "uv pip install --python venv/bin/python -r requirements.txt")
    if not os.path.exists(_CAT_PY):
        sys.exit(f"!! Step E reuses Layer 00's fetcher, but its venv is not built.\n"
                 f"   cd {c.rel(_CAT_DIR)} && uv venv --python 3.11 venv && "
                 "uv pip install --python venv/bin/python -r requirements.txt")
    os.environ["_CS_RELAUNCHED"] = "1"
    print(f"   (re-launching in Layer 00's runtime: {c.rel(_CAT_PY)})")
    os.execv(_CAT_PY, [_CAT_PY, os.path.abspath(__file__)] + sys.argv[1:])

_H1 = re.compile(r"^#\s+\S", re.M)     # the extractors mark headings with # markers


def _trim_chrome(body):
    """Drop the nav/cookie/tag-manager preamble before the first H1.

    Measured 2026-07-20: 46% of extracted bodies opened with navigation junk ("Google Tag Manager
    (noscript)", a menu, "Book a Demo") before the article began. Trimming to the first H1 halves that
    to 25%. Deliberately conservative — if no H1 is found, or the first H1 sits past the halfway point
    (so the "chrome" would be most of the page), the body is left untouched. Never removes content.
    The rest is tolerable: it is noise to a reader, not corruption."""
    m = _H1.search(body)
    if not m or m.start() > len(body) * 0.5:
        return body
    return body[m.start():]


SOFT404 = re.compile(
    r"\b(page not found|404 error|page you (are|were) looking for (does not|doesn't) exist|"
    r"this page (does not|doesn't) exist|nothing (was )?found|content not available|"
    r"sorry,? (we )?(can'?t|could not|couldn'?t) find)\b", re.I)


_L00 = {}
_DOMAIN_BUCKETS = {}
# Serialises the ONE thread-unsafe thing in extraction: libxml2's HTML parser. _extract_one parses
# internally, so we lock around the whole call. Extraction is CPU-fast; the slow network fetch runs
# OUTSIDE this lock and stays fully parallel. See _read_one for the crash this prevents.
_EXTRACT_LOCK = threading.Lock()


_BUCKET_LOCK = None


class _PerDomainBucket:
    """Layer 00's rate limiter is ONE GLOBAL bucket at 1 req/sec — correct for its job (crawling a
    single site politely), wrong for ours (24 different sites). Every page queued behind one global
    limit, so 3,884 pages meant 65 minutes MINIMUM however many threads were running.

    Each domain gets its OWN bucket here. testgorilla.com still sees exactly 1 req/sec, and so does
    every other site — but the sites proceed in parallel. Politer per host AND far faster overall,
    because the load is spread instead of serialised. (Devansh's suggestion, 2026-07-20.)"""

    def __init__(self, rps):
        import threading
        self.rps = rps
        self._lock = threading.Lock()
        self._buckets = {}

    def _for(self, host):
        import threading
        with self._lock:
            b = self._buckets.get(host)
            if b is None:
                b = {"delay": 1.0 / max(self.rps, 0.05), "next": 0.0, "lock": threading.Lock()}
                self._buckets[host] = b
            return b

    def wait_for(self, url):
        import time
        from urllib.parse import urlsplit
        host = (urlsplit(url).netloc or "").lower()
        b = self._for(host)
        with b["lock"]:
            now = time.monotonic()
            wake = max(now, b["next"])
            b["next"] = wake + b["delay"]
        time.sleep(max(0.0, wake - time.monotonic()))

def _layer00():
    """Import Layer 00's fetch+extract IN ISOLATION and cache them.

    Both layers have a scripts/config.py, so a plain import makes Layer 00's fetcher bind to the ASSET
    ENGINE's config and die on the first missing constant (config.RATE_RPS). We therefore swap sys.path
    and the cached 'config' module for the duration of the import, then restore. fetch/extract capture
    Layer 00's config at import time, so they keep working afterwards.

    Layer 00's fetcher caches raw HTML under ITS config.RAW — pointing at the company's own site cache.
    We redirect that to this engine's own _raw/pages so a competitor crawl never pollutes the company's
    catalogue cache."""
    if _L00:
        return _L00["fetch"], _L00["extract"]
    saved_path, saved_cfg = list(sys.path), sys.modules.pop("config", None)
    try:
        sys.path.insert(0, _CAT)
        import config as cat_cfg
        cat_cfg.RAW = os.path.join(c.RAW, "pages")          # keep competitor HTML out of Layer 00's cache
        cat_cfg.RATE_RPS = 1000.0                           # disarm the GLOBAL bucket (this process only);
                                                            # politeness is enforced per-domain below
        # PATIENCE DIALS — Layer 00 waits 120s after a firewall block and retries 6 times, because its
        # job is EVERY page of one site: coverage is its deliverable, so waiting is worth it. Ours is
        # different — we read 24 competitors and missing a few pages changes nothing, while 5 blocks
        # cost 10 minutes of pure sleeping (measured 2026-07-20: that was the whole 7-minute smoke test).
        # A blocked page is recorded FETCH FAILED and we move on. Same code, different dials.
        # THE GLOBAL IN-FLIGHT CAP. Layer 00 allows FETCH_CONCURRENCY requests in flight for the whole
        # run (default 6) — right when crawling ONE site, since you should not open 36 connections to
        # someone's server. But we read 24 DIFFERENT sites, and everything funnels through that one
        # gate: measured 2026-07-20, peoplemanagingpeople's blocked requests each held a slot for 8s,
        # starving all 6 competitor workers and stalling the entire scrape (zero pages in 10 minutes).
        # Politeness is already enforced PER HOST by _PerDomainBucket, so the global cap only has to be
        # wide enough not to be the bottleneck.
        cat_cfg.FETCH_CONCURRENCY = c.GLOBAL_INFLIGHT
        cat_cfg.BLOCK_GIVE_UP = c.BLOCK_GIVE_UP
        cat_cfg.FIREWALL_COOLDOWN = c.BLOCK_COOLDOWN
        cat_cfg.FETCH_ATTEMPTS = c.FETCH_ATTEMPTS
        cat_cfg.FETCH_TIMEOUT = c.FETCH_TIMEOUT
        cat_cfg.FRONTIER_DB = os.path.join(c.WORK, "fetch-frontier.sqlite")
        os.makedirs(cat_cfg.RAW, exist_ok=True)
        import fetch as cat_fetch
        import extract as cat_extract
        # fetch.py sizes its semaphore at IMPORT time, so setting the config value above is not enough
        import threading
        cat_fetch._sem = threading.BoundedSemaphore(c.GLOBAL_INFLIGHT)
        _L00["fetch"], _L00["extract"] = cat_fetch, cat_extract
        return cat_fetch, cat_extract
    finally:
        sys.path[:] = saved_path
        sys.modules.pop("config", None)
        if saved_cfg is not None:
            sys.modules["config"] = saved_cfg


def _read_one(row):
    """Fetch + extract one page through Layer 00's stack. Never raises."""
    from urllib.parse import urlsplit
    cat_fetch, cat_extract = _layer00()
    url = row.get("url") or ""
    host = (urlsplit(url).netloc or "").lower()
    _DOMAIN_BUCKETS["b"].wait_for(url)          # 1 req/sec PER SITE, not 1 req/sec in total
    try:
        res = cat_fetch.get(url, obey_robots=True)
        html = getattr(res, "text", None) or getattr(res, "html", None) or ""
        status = getattr(res, "status", None) or getattr(res, "status_code", None)
        if not html:
            row.update(body="", read_status="FETCH FAILED", read_method="empty", http=status)
            return row
        # THE FULL LADDER. Call Layer 00's real _extract_one — the exact 5-rung extractor that built the
        # site catalogue at 0% one-line blobs. This engine used to RE-IMPLEMENT only rung 2 (the three
        # extractors) plus the raw html2txt floor, dropping rung 3 (JSON-LD articleBody / bare <article>)
        # and rung 4 (the SPA browser-render label). On competitor pages the three extractors come back
        # thin far more often than on our own WordPress site, so 960 reads (40%) fell to that floor and
        # returned one unbroken line — menu and article mashed together, no structure. Measured
        # 2026-07-21 over the cached HTML: calling the full ladder recovers 97% of those blobs to clean,
        # structured text, almost all via `dom`, no browser needed. (Devansh: "follow the 00 code".)
        #
        # _extract_one parses HTML with libxml2's thread-UNSAFE parser — the `Abort trap: 6` that killed
        # the run at GLOBAL_INFLIGHT=40 (POINTER_BEING_FREED inside _fixHtmlDictNames). Serialise the
        # parse with _EXTRACT_LOCK; it is CPU-fast, and the slow network fetch above stays parallel.
        try:
            with _EXTRACT_LOCK:
                xr = cat_extract._extract_one(url, {}, html, "")
            body = xr.get("Full content") or ""
            method = xr.get("extractor") or "none"
        except Exception as e:
            body, method = "", f"extract-error:{type(e).__name__}"
        row["read_method"] = method
        body = _trim_chrome(body.strip()).strip()
        if not body or len(body.split()) < c.MIN_BODY_WORDS:
            row.update(body=body, read_status="FETCH FAILED", http=status)
        elif SOFT404.search(body[:1200]):
            row.update(body=body, read_status="FETCH FAILED", read_method="soft-404", http=status)
        else:
            row.update(body=body, read_status="ok", http=status)
    except Exception as e:
        name = type(e).__name__
        row.update(body="", read_status="FETCH FAILED", read_method=f"error:{name}", http=None)
    return row


def run(redo=False, limit=0):
    _layer00()                     # load ONCE on the main thread — the sys.modules swap is not thread-safe
    _DOMAIN_BUCKETS["b"] = _PerDomainBucket(c.PER_DOMAIN_RPS)
    os.makedirs(os.path.join(c.WORK, "read"), exist_ok=True)
    fdir = os.path.join(c.WORK, "formats")
    files = sorted(f for f in os.listdir(fdir) if f.endswith(".json"))
    if not files:
        sys.exit("!! no _work/formats/*.json — run step_d_format.py first")

    def _do_competitor(f):
        """One competitor, start to finish. Safe to run several of these at once: each site has its
        own rate bucket, so parallelism here spreads load across hosts instead of hammering one."""
        domain = f[:-5]
        out_path = os.path.join(c.WORK, "read", f)
        if os.path.exists(out_path) and not redo:
            rows = json.load(open(out_path))
            return domain, rows, {"competitor": domain, "cached": True, "rows": len(rows)}
        rows = json.load(open(os.path.join(fdir, f)))
        # Skip shapes the canonicaliser already judged NOT a content asset (user profiles, help pages,
        # homepages, spam). Format is decided BEFORE this step, so there is no reason to spend a fetch
        # on a page we will exclude from every downstream table anyway. Measured 2026-07-20: 306 of the
        # first 1,202 pages scraped were junk — fetched, then discarded. Run F0 before E and they cost
        # nothing. Their rows are kept with a status so the count still reconciles.
        skipped = [dict(r, read_status="SKIPPED (not a content asset)", body="") 
                   for r in rows if r.get("format_junk")]
        rows = [r for r in rows if not r.get("format_junk")]
        if limit:
            rows = rows[:limit]
        if not rows:
            c.write_json(out_path, [])
            return domain, [], {"competitor": domain, "rows": 0}
        done = []
        with ThreadPoolExecutor(max_workers=c.READ_WORKERS) as ex:
            for fut in as_completed([ex.submit(_read_one, r) for r in rows]):
                done.append(fut.result())
        # repeated-body check: N pages sharing one byte-identical body is a template, not content
        sig = {}
        for r in done:
            if r.get("read_status") == "ok":
                h = hashlib.sha256((r.get("body") or "").encode()).hexdigest()
                sig.setdefault(h, []).append(r)
        for h, group in sig.items():
            if len(group) >= c.DUP_BODY_ALARM:
                for r in group:
                    r["read_status"] = "FETCH FAILED"
                    r["read_method"] = f"duplicate-body x{len(group)}"
        ok = sum(1 for r in done if r["read_status"] == "ok")
        done += skipped                                    # keep them so the counts reconcile
        c.write_json(out_path, done)                       # written per competitor -> resumable
        return domain, done, {"competitor": domain, "rows": len(done), "read": ok,
                              "failed": len(done) - ok - len(skipped), "skipped": len(skipped)}

    master, report = [], []
    print(f"   {len(files)} competitors · {c.COMPETITOR_PARALLEL} at a time · "
          f"{c.PER_DOMAIN_RPS} req/sec per site · {c.READ_WORKERS} threads within each")
    with ThreadPoolExecutor(max_workers=c.COMPETITOR_PARALLEL) as pool:
        futs = {pool.submit(_do_competitor, f): f for f in files}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                domain, rows, rep = fut.result()
            except Exception as e:
                print(f"   !! {futs[fut]}: {str(e)[:80]}"); continue
            master += rows
            report.append(rep)
            tag = ("cached" if rep.get("cached") else
                   f"{rep.get('read',0)} read, {rep.get('failed',0)} failed"
                   + (f", {rep['skipped']} junk skipped" if rep.get("skipped") else ""))
            print(f"   [{i:>2}/{len(files)}] {domain:26s} {rep.get('rows',0):>4} rows · {tag}")

    c.write_json(os.path.join(c.WORK, "master.json"), master)
    c.write_json(os.path.join(c.WORK, "read-report.json"), report)
    ok = sum(1 for r in master if r.get("read_status") == "ok")
    print(f"\n   THE TALLY (the recipe demands this): "
          f"{len(master)} rows -> {ok} read, {len(master)-ok} FETCH FAILED")
    print(f"   master sheet -> {c.rel(os.path.join(c.WORK, 'master.json'))}")
    return master


if __name__ == "__main__":
    _ensure_layer00_runtime()          # must happen before any Layer 00 import
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="first N rows per competitor (a smoke test)")
    a = ap.parse_args()
    run(a.redo, a.limit)
