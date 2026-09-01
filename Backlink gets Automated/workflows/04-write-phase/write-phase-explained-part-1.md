---
type: WRITE PHASE EXPLAINED, PART 1 — blend, wrapper and coherence (writer steps 2, 3 and 4)
purpose: so you can hold all three in your head and know exactly where any change belongs
covers: scripts/blend.py + wrapper.py + coherence.py, and their four prompts, quoted in full
companion: write-phase-explained-part-2.md (steps 5-8) · write-body-explained.md (step 1) · architect-explained.md
real numbers from: the 4 finished Testlify articles. BLEND's and the WRAPPER's are from their OLD
  designs, which is why both were rebuilt. Both rebuilds have now run ONCE, on cost-per-hire
  (2026-08-12); that run's results are not folded into the tables below, which remain old-design.
  Only COHERENCE's numbers describe code that is still in place.
last_updated: 2026-08-13
---

# The Editors, explained

Write body finished. Twelve writers each produced one section, none of them able to see another's
text. What exists at this point is not an article. It is a pile of sections that happen to be in the
right order.

These three steps turn that pile into an article. Then four more steps clean it up.

**BLEND and the WRAPPER were both rebuilt on 2026-08-11 and each has now run once**, on
cost-per-hire on 2026-08-12. One run is not a record. Coherence is untouched and still the only one
of the three with four runs behind it, though that same run produced its first ever block. That
matters when you read the output: if two sections contradict each other, that is old code doing what
it has always done. If blend or the wrapper does something surprising, that is new and barely tested.

---

## Part 0 — The one idea

**All three are editors, and no editor is handed any cards.**

Write body was allowed to state facts because it was given cards. These three are given **prose
only**. They never see a card, never see a source URL, never see the research. So the only facts in
front of them are the ones already sitting in the sections.

That single design choice is why nothing after write body can fabricate anything in the body. It is
also why these steps cannot fix a section that is missing a fact. They can only rearrange, cut, and
connect what is already there.

**One deliberate exception, added 2026-08-11: the FAQ.** An FAQ question that the article already
answers is a wasted slot, because a search engine will lift the section's own sentence. So the FAQ
is allowed to ask something the article does not cover and answer it from what the model knows. That
makes the FAQ the one part of a published article with no sourced card behind it. Code measures
which figures in an answer are not in the article and shows them, but never removes them.

Everything else in this document follows from those two things.

---

## Part 1 — Where they sit

```
writer/_work/body.json          12 sections, written blind to each other
        |
   >>> BLEND <<<                step 2 — join them, then cut what did not earn its place
        |
writer/_work/blend.json
        |
   >>> WRAPPER <<<              step 3 — the intro on PAS, the FAQ, the close
        |
writer/_work/wrapper.json       now a complete article for the first time
        |
   >>> COHERENCE <<<            step 4 — the first read of the whole thing
        |
writer/_work/coherent.json
        |
   slop -> links -> clean -> assemble
        |
writer/draft.md
```

**Reading the article at each of these moments:** every step page links to a clean read of the piece
as it stands after that step, in `writer/reads/`. Added 2026-08-13; see part 2 for how it works.

The order is not arbitrary. Coherence must come **after** the wrapper, because until the wrapper
runs there is no intro, no FAQ and no close, and those carry rules and numbers of their own that can
clash with the body. It must come **before** links, because links match anchor text against exact
sentences and coherence rewrites sentences.

---

## Part 2 — The safety design all three share

Every one of these steps runs the same three-part guard, because every one of them is an AI rewriting
prose it could quietly corrupt.

| Guard | What it does |
|---|---|
| **No cards** | The prompt receives prose. It has no sources, so it cannot cite one it invented. The FAQ is the one deliberate exception, see Part 0 |
| **A tag audit in code** | Code reads every `[c412]` tag out of the output. A tag that was not in the input is an invention. It gets stripped and counted |
| **A malformed reply changes nothing** | If the JSON comes back the wrong shape, the original passes through untouched and it says so loudly |

**The `[c412]` tags are the whole point of the audit.** Each one is how the finished article credits
a fact to a real page. An editor that keeps a claim but drops its tag has just published an unsourced
statistic. The code cannot tell the difference between "cut the claim, cut the tag" (correct) and
"kept the claim, lost the tag" (a citation lost), so it logs every disappearance and lets a human
look.

Across the four finished articles, **zero invented tags were stripped** in blend and zero in the
wrapper. The design works.

---
---

# STEP 2 — BLEND

**Rebuilt 2026-08-11, run once on 2026-08-12.** What follows describes the new design. Every number
in this section is still either from the old design (marked as such) or from code measurements taken
against articles already on disk. That single run's results are not folded in below.

## What it does

One AI call. It receives the whole article, each section's **job**, and an exact list of faults that
code counted first. It returns the whole article edited.

It is no longer a seam repairer. It is **the editor**: the step that reads everything and cuts what
did not earn its place.

## Why it was rebuilt

The old design gave the editor five tiny permitted moves and trusted its self-report. Here is what
that produced across the four finished articles:

| Article | edits made | what they were | keyword set | claimed woven | claimed skipped | tags in → out |
|---|---|---|---|---|---|---|
| hackathon | **1** | "none" | 2 | 2 | 0 | 135 → 135 |
| strategic | 17 | 14 transitions, 3 keyword swaps | 24 | 3 | 23 | 149 → 149 |
| cost-per-hire | **1** | "none" | 5 | **6** | 2 | 130 → 130 |
| Type D | 3 | 2 transitions, 1 re-intro | 13 | **10** | **11** | 113 → 111 |

Three findings, and each one drove part of the rebuild.

**It did nothing on half the articles.** Two came back with `{"what": "none"}` for the entire piece.
On a 4,780-word article written by eight writers who could not see each other, that is not a result.

**Cutting a repetition never once fired.** Zero, across 19,000 words. It was move 2 of 5 and the most
valuable thing the step could do.

**The self-report is fiction.** Cost-per-hire claims 6 keywords woven out of a set of **5**. Type D
claims 10 woven plus 11 skipped out of a set of **13**. Those numbers are arithmetically impossible,
so the editor was guessing, not counting.

Coherence had exactly this failure and was fixed by handing the model a list instead of asking it to
hunt. It went from 1 finding to 27. Blend now uses the same shape.

## The four sub-steps

**1. COUNT, in code.** Free, no AI. Every sentence over 25 words, every paragraph over 4 sentences,
and the body total against the article's word band.

**2. EDIT.** The article, the jobs, and that list. Eleven faults, most valuable first. Returns the
whole article.

**3. MEASURE, in code.** Diff every section. Count every keyword in the finished text. We do not ask
what it did; there is a diff.

**4. GUARDS, in code, all or nothing.** Any blocking failure and the original body publishes,
unchanged and loudly logged.

## What the counter finds

Measured against the two articles currently on disk, so these are the real list sizes:

| Article | sentences | over 25 words | paragraphs over 4 sentences |
|---|---|---|---|
| cost-per-hire | 203 | **36** (18%) | 6 |
| hackathon | 206 | **46** (22%) | 4 |

Two details in the counting that matter:

- **Headings and table rows are excluded.** A markdown table row has no full stop, so it counts as one
  enormous sentence and poisons the list. Coherence hit this same bug.
- **A list is not a paragraph.** A four-item bulleted list is four separate thoughts a reader takes
  one at a time. Counting its sentences and calling it a fat paragraph is a false positive, and it
  produced two of them on the first test run. Its items are still read for over-long sentences.

## What it is told about length

Not a quota. A statement of fact, computed in code:

> the sections below total 4,266 words. The finished article should land between 3,000 and 4,000. An
> intro, five FAQ answers and a close are written AFTER you and add roughly 600 words, so the sections
> need to come in around 2,400 to 3,400. Right now they are over that aim by about 866 words.

The 600-word reserve matters. Blend sees only the sections, because the intro, the FAQ and the close
do not exist until the wrapper runs. Without the reserve it would aim at the full band and the
finished article would land over it every time. Measured across the four Testlify articles, the
wrapper adds 550 to 750 words.

## The jobs, which blend has never seen before

Every section's `job` now goes into the prompt alongside its word target and what was actually
written:

```
1. The $4,700 Figure Is Two SHRM Editions Out of Date  [target 245w, written 264w]
   JOB: Settle what the widely quoted figure actually is: a stack of superseded SHRM editions,
   $4,129 from a 2016 report and ~$4,700 from the 2022 cycle, cited as if current...
```

This is what makes fault 6 possible. Without the job, blend cannot tell "this section never landed
its point" from "this section is about something else."

## The eleven faults

**Only blend can see the first four.** No earlier step could, and no later step will.

| # | Fault | Note |
|---|---|---|
| 1 | Sections that do not connect | The original blend job, now first. Told to keep the word count in mind, because every link it writes adds words |
| 2 | The same point made twice | Never fired once under the old design |
| 3 | A term explained twice | **Delete the second outright.** Not shorten it, not turn it into a reference |
| 4 | A reference to something that is not there | "As we saw above" about something that is not above |
| 5 | The keywords | Moved up from a trailing block. Unchanged in substance: swap the exact phrase into a sentence that already says it |

**Then these, inside any section.**

| # | Fault | Note |
|---|---|---|
| 6 | The first paragraph does not deliver | Framed around the reader who stops after paragraph one, because most do |
| 7 | Fluff | Cut padding, keep connective tissue |
| 8 | A number with no point | A statistic with nothing attached is trivia |
| 9 | Sentences that run long | From the counter's list |
| 10 | Paragraphs that run long | From the counter's list |
| 11 | Too hard to read on one pass | Smallest change that works. Never simplify the idea, only the sentence |

## The leniency rule

This block exists because the obvious failure mode of handing a model a list of 36 long sentences is
that it wrecks 36 sentences to clear the list.

> 25 words is the aim. It is not a guillotine. A 30-word sentence that reads well is fine and you
> should leave it alone.
>
> NEVER WRECK A SENTENCE TO HIT A NUMBER. A sentence chopped at the wrong place, or a paragraph left
> as three stubs, is worse than the long sentence you started with.

It then names the difference. Fix the ones that are long because they are **badly built**, two ideas
jammed together with a "which". Leave the ones that are long because **the idea is long**.

## Who decides what

**The AI decides:** every edit. Which repetition survives, what a transition says, whether a long
sentence is badly built or genuinely long, whether a first paragraph delivers its job.

**The code decides:**
- What goes on the counter's list, and how it is worded
- The length statement and the 600-word wrapper reserve
- Which keywords it sees, carried forward from the architect
- Whether the reply is usable at all, via the guards
- What actually changed, via the diff
- The real keyword counts, in the finished text

## The guards

**BLOCKING.** The whole edit is discarded and the body publishes as written:

| Guard | Why |
|---|---|
| Section count changed | Never a legitimate outcome |
| A heading changed | They belong to the architect |
| A section left empty | Never legitimate |
| More than 25% of source tags gone | That is not editing, that is dropping brackets |

**WARNING.** Surfaced loudly, edit still applies:

| Warning | Why it does not block |
|---|---|
| A few source tags lost | Correct when the claim was cut. Blocking a whole article over one costs more than it saves |
| **No edit made at all** | The check that catches what the old design was doing |

The tag threshold is copied from coherence. The old blend had **no threshold at all**: it logged
missing tags and published anyway.

## The prompt, in full

```
You are the editor. The article below was written by twelve different writers, all at once, none of
them able to see any other. Your job is to turn that into one article a person would want to read.

You are the first person to see it whole. Nobody after you reads it as a reader does.

════════════════════════════════════════════════════════════════════════
THE COMPANY publishing this: {{BRAND}} — {{ABOUT}}

THE ARTICLE:
- Title: {{TITLE}}
- What it was built to deliver (the angle): {{ANGLE}}
- What the whole piece argues (the spine): {{SPINE}}

LENGTH: {{LENGTH}}

THE KEYWORDS it targets. The architect chose these and already placed them in the H1 and the
headings. Those are done. What is left is the body prose, which only you can judge, because only
you can see the finished sentences.
- Primary: {{PRIMARY}}
- Natural rewords of it: {{VARIATIONS}}

════════════════════════════════════════════════════════════════════════
WHAT EACH SECTION WAS SUPPOSED TO DO

Every writer was given a job: the one thing their section had to settle. Read these before you read
the article. A section that never lands its job is the most common fault here, and you are the only
one who can see it, because the writer thought it had.

{{JOBS}}

════════════════════════════════════════════════════════════════════════
THE ARTICLE, in order, as written:

{{SECTIONS}}

════════════════════════════════════════════════════════════════════════
WHAT THE COUNTER ALREADY FOUND

These were counted by code, so the list is exact. You do not need to look for them.

{{FLAGS}}

════════════════════════════════════════════════════════════════════════
YOUR JOB. Eleven things, most valuable first.

ONLY YOU CAN SEE THE FIRST FOUR. No earlier step could, and no later step will.

1. SECTIONS THAT DO NOT CONNECT. This is the whole reason this step exists, so start here.
   Where a section does not pick up from the one before, or does not hand off to the one after,
   write the link. Take the room you need. One sentence is usually right, two is fine, a short
   paragraph is fine when the jump is genuinely large.
   Twelve writers who could not see each other produce twelve separate essays sitting in a row.
   Your first job is to make them one piece.
   KEEP THE WORD COUNT IN MIND WHILE YOU DO IT. Every link you write adds words to an article that
   is already at the length shown above. A link earns its words or it does not go in.

2. THE SAME POINT MADE TWICE. Two sections explaining the same thing, or using the same statistic.
   Keep it where it belongs best and cut the second telling. Say which one you cut.
   Twelve writers who cannot see each other WILL repeat each other. If you find none, look again.

3. A TERM EXPLAINED TWICE. A term gets its explanation ONCE, in the first section that uses it,
   and never again. If section 3 explains it in brackets and section 8 explains it again, in
   brackets or in prose, DELETE the second explanation outright. Do not shorten it. Do not turn it
   into a reference. The reader already has it, and being told twice is what makes prose feel
   written by a machine.

4. A REFERENCE TO SOMETHING THAT IS NOT THERE. A writer working alone may say "as we saw above"
   about something that is not above it, or set up something the reader already has. Fix it.

5. THE KEYWORDS. These are what real people type into search for this topic, and the writers never
   saw them, so this is the only chance the article gets.
   Where a sentence ALREADY says one of these things in vaguer words, swap in the exact phrase.
   "The time it takes to fill a role" becomes "time to fill". Same meaning, exact phrase, same
   sentence.
   Only where it already fits. Never bend a sentence to fit a phrase, never add a sentence to house
   one, never repeat one to raise a count. Prefer the exact primary in the sections carrying the
   article's main argument. If a phrase has no home here, report it skipped.
   This is a word swap inside a sentence that already exists. Never a new sentence, never a new
   fact. If a swap makes the sentence read worse, do not make it.

THEN THESE, INSIDE ANY SECTION.

6. THE FIRST PARAGRAPH DOES NOT DELIVER. Compare each section against its job above.
   Assume the reader stops reading after the first paragraph, because most of them do. They should
   still leave with what that section was for: the finding, the number, the verdict.
   If the first paragraph is background, build-up, or a restatement of the heading, the section has
   failed for almost everyone who reached it. Move the answer up. Cut whatever was standing in
   front of it.

7. FLUFF. Throat-clearing before a fact. Restating the heading in the first sentence. A closing
   sentence summarising what the reader just read. A sentence that only re-says the one before it.
   Cut all of it.
   But do NOT cut connective tissue. "Since then", "but", "which is why", "even so" carry the reader
   from one fact to the next. Strip those and the prose stops being an argument and becomes a list.

8. A NUMBER WITH NO POINT. A statistic sitting there with nothing attached is trivia. Say what it
   means for the reader's decision, in the same breath. Use only what the article already says.

9. SENTENCES THAT RUN LONG. The counter listed them. Read the leniency block below before you touch
   one.

10. PARAGRAPHS THAT RUN LONG. The counter listed these too. Over four sentences usually means two
    ideas sharing a paragraph. Split it where the second idea starts, not in the middle.

11. TOO HARD TO READ ON ONE PASS. A capable adult who does NOT work in this field should follow
    every sentence the first time. If you have to read a sentence twice to work out what it says,
    the reader will not read it twice. They will leave.
    FIX IT WITH THE SMALLEST CHANGE THAT WORKS: swap a corporate word for a plain one, cut a clause
    carrying nothing, split where two ideas were joined, or explain a term in a short bracket if it
    genuinely needs one and does not have one.
    DO NOT rewrite the paragraph. DO NOT simplify the idea, and DO NOT drop a real term for a vague
    one. The reader is senior, so the subject stays exactly as hard as it is. Only the sentence gets
    easier.
    AND MIND THE ARTICLE'S LENGTH WHILE YOU DO IT. The smallest change is usually the shorter one.
    Making a sentence readable should not make it longer.

════════════════════════════════════════════════════════════════════════
THE LENIENCY RULE. READ THIS BEFORE YOU CUT ANYTHING.

25 words is the aim. It is not a guillotine. A 30-word sentence that reads well is fine and you
should leave it alone.

NEVER WRECK A SENTENCE TO HIT A NUMBER. A sentence chopped at the wrong place, or a paragraph left
as three stubs, is worse than the long sentence you started with. If a sentence cannot be split
without damage, leave it and move on. Nobody is counting your score.

The ones worth fixing are long because they are BADLY BUILT: two ideas jammed together with a
"which", a second comma-clause carrying a whole new thought, three facts piled into one line. Split
those, and use a real joining word when you do, not just a full stop.

The ones to leave alone are long because THE IDEA IS LONG. One thought that genuinely needs 28 words
is one sentence, not two.

The same holds for the article's total length. You can see the number above. Where the article runs
long, it is because writers used every fact they were handed, and several facts often make the same
point in slightly different words. Cut the weaker telling. Do not compress good prose into shorthand
to save words.

════════════════════════════════════════════════════════════════════════
WHAT YOU MAY NEVER DO

1. NEVER INVENT ANYTHING. No fact, number, name, quote, example or claim. You have no sources and
   cannot verify a thing. Every fact in your output must already be in the article above.

2. NEVER CHANGE A HEADING OR THE H1. The architect researched those against real search data.

3. NEVER DELETE A SECTION. You may cut a paragraph, a passage or a whole argument inside one. The
   section stays, keeps its heading, and must still say something.

4. NEVER MAKE A LIST, AND NEVER UNMAKE ONE. Where a writer set something out as a numbered or dashed
   list, that was a deliberate call about content the reader holds in order. Keep the list, keep its
   markers exactly, keep each item on its own line. Equally, do not turn a paragraph into a list.

5. NEVER REORDER THE SECTIONS. The order was decided deliberately.

6. NEVER TAKE A [c…] TAG OFF A CLAIM YOU KEPT. Each tag is how the published article credits that
   fact to a real page. If you move a sentence, its tag moves with it. If you cut a claim, its tag
   goes with it, and that is correct. What is never correct is keeping the claim and losing the tag.

════════════════════════════════════════════════════════════════════════
HOW TO WORK

- Read the jobs, then the article, then the counter's list. Then decide.
- DO THE WHOLE JOB. Where a repetition spans three paragraphs, cut three. A half-fix that leaves the
  reader with the same problem is worse than no fix, because it looks handled.
- Most sentences will come through untouched, and that is normal. But an article that comes back
  with no edits at all is not a result. Twelve blind writers always leave something.
- Where you are unsure, prefer the smaller edit.

RETURN THE WHOLE ARTICLE, every section in order, changed or not.

Return ONLY this JSON, nothing else:
{"sections": [{"heading": "<unchanged heading>", "prose": "<the section after your edits>"}],
 "edits": [{"section": "<heading>",
            "what": "added transition | cut repetition | deleted a repeat explanation | fixed reference | moved the answer up | cut fluff | added the so-what | split a sentence | split a paragraph | made a sentence readable",
            "why": "<one short line>"}],
 "keywords_used": [{"keyword": "<the phrase>", "section": "<heading>",
                    "how": "swapped a paraphrase for it | it was already there"}],
 "keywords_skipped": [{"keyword": "<the phrase>", "why": "<why no section is genuinely about this>"}]}
```

## What changed from the old prompt

**Gained:** the section jobs, the counter's list, the length statement, and six new faults (job not
landed, fluff, no so-what, long sentences, long paragraphs, too hard to read).

**Deleted:** *"Do NOT rewrite prose that reads fine. Most sentences must come through untouched."*
You cannot ask a step to trim and cut fluff while telling it that. A softer version survives under
HOW TO WORK, so it still prefers the smaller edit without being frozen.

**Reordered:** connection is now fault 1, because that is the step's name and its reason for
existing. Keywords moved from a trailing afterthought to fault 5.

**Strengthened:** a term explained twice is now deleted, not shortened. The old rule said "shorten
the later one to a reference", which still leaves the reader being told twice.

**Reworded:** the tag rule now says what it always meant. It may drop a tag when it drops the claim.
The old wording read as an absolute ban and was confusing.

## What is still unknown

It has run once, on cost-per-hire on 2026-08-12. One run settles none of this, so these are still the
three things to check:

- **Does it edit at all?** The "no edit made" warning exists precisely because the old one didn't.
- **Does the counter's list shrink?** 36 long sentences and 6 fat paragraphs on cost-per-hire is the
  starting number. `counter_after` records what survived.
- **Did it wreck sentences to clear the list?** Read the diff, not the count. A cleared list with
  butchered prose is the failure the leniency rule was written to prevent.

---
---

# STEP 3 — WRAPPER

**Rebuilt 2026-08-11**, on two notes from the SEO reviewer, and run once on 2026-08-12. Every number
in this section is still from the old design, and is the evidence for why it changed.

## What it does

One AI call. It writes everything that is not a body section: the intro, the FAQ, the close. Plus
touch-ups on any section those additions broke.

It is the second most important writing step after write body, because the intro is the only part
most readers finish.

## Why it was rebuilt

### The FAQ had two rules that fought each other

The old prompt said both of these:

- (a) The question must **not** be one the article answers under a heading.
- (b) The answer must be built **only** from facts already in the body.

So a question had to be about something the article does not cover, answered from what the article
does cover. The window between those is very narrow, and the measurements show it closing: **16 of
20 FAQ slots across four articles went to questions the model invented**, not to real searched ones.

The reviewer settled it in one line: *"If it is already included in the article, omit these in FAQ."*
Her reasoning is that a search engine will lift the section's own sentence, so repeating it in an FAQ
wastes the slot.

That confirms rule (a) and kills rule (b). The question may now go anywhere contextually related, and
the answer may be worked out by the model rather than assembled from the body.

**What that costs, stated plainly.** The FAQ becomes the one part of the published article that does
not trace back to a sourced card. Everything else in the piece carries a `[c412]` tag and a real
link. Wiring a search behind each answer was designed and deliberately parked, not forgotten.

### The searched questions turn out to be nearly all unusable

Once you omit everything the article already answers, the pool empties:

| Article | Questions researched | Usable after the rule |
|---|---|---|
| cost-per-hire | 6 | roughly **0** |
| hackathon | **0** | 0 |
| strategic questions | 4, all "list me 10 questions" | roughly **0** |
| Type D | 4 | maybe **1** |

The whole cost-per-hire pool is the article's own headings: *"How do I calculate cost per hire?"*
sits next to a section called "How to Calculate Cost Per Hire (and Where It Stops)".

That is not a bug. The architect built the headings from search demand, so of course they overlap.
But it means the FAQ will be mostly model-found questions in practice, which is why the sourcing
question above matters more than it first looked.

### The prose rules had drifted, and were deleted

The old prompt carried seven writing rules under the line *"Same rules as write-body.md, edit both
files together."* That stopped being true. Write body gained a 25-word sentence ceiling, a
4-sentence paragraph limit, grade 12 and brackets, and none of them reached the wrapper. So the part
of the article a reader meets **first** was held to a **looser** standard than the body, in a prompt
whose own line said to hold it tighter.

They are gone. Six rules that actually apply to an intro, an answer and a close replace them.

## What it receives

| What | Where from | Note |
|---|---|---|
| **The whole article**, already blended | `blend.json` | It is the only writer who reads the piece end to end |
| **The H1** | the architect | Returned exactly. Code stamps it regardless of the reply |
| **The angle and the spine** | the queue and the architect | |
| **The persona** | the planner | **New.** The wrapper never had it, and it writes the most reader-facing part |
| **The primary keyword and its variations** | the architect | Must land in the first 100 words |
| **The searched questions** | the planner's PAA pool | Offered first, as the best available |
| **`features.md`** | the brand pack, **capped at 8 KB** | **Was 69 KB, uncapped**, for a five-sentence close |
| **Three voice files**, trimmed | 6,000 characters each | |

It still receives **no cards**. Giving it the unused card pool was designed and rejected: there is no
way to know the leftover cards are the good ones.

## The four things it writes

**1. The H1.** Returned exactly as given. Code overwrites it either way.

**2. The intro, on PAS.** Four to six sentences, no heading of its own.

| Beat | What goes in it |
|---|---|
| **Problem** | What the reader is actually stuck on. Not the topic, the trouble |
| **Agitate** | Why it is worse than they think. The cost they are not counting. This is where a real figure earns its place |
| **Solution** | What this article settles |

The reviewer offered three frameworks. **PAS was the only one used.** AIDA and FAB both end in
selling something, and the body is deliberately product-free.

One adaptation, worth knowing: her third beat is *"show your product as the fix."* Ours is **the
article's answer**. The prompt states it in caps, because it is the most likely thing to be got
wrong: *"THE SOLUTION IS THE ARTICLE'S ANSWER, NOT {{BRAND}}."*

The banned-opener list survives untouched, with its worked example. It is the strongest thing in the
prompt:

> Wrong: "This article breaks down hard versus soft costs by role and industry."
> Right: "Two thirds of what a hire costs never appears on an invoice."

**3. The FAQ.** Up to five questions. Five is a ceiling, not a target.

- Searched questions first, then its own if it needs more.
- Contextually and semantically related. *An article on cost per hire can take a question on agency
  fee structures or on how cost per hire differs from time to fill. It cannot take a question about
  payroll software.*
- Never one the article answers under a heading.
- **No two questions may be the same question.** Not in other words, not from another angle, not one
  general and one specific version. This rule existed before as the third bullet in a list and was
  invisible; it is now the loudest thing in that block, because a five-question FAQ that is really
  three questions asked twice is the most common failure here.
- 40 words per answer, with the same leniency wording blend uses: *"45 words that read well beat 40
  with the verb missing."*
- Three real questions beat five padded.

**4. The close.** Three to five sentences. Every product claim grounded in `features.md`, and it must
*"never imply it solves something the article showed to be unsolvable."*

**5. Touch-ups.** Adding an intro and a close creates two seams. The first section may now repeat the
intro; the last may not flow into the close. Three moves only, and *"most articles need one or two
touch-ups, not ten."*

## Who decides what

**The AI decides:** every word of the intro, the FAQ and the close. Which questions survive. Which
sections need a touch-up.

**The code decides:**
- **The H1 is stamped from the architect, never from the reply.**
- The tag audit, on the intro, the close, every question, every answer and every touched-up section.
- A touch-up naming a heading that does not exist is **ignored, not guessed at**, and logged.
- If there is no intro or no close, `ok` is false, the article is left completely unchanged, and it
  prints `!! wrapper reply malformed`.

## What code measures and never edits

A version of this step that **deleted** FAQ answers was built and removed the same day. It dropped an
answer carrying a figure the article did not have, and dropped an answer over a 60-word ceiling.
Both were wrong:

- The FAQ is now deliberately allowed to answer past the article, so an outside figure is **expected**,
  not a fault.
- A long answer is a style problem. That is a thing to see on the review page, not a thing for code
  to delete behind your back.

Tested against the four existing articles, the deleting version killed **all five answers on three of
the four**, because every answer written under the old rule ran long.

What survives is measurement only:

| Recorded per answer | Shown as |
|---|---|
| Word count against 40 | "83 words, over 40" or "38 words" |
| Figures not found in the article | "check 2 figures from outside the article", listed underneath |

Nothing is dropped. There is no ceiling and no floor.

## Real numbers, from the old design

| Article | intro | FAQ | dropped | answer length | close | touch-ups | invented tags |
|---|---|---|---|---|---|---|---|
| hackathon | 102 w | 5 | 3 | **87-146 w** | 157 w | 1 | 0 |
| strategic | 90 w | 5 | 3 | **109-140 w** | 163 w | 1 | 0 |
| cost-per-hire | 98 w | 5 | 5 | **66-119 w** | 118 w | 1 | 0 |
| Type D | 64 w | 5 | 0 | **47-61 w** | 65 w | 0 | 0 |

**Every answer was over target.** 47 to 146 words against a 40-word ask. Nothing counted them, which
is why counting them is now the main thing code does here.

**Zero invented tags across all four.** The sourceless design holds for the intro and the close.

**All four returned exactly five**, and three declared dropped questions with reasons, so the model
was genuinely rejecting rather than padding. That behaviour should survive the change from "exactly
five" to "up to five".

## The prompt, in full

```
You have the finished article below, already written and already edited into one continuous piece.
Your job is to write what wraps around it: the opening the reader meets first, the questions they
still have at the end, and the close they leave on.

You are the only writer who has read the whole thing, so you are the right person for it.

════════════════════════════════════════════════════════════════════════
THE COMPANY publishing this: {{BRAND}} — {{ABOUT}}

THE ARTICLE:
- Working H1: {{H1}}
- What it was built to deliver (the angle): {{ANGLE}}
- What the whole piece argues (the spine): {{SPINE}}
- Primary keyword: {{PRIMARY}}
- Natural rewords of it: {{VARIATIONS}}

WHO IT IS FOR:
{{PERSONA}}

THE ARTICLE ITSELF, in order. READ ALL OF IT BEFORE YOU WRITE A WORD:
{{SECTIONS}}

════════════════════════════════════════════════════════════════════════
WRITE THESE FOUR THINGS.

────────────────────────────────────────────────────────────────────────
1. THE H1

Return it EXACTLY as given: "{{H1}}". The architect already placed the primary keyword in it. Not
one character is yours to change.

────────────────────────────────────────────────────────────────────────
2. THE INTRO — 4 to 6 sentences, directly under the H1, with no heading of its own.

BUILD IT ON PAS: PROBLEM, AGITATE, SOLUTION. Three beats, in order.

  PROBLEM.   Open on the thing the reader is actually stuck on. Not the topic, the trouble. One or
             two sentences.
  AGITATE.   Show it is worse than they think. The cost they are not counting, the decision they are
             getting wrong, the number that says so. One or two sentences. This is where a real
             figure from the article earns its place.
  SOLUTION.  What this article settles. One or two sentences.

ON THE THIRD BEAT: THE SOLUTION IS THE ARTICLE'S ANSWER, NOT {{BRAND}}. This is not an ad. The
reader gets what the piece resolves for them. {{BRAND}} is named in the close, and only there.

You have read the whole article, so build all three beats from what is actually in it. The agitate
beat is where most intros go wrong: writers reach for the most striking fact they found instead of
the one that makes the reader's problem hurt.

WRITE FOR SOMEONE WHO KNOWS NOTHING YET. Nothing in your opening may depend on a term, a measure or
a comparison that only the body explains.

BANNED. Never open with, or include anywhere in the intro, any sentence that describes the article
instead of informing the reader:
  "This article breaks down / covers / explores / explains / walks through…"
  "In this article we will…" · "This guide will show you…" · "Below we look at…"
  "Here's everything you need to know about…" · "Let's dive into…"
If you catch yourself naming the article, delete that sentence and state the fact instead.
  Wrong: "This article breaks down hard versus soft costs by role and industry."
  Right: "Two thirds of what a hire costs never appears on an invoice."

Work the primary keyword in naturally. It must appear within the article's first 100 words and must
not read as though it was inserted.

────────────────────────────────────────────────────────────────────────
3. THE FAQ — up to 5 questions, under the heading "Frequently asked questions".

WHERE THE QUESTIONS COME FROM.

  FIRST, these. They are what real people typed into a search engine around this topic, so they
  carry real demand and they are the best questions available to you:
{{PAA}}

  THEN your own, if you need more. You may go BEYOND what the article covers. A reader who finishes
  this piece has a next question, and it is usually about the thing sitting next to the subject
  rather than inside it.
  It must stay contextually and semantically related. The test is whether someone reading THIS
  article would plausibly ask it next.
    An article about cost per hire can take a question on agency fee structures, or on how cost per
    hire differs from time to fill, because someone working on one is working on the other.
    It cannot take a question about payroll software. That is a different subject.

DO NOT ASK WHAT THE ARTICLE ALREADY ANSWERS UNDER A HEADING. If a section is devoted to it, a search
engine will lift that section's own sentence. Repeating it here wastes a slot and tells the reader
nothing new.

THE OTHER THREE TESTS:
  · It is specific enough to have a real answer: a number, a threshold, a method, a verdict. Skip
    the vague ("What is X?" when the whole article is about X).
  · It is phrased the way someone types it into a search box, not invented to sound thorough.
  · NO TWO QUESTIONS MAY BE THE SAME QUESTION. Not in other words, not from another angle, not one
    general version and one specific version of it. If two would be answered with the same facts,
    they are one question wearing two hats. Keep the better-phrased one and find a different one.
    This is the most common fault here: a five-question FAQ that is really three questions, two of
    them asked twice.

HOW TO ANSWER. Answer it properly.
Where the article already holds the fact, use it, and carry its [c…] tag across unchanged.
Where it does not, work the answer out yourself from what you know about how this job is really
done, and write the best short answer there is.
Do not dodge a good question because the article did not cover it. Being able to go past the
article is the entire point of this section.

ANSWER IN {{FAQ_WORDS}} WORDS OR FEWER. Count them.
That is short on purpose. This is the answer a search engine lifts and shows on its own, so it has
to be complete in one breath. Most good answers are one sentence carrying the verdict, then one
carrying the condition.
The leniency: {{FAQ_WORDS_SOFT}} words that read well beat {{FAQ_WORDS}} with the verb missing.
Never break an answer to hit the number. But do not read this as a suggestion either. Every answer
written before this rule existed ran between 47 and 146 words, which is why it is now counted.

THREE REAL QUESTIONS BEAT FIVE PADDED. Five is the ceiling, not a target. If only three pass every
test, return three and say in dropped_questions why the others failed. Never invent a fourth to
fill the space, and never split one question into two to reach the number.

Rank them: the most useful question first.

────────────────────────────────────────────────────────────────────────
4. THE CLOSE — 3 to 5 sentences.

Wrap up what the article established, with no new facts. Then the honest bridge to {{BRAND}}, then
one clear call to action that fits THIS article and THIS reader.

What {{BRAND}} offers:
{{FEATURES}}

  · Ground every claim about {{BRAND}} in that list. Never overclaim. Never imply it solves
    something the article showed to be unsolvable.
  · This is a forward step for the reader, not a recap of what they just read.
  · Work the primary keyword ("{{PRIMARY}}") in where it reads naturally. If it cannot go in without
    sounding bolted on, leave it out and let the close read well.

────────────────────────────────────────────────────────────────────────
5. TOUCH-UPS — the two seams you just created.

Adding an intro and a close creates two joins. The article's first section may now repeat what your
intro said. Its last section may no longer flow into your close. Fix that.

For any section you touch, return its heading and its corrected prose, using ONLY these moves: cut a
repetition, shorten a re-introduction to a reference, add or adjust one linking sentence.

Never add a fact. Never change a heading. Leave every other section alone. Most articles need one or
two touch-ups, not ten.

════════════════════════════════════════════════════════════════════════
HOW THE INTRO, THE ANSWERS AND THE CLOSE MUST READ

This is the first thing a reader meets and the last thing they leave on, so these are held TIGHTER
here than in the body, not looser.

- NO SENTENCE OVER 25 WORDS. Not "most". None. Count them.
- NO PARAGRAPH OVER 4 SENTENCES.
- READING LEVEL: GRADE 12. A capable adult who does NOT work in this field reads it once and gets
  it. You write FOR the reader described above. You write AT twelfth grade. Their seniority earns
  them the subject, not the vocabulary.
- ONE IDEA PER SENTENCE. When you catch yourself joining two points with "which", "while", or a
  second comma-clause, split it in two.
- EXPLAIN A RARE TERM IN A SHORT BRACKET, ONCE. Only a term from inside one profession that a smart
  twelfth grader outside it would genuinely not know. Never explain ordinary working vocabulary:
  cost per hire, turnover, onboarding, ROI, attrition, shortlist. Over-explaining is the worse
  mistake. The intro reaches the least committed reader in the piece, so an unexplained term there
  loses them for good, and an over-explained one insults them.
- WRITE THE PLAIN WORD. Use, not utilise. Help, not facilitate. Start, not commence.
- NO EM DASHES. Use a comma, a colon, or a full stop.

HOW THIS COMPANY WRITES. The sections you are wrapping were written against these, so an opening in
a different voice announces itself.
{{VOICE}}

════════════════════════════════════════════════════════════════════════
ON MENTIONING {{BRAND}}: the close is where it belongs, and nowhere else. Never in the intro, never
in an FAQ answer. A forced mention costs more trust than it buys.

Return ONLY this JSON, nothing else:
{"h1": "<the H1, exactly as given above>",
 "intro": "<4-6 sentences, built on PAS>",
 "faq": [{"question": "<the question>", "answer": "<{{FAQ_WORDS}} words or fewer>",
          "origin": "researched | added"}],
 "dropped_questions": [{"question": "<the one you dropped>", "why": "<one line>"}],
 "close": "<3-5 sentences ending in the call to action>",
 "touch_ups": [{"heading": "<unchanged heading>", "prose": "<that section's corrected prose>",
                "what": "cut repetition | fixed re-intro | added transition", "why": "<one short line>"}]}
```

## That prompt, block by block

- **The framing.** "You are the only writer who has read the whole thing." That is the claim the
  whole step rests on, and it is why the article sits above the instructions with **READ ALL OF IT
  BEFORE YOU WRITE A WORD** over it.
- **The H1** is told to come back untouched. Code overwrites it either way, so the instruction is
  belt and braces.
- **The intro** is the only part with a named structure. Three beats, then the line that matters
  most in caps: *"THE SOLUTION IS THE ARTICLE'S ANSWER, NOT {{BRAND}}."* Without it PAS turns an
  article opening into an ad, because that is what PAS is normally for.
- **The agitate warning.** *"Writers reach for the most striking fact they found instead of the one
  that makes the reader's problem hurt."* That is the failure mode of a writer who has just read a
  whole article full of statistics.
- **The banned openers**, unchanged from the old prompt, with the worked example. A list of shapes
  beats a rule about tone, because a model can check a shape.
- **The FAQ, where the questions come from.** Searched ones first and named as "the best questions
  available to you", then its own. The related test is given as one worked pair rather than a
  definition: agency fees yes, payroll software no.
- **The duplicate rule**, in caps, covering three ways a question can be a repeat. It was the third
  bullet in a list before and nobody reading the prompt noticed it, which is exactly what it warns
  about happening to the reader.
- **HOW TO ANSWER** replaced the old "you have no sources" block. Four lines, no threat, no code
  warning: use the article's fact where there is one, work it out yourself where there is not, and
  *"do not dodge a good question because the article did not cover it."*
- **The 40 words**, with blend's leniency wording and the real history attached: *"every answer
  written before this rule existed ran between 47 and 146 words, which is why it is now counted."*
  A rule with its own evidence in it is harder to ignore than a rule alone.
- **Three beats five padded.** Five is stated as a ceiling twice, once at the top of the section
  and once at the bottom.
- **The close** is the only place the brand appears, and the prompt says so twice: once in the
  close's own rules and once in a standing line at the end.
- **The touch-ups** cap their own expectations: *"most articles need one or two, not ten."*
- **HOW THE INTRO, THE ANSWERS AND THE CLOSE MUST READ**, six rules, every one specific to this
  step. This block replaced seven rules copied from write-body.md that had drifted out of sync
  with it.

## What is still unknown

It has run once, on cost-per-hire on 2026-08-12. Three things still to check:

- **Does the intro actually follow PAS**, or does it write the same "start with the striking fact"
  opening and call the first sentence a problem?
- **Do the answers come down?** 47 to 146 is the starting number. The word count is now recorded per
  answer, so this is directly checkable.
- **How many questions come back?** If it still returns five every time, the "three beats five
  padded" line is not landing.

---
---

# STEP 4 — COHERENCE

## What it does, in one line

**It is the first person to read the whole article, and it asks one question: does this article
disagree with itself?**

## Why that question needs its own step

Twelve writers wrote twelve sections. None of them could see any other. Then:

- **Blend** read everything, but its job is how the article reads, not whether it is true.
- **The wrapper** read everything, but it was busy writing the intro and the close.

So nobody has ever checked whether section 5 and section 9 agree.

Here is the thing that makes this hard. **Every section reads perfectly fine on its own.** The
problem only appears when you hold two of them side by side. Four real examples:

- Section 7 says never do X. Section 5 shows you how to do X.
- Section 3 scores something out of 5. Section 9 scores the same thing 0, 2 or 4.
- Section 2 warns about a risk. Section 8 tells you to do the thing that causes it.

No human reviewer reliably spots these. You would have to hold a 5,000-word article in your head at
once.

## How it works: four steps

Two of them are AI calls. Two are plain code.

**Step 1. Make a list.** An AI reads the article and writes down every rule, every scoring scale,
and every number, plus where each one appears. It is told not to judge anything.

**Step 2. Fix it.** A second AI gets that list first, then the article, then returns the whole
article edited.

**Step 3. Check what changed.** Code compares the before and after, word by word.

**Step 4. Check it did not break anything.** Code runs a set of safety checks. If any serious one
fails, the whole edit is thrown away and the original article publishes.

## Why it is built that way, and not the obvious way

The obvious way was tried first, on 2026-08-05, and it failed. It asked **one** AI call to read the
article and "find anywhere it contradicts itself", then hand back pairs of sentences for code to
swap in.

It failed for two separate reasons, and both shaped the rebuild.

**It could not see.** One finding across four articles. It called three of them "internally
consistent". Those same three articles contained five different scoring scales, a rule that said 5-6
in one place and 3-6 in another, a recommendation that contradicted the article's own legal warning,
and a 19% drop described as "essentially flat".

Why? Because it was asked to work out **what to look for** and **find it**, in one pass. That is
hunting for a needle when nobody has told you what the needle looks like.

**It could not fix.** A pair of sentences can only change one spot. The hackathon article used the
0-2-4 scale in ten different places, with worked examples attached to each. There is no way to
express that fix as a sentence pair. So the old design could not have made it even if it had spotted
it.

The fix for both: **hand it the list, and let it hand back the whole article.**

### Step 1, up close: the list

The file is `coherence-inventory.md`. Its first line tells the AI: *"Do not judge any of them. Do not
look for problems. You are making a list, not a report."*

It writes down three things, and where each one appears:

| The list | What goes in it |
|---|---|
| **Rules and warnings** | Every place the article tells you to do something, not do something, or says something is risky |
| **Scales and ranges** | Every scoring scale or range. "1 to 5", "0-2-4", "pick 5-6 skills". **Every single time it appears, even the same one twice** |
| **Quantities** | Every number, including ones written as words ("a third", "double") and ones written as multiples ("three times salary") |

**The whole trick is in that bold bit.** Recording every occurrence, even repeats, is what makes the
next step work. Once four different scales are sitting in one column, the problem is obvious. Nobody
has to be clever about it.

Two smaller details that earn their place:

- **Multiples are recorded on purpose.** "Three to four times salary" is the figure people miss most
  often, and the one that most often disagrees with a worked example somewhere else in the article.
- **It must describe each number in plain words.** Write "total hiring cost as a multiple of salary",
  not "the 3-4x rule". Two figures for the same thing can only be spotted later if both are described
  the same way.

### Step 2, up close: the fix

The file is `coherence-edit.md`. It gets the list **before** the article, then the article in full.

It fixes exactly four things:

1. **It breaks its own rule.** Says never do X, then explains how to do X.
2. **Advice its own warning covers.** One section names a risk, another recommends the thing that
   causes it. Neither mentions the other.
3. **One job, several scales.** Same thing scored 1-5 here and 0-2-4 there. Pick one, change all of
   them.
4. **Numbers that disagree.** Two figures for the same thing that cannot both be true.

And one rule for when two of these collide: **the warning wins.** If a warning and a recommendation
clash, cut or soften the recommendation, never the warning. Either one makes the clash go away. Only
one is honest.

It hands back the **whole article**, every section, changed or not. That is what makes fix 3
possible: a scale that is wrong in ten places gets fixed in all ten.

The prompt also tells it what not to touch, so it does not undo work done by a step that knew more:
the subject boundary, the headings, the H1, the source markers, and the joins blend already made.

And it says what happens after it, so it does not do someone else's job twice:

> COMING AFTER YOU: a style clean-up, then internal and external links. So do NOT fix awkward
> phrasing, strip AI-sounding words, or add links.

### Step 3, up close: what actually changed

Code compares the article before and after, word by word, using a standard text-comparison tool. It
records every changed passage.

The point is that we do not ask the AI what it changed. We look. The code comment says it plainly:

> we MEASURE what changed rather than trusting it to report. It cannot under-report, because there is
> no report; there is a diff.

### Step 4, up close: the safety checks

There are two kinds. Some throw the whole edit away. Some just get flagged for a human.

**These throw the edit away.** The original article publishes instead, and it says so loudly.

| Check | Why it is this strict |
|---|---|
| A heading or the headline was changed | The architect picked those from real search data |
| A section was deleted or left empty | Never a legitimate thing to do |
| A number appears that was nowhere in the original | That is a made-up fact |
| More than **25%** of source markers gone | That is not editing, that is dropping brackets |

**These only get flagged.** The edit still goes through.

| Flag | Why it does not throw the edit away |
|---|---|
| A few source markers lost | Losing one or two while rewriting is normal. Killing a whole article over one costs more than it saves |
| Numbers that **changed** | **That is the repair.** Turning a 0-2-4 scale into 1-5 has to remove 0, 2 and 4 and add 1, 3 and 5 |
| The article got more than **5%** longer or shorter | A human should look, but it is a judgment call. Was 10% when the four articles below ran |

**That second row is the most important tuning in this step.** The first design blocked on any number
change, and threw away ten good fixes because of it.

### Step 5, added 2026-08-13: one retry

On 2026-08-12 a blocking guard fired **for the first time in five articles**. Coherence found 9 real
faults, fixed all 9, then wrote **"32,000"**, a figure that appears nowhere in the article. All-or-
nothing threw the whole edit away and the original published.

The guard was right. It stopped a fabricated statistic. But losing 9 corrections to catch 1 invention
is a bad trade, and those 9 faults are still in the published article.

So there is now **one** retry. When the guards fail, code sends the edit back naming exactly what
broke, using `prompts/coherence-retry.md`:

> Your edit of this article was REJECTED by code and has not been used. [...]
> If the fault is an INVENTED NUMBER: that figure appears nowhere in the original article. You have
> no sources and cannot look anything up, so a number you did not read is one you made up. Remove it,
> or rewrite that sentence using only figures the article already contains.

The reply goes through **the same guards**. Clean, it applies. Still failing, the original publishes,
exactly as before. One retry only, never a loop.

**Why a retry and not a partial revert.** Reverting only the section containing the bad number was
designed and rejected. This step's best work is cross-section: one scale corrected in ten places. If
you revert one of those ten, nine sections say 1-5 and one still says 0-2-4, and the article ends up
**more** inconsistent than if nothing had been applied. A retry has no partial state. Either a whole
clean article or the original, untouched.

**Cost:** one extra call, and only on a run that was about to be discarded anyway. On a clean run it
never fires.

## Who decides what

**The AI decides:** what goes on the list. Which of the four faults are in the article. How to fix
each one, across as many sections as it takes. Whether the article is safe to publish.

**The code decides:** how long to wait, what actually changed, which checks are strict, and whether
the edit is used at all.

One practical detail. This step sends the whole article twice and gets the whole article back, so
roughly 5,600 words in and 5,600 out. The normal 300-second limit is sized for one section, and it
was cutting this step off mid-thought. A run burned three attempts producing nothing, then quietly
fell back to a weaker model. The limit here is now **1,200 seconds**.

## What it found, on the four real articles

| Article | rules / scales / numbers found | fixes made | could not fix | verdict |
|---|---|---|---|---|
| hackathon | 121 / **30** / 60 | **9** | 0 | applied |
| strategic | 71 / 25 / 18 | 4 | 0 | applied |
| cost-per-hire | 88 / 24 / **207** | **13** | 3 | applied |
| Type D | 16 / 4 / 9 | 1 | 0 | applied |

**Nothing was blocked on any of these four.** The first block came later, on the cost-per-hire rerun
of 2026-08-12: the edit introduced the number 32,000, which was nowhere in the original, so the
whole edit was discarded and the original published. Nine fixes went with it, including cutting a
$180,000 figure that contradicted every band in the article. `applied: false`, `reason: guards
failed — keeping the original`.

### The actual fixes, so you can judge them yourself

**Hackathon, 9 fixes. A few of them:**
- Three judges scored an example 7, 8 and 6, in an article whose own scale only goes to 5. Changed to
  3, 4 and 5.
- The article called "three to six dimensions" the same range as "five to six". It is not.
- The article warned against automating the arithmetic, then told you to automate it in a spreadsheet.
- The intro promised the top and bottom bands for AI ownership. They were missing. It built them from
  material already in the article.

**Cost-per-hire, 13 fixes**, on an article where the list found **207 separate numbers:**
- A bare "$5,475 national average" with no edition or method attached. It added them.
- Three dollar examples that were not labelled as what they actually were.
- Named 15-25% as the article's working range, matching the band its own heading used.

That first one is the shape of this whole step. Read that section on its own and the figure looks
fine. It is only wrong next to the rest of the article.

**Strategic, 4 fixes, three of them broken promises.** The intro said twenty fully worked
question-and-answer pairs. The article had fewer. One fix inserted a question that was **missing
entirely**: *"Tell me about a time you disagreed…"*. A missing question, in an article about
interview questions. Caught only because the intro's promise was written down on the list.

> **This fault was removed on 2026-08-11.** "A promise not kept" was the fifth fault and it is gone,
> along with the promises list in the inventory. Coherence now hunts four faults, not five.
>
> That is worth knowing when you read the table above. Three of strategic's four fixes were broken
> promises, so the same run today would find one. The missing interview question would ship.
>
> Nothing else replaces it. No step checks whether the intro delivers what it promised.

**Type D, 1 fix.** Small article, 16 rules and 4 scales, one finding. That is the system behaving
sensibly, not failing.

### What that table tells you

**The bigger the list, the more it finds.** 30 scale mentions produced 9 fixes. 4 produced 1. Handing
the AI a list is what lets it see, which is exactly what the rebuild was for.

**But the article gets longer, sometimes a lot longer.**

| Article | words before | after | change |
|---|---|---|---|
| hackathon | 5,469 | 5,709 | +4% |
| **strategic** | **8,068** | **10,341** | **+28%** |
| cost-per-hire | 4,868 | 5,569 | +14% |
| Type D | 3,234 | 3,294 | +2% |

The limit was 10% when these four ran, and is **5%** today ([coherence.py](scripts/coherence.py),
`WORD_TOLERANCE`). Two of four went past the looser number, one by nearly three times, and all four
would go past today's. Length only ever gets flagged, never blocked, so a 28% increase publishes.

One honest note: strategic's saved report has no length flag on it at all, because that run is from
2026-08-06 and predates the check. Today's code would flag it. It still would not stop it.

## The two prompts, in full

### coherence-inventory.md

```
Go through this article and write down three things. Do not judge any of them. Do not look
for problems. You are making a list, not a report.

THE ARTICLE:
{{ARTICLE}}

1. RULES AND WARNINGS — every place it tells the reader to do something, not do something,
   or says something carries a risk. Copy the sentence. Note its section.

2. SCALES AND RANGES — every scoring scale, rating range or prescribed count it uses.
   "1 to 5", "0-2-4", "poor/okay/great", "pick 5-6 skills", "3-6 dimensions".
   Copy each exactly, note its section, and RECORD EVERY OCCURRENCE — even the same scale
   twice. How many times each appears is the whole point of this list.

3. QUANTITIES — every stated size, with what it measures and when.
   "cost per hire = $1,300, nonexecutive median, 2026".

   A QUANTITY IS NOT ONLY MONEY AND PERCENTAGES. Record all of these, and write the amount
   in the article's own words:
     · money and percentages — "$1,300", "60-70%"
     · MULTIPLES AND RATIOS — "three to four times a position's salary", "twice as many",
       "half of all hires", "1 in 5"
     · TIME AND EFFORT — "45 hours of calendar time", "38 days to fill", "the first 30 days"
     · COUNTS OF REAL THINGS — "291 applications per hire", "15 open roles", "7 judges"
     · anything expressed in words instead of digits — "a third", "double", "nearly half"

   A figure written as a multiple of something else is the one most often missed, and it is
   the one that most often disagrees with a worked example elsewhere in the article. Record it.

   In "measures", say WHAT THE NUMBER IS OF, in plain words, so two entries about the same
   thing read the same way: "total hiring cost as a multiple of salary", not "the 3-4x rule".
   Two figures for one thing are only findable later if both describe that thing the same way.

   Skip step numbers ("step 3"), position-in-a-list counts, and years used only as dates.

Record duplicates. Record things that look like they disagree. Sorting that out is someone
else's job — you are only recording what is there.

Return ONLY this JSON:
{"rules": [{"text": "...", "section": "..."}],
 "scales": [{"scale": "...", "used_for": "...", "section": "..."}],
 "quantities": [{"amount": "...", "measures": "...", "when": "...", "section": "..."}]}
```

### coherence-edit.md

```
You are the last editor before this article publishes, and the FIRST person to read it whole.

Every section was written by a different writer, all at once, none able to see the others.
So the article has never been read end to end by anyone. That is why you exist: the faults
that live BETWEEN sections and are invisible inside any one of them.

THE COMPANY publishing this: {{BRAND}} — {{ABOUT}}

THE ARTICLE
- H1: {{H1}}
- What it was built to deliver: {{ANGLE}}
- What it argues, for whom: {{SPINE}}
- What it IS about: {{WORLD_ABOUT}}
- What it is NOT about: {{WORLD_NOT_ABOUT}}

WHO IT IS FOR:
{{PERSONA}}

════════════════════════════════════════════════════════════════════════
WHAT SOMEONE ALREADY WROTE DOWN FOR YOU

Another pass went through and listed every rule, scale and quantity in this article, with
where each one appears. Read it before the article. The faults are usually visible in the
list alone — the same scale under four different names, two rules that disagree, two
figures for the same thing.

{{INVENTORY}}

════════════════════════════════════════════════════════════════════════
THE ARTICLE IN FULL:

{{ARTICLE}}

════════════════════════════════════════════════════════════════════════
WHAT HAS ALREADY BEEN DECIDED, AND IS NOT YOURS TO UNDO

You are being handed real freedom. Use it on the faults below, not on work already done
deliberately by a step that knew more than you do:

- THE SUBJECT BOUNDARY. The "is / is not about" lines were written before any research was
  gathered. Material is missing because it belonged to a different subject. Do not miss it.
- WHAT EARNED A PLACE. Sub-topics were dropped on purpose, and every citable number was
  checked against the page it credits. A fact you find surprising is already verified.
- THE HEADINGS AND THE H1. Researched against real search data. Not yours.
- THE SOURCE TAGS. Every [c…] tag is how the published article cites that fact. Break one
  and the citation is lost.
- THE SEAMS. Someone already stitched the sections together. It reads continuously on purpose.

COMING AFTER YOU: a style clean-up, then internal and external links. So do NOT fix awkward
phrasing, strip AI-sounding words, or add links. Those are handled.

════════════════════════════════════════════════════════════════════════
FIX EXACTLY THESE FOUR THINGS

1. IT BREAKS ITS OWN RULE — says never do X, then explains how to do X, recommends it, or
   gives a worked example of it.

2. ADVICE ITS OWN WARNING COVERS — one section describes a risk, another recommends the
   exact behaviour that triggers it. Neither mentions the other, so both read fine alone.

3. ONE JOB, SEVERAL SCALES — the same thing scored on 1-5 in one place and 0-2-4 in another.
   Pick one and make the whole article use it. Prefer the one used most, or the one the
   headings use. This is the fix a section-by-section editor cannot make, and you can.

4. NUMBERS THAT DISAGREE — two figures for the same quantity that cannot both be true. Two
   figures measuring different scopes are fine, but only if the article SAYS they are
   different. If it does not, the reader cannot tell, and that is the fault.

THE RULE FOR THE HARD CASE: when a warning and a recommendation collide, THE WARNING WINS.
Cut or qualify the recommendation. Never soften the warning. Both make the clash disappear;
only one is honest.

════════════════════════════════════════════════════════════════════════
THREE THINGS YOU MAY NEVER DO

These are not preferences. Break any one and your entire version is discarded, unread, and
the original article publishes instead. Nobody sees your work.

1. NEVER TOUCH A HEADING OR THE H1. They were researched against real search data by a step
   that had information you do not have. Not one character.

2. NEVER DELETE A SECTION. You may cut a paragraph, a passage, or a whole argument inside a
   section. The section itself stays, keeps its heading, and must still say something.

3. NEVER INVENT A FACT. You have no sources. If a number, name, statistic or claim is not
   already somewhere in this article, it does not go in. Not even inside an example.

════════════════════════════════════════════════════════════════════════
TWO THINGS THAT ARE NOT BLOCKED, AND MATTER MORE BECAUSE OF THAT

Nothing stops you doing either of these. A human reads what you did afterwards, so get them
right rather than getting away with them.

- THE [c…] TAGS ARE THE CITATIONS. Each one is how the published article credits that fact
  to a real page. It looks like clutter; it is the opposite. Drop one and the claim goes out
  with no source and the reader has no idea. If you rewrite a sentence, the tag travels with
  the fact it belongs to. If you cut a claim, its tag goes with it — that is correct. What
  is never correct is keeping a claim and losing its tag.

- CHANGING A REAL FIGURE IS A FACT CHANGE. A rating band (0-2-4 becoming 1-5) is the repair
  and you should make it. A statistic, a price, a percentage, a date — changing one of those
  alters what the article claims about the world. If you must, DECLARE IT in
  "numbers_changed" with the reason. An undeclared statistic that moved is the single worst
  thing you can leave behind here.

════════════════════════════════════════════════════════════════════════
HOW TO WORK

YOUR WORD BUDGET. Do not hand back an article more than {{WORD_TOLERANCE}}% longer than the
one you were given. That is a ceiling, not an allowance to spend. A good pass lands within
2 or 3%. Coming back at 0% is a fine result.

EVERY REAL FIX IS ALREADY CHEAP. Changing a scale in ten places costs nothing, because you
are swapping numbers, not adding sentences. Cutting a passage that contradicts the article
gives words back. What costs words is explaining yourself: a clause added to smooth a fix,
a sentence of context nobody asked for, a re-statement of the thing you just corrected.

IF A FIX GENUINELY NEEDS ROOM, TAKE IT. A correction that matters is worth its words. Look
first at whether that section already holds a weak sentence you can cut, because those
words are free. If it does not, write what the fix needs. Never cut something that matters
in order to make space.

- DO THE WHOLE JOB, INSIDE THAT BUDGET. You are an editor, not a proofreader. Where a scale
  is wrong in ten places, change all ten; that is exactly what you are here for and it costs
  you almost nothing. Where a passage contradicts the article and cannot be rescued, cut it.
  A half-fix that leaves the reader with the same confusion is worse than no fix, because it
  looks handled.
- REACH ACROSS SECTIONS FREELY. That is the one thing you can do that nobody before you
  could. If fixing section 5 means adding a line to section 7 so the two agree, do it.
- DO NOT RESTYLE PROSE THAT HAS NO FAULT IN IT. Not because you would make it worse, but
  because that work is already done and a step after you handles it. Every word you spend
  there is a word you no longer have for a real fix.
- A clean article is a normal outcome. Returning it unchanged is a real answer.

════════════════════════════════════════════════════════════════════════
RETURN THE WHOLE ARTICLE, EDITED — every section, in order, whether you changed it or not.
Then list what you changed and why.

Return ONLY this JSON:
{"h1": "<unchanged>",
 "intro": "<the intro>",
 "sections": [{"heading": "<unchanged>", "prose": "<the section>"}],
 "faq": [{"question": "<unchanged>", "answer": "<the answer>"}],
 "close": "<the close>",
 "changes": [{"kind": "breaks-own-rule | own-warning | several-scales | numbers-disagree",
              "section": "<where>",
              "what_you_did": "<one line>",
              "why": "<one line: what it collided with, and where>"}],
 "numbers_changed": [{"was": "<the figure as written>", "now": "<what it became>",
                      "why": "<one line — say if this is a rating band, not a real-world figure>"}],
 "could_not_fix": [{"what": "<the fault>", "where": "<section>", "why_not": "<one line>"}],
 "verdict": "<one line: is this article honest and safe to publish now?>"}
```

## What is wrong with coherence

**1. It makes the article longer and only a flag stops it.** Plus 28% on one article, plus 14% on
another. The prompt now carries a word budget, 5%, and the flag was lowered from 10% to match it,
but it is still only a flag. A version that threw the edit away for going over was written and
deliberately left out: an editor afraid of the ceiling skips the fix that needed room. The prompt tells it to "do the whole job" and hands it
the whole article to return, so getting longer is the natural way this design goes wrong. Nobody has
decided yet whether 2,273 extra words on an already-long article is a fair price for four fixes.

**2. It never sees how long the article was supposed to be.** The architect gives every section a
word target. Write body ignores it. Blend now at least shows it, next to what was actually written.
The wrapper does not see it. Coherence does not see it. Five steps touch the article and only one of
them is even shown the length it was planned to be.

**3. Its safety checks fired for the first time on the fifth run.** Four articles, zero blocks, then
the cost-per-hire rerun of 2026-08-12 tripped the invented-number check on 32,000 and the whole edit
was thrown away. So the guards do work. What is now untested is the other direction: whether
discarding nine good fixes over one bad number is the trade we want, since the check is all or
nothing and nobody has looked at whether the 32,000 was load-bearing.

**4. It is the most expensive step in the writer.** The whole article goes in and the whole article
comes back, twice, with a 20-minute limit. Every other step works on one section at a time.

---
---

# Part 9 — What the reviewer asked for, and where it lives

### Belongs to these three steps

| What | Which step | Status |
|---|---|---|
| **FAQ answers max 40 words** | wrapper | Now the rule, counted per answer and shown. Was 47 to 146 words with nothing counting |
| **The intro states the intent, no throat-clearing** | wrapper | Strong. A banned-phrase list with a worked example, kept as it was |
| **Problem, agitate, solution intro** | wrapper | **Now the intro's whole structure.** AIDA and FAB were offered too and not used: both end in selling, and the body is product-free |
| **An FAQ must not repeat the article** | wrapper | The reviewer's own line. Was already the rule, and the collision it caused with "answer only from the body" is what forced the rebuild |
| **No two FAQ questions the same** | wrapper | Was buried as the third bullet in a list and invisible. Now the loudest rule in that block |
| **Don't force five questions** | wrapper | Five is a ceiling. "Three real questions beat five padded" |
| **Don't repeat yourself across sections** | blend | Never fired under the old design. Now fault 2 of 11, with "if you find none, look again" |
| **No fluff, get to the point** | blend | Now fault 7, plus fault 6: the first paragraph must deliver the section's job |
| **Answer the H2** | blend | Now fault 6. Blend gets the section jobs for the first time |
| **Simple English, 12th grade** | blend | Now fault 11, smallest change that works. Nothing measures it |
| **Sentences max 25 words, paragraphs max 4** | blend, for the body | Counted in code, handed over as an exact list. The leniency rule stops it wrecking sentences to clear that list |
| **The article keeps its promise** | nowhere, as of 2026-08-11 | Was coherence's fifth fault and its strongest result. Removed on request. Nothing checks this now |
| **Internally consistent scoring** | coherence | Working. The strongest thing in these three steps |
| **Sentences max 25 words** | wrapper, for the intro/FAQ/close | Now in the prompt. The seven drifted rules it copied from write body were deleted |
| **Paragraphs max 4 sentences** | wrapper | Now in the prompt |
| **Explain a term in brackets** | wrapper | Now brackets, once, with the twelfth-grader test and the never-explain list |
| **Keywords in the body prose** | blend | Fault 5. Working. The count is now measured in code, because its own report did not add up |

### Does NOT belong here

| What | Where it lives |
|---|---|
| AI writing tells, "delve", "seamless" | `slop_pass.py`, step 5 |
| External links, capped | `links_pass.py`, step 6 |
| Internal links | `links_pass.py`, step 6 |
| Character and spacing fixes | `clean.py`, step 7, pure code |
| Section word targets | Set by the architect. Blend now shows them beside what was written, but still nothing enforces one |
| Sentence rhythm, nouns-as-verbs, qualifier stacks | Write body's rules. Deliberately NOT re-checked at blend (Devansh, 2026-08-11) |
| Which facts exist at all | The planner and write body |

---

# Part 10 — The one thing to understand before changing anything

**One shape works, and it is now used twice.**

Coherence made 27 real fixes across four articles, including a scale used inconsistently in ten
places, and a promise the intro made that the article never kept, back when it still looked for
those. It did not always work. Its first
design found **one** fault across all four, because it was asked to hunt and fix in a single pass.
The rebuild split those apart: a listing call with no judgement in it, then an editing call handed
that list. Do not touch its design.

Blend had the same failure and now has the same fix. Under the old design it made 22 edits across
four articles, 16 of them transitions, **zero repetitions cut**, and returned "none" for two entire
articles. Code now counts what a model counts badly and hands over an exact list, so blend judges
instead of hunting. That is the whole change, and one run is all the evidence there is for it.

The wrapper was rebuilt the same day, but for a different reason and with the opposite move. Blend
and coherence needed code to hand the model a list. The wrapper needed code to **stop taking things
away**: a version that deleted over-long FAQ answers and answers carrying outside figures was built
and removed within hours, because it killed all five answers on three of four articles. Its code now
measures and shows, and edits nothing except the H1 and invented tags.

**The rule that runs through all three: code counts, the model judges, and a human sees both.** Where
that balance tips either way, the step stops working. Coherence's first design asked the model to
count and it found one fault in four articles. The wrapper's deleting version let code judge and it
emptied the FAQ.

---

# Part 11 — Change hooks

Neutral list. Nothing here is decided.

## Done on 2026-08-11

**Blend**, rebuilt in coherence's shape
- ~~A code check on whether the text actually changed~~ → the "no edit made" warning
- ~~Count the woven keywords in code~~ → `keywords_measured`, counted in the finished text
- ~~Give blend each section's `job`~~ → the `{{JOBS}}` block
- ~~A tag-loss threshold~~ → blocks at 25%, copied from coherence
- ~~Long sentences and fat paragraphs counted for it~~ → the `{{FLAGS}}` block

**The wrapper**, rebuilt on the reviewer's notes
- ~~Bring `wrapper.md` in line with the rewritten `write-body.md`~~ → the drifted copy was deleted,
  six step-specific rules replace it, including the 25-word and 4-sentence limits
- ~~Cap FAQ answers in words and count them in code~~ → 40 words, counted per answer, shown
- ~~Give the wrapper the persona~~ → it never had one
- ~~Cap `features.md`~~ → 8 KB, was 69 KB uncapped
- ~~An intro framework~~ → PAS. AIDA and FAB offered and not used

**Rejected, on purpose**
- Giving the wrapper the unused card pool. There is no way to know the leftovers are the good ones
- Re-checking sentence rhythm, nouns-as-verbs and qualifier stacks at blend. They stay write body's
  rules and are not audited afterwards
- Code deleting FAQ answers for length or for carrying a figure the article lacks. Built and removed
  the same day: it killed all five answers on three of four articles

## Still open

1. **The FAQ is the only unsourced part of a published article.** Everything else traces to a card
   with a real link. A search behind each answer was designed and parked, not forgotten. Roughly
   1.5 cents an article.
2. **The searched-question pool is nearly unusable** once you omit what the article already answers.
   Six questions became about zero; one article had none researched at all. Research-phase fix.
3. ~~**The review page still shows blend's own `keywords_used`**~~ → done. `eval_pages.py` reads
   `keywords_measured`. Worth knowing why it mattered: on the first run blend still self-reported 8
   keywords used and 2 skipped out of a set of **5**. The report is as arithmetically impossible as
   it was under the old design. Measuring it in code is what makes that harmless.
4. **Nothing enforces a section's `word_target`.** Blend now displays it beside what was written,
   which is one step short of acting on it.
5. **Should length ever block?** Coherence let a 28% growth publish on a warning. Blend's length
   statement reserves 600 words for the wrapper; coherence reserves nothing.
6. **Coherence blocked for the first time on 2026-08-12**, on an invented 32,000, discarding nine
   fixes. The guards are no longer untested. Open now: is all-or-nothing the right response to one
   bad number?
7. **The architect's word budget already overshoots.** On cost-per-hire it allocated 3,500 words of
   sections against a 3,000-4,000 band, and the wrapper adds another 600 on top. The article is
   planned over before a word is written.
8. **The card supply is six times what the word targets can hold.** A 210-word section was handed
   29 cards; 263 cards went out against targets holding about 44 paragraphs.
