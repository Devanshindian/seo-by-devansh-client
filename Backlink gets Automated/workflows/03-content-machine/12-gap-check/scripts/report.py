"""Step 4 — Report. Pure assembly, no new thinking: every line traces to an upstream file.
Reads:  coverage-items.json, coverage-verdicts.json, gap-queries.json, storm-iterations.json (if any).
Writes: gap-check.md
"""
import sys, os, json
import config

MARK = {"covered": "[x]", "partial": "[~]", "no": "[ ]"}


def run(run_dir):
    items = json.load(open(os.path.join(run_dir, "coverage-items.json")))
    verdicts = json.load(open(os.path.join(run_dir, "coverage-verdicts.json")))["verdicts"]
    queries = json.load(open(os.path.join(run_dir, "gap-queries.json")))["queries"]
    it_path = os.path.join(run_dir, "storm-iterations.json")
    iterations = json.load(open(it_path))["iterations"] if os.path.exists(it_path) else []

    counts = {}
    for v in verdicts:
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
    misses = [v for v in verdicts if v["verdict"] in ("no", "partial")]

    L = [f"# Gap-check — {items['asset_title']}", "",
         f"> **Distinct angle:** {items['distinct_angle']}", "",
         "## Summary",
         f"- Items checked: **{len(verdicts)}** "
         f"(covered {counts.get('covered', 0)} · partial {counts.get('partial', 0)} · no {counts.get('no', 0)})",
         f"- Gaps (no + partial): **{len(misses)}**",
         f"- STORM iterations run: **{len(iterations)}**", ""]

    L += ["## Coverage verdict per item",
          "| | verdict | type | item | why | evidence |",
          "|---|---|---|---|---|---|"]
    for v in verdicts:
        ev = (v["evidence"] or "").replace("|", "\\|").replace("\n", " ")
        rs = (v["reason"] or "").replace("|", "\\|").replace("\n", " ")
        it = v["item"].replace("|", "\\|")
        L.append(f"| {MARK.get(v['verdict'], '?')} | {v['verdict']} | {v['type']} | {it} | {rs} | {ev} |")
    L.append("")

    L.append("## Gaps found (fed to triage)")
    L += ([f"- **[{v['verdict']}]** ({v['type']}) {v['item']} — {v['reason']}" for v in misses]
          or ["- none — the dossier covers every checked item."])
    L.append("")

    L.append("## STORM iterations")
    if queries:
        for i, q in enumerate(queries, 1):
            rec = next((r for r in iterations if r["i"] == i), None)
            L += [f"### Iteration {i}",
                  f"- **Query:** {q['query']}",
                  f"- **Why:** {q.get('why', '')}",
                  f"- **Fills:** {', '.join(q.get('fills', []))}",
                  f"- **Saved to:** `projects/{config.COMPANY}/content-machine/storm/out/{rec['dir']}/`" if rec and rec.get("dir")
                  else "- **Saved to:** (run produced no output dir)", ""]
    else:
        L += ["- none — no gap cleared the 'important AND uncovered' bar. No re-run needed.", ""]

    L += ["## Proof (raw files)",
          "- `coverage-items.json` — items read from the brief (Step 0).",
          "- `coverage-verdicts.json` — coverage verdict per item (Step 1).",
          "- `gap-queries.json` — the STORM queries (Step 2)."]
    if iterations:
        L.append(f"- `storm-iterations.json` + `projects/{config.COMPANY}/content-machine/storm/out/<Topic>/iteration-<n>/` — the gap-fill runs (Step 3).")

    out = os.path.join(run_dir, "gap-check.md")
    config.write_text(out, "\n".join(L) + "\n")
    print(f"report -> {out}")
    return out


if __name__ == "__main__":
    run(sys.argv[1])
