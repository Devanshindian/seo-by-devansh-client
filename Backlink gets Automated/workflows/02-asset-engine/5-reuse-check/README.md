# Reuse check — do we already own this asset?

Method 5 of the asset engine. Runs AFTER `4-merge`, on the merged `clubbed-ideas.csv`. For every asset
idea it finds the closest existing pages (**RAG**) and lets an **LLM decide** build-vs-reuse — so we don't
rebuild what we already own, and we reuse related pages as research when we do build. Fills the sheet's 6
reuse columns in place; the sheet stays link-only (page text is fetched on demand, never stored inline).

## Run it

```bash
COMPANY=<slug> python run_reuse_check.py --company <slug>
```
One command, two steps: **retrieve → judge**. Resumable (`--from 2`, `--redo`, `--reindex`). Needs
`clubbed-ideas.csv` (from 4-merge) and `content-database.csv` WITH the `Full content` column (from
`00-foundation/1-site-catalogue`). Voyage key from `VOYAGE_API_KEY` or `~/.testlify-access.md`.

| Step | Script | Does | Writes (into clubbed-ideas.csv) |
|---|---|---|---|
| 1 | `step_1_retrieve.py` | Stage 1+2: build/load the two-vector Voyage index (title + body), blended dense retrieve → `rerank-2.5` → top-15; plus the deterministic topic-keyword catalogue | `RAG candidates`, `Topic pages we own`, `Reference links` |
| 2 | `step_2_judge.py` | Stage 3: parallel LLM verdict per idea, reading the top-7 candidates' text fetched by URL from `content-database.csv` | `Reuse verdict`, `Chosen links`, `Why` |

Single source of truth: step 1 owns the first three columns, step 2 the last three. `Chosen links` is
enforced in code to be a **subset** of that idea's RAG candidates — an invented URL is dropped.

## The RAG settings (proven — ported from `rag.py`, do not retune)

| Knob | Value | Meaning |
|---|---|---|
| embed model | `voyage-4-large` | from `_shared/voyage.py` |
| rerank model | `rerank-2.5` | from `_shared/voyage.py` |
| `ALPHA` | 0.5 | title weight in the blended dense score `α·title + (1−α)·best-body-chunk` |
| `N_RETRIEVE` | 40 | dense candidates cast before reranking |
| `TOPK` | 15 | RAG candidate links kept per idea |
| `CHUNK_CHARS` / `OVERLAP` | 4800 / 600 | body chunking |
| `RERANK_DOC_CHARS` | 4000 | per-candidate truncation for the rerank call |

Query = the **Asset title only**, with parentheticals stripped (never the Distinct angle — it drags the
search off-topic). Foreign-language pages (ISO-code first path segment) are excluded from retrieval and the
catalogue. All knobs are env-tunable named constants in `scripts/config.py`.

## The topic catalogue (companion to the RAG match)

RAG is precision (the best few matches); the catalogue is recall (EVERY page we own on the topic). Smart
label + dumb match: one LLM pass emits 1-3 distinctive keywords per asset (`prompts/topic-keywords.md`),
then a deterministic matcher lists every English page whose title/URL contains a keyword (light stemming so
`screening`/`screener`/`screen` collapse), drops over-generic keywords (> 80 pages), and caps the list at
30 with the true count shown.

## File map
```
5-reuse-check/
  run_reuse_check.py · README.md · reuse-check.workflow.md · reuse-check.html
  scripts/  config.py · step_1_retrieve.py · step_2_judge.py
  prompts/  reuse-judge.md · topic-keywords.md
projects/<company>/02-asset-engine/clubbed/
  output/ clubbed-ideas.csv          (the 6 reuse columns filled in place)
  _work/  content-index/ (title/ + body/) · topic-keywords.json · reuse-judge-results.jsonl
          .stage2-retrieved.done · .stage3-judged.done   (orchestrator resume markers)
```
