# Gap-check — the coverage layer (self-contained)

Given a DataForSEO brief and a STORM dossier for the same topic, it checks whether the dossier already covers
what the brief says matters, and runs up to 2-3 targeted STORM re-runs for the important gaps.
See `gap-check-plan.md` for the full recipe.

## Layout
```
gap-check/
├── gap-check-plan.md   READ THIS FIRST — the recipe, step by step
├── README.md           how to run + this layout
├── prompts/
│   ├── parse-brief.md      Step 0 — read the brief into coverage items
│   ├── coverage-judge.md   Step 1 — per-item coverage judge
│   └── gap-triage.md       Step 2 — spend the 2-3 STORM runs on what matters
├── scripts/
│   ├── config.py           paths + coverage-target policy
│   ├── llm.py              headless-Claude caller + JSON extraction (no API key, no shim)
│   ├── parse_brief.py      Step 0 — brief -> coverage-items.json
│   ├── judge.py            Step 1 — coverage-verdicts.json
│   ├── triage.py           Step 2 — gap-queries.json
│   ├── rerun_storm.py      Step 3 — STORM re-run -> storm/out/<Topic>/iteration-<n>/
│   ├── report.py           Step 4 — gap-check.md
│   └── run_gapcheck.py     the orchestrator (runs 0-4, resumable; --redo forces a full rerun)
└── (outputs) →         projects/testlify/03-content-machine/gap-check/out/<slug>/  (never inside this folder)
```

## How to run
```bash
cd scripts
python3 run_gapcheck.py --slug recruiting-metrics-benchmark \
  --brief   ../../../../projects/testlify/03-content-machine/dataforseo/out/recruiting-metrics-benchmark/research-doc-recruiting-metrics-benchmark.md \
  --dossier "../../../../projects/testlify/03-content-machine/storm/out/Recruiting_metrics_benchmarks/storm_gen_article_polished.txt"
```
Runs all five steps end to end. If the triage finds gaps, it fires the STORM re-runs automatically (starting
STORM's shim if needed) and saves them under `storm/out/<Topic>/iteration-<n>/`.

## Dependencies
- A headless LLM CLI for the three LLM steps — `claude` (default) or `codex`, set via `LLM_PROVIDER` / `config.LLM_PROVIDER` (or `--provider`). Free, no key.
- STORM (sibling `../11-storm/`) for the re-run step; its shim auto-starts.
- Python 3, standard library only.
