#!/usr/bin/env python3
"""Polite, resumable HTTP for the site being catalogued — everything else depends on this.

Reads:  config (rate, identity, paths). The target site's robots.txt governs what we touch.
Writes: _raw/<sha[:2]>/<sha>.<ext>  (content-addressed raw payload cache, atomic)
        _work/catalogue.sqlite      (pages table: url -> sha/etag/status; frontier table: resume)

The rules, all measured or spec-mandated:
- ONE token bucket owns the request rate (~1 req/s default; concurrency never raises the rate —
  8 workers once dropped 46% of requests, and ~1.3 r/s tripped the site's firewall).
- Honest User-Agent from the company record. A spoofed browser UA is worse: the TLS fingerprint
  contradicts the claim and the mismatch is itself a bot signal.
- Retries (tenacity) on timeouts / transport errors / 429 / 5xx ONLY, full-jitter backoff,
  honouring Retry-After. A 403 or a cf-mitigated header = FIREWALL BLOCK: sit out a long
  cooldown, permanently slow the bucket, retry a little — then raise Blocked. Never silence.
- Cache the raw payload, not the HTTP transaction: fetch once, re-parse offline forever.
  A cached URL is served with ZERO network calls. refresh=True revalidates with a conditional
  GET (ETag/Last-Modified) instead.
- The frontier table hands out work with an atomic claim (UPDATE...RETURNING), so a killed run
  resumes exactly where it stopped and two workers can never claim the same URL.
"""
import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
import urllib.parse as _up

import httpx
from protego import Protego
from tenacity import (Retrying, retry_if_exception_type,
                      stop_after_attempt, wait_random_exponential)

import config


# A host that has refused us BLOCK_GIVE_UP times running will refuse the next one too. Without this
# the crawler keeps paying full cooldowns for every remaining URL on a site that will never answer
# (262 pages x 8s = 35 wasted minutes, measured 2026-07-20). Any success clears the streak.
_dead_hosts = {}
_dead_lock = threading.Lock()


def _note_block(host):
    with _dead_lock:
        _dead_hosts[host] = _dead_hosts.get(host, 0) + 1
        return _dead_hosts[host]


def _note_success(host):
    with _dead_lock:
        _dead_hosts.pop(host, None)


def host_given_up(url):
    """True once a host has blocked us config.BLOCK_GIVE_UP times in a row."""
    with _dead_lock:
        return _dead_hosts.get(_host_of(url), 0) >= config.BLOCK_GIVE_UP


class Blocked(Exception):
    """The site's firewall is refusing us (403 / cf-mitigated) and the cooldowns didn't clear it.
    Loud by design — a block must stop the stage, never read as 'page empty'."""


class RobotsDisallowed(Exception):
    """robots.txt forbids this URL for our UA. We do not fetch it."""


# ---- stats (checkpoint evidence: "second run serves from cache with zero network calls") ----
STATS = {"network": 0, "cache": 0, "retries": 0, "cooldowns": 0, "not_modified": 0}

# ---- the token bucket — the ONE owner of the request rate -----------------------------------
class _Bucket:
    def __init__(self, rps):
        self.delay = 1.0 / max(rps, 0.05)
        self._next = 0.0
        self._lock = threading.Lock()

    def wait(self):
        with self._lock:
            now = time.monotonic()
            wake = max(now, self._next)
            self._next = wake + self.delay
        time.sleep(max(0.0, wake - time.monotonic()))

    def slower(self):
        """Firewall pushback: permanently double the spacing (cap 8s). Delay only ever grows."""
        with self._lock:
            self.delay = min(8.0, self.delay * 2)
        return self.delay


# ONE BUCKET PER HOST, not one for the whole run.
#
# It was a single global bucket, which is right when crawling ONE site but wrong the moment a run
# spans many. Measured live 2026-07-20 on the competitor study (24 sites): peoplemanagingpeople.com
# firewalled every request, each block called slower(), and because "delay only ever grows" the ONE
# shared bucket was permanently dragged to its 8s cap — so all 24 sites crawled at 8s/page and the
# run stalled dead (zero pages in 10 minutes). One hostile host must only ever slow ITSELF.
_buckets = {}
_buckets_lock = threading.Lock()


def _host_of(url):
    try:
        return (_up.urlsplit(url).netloc or "").lower()
    except Exception:
        return ""


def _bucket_for(url):
    host = _host_of(url)
    with _buckets_lock:
        b = _buckets.get(host)
        if b is None:
            b = _buckets[host] = _Bucket(config.RATE_RPS)
        return b
_sem = threading.BoundedSemaphore(config.FETCH_CONCURRENCY)
_client = httpx.Client(
    headers={"User-Agent": config.USER_AGENT},
    timeout=config.FETCH_TIMEOUT,
    follow_redirects=True,
    http2=True,
)

# ---- robots.txt (protego), fetched once per host, crawl-delay respected ---------------------
_robots = {}
_robots_lock = threading.Lock()

def _robots_for(url):
    host = _up.urlsplit(url).netloc
    with _robots_lock:
        if host in _robots:
            return _robots[host]
    robots_url = f"{config.SCHEME}://{host}/robots.txt"
    try:
        _bucket_for(url).wait()
        r = _client.get(robots_url)
        STATS["network"] += 1
        rp = Protego.parse(r.text) if r.status_code == 200 else Protego.parse("")
    except httpx.HTTPError:
        rp = Protego.parse("")          # unreachable robots = allow (standard), the fetch itself will tell
    delay = rp.crawl_delay(config.USER_AGENT)
    b = _bucket_for(url)
    if delay and delay > b.delay:
        b.delay = float(min(delay, 30))         # the site asked for slower — obey, capped
    with _robots_lock:
        _robots[host] = rp
    return rp


def sitemaps_from_robots(domain):
    """Every Sitemap: line the host's robots.txt declares (some sites publish 8)."""
    rp = _robots_for(f"{config.SCHEME}://{domain}/")
    return list(rp.sitemaps)


# ---- the sqlite store (WAL): page cache metadata + the resume frontier ----------------------
_db_lock = threading.Lock()
_db = None

def _conn():
    global _db
    if _db is None:
        os.makedirs(os.path.dirname(config.FRONTIER_DB), exist_ok=True)
        _db = sqlite3.connect(config.FRONTIER_DB, check_same_thread=False)
        _db.execute("PRAGMA journal_mode=WAL")
        # WAL's documented companion. The default (FULL) fsyncs on EVERY commit, and the frontier
        # commits ~3x per page behind one global lock — measured 2026-07-19 as the real ceiling
        # once fetching went parallel (1.36 pages/s against a 2.5/s network allowance). NORMAL
        # cannot corrupt the DB in WAL mode; a power cut may lose the last few transactions, which
        # here means a few pages revert to 'pending' and are re-fetched. The raw HTML cache is
        # written atomically and separately, so no page CONTENT is at risk either way.
        _db.execute("PRAGMA synchronous=NORMAL")
        _db.execute("""CREATE TABLE IF NOT EXISTS pages(
            url TEXT PRIMARY KEY, sha TEXT, status INTEGER, content_type TEXT,
            etag TEXT, last_modified TEXT, final_url TEXT, fetched_at REAL,
            kept_headers TEXT DEFAULT '')""")
        _db.execute("""CREATE TABLE IF NOT EXISTS frontier(
            url TEXT PRIMARY KEY, state TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0, claimed_at REAL, error TEXT)""")
        _db.commit()
    return _db


def _raw_path(sha, content_type):
    ext = ".html"
    ct = (content_type or "").lower()
    if "xml" in ct:
        ext = ".xml"
    elif "json" in ct:
        ext = ".json"
    elif "html" not in ct and ct:
        ext = ".bin"
    return os.path.join(config.RAW, sha[:2], sha + ext)


class FetchResult:
    __slots__ = ("url", "final_url", "status", "content", "content_type", "headers", "from_cache")

    def __init__(self, url, final_url, status, content, content_type, headers, from_cache):
        self.url, self.final_url, self.status = url, final_url, status
        self.content, self.content_type = content, content_type
        self.headers, self.from_cache = headers, from_cache

    @property
    def text(self):
        return self.content.decode("utf-8", "ignore") if self.content else ""


# Headers worth keeping for cached responses (case-insensitive; stored lowercase). X-WP-Total
# lets the WP layer assert coverage OFFLINE from cache; Link carries rel=canonical.
KEPT_HEADERS = ("x-wp-total", "x-wp-totalpages", "link", "content-length")


def _cached(url):
    with _db_lock:
        row = _conn().execute(
            "SELECT sha, status, content_type, etag, last_modified, final_url, kept_headers "
            "FROM pages WHERE url=?", (url,)).fetchone()
    if not row:
        return None
    sha, status, ctype, etag, lastmod, final_url, kept = row
    path = _raw_path(sha, ctype) if sha else None
    if sha and not os.path.exists(path):
        return None                      # cache row without payload — treat as uncached
    content = open(path, "rb").read() if sha else b""
    headers = json.loads(kept) if kept else {}
    return FetchResult(url, final_url or url, status, content, ctype, headers, True), etag, lastmod


def _store(url, resp):
    body = resp.content or b""
    ctype = resp.headers.get("content-type", "")
    sha = ""
    if body:
        sha = hashlib.sha256(body).hexdigest()
        config.write_bytes(_raw_path(sha, ctype), body)
    kept = json.dumps({k: resp.headers[k] for k in KEPT_HEADERS if k in resp.headers})
    with _db_lock:
        _conn().execute(
            "INSERT OR REPLACE INTO pages(url, sha, status, content_type, etag, last_modified, final_url, fetched_at, kept_headers) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (url, sha, resp.status_code, ctype, resp.headers.get("etag", ""),
             resp.headers.get("last-modified", ""), str(resp.url), time.time(), kept))
        _conn().commit()


def _is_block(resp):
    return resp.status_code == 403 or config.BLOCK_HEADER in resp.headers


def _network_get(url, extra_headers=None, method="GET", attempts=None, last=None, timeout=None):
    """One rate-limited HTTP round trip. Retries timeouts / transport errors / 429 / 5xx with
    full-jitter backoff, honouring Retry-After. Block handling (403/cf-mitigated) lives in get() —
    this helper only does transport-level retries.

    `attempts` overrides FETCH_ATTEMPTS for callers that have ALREADY proved this URL fails
    persistently (the enumerator's bisection probes) — re-proving it 6 times each costs minutes
    and teaches nothing."""
    for attempt in Retrying(
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
            wait=wait_random_exponential(multiplier=1, max=30),
            stop=stop_after_attempt(attempts or config.FETCH_ATTEMPTS),
            reraise=True):
        with attempt:
            _bucket_for(url).wait()
            resp = _client.request(method, url, headers=extra_headers or {},
                                   **({"timeout": timeout} if timeout else {}))
            STATS["network"] += 1
            if resp.status_code == 429 or resp.status_code >= 500:
                retry_after = resp.headers.get("retry-after")
                if (retry_after or "").isdigit():
                    time.sleep(min(int(retry_after), 300))
                STATS["retries"] += 1
                # Keep the response: if the retries exhaust, the caller must be able to tell
                # "the server ANSWERED 500" from "we never reached the server". Collapsing both
                # to status 0 lets a dropped network masquerade as the site's own data.
                if last is not None:
                    last["resp"] = resp
                raise httpx.TransportError(f"HTTP {resp.status_code} (retryable)")
            return resp


def get(url, force=False, refresh=False, obey_robots=True, attempts=None):
    """Fetch a URL through the cache. Returns FetchResult.

    - cached & not refresh/force -> served from disk, ZERO network calls
    - refresh -> conditional GET (ETag/Last-Modified); 304 keeps the cached payload
    - force   -> unconditional refetch, replaces the cache
    - 403/cf-mitigated -> cooldown + slower bucket, few retries, then raises Blocked
    """
    hit = None if force else _cached(url)
    if hit and not refresh:
        STATS["cache"] += 1
        return hit[0]

    if obey_robots and not _robots_for(url).can_fetch(url, config.USER_AGENT):
        raise RobotsDisallowed(url)

    extra = {}
    if hit and refresh:
        _, etag, lastmod = hit
        if etag:
            extra["If-None-Match"] = etag
        if lastmod:
            extra["If-Modified-Since"] = lastmod

    if host_given_up(url):
        raise Blocked(f"{_host_of(url)} — abandoned after {config.BLOCK_GIVE_UP} blocks in a row")

    with _sem:
        cooldowns = 0
        while True:
            last = {}
            try:
                resp = _network_get(url, extra_headers=extra, attempts=attempts, last=last)
            except (httpx.TimeoutException, httpx.TransportError) as e:
                # Retries exhausted. ONE bad URL must never crash a whole-site run — return a
                # failed result the caller records as body_status=failed. Not cached: a later
                # run retries.
                #   status 0   = NO answer at all (timeout, DNS, connection reset, wifi dropped)
                #   status 5xx = the server DID answer, persistently, with its own error
                # The distinction is load-bearing: the enumerator bisects around a server error
                # (a record the CMS cannot render) but must ABORT on status 0, because treating
                # our own dead network as the site's data invents gaps that never existed.
                STATS["fetch_failed"] = STATS.get("fetch_failed", 0) + 1
                answered = last.get("resp")
                return FetchResult(url, url, answered.status_code if answered is not None else 0,
                                   b"", "", {"_fetch_error": str(e)[:200]}, False)
            if _is_block(resp):
                cooldowns += 1
                STATS["cooldowns"] += 1
                if cooldowns > 3:
                    n = _note_block(_host_of(url))
                    if n >= config.BLOCK_GIVE_UP:
                        print(f"  !! {_host_of(url)} has blocked us {n}x in a row — abandoning it; "
                              f"its remaining pages will be recorded as failed", file=sys.stderr)
                    raise Blocked(f"{url} — still blocked after {cooldowns - 1} cooldowns "
                                  f"(HTTP {resp.status_code}, {config.BLOCK_HEADER}="
                                  f"{resp.headers.get(config.BLOCK_HEADER, '-')})")
                delay = _bucket_for(url).slower()
                print(f"  .. firewall block on {url} — cooling down {config.FIREWALL_COOLDOWN}s "
                      f"(spacing now {delay:.1f}s)", file=sys.stderr)
                _sem.release()                      # do NOT hold a global slot while sleeping —
                try:                                # it starves every other host in the run
                    time.sleep(config.FIREWALL_COOLDOWN)
                finally:
                    _sem.acquire()
                continue
            break

    _note_success(_host_of(url))
    if resp.status_code == 304 and hit:
        STATS["not_modified"] += 1
        with _db_lock:
            _conn().execute("UPDATE pages SET fetched_at=? WHERE url=?", (time.time(), url))
            _conn().commit()
        return hit[0]

    _store(url, resp)
    return FetchResult(url, str(resp.url), resp.status_code, resp.content,
                       resp.headers.get("content-type", ""), dict(resp.headers), False)


def head(url, obey_robots=True):
    """Liveness probe (archive layer). No cache — a HEAD answers 'does it exist NOW'.

    Deliberately NOT on the content-fetch retry ladder: that exists so a transient failure never
    loses a page's TEXT, but a probe only asks whether the URL answers right now, and a URL that
    needs six retries across several minutes is not a live page. Measured 2026-07-19: the full
    ladder dragged archive liveness to 0.42 req/s, its slow tail being dead URLs timing out."""
    if obey_robots and not _robots_for(url).can_fetch(url, config.USER_AGENT):
        raise RobotsDisallowed(url)
    with _sem:
        return _network_get(url, method="HEAD", attempts=config.LIVENESS_ATTEMPTS,
                            timeout=config.LIVENESS_TIMEOUT)


# ---- the frontier: resumable work-queue with an atomic claim --------------------------------
def frontier_add(urls):
    with _db_lock:
        _conn().executemany("INSERT OR IGNORE INTO frontier(url) VALUES(?)", [(u,) for u in urls])
        _conn().commit()


def frontier_claim(stale_after=900):
    """Atomically claim one pending URL (or reclaim one stuck in_progress > stale_after seconds).
    Returns the URL or None when the frontier is drained."""
    now = time.time()
    with _db_lock:
        row = _conn().execute(
            "UPDATE frontier SET state='in_progress', claimed_at=?, attempts=attempts+1 "
            "WHERE url=(SELECT url FROM frontier WHERE state='pending' "
            "           OR (state='in_progress' AND claimed_at < ?) LIMIT 1) "
            "RETURNING url", (now, now - stale_after)).fetchone()
        _conn().commit()
    return row[0] if row else None


def frontier_done(url):
    with _db_lock:
        _conn().execute("UPDATE frontier SET state='done', error=NULL WHERE url=?", (url,))
        _conn().commit()


def frontier_fail(url, error):
    with _db_lock:
        _conn().execute("UPDATE frontier SET state='failed', error=? WHERE url=?", (str(error)[:500], url))
        _conn().commit()


def frontier_counts():
    with _db_lock:
        rows = _conn().execute("SELECT state, COUNT(*) FROM frontier GROUP BY state").fetchall()
    return dict(rows)
