---
type: workflow-recipe
stage: brand-context (Stage 01 — runs LAST in this layer)
reusable: any company
reads:
  - projects/[company]/01-brand-context/brand-voice.md          # pillars · tone · messaging · terminology
  - projects/[company]/01-brand-context/style-guide.md          # mechanics · preferred terms · banned words
  - projects/[company]/01-brand-context/voices.md               # the byline and its person ("we" / "I")
  - projects/[company]/01-brand-context/writing-integrity.md    # honesty · sourcing · competitor rules
produces:
  - projects/[company]/01-brand-context/writer-brief.md         # the deliverable
  - projects/[company]/01-brand-context/_work/writer-brief/classified.json
  - projects/[company]/01-brand-context/_work/writer-brief/dropped.md
last_updated: 2026-08-10
---

# Writer brief — build workflow

> **Where this lives:** `Backlink gets Automated/workflows/01-brand-context/7-writer-brief/`. Reads the
> brand pack from `projects/[company]/01-brand-context/`; writes `writer-brief.md` back to the same folder.
> Numbered **7** because it runs after 1-brand-voice, 2-style-guide and 6-voices have produced their files.
> It reads their output; it never reads a website.

**This engine is standalone.** It reads four files and writes one. It changes nothing before it and
decides nothing after it. It does not know or care what any other step does with its output.

---

## What this does — in one line

**Boil a company's brand documents down to the part that governs how a body sentence gets written.**

A brand pack grows into several files and tens of thousands of words. Most of it governs work that is
not writing a body sentence: headings, intros, links, meta tags, images, pricing, checklists. Some of it is facts rather
than rules. And because the files were written at different times, several of them contradict each other.
This engine keeps the part that is a rule, is this company's own, and can actually be followed while
typing a sentence of prose.

---

## The one rule that governs everything

**Keep a line only if following it changes a sentence of body prose.**

Everything follows from this. A rule about how a heading should read is out, because a body sentence is
not a heading. A rule about anchor text is out. A rule about pricing is out. A statistic is out, because a
statistic is not a rule. A rule that any company in any industry would want is out, because this file is
about what makes THIS company's writing its own.

---

## What you produce

| Step | Output | What it holds |
|---|---|---|
| 1 | `_work/writer-brief/classified.json` | Every section of every source file, with its three answers and the derived keep-or-drop |
| 2 | `writer-brief.md` | The deliverable |
| 2 | `_work/writer-brief/dropped.md` | A record of what did not make it, and why |

---

## Inputs

- The four **rule-carrying** brand files, listed in the frontmatter. `config.SOURCE_FILES` owns that list.
- **Not read, and each exclusion is a decision:**
  - `stats.md`, `stories.md` — statistics and customer stories. Facts, not rules about writing.
  - `features.md` — a product catalogue. Not rules about writing.
  - `persona.md` — describes the reader, not the company's own voice.
  - `writing-examples.md` — five complete published articles. Whole finished pages, not rules.
  - `opinions.md` — an empty template with no opinions recorded in it.
- **`projects/[company]/01-brand-context/writer-brief-rulings.md`** (optional, hand-written) — decisions a
  human made that cannot be worked out from the source files. It is company content, so it lives under
  `projects/`, never in this folder. Copy `templates/rulings.md` to start one. Keep it short: where two
  files simply disagree, Step 2 resolves it on its own.

---

## The steps

### Step 1 — Classify every section

**What it does.** Reads each source file whole and splits it at its own headings. For every section it
answers three questions, and code derives keep-or-drop from the answers.

**The three questions.**

| Question | Field | Values |
|---|---|---|
| Can the writer act on it? | `actionable` | `true` · `false` |
| True for any company, or only this one? | `scope` | `universal` · `company` |
| What sort of thing is it? | `kind` | `rule` · `fact` · `reference` |

**Keep-or-drop is derived in code, not asked for.** One LLM answer cannot then disagree with itself:

```
actionable is false     -> drop  (the writer cannot act on it)
kind == fact            -> drop  (a fact, not a rule about writing)
kind == reference       -> drop  (a lookup list a human consults, not something applied while writing)
scope == universal      -> drop  (true for any company, so it is not this company's brief)
otherwise               -> keep
```

**It also returns `carry`:** the actual lines to keep, tightened but never invented. Where a section is a
table of terms, `carry` holds every row.

**Follows:** `prompts/classify-sections.md`. **Output:** `classified.json`.

**Two gotchas, both measured on the first real run.**
- The model keeps **commercial material** — pricing, guarantees, refunds, buying objections — because it
  sounds like the brand. It is not body prose. The prompt names this trap explicitly.
- The model keeps a whole block of **quoted samples** because some of the samples are good. Samples from a
  pricing page, a tagline, or an article's opening hook are not the register this writer works in.

### Step 2 — Assemble the brief

**What it does.** Fills the template below from everything kept, **resolving the places the sources
contradict each other** rather than printing both sides. It moves content; it never invents any.

**How a disagreement is settled**, in order: a legal or safety line wins · a rule beats a quoted sample ·
a closed named list beats an open category · the narrower rule wins when the broader one would make
ordinary writing impossible · a default beats an exception that only adds ambiguity. Only when none of
those settle it does the brief keep both and state the boundary in one line.

**Why a rule beats a sample.** Guardrail documents are written as rules. Voice documents are usually
reverse-engineered from copy that already shipped, so their quoted samples routinely break rules written
after that copy went live. On the first real run, **four of the eleven contradictions found were a
sample contradicting a rule**, and in every one the rule was right.

**Follows:** `prompts/assemble-brief.md`. **Output:** `writer-brief.md`, written in place.

**Gotcha.** The failure mode is losing specifics. Twenty-three house spellings become "follow house
spelling", and the brief is then useless, because a specific is the only thing a writer can act on. Step 2
counts the concrete items it was given and reports how many survived, so a loss is visible.

---

## The template (Step 2 fills this; it is lifted VERBATIM by the code)

```markdown
# Writer brief — [Company]

> What makes [Company]'s writing its own: what it believes, how it speaks, the words it uses and the words
> it refuses. General writing craft is not here. Statistics and stories are not here.

## Who is writing
[The byline. Which person to write in. What a first-hand marker may sound like, and what is never allowed.]

## What we believe
[This company's convictions, numbered. For each: the conviction in one line, how it sounds when written
well, and what to avoid. These are beliefs, never product claims.]

## Naming [Company]
[Where the company genuinely wins and where it does not. How the name itself is written.]

## How our writing sounds
[The register in two or three lines, then real published sentences as samples.]

## Words we use
| Write this | Not this | Why |
|---|---|---|

## House spelling
[This company's settled spelling and casing for its industry's terms.]

## Phrases we never use
[The banned list, grouped so it can be scanned.]

## Competitors
[How they are named, and the never-cite rule with the real list.]
```

---

## Mapping — every step traces to its source

| Step | Grounded in |
|---|---|
| 1 · the three questions | A hand pass over a real brand pack, 2026-08-10: can it be acted on · any company or this one · rule or fact |
| 1 · keep-or-drop derived in code | `building-workflows.md` F1 (decide a value once) and J2 (decide a verdict once) |
| 1 · the prompt names both traps | `building-workflows.md` J2 (a judge must SEE the criteria that define its verdict) |
| 2 · the resolution order | The eleven contradictions found in a real brand pack on the first run |
| 2 · pure assembly, template lifted verbatim | `building-workflows.md` F2 (traceable outputs) and F1 (the recipe owns the template) |
| 2 · concrete items counted | `project-structure-conventions.md` C3 (verify in code, not by trust) |

---

## Rules shelf

- `building-workflows.md` — F1 single source of truth · F2 traceable outputs · F3 earn every step · J2 a judge must see its criteria
- `project-structure-conventions.md` — Part B tool-folder standard · C1 config · C3 step shape · C5 atomic saves
- `../1-brand-voice/brand-voice.workflow.md` — produces one of the inputs
- `../2-style-guide/style-guide.workflow.md` — produces one of the inputs
- `../6-voices/voices.workflow.md` — produces one of the inputs

---

## Gotchas

- **The brief is derived, so never hand-edit it.** Edit the source file and re-run, or the two drift and
  nobody knows which is real.
- **Nothing is deleted from the source files.** `brand-voice.md` and `style-guide.md` stay exactly as they
  are. The brief is a new file built from them, so a wrong split costs one re-run and nothing else.
- **Run this LAST in the layer.** It reads what 1, 2 and 6 produced.
- **Read `dropped.md` on the first run for a company.** It is the only place a wrong drop shows up.

---

## Build / run checklist

- [ ] 1-brand-voice, 2-style-guide and 6-voices have run; their files exist
- [ ] `COMPANY=<slug> python3 scripts/run_writer_brief.py`
- [ ] Read `_work/writer-brief/dropped.md` — does any drop look wrong?
- [ ] Read `writer-brief.md` end to end — is any specific missing that the pack had?
- [ ] Check the concrete-items count printed by Step 2
- [ ] `git diff` the brief; commit
