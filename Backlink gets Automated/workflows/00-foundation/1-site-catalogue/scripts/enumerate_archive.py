#!/usr/bin/env python3
"""Layer 3 — URLs the public web archive remembers, filtered hard, then liveness-checked.

Reads:  the Wayback CDX index for the company domain (statuscode:200 + mimetype:text/html only,
        collapsed on urlkey — the raw index is full of junk).
Writes: URLS_ARCHIVE (urls-archive.json):
  { "urls": { <url>: {"alive": true, "final_url": ...} },
    "dead": [...], "checked": N, "cdx_rows": N }

Rules:
- Historical sources tell you what EXISTED; only a live check tells you what EXISTS. Every CDX
  URL is HEAD-checked against the live site (~25% are typically dead) before it may join the union.
- Rate-limit the archive hard (ARCHIVE_MAX_PER_MIN ceiling; blocks double on repeat offence).
- Keep only the company's own hosts (apex + www). Subdomain apps are not site pages.
- Liveness results persist in sqlite (archive_liveness) so a killed run resumes, not restarts.
"""
import json
import os
import time
import urllib.parse as _up

import httpx
from concurrent.futures import ThreadPoolExecutor

import config
import fetch

CDX = "https://web.archive.org/cdx/search/cdx"


def _archive_liveness_table():
    with fetch._db_lock:
        fetch._conn().execute("""CREATE TABLE IF NOT EXISTS archive_liveness(
            url TEXT PRIMARY KEY, alive INTEGER, status INTEGER, final_url TEXT)""")
        fetch._conn().commit()


def _known():
    with fetch._db_lock:
        rows = fetch._conn().execute(
            "SELECT url, alive, status, final_url FROM archive_liveness").fetchall()
    return {u: {"alive": bool(a), "status": s, "final_url": f} for u, a, s, f in rows}


def _record(url, alive, status, final_url):
    with fetch._db_lock:
        fetch._conn().execute(
            "INSERT OR REPLACE INTO archive_liveness(url, alive, status, final_url) VALUES(?,?,?,?)",
            (url, int(alive), status, final_url))
        fetch._conn().commit()


def _declared_elsewhere():
    """Match-keys of every URL the CMS and sitemap layers already declared in THIS run."""
    from reconcile import _match_key
    keys = set()
    for path in (config.URLS_WP, config.URLS_SITEMAP):
        if os.path.exists(path):
            for u in (json.load(open(path)).get("urls") or {}):
                keys.add(_match_key(u))
    return keys


def _cdx_rows(domain):
    """EVERY page of the CDX index. The archive is an API here, not a crawl target — its
    published ceiling (ARCHIVE_MAX_PER_MIN) is the law; we stay far under it.

    `page` is the archive's PAGINATION API: it returns an index BLOCK whose row count has nothing
    to do with `limit`, so "this page came back short" NEVER means the end of the data. Ask the
    index how many pages exist and read them all. Measured 2026-07-19: stopping on a short page
    returned 1,415 of 13,616 rows — 90% of the archive silently missing. Same bug as the CMS
    layer's, in a second file: an authoritative total beats any amount of careful looping.
    """
    client = httpx.Client(headers={"User-Agent": config.USER_AGENT}, timeout=60)
    base = {"url": f"{domain}/*", "matchType": "domain",
            "filter": ["statuscode:200", "mimetype:text/html"]}

    r = client.get(CDX, params={**base, "showNumPages": "true"})
    r.raise_for_status()
    n_pages = int((r.text or "").strip() or 1)
    print(f"   archive index: {n_pages} page(s) to read")

    rows = []
    for page in range(n_pages):
        params = {**base, "output": "json", "collapse": "urlkey", "fl": "original",
                  "limit": "50000", "page": str(page)}
        while True:
            resp = client.get(CDX, params=params)
            if resp.status_code == 429:
                print("   archive says slow down — sitting out 70s")
                time.sleep(70)
                continue
            resp.raise_for_status()
            break
        data = resp.json() if resp.text.strip() else []
        if data and data[0] == ["original"]:
            data = data[1:]
        rows += [d[0] for d in data if d]
        if page + 1 < n_pages:
            time.sleep(60.0 / config.ARCHIVE_MAX_PER_MIN)
    print(f"   read {n_pages}/{n_pages} index page(s) -> {len(rows)} rows")
    return rows


def run():
    domain = config.DOMAIN
    _archive_liveness_table()

    raw = _cdx_rows(domain)
    print(f"   CDX returned {len(raw)} collapsed rows")

    # filter to the site's own hosts; drop query-string noise the archive loves to keep
    candidates = set()
    for u in raw:
        try:
            parts = _up.urlsplit(u)
        except ValueError:
            continue
        if not config.is_own_host(u) or parts.scheme not in ("http", "https"):
            continue
        u2 = _up.urlunsplit((config.SCHEME, domain, parts.path, parts.query, ""))
        candidates.add(u2)
    print(f"   {len(candidates)} candidate URLs on the site's own hosts")

    # Liveness is for HISTORICAL urls (~25% of what the archive remembers is gone). A URL the CMS
    # or the sitemap declared in THIS run is a CURRENT declaration that joins the union on its own
    # merit, so re-HEADing it here proves nothing and costs hours at archive scale (9,663 of
    # 11,518 candidates were already declared, measured 2026-07-19). Check what only the archive
    # knows; keep the rest in the set so provenance and the archive-only difference stay correct.
    from reconcile import _match_key
    declared = _declared_elsewhere()
    known = _known()
    todo = [u for u in candidates if u not in known and _match_key(u) not in declared]
    print(f"   liveness: {len(known)} already checked, {len(todo)} to check "
          f"({sum(1 for u in candidates if _match_key(u) in declared)} skipped — already declared "
          f"by the CMS/sitemap this run)")
    def probe(u):
        """One liveness probe. Returns nothing — it records its own verdict, so a failure here
        can never take down the sweep (one bad URL must never end the job)."""
        try:
            r = fetch.head(u)
            if r.status_code == 405:                      # HEAD not allowed — ask properly
                r = fetch._network_get(u)
            _record(u, r.status_code == 200, r.status_code, str(r.url))
        except fetch.RobotsDisallowed:
            _record(u, False, -1, "")
        except httpx.HTTPError as e:
            _record(u, False, -2, str(e)[:200])

    # Probes run concurrently up to the in-flight cap. This does NOT raise the request rate: the
    # global token bucket still governs req/s. It only stops ONE slow dead URL holding up the
    # queue behind it, which is what a serial loop does and why this stage crawled.
    with ThreadPoolExecutor(max_workers=config.LIVENESS_WORKERS) as ex:
        for i, _ in enumerate(ex.map(probe, todo), 1):
            if i % 100 == 0:
                print(f"   .. {i}/{len(todo)} checked")

    known = _known()
    urls, dead, assumed = {}, [], 0
    for u in sorted(candidates):
        if _match_key(u) in declared:
            # Deliberately NOT liveness-checked: another layer declared it this run. It stays in
            # the archive set so reconcile's provenance (and the archive-only set difference,
            # which is a finding) remains exact.
            urls[u] = {"alive": True, "final_url": "", "liveness": "declared-elsewhere"}
            assumed += 1
            continue
        k = known.get(u)
        if k and k["alive"]:
            urls[u] = {"alive": True, "final_url": k["final_url"], "liveness": "checked"}
        else:
            dead.append(u)
    print(f"   TOTAL: {len(urls)} alive ({assumed} declared elsewhere, {len(urls) - assumed} "
          f"archive-only and HEAD-verified), {len(dead)} dead of {len(candidates)} candidates")
    config.write_json(config.URLS_ARCHIVE, {
        "urls": urls, "dead": dead, "checked": len(candidates), "cdx_rows": len(raw),
        "liveness_skipped_declared": assumed,
    })


if __name__ == "__main__":
    run()
