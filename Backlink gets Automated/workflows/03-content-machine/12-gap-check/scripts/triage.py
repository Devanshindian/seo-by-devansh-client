"""Step 2 — Gap triage + STORM query writer. One call over all the misses PLUS the dossier itself.
2026-08-04: triage now reads the whole dossier and may raise an under-researched AREA nobody flagged
(source="own_find", higher bar than flagged items — see the prompt). It also knows what STORM actually is
(a research team, not a lookup), so single-fact holes are dropped instead of burning a run.
Reads:  coverage-verdicts.json (from judge) + the dossier. Takes only verdict in {no, partial}.
Writes: gap-queries.json — { "queries": [ {query, fills, source, why}, ... ] }  (0 to 3 queries)
"""
import sys, json
import config
import llm

TEMPLATE = llm.load_prompt("gap-triage.md")

# The coverage judge may only emit these three (mirrors report.py MARK). An UNKNOWN verdict must be a hard
# error, not a silent "not a miss" — otherwise a judge that writes "not covered" / "yes" / "unclear" drops the
# item off the miss list and it is treated as covered. That is the exact fail-open [A#17] this guards against.
VALID_VERDICTS = ("covered", "no", "partial")
MISS_VERDICTS = ("no", "partial")


def run(verdicts_path, out_path, dossier_path=None):
    data = json.load(open(verdicts_path))
    dossier = open(dossier_path).read() if dossier_path else "(dossier not provided)"
    bad = [v for v in data["verdicts"] if v.get("verdict") not in VALID_VERDICTS]
    if bad:
        sample = "; ".join(f"{v.get('item','?')!r}={v.get('verdict')!r}" for v in bad[:5])
        raise ValueError(f"{len(bad)} coverage verdict(s) outside {VALID_VERDICTS}: {sample}. "
                         f"Refusing to triage — an unrecognised verdict silently reads as 'covered'.")
    misses = [v for v in data["verdicts"] if v["verdict"] in MISS_VERDICTS]
    # NOTE (2026-08-04): no early-exit on zero misses any more — triage also reads the dossier for
    # under-researched AREAS (own_find), so it runs even when the checklist is fully covered.
    lines = ([f"- [{v['verdict']}] ({v['type']}) {v['item']} — judge: {v['reason']}" for v in misses]
             or ["(none — every checklist item was judged covered)"])
    prompt = (TEMPLATE
              .replace("{{ASSET_TITLE}}", data["asset_title"])
              .replace("{{DISTINCT_ANGLE}}", data["distinct_angle"])
              .replace("{{SPINE}}", data.get("spine") or "(not available)")
              .replace("{{ABOUT}}", data.get("about") or "(not available)")
              .replace("{{NOT_ABOUT}}", data.get("not_about") or "(not available)")
              .replace("{{NO_AND_PARTIAL_ITEMS}}", "\n".join(lines))
              .replace("{{DOSSIER_TEXT}}", dossier))
    result = llm.call_json(prompt)
    queries = result.get("queries", [])[:3]         # hard cap at 3
    config.write_json(out_path, {"queries": queries})
    print(f"{len(misses)} misses -> {len(queries)} STORM queries -> {out_path}")
    for q in queries:
        print(f"  Q [{q.get('source', 'flagged')}]: {q['query']}")
    return {"queries": queries}


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
