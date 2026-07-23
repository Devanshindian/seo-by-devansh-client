#!/usr/bin/env python3
"""Step 3 — RELEVANCE RECHECK: a final atomic gate that removes obvious junk / off-brand ideas.

Reads:  output/clubbed-ideas.csv        (the merged pool from step 2)
        competitor-study/output/brand-scope.md   (the approved ownership anchor — shared across methods)
Writes: _work/relevance-verdicts.json   (every KEEP/DROP verdict + reason — auditable)
        _work/relevance-drops.json       (just the drops — the list Devansh approves)
   --apply only:
        output/clubbed-ideas.csv         (rewritten WITHOUT the dropped rows)
        _work/clubbed-before-relevance.csv  (a backup of the pre-drop file)

WHY THIS STEP (Devansh, 2026-07-22). G2 reasons on ONE page at a time and is generous, so junk survives:
self-referential product/pricing pages that leaked through Step C ("Company X Pricing Calculator"), and
off-brand subjects (reference/background checks) the per-page SKIP missed. This pass looks at the FINISHED
idea with fresh eyes and removes obvious junk only. Design rules:
 - ATOMIC: judge each idea on its own (J3), never a group.
 - CONSERVATIVE: drop only clear nonsense / off-brand; when unsure, KEEP. Few backlinks is NEVER a reason.
 - PROTECT: an idea with strong backlink proof (>= PROTECT_DOMAINS) is never dropped, whatever the model says.
 - CAPPED: if the model wants to drop more than DROP_CAP of the pool, that's suspicious — refuse to apply
   without --force, so a bad run can't silently gut the list.
 - GATED: default is PROPOSE (write the drop list, change nothing). --apply removes, after a backup.
 - GROUND-TRUTH: validate against idea-review/drop-list.csv (must catch the same KINDS) before trusting it.
"""
import argparse, csv, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c
sys.path.insert(0, c.SHARED)
import llm

csv.field_size_limit(1 << 24)
PROMPT = None


def _brand_scope():
    """The approved scope lives in the competitor-study output (shared anchor across methods)."""
    p = os.path.join(c.ASSET_ENGINE, "competitor-study", "output", "brand-scope.md")   # noqa: F405
    return open(p).read().strip() if os.path.exists(p) else ""


def _int(v):
    try:
        return int(float(str(v).replace(",", "")))
    except (ValueError, TypeError):
        return 0


def _row_line(i, r):
    return (f"id={i} · {(r.get('Asset') or '')[:110]} · [{r.get('Format','?')}] · "
            f"{r.get('Brand fit','?')} · angle: {(r.get('Distinct angle') or '')[:130]}")


def _judge_batch(idx_rows, scope):
    block = "\n".join(_row_line(i, r) for i, r in idx_rows)
    prompt = PROMPT.replace("{{BRAND}}", c.BRAND).replace("{{BRAND_SCOPE}}", scope).replace("{{ROWS}}", block)
    try:
        out = llm.call_json(prompt)
    except Exception as e:
        print(f"   !! a batch failed ({str(e)[:50]}) — kept all KEEP")
        return {i: ("KEEP", "") for i, _ in idx_rows}
    by_id = {int(o.get("id", -1)): o for o in (out.get("verdicts") or [])}
    res = {}
    for i, _ in idx_rows:
        o = by_id.get(i) or {}
        dec = "DROP" if str(o.get("decision", "")).upper() == "DROP" else "KEEP"
        res[i] = (dec, o.get("reason", "") if dec == "DROP" else "")
    return res


def run(apply=False, force=False):
    global PROMPT
    PROMPT = llm.load_prompt("relevance-recheck.md")
    if not os.path.exists(c.CLUBBED):
        sys.exit(f"!! no {c.rel(c.CLUBBED)} — run the merge (steps 1-2) first")
    scope = _brand_scope()
    if not scope:
        print("   ⚠ no brand-scope.md found — the judge runs without the ownership anchor (weaker). Continuing.")
    rows = list(csv.DictReader(open(c.CLUBBED)))
    n = len(rows)

    # --apply reuses the ALREADY-PROPOSED + human-validated drop list — it does NOT re-judge (decide once, F1).
    # Re-judging on apply would re-spend the LLM and could drift from the exact set that was reviewed.
    saved_drops = os.path.join(c.WORK, "relevance-drops.json")
    if apply and os.path.exists(saved_drops):
        drop_assets = {d.get("asset", "") for d in json.load(open(saved_drops)) if d.get("asset")}
        keep = [r for r in rows if r.get("Asset", "") not in drop_assets]
        import shutil
        shutil.copyfile(c.CLUBBED, os.path.join(c.WORK, "clubbed-before-relevance.csv"))
        with open(c.CLUBBED + ".tmp", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=c.COLS, extrasaction="ignore"); w.writeheader(); w.writerows(keep)
        os.replace(c.CLUBBED + ".tmp", c.CLUBBED)
        print(f"   APPLIED saved drops — removed {n - len(keep)}, kept {len(keep)}. "
              f"Backup: _work/clubbed-before-relevance.csv")
        return keep

    # PROTECT: strong-proof ideas are never even sent to the judge (they can't be dropped) — J3 protect rule.
    protected, candidates = [], []
    for i, r in enumerate(rows):
        (protected if _int(r.get("Total domains")) >= c.PROTECT_DOMAINS else candidates).append((i, r))
    print(f"   {n} ideas · {len(protected)} protected (>= {c.PROTECT_DOMAINS} domains) · {len(candidates)} to judge")

    batches = [candidates[k:k + c.RELEVANCE_BATCH] for k in range(0, len(candidates), c.RELEVANCE_BATCH)]
    verdicts = {i: ("KEEP", "") for i, _ in protected}
    with ThreadPoolExecutor(max_workers=c.RELEVANCE_WORKERS) as ex:
        futs = [ex.submit(_judge_batch, b, scope) for b in batches]
        for m, fut in enumerate(as_completed(futs), 1):
            verdicts.update(fut.result())
            if m % 10 == 0:
                print(f"   ...{m}/{len(batches)} batches")

    drops = [{"id": i, "asset": rows[i].get("Asset", ""), "format": rows[i].get("Format", ""),
              "brand_fit": rows[i].get("Brand fit", ""), "domains": _int(rows[i].get("Total domains")),
              "reason": verdicts[i][1]} for i in range(n) if verdicts.get(i, ("KEEP",))[0] == "DROP"]
    drop_frac = len(drops) / max(n, 1)

    os.makedirs(c.WORK, exist_ok=True)
    c.write_json(os.path.join(c.WORK, "relevance-verdicts.json"),
                 [{"id": i, "decision": verdicts[i][0], "reason": verdicts[i][1],
                   "asset": rows[i].get("Asset", "")} for i in range(n)])
    c.write_json(os.path.join(c.WORK, "relevance-drops.json"), drops)

    print(f"\n   proposed DROPS: {len(drops)}/{n} ({100*drop_frac:.1f}%)")
    for d in drops[:20]:
        print(f"     - [{d['brand_fit'][:4]}] d={d['domains']:>4} {d['asset'][:60]}  ||  {d['reason'][:45]}")
    if len(drops) > 20:
        print(f"     ... +{len(drops)-20} more in _work/relevance-drops.json")

    if drop_frac > c.RELEVANCE_DROP_CAP and not force:
        print(f"\n   ⛔ drop rate {100*drop_frac:.1f}% exceeds the cap ({100*c.RELEVANCE_DROP_CAP:.0f}%). "
              f"NOT applying — review _work/relevance-drops.json, then re-run with --apply --force if it's right.")
        return drops

    if not apply:
        print(f"\n   PROPOSE mode — nothing removed. Review _work/relevance-drops.json, then re-run with --apply.")
        return drops

    # --apply: back up, then rewrite clubbed WITHOUT the drops (atomic)
    keep = [rows[i] for i in range(n) if verdicts.get(i, ("KEEP",))[0] != "DROP"]
    import shutil
    shutil.copyfile(c.CLUBBED, os.path.join(c.WORK, "clubbed-before-relevance.csv"))
    with open(c.CLUBBED + ".tmp", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=c.COLS, extrasaction="ignore"); w.writeheader()
        w.writerows(keep)
    os.replace(c.CLUBBED + ".tmp", c.CLUBBED)
    print(f"\n   APPLIED — removed {len(drops)}, kept {len(keep)}. Backup: _work/clubbed-before-relevance.csv")
    return drops


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually remove the drops (default: propose only)")
    ap.add_argument("--force", action="store_true", help="apply even if the drop rate exceeds the cap")
    ap.add_argument("--redo", action="store_true", help="(ignored) present so the orchestrator can pass it")
    a = ap.parse_args()
    run(apply=a.apply, force=a.force)
