#!/usr/bin/env python3
"""Step 1b — RANKED net (replaces the wide net). Pulls the keywords that WINNING pages already rank for.
URL source (2026-08-04 revision, decided with Devansh):
  HUBS  — the vetted competitor proof-URLs ONLY (<run_dir>/proof/00-competitor-urls.txt), capped at
          config.RANKED_URL_CAP. The old second source (SERP the head seed, take its top organic pages)
          was dropped for hubs: the head seed is a guess at this point, so its SERP could aim the net at
          the wrong pages — the vetted competitor list is the better source.
  SPOKES — SERP-derived links from the given seed, as before: a spoke has no clubbed competitor URLs,
          so the SERP is its only source.
For each URL, ranked_keywords returns EVERY keyword that page ranks for (any position, capped by config.RANKED_PER_URL).
Then merges the ranked-net into <run_dir>/proof/01-pool.json (which s1_expand.py wrote with the tight net).
Usage: python3 s1b_ranked.py <run_dir> "<serp seed>"
"""
import os, sys, json
from urllib.parse import urlparse
import dfs, config

BASE = {"location_name": config.LOCATION, "language_code": config.LANGUAGE}

def rk_for_url(u):
    p = urlparse(u); dom = p.netloc.replace("www.", ""); seg = p.path.rstrip("/").split("/")[-1]
    if not dom or not seg: return []
    resp = dfs.call("/v3/dataforseo_labs/google/ranked_keywords/live", [{
        **BASE, "target": dom, "limit": config.RANKED_PER_URL,
        "order_by": ["keyword_data.keyword_info.search_volume,desc"],
        "filters": [["ranked_serp_element.serp_item.relative_url", "like", "%" + seg + "%"]]}])
    out = []
    for it in dfs.first_result(resp).get("items") or []:
        kd = it.get("keyword_data", {}) or {}; ki = kd.get("keyword_info", {}) or {}; kp = kd.get("keyword_properties", {}) or {}
        if kd.get("keyword"):
            out.append({"kw": kd.get("keyword"), "vol": ki.get("search_volume") or 0,
                        "kd": kp.get("keyword_difficulty"), "comp": ki.get("competition_level"), "src": "ranked"})
    return out

def main():
    run, seed = sys.argv[1], sys.argv[2]
    proof = os.path.join(run, "proof"); os.makedirs(proof, exist_ok=True)

    comp_file = os.path.join(proof, "00-competitor-urls.txt")
    competitor_urls = [l.strip() for l in open(comp_file)] if os.path.exists(comp_file) else []
    competitor_urls = [u for u in competitor_urls if u and not u.startswith("#")]

    if competitor_urls:
        # HUB: vetted competitor pages only, capped — no seed-SERP guessing.
        urls = list(dict.fromkeys(competitor_urls))[:config.RANKED_URL_CAP]
        serp_urls = []
        print(f"  hub mode: top {len(urls)} competitor URLs (of {len(competitor_urls)}), no seed-SERP")
    else:
        # SPOKE: no clubbed competitor URLs exist — the seed's SERP is the only source.
        serp = dfs.call("/v3/serp/google/organic/live/advanced", [{**BASE, "keyword": seed, "depth": 10}])
        serp_urls = [i.get("url") for i in (dfs.first_result(serp).get("items") or [])
                     if i.get("type") == "organic"][:config.RANKED_SERP_LINKS]
        urls = list(dict.fromkeys(serp_urls))
        print(f"  spoke mode: {len(urls)} SERP-derived URLs for seed {seed!r}")
    ranked = {}
    failures = []
    for u in urls:
        try:
            items = rk_for_url(u)
            for r in items:
                ranked[r["kw"]] = r
            print(f"  {u[:58]:<58} -> {len(items)} kws")
        except Exception as e:
            failures.append({"url": u, "error": str(e)[:200]})   # RECORD, don't just print [A#21]
            print(f"  {u[:58]:<58} ERR {str(e)[:40]}")
    config.write_json(f"{proof}/01b-ranked.json", list(ranked.values()))
    if failures:
        # A run where most URLs failed must be distinguishable from a healthy one on disk. Loud + on record.
        config.write_json(f"{proof}/01b-failures.json", failures)
        if len(failures) > len(urls) / 2:
            print(f"  !! ranked-net: {len(failures)}/{len(urls)} URLs FAILED — thin ranked pool "
                  f"(see 01b-failures.json)")

    # merge ranked-net into the pool (tight net already there)
    pool = {r["kw"]: r for r in json.load(open(f"{proof}/01-pool.json"))}
    tight_n = len(pool)
    for k, r in ranked.items():
        if k not in pool: pool[k] = r
    config.write_json(f"{proof}/01-pool.json", list(pool.values()))
    print(f"\nsources: {len(competitor_urls)} competitor + {len(serp_urls)} SERP = {len(urls)} URLs")
    print(f"ranked-net: {len(ranked)} unique | tight pool was {tight_n} | merged pool: {len(pool)}")
    print(f"saved -> {proof}/01b-ranked.json + merged into 01-pool.json")

if __name__ == "__main__":
    main()
