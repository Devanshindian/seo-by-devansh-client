#!/usr/bin/env python3
"""Step E — assemble the deliverable CSV (pure assembly, no LLM).

Reads:  _work/scored.json
Writes: output/model-other-niches-ideas.csv   THE DELIVERABLE — the shared 12-column merge schema

Pure assembly (F2): every cell traces to an earlier step. Nothing is invented here. Sort:
  Brand fit (CORE -> TRANSPLANT -> ADJACENT) -> Evidence x Beatability desc -> Effort (S<M<L).
"""
import argparse, csv, json, os, re, sys
import config as c

_FIT_ORDER = {"CORE": 0, "TRANSPLANT": 1, "ADJACENT": 2, "OUT": 9}
_EFFORT_ORDER = {"S": 0, "M": 1, "L": 2}

COLS = ["Idea #", "Method", "Brand fit", "Asset", "Format", "Tool escalation", "Our topic", "Distinct angle",
        "Source niche", "Evidence URLs", "Beatability", "Effort", "Notes"]


def _urls(example):
    """Evidence URLs = the real example URL(s) from the swipe row (proof inline)."""
    found = re.findall(r"https?://[^\s;,)]+", example or "")
    if found:
        return "; ".join(found)
    # the swipe example is often 'Big Mac Index — economist.com/big-mac-index' (bare domain) — keep as-is
    return example or ""


def _evidence_count(example):
    return max(len(re.split(r"[;,]| and ", example)) if example else 0, 1)


def run(redo=False):
    ideas = json.load(open(os.path.join(c.WORK, "scored.json")))
    ideas.sort(key=lambda r: (_FIT_ORDER.get(r.get("brand_fit"), 5),
                              -(_evidence_count(r.get("example", "")) * int(r.get("beatability", 2))),
                              _EFFORT_ORDER.get(r.get("effort", "M"), 1)))
    rows = []
    for i, r in enumerate(ideas, 1):
        notes = f"Headline: {r.get('headline','')} · What it'd be: {r.get('what_it_would_be','')}"
        if r.get("transplant_note"):
            notes += f" · Transplant: {r['transplant_note']}"
        rows.append({
            "Idea #": f"{c.IDEA_PREFIX}-{i:03d}",
            "Method": c.METHOD_TAG,
            "Brand fit": r.get("brand_fit", ""),
            "Asset": r.get("asset", ""),
            "Format": r.get("format", ""),
            "Tool escalation": r.get("tool_escalation", ""),
            "Our topic": r.get("our_topic", ""),
            "Distinct angle": r.get("distinct_angle", ""),
            "Source niche": r.get("source_niche", ""),
            "Evidence URLs": _urls(r.get("example", "")),
            "Beatability": r.get("beatability", ""),
            "Effort": r.get("effort", ""),
            "Notes": notes,
        })
    os.makedirs(c.OUT, exist_ok=True)
    path = os.path.join(c.OUT, "model-other-niches-ideas.csv")
    with open(path + ".tmp", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader()
        w.writerows(rows)
    os.replace(path + ".tmp", path)

    from collections import Counter
    print(f"   {len(rows)} ideas -> {c.rel(path)}")
    print(f"   brand fit: {dict(Counter(r['Brand fit'] for r in rows))}")
    print(f"\n   TOP 8:")
    for r in rows[:8]:
        print(f"     {r['Idea #']} [{r['Brand fit'][:4]}] {r['Asset'][:60]}")
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
