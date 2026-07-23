---
name: seo-foundation
description: The backlink machine for any company. Four layers, numbered in run order. 00-foundation - the site-catalogue engine catalogues every page + its search traffic in one command. 01-brand-context - the one-time builders that learn how the company writes + what it sells. 02-asset-engine - build a free asset other sites link to. 03-content-machine - research each chosen topic into a write-ready bundle (the /research pipeline, once per topic). Layers 00-02 run once per company, in order; 03 then runs per topic. All outputs land under projects/<company>/.
---

# Backlink Machine

A reusable machine that earns backlinks for any company. **Four layers, numbered in run order** —
the number of a folder IS its stage:

| Layer | What it does | Runs |
|---|---|---|
| **00-foundation** | learn the company's PAGES — every page it has + its search traffic | once per company |
| **01-brand-context** | learn how the company TALKS + what it SELLS — the builder files every later step reads | once per company |
| **02-asset-engine** | build one genuinely useful **free asset** other sites *choose* to link to, then funnel that authority to the money pages | once per company |
| **03-content-machine** | research each chosen topic into a **write-ready bundle** | once per **topic** |

**One-time vs per-topic:** layers 00-02 are built **once per company**. After that, every new article just
runs the research pipeline (`/research`) on the next topic — you never redo the foundation or the builders.

All outputs go under `projects/<company>/`.

---

# Layer 00 - Foundation

Set up a company. Works for any company. All outputs go under `projects/<company>/`.

## Step 1 - Site Catalogue (one command: every page + its search traffic)
Catalogue the company's whole website and how it earns search traffic. Replaces the two retired
steps (the WordPress-only content database and the manual Semrush browser export).
- ONE command, driven entirely by the company record: `COMPANY=<slug> python3 run_catalogue.py`.
- Enumerates pages from FOUR independent sources (CMS API, sitemaps, public web archive,
  link crawl), unions them with provenance, fetches politely through a raw cache, extracts every
  body with a multi-extractor stack (headings kept inline as #/##/### markers), pulls ranked
  keywords from DataForSEO in one bulk call, and FAILS loudly if coverage gates aren't met.
- Scripts: `workflows/00-foundation/1-site-catalogue/scripts/` (`run_catalogue.py` is the entry).
- **Full steps:** `workflows/00-foundation/1-site-catalogue/README.md`.
- **Output:** `projects/<company>/00-foundation/output/`:
  `content-database.csv` (one row per page: URL, Type, Title, Description, **Full content**,
  Traffic, Intent, canonical, word_count, modified, lang, source, extractor, body_status),
  `top-pages.csv` (URL, Traffic, Traffic_clean, Top Keyword, Primary Intent, Market) and
  `catalogue-report.md` (coverage per type, gates, provable gaps). `Full content` is the page's
  entire clean text - it's what the asset-engine **reuse check** runs RAG against.

## Step 2 - (retired) Brand Brain
**Retired 2026-07-19** — its three jobs live elsewhere now: the page shortlist + saved pages are the
FIRST STEP of brand-voice (Layer 01) and sit at `projects/<company>/01-brand-context/`
(`page-shortlist.md` + `_pages/`); `stats.md` / `opinions.md` / `stories.md` (interview-sourced SEED —
preserved, never regenerated) live in the same `brand-context/` folder and are built by the
`0-brand-facts` intake builder; `brand-scope.md` derives from brand-voice + features + the company
record (competitor-study G0, same human gate). The old folder and the voice-analyser are deleted;
competitor-study's Step E re-execs into **Layer 00's site-catalogue extractor** (the 5-rung ladder), so it
has no page extractor of its own.

---

# Layer 01 - Brand Context

Seven builders that learn how the company writes + what it sells, producing the reference files the
asset engine and the write phase read. Build once per company, in numbered order. Outputs land in
`projects/<company>/01-brand-context/`.

**Every builder is ONE command.** Run them in this order (each writes its real file in place —
`git diff` is the review surface). All commands are run from the builder's own folder:

```bash
cd workflows/01-brand-context/<builder>
COMPANY=<slug> python3 scripts/<the command below>
```

| # | Builder | Command | Writes | Human gate |
|---|---|---|---|---|
| 0 | Brand facts (intake) | `run_brand_facts.py` | `stats.md` · `stories.md` · `opinions.md` | confirm the ⚠️ rows; answer the opinion interview |
| 1 | Brand voice | `run_brand_voice.py` | `brand-voice.md` | review the diff; confirm `_work/brand-voice/oneliner-draft.json` into `company.json` |
| 2 | Style & mechanics | `run_style_guide.py` | `style-guide.md` | review the diff; the `[COMPANY]` lines say "confirm with marketing" |
| 3 | Product facts | `run_features.py` | `features.md` | review the diff; fill `_seed/features-seed.md` with any JS-rendered facts (e.g. a price table) |
| 4 | Worked examples | `run_writing_examples.py` | `writing-examples.md` | review the diff |
| 5 | Reader persona | `run_persona.py` | `persona.md` | recipe Step 3: edit/approve the personas |
| 6 | Author voices | `instantiate.py` | `voices.md` (questionnaire) | **fill it with the team** — real people only, never machine-drafted |

**Order matters:** 0 and 1 first — brand-voice is the yardstick builders 2-5 read. Builder 6 is a
questionnaire the machine never answers.

**Deep recipes** (what each builder actually does, its schema and its rules) live beside each command:
`0-brand-facts/0-brand-facts-plan.md` · `1-brand-voice/brand-voice.workflow.md` ·
`2-style-guide/style-guide.workflow.md` · `3-features/features.workflow.md` ·
`4-writing-examples/writing-examples.workflow.md` · `5-persona/persona.workflow.md` ·
`6-voices/voices.workflow.md`

**Write-time rules are NOT builders** — the SEO/AEO/GEO checklist, the writing-integrity contract and the
avoid-AI-writing check are static rule files that ride into each research bundle. They live with the
pipeline that enforces them: `03-content-machine/reference/` (see Layer 03).

---

# Layer 02 - Asset Engine

Build one free asset other sites *choose* to link to - the **reverse-silo**: external links -> the asset
-> internal links -> the money pages. Six stages, D0-D5. Full recipe: `02-asset-engine.workflow.md`.
Outputs go under `projects/<company>/02-asset-engine/`.

## D1 - Idea Backlog (built)
Three methods, each a deep recipe in `02-asset-engine/`, each producing its **own** idea pool.
They share one ownership anchor - **`brand-scope.md`** (derived from brand-voice + features + the company record, user-approved) - so the
three pools can be compared and merged. Run all three, then **merge them into one sheet** (next section).

### Method 1 - Competitor Study
**What it is:** steal the formats that already earn competitors the most backlinks (the shape, not the topic),
and build our own version on a subject we own.
**Full steps:** `02-asset-engine/1-competitor-study/competitor-study.workflow.md` (+ `README.md` for how-to-run)
**Run:** `python workflows/02-asset-engine/1-competitor-study/run_competitor_study.py --company <slug>` — one resumable command, steps A→H, stops at the A and G0 human gates. DataForSEO + Voyage keys from `~/.testlify-access.md`.
**Output:** `projects/<company>/02-asset-engine/competitor-study/output/competitor-study-ideas.xlsx` - Tab 2 (Ideas) is the one we use.
**Columns (Tab 2):** `# · Build window · Brand fit · Asset · Format · Distinct angle · Total domains · # comps · # pages · Median words · Backing URLs`

### Method 2 - Model Other Niches — ✅ format-honesty fixed (2026-07-22)
**Status:** included in the merge (`INCLUDE_M2=True`). It still imports proven cross-niche formats, but the
`b-adapt.md` prompt now follows Method 1's rules: the asset title carries no shape-words, and anything needing
a real build (interactive tool / our own original data / new primary research) is flagged in the
`Tool escalation` column — so the write phase picks only the desk-doable ideas and genuine tool ideas are
labelled for a human. See `format-honesty-fix-plan.md`.
**What it is:** import proven link-bait formats from other industries that no competitor in our niche has
built yet, and adapt each one on-brand.
**Full steps:** `02-asset-engine/2-model-other-niches/model-other-niches.workflow.md` (+ `README.md` for how-to-run)
**Run:** `python workflows/02-asset-engine/2-model-other-niches/run_model_niches.py --company <slug>` — one resumable command, steps A→E. No API, no gates. Reads `brand-scope.md` (Method 1) + brand context.
**Output:** `projects/<company>/02-asset-engine/model-other-niches/output/model-other-niches-ideas.csv`
**Columns:** `Idea # · Method · Brand fit · Asset · Format · Our topic · Distinct angle · Source niche · Evidence URLs · Beatability · Effort · Notes`

### Method 3 - Study Trends
**What it is:** read what the niche is fired up about right now on Reddit, distil it into recurring tensions,
and shape each into a timely asset idea.
**Full steps:** `02-asset-engine/3-study-trends/study-trends.workflow.md`
**Output:** `projects/<company>/02-asset-engine/study-trends/output/study-trends-ideas.csv`
**Columns:** `Tension · Asset title · What it'd be · Brand fit · Unfair advantage · # posts · Audience · Emotion · Best example URL`

## Method 4 - Merge the pools into one sheet (scripted)
Once the methods are done, club them into one CSV. (Method 2 is on hold, so this is M1 + M3 by default.)
**Run:** `python workflows/02-asset-engine/4-merge/run_merge.py --company <slug>` (+ `README.md`).
Three steps: **stack** (map each method's columns into the shared schema) → **dedup** (embed → block → LLM
adjudicate → merge the ideas that repeat *across* methods) → **relevance recheck** (`step_3_relevance.py`, a
final atomic gate that removes obvious nonsense / off-brand ideas — runs in PROPOSE mode, writes
`_work/relevance-drops.json`; a HUMAN approves, then `--apply` removes them; conservative, protects
high-backlink ideas, refuses to apply if it wants to cut > the cap). A repeat found by two methods becomes ONE
row whose **Sources** column records "M1 + M3" (a stronger bet), pooling both proofs. Same Voyage
entity-resolution as the competitor-study dedup; conservative. Sorted by Brand fit then each idea's own strength.
**Output:** `projects/<company>/02-asset-engine/clubbed/output/clubbed-ideas.csv`

**Columns** (blank where a column doesn't apply to that method):
`Sources · Brand fit · Asset · Format · Tool escalation · Distinct angle · What it'd be · # pages · # words ·
Total domains · # comps · # posts · Beatability · Effort · Proof URLs` + the reuse-check placeholders
(`RAG candidates · Topic pages we own · Reference links · Reuse verdict · Chosen links · Why`, filled by Method 5).
**`Tool escalation`** = empty for normal article ideas; a one-line reason only when the format genuinely needs
a build (a real tool/test page, or an angle that truly requires interactivity). The format-honesty rule:
G2 copies the competitor's format and never invents a tool to differentiate; the differentiator is a content
gap a writer can close from public sources (`format-honesty-fix-plan.md`).
Mapping notes: M3's `Asset title → Asset` (the research key); M3 has no distinct-angle column so its
`Unfair advantage` (tension-prefixed) fills `Distinct angle`. **What the research phase reads:** Asset,
Distinct angle, Proof URLs, RAG candidates, Topic pages we own, Reuse verdict — the rest is context.

## Method 5 - Reuse check - do we already have it? (D2)
Runs on the merged `clubbed-ideas.csv`. **Scripted** (`02-asset-engine/5-reuse-check/`):
`COMPANY=<slug> python run_reuse_check.py --company <slug>` — Stage 1 `step_1_retrieve.py` (builds/REUSES a
two-vector content index of the company's own pages, then per-idea retrieve + topic catalogue), Stage 2
`step_2_judge.py` (per-idea LLM verdict). The page-index is cached and reused across runs unless forced, so a
re-run over changed ideas only redoes the idea-side lookup + judge.
Before building anything, match every idea in `clubbed-ideas` against the company's **existing content** (the
`Full content` in the content database) - **Voyage (`voyage-4-large`) two-vector retrieval (title + body,
blended) → `rerank-2.5` → top 7 pages**, then **parallel LLM sub-agents (one idea each)** read them and judge.
Fills, in `clubbed-ideas.csv`: **RAG candidates** + **Candidate 1–7 content** (the
candidates' full text, pasted inline) in Stage 2, then **Reuse verdict** (Already have it / Improve existing /
Build from parts / Brand new) **· Chosen links · Why** in Stage 3. So you never rebuild what already exists,
and you reuse existing research when you do build.

**Outputs (under `projects/<company>/02-asset-engine/clubbed/`):**
- `clubbed-ideas.csv` — the full scored + reuse-checked pool (includes the bulky `Candidate 1–7 content` columns).
- `clubbed-ideas-review.csv` — the lean **review copy** (same file minus the content columns), opens cleanly.
- **A web viewer** — a self-contained `index.html` (search · filter · expand · Keep/Maybe/Cut + CSV export),
  published to a **public GitHub Pages URL** (personal account, randomised repo name, push-clone kept in
  `clubbed/output/_pages-repo/`) so a reviewer just opens one link. Built from the review CSV; on later runs, **update
  the same repo's `index.html` — never create a second repo / link**.

**Full steps:** `02-asset-engine/5-reuse-check/reuse-check.workflow.md` (+ `README.md`).

---

# Layer 03 - Content Machine

Turn each chosen idea into a **write-ready bundle** the writer can pick up. Lives under
`workflows/03-content-machine/`; all outputs under `projects/<company>/03-content-machine/`.
Runs **once per topic** off `clubbed-ideas.csv` — the per-topic layer, after 00-02 are in place.

## The research pipeline (once per topic) - `/research`
**What it is:** one command researches the next topic end to end and hands the writer a bundle. It picks the next
topic, runs the four research engines, builds the blueprint, packages the write-ready bundle, logs it done, and
queues that topic's spokes. **Resumable** - a step is skipped if its output already exists; safe to Ctrl-C and
re-run.

**Run:** `python3 workflows/03-content-machine/14-research-conductor/scripts/run_research.py` (auto-picks the next
topic; `--asset "..."` forces one). **Full steps:** `03-content-machine/14-research-conductor/research-conductor-plan.md`.

**The chain (per topic):**
| Step | Does | Engine | Output |
|---|---|---|---|
| 0 | pick topic + tick the sheet | `topic_pick.py` | a row in `research-log.csv` |
| 1 | keyword + SERP + AI-answer brief | `10-dataforseo` | `dataforseo/out/<slug>/research-doc-<slug>.md` |
| 2 | deep evidence dossier | `11-storm` | `storm/out/<TopicDir>/…polished.txt` |
| 3 | fill gaps the brief needs but STORM missed | `12-gap-check` | `gap-check/out/<slug>/gap-check.md` |
| 4 | the article blueprint | `13-research-structure` | `research-structure/out/<slug>/structure-<slug>.json` + `.html` |
| 5 | the write-ready bundle | `bundle.py` | `research-bundle/<slug>/bundle-<slug>.md` |
| 6 | log done + enqueue spokes | `topic_pick.py` | updated `research-log.csv` |

**The queue (`projects/<company>/03-content-machine/research-log.csv`):** the source of truth for *status*
(`clubbed-ideas.csv` stays the source of truth for *idea data*). Pull-based: pick the next `pending` row (a
topic's spokes sit right after it - depth-first); if none pending, pull the next eligible idea from
`clubbed-ideas.csv`. One topic per run. **Reuse/tool handling (2026-07-22):** a `Tool escalation` idea is never
written — it's enqueued as a terminal `tool-build` marker (a human builds it). Writable ideas are pulled in
priority order: `Brand new` / `Build from parts` first, `Improve existing` LAST (rebuilt from the distinct angle
for now). The queue now also carries `format`, `target_words` (clubbed `# words` = median length of what ranks),
`reuse_verdict`, `chosen_links` — surfaced in the write-ready bundle's "at a glance" block.

## `reference/` - the write-time rules (not builders, not per-company)
Static rule files the bundle points at; the write phase reads them in place:

| File | Role | Per company? |
|---|---|---|
| `reference/seo-aeo-geo-guidelines/seo-aeo-geo-checklist.md` | SEO/AEO/GEO structure checklist | **No — a pointer.** Never copied (a byte-identical copy is only a drift risk). |
| `reference/writing-integrity/writing-integrity.md` | the honest + distinctive writing contract | **Template → instance.** Has a real brand slot; each company gets an instantiated copy in `brand-context/` (instantiation to be scripted — revamp plan 3.0a). |
| `reference/avoid-ai-writing/SKILL.md` | the final anti-AI writing pass | **No — a pointer**, applied at write time. |

**Deep dives per engine:** `10-dataforseo/README.md` · `11-storm/README.md` · `12-gap-check/README.md` ·
`13-research-structure/README.md` (where the blueprint is built) · `14-research-conductor/scripts/bundle.py`.

**The flow, one line:** `clubbed-ideas.csv` (a chosen topic) → DataForSEO brief → STORM dossier → gap-fill →
blueprint → **write-ready bundle** → (write phase).
