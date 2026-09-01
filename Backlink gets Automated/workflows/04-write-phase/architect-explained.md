---
type: a complete plain-English explanation of the ARCHITECT (write phase, steps 1 to 5)
purpose: so you can hold the whole architect in your head and know exactly where any change belongs
covers: run_architect.py + shape.py + enrich.py + allocate_words.py + section_keywords.py + headings.py
        and all 15 prompt files they use, quoted in full
real numbers from: the 4 finished Testlify articles
state: current — this describes what the code does today, not how it got here
last_updated: 2026-08-09
---

# The Architect, explained

## Part 0 — The one idea

The architect is the **step between research and writing**.

- **Research** already happened. It gave us a pile of facts and a rough outline.
- **The writer** comes later. It turns each section into prose.
- **The architect sits in the middle.** Its whole job is: turn a rough outline plus a pile of facts
  into a **final blueprint** for the article. Sections, in order, each with a heading, a job, its
  facts, and a word target.

Nothing here writes a single sentence of the article. It is all planning.

**In one line:** design the sections → go get any missing facts → decide how long each section is →
decide which sections deserve a keyword → write the final headings and the H1.

---

## Part 1 — The five steps, in one picture

Run with one command:

```bash
python3 run_architect.py --slug <slug>          # run or resume
python3 run_architect.py --slug <slug> --redo   # force everything to rerun
```

[run_architect.py](scripts/run_architect.py) is **pure sequencing**. It calls each step in order and
does nothing else.

| # | Step | Script | What it decides | Lines of code |
|---|------|--------|-----------------|---------------|
| 1 | **shape** | [shape.py](scripts/shape.py) | Which sections exist, in what order, what goes in each | 333 |
| 2 | **enrich** | [enrich.py](scripts/enrich.py) | Goes and researches whatever step 1 said was missing | 256 |
| 3 | **allocate** | [allocate_words.py](scripts/allocate_words.py) | How many words each section gets | 99 |
| 4 | **section-keywords** | [section_keywords.py](scripts/section_keywords.py) | Which sections deserve a search keyword, and which one | 252 |
| 5 | **headings** | [headings.py](scripts/headings.py) | The final wording of every heading, then the H1 | 290 |

Total: **1,230 lines of Python and 15 prompt files.**

### The file chain

Each step writes a named file. The next step reads it. That is the whole design.

```
planner/article-plan.json      (comes in from the planner)
gather/plan-inputs.json        (the fact cards)
        |
   1. shape
        v
architect/_work/structure.shaped.json
        |
   2. enrich
        v
architect/structure.json          <-- from here on, every step EDITS this same file
architect/enriched-cards.json     (any new facts it found)
        |
   3. allocate   -> adds "word_target" to every section
        |
   4. section-keywords -> writes architect/_work/section-keywords.json  (edits nothing)
        |
   5. headings   -> rewrites every "headline", adds "h1" and a "keywords" block
        v
architect/structure.json          <-- THE final blueprint the writer reads
architect/structure.md            <-- the same thing, readable, for humans
```

### Resumable

Every step checks "does my output file already exist?" If yes it skips and prints `reusing …`. So a
crash halfway does not restart from zero, and `--redo` forces a fresh run. This matters because step 2
and step 4 **spend money** (DataForSEO lookups).

---

## Part 2 — The seven words you need

Learn these once. They are used everywhere, including in the prompts.

- **The reader** = the persona this article is written for, e.g. "Hiring Manager (non-HR-native)".
  Chosen by the planner, and read by every architect step that makes a judgment.
- **Card** = one researched fact with its source link. The atom of everything. Written like `[c412]`.
- **Box** = one small group of cards on one narrow sub-topic, taken from the research outline. The
  architect numbers every box `#1` to `#N` and then only ever talks in box numbers. **A box label is
  a planning note, not a heading.** The architect writes the real headings itself.
- **Lead** = the boxes in a section that sit above its first sub-heading, so the opening prose.
- **H3** = a sub-heading the architect writes, with its own boxes under it. Only created when a
  section would run past about 3 paragraphs.
- **Archetype** = the article's format family. There are eight: `how-to-guide`, `listicle`,
  `comparison-rankings`, `answer-bait-definitional`, `data-benchmark-report`, `glossary`,
  `template-resource`, `common-spine`.
- **Spine** = one paragraph saying what the whole article argues, for whom, and what the reader can do
  at the end. Written fresh by the architect in step 1.
- **Job** = one or two sentences per section saying what that section must deliver. Written in step 1
  and carried all the way to the writer. This is the most under-used field in the whole machine.
- **The world** = two lines decided way back in research: what this article **is** about and what it
  **is not** about. Injected into most prompts here to stop the article drifting into a neighbouring
  field.
- **Word band** = the min and max word count for this article, decided in research. For example
  2,800 to 3,800.

---

## Part 3 — What goes in

The architect reads three things:

1. **`planner/article-plan.json`** - the frozen outline from the planner. H2s, their H3s, which cards
   sit under each, plus the word band and the planned H1.
2. **`gather/plan-inputs.json`** - the actual text of every card.
3. **The queue row** - the article's title and its "distinct angle" from `research-log.csv`.

Plus the format rulebook for this archetype, from [formats/](formats/). Those are short files. Example,
the whole structure section of `how-to-guide.md`:

```
## Structure (the format's signature)
- [ ] A **separate "what is X" definition section when the topic needs one — never mixed into the steps.**
- [ ] **Body:** the steps in procedural order, one H2/H3 per step, as a **numbered list**.
```

That file gets pasted into the structure prompt as `{{FORMAT_STRUCTURE}}`.

---
---

# STEP 1 — SHAPE

**File:** [shape.py](scripts/shape.py) · **Writes:** `architect/_work/structure.shaped.json`

## What it does

This is the big one. It designs the article.

- Every H3 in the research outline becomes a **numbered box**. The hackathon article had 56 boxes. The
  strategic-questions one had 67.
- The boxes, with their card text, get handed to an AI along with the title, the angle, the world, the
  format rulebook and the word budget.
- The AI returns: **a spine, then a list of sections**. For each section: its job, its headline, and
  **which box numbers go in it**.
- It answers only in box numbers. It never retypes the material. That is deliberate: it cannot invent
  content because it is only allowed to point at boxes.
- It may also leave boxes out (called **benching**), ask for extra research on a section
  (**needs_research**), and mark a section to be rendered as a **table**.

## The four roads

Not every article gets the same treatment. The code picks a road by archetype:

| Road | Which archetypes | What happens |
|------|------------------|--------------|
| **simple** | how-to-guide, answer-bait-definitional, data-benchmark-report, glossary, common-spine | One AI call. `structure-simple.md` |
| **listicle** | listicle | First `detect-items.md` finds the list items, then `structure-listicle.md` |
| **comparison** | comparison-rankings | Three calls first: `detect-entities` → `find-yardsticks` → `filter-tools`, then `structure-comparison.md` |
| **template** | template-resource | One call, `structure-template.md`, which also designs the downloadable file |

**Only one road ever runs.** Of the 4 finished articles: hackathon took the simple road, cost-per-hire
took the simple road, Type D took the simple road, strategic questions took the listicle road. The
comparison road has never run on a real article yet.

## The section count

- `budget` = the **midpoint** of the word band. Not the ceiling. A 2,800-3,800 band gives 3,300.
  With no band at all it falls back to **1,500**.
- `sec_target` = `budget / 300`, minimum 4. (300 is `WORDS_PER_SECTION` in config.)
- The prompt calls this a **ceiling**: fewer is better, never exceed it. Code still does not enforce
  it, but an overrun now prints a loud line so it is visible in the run.

Why the ceiling exists: without it nothing connects the word budget to the section count, and an
article can come out at 24 sections on a 2,800-word budget — 117 words each, which is not writable.

## Who decides what

**The AI decides:**
- the spine
- how many sections, their order, their headlines, their jobs
- which boxes go in which section
- **the H3s inside each section: their titles, and which boxes sit under each**
- **which boxes open the section, above the first H3 (`lead_boxes`)**
- which boxes get benched, and why
- which sections need extra research, and what to research
- which sections become a table, and its columns
- **which sections become a list, and whether it is numbered or bulleted**
- (listicle only) the per-item contract `item_fields`, **and which sections are items**

**The code decides:**
- numbering the boxes (`#1` to `#N`, in plan order)
- the budget and the section ceiling
- throwing away any box number that does not exist
- **making sure a box appears exactly once inside a section**, across the lead and every H3
- **folding an H3 with no title back into the lead** (an untitled H3 is not a heading)
- **accepting a flat `boxes` list** when neither `lead_boxes` nor `h3s` came back, so a malformed
  reply loses its sub-headings rather than its whole section
- warning when two sections claim the same box (a warning, **not** a rejection)
- keeping a table only if it named **2 or more columns**. A `"table": {}` with no columns is dropped
- **keeping a list only if its kind is `numbered` or `bulleted`**. Anything else is dropped
- capping `item_fields` at 4
- listing every unused box, and flagging **any** of them with no reason given
- **coverage**: re-checking how many of the research promises (gaps, table-stakes H2s, PAA questions)
  survived into the real sections. The architect never sees those promises, so this is a report on
  what happened, not something the design was steered by
- **stripping the developer header out of the format rulebook** before it reaches the prompt
- hard stop if the AI returned no sections at all

## Real numbers from the 4 articles

| Article | Archetype | Budget | Boxes | Sections | Ceiling | Authored H3s | Benched |
|---|---|---|---|---|---|---|---|
| running-hiring-hackathon | how-to-guide | 3,300 | 56 | 10 | 11 | 26 | 1 |
| the-type-d-personality-label | answer-bait | 2,800 | 38 | 9 | 9 | 13 | 0 |
| strategic-interview-questions | listicle | 6,500 | 67 | 14 | 22 | 6 | 44 |
| the-real-cost-recruitment | data-report | 3,500 | 39 | 12 | 12 | 29 | 3 |

All four are at or under their section ceiling. The listicle is 12 items plus 2 supporting sections.

**Read the H3 counts with care.** These runs predate the paragraph maths described above, so two
articles are over-headed: the hackathon article carries 36 headings on 3,300 words and cost-per-hire
carries 41 on 3,500. Re-running is item 6 in Part 7.

---

## The prompt: structure-simple.md

This is the main prompt of the whole architect. The other three structure prompts are the same file
with small additions, which I show right after.

```
THE COMPANY publishing this article: {{BRAND}} — {{ABOUT}}

You are designing the final structure of an article's BODY — the exact sections, in the exact order
the article will be written, and the sub-headings inside them.

THE ARTICLE (what we are building):
- Asset title: {{TITLE}}
- Distinct angle (what this article is built to deliver): {{ANGLE}}
- H1: {{H1}}
- What this article IS about: {{WORLD_ABOUT}}
- What this article is NOT about: {{WORLD_NOT_ABOUT}}

WHO THIS ARTICLE IS FOR — the reader every decision below is made for:
{{PERSONA}}

THE FORMAT'S REQUIRED SHAPE:
{{FORMAT_STRUCTURE}}

THE MATERIAL — numbered BOXES. Each box is one group of evidence cards on one narrow sub-topic,
shown grouped under the original section (H2) it came from. Those box labels are working notes from
an earlier planning step: they are NOT the article's headings, and their wording does not bind you.
{{BOXES}}

THE MAIN RULE — above everything else:
- STAY INSIDE OUR WORLD. Read the NOT ABOUT line above before you place anything. A box can be well
  evidenced, well written and genuinely interesting and still belong to a different field — the same
  words used by a different audience, a neighbouring industry, an academic or clinical use of the term.
  Those boxes are benched, whatever they match. This is the last step that can catch one: after you, it
  becomes a section and gets written.
- WRITE FOR THIS READER, NOT THE OTHER SIDE OF THE TABLE. Read the reader above before you place
  anything. A box can be squarely about our subject and still be written for the wrong person —
  advice for the candidate in an article for the recruiter, for the patient in an article for the
  clinician, for the employee in an article for the manager. The words overlap completely, so this is
  easy to miss and impossible to fix later: the section gets written and the reader wonders who it
  was for. Bench those with everything else that does not belong.
- The article must speak about ONE main idea from start to finish, and it must READ as one continuous
  piece: each section following naturally from the one before, building a single argument a reader can
  follow top to bottom. A section that pulls the article into a side-topic does not belong in it.
- NOTHING IN THIS ARTICLE MAY CONTRADICT ANYTHING ELSE IN IT. Two sections that argue opposite ways,
  or two boxes inside one section whose figures or conclusions disagree, leave the reader unable to
  act and cost the piece its authority. Where the material genuinely conflicts, you have two honest
  options: place the better-evidenced side and bench the other with its reason, or give the
  disagreement ONE section that names it and resolves it. Never let a contradiction sit unexplained
  in two different places.
- NEVER pad a section with material that does not belong just to fill it out. A reader feels it
  immediately. If a section cannot be built from material that genuinely fits, leave its boxes empty.

════════════════════════════════════════════════════════════════════════
HOW MANY SECTIONS THIS ARTICLE CAN CARRY

This article is budgeted at about {{WORD_BUDGET}} words, and a section needs roughly
{{WORDS_PER_SECTION}} words to make its point, back it and say what it means. That is
{{PARAGRAPHS_PER_SECTION}} paragraphs of about {{WORDS_PER_PARAGRAPH}} words each.

So {{SECTION_TARGET}} sections is the CEILING. It is a maximum, not a target. Fewer is better, and
NEVER exceed it.

Every heading you add takes words from all the others, so a list at the ceiling means every section
is written to the bone. Two sections a reader would answer the same way are one section. If the
material honestly fills only half the ceiling, return half — a shorter article that lands beats a
longer one that repeats itself.

The format's required shape above wins if it asks for something different.


HOW TO BUILD IT — work in this order; each decision feeds the next:
1. The SPINE first: one short paragraph stating what this whole article argues, for whom, and what
   the reader should be able to do at the end. Every section must serve it.

2. Then the sections, in the exact order the final article should read. For each one,
   write its JOB before its headline: one or two sentences saying what that section must deliver
   and how it moves the argument forward (including what it depends on or sets up). Then give it a
   real, publishable HEADLINE (an actual article heading, not a label) that names what the job
   describes.

3. Then fill each section with its boxes. Answer only with box numbers shown above — never invent a
   number. Each box belongs in ONE section; two sections must not share the same box. If a section
   genuinely does not have good-enough material among the boxes, do NOT force-fit boxes into it —
   leave its boxes empty.

   THE BOXES MUST ANSWER THE HEADLINE. Before you move on, read the headline back as a question and
   check that the boxes you just placed can actually answer it. Material that is ABOUT the subject
   but never reaches the answer produces a section that circles for four paragraphs and never lands,
   which is the most common way one of these articles fails. If the boxes cannot answer it, do one of
   two things: change the headline to what the boxes CAN answer, or keep the headline and name the
   missing answer in "needs_research". Never leave a heading the material cannot pay off.

4. Then shape the INSIDE of each section — and MOST SECTIONS GET NO SUB-HEADINGS AT ALL.

   DO THE ARITHMETIC FIRST:
     · a sentence runs about {{WORDS_PER_SENTENCE}} words
     · a paragraph runs about {{SENTENCES_PER_PARAGRAPH}} sentences, so about {{WORDS_PER_PARAGRAPH}} words
     · a section is about {{PARAGRAPHS_PER_SECTION}} paragraphs, so about {{WORDS_PER_SECTION}} words

   Look at the boxes you placed in this section and ask: written properly, with nothing padded and
   nothing repeated, how many PARAGRAPHS is this material actually worth? Count distinct points, not
   cards — twelve cards making the same point are one paragraph.

     · {{PARAGRAPHS_PER_SECTION}} PARAGRAPHS OR FEWER -> NO sub-headings. Every box goes in
       "lead_boxes" and "h3s" is []. This is the NORMAL case: a section of the normal size does not
       get split. A sub-heading over a paragraph of text is a label, and a page of those reads as
       padded however good the writing is.
     · MORE THAN THAT -> it may split, and each sub-heading needs at least
       {{PARAGRAPHS_PER_SUBHEAD}} paragraphs of its OWN material (about {{MIN_WORDS_PER_SUBHEAD}}
       words). Five paragraphs is ONE sub-heading, not two. Seven is two.

   THE COUNT DECIDES HOW MANY SUB-HEADINGS, NEVER WHERE THEY GO. You split by BOX, so the boundary
   falls where the material changes subject. Never place a sub-heading to break up a long stretch of
   text; place it where one part of the section genuinely ends and another begins. If you cannot find
   a natural break, the section did not need splitting.

   A TABLE OR A LIST DOES NOT COUNT towards those paragraphs. A section built around one table is
   usually two or three paragraphs plus the table, so it needs no sub-heading.

   Then, for a section that does get them:
   - "lead_boxes" holds the boxes that open the section, above the first sub-heading.
   - For each H3, write its title and list the boxes that sit under it.
   - The H3 titles are yours to write, in the same voice as the headlines: specific, publishable,
     never a label. Do not copy the box labels; they are planning notes, not headings.
   - Every box you gave this section must appear exactly ONCE, in "lead_boxes" or under one H3.
     Never in two places, never in none.
   - Never more than three sub-headings in one section. If the material needs more than three, this
     was two sections and you should have split it in step 2.

THE MECHANICS:
- Design the BODY only. The intro, TL;DR, CTA and FAQ are added later by another step —
  do not create them, do not reserve space for them, do not force-feed them.
- If the format's required shape above names a block (a methodology block, an appendix, a definition
  block), you MUST create a section for it. The ONLY blocks another step adds are the intro, TL;DR,
  CTA and FAQ.
- BENCHING: before benching a box, check whether one of your own sections could naturally host it.
  Bench what no section genuinely wants, and bench what would pull the article away from its one main
  idea. Not every box must be used — leave out what the article does not honestly need. But EVERY box
  you leave out needs one line in "benched" saying why. No box is ever dropped silently.
- RESEARCH: a section that cannot be written well from the boxes it holds raises a research request.
  Put the H3 titles you want researched in that section's "needs_research".
    · FACTS ONLY: data, pricing, benchmarks, named studies, real-world figures, dates.
    · NEVER JUDGMENT: how to score, rank, weigh or prioritise something is your call, not the web's.
    · WRITE THE TITLE AS IT WILL BE USED — it is passed downstream word for word. Make it specific
      and self-explanatory, with the metric, segment or timeframe inside the title itself.
    · RAISE IT ON QUANTITY TOO: a section resting on one or two cards lacks material however well
      those cards fit. Raise a marker rather than stretch the little you have.
    · As many as the section genuinely needs, and none at all for sections already well covered.
- TABLES: if a section would repeat the same sentence shape for every item — six criteria each with
  a weight and score bands, four options each rated on the same axes, three cost categories each with
  a range and a driver — give it a "table" and name the columns. An argument is never a table; a
  reader forced to hold six parallel things in their head is why the table exists.
  AT MOST TWO TABLES IN THE WHOLE ARTICLE. Most articles need one. Many need none.
  A TABLE YOU CANNOT FILL IS WORSE THAN NO TABLE. Before marking one, check the boxes actually hold
  something for every cell. Where a column would be empty, raise it in that same section's
  "needs_research" naming the exact missing data — "AI-use scoring bands from published hiring
  rubrics", not "more on rubrics". You are already raising research for thin sections, and a
  half-empty table is a thin section.
  If the title or the angle promises a named artifact — a rubric, a scorecard, a checklist, a
  comparison — one section must RENDER it, not describe it. A rubric explained in paragraphs is not
  a rubric; the reader came for the object.
- LISTS: if a section's payload is genuinely a set of parallel items, give it a "list" and say which
  kind. ALL THREE of these must hold, or leave it as prose:
    · THREE OR MORE items. Two things are a sentence with "and" in it.
    · EACH ITEM STANDS ALONE. If item two only makes sense after item one, that is an argument, and
      argument belongs in prose.
    · EACH ITEM IS SHORT — a line or two. An item needing four sentences is a paragraph in disguise.
  Then choose the kind, and the choice is not cosmetic:
    · NUMBERED when the ORDER MATTERS — steps performed in sequence, a ranking, a countdown. The
      numbers are telling the reader where they are.
    · BULLETED when the items are PARALLEL and could be read in any order.
  Never mark a section as a list to break up long prose. A section that is mostly bullets reads as a
  slide deck, and a list of near-identical stubs is the most obvious machine-writing tell there is.
  Most sections are prose and return null.

Return ONLY this JSON, nothing else:
{"spine": "<what this whole article argues, for whom, and what the reader can do at the end>",
 "sections": [{"job": "<what this section must deliver and how it moves the argument>",
               "headline": "<the section's real heading>",
               "lead_boxes": [<box numbers that open the section, above any sub-heading>],
               "h3s": [{"h3": "<a sub-heading you write>", "boxes": [<box numbers under it>]}],
               "table": {"columns": ["<column>", "..."]} | null,
               "list": {"kind": "numbered | bulleted", "of": "<one line: what the items are>"} | null,
               "needs_research": ["<H3 title to research>", "<another H3 title>", ...]}],
 "benched": [{"box": <n>, "why": "<one line: why this box is not in the article>"}]}
(h3s is [] for a section that needs no sub-headings, which is many of them;
 needs_research is OPTIONAL — include it only for sections that genuinely need research;
 table and list are null for every section that is plain prose, which is most of them)
```

### That prompt, block by block

- **The setup.** Who is publishing, what the article is, the world, and the format rulebook.
- **"THE MATERIAL"** - all 39, 56 or 67 boxes, each with its label, its card count and a one-line
  gloss of every card. The biggest block in the prompt. Note the sentence after it: those labels are
  planning notes, **not** headings, and their wording does not bind the architect.
- **"THE MAIN RULE"** - four rules, in order. Stay inside our world beats everything. Then one main
  idea. Then **nothing may contradict anything else**, with two allowed resolutions and no third.
  Then never pad.
- **"HOW MANY SECTIONS"** - the ceiling. Fewer is better, never exceed it, and if the material only
  fills half the ceiling then return half.
- **"HOW TO BUILD IT" 1 to 4** - the order matters:
  1. **Spine first**, so every section has something to serve.
  2. **Job before headline**, which stops the AI naming a section before it knows what it does.
  3. **Boxes, then the answer check.** Read the headline back as a question and confirm the boxes can
     answer it. If they cannot: change the headline, or raise research. This is the rule aimed at the
     four-paragraph section that circles and never lands.
  4. **The inside of the section.** 2 or 3 paragraphs of prose, and past that it gets H3s the
     architect writes itself. Lead boxes above the first sub-heading, then boxes under each H3. Every
     box exactly once. Tables and lists do not count towards the paragraph budget.
- **"THE MECHANICS"** - six rules:
  - **Body only.** Intro, TL;DR, CTA and FAQ belong to a later step.
  - **Format blocks are mandatory.** If the rulebook names a methodology block, it must exist.
  - **Benching.** Leaving material out is allowed, but **every** dropped box needs one line.
  - **Research.** Facts only, never judgment, title written exactly as it will be used, and raise it
    on thinness as well as absence.
  - **Tables.** When to use one, a cap of two per article, a table you cannot fill is worse than
    none, and if the title promises a rubric one section must render it.
  - **Lists.** Three tests that must all hold, then numbered when the order matters and bulleted when
    the items are parallel. Never used to break up long prose.
- **The JSON block** - `lead_boxes` and `h3s` carry the section's shape, `table` and `list` are null
  for most sections, `needs_research` is optional.

### The other three structure prompts

**`structure-listicle.md`** is the same file, plus:
- a `{{ENTITIES}}` block listing the items **with the card count behind each**
- a budget block that replaces the shared section ceiling entirely
- step 2 says give each surviving item ONE section, and put **every item before any supporting section**
- an `is_item` flag on every section, and a `dropped_items` list
- and the per-item contract block

**The budget block.** A listicle's length is governed by its items, not by a section count, so it
gets its own arithmetic instead of the shared ceiling:

```
FIT THE LIST TO THE BUDGET — do this arithmetic before you design anything else.

Every listicle needs some supporting sections: how the list was chosen, how to use it, what the
reader does next. Those come out of the budget FIRST, not out of whatever is left over.

An item written properly needs about {{MIN_ITEM_WORDS}} words: enough to say what it is, why it
matters, and whatever the per-item contract below requires of it. Below that it becomes a stub, and a
shorter list that is fully written beats a longer list of stubs.

  1. RESERVE {{SUPPORTING_RESERVE}} words for the supporting sections, of which you may write at
     most {{SUPPORTING_MAX}}. What remains is the ITEM BUDGET.
  2. Divide the ITEM BUDGET by the number of items above. If every item clears {{MIN_ITEM_WORDS}}
     words, keep them all and move on.
  3. If it does not, work out how many items the ITEM BUDGET can carry, and drop the rest.
     Name every item you drop in "dropped_items" with one line saying why.
  4. Never go below {{MIN_ITEMS}} items. A list shorter than that has stopped being a list. If even
     {{MIN_ITEMS}} items cannot clear the word bar, keep the {{MIN_ITEMS}} strongest anyway and say
     so — do not quietly shrink the article into a different format.

WHICH ITEMS TO DROP — this is a judgment, not a sort.
The card count shown against each item tells you how much evidence sits behind it, and it is where
you start. It is NOT the whole answer. An item with 4 cards that answers something the reader
genuinely needs, and answers it with a real figure or a named standard, beats an item with 20 cards
that only restates what the article already says elsewhere. Keep what the reader would miss most,
drop what they would not notice was gone. When two items are genuinely close, the better-evidenced
one stays.

TWO THINGS YOU MAY NOT DO:
  · Never drop an item to reach a rounder number, or because the list looks untidy. The word budget
    is the ONLY reason to drop one.
  · Never drop an item silently. Every one gets a line in "dropped_items".

Whatever items survive each get their own section, and the supporting sections come after them.
Two supporting sections a reader would answer the same way are one section.
```

The three numbers are `LISTICLE_SUPPORTING_SECTIONS` (3, so 900 reserved words),
`LISTICLE_MIN_ITEM_WORDS` (200) and `LISTICLE_MIN_ITEMS` (5). Worked through on real bands:

| Band | Budget | After reserving 900 | Room for | Result |
|---|---|---|---|---|
| 5,500-7,500 | 6,500 | 5,600 | 28 items | keeps all 12 |
| 2,400-3,200 | 2,800 | 1,900 | 9 items | **keeps 9, drops 3** |
| 1,000-1,400 | 1,200 | 300 | 1 item | **hits the floor, keeps 5** |

`LISTICLE_SUPPORTING_SECTIONS` is the one number tied to article length. It is a flat word count, so
if the house band ever drops to around 1,500 it would eat more than half the article and should
become a percentage instead.

**The per-item contract block.**

```
THE PER-ITEM CONTRACT — the one thing that makes a listicle useful instead of a list.
Read the article's distinct angle above. If it promises the reader something that must come back on
EVERY item, name those parts in "item_fields". They become a hard requirement: every ITEM section
must end with exactly those labelled parts, in that order, every time.

WHAT COUNTS AS A CONTRACT FIELD — something that genuinely differs from item to item:
  · a list of mistakes might carry "What it costs you" and "The fix" on every mistake
  · a list of tools might carry "Best for" and "Pricing" on every tool
  · a list of interview questions might carry "Strong answer" and "Weak answer" on every question
  · a list of tax deductions might carry "Who qualifies" and "What you can claim" on every one

WHAT IS NOT A CONTRACT FIELD — anything the reader needs ONCE rather than per item. A scoring method,
a selection methodology, a how-to-use-this guide, a rubric, a set of general principles: each of those
is ONE supporting section of its own, placed after the items. Bolting a once-only thing onto the end
of every item is how a list of twelve turns into twelve near-identical blocks, and it is the most
common way this format fails.

THE TEST, for each field you are considering: could a reader lay this part side by side across all
the items and learn something from the differences? "Pricing" differs per item, so it passes. "How we
scored these" is the same answer every time, so it fails and becomes its own section instead.

- Take the fields from what the ANGLE actually promises, in the angle's own words. Do not invent a
  richer contract than the article promised, and do not quietly drop part of what it did promise.
- 2 to 4 fields, and fewer is better.
- Each must be something a writer can produce for EVERY item from that item's own cards; a field only
  half the items could fill is not a contract, it is a wish.
- Label them as they should appear to the reader.
- If the angle promises nothing repeating — the items are simply a list — return an empty list. An
  invented contract is worse than none: it forces filler onto items that never needed it.

THE CONTRACT APPLIES TO ITEM SECTIONS ONLY. Mark every section with "is_item": true when it IS one of
the list items above, and false when it is a supporting section. A supporting section never carries
the contract and never gets one of its labelled parts tacked onto the end.
```

**Why the scoping matters.** Without `is_item`, nothing downstream can tell a list entry from a
supporting section, and the contract lands on both. A section like "Build an Interview Question Bank"
then ends with a Strong Answer and a Weak Answer, which is filler. **The writer does not read
`is_item` yet**, so this only half works today — see `../PENDING-WRITER-CHANGES.md`.

**`structure-comparison.md`** is the same file, plus four blocks of context and one rule.

The context, all of it computed by the pre-calls:

```
THE PRODUCT CATEGORY this article's reader is buying: {{CATEGORY}}

THE OPTIONS this comparison covers (each earns its own section, in the format's order). An earlier
step read the material, decided which options this article is really about, and shortlisted them.
Where an option is short of information on one of the yardsticks below, that gap is named against it:
{{ENTITIES}}

OPTIONS THE SAME STEP REMOVED, because the material could not speak to enough of the yardsticks
for them:
{{DROPPED}}
They were removed on purpose. Do not build a section about any of them, and do not use their cards
anywhere in this article — not as an aside, not as an example, not inside another section's prose.

THE YARDSTICKS every option's section should speak to:
{{YARDSTICKS}}
```

`{{ENTITIES}}` now looks like this in a real run:

```
- Alpha
- Beta   MISSING INFORMATION ON: setup effort, support
```

Plus a rule saying what to do about a gap, and the brand rule:

```
- MISSING YARDSTICKS: an option above may be marked short of information on one or more yardsticks.
  What to do about it is your call. If that gap would leave the option's section unable to answer
  something the reader is genuinely comparing on, name the missing yardstick in that section's
  "needs_research" as a specific H3 title. If the gap does not matter for this article, leave it.
  There is no limit on how many of these you raise.
- {{BRAND}} is the company publishing this article. IF {{BRAND}} is among the options above, it is an
  option like any other: it keeps its own section, it appears in EVERY table, score grid and ranked
  list that covers the other options, judged on the same yardsticks and on the same scale. It may
  score below a rival — say so plainly when the evidence says so. It may never be missing from a
  comparison the others are in: a grid that scores every rival but not the publisher reads as though
  the publisher has something to hide, and costs the article its whole credibility.
  If {{BRAND}} is NOT among the options (this article compares something else entirely — methods,
  approaches, categories, providers we don't sell against), this rule does not apply at all: do not
  insert {{BRAND}} into the comparison.
```

**`structure-template.md`** is the same file, plus one line and one extra JSON field:

```
- This article wraps a downloadable ARTIFACT (a template / checklist / sheet / PDF). Besides the page
  structure, DECIDE the artifact itself: what kind of file it should be, and which boxes' content goes
  INSIDE the artifact (the template's own rows/fields) versus on the page around it.
```
```
 "artifact": {"type": "<sheet | pdf | checklist | doc>", "contains_boxes": [<box numbers>], "note": "<one line on what the artifact is>"}
```

---

## The listicle pre-call: detect-items.md

Runs before the listicle structure call. Finds the actual list items.

The cap is a flat **12** (`LISTICLE_MAX_ITEMS`). It replaced a sliding formula that let a 7,500-word
band ask for 30. The cap is a sentence in the prompt and is not re-checked in code.

```
You are finding the LIST ITEMS of a listicle — the concrete things the reader came for.

THE COMPANY publishing this article: {{BRAND}} — {{ABOUT}}

THE ARTICLE (what we are building):
- Asset title: {{TITLE}}
- Distinct angle (what this article is built to deliver): {{ANGLE}}
- What this article IS about: {{WORLD_ABOUT}}
- What this article is NOT about: {{WORLD_NOT_ABOUT}}

WHO THIS ARTICLE IS FOR:
{{PERSONA}}

THE MATERIAL (the planned sections — H2s, their H3s, and the evidence cards under each):
{{MATERIAL}}

The items come from the CONTENT of the material, not from brands or publishers. What an item IS
depends entirely on what the article promises. Examples across different subjects, so you get the
idea rather than the subject:
- "common onboarding mistakes"        -> each MISTAKE
- "best project management tools"     -> each TOOL
- "tax deductions freelancers miss"   -> each DEDUCTION
- "strategic interview questions"     -> each individual QUESTION, as it would be asked aloud
- "reasons a warehouse audit fails"   -> each REASON

Rules:
- Return at most {{MAX_ITEMS}} items. A shorter list that is fully written beats a longer list of stubs.
- STAY INSIDE OUR WORLD. Read the NOT ABOUT line. An item can appear in the material, read well, and
  still belong to a different field or a different audience. Drop it, whatever it matches.
- Two items a reader would answer the same way are ONE item. Merge near-duplicates (the same thing in
  different wording, tense, or scale) and keep the clearest phrasing.
- Keep an item ONLY if the material contains evidence about THAT item specifically — an example, a
  standard, a figure, a named case. An item mentioned only in passing inside a general box does not
  qualify.
- Every item must serve the article's angle above. Drop items that belong to a neighbouring topic
  even when the material mentions them.
- Each item must be complete and usable as it stands, never a fragment or a stub.
- Pick the true grain the article promises — the individual things, not the categories they fall into.
- Only items the material actually supports. Never invent one.
- Do NOT list the studies, publishers, research bodies, authors or data vendors the cards cite. Those
  are the sources OF the material, not items IN the article, and they appear often enough to look
  like items if you count mentions.
- Return each with a rough count of the cards supporting it.

Return ONLY this JSON, nothing else:
{"entities": [{"name": "<the list item>", "count": <supporting cards>}]}
```

**In plain terms:** find the things, merge duplicates, stay inside our world, drop anything the
material does not actually have evidence for, and never mistake a source (a research body, a
publisher) for an item.

## The comparison pre-calls (three of them)

These have never run on a real Testlify article yet. Read them, but do not spend long here.

### detect-entities.md - who is being compared

```
You are finding the OPTIONS of a comparison article — the named things this article will compare.

THE COMPANY publishing this article: {{BRAND}} — {{ABOUT}}

THE ARTICLE (what we are building):
- Asset title: {{TITLE}}
- Distinct angle (what this article is built to deliver): {{ANGLE}}
- What this article IS about: {{WORLD_ABOUT}}
- What this article is NOT about: {{WORLD_NOT_ABOUT}}

WHO THIS ARTICLE IS FOR:
{{PERSONA}}

THE MATERIAL (the planned sections — H2s, their H3s, and the evidence cards under each):
{{MATERIAL}}

Your job: list the NAMED options a reader of THIS article would actually be choosing between. What counts
as an option depends entirely on the article — it might be software products, service providers, agencies,
vendors, platforms, courses, banks, or anything else this article genuinely compares.

Examples across different domains (so you get the idea, not the domain):
- "best video interview software"        -> HireVue, Spark Hire, Willo, VidCruiter...
- "top recruiting agencies for startups" -> the named agencies
- "best coding bootcamps"                -> the named bootcamps
- "business credit cards compared"       -> the named cards

Rules:
- IT MUST BE THIS READER'S OPTION. An option aimed at the other side of the table — the
  candidate rather than the recruiter, the employee rather than the manager — is not this article's
  option, however well the material covers it.
- STAY INSIDE OUR WORLD. Read the NOT ABOUT line. An option that belongs to a neighbouring field or a
  different audience is not an option here, however often the material names it.
- An option must be something a buyer of THIS article would put on ONE shortlist against the others.
  A product from an ADJACENT category that the material merely mentions — a component, an integration,
  a supplier to the category — is not an option, however often it appears.
- NEVER list tools that produced or fetched the research itself (scrapers, search APIs, data vendors).
- Drop anything mentioned by fewer than 3 cards — one passing mention is not an option.
- Only NAMED options that genuinely appear in the material. Never invent one.
- Give each a rough count of how many cards mention it.
- Do NOT list the studies, publishers, or data sources the cards cite (SHRM, Gartner, a university) —
  those are sources, not options — unless the article genuinely compares them as options.

Return ONLY this JSON, nothing else:
{"entities": [{"name": "<option>", "count": <cards mentioning it>}]}
```

### find-yardsticks.md - what they are measured on

```
You are choosing the YARDSTICKS of a comparison article — the axes every option gets measured on.

THE COMPANY publishing this article: {{BRAND}} — {{ABOUT}}

THE ARTICLE (what we are building):
- Asset title: {{TITLE}}
- Distinct angle (what this article is built to deliver): {{ANGLE}}
- What this article IS about: {{WORLD_ABOUT}}
- What this article is NOT about: {{WORLD_NOT_ABOUT}}

THE OPTIONS being compared:
{{ENTITIES}}

THE MATERIAL (the planned sections — H2s, their H3s, and the evidence cards under each):
{{MATERIAL}}

Pick the 4-6 yardsticks that (a) a buyer making THIS decision genuinely weighs, and (b) the material can
actually speak to for these options. Read the NOT ABOUT line first: an axis that matters to a
neighbouring field's buyer, but not to this article's reader, is not a yardstick here. Name each in 2-4 plain words (e.g. "pricing", "detection accuracy",
"integration effort", "support quality").

The yardsticks must measure DIFFERENT things — no two may be restatements of the same axis (four axes that
are all about detection is one axis, not four). Together they should cover the whole decision: what the
product can DO, how well it FITS and what it takes to set up, what the EXPERIENCE is like, and what it COSTS.

Return ONLY this JSON, nothing else:
{"yardsticks": ["<yardstick>", ...]}
```

Code keeps at most 6.

### filter-tools.md - which options have enough material to earn a section

```
You are checking which options have enough material to earn their own section in a comparison article.

THE COMPANY publishing this article: {{BRAND}} — {{ABOUT}}

THE ARTICLE (what we are building):
- Asset title: {{TITLE}}
- Distinct angle (what this article is built to deliver): {{ANGLE}}
- What this article IS about: {{WORLD_ABOUT}}
- What this article is NOT about: {{WORLD_NOT_ABOUT}}

THE OPTIONS:
{{ENTITIES}}

THE YARDSTICKS every option is measured on:
{{YARDSTICKS}}

THE MATERIAL (the planned sections — H2s, their H3s, and the evidence cards under each):
{{PAGES_NOTE}}{{MATERIAL}}

FIRST, name the category in one line: what kind of thing is this article's reader actually choosing
between? It might be software, agencies, providers, courses, accounts, methods or anything else.
Then remove from consideration any option that is not that kind of thing, however well covered it is
— a component of the category, an integration with it, or a supplier to it is not a competitor
within it. Remove anything belonging to the NOT ABOUT world for the same reason.

THEN, for EACH remaining option, go through the cards and SHOW YOUR WORK: list which yardsticks the
material has real information about for THIS option. Then decide: KEEP the option if it has
information for at least {{MIN_PCT}}% of the yardsticks; DROP it otherwise.

Sanity rules:
- RANK CHECK, before you answer: sort every option by its card count. If any option you DROPPED has more
  cards than any option you KEPT, you have misread the material — recount that pair and name the yardstick
  you found for the better-covered one, or move it back into keep.
- {{BRAND}} is the company publishing this article. When it appears among the options, NEVER drop
  it — it always keeps its place, evaluated on the material it has.
- Judge from the cards only; never from your own knowledge of these options.

Return ONLY this JSON, nothing else:
{"category": "<the kind of thing the reader is choosing between>",
 "keep": [{"name": "<option>", "yardsticks_covered": ["<yardstick>", ...]}],
 "dropped": [{"name": "<option>", "yardsticks_covered": ["<yardstick>", ...]}]}
```

`{{MIN_PCT}}` is `SHAPE_MIN_YARDSTICK_PCT`, set to **60** in config.

# STEP 2 — ENRICH

**File:** [enrich.py](scripts/enrich.py) · **Writes:** `architect/structure.json`, `architect/enriched-cards.json`

## What it does

Step 1 could mark any section with `needs_research`. This step goes and does that research, on the
live web, and turns the results into new cards.

**If there are zero markers, this step does nothing but rename the file.** It promotes
`structure.shaped.json` to `structure.json` and moves on. Two of the four finished articles had zero
markers.

## The loop, per marker

For each `needs_research` H3:

1. **Plan queries** - `plan-queries.md` writes up to **3** web search queries.
2. **Search** - each query goes to DataForSEO's Google SERP, depth 10, **organic results only**, ads
   and every other block excluded.
   - Before any of this, the code checks the **DataForSEO balance**. Below `DFS_MIN_CREDITS` (1.0) it
     falls back to a single Claude web-search call (`search-urls.md`).
   - If the run is pinned off Claude (`NO_CLAUDE=1`), the fallback returns nothing and the step
     records an honest failure rather than quietly spending Claude quota.
3. **Download** - the result URLs from all 3 queries are **rank-interleaved** (first result of query 1,
   first of query 2, first of query 3, then the seconds, and so on), deduplicated, and then downloaded
   one by one until **15 pages** load successfully. A page under 500 characters is skipped. Whitespace
   is collapsed **before** truncating (a raw slice of a heavy page would otherwise hand the extractor a
   navigation menu), then the top **8,000 characters** are kept.
4. **Extract cards** - `extract-cards.md` turns the pages into cards.
5. **Validate and attach** - code throws away any card whose source URL was not one of the pages we
   actually downloaded. Survivors get IDs starting at **9001** and are attached to their section as a
   new H3.

**Speed:** 8 markers run at once on the DataForSEO route. The Claude fallback runs one at a time,
because the CLI cannot take the load.

**Failure is never fatal.** A marker that finds nothing logs `nothing usable found` and the rest carry
on.

## Who decides what

**The AI decides:** the search queries, and what counts as a card worth building from a page.

**The code decides:** the balance check and which route to use, how many pages to download, how much
of each page to keep, rejecting cards with an unknown source URL, minting the IDs, and where the new
H3 lands.

## Real numbers

| Article | Markers | Resolved | New cards |
|---|---|---|---|
| running-hiring-hackathon | 2 | 2 | yes |
| strategic-interview-questions | 0 | - | - |
| the-real-cost-recruitment | 5 | 3 | yes |
| the-type-d-personality-label | 0 | - | - |

Two of five markers on the cost-per-hire article came back with **nothing usable**. The section still
exists, just thinner than planned. Nothing acts on that.

## The prompts

### plan-queries.md

```
You are planning web research for ONE missing sub-topic (an H3) of an article.

THE COMPANY publishing this article: {{BRAND}} — {{ABOUT}}
THE ARTICLE: {{TITLE}} — distinct angle: {{ANGLE}}
- What this article IS about: {{WORLD_ABOUT}}
- What this article is NOT about: {{WORLD_NOT_ABOUT}}
WHO THIS ARTICLE IS FOR:
{{PERSONA}}
THE SECTION being enriched: {{SECTION_HEADLINE}}
Its JOB — what this section has to deliver for the reader:
{{SECTION_JOB}}
THE H3 that needs research (this exact sub-topic): {{H3}}

Write up to {{N}} web search queries that would genuinely find this material — phrased the way real
search engines are used: short, concrete, varied (statistic phrasings, survey names, year-scoped
variants), so one dead end does not sink the topic.

AIM AT THE JOB, NOT AT THE WORDING. A heading is a label and can be vague; the job above says what
the section must actually give the reader. Read it before you write a query, and search for the
material that pays that job off. Where the H3's phrasing and the job point in slightly different
directions, the job is the truer target.

KEEP EVERY QUERY INSIDE OUR WORLD. Read the NOT ABOUT line. Where this subject shares a word with a
different field, a bare query will return that field's pages — and every card built from them looks
plausible and is wrong for this reader. Put the setting or the audience INTO the query itself
(who is doing this, in what context), so the results cannot drift.

Return ONLY this JSON, nothing else:
{"queries": ["<query>", ...]}
```

**The point:** three varied queries, aimed at the section's JOB rather than its heading, and the
world rule repeated here because a bare query is exactly how a search lands in the wrong field.

Why the JOB matters here: this is the step that decides what we go out and buy. A heading like
"Appendix: Full Methodology and Data Sources" sends the planner hunting for a report's own internal
sample size, which lives behind a membership. Its job points instead at which edition each figure
comes from and what stops two being compared, which is answerable in public.

### search-urls.md (the fallback only)

```
You have web search. Run the queries below and return the best result page URLs.

QUERIES:
{{QUERIES}}

Rules:
- Run every query. Collect the strongest organic results across all of them (skip ads/sponsored).
- Return up to {{MAX}} unique page URLs, most relevant first.
- Only REAL URLs that actually appeared in results — never constructed or guessed.

Return ONLY this JSON, nothing else:
{"urls": ["https://...", ...]}
```

### extract-cards.md

```
You are building evidence cards for ONE sub-topic (an H3) of an article, from freshly scraped web pages.

THE COMPANY publishing this article: {{BRAND}} — {{ABOUT}}
THE ARTICLE: {{TITLE}} — distinct angle: {{ANGLE}}
THE SECTION this belongs to: {{SECTION_HEADLINE}}
The section flagged this H3 as a research need. The H3 stays EXACTLY as written — you are filling it,
not renaming it:
H3: {{H3}}

THE SCRAPED PAGES (each labelled with its link; top slice of the article text):
{{PAGES}}

────────────────────────────────────────────────────────────────────────
THE CARD IS ALL THE WRITER WILL EVER SEE.

Your cards go straight to the writer of this article, exactly as you write them. That writer CANNOT
open the source link, CANNOT search the web, and CANNOT see the page you are reading now. If a fact
is not written inside the card, it does not exist as far as this article is concerned.

So every card has to stand completely on its own:
- THE ACTUAL NUMBER, never a promise of one. "The report gives an average cost per hire" is worth
  nothing. "The average cost per hire was $4,700" is the card.
- WHO SAID IT, AND WHEN. Name the publisher and the year inside the card, so the writer can credit
  the source in a sentence without looking anything up.
- WHAT IT COVERS. A figure means little without its scope — the sample size, the country, the
  industry, the period it measures. Where the page states it, the card carries it.
- NO POINTERS. Never write "see the source", "as detailed in the report", "the full methodology is
  available there". The writer cannot follow any of those.

One downstream rule makes this unforgiving: the writer is FORBIDDEN from writing a vague quantity
when its card does not hold the specific one, and is told to drop the claim instead. So a card that
gestures at a number does not produce a woolly sentence — it loses the fact altogether, after we
have already paid to go and find it.
────────────────────────────────────────────────────────────────────────

Create as many cards as the material honestly supports. The rules:
- Build ONLY from what these pages actually say — never your own knowledge, never fabricated.
  Joining and phrasing is fine; inventing is not.
- A card summarizes material from ONE page only. NO cross-page summarization — never blend two
  sources into one card. Multiple cards from the same page are fine.
- Each card: "gloss" (a one-line summary of the fact), "summary" (the card's content — a faithful
  summary of that page's relevant material, with the concrete numbers kept), "source_url" (that
  page's link, exactly as labelled above).
- If the pages turned up nothing genuinely useful for this H3, return an empty list. Never force
  weak cards.

Return ONLY this JSON, nothing else:
{"cards": [{"gloss": "...", "summary": "...", "source_url": "..."}]}
```

**Two rules carry this prompt.**

**One card, one page.** Never blend two sources into one card. That is what keeps every fact
traceable to exactly one link later.

**The card is all the writer will ever see.** The writer cannot open the link,
cannot search, and cannot see the page — so a card that says "the report gives the figure" without
the figure is worthless. Worse than worthless: the body writer is forbidden from writing a vague
quantity when its card lacks the specific one, and is told to drop the claim instead. So a thin
card does not produce a woolly sentence, it silently loses a fact we already paid to find.

# STEP 3 — ALLOCATE

**File:** [allocate_words.py](scripts/allocate_words.py) · **Writes:** a `word_target` on every section

## What it does

The shortest step. It gives each section a word count.

1. **Base** = the **midpoint** of the word band. A 3,000-4,000 band gives 3,500. Deliberately the
   midpoint, not the ceiling, so there is room to trim later.
2. **Share** = an AI reads every section (its heading, its job, what it covers, how many cards it has)
   and assigns each a **percentage** of the article.
3. **Target** = base × share. Code does the arithmetic so the shares always total 100 and the words
   always add up.

The AI is told explicitly to judge by **how much the section matters to the argument, not by how many
cards it holds**.

## The overwrite buffer, and why it is now zero

`WRITE_OVERWRITE_PCT` is **0**: the targets are planned straight to the band, with no buffer.

Measured on 2026-08-02: **the blending step trims nothing.** So the buffer became permanent overshoot.
Both articles were planned **above their own ceiling before a word was written** (band max 3,800 →
planned 3,961 → written 4,866; band max 7,500 → planned 7,800 → written 8,594).

`WRITE_OVERWRITE_PCT` now defaults to **0**. The note in the code says raise it only if a measured
trim step ever exists.

## The safety net

If the AI call fails or returns nonsense, the code falls back to an **even split** across all sections.
The pipeline never stalls here.

## Real numbers

| Article | Band | Base | Sum of targets | Sections |
|---|---|---|---|---|
| running-hiring-hackathon | 2,800-3,800 | 3,300 | 3,300 | 8 |
| strategic-interview-questions | 5,500-7,500 | 6,500 | 6,503 | 27 |
| the-real-cost-recruitment | 3,000-4,000 | 3,500 | 3,500 | 13 |
| the-type-d-personality-label | 2,400-3,200 | 2,800 | 2,800 | 9 |

The hackathon spread: 198, 231, 264, 264, 462, 495, 660, 726. The AI genuinely varied them.
The strategic spread: mostly 220 to 251, with four larger. On 27 sections there is not much room to
vary.

## The prompt: allocate-words.md

```
You are budgeting an article's length across its sections.

THE COMPANY publishing this article: {{BRAND}} — {{ABOUT}}

THE ARTICLE:
- Asset title: {{TITLE}}
- Distinct angle: {{ANGLE}}
- The spine: {{SPINE}}

WHO THIS ARTICLE IS FOR:
{{PERSONA}}

TOTAL LENGTH TO DISTRIBUTE: {{TARGET}} words (the body only).

THE SECTIONS — each with its job, what it covers, and the facts it actually holds:
{{SECTIONS}}

────────────────────────────────────────────────────────────────────────
Decide what SHARE of the article each section deserves, as a percentage. Work it in two passes, in
this order — they answer different questions and the order is what keeps the answer honest.

PASS 1 — IMPORTANCE SETS THE NUMBER.
Read the spine, then read each section's job. How much does this section matter to the argument, and
how much does THE READER ABOVE need from it? A section that would matter enormously to somebody else
— the other side of the table, a different seniority, a specialist — earns little here.

That, and only that, sets the first number. The section carrying the article's central claim earns
the most words even when it is thinly evidenced. A section that sets up, bridges or hands off earns
few even when it is stacked with facts.

ONE THING IS ALREADY PART-DECIDED FOR YOU: THE SUB-HEADINGS.
The step before this one either split a section into sub-headings or left it whole, based on how much
distinct ground its material actually covers. That count is real information, so use it. A section
with 2 sub-headings is carrying three separate stretches of ground — the opening plus each
sub-heading — and needs the words to cover them.

Every stretch needs about {{MIN_WORDS_PER_SUBHEAD}} words to be worth its heading. So a section with
N sub-headings needs at least (N + 1) x {{MIN_WORDS_PER_SUBHEAD}} words. A section with none has no
such floor and can be as short as its importance deserves.

This does NOT override importance. A section unimportant to the argument stays small even when it was
split — the split only tells you it cannot go below its floor without its sub-headings becoming
labels on single paragraphs. If you genuinely cannot give a split section its floor without starving
a more important one, give the important one its words and say so in the split section's reason.

WHEN THE ARTICLE IS A LIST, THE ITEMS ARE PARALLEL AND SHARE EVENLY.
Sections marked [LIST ITEM] below are the entries of a list, and a reader reads them side by side and
compares them. So they get ROUGHLY EQUAL shares. One item is not three times more important than
another because the research happened to turn up more material about it — that is an accident of
what was available, and letting it set the length makes the list read as though half the entries were
an afterthought.

Work it in this order when items are present: decide what share the ITEM BLOCK AS A WHOLE deserves
against the supporting sections, then divide that block evenly across the items. Vary by a little
where one genuinely needs more room, never by more than about a quarter either way.

Importance still ranks the supporting sections against each other, and ranks the item block against
them. It does NOT rank items against items.

PASS 2 — THE EVIDENCE IS A CEILING, NEVER A CLAIM.
Now read the facts each section actually holds, and ask ONE question of each: can this section be
WRITTEN to the length pass 1 just gave it, from this material, without padding? If it cannot, cut it
back to what the material honestly supports and move those words to a section that can use them.

The evidence only ever takes words away. It never earns them.

A long list of facts is not a claim on length. It is often the same point restated by twelve sources,
and it compresses into two sentences. So judge what is DISTINCT in the list, not how long the list
is: five facts that each say something new carry more words than forty that agree with each other.
Some sections show only their first {{CARD_CAP}} facts with a note saying how many more there are —
that note is there for honesty, not as an argument for a bigger share.

Rules:
- The shares must add up to 100.
- No section below 4 — anything that small should not be its own section.
- Give one short reason per section. Where pass 2 cut a section back, say so in that reason.

Return ONLY this JSON, nothing else:
{"allocation": [{"section": <index as listed>, "share": <percent>, "why": "<one short line>"}]}
```

# STEP 4 — SECTION KEYWORDS

**File:** [section_keywords.py](scripts/section_keywords.py) · **Writes:** `architect/_work/section-keywords.json`

## What it does

Decides which sections deserve a search keyword of their own, then buys real search data for those
sections only.

**This step edits nothing.** It writes one file that step 5 reads. That is deliberate: it is
research, not a decision about the article.

### Why it exists

Keywords are bought **here** rather than in the research phase, because research works from the
planned outline and the architect then redesigns those headings away. Buying against a plan that no
longer exists means paying for keywords whose sections were deleted. This step runs where the sections
are real and their evidence is final.

### 4a - the gate (free)

One AI call over the whole article. For every section it answers one question: **would a person type
this section's subject into Google as its own search?**

Most sections should be NO. They carry the argument, they do not answer a search. Nothing is bought
for a section the gate rejects.

Important detail in the code: a section the gate **never mentioned** is treated as NO. Silence must
never mean "spend money".

### 4b - the hunt (paid), for gated-YES sections only, in parallel

1. **Seeds** - an AI reads that section's **cards** (not just its heading) and writes 2 or 3 short
   seed phrases.
2. **Lookup** - each seed goes to DataForSEO `keyword_suggestions`, 80 phrases per seed.
3. **Filter (code)** - keep only phrases with monthly volume **>= 100** (`VOL_FLOOR`) and difficulty
   **< 40** (`KD_CEIL`).
4. **Show** - top 25 survivors by volume go to the picker.
5. **Pick** - an AI picks **one, or none**. Returning none is explicitly a good answer.
6. **Guard (code)** - if the picker returns a phrase that was not in the list it was shown, the pick is
   rejected outright.

## Real numbers

| Article | Sections | Gate said YES | Keywords actually found |
|---|---|---|---|
| running-hiring-hackathon | 8 | 3 | 0 |
| strategic-interview-questions | 27 | 11 | 4 |
| the-real-cost-recruitment | 13 | 7 | 1 |
| the-type-d-personality-label | 9 | 4 | 0 |

So the gate is doing its job (roughly a third to a half say yes, exactly as the prompt asks). But the
**hunt very often comes back empty**. Two of four articles found nothing at all. That is the filter at
work: on a narrow topic, few phrases clear 100 volume and under 40 difficulty.

Note: the hackathon article still ended up with three keywords in its headings. Those came from the
**leftover pool** of secondary keywords research had already bought, which step 5 also offers to every
heading writer.

## The prompts

### keyword-gate.md

```
You are deciding which sections of an article should target a search keyword — and which should not.

Most sections should NOT. An article has one main search target (its H1) and a handful of sections that
answer a real search of their own. The rest exist to carry the argument: they set up, they connect, they
conclude. Giving those a keyword produces a forced heading and wastes a paid lookup.

THE ARTICLE
- Title: {{TITLE}}
- Distinct angle: {{ANGLE}}
- The spine — what this article argues, for whom, and what the reader can do at the end:
  {{SPINE}}
- What this article IS about: {{ABOUT}}
- What this article is NOT about: {{NOT_ABOUT}}
- The primary keyword (the H1 already targets this): {{PRIMARY}}
- WHO THIS ARTICLE IS FOR:
{{PERSONA}}

THE SECTIONS, in order:
{{SECTIONS}}

────────────────────────────────────────────────────────────────────────
For EACH section answer one question: would THE READER ABOVE type this section's subject into Google
as their own search? Not anyone — that reader. A phrase the other side of the table searches for
(the candidate rather than the recruiter, the employee rather than the manager) brings the wrong
visitor to the page, and they leave.

Say YES when:
- the section answers a question someone would ask on its own, outside this article
- it names a thing people look up: a method, a number, a comparison, a cost, a process
- someone could land on this section from a search and be satisfied

Say NO when:
- it only makes sense inside this article's argument
- it sets up, bridges, concludes or summarises
- its subject is the primary keyword again, just from a different side — the H1 already owns that
- it is about our own product or the closing pitch

Expect roughly a third to a half of the sections to be YES. If you are saying yes to nearly all of them,
you are being too generous — go back and cut to the ones a stranger would genuinely search for.

Return ONLY this JSON, nothing else:
{"sections": [{"n": <number>, "hunt": true|false, "why": "<one short line>"}]}
```

**Block by block:** the opening paragraph is the whole philosophy, stated before any data. Then the
article context including the world. Then one question, with a yes list and a no list. Then a
calibration line ("a third to a half") which is what stops it saying yes to everything.

### section-seeds.md

```
You are finding the search phrases to look up for ONE section of an article.

THE ARTICLE
- Title: {{TITLE}}
- The spine: {{SPINE}}
- What this article IS about: {{ABOUT}}
- What this article is NOT about: {{NOT_ABOUT}}
- WHO THIS ARTICLE IS FOR:
{{PERSONA}}
- The primary keyword (the H1's — do not seed this or a reword of it): {{PRIMARY}}

THIS SECTION
- Working heading: {{HEADING}}
- Its job: {{JOB}}
- The evidence it actually holds:
{{CARDS}}

────────────────────────────────────────────────────────────────────────
Write 2 or 3 SEED PHRASES a person would type into Google to find THIS section.

Read the EVIDENCE, not just the heading. A section whose heading says "pricing" but whose evidence is
all commission percentages is a section about commission rates — seed it that way.

Rules:
- KEEP THEM SHORT: 2 or 3 words. This is the single most important rule here. These go into a keyword
  suggestion index that matches on the phrase itself — a 4-or-5-word seed almost always returns NOTHING,
  and the section ends up with no keyword at all. Seed the SHORT head of the idea and let the index find
  the longer phrases around it. Write "hackathon ai policy", not "AI policy for a hiring hackathon".
- Plain search language, not our internal phrasing — the words THAT reader would type, not the words
  the other side of the table would.
- Inside our world. Never seed a phrase belonging to something in the NOT ABOUT list, even when it
  matches our words — those searches come from a different field.
- Seed what this SECTION delivers, not the whole article's subject.
- Vary them. If your seeds are the same words reordered, you get one set of results, not three.

Return ONLY this JSON, nothing else:
{"seeds": ["...", "..."], "why": "<one line: what this section is really about, from its evidence>"}
```

**The two load-bearing rules:** read the evidence not the heading (a heading can lie about what a
section became), and keep the seed to 2 or 3 words (a long seed returns nothing from the index).

### pick-section-keyword.md

```
Pick the ONE keyword this section should target, from the real search data below — or none.

THIS SECTION
- Working heading: {{HEADING}}
- Its job: {{JOB}}
- What it is really about (from its evidence): {{WHY}}

ARTICLE CONTEXT
- The spine: {{SPINE}}
- What this article is NOT about: {{NOT_ABOUT}}
- WHO THIS ARTICLE IS FOR:
{{PERSONA}}
- The primary keyword (the H1's): {{PRIMARY}}

CANDIDATES (keyword | monthly volume | difficulty):
{{CANDIDATES}}

────────────────────────────────────────────────────────────────────────
CHOOSE by fit first, volume second:

- It must name what THIS section delivers. A bigger number for a phrase the section does not answer is
  worth nothing — the page ranks and the reader bounces.
- Reject a phrase searched by the wrong person. A keyword the other side of the table types brings a
  visitor this article was not written for, and a high-volume one does that at scale.
- Reject anything from the NOT ABOUT world, whatever its volume. A phrase that matches our words but
  belongs to another field is the most damaging pick available here.
- Do not pick the primary or a reword of it. The H1 owns that.

RETURNING NOTHING IS A GOOD ANSWER. If no candidate genuinely names this section, return null and say
why. Do not stretch.

Return ONLY this JSON, nothing else:
{"keyword": "<the phrase, or null>", "volume": <n or null>, "kd": <n or null>,
 "why": "<one line: why this fits, or why nothing did>"}
```

**Fit first, volume second.** And "returning nothing is a good answer" in capitals, because the default
instinct of any model handed 25 options is to pick one.

# STEP 5 — HEADINGS

**File:** [headings.py](scripts/headings.py) · **Writes:** the final `headline` on every section, the `h1`, and the `keywords` block

## What it does

Three sub-steps.

### 5a - one heading per section, all in parallel

Each call sees:
- the article title, angle, spine, primary keyword and its rewords
- **that section's own draft heading and its job**
- **that section's full cards** (this is the important part: it can see what the section actually
  became)
- the keyword researched for that section in step 4, if any
- the leftover pool of secondary keywords research bought earlier

It returns a final heading and says which keyword it used, or none. **Whatever it names becomes that
heading's LOCKED phrase for step 5b**, and it can come from any of four places:

1. the keyword bought for that section in step 4
2. the leftover pool of secondaries
3. the primary keyword, or one of its rewords
4. none at all, which is an allowed answer

So a lock is **not** proof that a keyword was bought for that section. On the cost-per-hire article
all five step-4 hunts came back empty, and 8 of the 12 headings still carried a lock: five from the
primary, two from the pool, one from a variation. **Zero from step 4.**

**A code guard:** if it claims a keyword it was never shown, the whole result is thrown away and the
draft heading is kept. That is corruption protection, not a quality judgment.

### 5b - the cross-section pass

One call that reads **every finished heading as a set**. This is the only place in the machine that
sees all the headings together before the body exists.

**What it is handed, three lines per section:**

```
  3. Executive Cost Per Hire Is Climbing – Here's What SHRM Says
       job: Resolve the confusion created by SHRM's multiple reports by showing that executive
            cost-per-hire is climbing steeply (to $15,000 median by 2026) while non-executive stays
            flat, and that SHRM's switch between averages and medians makes a huge difference.
       LOCKED — this phrase must survive: "cost per hire"
```

- **The heading**, numbered, so edits can be returned by number and broken counting is visible.
- **The job**, in full. This is the leash: the pass may rewrite the promise however it likes, but the
  job says what that section actually delivers, so it cannot point a heading at something the section
  does not do.
- **LOCKED**, only where 5a placed a keyword. See 5a above for where those come from.

It exists because of what the per-section writers cannot see:
- numbering that ran 1 to 5 then jumped to 16
- one instrument called "BARS" in one heading and by its full name in another
- Title Case and sentence case mixed inside one article

The coherence step later found two of these in the finished draft and **could not fix them**, because
headings belong to the architect. Doing it here costs nothing, because no body has been written yet.

**The keyword guards, and there are two shapes of them.**

*A phrase used in `MAX_HEADINGS_PER_KEYWORD` headings or fewer (2 by default) is hard-locked.* It must
survive the edit. The check is deliberately blind to capitalisation, punctuation and a trailing
plural, so the pass may recase "Type-D" or write "Rating Scales" for "rating scale". What it will not
allow is a changed or reordered word: "Cost of a Hire" does not carry "cost per hire". The guard runs
**per heading** — one heading that breaks its lock is reverted on its own and the rest of the pass
still lands.

*A phrase used in MORE than that is marked **OVER-USED**, and this pass may strip it.* 5a writes every
heading in parallel and blind, so each writer is offered the same keyword, each honestly answers "yes
it fits", and nobody counts. On the cost-per-hire article `cost per hire` ended up locked into 5
headings, plus 2 more carrying `calculate cost per hire` and 1 carrying `cost to hire`. Code counts
the reuse; the AI chooses which copies to keep, because it is the only thing that sees all the
headings at once.

The guard flips to **per phrase**: at most 2 is what the prompt asks for, **at least 2 is what code
enforces**. If the pass leaves an over-used phrase in fewer than 2 headings, the whole pass is refused
and every heading kept as written — so a keyword we paid for can never vanish from the page. A heading
that does drop its phrase has its `keyword_used` cleared, so the record stays honest.

The prompt also tells it to **take the phrase out, not rebuild the heading**: change the fewest words
that remove it. More rewriting means more chances to make something worse.

### 5c - the H1

One final call, written after every heading is final, so the H1 can promise only what the article
actually delivers.

**Deliberately not here:** replacing the primary keyword. Research picked it from real search data with
a world-check, and second-guessing that from inside the architect would be a weaker decision overriding
a better-informed one.

### The keywords block, computed in code

At the end, code (not AI) writes `st["keywords"]`:
- `section_keywords` = **only** phrases that actually landed in a final heading. Nothing gets in for
  merely existing.
- `unplaced` = every pool keyword no heading took, with the reason.

### The redo safety

A snapshot called `structure.pre-headings.json` is written **once**. A rerun starts from the original
shaped headings, not from the previous run's rewritten ones, so repeated runs do not compound their own
edits. A stale snapshot (older than the current shaped structure) is discarded rather than restored.

## Real numbers

| Article | Headings edited by 5b | Over 60 characters |
|---|---|---|
| running-hiring-hackathon | 3 of 8 | 1 |
| strategic-interview-questions | 8 of 27 | 2 |
| the-real-cost-recruitment | 4 of 13 | 2 |
| the-type-d-personality-label | 3 of 9 | 0 |

The 60-character limit is **recorded, never enforced**. An over-length heading is printed and logged in
`heading-map.json`, and kept.

## The prompts

### write-heading.md

```
You are writing the final heading for ONE section of an article.

════════════════════════════════════════════════════════════════════════
BEFORE ANYTHING ELSE — THE LENGTH:
Aim for UNDER 60 CHARACTERS, and count as you write rather than after. Longer gets cut off in search
results and skimmed past on the page, so 60 is the box you write inside by default.
Go over it only when the shorter version genuinely says less — when trimming would cost the specific
thing (the number, the role, the named decision) that makes the heading worth reading. A 64-character
heading that lands beats a 58-character one that says nothing.
════════════════════════════════════════════════════════════════════════

THE ARTICLE
- Title: {{TITLE}}
- Distinct angle: {{ANGLE}}
- The spine — what this article argues, for whom, what the reader can do at the end:
  {{SPINE}}
- WHO THIS ARTICLE IS FOR:
{{PERSONA}}
- Primary keyword (the H1 targets this): {{PRIMARY}}
- Rewords of the primary: {{VARIATIONS}}

YOUR SECTION
- Working heading (a draft — you are replacing or keeping it): {{HEADING}}
- Its job: {{JOB}}
- The keyword researched FOR this section: {{SECTION_KEYWORD}}
- Other researched keywords still unused, if one fits better:
{{POOL}}
- The evidence this section actually holds:
{{CARDS}}

────────────────────────────────────────────────────────────────────────
THE EVIDENCE TELLS YOU WHAT THIS SECTION ACTUALLY BECAME.

Its job was written before the research came back. The evidence is what it really holds now. Where the
two disagree, the evidence wins — a heading that promises what the section cannot deliver is worse than
a plain one.

CHOOSE A KEYWORD, IN THIS ORDER — and it is fine to end with none:
1. The keyword researched for this section. Does it name what this section delivers, and can the heading
   carry it without strain? If yes, use it.
2. If not, is there one in the pool above that fits this section better? Use that instead.
3. If not, would the primary or one of its rewords sit here naturally? It may — but only if it truly
   belongs; the H1 already carries it.
4. If none of them fit, use NO keyword. Write the best heading this section deserves on its own.

A well-researched keyword that does not fit is still a keyword that does not fit. Never force one in.

THE RULES for whatever you write:

- SPECIFIC, NEVER GENERIC. "Overview", "Key considerations", "Things to know", "Best practices",
  "Understanding X" say nothing, and they are the default an AI reaches for. Name the actual thing: the
  role, the number, the question a reader would ask out loud, the decision being made. Use the evidence
  — a real figure or a named thing in the heading is what makes it specific.
    Weak:   "Interview Question Considerations"
    Strong: "Questions to Ask a Candidate About Failure"
    Weak:   "Understanding Cost Per Hire"
    Strong: "What a Bad Hire Actually Costs You"

- ONE keyword only, never two. A heading holding two search phrases reads as written for a machine.

- SAY WHAT THE SECTION DELIVERS. After your edit it must still match its job and its evidence.

Return ONLY this JSON, nothing else:
{"heading": "<the final heading, aiming under 60 characters>",
 "keyword_used": "<the phrase you carried, or null>",
 "why": "<one short line: why this heading, and why that keyword or none>"}
```

**Block by block:**
- **Length first, in a box.** Deliberately before everything else, because a length rule at the bottom
  of a long prompt gets ignored.
- **The article context**, then the section's own material.
- **"The evidence tells you what this section actually became."** This is the key idea of the whole
  step. The job was written before research came back. The evidence is the truth now. Where they
  disagree, the evidence wins.
- **The keyword ladder**, four rungs, ending in "none is fine". Then one line repeating that a keyword
  that does not fit is still a keyword that does not fit.
- **Three writing rules** with worked weak-versus-strong examples.

### heading-pass.md

```
Every heading in this article was written by a different writer, and each of them saw only their own
section. Nobody has yet read the headings as a set. That is your job, and it is the only way to catch
what none of them could: numbering that does not run, one thing called two names, half the article in
Title Case and half in sentence case, eight headings in a row built to the same template.

You are reading them as a reader will — as a list, top to bottom, before they read a single word of
the body.

THE ARTICLE
- Title: {{TITLE}}
- Distinct angle: {{ANGLE}}
- The spine — what this article argues, for whom, what the reader can do at the end:
  {{SPINE}}
- WHO THIS ARTICLE IS FOR:
{{PERSONA}}
- Primary keyword (the H1 targets this): {{PRIMARY}}

THE HEADINGS, in order. Each shows the section's JOB (what it must deliver) and, where research
bought one, a LOCKED keyword:
{{HEADINGS}}

────────────────────────────────────────────────────────────────────────
TWO THINGS YOU MAY NEVER CHANGE:

1. A LOCKED KEYWORD. Where a heading is marked LOCKED, that phrase stays in it, word for word. It was
   chosen from real search data. You may move it within the heading, reword everything around it, and
   rewrite the rest freely — and you may change its capitalisation to match the rest of the list — but
   not one word of it changes, and nothing is added inside it. Code checks every locked phrase; a
   heading that lost one is thrown out and the original put back.

   THE ONE EXCEPTION IS A HEADING MARKED **OVER-USED**. Every heading above was written on its own, by
   a writer who could not see the others, so each was offered the same keyword and each accepted it.
   Nobody counted. You are the first to see the result:

{{OVERUSED}}

   A phrase repeated across most of the headings makes the page read as written for a search engine
   rather than a person, and the H1 already carries the article's main keyword. So for each phrase
   above: decide which {{KEYWORD_CAP}} headings genuinely earn it — the ones where someone typing that
   phrase would be satisfied landing on THAT section, not merely where it fits — and TAKE IT OUT of
   every other one.

   TAKE THE PHRASE OUT, DO NOT REBUILD THE HEADING. Change the fewest words that remove it and leave a
   heading that still reads well and still matches its job. You are removing a repetition, not
   rewriting from scratch, and a heading you rebuild is a heading you can break.

   Code enforces the other side of this: each of those phrases must still appear in at least
   {{KEYWORD_CAP}} headings when you are done. Strip it from too many and the whole pass is thrown
   away, so do not overshoot.

2. THE JOB. A heading promises what its section delivers. Rewrite the promise however you like, but
   after your edit it must still be a promise that section can keep. Never point a heading at
   something the section does not do.

Everything else is yours. You may not add, remove or reorder sections — same headings, same count,
same order, in and out.

────────────────────────────────────────────────────────────────────────
FIRST DUTY — fix what only the whole set reveals. These are the real reason this step exists:

- NUMBERING THAT DOES NOT RUN. If some headings are numbered, they run 1, 2, 3 with nothing skipped
  and nothing repeated. "Step 1 … Step 5, Step 16" is broken. Fix it one of two ways, never a third:
  RENUMBER when the article really is a procedure the reader works through in order — the numbers are
  telling them where they are, and that is worth keeping. DROP the numbers from every heading when
  only a handful of sections are steps and the rest are not; a short numbered run inside a mostly
  unnumbered article promises a sequence the article does not have. Never leave a partial sequence.
- ONE NAME PER THING. If section 4 says "BARS" and section 9 says "behaviorally anchored rating
  scale", the reader thinks they are two topics. Pick the form that serves each spot — the full name
  where it is first explained, the short one later — but never two names with no signal they are the
  same thing.
- ONE CASE. All Title Case, or all sentence case. Whichever most of the headings already use, make
  the rest match. A mixed list looks unproofed before a word is read.
- BREAK THE TEMPLATE. When four or more headings in a row open with the same construction — "Why X
  is Y", "How to X", "The X of Y" — the list reads as generated. Vary the ones that can carry a
  different shape without losing what they say. Do not vary for the sake of it; a run of three is
  fine.
- A HEADING AIMED AT THE WRONG PERSON. Read the list as that reader. A heading written for the other
  side of the table — "How to Answer X" in an article for the people ASKING X — tells them this page
  is not for them, and one is enough to lose them. You cannot delete the section, but you can turn
  the heading round to face the right reader.
- NO TWO HEADINGS THAT PROMISE THE SAME THING. If two headings would send a reader to the same
  answer, sharpen each so the difference between them is visible in the words.

SECOND DUTY — improve any heading that is weak on its own:

- A LABEL IS NOT A HEADING. "How we compiled these figures" files the section away. "Which figures we
  kept apart, and why" tells the reader what they get. Name the actual thing: the number, the role,
  the question someone would ask out loud, the decision being made.
- SPECIFIC, NEVER GENERIC. "Overview", "Key considerations", "Things to know", "Best practices",
  "Understanding X" say nothing, and they are what an AI reaches for by default.
- NEVER TRADE A PLAIN HEADING FOR AN ABSTRACT ONE. "Score how AI was used, not whether it was used"
  beats "Scoring AI Collaboration Quality" — the first is a sentence a person would say, the second
  names a concept. When your edit swaps everyday words for a noun phrase, you have made it worse.
  Leave it as it was.
- UNDER 60 CHARACTERS where you can. Longer gets cut off in search results and skimmed past on the
  page. Go over only when the shorter version genuinely says less — when trimming would cost the
  specific thing that makes the heading worth reading. Reading them as a set, you can also see when
  one heading is three times the length of its neighbours; even those out.
- LEAVE A GOOD HEADING ALONE. Most of them will already be right. Changing a heading that works is a
  cost with no gain, and it buries the changes that matter. Return it unchanged and say so.

────────────────────────────────────────────────────────────────────────
Return EVERY heading, in the same order, changed or not.

Return ONLY this JSON, nothing else:
{"headings": [{"n": <the number shown above>,
               "heading": "<the final heading — unchanged, or your edit>",
               "changed": true | false,
               "why": "<one short line, only when changed; empty string when not>"}],
 "notes": "<one or two lines: what you found across the set, or empty if nothing needed fixing>"}
```

**Block by block:**
- **The opening explains why this step exists at all**: nobody has read the headings as a set. That
  framing is what makes it look for set-level problems instead of rewriting each heading again.
- **Two things it may never change**: a locked keyword, and the job. Plus: it may not add, remove or
  reorder sections. Same count in and out.
- **First duty, five set-level problems**: numbering, one name per thing, one case, template
  repetition, two headings promising the same thing. Each has a specific fix, and the numbering rule
  gives two allowed fixes and forbids a third.
- **Second duty, five per-heading problems**, ending with "leave a good heading alone" which is what
  stops it churning every heading for no gain.

### write-h1.md

```
You are writing the final H1 for an article that is now fully built.

════════════════════════════════════════════════════════════════════════
BEFORE ANYTHING ELSE — THE LENGTH:
Aim for UNDER 60 CHARACTERS, and count as you write rather than after. Go over only when the shorter
version genuinely promises less than the article delivers.
════════════════════════════════════════════════════════════════════════

- H1 as planned: {{H1}}
- Distinct angle: {{ANGLE}}
- The spine: {{SPINE}}
- Primary keyword this article targets: {{PRIMARY}}
- Rewords of it: {{VARIATIONS}}

THE ARTICLE'S FINAL HEADINGS, in order — this is what the article actually delivers:
{{HEADINGS}}

────────────────────────────────────────────────────────────────────────
Return an H1 that carries the primary keyword naturally and still promises what the planned H1 promised.
If the planned H1 already carries the primary, return it unchanged.

- SPECIFIC, NEVER GENERIC. Name the actual thing — the number, the correction, the promise. "A Guide to
  X" and "Understanding X" are not titles, they are labels.
- It must not promise something the headings above do not deliver.
- Never invent a keyword. Use only the primary or one of its rewords.

Return ONLY this JSON, nothing else:
{"h1": "<the H1>", "why": "<one short line>"}
```

**The one rule that matters:** the H1 must not promise something the headings do not deliver. It is
written last precisely so it can be checked against the real list.

# Part 4 — Every setting in one table

All of these live in [scripts/config.py](scripts/config.py) and can be overridden with an environment
variable of the same name.

| Setting | Value | Used by | What it controls |
|---|---|---|---|
| `WORDS_PER_SECTION` | 300 | shape | Budget divided by this = the section **ceiling** |
| `WORDS_PER_SENTENCE` | 25 | shape | The unit the H3 rule counts in |
| `SENTENCES_PER_PARAGRAPH` | 4 | shape | So a paragraph is 100 words, and a 3-paragraph section is exactly 300 |
| `MIN_WORDS_PER_SUBHEAD` | 200 | shape, allocate | 2 paragraphs. Below this a sub-heading is a label on a paragraph |
| `LISTICLE_MAX_ITEMS` | 12 | shape | Hard cap on how many items a listicle may carry |
| `LISTICLE_SUPPORTING_SECTIONS` | 3 | shape | Supporting sections to reserve words for, before the items get any |
| `LISTICLE_MIN_ITEM_WORDS` | 200 | shape | Below this an item is a stub, so it gets dropped instead |
| `LISTICLE_MIN_ITEMS` | 5 | shape | The floor: fewer than this and it has stopped being a list |
| `SHAPE_MIN_YARDSTICK_PCT` | 60 | shape | A comparison option needs info on this % of yardsticks to keep its section |
| `ENRICH_QUERIES_PER_H3` | 3 | enrich | Web queries planned per research marker |
| `ENRICH_PAGES_PER_H3` | 15 | enrich | Pages downloaded per marker |
| `ENRICH_PAGE_CHARS` | 8,000 | enrich | How much of each page is fed to the card builder |
| `DFS_MIN_CREDITS` | 1.0 | enrich | Below this balance, fall back to Claude web search |
| `ENRICH_WORKERS` | 8 | enrich | Markers researched at once (DataForSEO route) |
| `ENRICH_WORKERS_FALLBACK` | 1 | enrich | Markers at once on the Claude route |
| `WRITE_OVERWRITE_PCT` | 0 | allocate | Buffer added to every word target. Zero: plan straight to the band |
| `ALLOC_CARDS_PER_SECTION` | 60 | allocate | Facts shown per section, so one huge section cannot dominate |
| `ALLOC_GLOSS_CHARS` | 200 | allocate | Per fact, one line |
| `VOL_FLOOR` | 100 | section-keywords | Minimum monthly search volume |
| `KD_CEIL` | 40 | section-keywords | Maximum keyword difficulty |
| `SUGGEST_LIMIT` | 80 | section-keywords | Phrases pulled per seed (in the script, not config) |
| `CAND_SHOWN` | 25 | section-keywords | Candidates shown to the picker (in the script) |
| `MAX_HEADING_CHARS` | 60 | headings | Recorded only, never enforced (in the script) |
| `MAX_HEADINGS_PER_KEYWORD` | 2 | headings | How many headings may carry the same phrase. Over this, 5b may strip it |
| `SELECT_CONCURRENCY` | 8 | all | How many AI calls run at once |
| `LLM_RETRIES` | 1 | all | A bad JSON reply is retried once |

---

# Part 5 — Where money is spent

Only two of the five steps cost anything.

- **Step 2, enrich**: one DataForSEO SERP call per query, so up to 3 per research marker. Only when a
  section asked for research. Guarded by a balance check before anything is spent.
- **Step 4, section-keywords**: one DataForSEO keyword-suggestions call per seed, so 2 or 3 per
  gated-YES section. The gate exists specifically to keep this number down.

Everything else runs on the free local AI CLI (Claude by default, DeepSeek or Codex via
`LLM_PROVIDER`).

---

# Part 6 — The whole thing in one line

**Number the research into boxes → an AI designs the sections and the sub-headings from those boxes →
go fetch whatever it said was missing → split the word budget across the sections → decide which
sections deserve a keyword and buy it → write the final headings and the H1.**

The AI makes seven judgment calls in here: the structure, the list items or comparison options, the
research queries, what counts as a card, the word shares, the keyword gate and pick, and the headings.
Code does everything else, and guards every one of those calls.

---
---

# Part 7 — WHAT TO REVISIT

Everything from the reviewer's list and the braindump that the architect owns is either done or
listed here. Nothing below is in progress.

## Needs a decision from you
1. **May the cross-section heading pass merge or delete sections?** The reviewer asked for
   *"some headings could be combined or removed"*. Step 5b reads every heading as a set, which is the
   right place, and is explicitly forbidden from changing the count. Read step 5 first, then decide.
2. **The AI review pass after shape.** Your idea, parked. It overlaps with 1: if the review pass
   can delete a section, 5b may not need to.
3. **The 60-character heading limit.** Recorded on every run, never enforced. Enforcing means
   rejecting and re-asking, which can make headings worse. Recommendation: leave it, strike it off.

## Needs you to read three short files
4. **`formats/glossary.md`, `formats/template-resource.md`, `formats/common-spine.md`** — about 40
   lines in total, never reviewed. Same job as the other five: which bullets are wrong, which belong
   to a later step (those move to `formats/_craft/`), which get deleted.

## Found in a run, not investigated
5. **The `list` field never fired once** across all four articles. Either nothing was genuinely
   list-shaped, or the three-part test in step 4 of the structure prompts cannot be passed.
6. **Overlapping keywords still stack up.** The over-use cap counts the phrase a heading CLAIMED,
   not the words it contains. So on the cost-per-hire article `cost per hire` (5 headings) is capped,
   but `calculate cost per hire` (2) and `cost to hire` (1) are separate phrases under the cap — and
   both contain the same root. After the cap does its work, four headings plus the H1 still read
   "cost per hire". Better than eight, not solved. Counting by word overlap instead of exact phrase
   would fix it and risks over-stripping, so it is worth a look rather than an obvious change.

## Just needs running
7. **Re-run the architect** to see the 2026-08-09 fixes land (the H3 threshold and the parallel-item
   allocation). `bash _runs/rerun_architects.sh`. Last run: 37 minutes, $0.63.

## Not the architect's — do not wait on it here
- **The word band.** 2,400-7,500 versus the 1,500-2,000 the reviewer wants. Decided in the RESEARCH
  phase. Everything here is splitting a band that is already too big.
- **Bad topics shipping.** Two of the first four were judged bad picks (no product fit; a SERP
  dominated by healthcare). Upstream, in idea selection. The most expensive item on the whole list.
- **Everything about how a sentence reads** — length, jargon, readability, FAQ length, the intro.
  All in `../PENDING-WRITER-CHANGES.md`.

---
