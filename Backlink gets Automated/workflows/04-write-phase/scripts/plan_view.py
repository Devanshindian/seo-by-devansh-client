#!/usr/bin/env python3
"""Planner Step 5 — PLAN VIEW: render the frozen plan as plain-English markdown for human review.

Reads:  planner/article-plan.json (+ the _work stats when present).
Writes: planner/article-plan.md. Always rebuilds (it is a view, not a decision).
"""
import argparse
import json
import os
import config


def run(slug, redo=True):
    plan = json.load(open(config.artifact(slug, "article-plan.json")))
    wb = plan.get("word_band") or {}
    L = [f"# PLAN — {plan.get('h1', '')}", "",
         f"**Archetype:** {plan.get('format_archetype')} · **Primary keyword:** {plan.get('primary_keyword')} · "
         f"**Word band:** {wb.get('min')}-{wb.get('max')} · **Sections:** {len(plan.get('sections') or [])}", ""]

    for i, s in enumerate(plan.get("sections") or [], 1):
        tk = s.get("target_keyword") or {}
        kw = f"  _(target: {tk['keyword']}, {tk.get('volume', '?')}/mo)_" if tk.get("keyword") else ""
        L.append(f"## {i}. {s.get('h2', '')}{kw}")
        for h in s.get("h3s") or []:
            tags = ", ".join(h.get("tags") or []) or "-"
            placed = f"  ⇐ placed from: {h['placed_from']}" if h.get("placed_from") else ""
            L.append(f"- {h.get('h3', '')}  ({len(h.get('card_ids') or [])} cards) — {tags}{placed}")
        L.append("")

    # coverage summary (from the tags themselves)
    served = {t for s in plan.get("sections") or [] for h in s.get("h3s", []) for t in h.get("tags", [])}
    L.append("## Coverage")
    for kind, key, label in [("gap", "gaps_to_own", "Gaps"), ("common-h2", "winners_common_h2s", "Table-stakes"),
                             ("paa", "paa_pool", "PAA questions"), ("related", "related_searches", "Related searches")]:
        items = plan.get(key) or []
        holes = [x for x in items if f"{kind}: {x}" not in served]
        line = f"- **{label}:** {len(items) - len(holes)}/{len(items)} served"
        if holes:
            line += " — holes: " + "; ".join(h[:50] for h in holes)
        L.append(line)

    wd = config.planner_work_dir(slug)
    stats_p, police_p = os.path.join(wd, "selection-stats.json"), os.path.join(wd, "source-police.json")
    if os.path.exists(stats_p) or os.path.exists(police_p):
        L.append("")
        L.append("## What the pipeline did")
        if os.path.exists(stats_p):
            st = json.load(open(stats_p))
            L.append(f"- Selection: {st.get('survivors')}/{st.get('candidates')} sections kept · "
                     f"{st.get('h3s_dropped')} H3s dropped · {st.get('orphans_placed')} orphans re-homed")
        if os.path.exists(police_p):
            po = json.load(open(police_p))
            L.append(f"- Sources: {len(po.get('kept_ok') or [])} verified ok · {len(po.get('fixed') or [])} links FIXED · "
                     f"{len(po.get('cut') or [])} cards cut · {len(po.get('unverifiable_kept') or [])} unloadable kept")

    outp = config.artifact(slug, "article-plan.md")
    config.write_text(outp, "\n".join(L) + "\n")
    print(f"  -> {outp}")
    return outp


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Planner Step 5 — render the frozen plan for review.")
    ap.add_argument("--slug", required=True)
    a = ap.parse_args()
    print(f"== Planner Step 5: plan view — {a.slug} ==")
    run(a.slug)
