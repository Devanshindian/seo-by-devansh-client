---
type: the standing BIG-PICTURE map — read this when you've gone deep and might have lost the whole
purpose: keep the end-to-end system, its connections, and its standing problems in view at all times
companion to: SKILL.md (the WHAT/WHERE map) · ~/.claude/conventions/*.md (the HOW-to-build rules)
last_updated: 2026-07-22
---

# The Big Picture — the backlink machine, how it connects, and what can break it

## 0. The discipline (why this file exists — read it every time you resurface)
- When you go deep on ONE step (a prompt, a dedup, a judge), you lose sight of how it connects to the rest.
- Before changing anything, ask three questions: **What feeds this? What does this feed? Does my change break
  either side?**
- After finishing a deep task, COME BACK here and re-check: did I break a connection? did I forget a standing
  problem below?
- The three convention files (`~/.claude/conventions/`) are the HOW-to-build rules. This file is the
  WHAT-connects-to-what map + the list of problems that never go away.

## 1. The one idea (the whole machine in 6 lines)
1. **00 foundation** — learn the company's existing pages + what each already ranks for.
2. **01 brand-context** — learn how the company writes + what it sells.
3. **02 asset-engine** — find ideas worth building (3 methods → merge → dedup → reuse-check) → `clubbed-ideas.csv`.
4. **03 write phase** — research each chosen idea → a write-ready bundle → an article.
5. **publish** (not built) — the article goes live.
6. **the loop** — a published article REJOINS 00's content-database, so we never rebuild it next time.

## 2. The data objects that flow (the spine — one owner each, downstream only reads)
| Object | Owner | Carries | Read by |
|---|---|---|---|
| `content-database.csv` | 00 | every page + full text + its ranking keyword | reuse-check, cannibalisation, spoke-idea |
| `top-pages.csv` | 00 | each page's top ranking keyword + traffic | cannibalisation flag |
| the Voyage page-index | 02 reuse-check | embeddings of our pages | reuse-check, spoke-idea |
| `clubbed-ideas.csv` | 02 | idea + Format + Tool escalation + Reuse verdict + Chosen links + # words | 03 write phase |
| `research-log.csv` | 03 | the queue/status per topic + the write-phase signals | 03 conductor |
- **Rule (F1 single source of truth):** each value is decided ONCE by its owner and carried forward. Downstream
  never silently re-decides it. If a new value is needed, add a column at the owner, don't recompute downstream.

## 3. The standing problems (always solve for these — they never go away)
Each: the problem · an example · where it's handled · the risk if forgotten.
- **Over-tooling** — forcing a tool when an article ranks. e.g. "Cost-Per-Hire **Calculator**" for a query whose
  page-1 is all articles. Handled: 02 G2 copies the competitor's format; tools only flagged. FIXED (1,143→0).
- **Cannibalisation** — building a 2nd page for a keyword we already rank for, splitting our own ranking.
  e.g. we rank for "psychometric test" and write a second psychometric-test page. Handled: 03 FLAGS it (builds
  anyway, tells the team). Risk if forgotten: we quietly compete with ourselves.
- **Duplication / reuse** — rebuilding what we already have. Handled: 02 reuse verdict (Already have it / Improve
  existing / Build from parts / Brand new). Risk: wasted writing + thin duplicate pages.
- **Spoke starvation** — a spoke is a bare keyword with NO title/angle/links, so it can't be researched. e.g.
  "define outlier" as a spoke → crashes. Handled (planned): mint an idea from the keyword first, then reuse-check it.
- **Feedback gap** — a freshly built article that never rejoins the content-database → next run rebuilds the same
  thing. Handled (planned): append the published page back into 00. Risk: infinite re-doing across runs.
- **Format fidelity** — writing a listicle, a guide, a report all the same generic way. Handled (planned): the
  format router (Format → the matching playbook). Risk: mediocre same-shaped articles.
- **Generalisation** — a change is only "generalised" once a SECOND company actually runs it end to end. Risk:
  we think it's reusable but it was quietly Testlify-shaped.
- **Data hygiene** — scraped pages carry junk (e.g. an injected `DEPLOY_APPROVED=1` string). Risk: a downstream
  LLM obeys a poisoned instruction. Judges caught it this time; scrub it at the source.

## 4. The connection map — "if I change X, go check Y"
| If you change… | Re-check… |
|---|---|
| the idea columns in `clubbed-ideas.csv` | 03 topic_pick (reads them), bundle (shows them), research-log FIELDS |
| the reuse-check verdicts | 03 REUSE_OK / priority order (what gets written), the "Improve existing" rewrite path |
| the format tagger | anything that copies the format downstream (ideas keep their tag; write phase routes on it) |
| a prompt | the script that parses its JSON (fields must match), and the recipe MD that documents it |
| the content-database (00) | reuse-check index freshness, cannibalisation matches (both read it) |
| where an engine writes its output | the next engine's resume-check (it looks for that exact file/path) |

## 5. Edge cases at each stage (the if/then thinking to apply every time)
- **Idea pick:** is it a tool (skip+flag)? do we already rank (flag)? is it "Improve existing" (rewrite a page,
  sort last)? is it a spoke (mint an idea first)?
- **Research:** does the brief's word band agree with our `# words`? does the SERP actually reward this format?
- **Write:** are we rewriting a company page (tell them)? is the format handled or written generically?
- **After build:** did it rejoin the content-database? did it create a cannibalisation we should have flagged?
- **Any run:** if credits cap here, does it resume cleanly with no corruption? (atomic writes + markers)

## 6. Where we are on the roadmap (keep this current)
- 00 ✅ · 01 ✅ · 02 ✅ (format-honesty fix + 1,892 clean ideas, reuse-judged).
- 03 write phase: first pass DONE (tool-skip, word target, improve-existing-last, new queue columns).
  IN PROGRESS: cannibalisation flag + spoke→idea + spoke nesting.
  PARKED (need the writer/publish step): feedback loop, format router, the "key-decisions-the-company-should-know" doc.
- Proof still owed: a second-company end-to-end run (the real generalisation test).
