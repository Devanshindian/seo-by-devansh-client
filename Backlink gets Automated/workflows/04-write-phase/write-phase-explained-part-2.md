---
type: WRITE PHASE EXPLAINED, PART 2 — slop, links, clean and assemble (writer steps 5, 6, 7 and 8)
purpose: so you can hold the last four steps in your head and know exactly where any change belongs
covers: scripts/slop_pass.py + links_pass.py + clean.py + assemble.py, and their prompts
companion: write-phase-explained-part-1.md (steps 2-4) · write-body-explained.md (step 1) · architect-explained.md
real numbers from: the 4 finished Testlify articles. The step LOGIC of all four is unchanged, so
  every number here still describes code that is in place. Their review pages gained a link on
  2026-08-13; that is presentation, not behaviour.
last_updated: 2026-08-13
---

# Write phase explained, part 2

Part 1 covered the three editors: blend, wrapper and coherence. By the end of those, the article is
written, joined up, wrapped in an intro and a close, and checked for contradictions.

These last four steps do not change what the article says. They finish it.

**The logic of all four is untouched.** Every number below is real, measured, and describes code that
is still in place. The only change since they were written is that each step's review page now links
to a clean read of the article as it stands after that step. That is presentation; nothing about what
these steps DO has moved.

---

## Part 0 — The one idea

**Two of these steps use AI. Two are pure code. The split is deliberate and it is strict.**

| Step | What it is | Why |
|---|---|---|
| 5. Slop | AI | Deciding whether a sentence sounds machine-written is judgment |
| 6. Links | AI | Deciding whether a page genuinely deepens a sentence is judgment |
| 7. Clean | **Pure code, no AI, no cost** | Finding an invisible character is not judgment. It is a search |
| 8. Assemble | **Pure code, no AI, no cost** | Counting is arithmetic |

The rule behind the split is one line from `clean.py`:

> **CODE touches characters and spacing, the AI touches meaning.**

An AI asked to strip invisible characters misses some, costs money, and answers differently on two
runs. A search-and-replace misses none, is free, and gives the same answer every time.

---

## Part 1 — Where they sit

```
writer/_work/coherent.json      the article, checked for contradictions
        |
   >>> SLOP <<<                 step 5 — strip the AI writing tells
        |
writer/_work/polish.json
        |
   >>> LINKS <<<                step 6 — internal links, a read-more line, the visible sources
        |
writer/_work/linked.json
        |
   >>> CLEAN <<<                step 7 — invisible characters, dashes, spacing. No AI
        |
writer/_work/scrubbed.json
        |
   >>> ASSEMBLE <<<             step 8 — build the article, count the keywords. No AI
        |
writer/draft.md                 the finished article
writer/article.html             the page you review
```

**Why clean comes after links, not before.** The links step adds one new line to the article, the
read-more pointer. Anything added has to be scrubbed too, so the scrub goes last. Clean is also the
cheapest step in the whole machine to run again, so putting it at the end costs nothing.

**Why links comes after slop.** Links match anchor text against exact words in the article. If slop
ran afterwards it would rewrite a sentence a link was sitting on and break it.

---

## Part 2 — The pattern all four share

**The AI proposes. The code checks. If the check fails, the original survives.**

You have seen this in part 1. Here it is again, tighter, because these steps are editing prose that
has already been verified and any damage they do is damage to finished work.

| Step | What code checks afterwards |
|---|---|
| Slop | Every number and every `[c412]` source tag must be **identical** before and after, per block. Any difference and that block keeps its original text |
| Links | Undo every change the AI said it made, and the text must match the original **exactly**. Anything undeclared is reverted |
| Clean | Running it twice must change nothing the second time. Asserted in code |
| Assemble | Nothing to check. It only counts and formats |

---
---

# STEP 5 — SLOP

## What it does

It strips the writing patterns that make text read as machine-written. Em dashes, "delve",
"leverage", "seamless", "it's not just X, it's Y", bold scattered everywhere.

It works on **one block at a time**, in parallel. A block is a section, or the intro, or one FAQ
answer, or the close.

## Where the rules live

Two files, and the split matters:

- **`prompts/slop.md`**, 317 words. The instructions: what your job is, what you must not break.
- **`prompts/slop-rules.md`**, 5,977 words. The rules themselves.

`slop-rules.md` is the `avoid-ai-writing` ruleset carried over word for word, plus this pipeline's
own hard rules on top. **It is the one place to tune a rule.** The whole file goes into every call.

Its own header explains why it is separate:

> The slop step loads this whole file into its prompt. To tune a rule, edit it here, one place.

The pipeline's own rules sit at the top and override everything below them on conflict:

```
## THIS PIPELINE'S OWN P0 — overrides everything below on conflict

- **Facts are untouchable.** Never add, remove or alter a fact, number, statistic, name, quote or
  claim to fix style. If the only fix for a tell would change a fact, leave the sentence alone.
- **Every [c…] source tag stays attached to the claim it proves.** Never add, drop or move one.
- **Headings are never yours to change.**
- **The voice stays.** This pass removes tells; it does not restyle. A sentence with no tells comes
  through untouched.
- **Em-dash budget: target zero; hard max ~2 per 1,000 words, never two in one sentence.**
  Rewrite dash-glued clauses into separate sentences, or use a comma, colon, or parentheses where
  they genuinely fit.
```

Rules are graded P0, P1, P2. Fix every P0 and P1. Fix a P2 only where the fix clearly reads better.

## The guard, which is the interesting part

After the AI answers, code checks two things **per block**:

1. **The numbers must be identical.** Every number in the output must appear in the input, and every
   number in the input must survive.
2. **The source tags must be identical.** Same `[c412]` markers, same count.

If either fails, **that block keeps its original text** and the failure is logged. The rest of the
article still gets cleaned. It is not all-or-nothing like coherence, because one bad block should not
cost you seventeen good ones.

The prompt tells the AI this is happening, in those words:

> HARD LIMITS — checked by code after you answer; a violation throws your whole block away.

## Real numbers from the four articles

| Article | blocks | cleaned | already clean | changes made | rejected by the guard |
|---|---|---|---|---|---|
| hackathon | 18 | 0 | 18 | **0** | 0 |
| strategic | 34 | 30 | 4 | **110** | 0 |
| cost-per-hire | 19 | 10 | 9 | 21 | 0 |
| Type D | 16 | 11 | 5 | 37 | 0 |

And the counters it tracks, before and after:

| Article | em dashes | "delve"-type words |
|---|---|---|
| strategic | **77 → 9** | 8 → 5 |
| Type D | **38 → 5** | 3 → 2 |
| hackathon | 0 → 0 | 0 → 0 |
| cost-per-hire | 0 → 0 | 0 → 0 |

### What this tells you

**It works.** 77 em dashes down to 9 is a real result on a real article.

**The guard has never once fired.** Zero rejected blocks across 87 blocks and 168 changes. Either the
AI is genuinely respecting the fact rules, or the guard is easier to pass than it looks. Four runs is
not enough to know which.

**Two articles needed nothing.** Hackathon came back with 18 of 18 blocks already clean. That is the
correct outcome, not a failure, and it is worth knowing that this step is honest enough to do nothing
when there is nothing to do.

**It does not get everything.** Nine em dashes survived on strategic, five on Type D. That is by
design: the rules set a budget of about two per thousand words rather than zero, and the leftovers
are then swept up by the next-but-one step. See the handoff under Clean below, because it is the
clearest evidence in this document that two steps are correctly divided.

## Real examples of what it changed

Taken straight from the saved reports:

| Before | After | Rule |
|---|---|---|
| "scope — who the candidate had to align, and how much…" | "scope: who the candidate had to align…" | em-dash budget |
| "**Strong vs. Weak Answer Patterns.**" | "Strong vs. Weak Answer Patterns." | Bold overuse |
| "the benchmark genuinely was not moving" | "the benchmark was not moving" | hollow intensifier (genuinely) |
| "negative affectivity — with items like" | "negative affectivity, with items like" | em-dash budget |

## The prompt, in full

`slop-rules.md` is 5,977 words and is not reproduced here. Its P0 block is quoted above, which is the
part that governs safety. The rest is the pattern list, and it lives in one file precisely so you can
read it there.

```
You are cleaning ONE block of a finished article of AI writing patterns ("AI-isms") — the tells
that make text read machine-written. The article's facts, structure and voice are settled; your
only job is removing the patterns below wherever they appear in this block.

THE RULESET — priorities and patterns (P0 fix always · P1 fix before publishing · P2 only where
the fix clearly reads better):

{{RULES}}

────────────────────────────────────────────────────────────────────────
THE BLOCK, as written:

{{TEXT}}

────────────────────────────────────────────────────────────────────────
HOW TO WORK:
- Fix every P0 and P1 you find. Fix a P2 only where the fix clearly reads better.
- Preserve passages that are already clean — a sentence with no tells comes through untouched.
  This is pattern removal, not a rewrite. Most sentences should survive unchanged.
- Keep the writer's meaning and voice. You remove tells; you do not impose a new style.
- Keep the block's SHAPE. If it arrived as a numbered or dashed list, it leaves as one, with the same
  markers ("1." / "- ") and one item per line. Never merge a list into a paragraph, and never break a
  paragraph into a list — the shape was decided upstream and is not a writing tell.

HARD LIMITS — checked by code after you answer; a violation throws your whole block away:
- No fact, number, statistic, name, quote or claim may be added, removed or altered. Every number
  in your output must appear in the input, and every number in the input must survive.
- Every [c…] source tag stays attached to the same claim it proves. Never add, drop or move one.
- If fixing a tell would force a fact or number to change, leave that sentence as it is.

Return ONLY this JSON, nothing else:
{"prose": "<the block after your fixes>",
 "changes": [{"before": "<the original phrase or sentence>",
              "after": "<what it became>",
              "rule": "<which tell it was, in 2-4 words>"}]}
```

---
---

# STEP 6 — LINKS

## What it does

Three different jobs, three separate AI calls, one step. This is the biggest and most complicated
step in the writer, 849 lines of code.

| Pool | What it is | How many |
|---|---|---|
| **Inline** | A link laid over words that already exist, pointing to another Testlify page | 3 to 5 |
| **Read-more** | One added line saying "we cover this in full here" | 0 to 2, usually 0 or 1 |
| **External** | Which of the article's citations become visible clickable sources | up to 10 |

## Pool 1: inline links

**The rule that shapes everything: the link goes over words already in the article.** Not one
character may be added to make a link fit.

Where the candidates come from: Testlify pages found by searching the site for **each section's own
subject**, not the article's subject in general.

Each candidate arrives with two things:

- A **match score**, 0 to 1, from the search. The prompt is blunt that this is a hint only: *"Treat
  it as a hint about where to look first, never as permission."*
- **The page's real opening text.** *"Judge on this, not on the URL and not on the title."*

### The three tests, each written after a real failure

This is the best-documented part of the whole write phase, because each test names the article it was
added for:

| Test | The real mistake that created it |
|---|---|
| **Same activity** | A section on rubric anchors for a **hackathon** was linked to a page about scoring **video interviews**. Both use rating scales, so it looked like a match |
| **Same side** | A sentence about **candidates** using AI was linked to a guide about **recruiters** using AI. Same technology, opposite person |
| **Same direction** | A sentence saying research does **not** use job performance as an outcome was linked to a page arguing a trait model **does** predict it |

The prompt's own summary: *"'It is broadly about the same subject' is exactly how each slipped
through."*

### The anchor rule, where links are usually lost

The anchor is the words the link sits on. It must:

- Already exist in that section, **word for word, character for character**. A mismatch and code
  throws the link away.
- Be 2 to 6 words, and **name the thing the target page is about**.

The prompt gives both sides, using real examples from real articles:

> **Good**, because each names its target's subject: "cost per hire" · "indirect hiring costs" ·
> "work sample test".
>
> **Bad**, all of these were really placed: "A role sitting empty" · "Defending a placement decision
> later" · "turns to adaptability" · "Candidates are already using AI".
>
> The test: read the anchor alone, with no sentence around it. If it does not tell you what page it
> opens, it is the wrong anchor.

One more rule worth knowing: **include at least one product page** if the words honestly allow it.
Pricing, the test library, a calculator, a template. *"The reader who just read about scoring
candidates is the reader who wants the test library, and sending them to another blog post instead
wastes the moment."*

## Pool 2: the read-more pointer

**This is the only step in the entire write phase allowed to add a sentence.** Everything else can
only edit what exists.

That is why it exists. Some Testlify pages are a full treatment of a sub-topic, a calculator or a
complete guide, and the article may simply never use the words that would let a link sit over
existing text. Without this, the reader never learns those pages exist.

The test is harder than for an inline link. The page must **build on** what the reader just learned,
not merely relate to it.

Candidates come from meaning-matching: the article's fingerprint compared against Testlify's whole
site, which was turned into numbers in advance by the reuse-check work.

Two details:

- It may **lightly smooth** the sentence before and after so the added line does not read as bolted
  on. Every adjustment must be reported word for word, and code audits it. An unreported change is
  thrown away.
- The line ships exactly as written, because **the style-cleaning pass has already run**. The prompt
  says so: *"nothing downstream will fix it for you."*

## Pool 3: external links

Every fact in the article already carries a verified citation. Showing all of them would mean dozens
of links, most pointing at ordinary pages. This call picks which ones become visible.

Competitor domains and Testlify's own domain are removed **by code** before the AI sees anything.

The AI then judges them **against each other, not one by one**, because credibility is relative:

- **Credibility first.** Research bodies, government data, peer-reviewed journals, recognised industry
  surveys. Down: anonymous blogs, content-marketing pages, listicles. *"A page that merely repeats
  another source's number loses to the source itself."*
- **Prefer the critical numbers.** A claim carrying a decision-shaping figure is where a reader most
  wants a link to check.
- **One per domain**, hard maximum two.

The ones not kept do not vanish. They stay as internal provenance; they just are not shown.

## The integrity check

This is the strongest guard in these four steps.

**Undo every change the AI said it made. The text must then equal the original, exactly.** Anything
that does not match means a change was made and not declared, and that block is reverted.

It cannot be fooled by under-reporting, because under-reporting is precisely what it detects.

## Real numbers from the four articles

| Article | inline placed | failed | external kept | read-more |
|---|---|---|---|---|
| hackathon | **2** | 1 | 10 | 0 |
| strategic | 6 | 0 | 10 | 0 |
| cost-per-hire | 6 | 1 | 8 | 0 |
| Type D | 5 | 0 | 9 | 0 |

And what it turned down:

| Article | inline rejected | read-more rejected | external rejected | competitor urls blocked | dead links dropped |
|---|---|---|---|---|---|
| hackathon | 12 | 4 | 6 | 0 | **3** |
| strategic | 14 | 4 | 5 | 1 | 0 |
| cost-per-hire | 15 | 3 | 6 | 1 | 0 |
| Type D | **36** | 4 | 3 | 1 | 0 |

**The integrity check passed on all four.** 13, 29, 14 and 11 checks respectively, all clean.

### What this tells you

**The rejection rate is very high, and that is the design working.** Type D looked at 36 inline
candidates and placed 5. The three tests exist to reject, and they do.

**The read-more pointer has never fired. Not once, on any article.** Its own prompt says *"One
pointer is the normal outcome. Zero is right only when the candidates genuinely offer nothing
deeper."* Zero on four out of four means either Testlify has no page that genuinely continues these
articles, or the test is set too hard. Nobody has checked which.

**Hackathon placed 2 links against a target of 3 to 5**, and had 3 dead links dropped. Its
candidate pool was weak.

**"Failed" is not the same as "rejected".** A failure is a link the AI wanted to place that code
could not use, almost always because the anchor did not match the article word for word. Two of four
articles lost one that way.

## The three prompts, in full

### inline-links.md

```
You are placing INTERNAL LINKS into a finished article published by {{BRAND}}. An internal link
lays a link over words that ALREADY EXIST in the text, pointing to another {{BRAND}} page.

Below is every section of the article, in order. For each one you get what that section must
deliver, its text, and a shortlist of pages found by searching our site for that section's subject
specifically — not the article's subject in general.

Each shortlisted page comes with two things you must actually use:
- A MATCH SCORE from 0 to 1. Higher means our search thought the page was a closer fit. Treat it as
  a hint about where to look first, never as permission: a high score still has to survive your own
  reading below.
- WHAT IS ACTUALLY ON THAT PAGE — the page's real opening text. **Judge on this, not on the URL and
  not on the title.** A title like "Hiring via Job Simulation" can sit on a page that never once
  discusses the thing your section is about. The opening text tells you what is really there. If the
  text does not visibly cover the exact thing the anchor words claim, do not use that page.

{{SECTIONS}}

────────────────────────────────────────────────────────────────────────
THE TEST for every link — value first, always: a reader who clicks it must land on a page that
gives a genuinely deeper or more practical treatment of the exact thing those words talk about.
The link is a promise ("more on this here"); a link that breaks that promise teaches the reader to
stop clicking. When in doubt, do not link.

SAME TOPIC IS NOT ENOUGH. Before accepting any page, run these three checks. Each one has failed a
real article, and "it is broadly about the same subject" is exactly how each slipped through.
- SAME ACTIVITY, not merely the same idea. A section teaching rubric anchors for a HACKATHON was
  linked to a page on scoring VIDEO AND AUDIO INTERVIEWS. Anchored rating scales appear in both, so
  it read as a match. The reader was promised hackathon rubric help and got interview scoring. If
  the page teaches the technique in a different exercise, format or setting, reject it.
- SAME SIDE. A sentence about CANDIDATES using AI was linked to a guide about RECRUITERS using AI.
  Same technology, opposite person. Check who the page is written for and who the sentence is about.
- SAME DIRECTION. A sentence saying the research does NOT use job performance as an outcome was
  linked to a page arguing that a trait model DOES predict job performance. A link on a negative or
  limiting statement must not point at a page that asserts the opposite.

THE RULES:
- {{HOW_MANY_LOW}} to {{HOW_MANY}} links across the WHOLE article — this piece runs {{WORDS}} words, and
  that is the allowance a reader can absorb over that length. It is a target, not a quota: fewer beats
  forced, and if only half that many pages genuinely earn a link, place only those and say why in
  "rejected". Never stretch to reach the number.
- AT MOST ONE link per section. A section with nothing worth linking gets none, and most sections
  will get none — that is the normal outcome, not a failure.
- You are seeing every section at once for a reason: when the same page fits two sections, give it
  to the one whose words are the better home and leave the other alone. Never use one page twice.
- SPREAD THEM. Links bunched in the first three sections are worse than four spread across the piece.
- INCLUDE AT LEAST ONE [PRODUCT] PAGE if any section gives you honest words to hang it on. A product
  page is pricing, the test library, a specific test, a calculator, a glossary entry, a template.
  The reader who just read about scoring candidates is the reader who wants the test library, and
  sending them to another blog post instead wastes the moment. If no product page genuinely fits the
  words on the page, say so in "rejected" — never bend a sentence to fit one.

THE ANCHOR — this is where links are usually lost:
- It is a run of words that ALREADY EXISTS VERBATIM in that section's text above. You may not add,
  reword, extend or shorten the article by a single character to make a link fit.
- QUOTE IT EXACTLY: same capitalisation, same spacing, same hyphens, character for character. Copy
  it from the section's text, never from a heading — headings are not linkable. An anchor that does
  not match is thrown away by code and the link is lost.
- 2 to 6 words, and it must NAME THE THING the target page is about — a noun phrase a reader could
  look up. Not a description of what the sentence is doing.
  Good, because each names its target's subject: "cost per hire" · "indirect hiring costs" ·
  "stakeholder management" · "disparate-impact liability" · "work sample test".
  Bad, all of these were really placed and all describe the sentence instead of the destination:
  "A role sitting empty" · "Defending a placement decision later" · "turns to adaptability" ·
  "Candidates are already using AI" · "another judge reviews the evidence independently".
  The test: read the anchor alone, with no sentence around it. If it does not tell you what page it
  opens, it is the wrong anchor. Pick different words from the same section, or place no link.
- Never "click here", never a whole sentence, never a verb phrase.
- No two links may use the same wording.

Return ONLY this JSON, nothing else:
{"links": [{"section": "<the section heading, exactly as given above>",
            "anchor": "<the exact words from that section's text, verbatim>",
            "url": "<the target, from that section's shortlist>",
            "why": "<one line: what deeper value the reader gets by clicking>"}],
 "rejected": [{"url": "<a candidate you did not use>", "why": "<one line>"}]}
```

### read-more.md

```
You are deciding whether this article gets a "read more" pointer — a single added line inviting
the reader to a {{BRAND}} page that CONTINUES what this article started: a full, in-depth
treatment of a sub-topic this article could only cover in part. This is a stronger test than an
inline link: the target page must BUILD ON what the reader has just learned here, not merely
relate to it. The reader should finish that page knowing meaningfully more about the sub-topic
than this article alone could teach them.

THE ARTICLE, in full:

{{ARTICLE}}

THE CANDIDATE PAGES — found by meaning-similarity against {{BRAND}}'s whole site; these are the
only options. Each comes WITH ITS ACTUAL OPENING TEXT, so judge the page's real depth — a thin stub
does not qualify however good its title sounds:

{{CANDIDATES}}

────────────────────────────────────────────────────────────────────────
THE RULES:
- ONE pointer is the normal outcome. Two is the maximum. Zero is right only when the candidates
  genuinely offer nothing deeper than what this article already says.
  This is the ONLY step that may add a sentence, so it is the only way a reader ever learns that a
  full treatment exists — a calculator, a template, a complete guide — when the article never
  happens to use the words that would let a link sit over existing text. If a candidate genuinely
  continues this article, add the line. Do not hold back to seem disciplined.
- The pointer is ONE line — a natural sentence in the article's voice, any phrasing that fits
  ("We've broken down X in full here", "For a deeper look at X, see our guide", or better),
  ending with the link. Never more than one line. No heading, no box, no second sentence.
- Write the line with the link as markdown: the anchor words inside [.…](url).
- Place it where the sub-topic lives: name the section it should follow.
- SMOOTHING IS ALLOWED, SPARINGLY: if the line lands awkwardly between two existing sentences,
  you may slightly adjust the sentence immediately before and/or after it so the pointer reads as
  part of the flow. Report every such adjustment verbatim (the exact old sentence and the exact
  new one) — code applies and audits them, and an unreported change is thrown away. The
  adjustments must not touch any number, fact, or [c…] tag.
- The pointer line itself must contain NO factual claim and NO number — it is navigation, not
  content.
- The line is written in clean house style: NO em dashes (— or --), no "dive into", no "check out",
  no exclamation mark. A plain comma or a full stop does the job. This line is added AFTER the
  style-cleaning pass, so nothing downstream will fix it for you — it ships exactly as you write it.

Return ONLY this JSON, nothing else:
{"pointers": [{"after_section": "<heading of the section the line follows>",
               "line": "<the one line, with [anchor](url) inside it>",
               "url": "<the target url>",
               "why": "<one line: what the reader learns there that this article could not teach>",
               "adjust_before": {"old": "<exact sentence>", "new": "<exact sentence>"} | null,
               "adjust_after":  {"old": "<exact sentence>", "new": "<exact sentence>"} | null}],
 "rejected": [{"url": "<candidate>", "why": "<one line — related is not enough; say what depth it lacks>"}]}
(pointers is [] only when nothing genuinely deepens the article — not the usual answer)
```

### external-links.md

```
You are choosing which of this article's cited sources become VISIBLE LINKS in the published
version. Every fact in the article already carries a verified citation; showing all of them would
mean {{TOTAL}} links, most pointing at ordinary pages. Your job: pick the ones genuinely worth a
reader's click and the article's endorsement — the published article will link ONLY these, and
its short Sources list will contain ONLY these.

Judge them AGAINST EACH OTHER, not one by one — credibility is relative, and you can see the
whole field:

THE CANDIDATES — every distinct source the article cites (competitor and own-brand domains are
already removed). Each entry: domain · url · how many claims in this article it supports · the
key claims (with a ★ marking claims that carry a load-bearing NUMBER):

{{CANDIDATES}}

────────────────────────────────────────────────────────────────────────
HOW TO CHOOSE — at most {{MAX}} , fewer if fewer deserve it:
- CREDIBILITY FIRST: primary sources beat write-ups about them. Research bodies, government
  data, peer-reviewed journals, recognised industry surveys (SHRM, LinkedIn, Gartner and peers),
  named-methodology studies — up. Anonymous blogs, content-marketing pages, aggregator listicles
  — down. A page that merely repeats another source's number loses to the source itself.
- PREFER THE CRITICAL NUMBERS: a claim carrying a specific, decision-shaping number (★) is
  exactly where a reader wants a reliable link to check. All else equal, the source behind a
  ★ claim beats the source behind prose.
- ONE PER DOMAIN unless a second page from that domain supports a genuinely different set of
  claims (hard max 2 per domain).
- For each kept source, give the anchor: if the prose NAMES the source near its claim ("SHRM's
  2025 survey"), return that exact phrase as "anchor_phrase" so the name itself becomes the link;
  otherwise return null and the citation marker will carry the link. Quote the phrase EXACTLY as
  the body text spells it — same capitalisation, spacing and punctuation, copied from the
  paragraphs, never from a heading. A phrase that does not match character-for-character is thrown
  away by code.

Return ONLY this JSON, nothing else:
{"kept": [{"url": "<the source>",
           "anchor_phrase": "<exact phrase from the prose that names this source, or null>",
           "why": "<one line: why this source earns the endorsement>"}],
 "rejected_examples": [{"url": "<a notable rejection>", "why": "<one line>"}]}
```

---
---

# STEP 7 — CLEAN

## What it does

Pure code. No AI. No cost. It **never rewrites a word.** It fixes characters and spacing.

## The four jobs

**1. Invisible characters.** Characters you cannot see but that are in the file. Zero-width joiners,
byte-order marks, soft hyphens, direction marks. All deleted. Exotic spaces are turned into normal
spaces rather than deleted, because they look like a space and removing one would join two words.

Real measurement from a real draft: **31 narrow no-break spaces** survived every other pass, sitting
inside "85 %" and "New York City". As the code comment puts it: *"No human types one; it is a machine
fingerprint."*

**2. Lookalike characters.** Characters that render like an ordinary one but are not. The
non-breaking hyphen was the **most common non-ASCII character in a real finished draft, 63 of them**,
more than twice the invisible spaces.

Why that matters: `role‑specific` with a non-breaking hyphen does not match a search for
`role-specific`. Search, find-and-replace and exact matching all quietly fail. Nothing else in the
pipeline was catching it.

**3. Dashes.** Em dashes **and** en dashes. The slop pass only names em dashes, so seven en dashes
shipped in that draft. A number range like "60-90 minutes" becomes "60 to 90 minutes", never a comma,
because a comma breaks the sentence.

**4. Whitespace.** Runs of spaces, spaces before punctuation, trailing spaces, three or more blank
lines in a row.

## What it deliberately leaves alone

**Curly quotes.** Word, Google Docs, macOS and iOS all curl quotes automatically, so they are normal
in finished writing. There were 34 in that draft. Stripping them would be a change with no benefit to
the reader.

**Maths symbols** that carry meaning: ≥, ≈, ×.

## Two safety details

**It protects urls, markdown links and source tags.** Before any rule runs, those are lifted out and
replaced with placeholders, then put back afterwards. So no rule can reach inside a url and break it.

**It is idempotent**, which means running it twice changes nothing the second time. This is asserted
in code, not assumed.

## Real numbers from the four articles

| Article | fixes | what they were |
|---|---|---|
| hackathon | **0** | nothing to fix |
| cost-per-hire | **0** | nothing to fix |
| Type D | 27 | 19 lookalike hyphens, 6 em dashes, 1 number range, 1 en dash |
| strategic | **79** | 47 trailing spaces, 12 lookalike hyphens, 11 number ranges, 9 em dashes |

## The handoff, which is the thing to notice

This is the clearest evidence in this document that two steps are correctly divided.

| Article | em dashes slop left behind | em dashes clean then fixed |
|---|---|---|
| strategic | **9** | **9** |
| Type D | 5 | 6 |

Slop takes the em dash count from 77 down to 9, because its budget allows roughly two per thousand
words. Clean then takes the last 9 to zero, mechanically, for free.

Type D's extra one is not an error. It was **in a heading**, and slop is forbidden from touching
headings. Clean has no such restriction, because changing a character in a heading is not changing
the heading's words.

Two steps, one job, no overlap and no gap. That is what the split is supposed to look like.

---
---

# STEP 8 — ASSEMBLE

## What it does

Pure code. No AI. No cost. It builds the two files you actually look at.

| Output | What it is |
|---|---|
| `writer/draft.md` | The finished article: H1, intro, sections, FAQ, close, sources |
| `writer/article.html` | The review page. Hover a statistic to see its source. Hover a keyword to see what kind it is |
| `writer/_work/keyword-coverage.json` | The keyword count, measured from the finished text |

## The one rule that matters here

**It counts the keywords itself. It never asks.**

The code comment says it plainly:

> Coverage is arithmetic, so code owns it: the editor decides WHICH keywords to weave, this step
> counts what actually landed. A count the AI reported about itself would be a guess.

That is not theoretical. Blend's own keyword report has been measurably wrong: it claimed 6 keywords
woven out of a set of 5 on one article. This step is why that lie never reaches you.

It also strips markdown links down to their visible words before counting, so a keyword that only
appears inside a url is never counted as a real use.

## Which file it reads

It tries these in order and uses the first it finds:

```
scrubbed.json  →  linked.json  →  polish.json  →  coherent.json  →  wrapper.json
```

So if a late step failed, the article still gets built from the most finished version that exists.

**A small bug worth fixing:** the docstring at the top of `assemble.py` says it reads
`wrapper.json`. That was true once. The real chain is the five files above.

## Real numbers from the four articles

| Article | primary keyword | times used | in the H1 | in the first 100 words | in headings | in the close |
|---|---|---|---|---|---|---|
| cost-per-hire | "cost per hire" | **29** | yes | yes | 4 | yes |
| Type D | "type d personality" | **26** | yes | yes | 5 | yes |
| hackathon | "hackathon judging" | 5 | yes | yes | **0** | yes |
| strategic | "good questions to ask an interviewee" | **2** | **NO** | yes | **0** | yes |

### What this tells you

**Two articles are strong.** Cost-per-hire and Type D use their keyword 26 to 29 times, in the H1, in
several headings, in the opening and in the close. That is what good looks like.

**Strategic has failed on its main keyword, and this is the step that tells you.** The phrase "good
questions to ask an interviewee" appears **twice in the whole article**, is **not in the H1**, and is
in **no heading**.

That is not this step's fault. It is not the writer's fault either. The architect owns the H1 and
picks the keyword, and on that article the two do not match each other. Assemble is simply the first
place anyone would notice, because it is the first place anyone counts.

**Hackathon has a milder version of the same thing:** in the H1, but in no heading, and used 5 times.

This is the single most useful number these four steps produce, and it is produced by arithmetic, for
free, at the very end.

---
---

# READING THE ARTICLE AT EVERY STEP (added 2026-08-13)

Every step page in this document answers "what did this step CHANGE?" with diffs, counts and flags.
None of them answered "how does the article read now?", so you could see that blend cut a repetition
and still have no idea what the piece looked like afterwards.

`scripts/build_stage_reads.py` fixes that. It writes one clean page per step, in the same style as the
published article: no keyword highlights, no hover tooltips, no scoring panel.

| Page | The article... |
|---|---|
| `writer/reads/write-body.html` | as its writers produced it, blind to each other |
| `writer/reads/blend.html` | joined and cut back |
| `writer/reads/wrapper.html` | with the title, intro, FAQ and close added |
| `writer/reads/coherence.html` | after the contradictions were fixed |
| `writer/reads/slop.html` | after the writing tells were stripped |
| `writer/reads/links.html` | with internal links and only the sources that survived |
| `writer/reads/clean.html` | after the character scrub |
| `writer/reads/assemble.html` | finished, exactly as it would publish |

**How to reach them.** Every step's review page carries a link to its own read. Each read carries a
row of links to the others, so you can walk the article forward without going back to the index. The
front door lists the whole set under "what the client actually receives".

**A step that has not run is greyed out**, so a run stopped after coherence shows five reads and four
greyed names rather than four broken links.

It runs as part of `eval_pages.build_all`, so it happens on every run with no extra command.

**One thing this changed about `article.html`.** That page is the REVIEW artifact: it highlights every
keyword and hangs a tooltip off every statistic, which is what you want for tracing a number and
exactly what you do not want for reading. It now opens with a line pointing at the clean read, and the
front door lists the clean read first.

---
---

# Part 9 — What these four get right, and what is wrong

## What is genuinely good

**The AI/code split is the cleanest design decision in the write phase.** Judgment goes to the AI,
counting and characters go to code. Clean and assemble cost nothing, never drift, and give the same
answer every run.

**The slop-to-clean handoff is exact.** 9 em dashes left, 9 em dashes fixed.

**The links prompt learns from real mistakes.** Same activity, same side, same direction, each written
after a specific bad link shipped. Most prompts state rules. This one states the failure that caused
the rule.

**The integrity check cannot be fooled by under-reporting**, because under-reporting is what it
detects.

**Assemble counts rather than trusts.** It is the only reason you know strategic's keyword failed.

## What is wrong

**1. The read-more pointer has never fired.** Zero on four out of four. Its own prompt says one is
normal and *"do not hold back to seem disciplined."* Either Testlify has no page that genuinely
continues these articles, or the test is set too hard. Nobody has checked.

**2. Slop's guard has never fired either.** Zero rejected blocks across 87 blocks and 168 changes.
That is either the AI behaving or a guard that is easy to pass. Four runs cannot tell you which.

**3. The external link cap is 10, not the 4 or 5 the reviewer asked for.** Three of four articles kept
9 or 10.

**4. Inline links come in under target.** The aim is 3 to 5. Hackathon placed 2. Two articles lost a
link to an anchor that did not match the article word for word.

**5. Nothing checks that the primary keyword reached the H1.** Assemble records that it did not.
Nothing acts on it, and the article ships.

**6. `assemble.py`'s docstring is out of date** about which file it reads.

---

# Part 10 — Change hooks

Neutral list. Nothing here is decided.

**Cheap and obvious**
1. Fix the `assemble.py` docstring.
2. Lower the external link cap from 10 towards the reviewer's 4 or 5.

**Worth investigating before changing**
3. Why has the read-more pointer never fired? Read the four articles' `read_more_rejected` reasons.
   Twelve rejections are on record with a reason for each.
4. Why do inline links fail on the anchor? Two articles lost one each. The anchor must match word for
   word, and the reasons are logged.

**Bigger**
5. **A keyword gate at the end.** Assemble already knows the primary keyword is missing from the H1
   and from every heading. Nothing acts on it. This is the same shape as every other gap in the write
   phase: a number is measured, written down, and read by nobody.
6. Readability. Flesch score, twelfth-grade check. Pure arithmetic, no AI, and it lives nowhere in the
   machine. Assemble is the natural home, because it already counts things at the end.
