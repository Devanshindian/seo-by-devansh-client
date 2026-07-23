---
type: workflow-recipe
stage: content-machine (Stage 0 — brand context)
reusable: any company
reads:
  - projects/[company]/00-foundation/output/top-pages.csv   # THE POOL — every top article by Traffic, with Top Keyword (primary keyword)
  - projects/[company]/01-brand-context/_pages/*.md              # article bodies for the saved ones (Step 2); web-fetch the rest
  - projects/[company]/01-brand-context/brand-voice.md      # the voice standard (fed to the sub-agent to score + annotate)
produces:
  - projects/[company]/01-brand-context/writing-examples.md # 5 exemplar articles, pasted in full + annotated
last_updated: 2026-07-03
---

# Writing Examples — build workflow

> **Where this lives:** this recipe lives at `Backlink gets Automated/workflows/03-content-machine/`. It
> reads the saved pages, the Semrush CSV, and `brand-voice.md` from
> `Backlink gets Automated/projects/[company]/…`, and writes `writing-examples.md` to that company's
> `projects/[company]/03-content-machine/` folder.

---

## What this does

Pick **5 of the company's best real, published articles** and assemble them — each **pasted in full** and
**annotated with why it's exemplary** — into `writing-examples.md`. This is the "show, don't tell" companion
to `brand-voice.md`: brand-voice states the *rules*, writing-examples proves them with *real articles the
writer can imitate*. Same shape and depth as the Castos reference (Appendix B). Stage 0 of the content machine.

---

## The one rule that governs everything

**Every example is a REAL, published article that genuinely embodies `brand-voice.md`** — pasted **in full and
verbatim**, with a **"What Makes It Great"** grounded in **named brand-voice pillars/rules**, never generic praise.

- **Voice fit is judged in one place only:** the Step-2 sub-agent scores each article **/10 against
  `brand-voice.md`** (nothing else). An off-voice article gets **no** "What Makes It Great" and is dropped.
- **The Castos example (Appendix B) is a DEPTH/COMPLETENESS bar and REFERENCE ONLY** — never copy its articles,
  its topics, or its annotations. Copying Castos content is an automatic fail (see Step 3).

---

## What you produce (named output of each step)

| Step | Produces |
|------|----------|
| 1. Classify & select ≥7 articles | **the classification table** (Working title · URL · Format · Traffic · Primary keyword) + the **≥7 selected** |
| 2. Score, annotate & assemble (one sub-agent per article) | **`writing-examples.md` (draft)** — the top-5 on-voice examples, each = metadata + What Makes It Great + full verbatim content |
| 3. Quality gate vs the Castos bar | **pass/fail + redo instructions** (loops back to 1/2) |

---

## Inputs

- **`00-foundation/output/top-pages.csv`** — **the selection pool**: every top page ranked by **`Traffic`**, each
  with its **primary keyword** (the **`Top Keyword`** column) and **`Primary Intent`**. Source of truth for the
  pool, traffic, and primary keyword — **never guess the primary keyword from the title.**
- **`01-brand-context/_pages/*.md`** — the already-saved article bodies. Used in Step 2 for the **verbatim paste** when
  a selected article is already saved; otherwise **web-fetch the live URL** for its body.
- **`brand-voice.md`** — the voice standard, **fed into the Step-2 sub-agent** so the two files stay aligned and
  talk to each other.
- **Appendix A** (in this file) — the raw schema (blank template to fill).
- **Appendix B** (in this file) — the Castos structure + one real annotation block (depth bar). Full 89 KB
  reference lives at `seomachine/examples/castos/writing-examples.md`.

---

## The steps (in order)

### Step 1 — Classify the articles & select ≥7 (traffic + format diversity)
**What it does:** builds a format-classification table over the saved articles and picks the shortlist to score.

**Process:**
1. Open `top-pages.csv` — this is the pool (every top page, ranked by **`Traffic`**). Read **only the
   `URL` and `Top Keyword` columns** — **do not fetch or read any body** at this step.
2. **Filter to editorial articles.** Keep blog/article URLs; drop non-article pages by their slug — homepage,
   `/pricing/`, `/test-library/…`, `/hr-glossary/…`, `/tech-glossary/…`, `/integrations/…`,
   `/job-description-templates/…`, calculators/tools — they aren't the format the writer imitates.
3. **Infer each article's format from its URL alone** (see the signal table below). For **Traffic** and the
   **primary keyword**, copy the cell values **exactly as they appear in `top-pages.csv`** — the
   **`Traffic`** column and the **`Top Keyword`** column, respectively. Take them as-is: never recompute
   traffic, and never infer the keyword from the slug.
4. Build the **classification table** — one row per candidate: `Working title (from slug) · URL · Format ·
   Traffic · Primary keyword`.
5. **Select at least 7**: prioritise high **Traffic** while covering **format diversity** across these shapes —
   **definitional/pillar** ("What is X") · **listicle** ("Top N", "X ways") · **step-by-step how-to**
   ("How to X") · **comparison** ("X vs Y" / "alternatives") · **thought-leadership** — **or any other genuine
   format the site uses** (this list is not exhaustive; label it plainly and count it). Span **≥3 distinct formats**.

**Output:** the classification table + the **≥7 selected** (each carrying its URL + Traffic + Primary keyword forward).

**Format is inferred from the URL/title, e.g. (no body read):**

| Signal in the URL/title | Format |
|-------------------------|--------|
| `what-are-…`, `…-definition`, `types-of-…` | Definitional / pillar |
| `top-15-…`, `top-8-…`, `…-questions` | Listicle |
| `how-to-…`, `…-process`, `…-in-5-steps` | Step-by-step how-to |
| `…-vs-…`, `…-alternatives` | Comparison |
| broad opinion/strategy topic (`the-4-pillars-of-…`) | Thought-leadership |
| anything else the slug clearly signals | Other — label it plainly (e.g. case study, template, guide) |

**Example classification rows (illustrative — real Traffic/keyword come from the Semrush CSV):**

| Title | URL | Format | Traffic | Primary keyword |
|-------|-----|--------|---------|-----------------|
| Top 15 Vervoe Alternatives… | /vervoe-alternatives/ | Listicle / comparison | 0 | vervoe alternatives |
| What are pink collar jobs… | /pink-collar-jobs/ | Definitional / pillar | 185 | pink collar jobs |
| How to perform a talent review… | /talent-review/ | Step-by-step how-to | 25 | talent review |
| 60 inventory planner interview questions | /inventory-planner-interview-questions…/ | Listicle | 158 | inventory planner interview questions |

**Gotchas:**
- **Infer format from the URL only** — no fetching, no body-reading, at this step.
- **Primary keyword comes from the Semrush `Top Keyword` column**, never the title/slug.
- **Pick ≥7, not 5** — Step 2 will drop off-voice ones, and we still need 5.
- **No voice pre-screening here** — brand-voice was built from these same top pages, so Step 1 is purely
  traffic + format. Voice fit is scored later, in one place (Step 2).

---

### Step 2 — Score, annotate & assemble each (one sub-agent per selected article)
**What it does:** scores each article against `brand-voice.md`, annotates the on-voice ones, drops the rest,
and keeps the top 5 — using a fresh sub-agent per article so the main context never bloats.

**Process:**
1. For **each** of the ≥7, spawn **one sub-agent** with the prompt below. Fill **`<URL>`** and
   **`<PRIMARY_KEYWORD>`** straight from the Step-1 table. Resolve **`<FILE>`** by matching the article's URL to
   a saved page in `01-brand-context/_pages/` — if a match exists, pass that filename; if not, leave `<FILE>` empty and
   the sub-agent will **web-fetch `<URL>`** instead. It reads the article's full text **+** `brand-voice.md` and
   returns a **Voice score /10**, a **verdict**, and — **only if on-voice** — the **What Makes It Great**, plus
   the word count.
2. **Drop** any article the sub-agent marks off-voice (it will have no "What Makes It Great").
3. **If more than 5 remain on-voice, keep the top 5 by Voice score.** If **fewer than 5** remain, go back to
   Step 1 and pull more candidates — **and expect this to take more than one round.** In practice a pure
   top-traffic batch can mostly fail the voice gate (older, generic content often doesn't meet the brand's own
   standard). When you pull more, **target the genres that actually score on-voice** for this company (e.g. for
   Testlify: "how a big company hires at scale" case studies and competitor comparisons). Keep pulling + scoring
   batches until **5 on-voice articles** survive. *(See "A real run" below for how this played out.)*
4. The **assembler** writes each kept example into the schema (Appendix A), pulling each part from its own source:
   - **Metadata:** `URL` + `Primary keyword` from the **Semrush table**; `Title` + `Word Count` from the **sub-agent**.
   - **What Makes It Great:** from the **sub-agent** (its on-voice annotation).
   - **Full Content:** pasted **VERBATIM** — from the saved `01-brand-context/_pages/<FILE>` if it exists, otherwise
     from a **web-fetch of the live `<URL>`**. *(This "saved file or web-fetch" choice applies to the Full
     Content only.)*

**The exact sub-agent prompt (send one per selected article):**
```
Score and annotate ONE published article for the writing-examples file — judged ONLY against the attached brand voice.

Read the article's full text — from  Backlink gets Automated/projects/[company]/01-brand-context/_pages/<FILE>  if that
file exists; otherwise web-fetch the live page at <URL>.
Read the brand voice standard — this is the ONLY yardstick; do NOT use your own taste or "good writing" in general:
  Backlink gets Automated/projects/[company]/01-brand-context/brand-voice.md

Context (given — do not re-derive): URL <URL> · primary keyword <PRIMARY_KEYWORD> (from Semrush — use as given).

Return ONLY these fields, in this exact order:
1. Voice score: X/10 — how closely this article matches brand-voice.md (its pillars, tone, style, formatting).
   HARD STOP: score ONLY against brand-voice.md — not against generic "good writing." Name the two or three
   pillars it hits or misses to justify the number.
2. Voice verdict: on-voice / off-voice, plus one line why.
3. What Makes It Great: ONLY IF on-voice — 2–3 reasons, EACH naming a specific brand-voice pillar/rule the
   article demonstrates (e.g. "Confident, Backed by Proof — opens on the 55% time-to-hire stat, not an
   adjective"). Ground every reason in the actual article; no generic praise. If off-voice, write
   "n/a — off-voice" and stop here.
4. Title: the article's exact H1 headline (verbatim).
5. Word Count: approximate body word count.
```

**Output — from the prompt (per article):** Voice score `/10` · verdict · What Makes It Great (on-voice only) ·
Title (exact H1) · Word Count.
**Output — from the whole step:** `writing-examples.md` (draft) = the **top-5 kept examples**, each a complete
block of *metadata (URL · Title · Primary keyword · Word Count) + What Makes It Great + the
full article pasted verbatim (from `Backlink gets Automated/projects/[company]/01-brand-context/_pages/<FILE>` if that
file exists, otherwise web-fetched from the live `<URL>`)*.

**Gotchas:**
- **Primary keyword is passed in from the table** — the sub-agent never guesses it.
- **Full content is pasted verbatim** from the saved page file — never paraphrase, trim, or re-fetch it.
- **Off-voice → no annotation, dropped.** A "What Makes It Great" only exists for on-voice articles.
- **Every "What Makes It Great" reason must name a brand-voice pillar** — if it doesn't cite one, it's vibe; cut it.

**What one assembled example looks like (illustrative — real values come from the run):**

```markdown
## Example 1: What Are Pink Collar Jobs? A Definitive Guide + Examples

**URL**: https://testlify.com/pink-collar-jobs/
**Primary Keyword**: pink collar jobs
**Word Count**: ~2,000 words

**What Makes It Great**:
- **The Helpful Hiring Expert** — opens on the reader's real question and teaches the concept step by step ("But why is this trend emerging now? … This blog explores all the essential insights"), then hands recruiters a usable takeaway rather than lecturing.
- **Skills-First, Not Resume-First** — steers hiring toward structured, skills-based interviews over instinct: "recruiters focus on the skills and qualifications of the candidates rather than relying on their gut feeling."
- **Confident, Backed by Proof** — grounds claims in real figures (e.g. ~40% of women report workplace bias; 32% of candidates prefer employers that promote inclusion), not adjectives.

**Full Content**:
```
What are pink collar jobs?

A pink collar job typically refers to… [FULL ARTICLE PASTED VERBATIM — full intro, every
subheading, lists, stats, conclusion, CTA. Not a snippet.]
```
```

> Note: the **Voice score** and **verdict** are the sub-agent's working outputs (used to drop off-voice
> pieces and rank the top 5) — they do **not** appear in the final `writing-examples.md`.

---

### Step 3 — Quality gate vs the Castos bar (loop)
**What it does:** checks the draft is as **complete and deep** as the Castos reference — *without copying it.*

**Process — check four things:**
1. **Completeness:** exactly **5** examples, each with **all** fields (URL · Title · Primary Keyword · Word Count ·
   What Makes It Great · Full Content). No `[BRACKET]` placeholders.
2. **Depth:** each article's **full text is pasted verbatim** (not a snippet), and each annotation is **2–3
   specific, pillar-grounded reasons**.
3. **Diversity:** the set spans **≥3 distinct formats**.
4. **Voice:** every kept example scored **on-voice** against `brand-voice.md` (the score is recorded in the
   Step-2 output).

**Two HARD RULES (non-negotiable):**
- 🚫 **Castos is a depth/completeness bar ONLY.** If any article, topic, or annotation is borrowed from the
  Castos reference (Appendix B), it's an **automatic fail** — the examples must be the company's own real posts.
- 🔁 **Any off-voice example, snippet-only paste, missing format, or fewer than 5 examples fails** → return to
  Step 1 (pull more candidates) or Step 2 (re-score / re-paste). Repeat until all four checks pass.

**Output:** pass/fail per check + specific redo instructions. Only a full pass ships the document.

---

## Traceability map (every field ← a named source)

*If a field can't be traced to a source below, it isn't sourced and must be flagged, not invented.*

| Schema field | Source |
|--------------|--------|
| Title | sub-agent — the article's exact H1 (Step 1 uses a working title from the slug) |
| URL | `top-pages.csv` → `URL` |
| Primary Keyword | **`top-pages.csv` → `Top Keyword`** — passed to the sub-agent, never guessed |
| Traffic (selection only) | `top-pages.csv` → `Traffic` |
| Voice score `/10` + verdict | sub-agent, scored **only** against `brand-voice.md` |
| What Makes It Great | sub-agent (on-voice only), each reason grounded in a **named `brand-voice.md` pillar/rule** |
| Word Count | sub-agent (from the article body) |
| Full Content | `01-brand-context/_pages/<FILE>` if saved, else **web-fetch `<URL>`** — pasted **VERBATIM** |

---

## Rules shelf (what this recipe points to, not restates)

- **Voice standard:** `projects/[company]/01-brand-context/brand-voice.md` (fed to the sub-agent).
- **Traffic + primary keyword:** `projects/[company]/00-foundation/output/top-pages.csv`.
- **Raw schema to fill:** Appendix A (below) — mirror of `seomachine/context/writing-examples.md`.
- **Depth bar:** Appendix B (below) + the full reference at `seomachine/examples/castos/writing-examples.md`.

---

## Gotchas (top of mind)

1. **Format from the URL only** at selection — no fetching, no body-reading.
2. **Primary keyword from Semrush**, never the title.
3. **Score is judged only against brand-voice.md** — the two files must stay aligned.
4. **Off-voice → dropped, no annotation.** Start with ≥7 so 5 survive.
5. **Paste full articles verbatim** (from the saved page file, or a live web-fetch if not saved) — never a snippet.
6. **Castos is a ruler, never a source** — copying its articles/topics/annotations = auto-fail.

---

## Run artifacts — what gets saved under `_work/`

As you run this, save the working outputs to `projects/[company]/03-content-machine/_work/` so the whole thing is
auditable and re-runnable:

- **`writing-examples-step2-scores.md`** — every article's **Voice score `/10` + verdict + why** (all batches,
  including the ones that were dropped). This is the record of what passed, what failed, and the reasons.
- **`we-1-…md … we-5-…md`** — the **per-example blocks** (metadata + What Makes It Great + the full verbatim
  article), one file each. These are concatenated to build the final file (keeps the ~13k words of article
  text out of the main context during assembly).
- **`writing-examples.md`** (in `03-content-machine/`, not `_work/`) — the finished deliverable.

---

## A real run, in simple terms (Testlify, 2026-07-03)

This is exactly how the first run went — including the part where it didn't work the first time and had to be
redone. Expect the same shape.

1. **Step 1 — classify & pick 7.** Pulled 1,503 editorial articles from `top-pages.csv`, classified
   each by format from its URL, and picked **7** — highest traffic while covering different formats.
2. **Step 2 — score the 7. Only 1 passed.** Six of the seven scored **off-voice** (2–5/10). They were older,
   generic HR-explainer posts: no real numbers, written *about* the topic instead of *to* "you," and some using
   the banned AI-clichés — a few even opened like the ❌ anti-example in `brand-voice.md`. Only the Walmart
   "how a big company hires at scale" case study passed (9/10).
3. **Redo — pull a second batch.** Because fewer than 5 passed, we went back to Step 1 and pulled **another 7**,
   this time **targeting the genres that actually score on-voice** (more case studies + comparisons). This time
   **6 of 7 passed.**
4. **Keep the best 5.** We now had 7 on-voice articles. Took the top 5 by score, adjusting one pick for format
   variety (so it wasn't three near-identical case studies). Final 5 = 2 case studies + 1 comparison +
   1 definitional + 1 listicle.
5. **Assemble.** Each of the 5 was pasted in full (verbatim) with its metadata and its pillar-grounded
   "What Makes It Great" → `writing-examples.md` (~13k words, ~88 KB — Castos-scale).
6. **Step 3 — gate.** Checked completeness, verbatim full-text, ≥3 formats, all on-voice → **passed**.

**The one lesson to carry:** don't expect the first batch to yield 5. Most old content is off its own brand.
**Score a batch → keep the winners → pull another batch from the on-voice genres → repeat until you have 5.**

---
---

# Appendix A — Raw schema (fill every field; reference template)

> Mirror of `seomachine/context/writing-examples.md`. This is the skeleton Step 2 fills. Repeat the Example
> block for each of the 5 chosen articles. No `[BRACKET]` may survive.

```markdown
# [YOUR COMPANY] Writing Examples

This file contains exemplary blog posts from [YOUR COMPANY] that demonstrate the brand voice, style, and quality standards. Use these as reference when writing new content.

## Instructions
Add 3–5 complete blog post examples that represent: (1) ideal brand voice & tone, (2) strong SEO, (3) high-quality valuable content, (4) proper structure/formatting, (5) effective use of examples and data.
For each: URL · Title · Primary Keyword · Word Count · What Makes It Great · Full Content.

---

## Example 1: [ARTICLE TITLE]

**URL**: [https://site.com/article-url/]
**Primary Keyword**: [from Semrush top-keyword — as given]
**Word Count**: [~X,XXX words]

**What Makes It Great**:
- [Reason 1 — names a brand-voice pillar/rule it demonstrates]
- [Reason 2 — names a brand-voice pillar/rule]
- [Reason 3 — names a brand-voice pillar/rule]

**Full Content**:
```
[THE COMPLETE ARTICLE TEXT, PASTED VERBATIM — full intro, every subheading, lists, data, conclusion, CTA.]
```

---

## Example 2: [ARTICLE TITLE]   (repeat the same block)
## Example 3: [ARTICLE TITLE]   (repeat)
## Example 4: [ARTICLE TITLE]   (repeat)
## Example 5: [ARTICLE TITLE]   (repeat)
```

---
---

# Appendix B — Reference example (Castos) — REFERENCE ONLY · DO NOT COPY

> The **full** Castos writing-examples file (5 complete pasted articles, ~89 KB) lives at
> `seomachine/examples/castos/writing-examples.md`. It is too large to embed and there is no reason to — the
> **depth bar** is: 5 full real articles, diverse formats, each with a pillar-grounded "What Makes It Great."
> Below is the **structure + one real annotation block** as the calibration sample. **Do not copy any of it**
> (its topics, articles, or reasons) into a real `writing-examples.md` — that is an automatic fail (Step 3).

**Castos picked for format diversity:** Example 1 = definitional/pillar ("What is a podcast?", ~2,500w) ·
Example 2 = listicle ("How to Make Your First $100 Podcasting", ~1,595w) · Example 3 = step-by-step how-to
("How to Submit a Podcast to Spotify", ~2,100w) — three distinct shapes.

**One real annotation block (the depth to match, never the content):**
```markdown
## Example 1: What is a podcast? (+ easiest way to start in 2025)

**URL**: https://castos.com/what-is-a-podcast/
**Primary Keyword**: what is a podcast
**Word Count**: ~2,500 words

**What Makes It Great**:
- Thorough explanation of what a podcast is — covers all aspects of the topic.
- Includes customer pain points and the solutions that Castos provides.
- Strong structure with scannable subheadings.

**Full Content**:
[the complete ~2,500-word article, pasted verbatim]
```
