---
description: Write one already-researched topic — planner, architect, field, writer, in one go
argument-hint: "[slug]  ·  e.g. the-type-d-personality-label  ·  (blank = show what is ready to write)"
---

# /writer — turn a researched topic into a finished article

This runs the **write phase** (`04-write-phase/scripts/run_article.py`) for one topic that has already been
researched: **planner → architect → field → writer**, one command, resumable.

Use this when the research already exists and you want the article written, or re-written. It is the command you
reach for most, because research happens once per topic and writing gets re-run every time a prompt changes.

## Step 1 — decide which topic

Read `$ARGUMENTS`. The first bare word is the **slug**.

If no slug is given, read the queue and show what is ready, then ask which one:

```bash
python3 - <<'PY'
import csv
p="Backlink gets Automated/projects/testlify/03-content-machine/research-log.csv"
rows=[r for r in csv.DictReader(open(p)) if r["research_status"]=="done"]
for r in rows:
    print(f"  {r['write_status']:8}  {r['slug']:46}  {r['asset'][:56]}")
PY
```

Offer the ones with `write_status: pending` first (never written), then the `done` ones (a re-write). Use
**AskUserQuestion** with those as the options.

## Step 2 — decide the provider

Same rule as `/research`. Look for `claude` or `codex` in `$ARGUMENTS`; if neither is there, ask with
**AskUserQuestion** (Claude is the default). Both run on the local authenticated CLI, so neither needs an API key.

Pass it through the environment, because the write phase reads `LLM_PROVIDER` on every call:

```
LLM_PROVIDER=<provider> LLM_PROVIDER_CHAIN=claude,codex
```

The chain matters: if the pinned provider hits a usage limit mid-run, the next one picks it up instead of the run
stalling.

## Step 3 — run it

```bash
cd "Backlink gets Automated/workflows/03-content-machine/14-research-conductor/scripts"
COMPANY=testlify LLM_PROVIDER=<provider> LLM_PROVIDER_CHAIN=claude,codex \
  caffeinate -i python3 run_topic.py --write-only --slug <slug>
```

`caffeinate -i` keeps the machine awake — a full write is 30 to 60 minutes and sleep kills it.

Useful switches, pass them through when the user asks:

| switch | what it does |
|---|---|
| `--until coherence` | stop after the writing steps, before it spends anything on links |
| `--skip-field` | skip the Reddit/Blind/LinkedIn station |
| `--redo` | rerun every step instead of reusing what already finished |

## Step 4 — report

Report, in this order:

1. **The article**: word count, section count, and the path to `writer/draft.md`.
2. **The checks**: anything the run flagged with `!!`, especially the readable step's check list.
3. **The queue**: the run sets `write_status` itself — `done` when it finished, `failed` when it did not. Say which.

If a step fails, say plainly which one and that running the same command again resumes from there rather than
starting over.
