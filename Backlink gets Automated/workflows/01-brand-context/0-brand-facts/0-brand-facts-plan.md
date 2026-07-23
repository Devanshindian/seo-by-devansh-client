---
type: recipe (runnable process — the brand-facts intake builder)
reusable: any company (COMPANY is one setting; the templates carry {{BRAND}}/{{NICHE}} slots)
reads: projects/<company>/company.json · projects/<company>/00-foundation/output/content-database.csv (Layer 00)
produces: brand-context/stats.md · opinions.md · stories.md (instantiated; SEED once confirmed) + brand-context/_drafts/stats-draft.md · stories-draft.md (machine drafts, ⚠️ everything)
last_updated: 2026-07-19
---

# 0-brand-facts — the company's real numbers, stories and opinions, asked once and kept forever

## What this does
Instantiates the three brand-facts files for a company and machine-drafts what the company's own website
already publishes (its numbers, its customer stories), so the human gate is a CONFIRM job, not a from-scratch
writing job. Opinions are interview-only — the machine never drafts one.

## The one rule that governs everything
**The machine never writes the real files after instantiation, and never invents a fact.** Drafts live in
`_drafts/`, every entry marked ⚠️ with the URL it came from. Only a human moves a row into `stats.md` /
`stories.md` (dropping the ⚠️) or answers `opinions.md`. Once confirmed, the files are SEED — a rerun
re-USES them (instantiate skips existing files), never regenerates them.

## What you produce
| Step | Named output |
|---|---|
| 1 instantiate | `brand-context/stats.md` · `opinions.md` · `stories.md` (from `templates/`, brand slots filled; skipped if present) |
| 2 draft stats | `brand-context/_drafts/stats-draft.md` — candidate numbers, bucketed scale/results/credibility, each ⚠️ + source URL + verbatim quote |
| 3 draft stories | `brand-context/_drafts/stories-draft.md` — candidate anecdotes in stories.md's own format, each ⚠️ + source URL |
| the gate (human) | confirmed rows merged into the real files; opinions answered |

## Inputs
- The company record (`company.json`) — brand, niche, domain. Fail-closed: no record, no run.
- The site catalogue (Layer 00) — `Full content` + `Type` per page. Fail-closed: no catalogue, no run.

## The steps, in order
1. **Instantiate** — `instantiate.py`. Templates → `brand-context/`, `{{BRAND}}`/`{{NICHE}}` filled from the
   record. Existing file = SEED = untouched. *Gotcha: this runs at its SKILL.md stage (Layer 01 step 0),
   never as loose setup code.*
2. **Draft stats** — `draft_stats.py`. Candidates = the homepage + top-`BF_STAT_TOP` `page`-type rows by
   Traffic + every `certifications` page (`BF_STAT_TYPES`). One LLM call per page with the keep/drop criteria
   in `prompts/extract-stats.md`; script dedupes and assembles (pure assembly). *Gotcha: a Type missing from
   this CMS = zero candidates = a reported skip, never a crash.*
3. **Draft stories** — `draft_stories.py`. Candidates = every `successstory` / `press-release` / `podcast`
   page (`BF_STORY_TYPES`). One call per page via `prompts/extract-stories.md`; a page with no real actor or
   change returns null and is dropped.
4. **The gate (human)** — review `_drafts/`, merge confirmed rows, answer the opinion interview.

## Mapping table (where each rule comes from)
| Step | Grounded in |
|---|---|
| never-invent / ⚠️-until-confirmed | the templates' own rule headers (carried from the hand-built Testlify originals) |
| machine drafts, human confirms | revamp plan 1.1 producer pattern |
| criteria live in the prompt | building-workflows J2 |
| one output file per step, resumable | building-workflows S2 / structure C3-C4 |
| seed vs artifact | revamp plan Rule 2 (the regeneration test) |

## Rules shelf
`~/.claude/conventions/building-workflows.md` (F1-F5, J2, S1-S2) · `project-structure-conventions.md` (B, C1-C5)
· `revamp-phase-plan.md` 3.2 EXPANDED block (this builder's decision record).

## Gotchas
- `BF_STAT_TYPES` / `BF_STORY_TYPES` defaults were chosen on Testlify's CMS types — a new company's types
  come from ITS catalogue's Type column; tune the env vars, don't edit code.
- The drafts overwrite on `--redo-drafts` — the REAL files never do.
- ~30-90 LLM calls per company on the local CLI: free, but minutes, not seconds.

## Run checklist
- [ ] Layer 00 catalogue exists for this company
- [ ] `COMPANY=<slug> python3 scripts/run_brand_facts.py`
- [ ] Review `_drafts/stats-draft.md` — merge confirmed rows into `stats.md`, drop their ⚠️
- [ ] Review `_drafts/stories-draft.md` — approve into `stories.md`, sign each
- [ ] Answer `opinions.md`'s interview with the team
- [ ] Confirm the three real files read as SEED (rule headers intact, no ⚠️ left on confirmed rows)
