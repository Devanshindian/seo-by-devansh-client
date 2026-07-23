#!/usr/bin/env python3
"""site-catalogue config — EVERY path and setting, derived from one anchor.

The tool never knows which company it is running for. All company facts come from the
company record (projects/<COMPANY>/company.json, schema: workflows/company-record.md),
selected by the COMPANY environment variable. There is NO default company: an unset
COMPANY or a missing record is a hard stop (fail closed), never a fall-through.

Engine knobs (rates, thresholds, timeouts) live HERE as named constants — they are
method choices, not company facts, and never enter the record.
"""
import json
import os
import sys
import tempfile

# ---- the one path anchor --------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))          # .../1-site-catalogue/scripts
ENGINE = os.path.dirname(HERE)                             # .../1-site-catalogue
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(ENGINE)))   # .../Backlink gets Automated
VENDOR = os.path.join(HERE, "vendor")

# ---- the company record (fail closed — no default company exists in this engine) ------------
COMPANY = os.environ.get("COMPANY", "").strip()
if not COMPANY:
    sys.exit("!! COMPANY is not set. Run as: COMPANY=<slug> ... (or pass --company <slug>). "
             "The slug picks projects/<slug>/company.json — this tool has no default company.")

_RECORD_PATH = os.path.join(REPO_ROOT, "projects", COMPANY, "company.json")

def _load_record():
    try:
        with open(_RECORD_PATH) as f:
            rec = json.load(f)
    except FileNotFoundError:
        sys.exit(f"!! no company record at {_RECORD_PATH} — create it from the template in "
                 f"workflows/company-record.md before running.")
    except json.JSONDecodeError as e:
        sys.exit(f"!! company record is not valid JSON: {_RECORD_PATH} ({e})")
    if rec.get("company") != COMPANY:
        sys.exit(f"!! record mismatch: COMPANY={COMPANY!r} but {_RECORD_PATH} says "
                 f"company={rec.get('company')!r} — refusing to run on crossed wires.")
    missing = [k for k in ("brand", "domain", "location", "language") if not rec.get(k)]
    if missing:
        sys.exit(f"!! company record {_RECORD_PATH} is missing required field(s): "
                 f"{', '.join(missing)} (schema: workflows/company-record.md)")
    return rec

RECORD = _load_record()

BRAND = RECORD["brand"]                       # display name, e.g. for the User-Agent
DOMAIN = RECORD["domain"]                     # the company's own site — the thing we catalogue
WORDPRESS_URL = (RECORD.get("wordpress_url") or "").rstrip("/")   # empty = not a WordPress site
LOCATION = RECORD["location"]                 # DataForSEO location_name (the audience market)
LANGUAGE = RECORD["language"]                 # DataForSEO language code

# Honest bot identity (never a spoofed browser — the TLS fingerprint would contradict the claim)
USER_AGENT = f"{BRAND.replace(' ', '')}CatalogueBot/1.0; +https://{DOMAIN}/bot"

# URL scheme used when building site URLs from the bare domain (robots.txt, sitemap probes,
# the crawl start page). https everywhere real; the offline test harness serves plain http.
SCHEME = os.environ.get("CAT_SCHEME", "https")

def is_own_host(url_or_host):
    """Is this URL/host the company's own site (apex or www)? Port- and case-safe: urlsplit's
    .hostname strips ports and lowercases, so compare hostname to hostname, never to DOMAIN raw."""
    import urllib.parse as _up
    h = _up.urlsplit(url_or_host if "//" in url_or_host else f"//{url_or_host}").hostname or ""
    own = _up.urlsplit(f"//{DOMAIN}").hostname or DOMAIN.lower()
    return h in (own, f"www.{own}")

# ---- output layout: everything lands under projects/<company>/, never in this folder --------
PROJ = os.path.join(REPO_ROOT, "projects", COMPANY)
BASE = os.path.join(PROJ, "00-foundation")
OUT = os.path.join(BASE, "output")
WORK = os.path.join(BASE, "_work")
RAW = os.path.join(BASE, "_raw")              # content-addressed raw HTML: _raw/<sha[:2]>/<sha>.html

CATALOGUE_CSV = os.path.join(OUT, "content-database.csv")   # THE catalogue
TOP_PAGES_CSV = os.path.join(OUT, "top-pages.csv")          # search-traffic view
REPORT_MD = os.path.join(OUT, "catalogue-report.md")        # coverage report: counts, gates, gaps

URLS_WP = os.path.join(WORK, "urls-wp.json")                # layer 1 raw URL set (provenance evidence)
URLS_SITEMAP = os.path.join(WORK, "urls-sitemap.json")      # layer 2
URLS_ARCHIVE = os.path.join(WORK, "urls-archive.json")      # layer 3
URLS_CRAWL = os.path.join(WORK, "urls-crawl.json")          # layer 4 (only if the others are thin)
RECONCILED = os.path.join(WORK, "reconciled.json")          # unioned + canonicalised, source per URL
TRAFFIC_RAW = os.path.join(WORK, "traffic-raw.json")        # DataForSEO rows before grouping
FRONTIER_DB = os.path.join(WORK, "catalogue.sqlite")        # fetch frontier + seen-set (resume)

# ---- fetch politeness (Stage 2) -------------------------------------------------------------
RATE_RPS = float(os.environ.get("CAT_RATE_RPS", "1.0"))  # token bucket: requests/sec to the site
                                                         # (measured: 8 workers dropped 46% of
                                                         # requests; ~1.3 r/s tripped a firewall)
FETCH_WORKERS = int(os.environ.get("CAT_FETCH_WORKERS", "6"))   # parallel frontier workers.
                            # The frontier's atomic claim (UPDATE..RETURNING) was built for this.
                            # Workers do NOT raise req/s — RATE_RPS still governs that; they stop
                            # one slow page blocking the queue. Serial measured 1.0 pages/s
                            # against a 2.5/s allowance, so the loop, not politeness, was the cap.
FETCH_CONCURRENCY = max(3, FETCH_WORKERS)   # in-flight cap (semaphore); must not throttle the
                            # workers below their own count, or they queue on each other
FETCH_TIMEOUT = 30          # seconds per request
FETCH_ATTEMPTS = 6          # retries on 429/5xx/timeouts only (tenacity, full-jitter backoff)
FIREWALL_COOLDOWN = 120     # seconds to sit out after a 403/block signal before retrying
BLOCK_HEADER = "cf-mitigated"   # Cloudflare sets this when it challenged/blocked the request

# ---- enumeration (Stage 3) ------------------------------------------------------------------
WP_PER_PAGE = 100           # WP REST page size (101 -> HTTP 400)
MAX_UNREADABLE_PER_TYPE = 5 # more individually-failing items than this means the TYPE's endpoint
                            # is broken, not its records — stop bisecting and report the type as
                            # UNAVAILABLE rather than minting one false "gap" per item.
BISECT_ATTEMPTS = 2         # retries per bisection probe when cornering an unrenderable item.
                            # The parent range already proved the failure is persistent, so the
                            # full FETCH_ATTEMPTS ladder would burn minutes re-proving it.
SITEMAP_DEPTH_CAP = 5       # nested sitemap-index recursion cap (with cycle detection)
ARCHIVE_MAX_PER_MIN = 55    # public-archive query ceiling (60/min hard; blocks double on repeat)
LIVENESS_ATTEMPTS = 2       # a liveness HEAD asks "does this answer NOW", so the content-fetch
LIVENESS_TIMEOUT = 8        # retry ladder (6 x 30s + backoff) is the wrong shape: it can spend
                            # MINUTES per dead URL proving what one quick probe already showed.
                            # 2 attempts still absorbs a single blip, so a live page is not
                            # mislabelled dead by one hiccup.
LIVENESS_WORKERS = FETCH_CONCURRENCY   # probes run in parallel up to the in-flight cap; the
                            # token bucket still owns the RATE, so this cannot raise req/s above
                            # RATE_RPS — it only stops one slow probe blocking the queue.
CANONICAL_HOP_CAP = 5       # rel=canonical chain cap; beyond -> UNRESOLVED, never guessed
FAN_IN_ALERT = 20           # one canonical target absorbing more aliases than this = flagged bug

# ---- extraction (Stage 4) -------------------------------------------------------------------
EXTRACT_FAIL_CHARS = 250    # below this = failed -> escalate to the next ladder rung
EXTRACT_STUB_CHARS = 400    # 250-400 = genuine stub, recorded as such
FLAG_MEDIAN_FRAC = 0.25     # body < 25% of its type's median -> flagged for review
PRUNE_REVERT_FRAC = 0.60    # DOM pruning removed >60% of text -> revert to unpruned (mandatory)
EXTRACT_TIMEOUT = 20        # wall-clock kill per extractor per page (processes, not threads)
REST_MIN_SHARE = float(os.environ.get("CAT_REST_MIN_SHARE", "0.5"))
                            # the CMS-returned body is accepted outright only if it is at least
                            # this share of the LIVE page's text. Below it the CMS field is a
                            # fragment (page-builder sites often expose only the FAQ block) and
                            # the live-HTML stack is tried instead — the CMS body still competes,
                            # so it wins whenever the extractors do no better.

# ---- traffic (Stage 5) ----------------------------------------------------------------------
DFS_LIMIT = 1000            # ranked_keywords page size (bulk, never per-page: $2.50 vs $35.80)
MIN_CREDITS = float(os.environ.get("DFS_MIN_CREDITS", "1.0"))   # pre-flight credit guard ($)

# ---- gates (Stage 6) ------------------------------------------------------------------------
GATE_OVERALL = 0.95         # run FAILS below 95% extraction coverage overall
GATE_PER_TYPE = 0.90        # run FAILS below 90% for any single page type

# ---- atomic saves (C5: a file's existence must GUARANTEE it is complete) --------------------
def _atomic_write(path, writer):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")     # SAME dir -> the rename is atomic
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            writer(f)
        os.chmod(tmp, 0o644)                              # mkstemp defaults to 0600
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise

def write_json(path, data, indent=2):
    _atomic_write(path, lambda f: json.dump(data, f, indent=indent, ensure_ascii=False))

def write_text(path, text):
    _atomic_write(path, lambda f: f.write(text))

def write_bytes(path, data):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")     # SAME dir -> the rename is atomic
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise

def describe():
    """The resolved run context, printable — used by run_catalogue at startup and by --check."""
    return "\n".join([
        f"company   : {COMPANY}",
        f"record    : {_RECORD_PATH}",
        f"brand     : {BRAND}",
        f"domain    : {DOMAIN}",
        f"wordpress : {WORDPRESS_URL or '(none — not a WordPress site)'}",
        f"market    : {LOCATION} / {LANGUAGE}",
        f"user-agent: {USER_AGENT}",
        f"output    : {OUT}",
        f"work      : {WORK}",
        f"raw cache : {RAW}",
    ])

# A host that has firewalled us this many times IN A ROW is written off for the rest of the run:
# its remaining URLs fail instantly instead of each paying a full cooldown (D17, measured 2026-07-20).
BLOCK_GIVE_UP = int(os.environ.get("CAT_BLOCK_GIVE_UP", "5"))
