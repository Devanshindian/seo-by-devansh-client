#!/usr/bin/env python3
"""Architect Step 4 — SECTION KEYWORDS: which sections deserve a search keyword, and which one.

Built 2026-08-04. The research phase used to buy a keyword per H2 of the *planned* blueprint — headings
the architect then redesigned away (live proof: one article bought 5 keywords for 17 sections, 3 of them
for sections the spine filter later deleted). That step is gone; this is its replacement, run where the
sections are REAL and their evidence is final.

Two sub-steps:
  4a GATE   one AI call over the whole article: would a person type this section's subject into Google
            as its own search? Most sections should be NO — they carry the argument, not a search.
            Free. Nothing is bought for a section the gate rejects.
  4b HUNT   for each gated-YES section, in parallel:
              seeds  (reads that section's CARDS — the heading can lie, the evidence cannot)
              -> DataForSEO keyword_suggestions, one call per seed (same call s1_expand.py uses)
              -> filter: volume >= VOL_FLOOR, KD < KD_CEIL
              -> pick ONE, or none. Returning none is an explicitly good answer.

The world (about / not_about) rides into every prompt, so a phrase whose searchers live in a different
field is rejected here rather than becoming a heading.

Reads:  architect/structure.json · gather/plan-inputs.json (cards + keyword set) · the research bundle's
        spine.json (the world) + the queue row (title/angle).
Writes: architect/_work/section-keywords.json — every section, its gate verdict, its seeds, its
        candidates and its pick (including the nulls and why). Nothing here edits the structure.
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import article_ctx
import config
import llm

# The paid client lives with the DataForSEO engine (config.DFS_SCRIPTS). Imported lazily inside the hunt so
# the gate — and every import of this module — works even when that engine or its creds are unavailable.
_dfs = None


def _dfs_client():
    global _dfs
    if _dfs is None:
        if config.DFS_SCRIPTS not in sys.path:
            sys.path.insert(0, config.DFS_SCRIPTS)
        import dfs as _m
        _dfs = _m
    return _dfs

SUGGEST_LIMIT = 80          # phrases pulled per seed (same as the old per-H2 step)
CAND_SHOWN = 25             # candidates shown to the picker, best-by-volume


def _fill(name, **kw):
    p = llm.load_prompt(name)
    for k, v in kw.items():
        p = p.replace("{{" + k + "}}", str(v))
    return p


def _card_index(slug):
    """Every card the article may cite: the research cards, the enriched ones (9001+), and any of
    the company's own material the architect placed (8001+)."""
    idx = {}
    inp = json.load(open(config.artifact(slug, "plan-inputs.json")))
    for s in inp["group_b"]["sections_menu"]:
        for c in s.get("evidence", []):
            idx[str(c.get("card_id"))] = c
        for h in s.get("h3", []):
            for c in h.get("evidence", []):
                idx[str(c.get("card_id"))] = c
    for name in ("enriched-cards.json", "brand-cards-used.json"):
        ep = config.artifact(slug, name)
        if os.path.exists(ep):
            for cid, c in json.load(open(ep)).items():
                idx[str(cid)] = c
    return idx


def render_cards(sec, idx, limit=None):
    """One line per card under this section. limit=None means ALL of them (per-section calls can afford it)."""
    import shape                      # local: keeps this module importable without the shape chain
    lines = []
    for h in shape._groups(sec):
        for cid in h.get("card_ids", []):
            c = idx.get(str(cid)) or {}
            text = (c.get("verbatim") or c.get("gloss") or "").strip().replace("\n", " ")[:config.BODY_CARD_CHARS]
            if text:
                lines.append(f"- {text}")
            if limit and len(lines) >= limit:
                return "\n".join(lines)
    return "\n".join(lines) or "(this section holds no research facts)"


def _keyword_set(slug):
    ks = (json.load(open(config.artifact(slug, "plan-inputs.json")))["group_a"].get("keyword_set")) or {}
    if not ks.get("secondaries"):
        try:
            ks = dict(ks, secondaries=(json.load(open(config.structure_path(slug))).get("keyword_set") or {})
                      .get("secondaries") or [])
        except FileNotFoundError:
            ks = dict(ks, secondaries=[])
    return ks


# ---------------------------------------------------------------- 4a: the gate
def _gate(secs, sp, primary):
    block = "\n".join(f"  {i + 1}. {s.get('headline')}\n     job: {s.get('job') or '(none)'}"
                      for i, s in enumerate(secs))
    out = llm.call_json(_fill("keyword-gate.md",
                              TITLE=sp["title"] or "(untitled)", ANGLE=sp["angle"] or "(none recorded)",
                              SPINE=sp["spine"] or "(not available)", ABOUT=sp["about"] or "(not available)",
                              NOT_ABOUT=sp["not_about"] or "(not available)",
                              PRIMARY=primary or "(none)", PERSONA=sp["persona"], SECTIONS=block)) or {}
    verdicts = {}
    for r in out.get("sections") or []:
        try:
            verdicts[int(r["n"])] = {"hunt": bool(r.get("hunt")), "why": str(r.get("why") or "").strip()}
        except (KeyError, TypeError, ValueError):
            continue
    # A section the gate never mentioned is NOT hunted — silence must never mean "spend money".
    return [verdicts.get(i + 1, {"hunt": False, "why": "gate returned no verdict for this section"})
            for i in range(len(secs))]


# ---------------------------------------------------------------- 4b: the hunt
def _suggest(seed):
    """keyword_suggestions — one seed per call. Returns [{kw, vol, kd}]; [] on any failure (never fatal)."""
    try:
        resp = _dfs_client().call("/v3/dataforseo_labs/google/keyword_suggestions/live",
                        [{"location_name": config.LOCATION, "language_code": config.LANGUAGE,
                          "keyword": seed, "limit": SUGGEST_LIMIT,
                          "order_by": ["keyword_info.search_volume,desc"]}])
    except Exception as e:
        print(f"      ! suggestions failed for {seed[:34]!r}: {str(e)[:70]}")
        return []
    out = []
    for t in (resp.get("tasks") or []):
        for r in (t.get("result") or []):
            for it in (r.get("items") or []):
                ki, kp = it.get("keyword_info", {}) or {}, it.get("keyword_properties", {}) or {}
                if it.get("keyword"):
                    out.append({"kw": it["keyword"], "vol": ki.get("search_volume") or 0,
                                "kd": kp.get("keyword_difficulty")})
    return out


def _hunt_one(n, sec, sp, primary, idx):
    """seeds -> DataForSEO -> pick. Returns the record for this section (pick may be None)."""
    head, job = sec.get("headline") or "", sec.get("job") or "(none)"
    rec = {"n": n, "heading": head, "seeds": [], "why_seeds": "", "candidates": 0, "pick": None}
    try:
        s = llm.call_json(_fill("section-seeds.md",
                                TITLE=sp["title"] or "(untitled)", SPINE=sp["spine"] or "(not available)",
                                ABOUT=sp["about"] or "(not available)",
                                NOT_ABOUT=sp["not_about"] or "(not available)",
                                PRIMARY=primary or "(none)", PERSONA=sp["persona"], HEADING=head, JOB=job,
                                CARDS=render_cards(sec, idx))) or {}
    except Exception as e:
        rec["error"] = f"seeds failed: {str(e)[:90]}"
        return rec
    rec["seeds"] = [str(x).strip() for x in (s.get("seeds") or []) if str(x).strip()][:3]
    rec["why_seeds"] = str(s.get("why") or "").strip()
    if not rec["seeds"]:
        rec["error"] = "no seeds returned"
        return rec

    cands = []
    for seed in rec["seeds"]:
        cands += _suggest(seed)
    best = {}
    for c in cands:
        if (c["vol"] or 0) >= config.VOL_FLOOR and c["kd"] is not None and c["kd"] < config.KD_CEIL:
            if c["kw"] not in best or (c["vol"] or 0) > (best[c["kw"]]["vol"] or 0):
                best[c["kw"]] = c
    survivors = sorted(best.values(), key=lambda x: -(x["vol"] or 0))[:CAND_SHOWN]
    rec["candidates"] = len(survivors)
    if not survivors:
        rec["why_none"] = f"no candidate cleared vol>={config.VOL_FLOOR} / KD<{config.KD_CEIL}"
        return rec

    try:
        r = llm.call_json(_fill("pick-section-keyword.md",
                                HEADING=head, JOB=job, WHY=rec["why_seeds"] or "(not stated)",
                                SPINE=sp["spine"] or "(not available)",
                                NOT_ABOUT=sp["not_about"] or "(not available)",
                                PRIMARY=primary or "(none)", PERSONA=sp["persona"],
                                CANDIDATES="\n".join(f"{c['kw']} | {c['vol']} | {c['kd']}" for c in survivors))) or {}
    except Exception as e:
        rec["error"] = f"pick failed: {str(e)[:90]}"
        return rec

    kw = str(r.get("keyword") or "").strip()
    if not kw:
        rec["why_none"] = str(r.get("why") or "picker chose none").strip()
        return rec
    if kw not in best:                       # never accept a phrase we did not show it
        rec["why_none"] = f"picker returned {kw!r}, which was not among the candidates — rejected"
        return rec
    rec["pick"] = {"keyword": kw, "volume": best[kw]["vol"], "kd": best[kw]["kd"],
                   "why": str(r.get("why") or "").strip()}
    return rec


def run(slug, redo=False):
    outp = os.path.join(config.architect_work_dir(slug), "section-keywords.json")
    if os.path.exists(outp) and not redo:
        print(f"  reusing {os.path.basename(outp)} (--redo to redecide)")
        return json.load(open(outp))

    st = json.load(open(config.artifact(slug, "structure.json")))
    secs = st.get("sections") or []
    sp, ks, idx = article_ctx.article_context(slug, st), _keyword_set(slug), _card_index(slug)
    primary = ks.get("primary") or ""

    print(f"  == 4a gate == ({len(secs)} sections)")
    gate = _gate(secs, sp, primary)
    hunt_ns = [i + 1 for i, g in enumerate(gate) if g["hunt"]]
    for i, g in enumerate(gate):
        print(f"    [{'HUNT' if g['hunt'] else ' no ':^4}] {i + 1:2}. {(secs[i].get('headline') or '')[:62]}")
    print(f"  gate: {len(hunt_ns)} of {len(secs)} sections deserve a keyword")

    print(f"  == 4b hunt == ({len(hunt_ns)} lookups)")
    records = []
    if hunt_ns:
        with ThreadPoolExecutor(max_workers=llm.max_workers()) as ex:
            records = list(ex.map(lambda n: _hunt_one(n, secs[n - 1], sp, primary, idx), hunt_ns))
    by_n = {r["n"]: r for r in records}

    found = 0
    for i, g in enumerate(gate):
        r = by_n.get(i + 1)
        if r and r.get("pick"):
            found += 1
            p = r["pick"]
            print(f"    {i + 1:2}. {p['keyword']!r} (vol {p['volume']}, KD {p['kd']})")
        elif r:
            print(f"    {i + 1:2}. none — {r.get('why_none') or r.get('error') or 'no pick'}")

    # AN EMPTY HUNT IS NOW RECORDED (2026-08-08). Two of the first four articles gated sections YES,
    # paid for the lookups, and found ZERO keywords — and nothing anywhere said so. Usually it means
    # the floors bit (vol >= VOL_FLOOR, KD < KD_CEIL) on a narrow topic, which is the filter working;
    # occasionally it means the seeds were wrong. Either way a human should see it, so it is counted
    # in the file and printed loudly. It does not stop anything: no keyword is a valid outcome.
    empty = [{"n": r["n"], "heading": r["heading"],
              "why": r.get("why_none") or r.get("error") or "no pick",
              "seeds": r.get("seeds") or [], "candidates": r.get("candidates", 0)}
             for r in records if not r.get("pick")]
    result = {"slug": slug, "primary": primary,
              "hunted": len(hunt_ns), "found": found, "empty_hunts": empty,
              "sections": [{"n": i + 1, "heading": s.get("headline") or "",
                            "gate": gate[i], **{k: v for k, v in (by_n.get(i + 1) or {}).items() if k != "n"}}
                           for i, s in enumerate(secs)]}
    config.write_json(outp, result)
    print(f"  -> {found} section keyword(s) found across {len(hunt_ns)} hunt(s) -> {os.path.basename(outp)}")
    if hunt_ns and not found:
        print(f"  !! EVERY hunt came back empty: {len(hunt_ns)} section(s) were judged worth a keyword and "
              f"NONE cleared vol>={config.VOL_FLOOR} / KD<{config.KD_CEIL}. This article's headings will "
              f"carry no researched section keyword.")
    elif empty:
        print(f"  !! {len(empty)} of {len(hunt_ns)} hunt(s) came back empty:")
        for e in empty:
            print(f"       {e['n']:2}. {e['heading'][:44]} — {e['why'][:58]}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Architect Step 4 — gate + hunt a keyword per real section.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    run(a.slug, redo=a.redo)
