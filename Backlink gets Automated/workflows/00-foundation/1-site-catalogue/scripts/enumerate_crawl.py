#!/usr/bin/env python3
"""Layer 4 — internal-link crawl. LAST RESORT: runs only when the other three layers came back
thin (no CMS, no usable sitemap, little archive history), or when CAT_FORCE_CRAWL=1.

Reads:  URLS_WP + URLS_SITEMAP + URLS_ARCHIVE (to decide whether it is needed at all),
        then the live site breadth-first through fetch (rate-limited, cached, robots-obeying).
Writes: URLS_CRAWL (urls-crawl.json):
  { "skipped": null | "<reason>", "urls": { <url>: {"discovered_from": ...} } }

Rules:
- BFS stays on the site's own hosts (apex + www) — this layer walks the SITE, unlike sitemap
  children which may live elsewhere and are followed literally there.
- Caps: CRAWL_MAX_PAGES pages, CRAWL_DEPTH_CAP hops. State saved every 25 pages -> resumable.
- Only http(s) content pages: skips mailto/tel/fragments, obvious binaries by extension.
"""
import json
import os
import urllib.parse as _up

from lxml import html as lxml_html

import config
import fetch

CRAWL_IF_UNDER = 200        # other layers found fewer distinct URLs than this -> crawl kicks in
CRAWL_MAX_PAGES = 5000      # hard page budget
CRAWL_DEPTH_CAP = 6         # hops from the homepage
_SKIP_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".css", ".js",
             ".zip", ".gz", ".mp3", ".mp4", ".webm", ".woff", ".woff2", ".xml", ".json")


def _other_layers_count():
    n = set()
    for path in (config.URLS_WP, config.URLS_SITEMAP, config.URLS_ARCHIVE):
        if os.path.exists(path):
            n |= set(json.load(open(path)).get("urls", {}).keys())
    return len(n)


def _links(base_url, content):
    try:
        doc = lxml_html.fromstring(content)
    except Exception:
        return []
    out = []
    for href in doc.xpath("//a/@href"):
        href = href.strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        u = _up.urljoin(base_url, href)
        parts = _up.urlsplit(u)
        if parts.scheme not in ("http", "https"):
            continue
        if parts.path.lower().endswith(_SKIP_EXT):
            continue
        out.append(_up.urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, "")))
    return out


def run():
    found = _other_layers_count()
    if found >= CRAWL_IF_UNDER and os.environ.get("CAT_FORCE_CRAWL") != "1":
        print(f"   other layers found {found} URLs (>= {CRAWL_IF_UNDER}) — crawl not needed")
        config.write_json(config.URLS_CRAWL,
                          {"skipped": f"other layers found {found} URLs", "urls": {}})
        return

    domain = config.DOMAIN
    state_path = config.URLS_CRAWL + ".state.json"
    if os.path.exists(state_path):
        st = json.load(open(state_path))
        queue, seen, urls = st["queue"], set(st["seen"]), st["urls"]
        print(f"   resuming crawl: {len(urls)} found, {len(queue)} queued")
    else:
        queue, seen, urls = [[f"{config.SCHEME}://{domain}/", 0, "(start)"]], set(), {}

    def save():
        config.write_json(state_path, {"queue": queue, "seen": sorted(seen), "urls": urls})

    fetched = 0
    while queue and len(urls) < CRAWL_MAX_PAGES:
        url, depth, parent = queue.pop(0)
        key = url.rstrip("/")
        if key in seen or depth > CRAWL_DEPTH_CAP:
            continue
        seen.add(key)
        try:
            r = fetch.get(url)
        except (fetch.RobotsDisallowed, fetch.Blocked) as e:
            if isinstance(e, fetch.Blocked):
                save()
                raise
            continue
        if r.status != 200 or "html" not in (r.content_type or "").lower():
            continue
        urls[url] = {"discovered_from": parent}
        fetched += 1
        for link in _links(r.final_url, r.content):
            if config.is_own_host(link) and link.rstrip("/") not in seen:
                queue.append([link, depth + 1, url])
        if fetched % 25 == 0:
            save()
            print(f"   .. {len(urls)} pages, queue {len(queue)}")

    save()
    print(f"   TOTAL: {len(urls)} pages crawled")
    config.write_json(config.URLS_CRAWL, {"skipped": None, "urls": urls})


if __name__ == "__main__":
    run()
