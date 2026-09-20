# The machine, two points per step

A memory sheet for explaining the whole pipeline out loud. Four layers. Layers 00, 01 and 02 run **once per company**. Layers 03 and 04 run **once per article**.

The one line: **learn the site → learn the brand → find ideas worth building → research one idea → write it.**

---

## LAYER 00 — FOUNDATION (the site catalogue)

*One command. Answers "what pages does this company already have, and what do they rank for?"*

**1. Enumerate from the CMS**
- Asks WordPress what content types exist, then lists every page in each.
- Checks its own count against the number WordPress reports, so nothing is silently missed.

**2. Enumerate from sitemaps**
- Reads robots.txt, opens every sitemap it declares, follows each link.
- A sitemap that answers with a webpage instead of a sitemap is treated as blocked, not empty.

**3. Enumerate from the web archive**
- Asks the public archive which URLs this domain ever had.
- Checks each one against the live site, because "it existed once" is not "it exists now".

**4. Enumerate by crawling**
- Walks the site from the homepage, following links.
- Last resort only. It runs when the first three sources come back thin.

**5. Reconcile**
- Merges all four lists into one, keeping a record of which source found each URL.
- Collapses redirects and duplicate versions of a page, and drops fake 404s.

**6. Extract the text**
- Downloads every page once and pulls out the clean body text with the headings kept.
- Tries four different extractors and keeps the longest clean result.

**7. Traffic**
- One bulk paid call returns every keyword the domain ranks for, with position and URL.
- Fills traffic and intent per page, and writes the top-pages sheet.

**8. Gates**
- Checks coverage per page type against what the sources themselves claim.
- Fails the run loudly rather than shipping a short catalogue that looks complete.

**Output:** `content-database.csv` (every page plus its full text), `top-pages.csv`, `catalogue-report.md`.

---

## LAYER 01 — BRAND CONTEXT (ten builders, run once)

*Answers "how does this company write, and what does it sell?"*

**0. Brand facts**
- Drafts the company's real numbers and customer stories from its own website.
- A human confirms every row. Opinions are interview only, the machine never invents one.

**1. Brand voice**
- Reads about 30 cornerstone pages and writes down how the brand actually sounds.
- Runs a quality loop against its own evidence before it writes the final file.

**2. Style guide**
- Reads the top blogs and records the mechanics: grammar, punctuation, formatting, meta rules.
- Flags the lines that need marketing to confirm rather than guessing.

**3. Features**
- Reads every page to write what the product does, its benefits and its differentiators.
- Stays on voice by reading the brand-voice file first.

**4. Writing examples**
- Picks the five best-performing articles and pastes them in full.
- Annotates each one against the voice standard, so the writer has worked examples, not rules.

**5. Persona**
- Defines three or four real reader types the content is written to.
- Adds the rule for picking one persona per article, so nothing is written at "HR" in general.

**6. Voices**
- Captures the real named bylines the company publishes under, for author credibility.
- Filled by the team only. The machine never drafts a fake author.

**7. Writer brief**
- Boils the whole brand pack down to the one file the writer actually reads.
- 26,605 words compressed to 1,660, keeping only what changes a sentence.

**8. Brand cards**
- Turns the company's own research and customer results into small placeable cards.
- Results are parsed by code, research rows are judged by AI, because picking which rows matter is judgment.

**9. Field sources**
- Finds where this company's audience actually argues in public, mostly subreddits.
- Checks each community is real and active before it goes on the approved list.

---

## LAYER 02 — ASSET ENGINE (find ideas worth building)

*Answers "what should we build that other sites would choose to link to?"*

**Method 1: Competitor study**
- Finds which competitor pages earned the most backlinks and copies the format, not the topic.
- Human signs off the competitor list up front, and a semantic dedup merges repeated ideas at the end.

**Method 2: Model other niches**
- Imports link-bait formats proven in other industries that nobody in our niche has built.
- Adapts each one on brand, and flags anything that genuinely needs a tool built.

**Method 3: Study trends**
- Scrapes the approved subreddits and reads each post as a content card.
- Consolidates recurring phrases into tensions, then shapes each tension into a timely idea.

**Method 4: Merge**
- Stacks all three pools into one shared column set.
- Deduplicates across methods with embeddings plus an AI adjudicator, so an idea found twice becomes one stronger row.

**Method 5: Reuse check**
- Embeds every page we already own, then retrieves the seven closest pages for each idea.
- An AI reads those pages and returns a verdict: already have it, improve existing, build from parts, or brand new.

**Output:** `clubbed-ideas.csv`, the queue of ideas, plus a shareable web viewer for review.

---

## LAYER 03 — CONTENT MACHINE (research one topic)

*One command per topic. Turns one chosen idea into a write-ready bundle.*

### Step 0: Pick the topic
- Takes the next unfinished row in the queue, otherwise pulls the next eligible idea from the sheet.
- Skips ideas that need a tool built, and leaves "improve existing" for last.

### Step -1: The world statement
- Writes down what this article is about and what it is not about, before any keyword is bought.
- Every later step reads it, so a keyword whose searchers live in a different field is caught early.

### Step 1: DataForSEO brief (eight sub-steps)

**s0 Seeds**
- Pulls the anchors, seed keywords and competitor URLs straight from the idea row.
- No free brainstorming. Everything traces back to a real column.

**s1 Tight net**
- One keyword-suggestion call per seed, close to the subject.
- The old wide net was dropped because it only returned off-topic noise.

**s1b Ranked net**
- Pulls every keyword the winning competitor pages already rank for.
- This is where real breadth comes from, since those pages are proven.

**s2 Filter**
- Free filter on search volume and keyword difficulty. No API cost.
- Cuts the pool down to a shortlist worth paying for.

**s3 Metrics and scoring**
- Buys volume, difficulty and intent for the shortlist in one call.
- A panel of AI scorers plus a judge picks the primary keyword and writes the keywords section.

**s4 SERP**
- Reads the live page one for the primary keyword, and captures Google's AI Overview.
- Saves both the raw response and a clean structured extract.

**s4b Snapshot**
- Turns that raw SERP into a readable snapshot: who ranks, what format wins, where the gaps are.
- Picks the three pages worth actually opening.

**s5 Pages and winners**
- Fetches those pages for free and pulls their headings and word counts.
- Writes "what the winners cover", which becomes the checklist we have to beat.

**s7 Assemble**
- Lifts every section into the brief word for word, no re-summarising.
- The AI writes only two things: the verdict, and the build spec (word band, sources to cite, the close).

### Step 2a: The spine
- States what this specific article argues, built from the world statement plus the winners study.
- Extracts the competitor read: common headings, gaps we can own.

### Step 2: STORM (the evidence engine)
- Picks a research team of personas, who ask questions, search and read full articles.
- Produces a densely cited dossier. It never writes final copy, it manufactures the evidence.

### Step 3: Gap check
- Builds a coverage checklist in pure code: gaps to own, winner headings, the AI Overview skeleton.
- Judges the dossier item by item, turns real misses into up to three queries, and re-runs STORM on those only.

### Step 4: Build the blueprint (nine sub-steps)
- Harvests the dossier and our own pages into cards, one fact each with a verbatim quote and a source.
- Picks the persona, drops off-spine cards, clusters the rest, names and splits them into H2s and H3s, attaches evidence, checks for missed high-volume keywords, orders the sections, and renders the blueprint.

### Step 5: The bundle
- Copies the blueprint in and writes a cover sheet that points at the shared brand files.
- Picks the author byline. The persona was already decided upstream and is reused, never re-picked.

### Step 6: Log and enqueue
- Marks the topic done and queues its supporting articles right behind it.
- Runs the cannibalisation flag: if we already rank page one for that keyword, it says so rather than blocking.

---

## LAYER 04 — WRITE PHASE (turn the bundle into an article)

Three runners in order: **planner → architect → writer.**

### THE PLANNER (vets the raw material)

**1. Gather**
- Pulls the blueprint, the brief, the SERP proof files and the queue row into one file.
- Three AI calls only: lift the winners lists, read the word band, and drop off-angle questions.

**2. Select**
- Tags every sub-heading against what it serves: our angle, a gap, a table stake, a real search question.
- A section survives on arithmetic, not opinion, and anything cut is written to an audit file.

**3. Verify sources**
- Code finds every claim carrying a number, and AI picks which ones genuinely need proof.
- It opens the cited page and judges it. If the source is wrong, it hunts for a real one, and cuts the fact only if the hunt fails.

**4. Freeze**
- Checks the shape only: no empty sections, a primary keyword, a word band.
- Any hard fault stops the run. Once it passes, the plan is locked and never changes.

**5. Plan view**
- Renders the frozen plan as plain English for a human to read.
- A view, not a decision. It rebuilds every time.

### THE ARCHITECT (designs the article)

**1. Shape**
- Every approved sub-heading becomes a numbered box, and the AI designs the real structure by rearranging boxes.
- It answers with headlines and box numbers only, so it can restructure but cannot invent facts.

**2. Enrich**
- Where the structure says "I need research here", it plans queries, searches, and reads up to fifteen pages.
- New sourced cards are created and attached to the exact place the architect named.

**3. Brand cards**
- Places the company's own research and customer results, but only where they earn the spot.
- Caps are enforced in code, not just requested in the prompt, so the article cannot turn into a pitch.

**4. Allocate words**
- The AI decides each section's share by importance, then a second pass caps it by how much evidence exists.
- Code does the arithmetic so the shares total 100 and the sections add up to the target length.

**5. Section keywords**
- First a free gate: would a person actually type this section's subject into Google? Most sections should be no.
- Only for the ones that pass does it buy keyword data, and returning "none" is an acceptable answer.

**6. Headings**
- Writes the final heading for every section, one call each, with that section's evidence in view. Then the H1.
- A second pass reads all the headings as a set and fixes numbering, naming and capitalisation drift.

### THE WRITER (writes and polishes)

**1. Body**
- One AI call per section, in parallel. Each sees only its own cards, so it cannot invent a fact.
- Each also sees the plan of every other section, so twelve separate calls still pull in one direction.

**2. Blend (the editor)**
- Code counts first: every over-long sentence, every bloated paragraph, the total against the word band.
- The AI is handed that list and edits, then code diffs what actually changed. Any guard failure and the original ships.

**3. Wrapper**
- Writes the intro (problem, agitate, solution), the key takeaways, up to five FAQs and the closing CTA.
- The body stays product free. The product is allowed in the close and nowhere else.

**4. Coherence**
- The first and only step that reads the whole article at once, because every section was written blind to the others.
- Step one lists every rule, scale and number and where each appears. Step two fixes the clashes, for example four different scoring scales in one article.

**5. Slop pass**
- Strips the AI writing tells: em dashes, filler words, the same sentence rhythm repeated.
- Code checks every number and every source tag survived. A block that fails keeps its original text.

**6. Links**
- Three pools: internal links over existing words, a "read more" pointer matched against our own site, and up to ten external sources.
- Competitors are removed by code, and an integrity check confirms nothing else in the text moved.

**7. Clean**
- Pure code, no AI, no cost. Removes invisible characters, fixes spacing, normalises dashes.
- Running it twice changes nothing, and it never rewrites a word.

**8. Assemble**
- Builds the final draft, the sources list, and a review page where hovering a stat shows its source.
- Keyword coverage is counted by code from the finished text, never self-reported by the AI.

**9. Readable**
- Rewrites the finished article so a person wants to read it, since writing sections in isolation makes prose stiff.
- Written beside the original, never over it, so the two can be compared side by side.

### FIELD VOICES (a side runner, per article)
- Plans searches from the article itself, searches titles only across the approved communities, then decides what is worth opening.
- Downloads comment threads only for the shortlist, filters everything against the article, and writes one file of what practitioners actually say.

---

## The three ideas to repeat in the meeting

1. **Code counts, AI judges.** If you can count it, a script does it. If two sensible people could disagree, the AI does it.
2. **Nothing is invented.** Every fact carries a card id, a verbatim quote and a live source URL, and the source is verified by opening the page.
3. **Every step writes a named file.** So a crash resumes where it stopped, and any output can be traced back to the step that made it.
