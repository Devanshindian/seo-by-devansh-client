# site-catalogue — run it

One command that catalogues any company's website + its search traffic. Company-agnostic: every
company fact comes from `projects/<company>/company.json`; there is no default company.

## Run

```bash
cd "workflows/00-foundation/1-site-catalogue"
COMPANY=<slug> caffeinate -i venv/bin/python scripts/run_catalogue.py
```

- `--check` — validate the record + print resolved paths, run nothing
- `--from <stage>` — start at a stage (`enumerate-wp` `enumerate-sitemap` `enumerate-archive`
  `enumerate-crawl` `reconcile` `extract` `traffic` `gates`)
- `--redo` — ignore existing stage outputs
- Resumable by design: each stage's output file is its done-marker; the fetch pass resumes from
  the sqlite frontier; the paid traffic pull reuses `_work/traffic-raw.json`.

First-time setup: `uv venv --python 3.11 venv && uv pip install --python venv/bin/python
httpx[http2] protego tenacity lxml url-normalize w3lib trafilatura resiliparse`
(Playwright only if a run reports SPA candidates.) DataForSEO creds (`DFS_LOGIN`/`DFS_PW`) live
in the canonical repo `.env`.

## File map

```
site-catalogue-plan.md      # the recipe — read this first
README.md                   # this file
scripts/
  config.py                 # ALL paths + knobs from one anchor; loads the company record (fail-closed)
  run_catalogue.py          # THE entry point — pure sequencing over the 8 stages
  fetch.py                  # polite HTTP: token bucket, honest UA, robots, raw cache, frontier
  enumerate_wp.py           # layer 1 — CMS API (types derived at runtime, totals asserted)
  enumerate_sitemap.py      # layer 2 — robots Sitemap: lines + platform probes
  enumerate_archive.py      # layer 3 — CDX index + liveness checks
  enumerate_crawl.py        # layer 4 — BFS, only when the others are thin
  reconcile.py              # union + provenance + canonical collapse + soft-404 drops
  extract.py                # the extractor stack + escalation ladder (offline over the cache)
  traffic.py                # bulk DataForSEO pull -> top-pages.csv + catalogue join
  gates.py                  # the three run-failing gates + catalogue-report.md
  vendor/                   # vendored pieces only (currently none)
venv/                       # python 3.11 + deps (gitignored)
```

Output (never in this folder): `projects/<company>/content-database/`
- `output/content-database.csv` — the catalogue (URL · Type · Title · Description · Full content
  · Traffic · Intent · canonical · word_count · modified · lang · source · extractor · body_status)
- `output/top-pages.csv` — URL · Traffic · Traffic_clean · Top Keyword · Primary Intent · Market
- `output/catalogue-report.md` — gates verdict, per-type coverage, provable gaps
- `_work/` — the per-stage evidence files + `catalogue.sqlite` (frontier/cache metadata)
- `_raw/<sha[:2]>/<sha>.html` — content-addressed raw payloads (extractor changes never refetch)

## Downstream consumers (contract holders)

- reuse-check (RAG) — embeds `Full content` (heading markers inline)
- style-guide + features — read `URL`/`Traffic`/`Full content` by column name
- writing-examples — reads `top-pages.csv` (`URL` · `Traffic` · `Top Keyword` · `Primary Intent`)
- 13-research-structure `harvest_ownpages.py` — reads bodies from the catalogue via `CONTENT_DB`
