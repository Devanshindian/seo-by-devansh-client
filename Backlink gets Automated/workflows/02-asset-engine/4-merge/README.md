# Merge — club the 3 idea pools into one deduped sheet

The step after the three idea-generating methods. It **stacks** M1 (competitor study) + M2 (model other
niches) + M3 (study trends) into **one sheet**, then **de-duplicates across methods** (the same idea surfaced
by two methods becomes one row that records "found by M1 + M3" — a stronger bet, not a discarded copy).
Output: `clubbed-ideas.csv`, which the research phase reads directly. Reuse-check (Method 5) runs on it after.

## Run it

```bash
python run_merge.py --company <slug>
```
One command, two steps: **stack → dedup**. Resumable (`--from 2`, `--redo`). Needs the three method
deliverables to exist first. Voyage key from `~/.testlify-access.md`.

| Step | Script | Does | Writes |
|---|---|---|---|
| 1 | `step_1_stack.py` | map each method's columns into the shared schema (deterministic) | `_work/stacked.json` |
| 2 | `step_2_dedup.py` | embed → block → LLM adjudicate (SAME/COMBINE/SEPARATE) → merge, pooling sources + proof | `output/clubbed-ideas.csv` |

## The merged schema

```
Sources · Brand fit · Asset · Format · Distinct angle · What it'd be ·
# pages · # words · Total domains · # comps · # posts · Beatability · Effort · Proof URLs ·
RAG candidates · Topic pages we own · Reference links · Reuse verdict · Chosen links · Why
```
- **Shared** (every idea): Sources, Brand fit, Asset, Distinct angle.
- **Method-specific** (blank where N/A): # pages/# words/domains/comps (M1), Beatability/Effort (M2), # posts (M3).
- **Reuse-check placeholders** (last 6, filled by Method 5): RAG candidates … Why.

**What the research phase actually reads:** `Asset` (the key), `Distinct angle`, `Proof URLs`, `RAG candidates`,
`Topic pages we own`, `Reuse verdict`. The rest is prioritisation/human context. Mapping notes:
- M3's `Asset title` → `Asset` (load-bearing — the research key).
- M3 has no distinct-angle column; its `Unfair advantage` (prefixed with the tension) fills `Distinct angle`.
- `Reuse verdict` etc. stay blank here — Method 5 (reuse-check) fills them.

## Dedup — same entity-resolution as the competitor-study dedup
Embeddings only NOMINATE near-matches (looser threshold cross-method, since a backlink-idea and a Reddit-idea
are worded differently); the LLM decides SAME / COMBINE / SEPARATE. Conservative — merges only true repeats.
Knobs in `config.py`: `DEDUP_THRESHOLD`, `DEDUP_TOPK`, `DEDUP_MAX_CLUSTER`, `DEDUP_WORKERS`.

## File map
```
4-merge/
  run_merge.py · README.md
  scripts/  config.py · step_1_stack.py · step_2_dedup.py
  prompts/  merge-dedup.md
projects/<company>/02-asset-engine/clubbed/
  output/ clubbed-ideas.csv    _work/ stacked.json · merge-report.json · merge-emb-*.npy
```
