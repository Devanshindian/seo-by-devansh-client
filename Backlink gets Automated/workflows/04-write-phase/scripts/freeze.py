#!/usr/bin/env python3
"""Planner Step 4 — FREEZE: the final gate. Checks the verified plan's SHAPE, then stamps the immutable
planner/article-plan.json — the ONE file the Architect is allowed to read.

Reads:  planner/_work/article-plan.verified.json (a legacy article-plan.draft.json is adopted + migrated).
Writes: planner/article-plan.json (ONLY when no hard flag) + planner/_work/freeze-report.json (always).

HARD flags (structural breakage — the plan is NOT frozen): no sections · a section with zero H3s · an H3
with zero cards · missing h1 / primary keyword / archetype · word band missing or zero.
SOFT notes (recorded, never blocking): a hard-hole (a gap / table-stake / PAA question no H3 serves — the
coverage check lives here now) · fewer than 3 sections · source verification cut more than 15 cards.
Shape checks only: every judgment already happened upstream. Freeze is a bouncer, not a judge.
"""
import argparse
import json
import os
import shutil
import config


def _load_verified(slug):
    p = os.path.join(config.planner_work_dir(slug), "article-plan.verified.json")
    legacy = os.path.join(config.planner_dir(slug), "article-plan.draft.json")
    if not os.path.exists(p) and os.path.exists(legacy):
        shutil.move(legacy, p)                     # self-heal: adopt output written before the rename
        print(f"  migrated legacy draft -> {p}")
    return p, json.load(open(p))


def run(slug, redo=False):
    outp = config.artifact(slug, "article-plan.json")
    src_p, plan = _load_verified(slug)
    if os.path.exists(outp) and not redo and os.path.getmtime(outp) >= os.path.getmtime(src_p):
        print(f"  reusing {outp}")
        return {"hard": [], "soft": [], "reused": True}

    hard, soft = [], []
    secs = plan.get("sections") or []
    if not secs:
        hard.append("no sections")
    if not plan.get("h1"):
        hard.append("missing h1")
    if not plan.get("primary_keyword"):
        hard.append("missing primary keyword")
    if not plan.get("format_archetype"):
        hard.append("missing format archetype")
    wb = plan.get("word_band") or {}
    if not wb.get("min") or not wb.get("max"):
        hard.append("word band missing/zero")
    for s in secs:
        if not s.get("h3s"):
            hard.append(f"section with zero H3s: {s.get('h2', '?')[:50]}")
        for h in s.get("h3s") or []:
            if not h.get("card_ids"):
                hard.append(f"H3 with zero cards: {h.get('h3', '?')[:50]}")

    # the folded-in coverage check (soft): any promise no H3 serves?
    served = {t for s in secs for h in s.get("h3s", []) for t in h.get("tags", [])}
    for kind, key in [("gap", "gaps_to_own"), ("common-h2", "winners_common_h2s"), ("paa", "paa_pool")]:
        for item in plan.get(key) or []:
            if f"{kind}: {item}" not in served:
                soft.append(f"HOLE ({kind}): {item}")
    if len(secs) < 3:
        soft.append(f"only {len(secs)} sections")
    sp = os.path.join(config.planner_work_dir(slug), "source-police.json")
    if os.path.exists(sp):
        pol = json.load(open(sp))
        cuts = len(pol.get("cut") or [])
        if cuts > 15:
            soft.append(f"source verification cut {cuts} cards")
        unchecked = len(pol.get("search_failed") or [])
        if unchecked:
            soft.append(f"{unchecked} card(s) left UNVERIFIED (search failed or cap reached) — still in the plan")
        unloadable = len(pol.get("unverifiable_kept") or [])
        if unloadable > 20:
            soft.append(f"{unloadable} cards kept with sources that would not load — verify before publishing")

    report = {"hard": hard, "soft": soft}
    config.write_json(os.path.join(config.planner_work_dir(slug), "freeze-report.json"), report)
    if hard:
        print("  X NOT frozen — hard flags:")
        for x in hard:
            print("    -", x)
        return report
    config.write_json(outp, plan)
    print(f"  frozen -> {outp}" + (f" | {len(soft)} soft note(s)" if soft else ""))
    for x in soft:
        print("    note:", x)
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Planner Step 4 — freeze the plan (shape checks, then stamp).")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Planner Step 4: freeze — {a.slug} ==")
    run(a.slug, redo=a.redo)
