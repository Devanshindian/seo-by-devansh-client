#!/usr/bin/env python3
"""Layer 2 — every URL the site's sitemaps declare.

Reads:  robots.txt Sitemap: lines (ALL of them — some sites publish 8), then a platform-aware
        probe list (WordPress core + SEO plugins, Shopify, Webflow, Ghost, Squarespace, HubSpot,
        Wix, Next.js, Drupal, Craft, BigCommerce, Framer, Duda, Magento — techniques
        reimplemented, no GPL dependency).
Writes: URLS_SITEMAP (urls-sitemap.json):
  { "urls": { <loc>: {"lastmod": ..., "sitemap": <which sitemap listed it>} },
    "sitemaps_parsed": [...], "blocked": [...], "not_sitemaps": [...] }

Rules (all measured or spec'd):
- Branch on what the DOCUMENT declares (root element sitemapindex vs urlset), never the filename.
- Follow <loc> literally — NEVER reconstruct child URLs, NEVER same-host-filter children
  (Webflow's children live on a different host).
- Gzip by MAGIC NUMBER, not filename (either can lie).
- Refuse XML that declares entities (billion-laughs) — and HTML pretending to be a sitemap.
- Nested indexes: depth cap + cycle detection INCLUDING through redirects.
- A DECLARED sitemap answering with HTML = BLOCKED, logged loudly. A speculative PROBE answering
  HTML just isn't a sitemap (SPA catch-alls answer 200 to everything) — recorded, not fatal.
- Platforms serve identical sitemaps at several URLs, often via redirects — dedupe on our side.
"""
import gzip
import sys
import urllib.parse as _up

from lxml import etree

import config
import fetch

# The probe list — union of where real platforms put sitemaps (checked only if robots.txt's own
# Sitemap: lines don't already cover the site).
PROBE_PATHS = [
    "/sitemap.xml",            # near-universal default (Shopify, Webflow, Squarespace, HubSpot,
                               #   Wix, Ghost, Next.js, Drupal, Craft, Framer, Duda, Magento)
    "/sitemap_index.xml",      # WordPress: Yoast + Rank Math
    "/wp-sitemap.xml",         # WordPress core (5.5+)
    "/sitemap-index.xml",      # SEOPress and others
    "/sitemapindex.xml",
    "/sitemap1.xml",           # Blogger-style numbered
    "/sitemap-1.xml",
    "/post-sitemap.xml",       # Yoast children, when the index itself is hidden
    "/page-sitemap.xml",
    "/pages-sitemap.xml",
    "/sitemap/sitemap.xml",
    "/sitemap/index.xml",
    "/sitemap.xml.gz",
    "/xmlsitemap.php",         # BigCommerce
    "/media/sitemap.xml",      # Magento variant
    "/sitemaps.xml",
    "/sitemap.txt",            # the protocol's plain-text form
]

GZIP_MAGIC = b"\x1f\x8b"


def _decode(content):
    """Gzip by magic number (double-encoded and mislabelled files both land here correctly)."""
    if content[:2] == GZIP_MAGIC:
        content = gzip.decompress(content)
    return content


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower() if isinstance(tag, str) else ""


def _classify(content):
    """What IS this document? -> ('index'|'urlset'|'txt'|'html'|'bad', parsed-or-None)"""
    body = _decode(content)
    head = body[:4096].lstrip()
    if head[:1] != b"<":
        # maybe a plain-text sitemap: lines of URLs
        lines = [ln.strip() for ln in body.decode("utf-8", "ignore").splitlines() if ln.strip()]
        if lines and all(ln.startswith(("http://", "https://")) for ln in lines[:20]):
            return "txt", lines
        return "bad", None
    lowered = head[:2048].lower()
    if b"<!entity" in lowered or (b"<!doctype" in lowered and b"<!doctype html" not in lowered):
        return "bad", None               # entity-declaring XML — refuse (attack surface)
    try:
        root = etree.fromstring(body, etree.XMLParser(resolve_entities=False, no_network=True,
                                                      recover=False, huge_tree=True))
    except etree.XMLSyntaxError:
        return ("html", None) if b"<html" in lowered or b"<!doctype html" in lowered else ("bad", None)
    name = _local(root.tag)
    if name == "sitemapindex":
        return "index", root
    if name == "urlset":
        return "urlset", root
    if name == "html":
        return "html", None
    return "bad", None


def _looks_like_sitemap(loc):
    """Does this <loc> point at a nested SITEMAP rather than a content page? Judge by the target,
    not the wrapper tag. (Real case: TestGorilla wraps its sitemap INDEX in <urlset>/<url> instead
    of <sitemapindex>/<sitemap>, so a spec-literal parse mistakes 12 child sitemaps for 12 pages.)"""
    path = _up.urlsplit(loc).path.lower()
    return path.endswith(".xml") or path.endswith(".xml.gz")


def _locs(root, child_name):
    """<loc> values under <sitemap>/<url> children, taken literally, plus lastmod."""
    out = []
    for el in root:
        if _local(el.tag) != child_name:
            continue
        loc, lastmod = None, ""
        for sub in el:
            if _local(sub.tag) == "loc":
                loc = (sub.text or "").strip()
            elif _local(sub.tag) == "lastmod":
                lastmod = (sub.text or "").strip()
        if loc:
            out.append((loc, lastmod))
    return out


def run():
    domain = config.DOMAIN
    declared = fetch.sitemaps_from_robots(domain)
    print(f"   robots.txt declares {len(declared)} sitemap(s)")

    urls, parsed_ok, blocked, not_sitemaps = {}, [], [], []
    seen = set()                          # cycle detection: requested AND final URLs

    def walk(sm_url, depth, is_declared):
        key = sm_url.rstrip("/")
        if key in seen:
            return
        seen.add(key)
        if depth > config.SITEMAP_DEPTH_CAP:
            print(f"   !! depth cap {config.SITEMAP_DEPTH_CAP} hit at {sm_url} — not descending")
            return
        try:
            r = fetch.get(sm_url)
        except fetch.RobotsDisallowed:
            blocked.append({"sitemap": sm_url, "why": "robots disallows it"})
            return
        seen.add(r.final_url.rstrip("/"))          # cycles THROUGH redirects
        if r.status != 200:
            (blocked if is_declared else not_sitemaps).append(
                {"sitemap": sm_url, "why": f"HTTP {r.status}"})
            return
        kind, payload = _classify(r.content)
        if kind == "index":
            children = _locs(payload, "sitemap")
            print(f"   index {sm_url} -> {len(children)} child sitemap(s)")
            parsed_ok.append(sm_url)
            for loc, _ in children:
                walk(loc, depth + 1, is_declared=True)   # declared BY the index — must exist
        elif kind == "urlset":
            entries = _locs(payload, "url")
            parsed_ok.append(sm_url)
            nested = sum(1 for loc, _ in entries if _looks_like_sitemap(loc))
            if nested:
                print(f"   urlset {sm_url}: {nested}/{len(entries)} <url> entries point to nested "
                      f"sitemaps (mislabeled index) — recursing into those")
            for loc, lastmod in entries:
                if _looks_like_sitemap(loc):
                    walk(loc, depth + 1, is_declared=True)   # a <url> that is really a sitemap
                elif loc not in urls:
                    urls[loc] = {"lastmod": lastmod, "sitemap": sm_url}
        elif kind == "txt":
            parsed_ok.append(sm_url)
            for loc in payload:
                if loc not in urls:
                    urls[loc] = {"lastmod": "", "sitemap": sm_url}
        elif kind == "html":
            if is_declared:
                blocked.append({"sitemap": sm_url,
                                "why": "HTML where XML was expected — challenge/anti-bot page"})
                print(f"   !! BLOCKED: {sm_url} answered HTML where XML was expected", file=sys.stderr)
            else:
                not_sitemaps.append({"sitemap": sm_url, "why": "HTML (SPA catch-all, not a sitemap)"})
        else:
            (blocked if is_declared else not_sitemaps).append(
                {"sitemap": sm_url, "why": "unparseable / entity-declaring XML"})

    for sm in declared:
        walk(sm, 0, is_declared=True)
    if not urls:
        print("   robots.txt yielded nothing usable — probing the platform paths")
    for path in PROBE_PATHS:
        walk(f"{config.SCHEME}://{domain}{path}", 0, is_declared=False)

    if not urls and blocked:
        sys.exit(f"!! every sitemap source is BLOCKED ({len(blocked)}) — this layer is not "
                 f"'empty', it is being refused. Fix access before trusting any catalogue.")

    print(f"   TOTAL: {len(urls)} URLs from {len(parsed_ok)} sitemap file(s); "
          f"{len(blocked)} blocked, {len(not_sitemaps)} probes weren't sitemaps")
    config.write_json(config.URLS_SITEMAP, {
        "urls": urls, "sitemaps_parsed": parsed_ok,
        "blocked": blocked, "not_sitemaps": not_sitemaps,
    })


if __name__ == "__main__":
    run()
