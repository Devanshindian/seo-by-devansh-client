#!/usr/bin/env python3
"""Layer 1 — enumerate every page the site's own CMS (WordPress REST) knows about.

Reads:  config.WORDPRESS_URL (empty = not WordPress -> layer skipped, honestly recorded).
Writes: URLS_WP (urls-wp.json):
  { "skipped": null | "<reason>",
    "types":  { <type>: {"rest_base": ..., "total": N, "collected": N, "unreadable": [pos, ...]} },
    "urls":   { <link>: {"type","title","description","modified","rest_chars","api_page"} } }

Rules (all measured):
- The type list is DERIVED at runtime from /wp-json/wp/v2/types — never typed in (a hardcoded
  list once made 27% of the site invisible; a recovery list missed a whole type).
- Skip any rest_base containing "(" (one core type ships a literal regex as its rest_base) and
  "media" (the platform's file library — attachments, not site pages).
- per_page=100 exactly (101 -> HTTP 400).
- "No more data" is ONLY rest_post_invalid_page_number; any other failure retries in fetch.
- A CMS that cannot render ONE item answers 5xx for the WHOLE batch that item lands in. Retrying
  that batch can never succeed and aborting the type would throw away the healthy items around
  it, so we BISECT the failing item range until the poison is cornered at a single item, which is
  recorded in `unreadable` by position. One unrenderable item costs itself, never its type.
- Pagination is driven by the authoritative X-WP-Total, not by "a short page means the end" —
  after bisection a page IS legitimately short.
- Every type is ASSERTED complete: collected + unreadable == X-WP-Total. Anything else = abort.
- An HTML body where JSON was expected = BLOCKED (loud), never an empty layer.

The rendered bodies stay in fetch's raw cache (the api_page field says which cached API page
holds each URL's content) — extract.py re-reads them OFFLINE; this file stays light.
"""
import json
import sys

import config
import fetch


def _strip_tags(s):
    """Tiny tag-stripper for title/excerpt fields (rendered HTML snippets)."""
    import html as _html
    import re
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", _html.unescape(s)).strip()


class _EndpointBroken(Exception):
    """The TYPE's endpoint is failing, not one record inside it. Bisecting further would just
    manufacture one 'unrenderable item' per item and report a confident lie."""


def _largest_proper_divisor(n):
    """The biggest d < n that divides n — the bisection ladder for a page size (100->50->25->5->1).
    A DIVISOR keeps every sub-page aligned to the parent's item range, so `page` arithmetic stays
    exact; halving an odd size would straddle boundaries and silently re-ask the wrong items."""
    for d in range(n // 2, 0, -1):
        if n % d == 0:
            return d
    return 1


def _result_page(slug, base, api, per_page, page, unreadable, state):
    """One page of a type's results. Returns the items, or None if the type is not publicly
    listable. `state["total"]` is filled from the first X-WP-Total header seen.

    On a PERSISTENT server error (the CMS cannot render some item in this range) the same range is
    re-asked in smaller aligned slices until the bad item is cornered alone and recorded in
    `unreadable`. Measured on a real site: one unrenderable item 5xx'd a 100-item page and would
    otherwise have cost that type's other 150 items — and, before this, the entire run.
    """
    url = (f"{api}/{base}?per_page={per_page}&page={page}"
           f"&_fields=link,type,title,excerpt,content,modified")
    # The parent range already proved this fails persistently; don't re-prove it 6 times per probe.
    attempts = None if per_page == config.WP_PER_PAGE else config.BISECT_ATTEMPTS
    r = fetch.get(url, attempts=attempts)

    if r.status == 400:
        try:
            err = json.loads(r.text).get("code", "")
        except json.JSONDecodeError:
            err = ""
        if err == "rest_post_invalid_page_number":
            return []                              # the one GENUINE end-of-data signal
        sys.exit(f"!! {slug}: unexpected 400 at page {page} (per_page={per_page}): {r.text[:200]}")

    if r.status in (401, 403) and page == 1 and per_page == config.WP_PER_PAGE:
        return None                                # not publicly listable

    # A type can be DECLARED in /types while its collection route is never registered (the plugin
    # exposes single items only, or registers under a route it does not advertise). The CMS says
    # so precisely — trust its own error code, don't infer it from the bare 404.
    if r.status == 404:
        try:
            code = json.loads(r.text).get("code", "")
        except json.JSONDecodeError:
            code = ""
        if code == "rest_no_route":
            if page == 1 and per_page == config.WP_PER_PAGE:
                print(f"   type {slug!r}: declared by the CMS but has no REST collection route "
                      f"({url.split('/wp-json/')[-1].split('?')[0]}) — skipped, nothing to count")
                return None
            sys.exit(f"!! {slug}: route vanished mid-pagination at page {page} — refusing to "
                     f"ship a partial type. URL: {url}")

    if r.status == 200:
        body = r.text.strip()
        if body[:1] != "[":
            raise fetch.Blocked(f"HTML where JSON was expected at {url}")
        state["saw_200"] = True
        if state.get("total") is None and r.headers.get("x-wp-total") is not None:
            state["total"] = int(r.headers["x-wp-total"])
        items = json.loads(body)
        for it in items:
            # the EXACT cached URL this item came from — extract.py re-reads bodies from it
            # offline, so after a bisection it must be the SMALL page, not the failed big one
            it["_api_page"] = url
        return items

    # ---- NOT a server error: we never got an answer. NEVER bisect this ------------------------
    # status 0 means no response reached us (timeout, DNS, connection reset, the laptop changed
    # network). Bisecting would file our own outage as "items the CMS cannot render" — gaps that
    # do not exist, in a shape that SATISFIES the coverage gate. Stop loudly instead.
    if r.status == 0:
        sys.exit(f"!! {slug}: no response from the server at page {page} (per_page={per_page}) — "
                 f"a transport failure, NOT a CMS error: {r.headers.get('_fetch_error', '')}\n"
                 f"   Nothing is recorded as a gap on a network failure. Check connectivity and "
                 f"re-run; finished stages and the raw cache are reused, so this is cheap.")
    if not 500 <= r.status < 600:
        sys.exit(f"!! {slug}: unexpected HTTP {r.status} at page {page} (per_page={per_page}) — "
                 f"aborting rather than guessing. URL: {url}")

    # ---- a persistent SERVER error on this range: bisect rather than lose it ------------------
    state["errors"] = state.get("errors", 0) + 1   # ANY error here forfeits the benign reading
                                                   # of a later shortfall (see run(): a shortfall
                                                   # with errors present is the silent-loss bug)
    start = (page - 1) * per_page                  # 0-based index of this range's first item
    if per_page == 1:
        unreadable.append(start + 1)
        # A poisoned record is rare and isolated. Many of them in one type means the ENDPOINT is
        # broken, so every further probe just mints another false "gap" — stop and say so.
        if len(unreadable) > config.MAX_UNREADABLE_PER_TYPE:
            raise _EndpointBroken(f"{len(unreadable)} items failed individually (HTTP {r.status}) "
                                  f"— the endpoint is failing, not its records")
        print(f"   !! {slug}: item #{start + 1} is unrenderable by the CMS (HTTP {r.status}) — "
              f"recorded as a known gap, not silently lost")
        return []
    d = _largest_proper_divisor(per_page)
    print(f"   .. {slug}: HTTP {r.status} on items {start + 1}-{start + per_page} — "
          f"bisecting at per_page={d}")
    out = []
    for k in range(per_page // d):
        got = _result_page(slug, base, api, d, start // d + k + 1, unreadable, state)
        out += got or []
    return out


def _get_json(url):
    """fetch.get + insist the payload is JSON. HTML here means a challenge page: BLOCKED."""
    r = fetch.get(url)
    body = r.text.strip()
    if r.status == 200 and body[:1] not in ("[", "{"):
        raise fetch.Blocked(f"HTML where JSON was expected at {url} — challenge/anti-bot page, "
                            f"not an empty result")
    return r, (json.loads(body) if body[:1] in ("[", "{") else None)


def run():
    if not config.WORDPRESS_URL:
        print("   no wordpress_url in the company record — layer skipped (not a WordPress site)")
        config.write_json(config.URLS_WP, {"skipped": "no wordpress_url in company record",
                                           "types": {}, "urls": {}})
        return

    root = config.WORDPRESS_URL + "/wp-json"
    core = root + "/wp/v2"                       # the type INDEX always lives in core

    # 1) ask the site what content types it has — never assume
    r, types_doc = _get_json(core + "/types")
    if r.status != 200 or not isinstance(types_doc, dict):
        sys.exit(f"!! /types returned HTTP {r.status} — cannot enumerate a WordPress site "
                 f"without its type list. (Blocked? robots? wrong wordpress_url?)")

    rest_bases = []
    for slug, t in sorted(types_doc.items()):
        base = t.get("rest_base") or slug
        if "(" in base:          # one core type ships a literal regex as its rest_base
            print(f"   skipping type {slug!r}: rest_base contains a regex ({base!r})")
            continue
        if base == "media":      # the platform's file library — attachments, not site pages
            continue
        # A type declares WHICH namespace serves it. Plugins register their own (Web Stories uses
        # web-stories/v1), so assuming wp/v2 asks a route that does not exist and gets a 404 —
        # the same "never reconstruct a reference the parent already gave you literally" rule the
        # sitemap layer learned. Fall back to core only when the type declares nothing.
        ns = t.get("rest_namespace") or "wp/v2"
        rest_bases.append((slug, base, f"{root}/{ns}"))
    nonstandard = sorted({ns for _, _, ns in rest_bases if not ns.endswith("/wp/v2")})
    print(f"   {len(rest_bases)} content types declared by the CMS"
          + (f" ({len(nonstandard)} non-core namespace(s): "
             f"{', '.join(n.rsplit('/wp-json/', 1)[-1] for n in nonstandard)})" if nonstandard else ""))

    # 2) paginate every type; assert X-WP-Total per type
    urls, per_type, unavailable = {}, {}, {}
    for slug, base, api in rest_bases:
        state, unreadable = {"total": None, "saw_200": False}, []
        try:
            items = _result_page(slug, base, api, config.WP_PER_PAGE, 1, unreadable, state)
            if items is None:
                print(f"   type {slug!r}: not publicly listable — skipped")
                continue
            total = state["total"]
            if total is None:
                if not state["saw_200"]:
                    raise _EndpointBroken("every request to this type errored; no X-WP-Total was "
                                          "ever served, so its size is unknowable")
                sys.exit(f"!! {slug}: answered 200 but sent no X-WP-Total header — cannot verify "
                         f"coverage. URL: {api}/{base}?per_page={config.WP_PER_PAGE}&page=1")

            # Drive pagination from the AUTHORITATIVE count, never from "this page looks short" —
            # after a bisection a page is legitimately short, and short must not mean the end.
            for page in range(2, -(-total // config.WP_PER_PAGE) + 1):
                items += _result_page(slug, base, api, config.WP_PER_PAGE, page,
                                      unreadable, state) or []
        except _EndpointBroken as e:
            # Decided with Devansh 2026-07-18: warn and continue with coverage stamped UNKNOWN for
            # this type. We cannot tell a broken endpoint hiding 0 pages from one hiding 5,000 —
            # but the sitemap / archive / traffic layers cross-check the CMS layer independently,
            # which is what the union design is for. Never silent: the report names it.
            print(f"   !! type {slug!r}: endpoint UNAVAILABLE — {e}. Coverage for this type is "
                  f"UNKNOWN (reported, not assumed empty).")
            unavailable[slug] = {"rest_base": base, "reason": str(e)}
            continue

        for it in items:
            link = it.get("link", "")
            if not link:
                continue
            urls[link] = {
                "type": slug,
                "title": _strip_tags((it.get("title") or {}).get("rendered", "")),
                "description": _strip_tags((it.get("excerpt") or {}).get("rendered", "")),
                "modified": it.get("modified", ""),
                "rest_chars": len(((it.get("content") or {}).get("rendered", "")) or ""),
                "api_page": it.get("_api_page", ""),
            }
        collected = len(items)
        withheld = 0
        if collected + len(unreadable) != total:
            # A shortfall is the engine's most dangerous symptom (2,000 of 3,623 pages once went
            # missing this way), so it may only be read benignly under a strict condition: EVERY
            # request for this type answered 200 and nothing errored. Then the server is not
            # failing, it is DECLINING — its count includes records an anonymous client may not
            # read (private/draft/protected items). If anything errored, that reading is void and
            # this is the silent-loss bug: abort.
            if unreadable or state.get("errors"):
                sys.exit(f"!! {slug}: collected {collected} + {len(unreadable)} unreadable != "
                         f"X-WP-Total {total}, with {state.get('errors', 0)} request error(s) — "
                         f"unexplained shortfall; aborting.")
            withheld = total - collected
            print(f"   {slug}: {collected} of {total} — {withheld} counted by the CMS but NOT "
                  f"served to an anonymous client (private/restricted records), every request 200")
        per_type[slug] = {"rest_base": base, "total": total, "collected": collected,
                          "unreadable": unreadable, "withheld": withheld}
        if not withheld:
            note = f" + {len(unreadable)} UNRENDERABLE {unreadable}" if unreadable else ""
            print(f"   {slug}: {collected} (X-WP-Total {total}){note} ok")

    print(f"   TOTAL: {len(urls)} URLs across {len(per_type)} types"
          + (f" ({len(unavailable)} type(s) UNAVAILABLE: {', '.join(sorted(unavailable))})"
             if unavailable else ""))
    config.write_json(config.URLS_WP, {"skipped": None, "types": per_type, "urls": urls,
                                       "unavailable": unavailable})


if __name__ == "__main__":
    run()
