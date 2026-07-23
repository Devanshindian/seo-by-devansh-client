---
type: recipe (the structure step — the LAST step of the research phase; self-contained)
reusable: yes — one run per asset (hub or spoke); brand-agnostic (paths + creds in config)
reads: STORM dossiers (hub + gap-fill iterations) + each run's url_to_info.json · the DataForSEO brief (research-doc-<slug>.md) + its keyword pool · our own pages (fetched for their REAL headings) · clubbed-ideas.csv
produces: out/<slug>/ — persona.json + cards.json + dropped-cards.json + clusters.json (proof) · structure-<slug>.json (machine source of truth) · structure-<slug>.html (interactive viewer)
last_updated: 2026-07-14
---

# Structure plan — turn all the research into the article's blueprint

## What this does
The last step of the research phase. It takes everything we gathered (STORM evidence, our own pages, the
competitor map, the gaps, the questions) and turns it into the article's **blueprint**: H1 → H2 → H3 → FAQ,
where each section already carries its **evidence**, its **internal + external links**, and its **target
keyword**. `/write` consumes this and just writes.

## The one rule
**Content-first, then keywords. Every section is built from the research, nothing invented; every card lands in
exactly one section (MECE).** The skeleton is built from the rich content (evidence + competitor coverage + gaps +
own pages); keywords are mapped on afterwards. Keywords are tags on sections, never the skeleton. If a section's
content can't be traced to a harvested card, it doesn't belong.

## The unit of work: a "card"
Every source is broken into small **cards**. A card is one atomic idea from one source:

```
{ id, gloss, verbatim | null, source_urls[], internal_link | null, tag }
```
- **id** — a single **continuous** number across ALL sources (STORM cards 1..N, then the first own page N+1.., etc.).
- **gloss** — one short line describing the card. This is the ONLY thing the clustering step reads.
- **verbatim** — the exact source text (copied, not reworded), or `null` for cards that have no underlying text.
- **source_urls** — where the verbatim came from (for external citation).
- **internal_link** — set when the card is one of OUR pages (the page URL, for internal linking).
- **tag** — `storm | ownpage | competitor | gap | question`.

### How the gloss is made (per source)
The gloss always reads the WHOLE chunk it summarises, never just a heading.

| source | gloss | verbatim | source_urls |
|---|---|---|---|
| STORM chunk | **LLM-written**, reading the whole chunk | the chunk text (keeps its `[n]` markers) | resolved from `[n]` via `url_to_info.json` |
| own-page chunk (a heading + its text) | **LLM-written**, reading the whole section text | the section text | the page URL |
| competitor H2 | the heading text itself | `null` | — |
| gap we can own | the gap phrase itself | `null` | — |
| PAA / AI question | the question itself | `null` | — |

## Inputs
| Input | What | From / default |
|---|---|---|
| `--slug` | run folder name | you choose (match the topic) |
| `--asset` | exact Asset title | `clubbed-ideas.csv` → `Asset` |
| STORM dossiers | hub + all gap-fill iterations | `projects/testlify/03-content-machine/storm/out/<Topic>/` + `projects/testlify/03-content-machine/storm/out/<Topic>/iteration-<n>/` |
| STORM citations | the `[n]` → URL maps | each dossier's `url_to_info.json` |
| DataForSEO brief | competitor H2s · gaps · PAA/AI questions | `projects/testlify/03-content-machine/dataforseo/out/<slug>/research-doc-<slug>.md` |
| keyword pool | the broad list already pulled (for the orphan check) | the DataForSEO run's proof files |
| our pages | which pages + their real headings | `clubbed-ideas.csv` (RAG + Topic-pages cols) → fetch each page |
| creds | WordPress API (own pages) + DataForSEO (per-H2 keywords) | `~/.testlify-access.md` |

## What you produce (named output of every step) — everything under `out/<slug>/`
| Step | Output | What it holds |
|---|---|---|
| 1a Pick persona | `persona.json` | the ONE reader persona (from persona.md); carried into the blueprint + reused by the bundle |
| 1 Harvest | `cards.json` | every card from every source, continuous ids, with the verbatim-exists check passed |
| 1b Angle filter | `dropped-cards.json` | off-angle cards dropped before clustering (scored through the persona's eyes); protected cards never dropped |
| 2-3 Cluster + verify | `clusters.json` | card-ids grouped per cluster, MECE-verified (every card used exactly once) |
| 4 Name + split | *(into structure)* | each cluster → H2 (+ H3s), working labels |
| 4c Re-decide differentiator | `differentiator-audit.json` | is_differentiator re-decided per section with angle + competitor/gap context (supersedes the blind clustering flag) |
| 5 Attach | *(into structure)* | evidence + internal/external links under each H2/H3 |
| 6 Keyword | *(into structure)* | target keyword + KD + volume per H2 |
| 7 Orphan check | *(into structure)* | any high-demand keyword no H2 covers → flagged/added |
| 8 FAQ + order | *(into structure)* | FAQ from question cards; H2s ordered |
| 9 Render | `structure-<slug>.json` + `structure-<slug>.html` | machine source of truth + interactive viewer |

## The steps, in order

### Step 0 — Scaffold   ·   *no prompt · no output (setup only)*
`research-structure/` with `scripts/` (config, llm, the step scripts, orchestrator), `prompts/`, `out/`.
`llm.py` = the headless-Claude JSON caller (free, no key); parallel calls = our "subagents".

### Step 1 — HARVEST cards (parallel, continuous ids)
*scripts:* `harvest_storm.py` · `harvest_ownpages.py` · `harvest_brief.py` — *prompts (one per source):*
`harvest-storm.md` · `harvest-ownpage.md` · `harvest-brief.md` — *output:* **`cards.json`**

Each source is read in its own small call so nothing bloats and nothing truncates. Cards are numbered continuously
across sources.
- **`harvest_storm.py`** *(prompt: `harvest-storm.md`)* — for the hub dossier AND every gap-fill iteration
  (STORM 1, 2, 3…, all found automatically): split each dossier on STORM's own
  section headings, and run **one parallel call per section** to emit its cards (gloss LLM-written from the chunk;
  verbatim kept with its `[n]`). Then **code** resolves each `[n]` → source URL via that dossier's `url_to_info.json`.
- **`harvest_ownpages.py`** *(prompt: `harvest-ownpage.md`)* — pull the asset's `RAG candidates` + `Topic pages we own` from `clubbed-ideas.csv`,
  dedupe by URL, **fetch each page live** and convert to markdown-ish (real `##`/`###` headings preserved).
  **Code** splits each page into heading-sections; **one parallel call per page** keeps the real content sections
  (skips nav/footer/related/CTA) and writes a gloss for each. `verbatim` = the **full section text** (code-supplied,
  100% faithful — not LLM-copied); `internal_link` = the page URL; tag `ownpage`.
- **`harvest_brief.py`** *(prompt: `harvest-brief.md`)* — from `research-doc-<slug>.md`, lift competitor common H2s, gaps-we-can-own, and PAA/AI
  questions into cards directly (gloss = the text; `verbatim = null`; tags `competitor` / `gap` / `question`).
- **Code checks (in `harvest_storm.py` / `harvest_ownpages.py`):**
  - *Anti-fabrication* — each STORM verbatim (LLM-produced) is checked as an exact substring of its source
    section; if it isn't there, the card is dropped. Own-page verbatims are code-sliced, so faithful by construction.
  - *Retry, don't skip* — any section or page that yields **0 cards** is re-run up to `config.HARVEST_RETRIES`
    times. If it still yields nothing, it's flagged loudly (`!!`) in the log and named in the harvest summary
    (e.g. "N section(s) produced NO cards after retries: [...]"), so a gap is surfaced, never silently swallowed.

### Step 1a — PICK THE READER PERSONA (single source of truth)
*script:* `pick_persona.py` — *prompt:* `pick-persona.md` — *output:* **`persona.json`** (`{name, lens, why}`)

Pick the ONE persona this asset serves, from the brand's `persona.md` library (its "How to pick" rules), given
the asset title + distinct angle. This is decided **once, here** — the filter (1b) scores every card through this
persona's eyes, `render` embeds it in the blueprint, and the bundle step **reuses** it (never re-picks) so the
research target and the writer's target are the same reader. Brand-agnostic: the library is per-company; if
`persona.md` is missing, it falls back to a generic "practitioner, not academic" reader so nothing breaks.

### Step 1b — ANGLE-RELEVANCE FILTER (drop off-angle cards before clustering)
*script:* `score_cards.py` — *prompt:* `score-cards.md` — *output:* **`dropped-cards.json`** (audit; the kept
cards flow on to clustering)

The biggest lever on blueprint quality. Rich STORM floods the clusterer with off-angle cards (field history,
clinical use, deep academic theory); left unfiltered they become encyclopedia-scale sections. This step scores
**every card** against the asset title + distinct angle and drops the off-angle tail — at the **card** level
(the atomic unit: one idea each), so a good card buried inside an off-angle topic survives on its own merit.
- **Rubric** (`score-cards.md`, brand-agnostic — the reader/angle come from the asset title, distinct angle, and
  `config.BRAND_ONELINER`, never a hardcoded vertical): `relevance` 0-5 — how directly the card helps the reader
  CHOOSE / EVALUATE / INTERPRET / USE the thing the brand offers (5 = a coefficient/threshold/which-fits-which/
  rule/sample; 0 = the field's history, off-topic uses, pure academic theory/math, scholarly debates). The reader
  is framed generically as a practitioner making a real decision, NOT an academic.
- **PROTECT (never dropped, whatever the score):** tag `gap`/`competitor` (handled in code — our differentiators
  + competitive intel); OR the judge marked `protected` (the card carries a number / % / coefficient / threshold
  / statistic, a concrete sample item, or ties a specific option to an outcome). This is load-bearing — it
  rescues the good data buried in off-angle sections (e.g. an adoption stat inside a history section).
- **Drop rule:** `relevance <= config.SCORE_KEEP_THRESH` (default 1) AND not protected. Threshold is
  tunable — 0 is conservative (drops only clear junk), 1 is the default (~35-40% cut). `config.SCORE_FLAG_PCT`
  raises a loud flag if the drop rate is implausibly high.
- **Safe by construction:** deletion happens BEFORE clustering, so nothing downstream can dangle; an unscored
  card defaults to KEEP; cards are redundant by design (harvest is exhaustive), so the same fact usually sits on
  several cards. Every drop is written to `dropped-cards.json` with its score + reason (auditable, like
  `competitor-drops.json`). Resumable: `build_structure.py` reuses `dropped-cards.json` unless `--refilter`.

### Step 2 — CLUSTER all cards
*script:* `cluster.py` — *prompts:* `cluster.md` (grouping); `cluster-merge.md` (only on the two-level path) —
*output:* **`clusters.json`**

One LLM call over the KEPT cards (the off-angle tail was already dropped in Step 1b), seeing only `id + gloss`
(compact — this is the anti-bloat move). Returns groups:
`[{ member_card_ids, is_differentiator }]`. Non-overlapping + complete. **Large sets (> `CLUSTER_SINGLE_MAX`)
switch to two-level:** batch the cards, cluster each batch with `cluster.md`, then merge the batch labels into
final groups with `cluster-merge.md` (one giant call would time out). Cards with no verbatim (gaps, questions,
competitor H2s) cluster on their gloss just like any other card — they contribute *what to cover*; the cluster's
evidence comes from whichever member cards DO have verbatim (STORM, own pages).

### Step 3 — VERIFY MECE (code)
*script:* `cluster.py` (code) — *output:* the validated `clusters.json` (same file, no new one)

Pure code makes MECE a guarantee, not a hope: `_dedupe` keeps each card in its **first** cluster only (drops
any duplicate or unknown id); any cards left unplaced get one **leftover clustering pass**, and anything still
unplaced lands in an explicit **"Unsorted (review)"** bucket; finally a code **`assert`** confirms every card is
placed **exactly once** (none missing, none doubled). No LLM "fix the violation" loop — the guarantee is in code.

### Step 4 — NAME + SPLIT each cluster → H2 (+ H3s)
*script:* `name_clusters.py` — *prompt:* `name-cluster.md` — *output:* **`sections.json`**

**One call per cluster** (small context = just that cluster's cards). Produces the working H2 label and, if the
cluster is big, splits its cards across H3s. Labels are working drafts, NOT final wording (that's `/write`).

### Step 4c — RE-DECIDE the differentiator flag (authoritative)
*script:* `redecide_differentiator.py` — *prompt:* `redecide-differentiator.md` — *output:* **`differentiator-audit.json`**

The `is_differentiator` flag set during clustering is unreliable — the cluster prompt sees only card glosses
(never the asset angle or what competitors cover) and the two-level merge OR-accumulates flags, so it over-fires.
This step **supersedes** it: given the asset's distinct angle + the competitor-covered topics + the gaps we can
own (the `competitor`/`gap`-tagged cards), it re-decides each final section's flag ONCE, strictly (a section is a
differentiator only if it matches our angle or a gap competitors don't cover). Single source of truth for the
flag; kills the blind OR-ratchet. Falls back to the clustering flags if the call fails.

### Step 4b — FILTER competitor sources (code)
*script:* `filter_sources.py` (code) — *no prompt* — *output:* cleaned cards (in-memory) + **`competitor-drops.json`** (audit)

Before attach, strip every competitor citation so none survives into the blueprint. The one authoritative
no-cite list = the **`## Direct competitors`** section of `02-asset-engine/competitor-study/output/competitors.md`
(the direct-competitor domains parsed from `competitors.md` by `competitors.py`, subdomain-aware). Per card: drop competitor URLs; if a card's *only*
source was a competitor → **delete the whole card**; if a legit source remains (mixed) → **keep it, competitor
link removed**; cards with no source (framing/structural) are untouched. Flags loudly if deletions exceed
`COMPETITOR_DROP_FLAG_PCT` (5%). Runs before attach so attach assembles clean sections automatically.

### Step 5 — ATTACH (code)
*script:* `attach.py` (code) — *no prompt* — *output:* evidence + links folded into each section (in-memory; no
separate file — it flows straight into Step 9's render)

Under each H2/H3, collect its cards' `verbatim` + `source_urls` (external links) and `internal_link`s (our pages),
kept as separate lists. Pure assembly by card id — nothing new is written.

### Step 6 — KEYWORD per H2 (DataForSEO)
*script:* `keywords.py` — *prompts (in order):* `h2-seeds.md` (make seeds) → `pick-keyword.md` (pick one) —
*output:* a `target_keyword` (+ KD + volume) on each H2 (in-memory; flows into the render)

For each H2: an LLM splits it into 1-3 **seed phrases** → **`keyword_suggestions`** per seed (the exact call
`10-dataforseo/scripts/s1_expand.py` uses, via the shared `dfs.py`) → keep candidates with **KD < 30 and
volume ≥ 100** → an LLM picks the single best relevant one. Differentiator/gap H2s with no qualifying keyword are
left keyword-free (correct — some of our best sections have no volume).
> **Use `keyword_suggestions`, NOT `keyword_ideas`.** `keyword_suggestions` returns phrases that *contain* the seed
> (on-topic). `keyword_ideas` returns broad associations (seed "cost per hire" → "soc2 compliance cost",
> "consultation fee") — the DataForSEO repo already dropped it as noise. Reuse the repo's method, don't reinvent it.

### Step 7 — ORPHAN CHECK
*script:* `orphan.py` — *prompt:* `orphan.md` — *output:* an `orphan_keywords` list (in-memory; flows into the render)

Against the **brief's existing keyword pool** (already pulled — no new API calls): any HIGH-demand keyword that no
H2 covers is an orphan (a searched topic our content-first build missed). Flag it, and add a candidate H2 if it's
worth one. Safety net for content-first.

### Step 8 — FAQ + ORDER
*script:* `faq_order.py` — *prompt:* `order.md` (FAQ is code, no prompt) — *output:* the `faq` list + the H2s reordered (in-memory)

FAQ = the `question` cards (PAA/AI) — code, no LLM. Order the H2s (one `order.md` call) via the AI Overview
grouping from the brief (logical order if there's no AIO).

### Step 8b — KEYWORD-SET
*script:* `keyword_set.py` — *prompt:* `keyword-set.md` — *output:* **`keyword-set.json`** `{primary, variations[], secondaries[], h2_keywords[], in_body[]}`

The consolidated set the write phase checks the article covers — combining BOTH sources:
- **from the DataForSEO brief** (top-down, one LLM call): **primary + variations** (rewords woven in-body) **+ secondaries + in-body-only**. Variations come from the brief's own `Variations` subsection (DataForSEO Step 3); for older briefs the prompt recovers them from the Primary entry's prose.
- **from the headings** (bottom-up): **`h2_keywords`** = each H2's own target keyword (from Step 6), deduped with vol/KD. So the yellow box shows both the research picks AND what the sections actually target (they overlap only partly, by design — see the orphan check for gaps).

Carried into the blueprint (render) + the bundle + shown in the HTML keyword-set box.

### Step 9 — RENDER
*script:* `render.py` — *no prompt (pure rendering)* — *output:* **`structure-<slug>.json`** + **`structure-<slug>.html`**
- **JSON** — the machine source of truth: `h1`, ordered `h2[]` (each: gloss/label · target_keyword+KD+volume ·
  evidence[] · internal_links[] · external_links[] · h3[]), `faq[]`, `write_guidance` (the §3.2 SEO spec pointers).
- **HTML** — an interactive viewer (STORM-viewer style): hover an **H2** → its keyword + KD + volume; hover the
  **evidence text** → its source links. Read-only.

## Scope note (research doc, not the article)
This produces the COMPLETE, organized menu of sections — it is NOT trimmed to the final 4-7 H2s and NOT refined
(no intro, TL;DR, section answers, or close — those are `/write`). The write phase selects which sections ship and
does the wording. The SEO shape (≤60-char H1, 2-3 keyword-carrying H2s, ≥50% questions, 40-60w answer-first,
primary-kw placement) travels in `write_guidance` for `/write` to apply, we don't pre-apply it.

## Traceability (every output value → its source)
| Value in structure.json | Comes from |
|---|---|
| H2 / H3 labels | Step 4 (named from the cluster's cards) |
| evidence text + external links | the member cards' `verbatim` + `source_urls` (Steps 1, 5) |
| internal links | the member `ownpage` cards' `internal_link` (Steps 1, 5) |
| target keyword + KD + volume | Step 6 (DataForSEO per H2) |
| FAQ | the `question` cards (Steps 1, 8) |
| every card | one named source in Step 1 (`cards.json`) |

## Rules shelf (inputs this consumes — not restated here)
- `storm/storm-plan.md` — the dossiers + `url_to_info.json` citation map.
- `10-dataforseo/research-plan.md` — the brief (competitor H2s · gaps · questions) + the keyword pool.
- `seo-aeo-geo-guidelines.md` §3.2 — the SEO structure spec carried in `write_guidance`.
- `clubbed-ideas.csv` — which of our pages are relevant (RAG + Topic-pages columns).
- `../../../research-phase-plan.md` — where this step sits in the research phase.

## Gotchas
- **STORM is the only source whose verbatim the LLM writes** (asked to copy exactly, then code-checked). Own-page
  verbatim is **code-sliced** from the page (the full section text, never LLM-touched → 100% faithful); the LLM
  there only judges keep/skip + writes the gloss.
- **Own-page boilerplate is dropped in two layers:** code strips `<nav>`/`<footer>`/`<script>`/`<style>`; the LLM
  skips the rest (breadcrumbs, related posts, author box, CTA, subscribe). So own-page text "coverage" reads ~75%
  of the *whole* page — the dropped ~25% is boilerplate, not article content.
- **Split before extracting.** Never one giant call over a whole dossier — output truncates/degrades. One call per
  STORM section and per own page, in parallel.
- **Cluster on the gloss only.** Verbatim never enters the clustering call (bloat) — it's re-attached by id.
- **MECE is verified in code,** not by asking the LLM to review itself.
- **Continuous card ids** across every source + iteration; a code coverage check ensures nothing is skipped.
- **Don't force keywords** on differentiator/gap H2s — no-volume sections are legitimate.

## Build checklist (this doc IS the checklist — tick as each lands)
- [ ] Step 0 — scaffold `structure/` (config, llm, prompts, out).
- [ ] Step 1 — `harvest_storm.py` (split by section · parallel · `[n]`→url via `url_to_info.json` · continuous ids).
- [ ] Step 1 — `harvest_ownpages.py` (pull relevant pages · fetch REAL headings via WP API/live · parallel · glosses LLM-written).
- [ ] Step 1 — `harvest_brief.py` (competitor H2s · gaps · questions → cards).
- [ ] Step 1 — code checks: verbatim-exists + nothing-skipped → `cards.json`.
- [ ] Step 1a — `pick_persona.py` + `prompts/pick-persona.md` (one persona from persona.md) → `persona.json`.
- [ ] Step 1b — `score_cards.py` + `prompts/score-cards.md` (angle-relevance filter through the persona, PROTECT rule) → `dropped-cards.json`.
- [ ] Step 2 — `cluster.py` + `prompts/cluster.md` (gloss-only, MECE) → `clusters.json`.
- [ ] Step 3 — MECE verify (code) + bounded fix loop.
- [ ] Step 4 — `name_clusters.py` + `prompts/name-cluster.md` (one call per cluster → H2/H3).
- [ ] Step 4c — `redecide_differentiator.py` + `prompts/redecide-differentiator.md` (flag re-decided with angle+competitor/gap) → `differentiator-audit.json`.
- [ ] Step 4b — `filter_sources.py` + `competitors.py` (drop competitor citations → `competitor-drops.json`).
- [ ] Step 5 — `attach.py` (evidence + internal/external links by card id).
- [ ] Step 6 — `keywords.py` + `prompts/pick-keyword.md` (DataForSEO per H2, KD<30 & vol≥100).
- [ ] Step 7 — orphan check vs the brief's keyword pool.
- [ ] Step 8 — FAQ from question cards + order via AIO.
- [ ] Step 8b — `keyword_set.py` + `prompts/keyword-set.md` → `keyword-set.json` (primary + variations + secondaries + in-body).
- [ ] Step 9 — `render.py` → `structure-<slug>.json` (incl. `keyword_set`) + interactive `structure-<slug>.html`.
- [ ] Prove Step 1 (STORM harvest) on the real recruiting-metrics dossier before wiring the rest.
