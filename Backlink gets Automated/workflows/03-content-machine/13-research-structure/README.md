# Research-structure (self-contained)

The **last step of the research phase**. Turns all the research for one asset (STORM evidence, our own pages,
the DataForSEO brief) into the article's blueprint: H1 → H2 → H3 → FAQ, where each section already carries its
evidence, internal + external links, and target keyword. `/write` consumes this.
See `structure-plan.md` for the full recipe.

## How it works (persona → cards → filter → clusters → sections)
First we pick the ONE **reader persona** this asset serves (Step 1a, from the brand's `persona.md`) — decided
once here and reused by the bundle so research and writing target the same reader. Every source is then broken
into small **cards** (`{id, gloss, verbatim, source_urls, internal_link, tag}`, continuous ids). An
**angle-relevance filter** (Step 1b) scores each card **through that persona's eyes** (against the asset's title +
distinct angle) and **drops the off-angle tail** (field history, off-topic use, deep academic theory) BEFORE
clustering — the biggest anti-bloat lever — while PROTECTING any card carrying hard data (a
number/coefficient/threshold/stat/sample item) or tagged `gap`/`competitor`. Every drop is logged to
`dropped-cards.json`. Clustering reads only the one-line
**gloss** (anti-bloat) and groups the surviving cards into **MECE** sections (every card in exactly one, verified
in code). Each cluster is named into an H2/H3, evidence + links attach by id, a fresh DataForSEO lookup picks a
target keyword per H2, and it renders to JSON + an interactive HTML viewer.

## Layout
```
research-structure/
├── structure-plan.md    READ FIRST — the recipe
├── README.md
├── prompts/             pick-persona · score-cards · harvest-storm · harvest-ownpage · harvest-brief · cluster · cluster-merge · name-cluster · redecide-differentiator · pick-keyword · orphan · order · keyword-set · h2-seeds
├── scripts/
│   ├── config.py · llm.py
│   ├── pick_persona.py       Step 1a — pick the ONE reader persona from persona.md (persona.json)
│   ├── harvest_storm.py      Step 1 — STORM dossiers -> cards ([n] -> url via url_to_info.json)
│   ├── harvest_ownpages.py   Step 1 — our pages, fetched for REAL headings -> cards
│   ├── harvest_brief.py      Step 1 — competitor H2s / gaps / questions -> cards
│   ├── score_cards.py        Step 1b — angle-relevance filter through the persona: drop off-angle cards (dropped-cards.json)
│   ├── cluster.py            Step 2-3 — MECE clustering, verified in code
│   ├── name_clusters.py      Step 4 — cluster -> H2 (+ H3s)
│   ├── redecide_differentiator.py  Step 4c — re-decide is_differentiator with angle+competitor/gap (differentiator-audit.json)
│   ├── filter_sources.py     Step 4b — drop competitor citations (competitor-drops.json)
│   ├── competitors.py        (helper) parse the direct-competitor domains from competitors.md
│   ├── attach.py             Step 5 — evidence + internal/external links by id
│   ├── keywords.py           Step 6 — DataForSEO target keyword per H2
│   ├── orphan.py             Step 7 — high-demand keyword no H2 covers
│   ├── faq_order.py          Step 8 — FAQ from question cards + order H2s
│   ├── keyword_set.py        Step 8b — primary + variations + secondaries + in-body (keyword-set.json)
│   ├── render.py             Step 9 — structure-<slug>.json + .html
│   └── build_structure.py    the orchestrator (Steps 1-9)
└── out/<slug>/          persona.json · cards.json · dropped-cards.json · clusters.json · competitor-drops.json · keyword-set.json · structure-<slug>.json · structure-<slug>.html
```

## How to run
```bash
cd scripts
python3 build_structure.py --slug recruiting-metrics-benchmark \
  --asset "Recruiting Metrics Benchmark Report: Time-to-Hire, Cost-per-Hire & Quality-of-Hire by Industry, Role & Company Size" \
  --storm-topic "../../../../projects/testlify/03-content-machine/storm/out/Recruiting_metrics_benchmarks"
# add --skip-keywords to skip the paid DataForSEO per-H2 step
```

## Dependencies
- A headless LLM CLI for the LLM steps — `claude` (default) or `codex`, set via `LLM_PROVIDER` / `config.LLM_PROVIDER` (or `--provider`). Free, no key. Parallel calls = "subagents".
- The sibling `10-dataforseo/scripts/dfs.py` + its `.env` for the per-H2 keyword step.
- Live web fetch (our own pages) — standard library only.
