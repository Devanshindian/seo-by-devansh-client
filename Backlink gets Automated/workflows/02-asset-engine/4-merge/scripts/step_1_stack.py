#!/usr/bin/env python3
"""Step 1 — STACK the three method pools into one sheet, mapped to the shared schema (pure assembly, no LLM).

Reads:  M1 ideas.csv · M2 model-other-niches-ideas.csv · M3 study-trends-ideas.csv
Writes: _work/stacked.json   — every idea in the shared COLS shape, tagged by its Source method

Per-method column mapping (F2 — every cell traces to a source column, nothing invented):
- M1 has # pages / # words / domains / comps + backing URLs; no What-it'd-be, no Beatability/Effort.
- M2 has Beatability/Effort/Source-niche + Evidence URLs; Notes carries the headline + what-it'd-be.
- M3 has Tension/Audience/Emotion + # posts; its 'Unfair advantage' IS its distinct angle; 'Asset title' -> Asset.
The research phase's load-bearing field is Asset (the key); M3's 'Asset title' MUST map to Asset or it's invisible.
"""
import argparse, csv, os, sys
import config as c

csv.field_size_limit(1 << 24)


def _rows(path):
    return list(csv.DictReader(open(path))) if os.path.exists(path) else []


def _blank():
    return {k: "" for k in c.COLS}


def _from_m1(r):
    d = _blank()
    d.update({"Sources": "M1", "Brand fit": r.get("brand_fit", ""), "Asset": r.get("asset", ""),
              "Format": r.get("format", ""), "Tool escalation": r.get("tool_escalation", ""),
              "Distinct angle": r.get("distinct_angle", ""),
              "# pages": r.get("backing_pages", ""), "# words": r.get("median_words", ""),
              "Total domains": r.get("total_domains", ""), "# comps": r.get("competitors", ""),
              "Proof URLs": r.get("backing_urls", "")})
    return d


def _from_m2(r):
    d = _blank()
    d.update({"Sources": "M2", "Brand fit": r.get("Brand fit", ""), "Asset": r.get("Asset", ""),
              "Format": r.get("Format", ""), "Tool escalation": r.get("Tool escalation", ""),
              "Distinct angle": r.get("Distinct angle", ""),
              "What it'd be": r.get("Notes", ""), "Beatability": r.get("Beatability", ""),
              "Effort": r.get("Effort", ""), "Proof URLs": r.get("Evidence URLs", "")})
    return d


def _from_m3(r):
    d = _blank()
    d.update({"Sources": "M3", "Brand fit": r.get("Brand fit", ""), "Asset": r.get("Asset title", ""),
              # M3 has no 'distinct angle' column; its Unfair advantage IS the angle (what lets us own it),
              # prefixed with the tension so the research phase's blueprint has the pain in view.
              "Distinct angle": ((f"[{r.get('Tension','')}] " if r.get("Tension") else "") + r.get("Unfair advantage", "")).strip(),
              "What it'd be": r.get("What it'd be", ""), "# posts": r.get("# posts", ""),
              "Proof URLs": r.get("Best example URL", "")})
    return d


def run(redo=False):
    m1, m3 = _rows(c.M1), _rows(c.M3)
    m2 = _rows(c.M2) if c.INCLUDE_M2 else []       # Method 2 on hold by default (format-first over-tools)
    if not c.INCLUDE_M2:
        print("   M2 (model-other-niches) is ON HOLD — excluded from the merge (set MG_INCLUDE_M2=1 to include)")
    print(f"   M1 competitor: {len(m1)} · M2 other-niche: {len(m2)} · M3 reddit: {len(m3)}")
    for label, rows in [("M1", m1), ("M2", m2), ("M3", m3)]:
        if not rows:
            print(f"   ⚠ {label} pool is EMPTY (its deliverable is missing) — it won't be in the merge")
    stacked = [_from_m1(r) for r in m1] + [_from_m2(r) for r in m2] + [_from_m3(r) for r in m3]
    # every idea needs an Asset (the research key) — drop any that somehow have none, loudly
    stacked = [r for r in stacked if (r["Asset"] or "").strip()]
    os.makedirs(c.WORK, exist_ok=True)
    c.write_json(os.path.join(c.WORK, "stacked.json"), stacked)
    print(f"   stacked {len(stacked)} ideas -> {c.rel(os.path.join(c.WORK, 'stacked.json'))}")
    return stacked


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
