# DataForSEO research engine (self-contained)

The **keyword + SERP + competitor** engine of the research phase. Given one topic (Asset title + distinct angle), it
pulls the keyword universe, scores it, reads the live SERP + AI Overview + competitor pages, and assembles a
**research brief** (`research-doc-<slug>.md`) that the later engines (STORM, gap-check, research-structure)
build on. One command, all steps, resumable. See `research-plan.md` for the full recipe.

## How it works (steps 0-7)
World-aware seeds → expand the keyword net → filter by volume/KD → metrics → score/judge (world-checked) → SERP + AI Overview → read top pages
(LLM-mentions) → assemble the brief. The plumbing/API steps are deterministic code; the judgment steps (seed
scoring, keyword verdict, the write-up) go through headless Claude (`llm.py`, free). Every step writes a named
file under `out/<slug>/proof/`; the next step reads it.

## How to run
```bash
cd scripts
python3 run_dataforseo.py --slug recruiting-metrics-benchmark \
  --asset "Recruiting Metrics Benchmark Report"          # hub: substring-matches the clubbed Asset row
# spoke / direct mode: pass the angle so Step 0 skips the clubbed lookup
python3 run_dataforseo.py --slug <slug> --asset "<full title>" --angle "<distinct angle>"
# resume is automatic (each step reuses its existing output); --redo forces all, --from <0-7> reruns from a step
```
Before spending, a **credit pre-flight** checks the DataForSEO balance and stops cleanly if it's below
`config.MIN_CREDITS` ($1, env-tunable) — leaving the topic un-marked so it resumes after top-up.

## Layout
```
10-dataforseo/
├── research-plan.md        THE RECIPE — the runnable process, steps in order
├── README.md               this file
├── dataforseo-capabilities.md   what the DataForSEO API can/can't do (reference)
├── research-doc-SAMPLE.md  an example assembled brief
├── prompts/                seeds · judge-keywords · score-keywords · serp-snapshot · winners · assemble · notes
└── scripts/
    ├── config.py           ALL paths/settings + thresholds (VOL_FLOOR, KD_CEIL, MIN_CREDITS, …) from one anchor
    ├── dfs.py              the DataForSEO client — the single cred chokepoint (loads scripts/.env) + balance()
    ├── llm.py              headless-Claude JSON/text caller (free, no key)
    ├── run_dataforseo.py   the orchestrator (pure sequencing, steps 0-7, resumable, credit pre-flight)
    ├── s0_seeds.py         Step 0 — anchors + seeds (from clubbed-ideas.csv, or --angle in direct mode)
    ├── s1_expand.py · s1b_ranked.py   Step 1 — expand the keyword net (tight + ranked)
    ├── s2_filter.py        Step 2 — filter by volume / KD
    ├── s3_metrics.py · s3_score.py    Step 3 — metrics + the keyword-scoring panel → 03-keywords.md, spoke-candidates.md
    ├── s4_serp.py · s4b_snapshot.py   Step 4 — SERP + AI Overview → serp-snapshot
    ├── s5_pages.py · s5b_winners.py   Step 5 — read top pages → what the winners cover
    └── s7_assemble.py      Step 7 — assemble research-doc-<slug>.md + research-notes.md
```

## Output
Everything lands under `projects/testlify/03-content-machine/dataforseo/out/<slug>/`:
`proof/` (every step's raw JSON + the readable snapshots) · `research-doc-<slug>.md` (the brief) ·
`research-notes.md`. Never inside this folder (recipe vs output split).

## Dependencies
- `scripts/.env` with `DFS_LOGIN` / `DFS_PW` (chmod 600; master copy in `~/.testlify-access.md`). Balance check:
  `python3 -c "import dfs; print(dfs.balance())"`.
- A headless LLM CLI for the judgment steps — `claude` (default) or `codex`, set via `LLM_PROVIDER` / `config.LLM_PROVIDER` (or `--provider`). Free, no key.
