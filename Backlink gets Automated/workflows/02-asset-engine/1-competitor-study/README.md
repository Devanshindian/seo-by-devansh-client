# Competitor Study — how to run it + the file map

Method 1 of the asset engine: find link-bait ideas by studying the pages that already earn competitors the
most backlinks, and stealing the **format** (the shape), not the topic. The full recipe (the WHAT/HOW, step by
step) lives in [`competitor-study.workflow.md`](competitor-study.workflow.md). This README is just how to run
it and where everything lives.

## Run it

```bash
python run_competitor_study.py --company <slug>
```

That is the whole thing — one resumable command, steps **A → H** in order. `<slug>` (or the `COMPANY` env var)
is the only per-company input. The orchestrator is pure sequencing: it calls each step, skips any whose output
already exists, and **stops at the two human gates** (after A = competitors, after G0 = brand scope) for
approval, then continues on the next run.

| Flag | What it does |
|---|---|
| `--company <slug>` | the company to run (or set `COMPANY=`). Required. |
| `--add "a.com,b.com"` | operator-named competitors, always kept (passed to Step A). |
| `--from <STEP>` | force a re-run from this step onward (e.g. `--from G2`). |
| `--redo` | force every step to re-run. |
| `--yes-gates` | don't stop at the human gates (they're already approved). |

**Credentials** (never in the repo): DataForSEO + Voyage keys are read from `~/.testlify-access.md` (or env).
Steps A and B are **paid** (DataForSEO) and do a pre-flight balance check — a run below `config.MIN_CREDITS`
exits cleanly having spent nothing.

## The steps (each writes one named file the next reads)

| Step | Script | Does | Writes |
|---|---|---|---|
| A | `step_a_competitors.py` | DataForSEO candidates → LLM shortlist of 15 → **human gate** | `output/competitors.md` |
| B | `step_b_pages.py` | pull each competitor's link-earning pages (DataForSEO) | `_raw/<domain>-pages.json` |
| C | `step_c_filter.py` | top 300 by follow-domains, drop junk, dedupe URLs | `_work/candidates/` |
| D | `step_d_format.py` | LLM-tag each page's format | `_work/formats/` |
| F0 | `step_f0_canonical.py` | canonicalise the format vocabulary | `_work/format-canonical.json` |
| E | `step_e_read.py` | scrape full page text (re-execs into Layer 00's extractor) | `_work/read/`, `_work/master.json` |
| F | `step_f_formats.py` | aggregate the format summary | `output/format-summary.csv` |
| G0 | `step_g0_scope.py` | distil the brand scope → **human gate** | `output/brand-scope.md` |
| G1 | `step_g1_sheet.py` | build the per-row reasoning sheet | `_work/g_sheet.json` |
| G2 | `step_g2_reason.py` | per-row LLM reasoning (parallel sub-agents) → asset + angle | `_work/g2_sheet.json` |
| G2.5 | `step_g25_dedup.py` | semantic dedup (Voyage embed → block → LLM SAME/COMBINE/SEPARATE) | `_work/g2_sheet.json` (+ `dedup-report.json`) |
| G3 | `step_g3_ideas.py` | keep specific ideas, rank by pooled follow-domains, add median words | `output/ideas.csv`, `_work/ideas-ranked.json` |
| H | `step_h_deliver.py` | build the two xlsx deliverables | `output/*.xlsx` |

## File map

```
1-competitor-study/                 ← THIS tool folder (company-agnostic)
  competitor-study.workflow.md      ← the recipe (read this)
  README.md                         ← you are here
  competitor-study.html             ← the visual explainer
  run_competitor_study.py           ← the orchestrator (one entry point)
  scripts/
    config.py                       ← all paths + tunables, from one anchor; company = one setting
    step_*.py                       ← one script per step (above)
    enrich_candidates.py, validate_domains.py  ← Step A helpers
  prompts/                          ← one file per LLM call
    shortlist-competitors.md (A) · tag-format.md (D) · canonicalize-formats.md (F0) ·
    g0-brand-scope.md (G0) · g2-reason-rows.md (G2) · g-dedup.md (G2.5)

projects/<company>/02-asset-engine/competitor-study/   ← ALL output (per company)
  output/   ← deliverables only (the two xlsx + ideas.csv, format-summary.csv, competitors.md, brand-scope.md)
  _raw/     ← raw DataForSEO pulls: <domain>-pages.json (one per competitor). Never hand-edited.
  _work/    ← every intermediate (see the workflow doc's folder rule)
```

**The two deliverables:** `competitor-study-ideas.xlsx` (the decision file — Tab 2 is the ranked ideas) and
`competitor-formats.xlsx` (the master evidence, one row per page). Shared clients (`dfs.py`, `voyage.py`,
`llm.py`) live in `workflows/02-asset-engine/_shared/`.
