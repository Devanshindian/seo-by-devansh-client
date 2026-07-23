#!/usr/bin/env python3
"""Step D — score Beatability (1-3) + Effort (S/M/L) on every survivor (same scales as Method 1).

Reads:  _work/filtered.json   (the survivors)
Writes: _work/scored.json     (same rows + beatability + effort)

One batched LLM call over the survivors (scoring is a light judgment against a fixed rubric). LLM JUDGMENT.
"""
import argparse, json, os, sys
import config as c
sys.path.insert(0, c.SHARED)
import llm


def run(redo=False):
    ideas = json.load(open(os.path.join(c.WORK, "filtered.json")))
    listed = "\n".join(
        f"{i}. asset: {r.get('asset','')} | format: {r.get('format','')} | "
        f"what: {r.get('what_it_would_be','')}" for i, r in enumerate(ideas))
    p = llm.load_prompt("d-score.md").replace("{{BRAND}}", c.BRAND).replace("{{IDEAS}}", listed)
    scores = {s["id"]: s for s in llm.call_json(p).get("scores", []) if "id" in s}

    out = []
    for i, r in enumerate(ideas):
        s = scores.get(i, {})
        out.append({**r, "beatability": int(s.get("beatability", 2)), "effort": s.get("effort", "M")})
    c.write_json(os.path.join(c.WORK, "scored.json"), out)
    from collections import Counter
    print(f"   scored {len(out)} ideas · beatability {dict(Counter(x['beatability'] for x in out))} · "
          f"effort {dict(Counter(x['effort'] for x in out))}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
