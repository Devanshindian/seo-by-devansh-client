# Model Other Niches — how to run it + the file map

Method 2 of the asset engine: import proven link-bait **formats** from *other* industries (calculators,
indices, generators, awards) and adapt them to ours — the ones that earn links anywhere but no competitor in
our niche has built. The full recipe (WHAT/HOW, step by step) is in
[`model-other-niches.workflow.md`](model-other-niches.workflow.md). This README is just how to run it.

## Run it

```bash
python run_model_niches.py --company <slug>
```

One resumable command, steps **A → E**. No API, no paid calls, no human gates — Method 2 is fully agent-doable
(the LLM *is* the research tool). Its only inputs are already on disk: `brand-scope.md` (from Method 1 / G0)
plus the brand context. All LLM calls run on the free headless Claude/Codex CLI.

| Flag | What it does |
|---|---|
| `--company <slug>` | the company (or `COMPANY=`). Required. |
| `--from <STEP>` | force a re-run from this step onward (e.g. `--from C`). |
| `--redo` | force every step. |

## The steps (each writes one named file the next reads)

| Step | Script | Does | Writes |
|---|---|---|---|
| A | `step_a_swipe.py` | parse the proven-format table from the recipe (A1, deterministic); LLM adds ~5 more formats (A2); LLM pre-screens each on brand fit vs `brand-scope.md` (A3) | `_work/swipe.json` + `output/format-swipe.md` |
| B | `step_b_adapt.py` | one {company} adaptation per surviving format (parallel) — topic → angle → asset → headline | `_work/adaptations.json` |
| C | `step_c_filter.py` | the real gate: Ownability + Linkability (same two tests as Methods 1 & 3) → KEEP/DROP + authoritative brand fit | `_work/filtered.json` (+ drops in `_work/run-log.md`) |
| D | `step_d_score.py` | Beatability (1-3) + Effort (S/M/L), same scales as Method 1 | `_work/scored.json` |
| E | `step_e_deliver.py` | assemble + sort → the deliverable CSV (pure assembly, no LLM) | `output/model-other-niches-ideas.csv` |

## Output

- **`output/model-other-niches-ideas.csv`** — ★ THE DELIVERABLE. The 12-column shared merge schema
  (`Idea # | Method | Brand fit | Asset | Format | Our topic | Distinct angle | Source niche | Evidence URLs |
  Beatability | Effort | Notes`), ideas numbered `M2-001…` so they never collide with Method 1 at the merge.
- **`output/format-swipe.md`** — the pre-screened swipe library (the formats that made it past Step A).
- Everything else is intermediate, in `_work/`.

> **This is a separate pool.** De-duplication and any "does a competitor already have this?" check happen once,
> later, at the cross-method merge where Methods 1, 2, 3 sit together — never inside this method. `Build window`
> (NOW/LATER) is likewise set at the merge, not here.

## File map

```
2-model-other-niches/
  model-other-niches.workflow.md   ← the recipe (owns the Source-1 format table)
  README.md                        ← you are here
  run_model_niches.py              ← the orchestrator (one entry point)
  scripts/  config.py · step_a_swipe · step_b_adapt · step_c_filter · step_d_score · step_e_deliver
  prompts/  a2-extra-formats · a3-prescreen · b-adapt · c-filter · d-score   (one file per LLM call)

projects/<company>/02-asset-engine/model-other-niches/
  output/  model-other-niches-ideas.csv · format-swipe.md
  _work/   swipe.json · adaptations.json · filtered.json · scored.json · run-log.md
```

Shared clients (`config_base.py`, `llm.py`) live in `workflows/02-asset-engine/_shared/`.
