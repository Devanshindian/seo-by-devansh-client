# Research pipeline scripts

The step scripts for the DataForSEO engine. **How to run + the file map live in `../README.md`; the recipe is
`../research-plan.md`.** Everything runs as one command — `python3 run_dataforseo.py --slug <slug> --asset "…"`
(resumable, steps 0-7) — not the manual per-step invocation this file used to describe. This page keeps only the
setup + the hard-won design notes.

## Setup
- Creds: `scripts/.env` (`DFS_LOGIN`, `DFS_PW`), chmod 600. Master copy in `~/.testlify-access.md`.
- Defaults (market, thresholds, limits): `config.py`.
- Low-level caller: `dfs.py` (`from dfs import call` / `python3 dfs.py /v3/<endpoint>` with a JSON body on stdin).
- Balance / auth check: `python3 -c "import dfs; print(dfs.balance())"`.

## Run
`python3 run_dataforseo.py --slug <slug> --asset "<title>" [--angle "<angle>"] [--redo] [--from <0-7>]` — one
command, all steps, resumable. Each step writes a named file under `out/<slug>/proof/`; the next reads it. See
`../README.md` for the full run notes + file map.

## Key design notes (proven in live runs)
- **Wide net (`keyword_ideas`) dropped** — 0 usable of 652; pure job-search/plumbing/finance noise.
- **Keywords = tight net + ranked net.** Tight net = `keyword_suggestions` per seed (on-topic long-tail).
  Ranked net (`s1b_ranked.py`) = `ranked_keywords` on winning pages (competitor proof-URLs + SERP-of-seed);
  this is the cleaner, richer source (adjacent concepts the seed-nets can't reach).
- **Ambiguous seeds poison the tight net** ("time to fill" → toilet/car-hire) — qualify them in Step 0.
- **AEO:** `llm_mentions` is often noise; cross-check with the AI Overview from `s4_serp.py`.
