"""Step 6 — pick a target keyword per H2, reusing the DataForSEO repo's method (NOT keyword_ideas, which the
repo proved returns off-topic noise). For each H2: split it into seed phrases -> keyword_suggestions per seed
(phrases that CONTAIN the seed = on-topic) -> keep candidates with KD < KD_CEIL and volume >= VOL_FLOOR ->
an LLM picks the single best relevant one (or none). Costs DataForSEO credits.

Reuses the sibling 10-dataforseo/scripts/dfs.py caller and the same keyword_suggestions call as s1_expand.py.
"""
import os, sys, json
from concurrent.futures import ThreadPoolExecutor
import config, llm

sys.path.insert(0, os.path.join(config.CM, "10-dataforseo", "scripts"))
import dfs  # noqa: E402

SEEDS = llm.load_prompt("h2-seeds.md")
PICK = llm.load_prompt("pick-keyword.md")
LOCATION, LANGUAGE = config.LOCATION, config.LANGUAGE   # market from the company record (was hardcoded here)
SUGGEST_LIMIT = 80


def _seeds(h2, glosses):
    g = "\n".join(f"- {x}" for x in glosses[:6])
    try:
        r = llm.call_json(SEEDS.replace("{{H2}}", h2).replace("{{GLOSSES}}", g))
        seeds = [s.strip() for s in r.get("seeds", []) if s and s.strip()]
    except Exception:
        seeds = []
    return seeds[:3] or [h2[:60]]


def _suggest(seed):
    """keyword_suggestions — one seed per call (same call as s1_expand.py). On-topic phrases + metrics."""
    try:
        resp = dfs.call("/v3/dataforseo_labs/google/keyword_suggestions/live",
                        [{"location_name": LOCATION, "language_code": LANGUAGE, "keyword": seed,
                          "limit": SUGGEST_LIMIT, "order_by": ["keyword_info.search_volume,desc"]}])
    except Exception as e:
        print(f"    ! suggestions failed '{seed[:30]}': {e}")
        return []
    out = []
    for t in (resp.get("tasks") or []):
        for r in (t.get("result") or []):
            for it in (r.get("items") or []):
                ki = it.get("keyword_info", {}) or {}
                kp = it.get("keyword_properties", {}) or {}
                out.append({"kw": it.get("keyword"), "vol": ki.get("search_volume") or 0,
                            "kd": kp.get("keyword_difficulty")})
    return out


def _pick(h2, cands):
    survivors = [c for c in cands if (c["vol"] or 0) >= config.VOL_FLOOR
                 and c["kd"] is not None and c["kd"] < config.KD_CEIL]
    if not survivors:
        return None
    best = {}
    for c in survivors:                                   # dedupe by keyword, keep highest volume
        if c["kw"] and (c["kw"] not in best or (c["vol"] or 0) > (best[c["kw"]]["vol"] or 0)):
            best[c["kw"]] = c
    survivors = sorted(best.values(), key=lambda x: -(x["vol"] or 0))[:25]
    lines = "\n".join(f"{c['kw']} | {c['vol']} | {c['kd']}" for c in survivors)
    try:
        r = llm.call_json(PICK.replace("{{H2}}", h2).replace("{{CANDIDATES}}", lines))
    except Exception:
        return None
    if not r.get("keyword"):
        return None
    return {"keyword": r["keyword"], "volume": r.get("volume"), "kd": r.get("kd"), "why": r.get("why", "")}


def _glosses(section):
    g = [e["gloss"] for e in section.get("evidence", [])]
    for h in section.get("h3", []):
        g += [e["gloss"] for e in h.get("evidence", [])]
    return g


def _one(section):
    seeds = _seeds(section["h2"], _glosses(section))
    cands = []
    for s in seeds:
        cands += _suggest(s)
    section["target_keyword"] = _pick(section["h2"], cands)
    return section


def run(sections):
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        sections = list(ex.map(_one, sections))
    for s in sections:
        tk = s.get("target_keyword")
        extra = f"  (KD {tk['kd']} · vol {tk['volume']})" if tk else ""
        print(f"    {s['h2'][:44]:<44} -> {(tk['keyword'] if tk else '(none)')}{extra}")
    return sections


if __name__ == "__main__":
    sections = json.load(open(sys.argv[1]))["sections"]
    config.write_json(sys.argv[2], {"sections": run(sections)})
    print(f"-> {sys.argv[2]}")
