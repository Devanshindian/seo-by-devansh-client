# 7-writer-brief

Boils a company's brand documents down to **the part that governs how a body sentence gets written**.

A brand pack grows into several files and tens of thousands of words. Most of it governs work that is
not writing a body sentence: headings, intros, links, meta tags, images, pricing, checklists. Some of it is facts rather than
rules. And because the files were written at different times, several contradict each other.

**Standalone.** It reads four files and writes one. It changes nothing before it and decides nothing
after it.

**The recipe is [`writer-brief.workflow.md`](writer-brief.workflow.md). Read that first.**

## Run it

```bash
cd scripts
COMPANY=<slug> python3 run_writer_brief.py
```

| Flag | What it does |
|---|---|
| *(none)* | Resumable. Any step whose output already exists is reused. |
| `--redo` | Re-runs both steps. |
| `--redo-assemble` | Re-runs Step 2 only. |

| Env | Default | What it does |
|---|---|---|
| `COMPANY` | *(required)* | The project slug under `projects/` |
| `WB_RULINGS` | `<brand-context>/writer-brief-rulings.md` | Hand-written house decisions that outrank the source files. Blank to copy: `templates/rulings.md` |
| `LLM_PROVIDER` | `claude` | `claude` or `codex` |
| `WB_WORKERS` | `4` | Parallel classify calls, one per source file |

## File map

| File | What it is |
|---|---|
| `writer-brief.workflow.md` | The recipe. The template lives here and is lifted verbatim by the code. |
| `templates/rulings.md` | The blank house-decisions file. Copy it into the company's brand-context folder and fill it in. Optional. |
| `scripts/config.py` | Every path and setting, from one anchor. `SOURCE_FILES` owns which brand files are read, with a reason beside every exclusion. |
| `scripts/llm.py` | The shared headless-CLI caller (Claude or Codex). No API key. |
| `scripts/run_writer_brief.py` | The orchestrator and its two steps. |
| `prompts/classify-sections.md` | Step 1. Asks: can the writer act on it · any company or this one · rule or fact. |
| `prompts/assemble-brief.md` | Step 2. Fills the recipe's template and resolves the contradictions. |

## What it writes

| Path | What |
|---|---|
| `projects/<company>/01-brand-context/writer-brief.md` | **The deliverable.** Written in place; `git diff` is the review surface. |
| `…/_work/writer-brief/classified.json` | Every section, its three answers, and the derived keep-or-drop |
| `…/_work/writer-brief/dropped.md` | A record of what did not make it, and why |

## Two things to know

- **The brief is derived. Never hand-edit it.** Edit the source file and re-run, or the two drift.
- **Nothing is deleted from the source files.** They stay exactly as they are. A wrong split costs one
  re-run and nothing else.
