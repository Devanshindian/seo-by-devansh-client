# STORM — the Evidence Engine (self-contained)

The deep-research engine for the content machine. Given a topic, it produces a densely-cited **research
dossier** that feeds the write phase. It is **Stage 4 (the Evidence Engine)** of the research-phase
roadmap — STORM never writes final copy; it manufactures the evidence that makes our copy non-generic.

**Everything is in this one folder** — the full source, its own virtual environment, the scripts, and the
outputs. Nothing lives in your home directory.

## Layout
```
storm/
├── storm-plan.md       READ THIS FIRST — the recipe: asset topic → dossier, step by step
├── README.md           how to run + this layout
├── .env                DataForSEO creds (DFS_LOGIN / DFS_PW); auto-loaded by run_storm.py — keep local
├── CHANGES.md          every modification we made to STORM, and why
├── scripts/            OUR code: shim.py · dataforseo_rm.py · run_storm.py · build_steplog.py
├── engine/             STORM's library source (our edits are documented in CHANGES.md); don't read to use it
├── venv/               the environment (generated; don't edit)
├── out/                run outputs land here (local)
├── logs/               shim.log · calls.jsonl (local)
├── requirements.lock   exact working dependency versions
└── setup.sh            rebuild the venv from scratch (disaster recovery)
```

**What to read:** `storm-plan.md` (the recipe), then `scripts/` (our 4 files). **What to ignore:** `engine/`
(the STORM engine source — our edits to it are documented in `CHANGES.md`) and `venv/` (the environment).

The venv imports `knowledge_storm` directly from the visible `./engine/knowledge_storm/` source (via a `.pth`
file), so **editing the source *is* editing what runs** — no hidden copy, no patch step.

## How to run
```bash
cd "<this folder>"
# DataForSEO creds live in .env (DFS_LOGIN / DFS_PW) and auto-load — no export needed.

# 1. start the shim (bridge that lets STORM run on Claude Code instead of a paid API):
nohup venv/bin/python scripts/shim.py > logs/shim.out 2>&1 &

# 2. run STORM:
venv/bin/python scripts/run_storm.py "YOUR TOPIC" --turns 4 --topk 5 --article --polish
```
Outputs appear in `out/<topic>/` — the polished dossier is `storm_gen_article_polished.txt`.

## The scripts (what each does)
- `shim.py` — local OpenAI-compatible server that forwards every LLM call to a headless CLI — `claude -p` (default) or `codex exec` ($0 API cost; pick with `--provider`).
- `dataforseo_rm.py` — finds links via DataForSEO, then scrapes each full article (deep RAG).
- `run_storm.py` — the control panel: sets every knob and runs research → outline → write → polish.
- `build_steplog.py` — renders the raw call log into a readable step-by-step of what STORM did.

## Rebuilding
If the venv ever breaks, run `./setup.sh` — it recreates the venv from `requirements.lock` and re-points
it at the visible source. Requires `uv`. Our source edits in `engine/knowledge_storm/` are untouched by this.

See `CHANGES.md` for every modification we made to STORM and the proven run config.
