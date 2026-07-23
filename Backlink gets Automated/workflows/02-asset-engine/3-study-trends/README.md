# Study Trends — how to run it + the file map

Method 3 of the asset engine: read what the niche is arguing about on **Reddit** right now, distil it into
recurring **tensions** (one-sentence shared pains), and turn each into a timely, link-worthy asset idea. It
supplies what Methods 1 & 2 can't: *timeliness*. Full recipe:
[`study-trends.workflow.md`](study-trends.workflow.md).

## Two phases

**Phase A — scrape Reddit (has the one human gate: choosing subreddits).** A separate tool:
```bash
# discover + vet subreddits, get user sign-off, then:
python3 scripts/reddit/reddit-scrape.py run "sub1,sub2,sub3" --posts 25 --sort top --time year \
  --out projects/<company>/02-asset-engine/study-trends/_raw/<company>-reddit-trends.xlsx \
  --raw projects/<company>/02-asset-engine/study-trends/_raw/reddit-json
```

**Phase B — mine the scrape into ideas (fully automated, no gates).**
```bash
python run_study_trends.py --company <slug>
```
One resumable command, stages 2a → 4, then the fail-closed **verify gate**. All LLM calls run on the free
headless Claude/Codex CLI. Stage 3 (KEEP/DROP) filters automatically — like Methods 1 & 2, no human stop.

| Flag | What it does |
|---|---|
| `--company <slug>` | the company (or `COMPANY=`). Required. |
| `--from <STAGE>` | force from a stage onward (`2a`,`2b`,`2c`,`2d`,`3`,`4`). |
| `--redo` | force every stage. |

## The stages (each writes a named file the next reads)

| Stage | Script | Does | Writes |
|---|---|---|---|
| 2a | `step_2a_phrases.py` | tag every post with 2-3 phrases (parallel shards) | `_work/all-phrases.tsv` |
| 2b | `step_2b_tensions.py` | consolidate phrases → tensions **through the merge-check gate** (`merge-check.md` written *before* tensions.csv) | `_work/merge-check.md` · `output/phrase-map.csv` · `_work/tensions_base.json` |
| 2c | `step_2c_assign.py` | assign every post to its dominant tension (parallel) | `_work/post-tension-map.tsv` |
| 2d | `step_2d_records.py` | build the tension record (LLM fields + mechanical counts) | `output/tensions.csv` |
| 3 | `step_3_filter.py` | Linkability + Ownability (transplant check) → KEEP/DROP | verdicts in `output/tensions.csv` |
| 4 | `step_4_ideas.py` | kept tensions → asset ideas | `output/study-trends-ideas.csv` |
| 5 | `study-trends-verify.py` | fail-closed gate (order, coverage, no junk bucket, no product-leak, ideas==kept) | PASS/FAIL |

## Output

- **`output/study-trends-ideas.csv`** — ★ THE DELIVERABLE. `Tension · Asset title · What it'd be · Brand fit ·
  Unfair advantage · # posts · Audience · Emotion · Best example URL`. A separate pool, merged with Methods 1 & 2 later.
- `output/tensions.csv` — every tension + full evidence + verdicts. `output/phrase-map.csv` — the phrase→tension audit trail.

## File map

```
3-study-trends/
  study-trends.workflow.md · README.md · run_study_trends.py
  scripts/
    config.py · _posts.py (xlsx reader)
    step_2a_phrases · step_2b_tensions · step_2c_assign · step_2d_records · step_3_filter · step_4_ideas
    study-trends-verify.py            ← the Stage-5 gate
    reddit/                           ← Phase A: the Reddit scraper tool (+ ocr-mac)
  prompts/  2a-phrases · 2b-consolidate · 2b-mergecheck · 2c-assign · 2d-records · 3-filter · 4-idea

projects/<company>/02-asset-engine/study-trends/
  _raw/   <company>-reddit-trends.xlsx + reddit-json/   (Phase A output — the input to Phase B)
  _work/  all-phrases.tsv · merge-check.md · tensions_base.json · post-tension-map.tsv
  output/ study-trends-ideas.csv · tensions.csv · phrase-map.csv
```

Shared clients (`config_base.py`, `llm.py`) live in `workflows/02-asset-engine/_shared/`.
