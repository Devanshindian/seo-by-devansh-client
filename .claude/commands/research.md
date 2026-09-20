---
description: Run the research conductor on the next topic — pick the LLM provider (Claude or Codex) and model
argument-hint: "[claude|codex] [model]  ·  e.g. codex gpt-5.4  ·  claude sonnet  ·  (blank = ask)"
---

# /research — research one topic, and stop there

> **Which command do you want?**
> · `/research` researches a topic and stops. Use it when you want the research without the article.
> · `/writer <slug>` writes a topic that is already researched. The one you reach for most.
> · `/article` does both for one topic, then stops.

This runs the **research conductor** (`14-research-conductor/scripts/run_research.py`): it picks the next topic and
runs the whole research phase end to end — **pick → DataForSEO → STORM → gap-check → build_structure → bundle → log**
— and produces a write-ready bundle. One command, one topic, resumable.

## Step 1 — decide the provider + model

Read `$ARGUMENTS`. Interpret the words as `[provider] [model]`:
- **provider** = `claude` (default, headless Claude Code) or `codex` (headless Codex). Both run for free, no API key.
- **model** = optional (e.g. `opus`, `sonnet`, `haiku` for Claude; `gpt-5.4` for Codex). Blank = that CLI's default.

If the provider is **not** clearly given in `$ARGUMENTS`, ask the user with **AskUserQuestion**:
1. **Provider** — "Claude Code (headless)" or "Codex". Default: Claude.
2. **Model** — offer the common models for the chosen provider plus a "CLI default" option.

If a provider (and optionally a model) IS given in `$ARGUMENTS`, use it directly and skip the questions.

> **Codex prerequisite:** the `codex` CLI must be installed and authenticated on this machine (the sub-engines and
> STORM's shim shell out to `codex exec`). If the user picks Codex, quickly confirm `codex` is on PATH
> (`which codex`); if it isn't, tell them and offer to fall back to Claude.

## Step 2 — run it

Run the conductor from its scripts dir, streaming output live (the run is long — STORM can take tens of minutes;
that's normal, not a hang):

```bash
cd "Backlink gets Automated/workflows/03-content-machine/14-research-conductor/scripts"
python3 run_research.py --provider <PROVIDER> [--model <MODEL>]
```

- With **no `--asset`** it auto-picks the next topic from the queue (`research-log.csv`), else the next eligible idea
  from `clubbed-ideas.csv`. To force a specific topic for testing, add `--asset "<full title>"`.
- **Resumable:** safe to interrupt and re-run — it resumes at the step that didn't finish. Add `--redo` to rerun all
  steps, `--from N` to force from step N, or `--until N` to stop after step N (e.g. `--until 2` = stop after STORM).
- The conductor starts STORM's bridge (shim) automatically for the chosen provider before the STORM step.

## Step 3 — report

When it finishes, report the write-ready bundle path it prints
(`projects/<company>/content-machine/research-bundle/<slug>/bundle-<slug>.md`) and tell the user the article is
**not written yet** — `/writer <slug>` is the next step, or `/article` would have done both in one go.

This command sets `research_status: done` and leaves `write_status: pending`, which is correct: nothing has been
written. If a step fails (e.g. the STORM word-count gate), surface the error plainly and say a re-run resumes from
there.
