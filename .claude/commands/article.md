---
description: One topic all the way — research it, write it, mark both done, stop
argument-hint: "[topic]  ·  blank = the next topic in the queue  ·  or type a brand new topic"
---

# /article — a topic in, a finished article out

This runs **both halves** for exactly one topic: research, then writing, then it marks the queue and **stops**.

  research → write → `research_status: done` + `write_status: done` → stop

It does not roll on to the next topic. A topic is either finished or it is the one in progress, never a pile of
half-done ones. Run the command again for the next one.

## Two ways it gets used

**Blank** (`/article`) — takes the next unfinished topic in the queue. If the queue is clear, it pulls the next
eligible idea from `clubbed-ideas.csv`.

**With a topic** (`/article Cost per hire benchmarks for 2026`) — researches and writes that one, **and adds it to
the queue**, so a hand-typed run leaves a record like any other.

## Step 1 — work out which of the two this is

Read `$ARGUMENTS`, ignoring any `claude`/`codex`/model words (those are the provider, see step 3).

- **Nothing left** → the blank case. Show the user what is about to be picked before spending anything:

```bash
python3 - <<'PY'
import csv
p="Backlink gets Automated/projects/testlify/03-content-machine/research-log.csv"
rows=list(csv.DictReader(open(p)))
nxt=[r for r in rows if r["research_status"] in ("pending","in_progress")]
print("next up:", (nxt[0]["slug"] + "  |  " + nxt[0]["asset"][:70]) if nxt
      else "queue is clear — it will pull the next idea from clubbed-ideas.csv")
PY
```

- **Something left** → a named topic. Go to step 2.

## Step 2 — a named topic needs three things

A topic cannot be researched from a title alone. These are the fields the queue carries out of
`clubbed-ideas.csv`, and three of them are required:

| field | required? | what it is |
|---|---|---|
| **title** | **yes** | what the article is called |
| **distinct angle** | **yes** | what makes our version different from the pages already ranking |
| **format** | **yes** | listicle, how-to guide, comparison, definition piece, and so on |
| target words | no | measured properly during research |
| reuse verdict | no | only for "improve an existing page" |
| chosen links | no | only for "improve an existing page" |

The user has given you the title. **Ask for the other two with AskUserQuestion** rather than inventing them:

- **The angle** — offer two or three specific angles you can defend from what you know of the topic, plus the
  option to write their own. Never pick one silently: the angle is what the whole article is built around.
- **The format** — offer the archetypes: `listicle`, `how-to-guide`, `comparison-rankings`,
  `answer-bait-definitional`, `data-benchmark-report`, `glossary`, `template-resource`. The format decides the
  article's shape **and** now drives the readability rewrite, so a wrong one costs real quality.

If the user already gave an angle and a format in their message, use those and do not ask.

## Step 3 — decide the provider

Same rule as `/research`. Look for `claude` or `codex` in `$ARGUMENTS`; if neither, ask (Claude is the default).
Both run on the local authenticated CLI, so neither needs an API key.

## Step 4 — run it

```bash
cd "Backlink gets Automated/workflows/03-content-machine/14-research-conductor/scripts"
COMPANY=testlify LLM_PROVIDER=<provider> LLM_PROVIDER_CHAIN=claude,codex \
  caffeinate -i python3 run_topic.py --provider <provider> [--asset "<title>"]
```

Omit `--asset` for the blank case. `caffeinate -i` keeps the machine awake: research plus writing runs an hour or
more and sleep kills it.

**Warn the user before starting** that this is the long one — research alone is around 40 minutes — and that it is
resumable, so an interruption costs nothing but time.

## Step 5 — report

1. **Which topic** it picked, and its slug.
2. **The article**: word count, sections, and the path to `writer/draft.md`.
3. **Anything flagged** with `!!` during the run, especially the readable step's checks.
4. **The queue**: it sets both columns itself. Say what they ended up as.
5. Remind them it stopped on purpose, and that running `/article` again takes the next topic.

If research fails, say so plainly and note that **nothing was written** and the queue was not touched. If research
succeeded and writing failed, the row honestly reads `research: done, write: failed`, and `/writer <slug>` picks it
up without redoing the research.
