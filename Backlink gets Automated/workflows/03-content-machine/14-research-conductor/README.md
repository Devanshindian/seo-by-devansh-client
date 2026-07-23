# 14 · Research conductor

The `/research` engine. **One command → one topic → all four research engines, autonomously.** Picks the next
topic, runs keyword+competitor research (DataForSEO), a deep dossier (STORM), gap-filling (gap-check), and the
article blueprint (build_structure), packages the **write-ready bundle** (Step 5), then logs it and queues its spokes.

## Run
```bash
python3 scripts/run_research.py                     # auto-pick the next topic (queue, else clubbed CSV)
python3 scripts/run_research.py --asset "Recruiting Metrics Benchmark"   # force one topic (testing)
python3 scripts/run_research.py --redo              # rerun every step
python3 scripts/run_research.py --from 3            # force-rerun from step 3 onward
python3 scripts/run_research.py --provider claude --model sonnet  # headless Claude Code with a selected model
python3 scripts/run_research.py --provider codex --model gpt-5.4  # headless Codex with a selected model
```
Resumable: a step is skipped if its output already exists. Safe to Ctrl-C and re-run — it picks up where it left off.

## The chain (per topic)
| Step | Does | Engine | Output |
|---|---|---|---|
| 0 | pick topic + tick the sheet | `topic_pick.py` | a row in `research-log.csv` |
| 1 | keyword + competitor research | `10-dataforseo` | `dataforseo/out/<slug>/research-doc-<slug>.md` |
| 2 | deep background dossier | `11-storm` | `storm/out/<TopicDir>/…polished.txt` |
| 3 | fill gaps the brief needs | `12-gap-check` | `gap-check/out/<slug>/gap-check.md` |
| 4 | article blueprint | `13-research-structure` | `research-structure/out/<slug>/structure-<slug>.json` + `.html` |
| 5 | write-ready bundle (10-division cover sheet + copied blueprint) | `bundle.py` | `research-bundle/<slug>/bundle-<slug>.md` |
| 6 | log done + enqueue spokes | `topic_pick.py` | updated `research-log.csv` |

## The queue (`projects/<company>/03-content-machine/research-log.csv`)
The single source of truth for **status**; the clubbed CSV stays the source of truth for **idea data**.
Columns: `slug · asset · angle · source · research_status · write_status · run_dir · created · updated`.
Pull-based: pick the next `pending` row (spokes sit right after their hub → depth-first per cluster); if none
pending, pull the next eligible idea from `clubbed-ideas.csv`. One topic per run. No triggers — a cron just
fires this repeatedly.

## Files
- `scripts/config.py` — all paths (from one repo anchor) + STORM/shim knobs + the reuse-verdict filter.
- `scripts/topic_pick.py` — the queue + the chooser (Step 0) + spoke insertion (Step 6).
- `scripts/run_research.py` — the conductor (pure sequencing; starts the STORM shim; resumable).

## Prerequisites
- The four engines set up (esp. STORM's venv + `.env`, and DataForSEO's `.env`).
- `--provider claude` is the default and uses the locally authenticated Claude CLI.
- `--provider codex` uses the locally authenticated Codex CLI. Neither provider needs an API key.

## Built, not yet fully tested end-to-end
- **Spokes**: the path IS built — DataForSEO takes a spoke's title+angle directly (`--angle`), the conductor enqueues
  spokes after their hub with the brief's `why` as the angle. Not yet run end-to-end on a real spoke.
- **Full run**: DataForSEO + STORM verified on fresh topics; one clean gap-check → blueprint → bundle run still pending.
