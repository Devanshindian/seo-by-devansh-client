#!/usr/bin/env python3
"""Step B — pull each approved competitor's pages, ranked by the links that actually pass authority.

Replaces the recipe's Semrush step ("this runs in Semrush on the user's login — the agent can't",
L175-176) with one API call per competitor. Resumable per competitor: a crash or a credit stop never
re-pays for a competitor already fetched.

RANKING (Devansh's call, 2026-07-20): we sort by FOLLOW referring domains, not the raw total. Measured
on testgorilla.com: 17 of the top 100 pages are >40% nofollow and four are ~100% nofollow — including
what looked like the #2 link magnet (343 domains, 340 of them nofollow). Nofollow passes no authority,
and routing authority to money pages is the entire point of the reverse-silo. Both numbers are kept.

Reads:  output/competitors.md (the APPROVED list — the gate's output)
Writes: _raw/<domain>-pages.json  (one file per competitor, cached)
        _work/pages-summary.json  (what was pulled, per competitor)

  COMPANY=<slug> python3 step_b_pages.py [--redo] [--only a.com,b.com]
"""
import argparse, json, os, re, sys
import config as c
sys.path.insert(0, c.SHARED)
import dfs

ENDPOINT = "/v3/backlinks/domain_pages/live"


def approved():
    """The competitors the human approved — parsed from the gate's own file, so editing
    competitors.md by hand IS the way to change the run (no second source of truth)."""
    path = os.path.join(c.OUT, "competitors.md")
    if not os.path.exists(path):
        sys.exit(f"!! no {c.rel(path)} — run step_a_competitors.py first, then approve it")
    out = []
    for line in open(path):
        m = re.match(r"^- \*\*([a-z0-9][a-z0-9.\-]*\.[a-z]{2,})\*\*", line.strip(), re.I)
        if m:
            out.append(m.group(1).lower())
    if not out:
        sys.exit(f"!! no competitors found in {c.rel(path)} — expected lines like '- **domain.com** — why'")
    return sorted(set(out))


def pull(domain, redo=False):
    path = os.path.join(c.RAW, f"{domain}-pages.json")
    if os.path.exists(path) and not redo:
        return json.load(open(path)), True
    r = dfs.call(ENDPOINT, [{"target": domain, "limit": c.PAGES_PER_COMPETITOR,
                             "order_by": ["page_summary.referring_domains,desc"]}])
    items = dfs.first_result(r).get("items") or []
    dfs.assert_shape(ENDPOINT, items, c.PAGE_FIELDS)
    rows = []
    for it in items:
        ps = it.get("page_summary") or {}
        meta = it.get("meta") or {}
        rd = ps.get("referring_domains") or 0
        nf = ps.get("referring_domains_nofollow") or 0
        rows.append({
            "competitor": domain,
            "url": it.get("page"),                      # `page`, NOT `url` — the 2026-07-20 lesson
            "status_code": it.get("status_code"),
            "domains_total": rd,
            "domains_nofollow": nf,
            "domains_follow": max(rd - nf, 0),          # THE ranking metric
            "backlinks": ps.get("backlinks") or 0,
            "rank": ps.get("rank"),
            "spam_score": ps.get("backlinks_spam_score"),
            "first_seen": ps.get("first_seen"),         # page age -> "stale?" for Beatability
            "title": meta.get("title") or "",
            "words": meta.get("words_count") or 0,      # thin? -> Beatability, and skip junk fetches
            "images": meta.get("images_count") or 0,    # format signal: infographic / visual asset
            "ext_links": meta.get("external_links_count") or 0,   # format signal: resource list
            "h1": (meta.get("h1") or [])[:3],
            "h2": (meta.get("h2") or [])[:12],          # format signal: what the page actually is
        })
    key = "domains_follow" if c.RANK_ON_FOLLOW else "domains_total"
    rows.sort(key=lambda x: -x[key])
    c.write_json(path, rows)
    return rows, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true", help="re-pay for competitors already pulled")
    ap.add_argument("--only", default="", help="just these domains, comma-separated")
    a = ap.parse_args()
    os.environ.setdefault("DFS_COST_LOG", c.COST_LOG)
    dfs.COST_LOG = c.COST_LOG

    comps = approved()
    if a.only:
        want = {x.strip().lower() for x in a.only.split(",")}
        comps = [x for x in comps if x in want]
    todo = [x for x in comps if a.redo or not os.path.exists(os.path.join(c.RAW, f"{x}-pages.json"))]
    est = len(todo) * 0.035
    print(f"company: {c.COMPANY} ({c.BRAND})")
    print(f"   {len(comps)} approved competitors · {len(todo)} to pull · estimated ${est:.2f}")
    if todo:
        dfs.preflight(need=est)

    opening = dfs.balance()          # ONE read at the start
    summary = []
    for i, d in enumerate(comps, 1):
        rows, cached = pull(d, a.redo)
        nf_heavy = sum(1 for r in rows if r["domains_total"] > 20
                       and r["domains_nofollow"] / max(r["domains_total"], 1) > 0.4)
        top = rows[0] if rows else {}
        summary.append({"competitor": d, "pages": len(rows), "cached": cached,
                        "top_follow_domains": top.get("domains_follow", 0),
                        "nofollow_heavy_pages": nf_heavy})
        print(f"   [{i:>2}/{len(comps)}] {d:26s} {len(rows):>4} pages · "
              f"top {top.get('domains_follow',0):>4} follow-domains · {nf_heavy} nofollow-heavy")

    c.write_json(os.path.join(c.WORK, "pages-summary.json"), summary)
    dfs.spend(f"step B — {len([s for s in summary if not s['cached']])} competitors pulled",
              opening, dfs.balance())          # ONE read at the end
    empty = [s["competitor"] for s in summary if s["pages"] == 0]
    print(f"   {sum(s['pages'] for s in summary)} pages total")
    if empty:
        print(f"   !! {len(empty)} competitors returned NO backlink data: {', '.join(empty)}")
    print(f"   -> {c.rel(c.RAW)}/<domain>-pages.json")


if __name__ == "__main__":
    main()
