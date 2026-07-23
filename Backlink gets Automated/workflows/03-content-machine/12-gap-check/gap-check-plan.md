---
type: recipe (the gap-check layer of the research phase; self-contained)
reusable: yes — one run per topic (hub or spoke)
reads: research-doc-<topic>.md (the DataForSEO brief) + storm_gen_article_polished.txt (the STORM dossier)
produces: projects/testlify/03-content-machine/gap-check/out/<slug>/ — coverage-items.json, coverage-verdicts.json, gap-queries.json, storm-iterations.json, gap-check.md; and gap-fill runs under projects/testlify/03-content-machine/storm/out/<Topic>/iteration-<n>/
last_updated: 2026-07-10
---

# Gap-check plan — does the dossier cover what the brief says matters?

## What this does
For each item the brief says the article must cover, check whether the STORM dossier already has the
substance to write it. For the important ones it doesn't, run STORM again (2-3 targeted queries) to fill
them, then write one report. It steers STORM at real gaps instead of letting it wander.

## The one rule
**A re-run only fires for a real, checkable gap.** Every gap names the brief item it came from and why the
dossier doesn't cover it. No gap → no re-run. Capped at **2-3 queries**, one round only — never a loop.

## What you produce
Everything for the check lands under `projects/testlify/03-content-machine/gap-check/out/<slug>/`; the gap-fill STORM runs land under `projects/testlify/03-content-machine/storm/out/<Topic>/`.

| Step | Output | What it holds |
|---|---|---|
| 0 Read brief | `coverage-items.json` | every coverage-target item: `{id, type, item, context}` + asset title + angle |
| 1 Coverage judge | `coverage-verdicts.json` | per item: `{id, type, item, verdict (covered/partial/no), reason, evidence}` |
| 2 Gap triage | `gap-queries.json` | `{queries: [{query, fills, why}]}` — 0 to 3 STORM queries |
| 3 STORM re-run | `projects/testlify/03-content-machine/storm/out/<Topic>/iteration-<n>/` + `storm-iterations.json` | the gap-fill runs (kept separate; original dossier untouched) |
| 4 Report | `gap-check.md` | the readable roll-up + a pointer to every proof file |

## Inputs
| Input | What | From |
|---|---|---|
| `--slug` | the run folder name | you choose (match the topic) |
| `--brief` | the SAMPLE-shaped research doc | `projects/testlify/03-content-machine/dataforseo/out/<topic>/research-doc-<topic>.md` |
| `--dossier` | the polished STORM dossier | `projects/testlify/03-content-machine/storm/out/<Topic>/storm_gen_article_polished.txt` |

## What we check (and what we don't)
Read straight from the brief:

| Item type | Read from | Judged? |
|---|---|---|
| `secondary_kw` | Keywords → Secondary table | yes |
| `in_body` | Keywords → In-body only | yes |
| `winner_h2` | What the winners cover → Common H2s | yes |
| `gap_we_own` | What the winners cover → Gaps we can own | yes — **the priority** |
| `paa` | SERP snapshot → PAA on-angle | yes |
| `aio_subtopic` | SERP snapshot → AI Overview "what it covers" | yes |
| `aeo_faq` | AI answer landscape | yes, only when there is a usable signal |
| `primary` | Keywords → Primary | parsed but never judged (excluded from JUDGED_TYPES), so never a gap trigger |
| spokes · PAA off-angle · related searches · snippet-holder · "cited by AI" | — | **excluded** (positioning, not dossier substance) |

## The steps, in order

### Step 0 — Read the brief → `coverage-items.json`
`parse_brief.py` sends the brief to an LLM that pulls the coverage-target items above into the JSON schema
(plus the asset title + distinct angle). Reading by meaning, not fixed regex, so a brief that drifts from the
exact SAMPLE formatting still parses.

### Step 1 — Coverage judge → `coverage-verdicts.json`  *(prompt: `prompts/coverage-judge.md`)*
One LLM call **per item**, the whole dossier in each call. The judge gets the asset title + angle, the item,
and the dossier, and returns `covered / partial / no` + a one-line reason + a **verbatim quoted sentence** as
proof. It's told to ignore outside knowledge and quote real dossier text — that's what keeps "covered" honest.

### Step 2 — Gap triage + query writer → `gap-queries.json`  *(prompt: `prompts/gap-triage.md`)*
One LLM call over only the `no` + `partial` items. It drops minor/duplicate misses, prioritises (`gap_we_own`
first, then section-anchoring keywords, then table-stakes H2s, then answer-level items), and clusters the
survivors into **at most 3** comprehensive research questions. Nothing important missing → `{"queries": []}`.

### Step 3 — STORM re-run → `projects/testlify/03-content-machine/storm/out/<Topic>/iteration-<n>/`
For each query, `rerun_storm.py` runs STORM's own runner and moves the fresh run into an `iteration-<n>`
folder inside the original topic's `projects/testlify/03-content-machine/storm/out/<Topic>/` (never overwriting the original dossier). STORM's shim
is auto-started if it isn't already up. No queries → nothing runs.

### Step 4 — Report → `gap-check.md`
Pure assembly: the coverage table, the gaps found, the queries fired and where each was saved, and a pointer
to every proof file. If a cell doesn't trace to an upstream file, it doesn't belong.

## How to run
```
cd scripts
python3 run_gapcheck.py --slug <topic> \
  --brief   ../../../../projects/testlify/03-content-machine/dataforseo/out/<topic>/research-doc-<topic>.md \
  --dossier ../../../../projects/testlify/03-content-machine/storm/out/<Topic>/storm_gen_article_polished.txt
```

## Rules shelf (inputs this consumes — not restated here)
- `projects/testlify/03-content-machine/dataforseo/out/<topic>/research-doc-<topic>.md` — the brief (the item source).
- `projects/testlify/03-content-machine/storm/out/<Topic>/storm_gen_article_polished.txt` — the dossier (what we judge).
- `../../../research-phase-plan.md` — where this layer sits in the research phase.

## Gotchas
- **Self-contained except the re-run.** Steps 0-2 run on a headless LLM CLI — Claude Code (default) or Codex (free, rubric in the prompt
  files). Only Step 3 reaches into STORM, because re-running STORM needs STORM.
- **The judge is the smart part.** No thresholds, no keyword matching — substance judged by an LLM, proven by a
  quoted sentence.
- **The 2-3 cap is a feature.** Scarcity forces the triage to spend re-runs on the angle, not on trivia.
