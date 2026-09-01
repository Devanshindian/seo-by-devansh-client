---
type: a complete plain-English explanation of WRITE BODY (writer step 1)
purpose: so you can hold the whole step in your head and know exactly where any change belongs
covers: scripts/write_body.py + prompts/write-body.md, quoted in full
companion: architect-explained.md (the step before) · PENDING-WRITER-CHANGES.md (the change list)
real numbers from: the 4 finished Testlify articles
last_updated: 2026-08-09
---

# Write Body, explained

The architect finished planning. This is the step that turns the plan into actual sentences. It is
the single most important step in the machine, because everything after it only edits what it wrote.

---

## Part 0 — The one idea

**One AI call per section, all sections written at the same time, each one blind to the others.**

- Section 3's writer cannot see section 4's text. It only sees section 4's *brief*.
- Each writer sees **only its own facts**. It cannot reach for a fact from another section, which is
  what makes it impossible to invent one.
- It writes the **body only**. No intro, no FAQ, no conclusion, no links. Those are later steps.

Everything else in this doc is a consequence of those three lines.

---

## Part 1 — Where it sits

```
architect/structure.json   (the plan: sections, jobs, facts, word targets)
        |
   >>> WRITE BODY <<<      writer step 1
        |
writer/_work/body.json     (per section: the prose + which facts it used)
        |
   blend -> wrapper -> coherence -> slop -> links -> clean -> assemble
        |
writer/draft.md            (the article a human reads)
```

Seven steps run after it. **Every one of them only edits.** None can add a fact, and none can
restructure the article. So a section written badly here stays badly written.

---

## Part 2 — What one writer receives

This is the whole of what a section writer knows. Nothing else exists for it.

| What | Where it comes from | Why |
|---|---|---|
| **The brand** and one line on what it does | `company.json` | So it knows who is publishing |
| **The title and the angle** | the topic queue | What the article promises |
| **The spine** | the architect | The one argument the whole piece makes |
| **The reader** | the planner's persona | Who this is for |
| **The full plan** | every section's headline, job and what it covers | So 12 writers pull one way and never overlap |
| **Its own heading and job** | the architect | What THIS section must deliver |
| **Its word target** | the architect's allocate step | How long |
| **Its SHAPE, with the facts inside it** | the architect | The opening's facts, then each sub-heading and its own facts. See below |
| **The per-item contract** | listicles only, **items only** | The labelled parts every item must end with |
| **A "you are not an item" note** | listicles only, supporting sections | So a supporting section does not imitate an item |
| **A table instruction** | only if the architect marked it | Render a real markdown table |
| **A list instruction** | only if the architect marked it | Render a numbered or bulleted list, with prose around it |
| **A thin-research warning** | only if that section's extra research came back empty | Write what the material supports and stop, do not pad |
| **The product rule** | computed per section | Almost always "never mention the brand" |
| **The brand voice pack** | 7 files, **174 KB, about 44k tokens, uncapped** | How the company writes |

### The shape block, which is the important one

The facts do not arrive as a flat pile with a separate list of sub-topics. They arrive **grouped
under the heading they belong to**, because a writer cannot follow a shape it cannot see:

```
THE OPENING — write this first, directly under the section heading, with no sub-heading of its own:
  [c370] Because no single rater's judgment is fully reliable even after calibration...
  [c371] a second-reader policy for borderline scores, where another judge reviews...

SUB-HEADING (render it exactly, as "### Set Up Independent Scoring Before Any Discussion"):
  [c9]  Independent scoring compounds this: judges should score privately...
  [c20] Each submission should be scored independently by at least two reviewers...

SUB-HEADING (render it exactly, as "### Run a Calibration Session That Surfaces Disagreement"):
  [c55] Judge selection and calibration matter as much as the rubric text...
```

A section the architect did not split gets a different opening line instead:

```
THIS SECTION HAS NO SUB-HEADINGS. Write it straight through as prose under its heading.
Do NOT invent sub-headings.
```

Most sections get that second version. The prompt also tells the writer it **may move a fact** if the
prose genuinely reads better another way — what it may not do is ignore the shape and write one
continuous block.

That voice pack is worth pausing on. Every single section call carries **all 174 KB** of it:

| File | Size |
|---|---|
| writing-examples.md | 81 KB |
| stories.md | 41 KB |
| brand-voice.md | 25 KB |
| style-guide.md | 12 KB |
| stats.md | 8 KB |
| writing-integrity.md | 3 KB |
| opinions.md | 1 KB |

`features.md` is **deliberately left out**, because the body is product-free.

---

## Part 3 — Who decides what

**The AI decides:** every word of the prose. Which facts to use and which to leave out. How the
section opens and hands off. Whether to move a fact from the group the architect put it in.

**The code decides:**
- Which facts the section may see at all (only its own)
- **The shape it is shown**: the opening's facts, then each sub-heading with its own facts, in order
- Whether it is told "no sub-headings, write it straight through", or given them to render
- Whether a **table** instruction is added (only if 2 or more columns were named)
- Whether a **list** instruction is added (only if the kind is `numbered` or `bulleted`)
- Whether this section gets the **per-item contract** or the "you are not an item" note (`is_item`)
- Whether a **thin-research warning** is added (does this section appear in `research_failures`)
- Whether the product rule is "mention the brand" or "never mention the brand" (does the heading
  contain the brand name)
- **Provenance**: it reads the `[c123]` tags out of the finished prose and builds the list of which
  fact backs which claim. A tag naming a fact that is **not in this section** is a hallucination, and
  it is dropped and counted
- Whether the per-item contract was honoured, counted **over item sections only**, plus a separate
  check for a supporting section that copied the contract anyway
- Word counts, printed per section

---

## Part 4 — What it actually produced

Measured on the four finished articles.

| Article | sections | target | written | over | sourced claims | hallucinated tags |
|---|---|---|---|---|---|---|
| hackathon | 8 | 3,300 | 3,545 | +7% | 139 | **0** |
| strategic | 27 | 6,503 | 9,397 | **+44%** | 204 | **0** |
| cost-per-hire | 13 | 3,500 | 3,657 | +4% | 126 | **0** |
| Type D | 9 | 2,800 | 2,900 | +3% | 113 | **0** |

### What this tells you

**The fact discipline is perfect.** Zero hallucinated citation tags across 582 sourced claims in four
articles. The "you may only see your own cards" design works exactly as intended. This is the
strongest thing in the whole machine and it should not be touched.

**Length is mostly fine, with one runaway.** Three articles land within 7% of target. The listicle
came in **44% over** — and that is the one the reviewer called too long.

**Sentence length is the real problem:**

| Article | sentences over 25 words |
|---|---|
| hackathon | **44%** |
| Type D | **40%** |
| strategic | **38%** |
| cost-per-hire | **29%** |

Between a third and a half of every article breaks the 25-word rule. (The very longest "sentences"
in that measurement are markdown tables, which have no full stops, so treat the maximum with care.
The percentage is solid.)

---

## Part 5 — The prompt, in full

```
You are writing ONE section of an article published by {{BRAND}}. Write as a neutral, credible
expert — a trusted industry writer, not a salesperson.

────────────────────────────────────────────────────────────────────────
THE COMPANY publishing this article: {{BRAND}} — {{ABOUT}}

THE ARTICLE:
- Asset title: {{TITLE}}
- Distinct angle (what this article is built to deliver): {{ANGLE}}
- What this whole piece argues (the spine): {{SPINE}}

WHO YOU ARE WRITING FOR (the reader — think about them, but NEVER name or address them):
{{PERSONA}}

────────────────────────────────────────────────────────────────────────
THE FULL PLAN — every section, what it must deliver, and what it covers.
The others are being written in parallel by other writers: you cannot see their text, only their
briefs. Never write "as we saw above" or quote prose that does not exist yet.

{{PLAN}}

YOU WRITE ONLY THE SECTION MARKED ABOVE. Do not cover another section's ground. Write so your
section picks up naturally from the one before and hands off cleanly to the one after.

────────────────────────────────────────────────────────────────────────
YOUR SECTION
Heading: {{HEADING}}
Its job:  {{JOB}}

Length: aim for about {{WORD_TARGET}} words. That is a target, not a quota — if the facts do not
justify it, write less. NEVER pad to reach it.
{{THIN}}{{ITEM_CONTRACT}}{{TABLE}}{{LIST}}

────────────────────────────────────────────────────────────────────────
HOW THIS SECTION IS SHAPED, AND THE ONLY FACTS YOU MAY USE.

The shape below was designed by the step that read every section's material and decided where each
part belongs. FOLLOW IT. Write the opening first, then each sub-heading in the order given, using
that part's own facts.

- RENDER EVERY SUB-HEADING AS A REAL MARKDOWN HEADING: "### " followed by its exact wording. Do not
  reword it, do not merge two of them, do not add one that is not listed, and do not silently turn
  them into bold text or into the first words of a paragraph. They are headings on the page.
- The facts under a sub-heading belong under that sub-heading. If, as you write, a fact genuinely
  reads better somewhere else in this section, move it — you are the one seeing the sentences form.
  What you may NOT do is ignore the shape and write one continuous block.
- A section listed as having NO sub-headings gets none. Do not invent them.

Each fact has an id like [c412] and its source. When you use a fact, put its id tag right after it:
"a bad hire costs 30% of first-year salary [c412]." Never use a fact that is not listed here, and
never invent a number, name, quote, or source.

{{SHAPE}}

────────────────────────────────────────────────────────────────────────
TWO KINDS OF CONTENT — read carefully
- A FACT — a statistic, a study result, a named outcome, a price, a real company's result, a quote
  — MUST come from a card above. NEVER invent one, not even inside an example.
- CRAFT you may compose yourself — a worked example, a sample answer, an illustrative walk-through
  — because it is guidance, not a claim about the real world. But it must contain ZERO invented
  specifics: no fabricated metric, no named company result, no fake study.

PREFER THE CONCRETE, PROVEN VERSION: when a point can be made generically OR with a specific number
or named source from the cards, always use the specific one — it turns an assertion into proof.
Do not write "bad hires are costly" when a card gives "a bad hire costs 30% of first-year salary."

FACT RULES — never break these:
- Use ONLY the facts above for anything factual. Never invent a fact, number, quote, or source.
- Every statistic keeps its [c…] tag, so its source travels with it. A number with no card ⇒ do not
  write it.
- Never write "studies show" or "experts agree" — the named source is in the card.
- Name a source in the prose only when it is credible enough to lend authority: research bodies,
  government data, peer-reviewed studies, major industry surveys (SHRM, LinkedIn, Gartner and the
  like). If a fact comes from a blog, a vendor's marketing page, or an unknown site, use the fact
  with its [c…] tag but do NOT name the site in the sentence — the source link carries it.
  Exception: when the section itself compares vendors or competitors, naming them is the point —
  name them freely as the SUBJECT you discuss, just never cite them as the AUTHORITY for a claim.
- {{PRODUCT_RULE}}
- Serve the article's one argument (the spine above). If a fact in your cards pulls away from it,
  leave that fact out.

WRITING RULES — how the prose must read:
(The last five are repeated in wrapper.md, which writes the intro/takeaways/FAQ/close — edit both together.)
- CUT PADDING, NOT CONNECTIVE TISSUE. No filler, no throat-clearing before a fact, no "in this
  section we will…", no restating the heading in the first sentence, no summarising at the end what
  the reader just read. A sentence that only re-says what you just said is padding — cut it.
  But a short phrase carrying the reader from one fact to the next — "since then", "but", "which is
  why", "even so" — is doing real work. Strip those out and the prose stops being an argument and
  becomes a list of findings. Facts with nothing between them are harder to read, not cleaner.
- LET A SENTENCE BREATHE. A fact and what it means usually belong together, joined. Three separate
  facts crammed into one sentence with a comma and a colon is a pile, not concision. Read it back:
  if you have to hold two things in your head to reach the end, split it in two — and use a real
  connecting word when you do, not just a full stop.
- NEVER make the same claim in two consecutive sentences. State it once, with its number, and move
  on. Rewording a point does not strengthen it — it tells the reader you had nothing to add. The
  editor who reads the finished article only checks for repetition BETWEEN sections; repetition
  inside your own paragraphs is yours to prevent and nobody else will catch it.
- OPEN WITH THE POINT. Your first sentence delivers what this section's job promises — the finding,
  the number, the verdict. Not background, not build-up. A reader who stops after your first
  sentence should still leave with the section's core.
- EVERY STATISTIC EARNS ITS "SO WHAT". A number alone is trivia; attach what it means for the
  reader's decision or money in the same breath: not "cost per hire rose 21% [c5]" and onward, but
  what that rise does to a hiring budget. If you cannot say why a number matters, question whether
  it belongs.
- NO VAGUE QUANTITIES OR TIMES. "Recently" hides a date; "many companies" hides a share. If a card
  holds the specific, the vague word is banned — write the date, write the share. If no card holds
  it, drop the claim rather than gesture at it.
- WRITE THE PLAIN WORD. Use, not leverage. Help, not facilitate. Start, not commence. Corporate
  vocabulary reads as filler even when the thinking behind it is sharp.
- ONE IDEA PER SENTENCE. A sentence carries a subject, a verb and one point. When you catch yourself
  joining two points with "which", "while", "and thereby" or a second comma-clause, split it in two.
  Keep most sentences under 20 words; a long one is fine when the next one is short.
- SAY IT AS A VERB, NOT A NOUN. "Evaluate candidates", not "conduct an evaluation of candidates".
  "Decide", not "make a determination". "Score the work", not "perform scoring of the work". Turning
  a verb into a noun doubles the words and drains the action out of the sentence.
- EXPLAIN A TERM THE FIRST TIME OR DROP IT. If a phrase would stop a competent reader from outside
  this field — "inter-rater reliability", "adverse impact", "construct validity", "behaviourally
  anchored" — give its meaning in the same sentence, in ordinary words. If you cannot explain it in
  a short clause, the sentence does not need it.
- CUT THE QUALIFIER STACK. One qualifier per claim. "A structured, behaviourally anchored, weighted
  rubric" is three stacked in front of one noun; keep the one that carries the meaning and drop the
  rest. The reader cannot hold three at once, so all three land as none.
- VARY THE SHAPE OF YOUR SENTENCES. Two long sentences earn a short one. Never let three in a row
  share the same construction — uniform rhythm reads machine-made even when every fact is right.

- A REAL SEQUENCE IS A LIST, NOT A PARAGRAPH. When you find yourself writing "First… Then… Third…"
  inside one paragraph, the reader is being asked to hold a list in their head with no shape on the
  page. Write it as a list instead. Use a NUMBERED list (1. 2. 3.) when the order matters — steps
  someone performs in sequence — and a dash list (- ) when the items are simply parallel and could be
  read in any order. Keep the [c…] tags on whichever items carry a fact.

  ALL THREE of these must hold, or leave it as prose:
    · THREE OR MORE items. Two things are a sentence with "and" in it.
    · EACH ITEM STANDS ALONE. If item two only makes sense after reading item one, it is an argument,
      not a list — argument belongs in prose.
    · EACH ITEM IS SHORT — a line or two. An item that needs four sentences is a paragraph in
      disguise, and a list of paragraphs is harder to read than the prose you started with.

  And do NOT reach for a list otherwise. A section that is mostly bullets reads as a slide deck, and
  a list of near-identical stubs is the most obvious machine-writing tell there is. Most sections
  should contain no list at all. If you write one, write it because the content genuinely is a
  sequence — never to break up a long paragraph.

VOICE & STYLE — match these:
{{VOICE}}

Output ONLY the section: the markdown heading "## {{HEADING}}", then the prose, with each sub-heading
rendered as "### <its exact wording>" in the order given above. No preamble, no sign-off, no notes.
```

---

## Part 6 — That prompt, block by block

- **The opening.** "Write as a neutral, credible expert, not a salesperson." Everything else hangs off
  that.
- **The company, the article, the reader.** Note the reader line: *"think about them, but NEVER name
  or address them."* No "you" writing.
- **THE FULL PLAN.** Every other section's headline, job and sub-topics, with this one marked. Then
  the rule that follows from it: *"you cannot see their text, only their briefs. Never write 'as we
  saw above' or quote prose that does not exist yet."* This is what stops 27 parallel writers
  contradicting each other.
- **YOUR SECTION.** Heading, job, word target. The word target says *"that is a target, not a quota.
  NEVER pad to reach it."* Then, only when they apply: the thin-research warning, the per-item
  contract or the "you are not an item" note, the table instruction, the list instruction.
- **HOW THIS SECTION IS SHAPED, AND THE ONLY FACTS YOU MAY USE.** One block doing two jobs. Every
  fact carries its `[c…]` id and its source URL, and this is what makes fabrication impossible: a
  fact not on this list does not exist for this writer. And the facts sit **under the heading they
  belong to**, so the shape and the material arrive together. Three rules go with it: render every
  sub-heading as a real `###` heading with its exact wording, a section listed as having none gets
  none, and you may move a fact if the prose genuinely reads better but you may not ignore the shape
  and write one continuous block.
- **TWO KINDS OF CONTENT.** The single most important distinction in the prompt. A **fact** (a
  statistic, a study, a price, a real company's result) must come from a card. **Craft** (a worked
  example, a sample answer) may be composed, because it is guidance rather than a claim about the
  world. But craft must contain zero invented specifics.
- **PREFER THE CONCRETE.** When a point can be made generically or with a real number, always the
  number. *"Do not write 'bad hires are costly' when a card gives 'a bad hire costs 30% of first-year
  salary'."*
- **FACT RULES.** Never invent. Every statistic keeps its tag. Never "studies show". Name a source in
  the prose **only** when it is credible enough to lend authority (SHRM, Gartner, government data),
  never when it is a blog or a vendor page. Serve the spine.
- **WRITING RULES**, twelve of them: cut padding but not connective tissue, let a sentence breathe,
  never make the same claim twice, open with the point, every statistic earns its "so what", no vague
  quantities, write the plain word, one idea per sentence, say it as a verb not a noun, explain a term
  or drop it, cut the qualifier stack, vary the shape of your sentences.
- **THE LIST RULE.** Three tests that must all hold: three or more items, each stands alone, each is
  short. Numbered when order matters, dashes when parallel. Then the warning: *"a section that is
  mostly bullets reads as a slide deck."* Note this is the writer's own judgment about a list inside
  its prose. It is separate from the architect marking a whole section as a list, which arrives as
  its own instruction near the top.
- **THE OUTPUT LINE.** `## <heading>`, then the prose, with each sub-heading rendered as
  `### <its exact wording>` in the order given.
- **VOICE & STYLE.** All 174 KB of the brand pack.
- **The output.** Just the heading and the prose. No preamble, no sign-off.

---

## Part 7 — What the architect decides, and what this step does with it

`structure.json` holds ten things per section. This is the full accounting.

| Field | What it holds | What the writer does |
|---|---|---|
| `headline` | The H2 | Used |
| `spine` | The article's one argument | Used |
| `job` | What this section must deliver | Given to the writer. **Never checked** |
| `word_target` | How long | Given to the writer. **Never checked** |
| `lead` | The H2's own facts, above the first sub-heading | Used — written first, as the opening |
| `h3s` | Sub-headings the architect wrote, each with its own facts | Used — rendered as real `###` headings, in order, each from its own facts |
| `table` | Columns, when the section is a table | Used |
| `list` | `numbered` or `bulleted`, when the section is a list | Used |
| `is_item` | Whether a listicle section is an entry or supporting | Used — the per-item contract goes to items only |
| `research_failures` | Sections whose extra research came back empty | Used — the writer is warned not to pad |

**Four of these were wired up on 2026-08-09.** Before that, the writer received every fact in one
flat pile and ignored the shape entirely, which is why 3 of the first 4 articles shipped with **zero
sub-headings on the page** despite the architect writing them. The per-item contract went to every
section, so `Strong Answer` / `Weak Answer` / `Scoring line` landed on all 27 sections of the
strategic article — including "Build an Interview Question Bank", which has no candidate answer to
score. The code check reported **zero misses**, because it counted every section rather than every
item.

**Two remain unchecked, and they are the same failure twice: a number is decided, passed along, and
never compared to the result.**

- **`job`** — the architect writes one sentence saying what the section must deliver. Nothing verifies
  it did. That is how a section spends four paragraphs on which report edition is stale and never
  reaches the answer.
- **`word_target`** — nothing compares what was written to it. On the strategic article 24 of 27
  sections came in over, nine of them by more than 50%, one at **142% over** (731 words against 301).
  The whole article ran **44% over** and nobody knew until the very last step.

---

## Part 8 — What the reviewer asked for, and whether it lives here

### Belongs to write body

| What | Status |
|---|---|
| **No fluff, get to the point** | Rule exists, being ignored |
| **Answer the H2, give the takeaway** | "Open with the point" exists, weakly |
| **Sentences max 25 words** | Prompt says "most under 20". No ceiling, no check. **29-44% break it** |
| **Vary sentence length, irregular** | Rule exists, no check |
| **Paragraphs max 4 sentences** | Not in the prompt at all |
| **Explain a complex term in brackets** | Rule exists but asks for "in the same sentence", not brackets |
| **Simple English, 12th grade** | Nothing measures it |
| **No jargon** | "Write the plain word" exists |
| **Bullet and numbered lists** | Rule exists. The architect's `list` field is not read |
| **Do not repeat yourself** | Rule exists for within a section |
| **Stay inside the word target** | Target is given, nothing acts on the result |
| **Render the architect's H3s** | Not done |
| **Listicle contract only on real items** | Not done, `is_item` unread |
| **Competitor pros/cons, G2, pricing** | Only possible if research gathers it first |
| **Name credible sources in the prose** | Rule exists, and it is what makes the source link work later |

### Does NOT belong here

| What | Where it lives |
|---|---|
| FAQ answers too long (40 words) | `wrapper.md` |
| The intro: myth-busting, problem-agitate-solution, states the intent | `wrapper.md` |
| External links capped at 4 or 5 | `links_pass.py`, hardcoded at 10 |
| Internal linking | `links_pass.py`, rebuilt already |
| An H3 when an H2 runs long | The architect, done 2026-08-09 |
| Article length / the 1,500-word target | The **research** phase sets the band |
| Is this topic relevant to us | Upstream, idea selection |
| EEAT: Reddit, Quora, Blind opinions | Research |
| Readability scoring, Flesch, Hemingway | A check that does not exist anywhere yet |
| An AI review pass, a publish checklist | Steps that do not exist yet |

---

## Part 9 — The one thing to understand before changing anything

**Most of the reviewer's prose feedback is already written into this prompt, and is being ignored.**

"Cut padding", "open with the point", "keep sentences short", "explain the term", "vary the shape",
"one idea per sentence", "write the plain word" — all there, at 1,528 words. Adding a thirteenth rule
to a prompt losing the first twelve will not change the output. The numbers in Part 4 prove it: the
sentence rule is in the prompt and 44% of sentences break it.

**The lever is a code check plus a targeted re-ask.** The machinery already half exists: the per-item
contract check counts misses and prints them, and never re-asks. Each section is a separate call, so
sending one section back with only its failures named is cheap.

### The checks that would make the prose rules real
- Longest sentence per section, flag anything over 25 words
- Sentences per paragraph, flag over 4
- Standard deviation of sentence length, so "every sentence the same length" fails too
- Section word count against its own target, which already exists and nothing reads
- **Does the section answer its heading?** Every section carries a `job` field saying what it must
  deliver. It is written by the architect, passed to the writer, and **checked by nobody**. It is the
  most under-used field in the machine, and this is the last step where it exists

---

## Part 10 — Change hooks

Neutral list. Nothing here is decided.

**Make the prose rules enforceable**
1. Sentence length check, over 25 words
2. Paragraph length check, over 4 sentences
3. Rhythm check, so uniform length fails
4. Word target check
5. "Does it answer its heading" check, using the `job` field
6. A targeted re-ask for any section that fails, since each is already its own call

**Prompt wording**
7. Sentence rule says "most under 20" and should say "never over 25"
8. Term explanation should ask for brackets
9. Paragraph limit is absent entirely

**Bigger questions**
10. The voice pack is 174 KB on **every** call. Nobody has measured whether all seven files help
11. Nothing checks a section against the article's readability target, because there is no target
12. `slop-rules.md` says 15-25 word sentences sound robotic while this prompt says stay under 20.
    **Two files give the writer opposite instructions**, and neither owns the rule
