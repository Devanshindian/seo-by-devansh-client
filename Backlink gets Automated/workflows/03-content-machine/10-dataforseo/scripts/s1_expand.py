#!/usr/bin/env python3
"""Step 1a — TIGHT net expansion (keyword_suggestions, one call per seed).
The wide net (keyword_ideas) was dropped — proven to return only off-topic noise. Relevant breadth now
comes from the ranked-net (s1b_ranked.py). This writes the tight pool; s1b merges the ranked-net into it.
Usage: python3 s1_expand.py <run_dir> "<seed1>" "<seed2>" ...
"""
import os, sys, json
import dfs, config

def row(it):
    ki = it.get("keyword_info", {}) or {}
    kp = it.get("keyword_properties", {}) or {}
    return {"kw": it.get("keyword"), "vol": ki.get("search_volume") or 0,
            "kd": kp.get("keyword_difficulty"), "comp": ki.get("competition_level"), "src": "tight"}

def all_items(resp):
    return [i for t in (resp.get("tasks") or []) for r in (t.get("result") or []) for i in (r.get("items") or [])]

def main():
    run, seeds = sys.argv[1], sys.argv[2:]
    if not seeds: sys.exit("give at least one seed")
    proof = os.path.join(run, "proof"); os.makedirs(proof, exist_ok=True)
    base = {"location_name": config.LOCATION, "language_code": config.LANGUAGE}

    # keyword_suggestions allows only ONE seed per call — loop.
    tight_all = []
    for s in seeds:
        tight_all.append(dfs.call("/v3/dataforseo_labs/google/keyword_suggestions/live",
            [{**base, "keyword": s, "limit": config.TIGHT_LIMIT,
              "order_by": ["keyword_info.search_volume,desc"]}]))
    config.write_json(f"{proof}/01a-tight.json", tight_all)

    pool = {}
    for resp in tight_all:
        for it in all_items(resp):
            r = row(it)
            if r["kw"]: pool[r["kw"]] = r
    config.write_json(f"{proof}/01-pool.json", list(pool.values()))
    print(f"tight net: {sum(len(all_items(r)) for r in tight_all)} pulled across {len(seeds)} seeds "
          f"| unique tight pool: {len(pool)}")
    print(f"saved -> {proof}/01a-tight.json, 01-pool.json  (run s1b_ranked.py next to add the ranked-net)")

if __name__ == "__main__":
    main()
