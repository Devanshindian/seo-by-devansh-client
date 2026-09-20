---
type: recipe
reusable: true
reads: clubbed-ideas.csv · research-log.csv · the 4 engines' runners + outputs
produces: per topic — a research blueprint (structure-<slug>.json/.html) + a write-ready bundle (bundle-<slug>.md) + an updated research-log.csv
last_updated: 2026-07-13
---

# Research conductor — one topic → a research blueprint (and, next, a write-ready bundle)

## What this does
Runs the whole RESEARCH phase for ONE topic, unattended: pick → DataForSEO → STORM → gap-check → build_structure
→ (bundle) → log. It invents nothing; it sequences the four engines and threads one topic's identity through them.

## The one rule that governs everything
**The slug is the thread.** The conductor picks ONE topic, remembers its `slug + asset title + angle`, and passes
those to every step; every engine writes under that same `<slug>`. The sheet holds identity + status only; the
clubbed CSV stays the source of truth for idea data (competitor URLs etc. are read live by matching the title).

## What you produce (named output of every step)
- Step 0 → a row in `research-log.csv` (status `in_progress`).
- Step 1 → `dataforseo/out/<slug>/research-doc-<slug>.md` (+ `proof/03-final.json` = primary keyword + spokes).
- Step 1b → the queue row gains `cannibalization` + `cannibalization_url` **only if** we already rank top-10 for the primary keyword (a FLAG; nothing written otherwise).
- Step 2 → `storm/out/<TopicDir>/storm_gen_article_polished.txt` (TopicDir = the primary keyword).
- Step 3 → `gap-check/out/<slug>/gap-check.md` (+ STORM gap-fill iterations).
- Step 4 → `research-structure/out/<slug>/structure-<slug>.json` + `.html` (the blueprint).
- Step 5 → `research-bundle/<slug>/` (**BUILT** — `bundle.py` writes `bundle-<slug>.md` + copies the blueprint).
- Step 6 → `research-log.csv` updated (`research=done`) + this hub's **top `config.MAX_SPOKES` (=3)** ranked spokes inserted right after it. **One level only** — a spoke enqueues no spokes of its own.

## Inputs
- `clubbed-ideas.csv` — the idea cabinet (Asset title = the unique key; Distinct angle; Proof URLs; Reuse verdict).
- `research-log.csv` — the queue/sheet (created on first run).

## The steps, in order
0. **Pick** (`topic_pick.pick_next`) — next `pending` queue row, else pull the next eligible clubbed idea.
   Reuse/tool rules (2026-07-22): a `Tool escalation` idea is NOT written — it's enqueued as a terminal
   `tool-build` marker (a human builds the tool). Writable ideas are pulled in priority order:
   `Reuse verdict ∈ {Brand new, Build from parts}` first, then `Improve existing` LAST (rebuilt from the angle
   for now). The queue row now also carries `format · target_words (= clubbed '# words', the median length of
   pages that rank) · reuse_verdict · chosen_links`, all surfaced in the bundle. Mint a slug; mark `in_progress`.
   *Follows:* the queue model. *Output:* a queue row. *Gotcha:* spokes (source `spoke-of:*`) use the DataForSEO
   direct-input path (`--angle`) so Step 0 skips the clubbed lookup — BUILT (untested end-to-end).
1. **DataForSEO** — `run_dataforseo.py --slug --asset "<title>"`. *Output:* the brief. *Gotcha:* `--asset` is the
   full (unique) title so Step 0 of DataForSEO matches exactly one clubbed row.
   1b. **Cannibalisation flag** (`cannibalization.check`, free) — before we spend on STORM, look the primary
   keyword up in OUR real ranking footprint (00-foundation's `ranked_keywords` pull, cached as
   `_work/our-rankings.json`). If we already rank in the **top `config.CANNIB_RANK_MAX` (=10, page 1)** for it,
   write the exact position + URL onto the queue row so the bundle can warn the team. *Follows:* single source of
   truth — the flag is decided ONCE here and carried forward. *Output:* `cannibalization` / `cannibalization_url`
   on the row (only when we rank). *Gotcha:* it NEVER blocks — we still build; a #11+ (page 2) is not flagged
   because it doesn't actually split our traffic. Off-switch `CANNIB_CHECK=0`.
   2a. **Working spine** (`spine.py`, 2026-08-03) — TWO judgment calls before STORM spends anything:
   (a) extract the three winners lists (gaps to own / common H2s / drift) from the DataForSEO study into
   `proof/07-competitor-read.json`; (b) turn title + angle + brand + those lists into the WORKING SPINE —
   what the article argues, for whom, what the reader can do at the end — plus the about / NOT-about world
   lines. *Output:* `<storm out>/<slug>/spine.json` (title/angle/spine/about/not_about — lives with the
   dossier). *Gotcha:* the "NOT about" line is the wrong-world guard (prize-contest rules ≠ hiring advice);
   later, compare this early spine against the write phase's final spine — same = hunch confirmed, different
   = the evidence changed our mind, vague = warning.
2. **STORM** — `run_storm.py "<subject>" --folder <slug> --spine-file <#2a> --perspectives 4 --article
   --polish` in the STORM venv; conductor starts the shim first. The brief steers the researcher picker
   (builder/sceptic/evidence/practitioner — no Wikipedia route, no 'Basic fact writer'), every question, the
   outline and every section. *Output:* the polished dossier. *Gotcha:* the STORM folder is the SLUG now
   (same as every other engine); pre-2026-08-03 title-mangled folders are auto-migrated by
   `_migrate_legacy_storm_dir` on first touch.
3. **gap-check** — `run_gapcheck.py --slug --brief <#1> --dossier <#2>`. *Output:* the gap report + STORM iterations.
4. **build_structure** — `build_structure.py --slug --asset "<title>" --storm-topic <#2 dir>`. *Output:* the blueprint.
5. **Bundle** — package blueprint + brand-context pointers (**BUILT** — `bundle.py`).
6. **Log** — mark done; insert this hub's `spoke-candidates` right after it in the queue. Spokes arrive **ranked**
   from DataForSEO (`0.5·relevance + 0.25·volume + 0.25·ease`); the conductor keeps only the **top `config.MAX_SPOKES`
   (=3)** (`_spokes()[:MAX_SPOKES]`). **One level only:** if the finished topic is itself a spoke, Step 6 enqueues
   nothing — a spoke never spawns spokes (else the queue grows `3 + 9 + 27…` unbounded).

## Mapping (every step traces to an engine)
| Step | Grounded in |
|---|---|
| 0, 6 | this folder's `topic_pick.py` + the queue model (research-phase-plan.md) |
| 1 | `10-dataforseo/run_dataforseo.py` |
| 1b | this folder's `cannibalization.py` (looks up 00-foundation's `traffic-raw.json` ranking footprint) |
| 2a | this folder's `spine.py` + `prompts/extract-winners.md` + `prompts/build-spine.md` |
| 2 | `11-storm/run_storm.py` (+ `shim.py`, venv, `prompts/pick-researchers.md`) |
| 3 | `12-gap-check/run_gapcheck.py` |
| 4 | `13-research-structure/build_structure.py` |
| 5 | `research-bundle` assembler (`bundle.py`) |

## Rules shelf
- Queue model + build order → `research-phase-plan.md` (repo root).
- Scripted-workflow standard → `~/.claude/conventions/project-structure-conventions.md` rules 4 + 9.
- Unattended ⇒ scripted (cron-able) → `~/.claude/conventions/authoring-principles.md` #10 + #11.

## Gotchas
- STORM is slow (a full article via headless Claude) and gap-check re-runs it to fill gaps — a cold run is tens of
  minutes. That's inherent, not a hang.
- Resume relies on each engine's output file; if an engine changes its output path, update `config.py` here.

## Build / run checklist
- [x] `config.py` — one anchor → all engine paths + outputs + STORM knobs.
- [x] `topic_pick.py` — queue read/write, pick (queue→clubbed), slug, mark_done, insert_spokes.
- [x] `run_research.py` — pure sequencing, shim auto-start, resumable, `== Step N ==`.
- [x] README + this plan.
- [ ] Live end-to-end run on one topic (proves the chain).
- [x] Step 5 bundle (`bundle.py`) wired in.
- [x] Step 1b cannibalisation flag (`cannibalization.py`) — top-10 footprint check, wired + shown in the bundle.
- [x] Spoke direct-input path (`--angle`) — built (untested end-to-end).
