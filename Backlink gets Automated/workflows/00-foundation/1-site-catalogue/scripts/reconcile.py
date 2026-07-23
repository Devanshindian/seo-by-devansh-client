#!/usr/bin/env python3
"""Union + provenance + URL normalisation + canonical collapse + soft-404 detection.

Reads:  urls-wp.json, urls-sitemap.json, urls-archive.json, urls-crawl.json — then the live
        site ONCE per surviving URL (rate-limited, through fetch's cache, resumable via the
        frontier). extract.py later re-parses the same cached HTML offline, fetching nothing.
Writes: RECONCILED (reconciled.json):
  { "pages":   { <stored_url>: {sources, aliases, type, title, description, modified,
                                rest_chars, api_page, status, final_url, canonical_declared,
                                canonical_state, match_key} },
    "dropped": {"dead": [...], "soft_404": [...], "collapsed": {alias: target},
                "offsite": [...], "robots": [...]},
    "fan_in":  { <target>: n_aliases },   # anomalies — flagged, NOT collapsed
    "stats":   {...} }

Rules (each one earned by a measured incident):
- UNION of independent sources; `sources` per URL is kept — the set differences are findings.
- The STORED url is minimally normalised (url-normalize); the MATCH KEY is aggressive
  (tracking-param blocklist, not an allowlist — an allowlist once deleted real permalinks).
  Two fields, never conflated.
- canonical_declared is stored verbatim; the RESOLVED state lives in canonical_state. A
  declaration is a hint, never a directive — overwriting it hides that it was wrong.
- Chains (redirects + canonicals) resolve with a hop cap and a visited-set; a loop or a cap
  is UNRESOLVED, surfaced, never guessed.
- Fan-in: a target absorbing > FAN_IN_ALERT aliases is a bug signature (homepage canonical,
  soft-404 template, staging leak) — flagged and NOT collapsed, so no data is destroyed.
- Soft 404s are detected by CONTENT SIGNATURE (identical small bodies across many URLs,
  not-found phrasing), never by status code.
- A single page answering 403 while the homepage still serves is a PAGE fact (recorded);
  403 with the homepage also refusing is a SITE block (the stage stops loudly).
"""
import hashlib
import json
import os
import re
import sys
import threading
import urllib.parse as _up
from concurrent.futures import ThreadPoolExecutor

from lxml import html as lxml_html
from url_normalize import url_normalize
from w3lib.url import url_query_cleaner

import config
import fetch

# Tracking params dropped from the MATCH KEY only (blocklist — real params like WP's ?p= survive)
# A BLOCKLIST, never an allowlist: an allowlist would discard the query parameters some CMSs use
# for real permalinks. Each entry below identifies a campaign/affiliate/session tag that cannot
# change what page you land on. Measured 2026-07-19 on a competitor's site: without the affiliate
# (`fpr`) and Google/Bing ad (`hsa_*`, `_bta_*`) tags, one homepage entered the catalogue dozens of
# times over and 92% of that site's rows were duplicates.
TRACKING_PARAMS = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                   "utm_id", "utm_source_platform", "utm_creative_format",
                   "gclid", "gclsrc", "gbraid", "wbraid", "dclid",          # Google Ads
                   "fbclid", "igshid", "ttclid", "twclid", "li_fat_id",     # social
                   "msclkid", "hsa_acc", "hsa_cam", "hsa_grp", "hsa_ad",    # Bing / Google ads
                   "hsa_src", "hsa_tgt", "hsa_kw", "hsa_mt", "hsa_net", "hsa_ver",
                   "mc_cid", "mc_eid", "_bta_c", "_bta_tid", "vero_id",     # email platforms
                   "fpr", "irclickid", "aff_id", "affiliate", "partner_id", # affiliate
                   "ref", "source", "srsltid", "gad_source", "campaignid", "adgroupid"]

SOFT404_MIN_CLUSTER = 5      # identical small bodies across at least this many URLs
SOFT404_MAX_WORDS = 150
_NOT_FOUND_RE = re.compile(r"\b(page not found|404|nothing (was )?found|doesn.t exist)\b", re.I)

# Standard non-content / protocol files (not site PAGES): RFC 8615 well-known URIs + root machine files.
_NON_CONTENT_RE = re.compile(
    r"(/\.well-known/|/(robots\.txt|security\.txt|ads\.txt|humans\.txt|favicon\.ico|"
    r"manifest\.json|browserconfig\.xml|sitemap[\w-]*\.xml|sitemap[\w-]*\.xml\.gz)$)", re.I)

# A binary/static asset is never a page, on any platform. Extension-based, so it needs no
# knowledge of the CMS. (.html/.htm/.php/.asp are deliberately ABSENT — those ARE pages.)
_ASSET_EXT_RE = re.compile(
    r"\.(?:png|jpe?g|gif|webp|avif|svg|ico|bmp|tiff?|"           # images
    r"woff2?|ttf|otf|eot|"                                        # fonts
    r"css|js|mjs|cjs|map|"                                        # styling / scripts
    r"mp4|webm|mov|avi|wmv|mp3|wav|ogg|m4a|"                      # media
    r"zip|gz|tgz|tar|rar|7z|dmg|exe|pkg)$", re.I)                 # archives / installers

# A CMS's API surface and internal directories are MACHINERY, not pages. This is platform-shape
# awareness (the same kind enumerate_sitemap's probe list already uses), never company knowledge:
# no domain, brand or slug appears here, and it holds for every site on these platforms.
# Measured 2026-07-19: 164 /wp-json/ endpoints and 12 /wp-content/ assets entered the catalogue
# via the archive layer and failed the coverage gate with 0% bodies — correctly, they are not pages.
_MACHINE_PATH_RE = re.compile(
    r"^/(?:wp-json|wp-admin|wp-includes|wp-content|xmlrpc\.php|"   # WordPress
    r"_next/static|_nuxt|_vercel|cdn-cgi|"                         # Next.js / Nuxt / Cloudflare
    r"ghost/api|admin/api|api/v\d+|graphql)(?:/|$)", re.I)         # Ghost / generic API roots


def _is_non_content(url):
    """True when the URL addresses machinery or a static asset rather than a PAGE."""
    path = _up.urlsplit(url).path
    return bool(_NON_CONTENT_RE.search(path) or _ASSET_EXT_RE.search(path)
                or _MACHINE_PATH_RE.match(path))


def _store_norm(u):
    """The STORED form: safe RFC-3986 normalisation + fragment stripped. Faithful."""
    try:
        u = url_normalize(u.strip())
    except Exception:
        return u.strip()
    return u.split("#", 1)[0]


def _match_key(u):
    """The aggressive GROUPING key — never stored as the record's URL."""
    u = url_query_cleaner(u, parameterlist=TRACKING_PARAMS, remove=True)
    parts = _up.urlsplit(u)
    host = (parts.hostname or "").lower()
    host = host[4:] if host.startswith("www.") else host
    path = parts.path.rstrip("/") or "/"
    # RFC 3986 §6.2.2.1: percent-encoding hex digits are CASE-INSENSITIVE and uppercase is the
    # canonical form. A sitemap may declare /%e3%83%96... where the site serves /%E3%83%96... —
    # the same page. Measured 2026-07-19: 7 non-Latin URLs (Japanese, Arabic, Chinese) were in
    # the catalogue AND reported as lost, purely because the two spellings keyed differently.
    path = re.sub(r"%([0-9a-fA-F]{2})", lambda m: "%" + m.group(1).upper(), path)
    return _up.urlunsplit(("https", host, path, parts.query, ""))


def _head_canonical(doc):
    """rel=canonical honoured the way a browser does: only from inside a real <head>."""
    for el in doc.xpath("//link[@rel]"):
        rels = (el.get("rel") or "").lower().split()
        if "canonical" not in rels:
            continue
        anc = [a.tag for a in el.iterancestors()]
        if "head" in anc:
            return (el.get("href") or "").strip()
    return ""


def _link_header_canonical(headers):
    for part in (headers.get("link", "") or "").split(","):
        if 'rel="canonical"' in part.lower() or "rel=canonical" in part.lower():
            m = re.search(r"<([^>]+)>", part)
            if m:
                return m.group(1).strip()
    return ""


def _load(path):
    return json.load(open(path)) if os.path.exists(path) else {"urls": {}}


def run():
    layers = {
        "wp": _load(config.URLS_WP), "sitemap": _load(config.URLS_SITEMAP),
        "archive": _load(config.URLS_ARCHIVE), "crawl": _load(config.URLS_CRAWL),
    }

    # 1) union with provenance, grouped by the match key ---------------------------------------
    groups = {}                                     # match_key -> record
    PREFER = {"wp": 0, "sitemap": 1, "archive": 2, "crawl": 3}
    for src in ("wp", "sitemap", "archive", "crawl"):
        for raw, meta in layers[src].get("urls", {}).items():
            stored = _store_norm(raw)
            key = _match_key(stored)
            rec = groups.setdefault(key, {
                "url": stored, "url_src": src, "sources": set(), "aliases": set(),
                "type": "", "title": "", "description": "", "modified": "",
                "rest_chars": 0, "api_page": "", "match_key": key,
            })
            rec["sources"].add(src)
            if stored != rec["url"]:
                # keep ONE stored form; prefer the CMS's own permalink over later layers' forms
                if PREFER[src] < PREFER[rec["url_src"]]:
                    rec["aliases"].add(rec["url"])
                    rec["url"], rec["url_src"] = stored, src
                else:
                    rec["aliases"].add(stored)
            if src == "wp":
                rec.update(type=meta.get("type", ""), title=meta.get("title", ""),
                           description=meta.get("description", ""),
                           modified=meta.get("modified", ""),
                           rest_chars=meta.get("rest_chars", 0),
                           api_page=meta.get("api_page", ""))
            elif src == "sitemap" and not rec["modified"]:
                rec["modified"] = meta.get("lastmod", "")

    pages = {rec["url"]: rec for rec in groups.values()}

    # drop standard non-content / protocol files — they are NOT site pages and must never become a
    # spurious page "type" (a single /.well-known/security.txt once failed the whole run's per-type
    # gate). RFC 8615 well-known URIs + the handful of root machine files. Company-agnostic.
    non_content = [u for u in pages if _is_non_content(u)]
    for u in non_content:
        del pages[u]
    if non_content:
        print(f"   dropped {len(non_content)} non-content/protocol file(s) (e.g. {non_content[0]})")

    stats = {"union": len(pages)}
    for src in layers:
        stats[src] = sum(1 for r in pages.values() if src in r["sources"])
    stats["wp_only"] = sum(1 for r in pages.values() if r["sources"] == {"wp"})
    stats["sitemap_only"] = sum(1 for r in pages.values() if r["sources"] == {"sitemap"})
    stats["archive_only"] = sum(1 for r in pages.values() if r["sources"] == {"archive"})
    print(f"   union: {stats['union']} pages "
          f"(wp {stats['wp']}, sitemap {stats['sitemap']}, archive {stats['archive']}, "
          f"crawl {stats['crawl']}; wp-only {stats['wp_only']}, "
          f"sitemap-only {stats['sitemap_only']}, archive-only {stats['archive_only']})")

    # 2) the network pass — make sure every page is in the raw cache (resumable) ---------------
    fetch.frontier_add(sorted(pages.keys()))
    done_states = fetch.frontier_counts()
    print(f"   frontier: {done_states}")
    CIRCUIT_BREAK = int(os.environ.get("CAT_CIRCUIT_BREAK", "40"))
    _n0 = fetch.frontier_counts()
    shared = {"fail_streak": 0, "done": _n0.get("done", 0) + _n0.get("failed", 0), "exc": None}
    guard = threading.Lock()                   # guards `shared` only; fetch owns its own locking

    def _fatal(exc):
        """First fatal error wins; the other workers see it and drain out rather than pile on."""
        with guard:
            if shared["exc"] is None:
                shared["exc"] = exc

    def _fetch_worker():
        while shared["exc"] is None:
            url = fetch.frontier_claim()       # atomic claim — the frontier was built for this
            if url is None:
                return                         # queue drained
            try:
                r = fetch.get(url)
                # a genuinely broken / unfetchable single page — record it and move on; one bad
                # URL never ends the run. body_status becomes failed downstream.
                failed = r.status == 0 or r.status >= 500
                (fetch.frontier_fail(url, f"fetch failed (HTTP {r.status})") if failed
                 else fetch.frontier_done(url))
            except fetch.RobotsDisallowed:
                fetch.frontier_fail(url, "robots")
                failed = False                 # robots is a policy skip, not a health signal
            except fetch.Blocked as e:
                # page-level 403 or site-wide block? The homepage decides.
                try:
                    site_ok = fetch.get(f"{config.SCHEME}://{config.DOMAIN}/",
                                        force=True).status == 200
                except Exception:
                    site_ok = False
                if not site_ok:
                    _fatal(fetch.Blocked(f"site-wide block while fetching {url}: {e}"))
                    return
                fetch.frontier_fail(url, "403 (page-level)")
                failed = False
            except Exception as e:             # a worker must never die quietly
                _fatal(e)
                return

            with guard:
                # "in a row" across workers: any success clears the streak, so this still means
                # "a WAVE of failures", never an accumulation of scattered bad pages.
                shared["fail_streak"] = shared["fail_streak"] + 1 if failed else 0
                shared["done"] += 1
                if shared["done"] % 100 == 0:
                    print(f"   .. fetched {shared['done']}/{len(pages)}")
                if shared["fail_streak"] >= CIRCUIT_BREAK:
                    _fatal(RuntimeError(
                        f"circuit breaker: {shared['fail_streak']} pages failed to fetch in a row "
                        f"— the site is likely down or throttling us. Stopping loudly (resume "
                        f"later; progress is saved)."))
                    return

    n_workers = max(1, config.FETCH_WORKERS)
    print(f"   fetching with {n_workers} worker(s) at <= {config.RATE_RPS} req/s")
    if n_workers == 1:
        _fetch_worker()
    else:
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            for f in [ex.submit(_fetch_worker) for _ in range(n_workers)]:
                f.result()
    if shared["exc"]:
        raise shared["exc"]                    # a block / breaker stops the run LOUDLY, as before

    # 3) offline parse of the cached payloads --------------------------------------------------
    dropped = {"dead": [], "soft_404": [], "collapsed": {}, "offsite": [], "robots": [],
               "non_content": non_content}
    body_sig = {}                                   # sha -> [urls] for soft-404 clustering
    frontier_state = {u: s for u, s in _frontier_states().items()}

    for url, rec in list(pages.items()):
        if frontier_state.get(url) == "failed":
            err = _frontier_error(url)
            if err == "robots":
                dropped["robots"].append(url)
                del pages[url]
                continue
            # keep the page (it exists) but record it couldn't be read this run; honest status
            rec.update(status=(403 if "403" in err else 0), final_url=url,
                       canonical_declared="", text_words=0)
            continue
        r = fetch.get(url)                          # cache — zero network
        rec["status"] = r.status
        rec["final_url"] = r.final_url
        rec["canonical_declared"] = ""
        rec["text_words"] = 0
        if r.status in (404, 410):
            dropped["dead"].append(url)
            del pages[url]
            continue
        if not config.is_own_host(r.final_url):
            dropped["offsite"].append(url)
            del pages[url]
            continue
        if r.status == 200 and "html" in (r.content_type or "").lower() and r.content:
            try:
                doc = lxml_html.fromstring(r.content)
            except Exception:
                continue
            canon = _head_canonical(doc) or _link_header_canonical(r.headers)
            if canon:
                rec["canonical_declared"] = _store_norm(_up.urljoin(r.final_url, canon))
            text = " ".join(doc.text_content().split())
            rec["text_words"] = len(text.split())
            if not rec["title"]:
                t = doc.xpath("//title/text()")
                rec["title"] = t[0].strip() if t else ""
            # Signature EVERY page, not just small ones. Byte-identical bodies are a fact, and
            # what they mean depends only on size (see step 4).
            sha = hashlib.sha256(text.encode()).hexdigest()
            body_sig.setdefault(sha, []).append(url)

    # 4) identical bodies: the same text served at many URLs -----------------------------------
    # Two different findings share one signal, separated by SIZE:
    #   small  + repeated -> a soft 404 / empty template. Drop them; they are not pages.
    #   large  + repeated -> ONE real page reachable at many addresses (tracking-parameter
    #                        variants, a redirect target, a paginated alias). Keep ONE and record
    #                        the rest as ALIASES — never N copies of the same article.
    # Measured 2026-07-19: the >=150-word cap meant only the first case was ever caught, so a
    # homepage appeared as 143 separate rows on one site, and 5,878 of 6,363 rows (92%) on another
    # were duplicates. Repetition is evidence, and it does not stop being evidence at 150 words.
    for sha, cluster in body_sig.items():
        live = [u for u in cluster if u in pages]
        if len(live) < 2:
            continue
        words = pages[live[0]].get("text_words", 0)
        phrased = any(_NOT_FOUND_RE.search(pages[u].get("title", "")) for u in live)
        if words <= SOFT404_MAX_WORDS and (len(live) >= SOFT404_MIN_CLUSTER or phrased):
            for u in live:                                  # small + repeated = not a page at all
                dropped["soft_404"].append(u)
                del pages[u]
            continue
        if words > SOFT404_MAX_WORDS:
            # Keep the best address for the content: the shortest URL with no query string wins
            # (that is the canonical-looking one), ties broken alphabetically for determinism.
            keeper = sorted(live, key=lambda u: (bool(_up.urlsplit(u).query), len(u), u))[0]
            for u in live:
                if u == keeper:
                    continue
                pages[keeper].setdefault("aliases", set()).add(u)   # aliases is a set here
                dropped["collapsed"][u] = keeper
                del pages[u]

    # 5) canonical + redirect collapse (hop cap, loops -> UNRESOLVED, fan-in flagged) ----------
    def next_hop(u):
        rec = pages.get(u)
        if not rec:
            return None
        fin = _store_norm(rec.get("final_url") or u)
        if fin != u and _match_key(fin) != rec["match_key"] and fin in pages:
            return fin                              # a real redirect to another catalogued page
        canon = rec.get("canonical_declared") or ""
        if canon and _match_key(canon) != rec["match_key"] and canon in pages:
            return canon
        return None

    fan_in = {}
    for url in list(pages.keys()):
        if url not in pages:
            continue
        seen, cur = [url], url
        while True:
            nxt = next_hop(cur)
            if nxt is None:
                target = cur
                break
            if nxt in seen or len(seen) > config.CANONICAL_HOP_CAP:
                target = None                       # loop or cap — UNRESOLVED
                break
            seen.append(nxt)
            cur = nxt
        if target is None:
            pages[url]["canonical_state"] = "unresolved"
        elif target == url:
            pages[url]["canonical_state"] = "self"
        else:
            fan_in[target] = fan_in.get(target, 0) + 1
            pages[url]["canonical_state"] = f"alias_of:{target}"

    flagged = {t: n for t, n in fan_in.items() if n > config.FAN_IN_ALERT}
    for url, rec in list(pages.items()):
        st = rec.get("canonical_state", "self")
        if st.startswith("alias_of:"):
            target = st.split(":", 1)[1]
            if target in flagged:
                rec["canonical_state"] = f"fan_in_suspect:{target}"   # flagged, NOT collapsed
                continue
            tgt = pages.get(target)
            if tgt:
                tgt["aliases"] = sorted(set(tgt["aliases"]) | {url} | set(rec["aliases"]))
                tgt["sources"] = sorted(set(tgt["sources"]) | set(rec["sources"]))
                for f in ("type", "title", "description", "modified", "api_page"):
                    if not tgt.get(f):
                        tgt[f] = rec.get(f, "")
                if not tgt.get("rest_chars"):
                    tgt["rest_chars"] = rec.get("rest_chars", 0)
                dropped["collapsed"][url] = target
                del pages[url]

    # 6) type inference for non-CMS pages: majority type per first path segment ----------------
    seg_type = {}
    for url, rec in pages.items():
        if rec.get("type"):
            seg = _up.urlsplit(url).path.strip("/").split("/", 1)[0]
            seg_type.setdefault(seg, {}).setdefault(rec["type"], 0)
            seg_type[seg][rec["type"]] += 1
    for url, rec in pages.items():
        if not rec.get("type"):
            seg = _up.urlsplit(url).path.strip("/").split("/", 1)[0]
            votes = seg_type.get(seg)
            if votes:
                rec["type"] = max(votes, key=votes.get)
            else:
                rec["type"] = seg if seg and "/" in _up.urlsplit(url).path.strip("/") else "pages"

    for rec in pages.values():                       # json-serialisable
        rec["sources"] = sorted(rec["sources"])
        rec["aliases"] = sorted(rec["aliases"])
        rec.setdefault("canonical_state", "self")
        rec.pop("url_src", None)

    stats.update(final=len(pages), dead=len(dropped["dead"]), soft_404=len(dropped["soft_404"]),
                 collapsed=len(dropped["collapsed"]), offsite=len(dropped["offsite"]),
                 robots=len(dropped["robots"]), fan_in_flagged=len(flagged))
    print(f"   final: {stats['final']} pages | dead {stats['dead']}, soft-404 {stats['soft_404']}, "
          f"collapsed {stats['collapsed']}, offsite {stats['offsite']}, "
          f"fan-in flags {stats['fan_in_flagged']}")
    config.write_json(config.RECONCILED, {
        "pages": {u: pages[u] for u in sorted(pages)},
        "dropped": dropped, "fan_in": flagged, "stats": stats,
    })


def _frontier_states():
    with fetch._db_lock:
        rows = fetch._conn().execute("SELECT url, state FROM frontier").fetchall()
    return dict(rows)


def _frontier_error(url):
    with fetch._db_lock:
        row = fetch._conn().execute("SELECT error FROM frontier WHERE url=?", (url,)).fetchone()
    return (row[0] or "") if row else ""


if __name__ == "__main__":
    run()
