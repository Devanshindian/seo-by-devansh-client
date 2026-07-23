#!/usr/bin/env python3
"""Step C — the real scored gate: Ownability + Linkability (same two tests as Methods 1 & 3).

Reads:  _work/adaptations.json   (the ideas, now with real subjects)
        brand-scope.md           (the ownership anchor)
Writes: _work/filtered.json      — the SURVIVORS, each carrying the AUTHORITATIVE brand_fit (supersedes A3's rough tag)
        _work/run-log.md (append)— every DROP with its reason (the cut is audit-able)

Survive = verdict is not DROP (KEEP = CORE/TRANSPLANT pass; MAYBE = ADJACENT, kept as the lowest tier).
The brand_fit written here is the authoritative one (F1 — decided once, at the real gate). LLM JUDGMENT.
"""
import argparse, json, os, sys
import config as c
sys.path.insert(0, c.SHARED)
import llm


def run(redo=False):
    ideas = json.load(open(os.path.join(c.WORK, "adaptations.json")))
    listed = "\n".join(
        f"{i}. asset: {r.get('asset','')} | topic: {r.get('our_topic','')} | format: {r.get('format','')} | "
        f"angle: {r.get('distinct_angle','')}" for i, r in enumerate(ideas))
    p = (llm.load_prompt("c-filter.md").replace("{{BRAND}}", c.BRAND)
         .replace("{{BRAND_SCOPE}}", open(c.BRAND_SCOPE).read()).replace("{{IDEAS}}", listed))
    verdicts = {v["id"]: v for v in llm.call_json(p).get("verdicts", []) if "id" in v}

    survivors, drops = [], []
    for i, r in enumerate(ideas):
        v = verdicts.get(i)
        if not v:                                              # no verdict returned -> keep, flag conservative
            survivors.append({**r, "brand_fit": r.get("prescreen_fit") or "ADJACENT",
                              "filter_reason": "no verdict returned — kept conservatively"})
            continue
        if v.get("verdict") == "DROP":
            drops.append((r.get("asset", ""), v.get("reason", "")))
            continue
        survivors.append({**r, "brand_fit": v.get("brand_fit", "ADJACENT"),
                          "transplant_note": v.get("transplant_note", ""),
                          "linkability_yes": v.get("linkability_yes", 0),
                          "filter_reason": v.get("reason", "")})

    c.write_json(os.path.join(c.WORK, "filtered.json"), survivors)
    if drops:
        with open(os.path.join(c.WORK, "run-log.md"), "a") as log:
            log.write(f"\n## Step C drops ({len(drops)})\n")
            for asset, why in drops:
                log.write(f"- **{asset}** — {why}\n")
    print(f"   {len(ideas)} ideas -> {len(survivors)} kept, {len(drops)} dropped (Ownability + Linkability)")
    from collections import Counter
    print(f"   brand fit: {dict(Counter(s['brand_fit'] for s in survivors))}")
    return survivors


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
