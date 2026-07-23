#!/usr/bin/env python3
"""Cannibalisation FLAG — checks OUR company's real ranking footprint. Do we ALREADY rank for this keyword?

Uses the dedicated DataForSEO `ranked_keywords` pull that 00-foundation ALREADY paid for and cached
(`00-foundation/_work/traffic-raw.json` — every keyword our domain ranks for + position + URL, ~18k rows).
We build a slim keyword→(rank,url) index from it ONCE (cached), then look up the article's target keyword: if we
rank for it in the top RANK_MAX (default 10 = page 1), flag it with the EXACT position + URL. EXACT (real ranking
data, not fuzzy), FREE at check-time (the $2.50 pull already happened in the foundation layer).

Never blocks — we still build (the new article should outperform); the flag rides into the bundle so the team
knows. Settings live in config.py: off-switch CANNIB_CHECK=0; rank window CANNIB_RANK_MAX (default 10 = page 1,
where a second page actually splits our own traffic).
"""
import os, json, re
import config

ENABLED = config.CANNIB_CHECK
RANK_MAX = config.CANNIB_RANK_MAX                            # only flag a TOP-N (page-1) ranking = real cannibalisation
TRAFFIC_RAW = os.path.join(config.REPO_ROOT, "projects", config.COMPANY, "00-foundation", "_work", "traffic-raw.json")
CACHE = os.path.join(config.PROJ_CM, "_work", "our-rankings.json")   # slim {normalised_kw: [rank, url]} lookup

_index = None


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())).strip()


def _build_index():
    """Slim keyword→[rank,url] index from the raw ranked_keywords pull. Cached; rebuilt only if the raw is newer."""
    if os.path.exists(CACHE) and os.path.exists(TRAFFIC_RAW) and os.path.getmtime(CACHE) >= os.path.getmtime(TRAFFIC_RAW):
        try:
            return json.load(open(CACHE))
        except Exception:
            pass
    if not os.path.exists(TRAFFIC_RAW):
        return {}
    try:
        raw = json.load(open(TRAFFIC_RAW))
    except Exception:
        return {}    # fail OPEN — a corrupt footprint file must never crash the run (this is a FLAG, never a gate)
    idx = {}
    for row in (raw.get("rows") or []):
        kw = _norm((row.get("keyword_data") or {}).get("keyword", ""))
        si = (row.get("ranked_serp_element") or {}).get("serp_item") or {}
        rank, url = si.get("rank_group"), si.get("url", "")
        if kw and rank and (kw not in idx or rank < idx[kw][0]):     # keep our BEST position for that keyword
            idx[kw] = [rank, url]
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        json.dump(idx, open(CACHE, "w"))
    except Exception:
        pass
    return idx


def check(keyword):
    """Return {'keyword','rank','url'} if we already rank (top RANK_MAX) for this exact keyword, else None."""
    global _index
    if not ENABLED:
        return None
    if _index is None:
        _index = _build_index()
    hit = _index.get(_norm(keyword))
    if hit and hit[0] and hit[0] <= RANK_MAX:
        return {"keyword": keyword, "rank": hit[0], "url": hit[1]}
    return None


if __name__ == "__main__":
    import sys
    print(check(sys.argv[1] if len(sys.argv) > 1 else "bricklayers exam"))
