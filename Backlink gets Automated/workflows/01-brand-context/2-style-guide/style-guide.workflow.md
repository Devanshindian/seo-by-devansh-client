---
type: workflow-recipe
stage: content-machine (Stage 0 — brand context)
reusable: any company
reads:
  - projects/[company]/00-foundation/output/content-database.csv   # top blogs (URL · Title · Traffic) + their Full content
produces:
  - projects/[company]/01-brand-context/style-guide.md          # the style guide (grammar · punctuation · formatting · SEO meta · checklist)
last_updated: 2026-07-04
---

# Style Guide — build workflow

> **Where this lives:** lives at `Backlink gets Automated/workflows/03-content-machine/`. Reads
> `content-database.csv` from `Backlink gets Automated/projects/[company]/…`; writes `style-guide.md` to
> `projects/[company]/03-content-machine/`.

---

## What this does — in one line

**Pull the top ~30 blogs from the content database → analyze them → fill the style-guide template.** About **85% of
the template is standard best-practice** (written straight in — no analysis needed); the rest — the few choices
that have to match how the company actually writes (capitalization, punctuation, industry terms/acronyms) — come
from **reading the real blogs.**

No brand-voice, no `voice-data`, no reference file — just the real published content + editorial standards.

---

## The one rule

**Every field is filled from one of three sources, and each is tagged so it's obvious where it came from:**
- **`[BLOGS]`** — decided by looking at the real top-30 blogs (via the Step-2 analysis).
- **`[STANDARD]`** — a best-practice editorial default, written straight in (same for most companies).
- **`[COMPANY]`** — needs the company's marketing team to confirm; fill what the blogs show, then flag it.

**Nothing is invented; no template section is missed.**

---

## What you produce

| Step | Produces |
|------|----------|
| 1. Pull the top ~30 blogs | **`_work/style-guide-top-blogs.md`** — table of Rank · Traffic · Format · Title · URL |
| 2. Analyze the blogs (3 sub-agents → merge) | **`_work/style-guide-blog-analysis.md`** — the observed style signals |
| 3. Fill the template | **`style-guide.md`** |

---

## The steps (in order)

### Step 1 — Pull the top ~30 blogs (from the content database)
**Process:** from `content-database.csv`, rank all pages by **`Traffic`**, keep only the **editorial blog
articles** (use the signal table below to confirm), and take the **top ~30**. Drop commercial pages
(product/pricing/feature/competitor/integration), glossary/catalog/template pages, and non-English/localized
duplicates.

**Identify a blog from its Title / URL slug:**

| Signal in the URL / title | Format (just a tag) |
|---------------------------|---------------------|
| `what-are-…`, `…-definition`, `types-of-…` | Definitional / pillar |
| `top-15-…`, `top-8-…`, `…-questions` | Listicle |
| `how-to-…`, `…-process`, `…-in-5-steps` | Step-by-step how-to |
| `…-vs-…` (topic comparison) | Comparison |
| broad opinion/strategy topic (`the-4-pillars-of-…`) | Thought-leadership |
| anything else the slug clearly signals | Other — label it (e.g. case study, guide) |
*(A page matching one of these AND not on the exclude list is a blog. Format is just a helpful tag — we take the
top 30 by traffic regardless of format.)*

**Output — save to `projects/[company]/03-content-machine/_work/style-guide-top-blogs.md`** — a table, so Step 2
knows exactly which pages to analyze:

| Rank | Traffic | Format | Title | URL |
|------|---------|--------|-------|-----|
| 1 | 185 | Definitional | What are pink collar jobs? A definitive guide | https://testlify.com/pink-collar-jobs/ |
| 2 | 158 | Listicle | 60 Inventory Planner interview questions… | https://testlify.com/inventory-planner-interview-questions…/ |
| 3 | 94 | Definitional | Job specialization: definition, examples, pros & cons | https://testlify.com/job-specialization/ |
| … | … | … | … *(down to ~30)* | … |

**Gotcha:** blogs only — the homepage and pricing page sneak into a naive traffic sort; the signal table + exclude
list drop them.

---

### Step 2 — Analyze the blogs (3 sub-agents → merge)
**What it does:** reads the ~30 blogs and extracts the handful of style signals the template's `[BLOGS]` fields
need — so those decisions come from real content, not guesses.

**Process:**
1. Take the ~30 blogs from **`_work/style-guide-top-blogs.md`** (Step 1's output) and split them into **3 batches
   of ~10**. Spawn **one sub-agent per batch** (they can run in parallel).
2. Each sub-agent reads each blog's **`Full content`** (match the URL → `Full content` column in
   `content-database.csv`; pre-extract each batch to a small file at run time) and returns the signals below.
3. **Merge** the 3 sub-agents' returns into one **blog-analysis table** — for the yes/no choices (Oxford comma,
   quote style…), **majority wins**; for lists (industry terms, acronyms), **union + dedupe**.

**The exact sub-agent prompt (send one per batch):**
```
Analyze how these Testlify blog articles are actually written, to inform a style guide. Read each blog's Full
content (match the URL to its row in content-database.csv → the `Full content` column).

Here is your batch of URLs:
<the batch>

Report ONLY what you OBSERVE across these blogs (not opinions). Give one answer per signal:
- headline_case: how titles/H2s are cased — Title Case or Sentence case (whichever dominates)
- brand_naming: how the company + its products are written (capitalization), e.g. "Testlify" always capitalized
- industry_terms: the recurring industry terms + their spelling/casing (e.g. "skills assessment", "candidate", "ATS", "time-to-hire")
- oxford_comma: Yes or No (which dominates)
- em_dash_usage: how em dashes / hyphens are used (e.g. "rare; hyphens preferred")
- quote_style: single, double, or curly quotes (which dominates)
- ellipses: how often / how used
- number_style: how numbers are written (spell out vs numerals; %, $, measurements)
- acronyms: the industry acronyms that appear (e.g. ATS, HR, DEI, KYC) — the ones worth defining on first use
- preferred_words: any consistent word choices worth keeping ("say this")
- avoided_words: any hype/filler/AI-cliché words that appear and should be cut ("not that")
```

**Output — save the merged table to `projects/[company]/03-content-machine/_work/style-guide-blog-analysis.md`**
(Step 3 pulls each `[BLOGS]` field from here):

| Signal | Observed value (merged across the top 30) |
|--------|-------------------------------------------|
| headline_case | *(e.g. Sentence case)* |
| brand_naming | *(e.g. "Testlify" always capitalized)* |
| industry_terms | *(e.g. skills assessment · candidate · ATS · time-to-hire · proctoring)* |
| oxford_comma | *(Yes / No)* |
| em_dash_usage | *(e.g. rare — hyphens preferred)* |
| quote_style | *(single / double / curly)* |
| ellipses | *(e.g. rare)* |
| number_style | *(e.g. numerals for stats; % and $ as numerals)* |
| acronyms | *(e.g. ATS, HR, DEI, KYC, SOC 2)* |
| preferred_words | *(observed "say this")* |
| avoided_words | *(observed "not that" — hype/filler)* |

---

### Step 3 — Fill the template
Fill the template below **exactly as written**: keep every `[STANDARD]` line as-is; replace each `[BLOGS: …]`
with the matching cell from the Step-2 table; fill each `[COMPANY: …]` with what the blogs show, then leave the
note for marketing. **Every section stays; no `[…]` tag is left unresolved.** Write the result to
`projects/[company]/01-brand-context/style-guide.md`.

```markdown
# [Company] Style Guide

## Grammar & Mechanics

### Capitalization
- **Headlines & subheadings**: [BLOGS: headline_case]
- **Product names**: [BLOGS: brand_naming]  (the company name is always capitalized)
- **Industry terms**: [BLOGS: industry_terms — list each term with its house spelling/casing]

### Numbers  [STANDARD]
- Spell out one–nine; use numerals for 10 and above.
- Always numerals for: percentages (5%), money ($500), measurements (5 GB), and stats/lists (for scannability).
- Large numbers: use commas (1,000+); spell out "million"/"billion". [BLOGS: number_style — adjust if the blogs differ]

### Punctuation
- **Oxford comma**: [BLOGS: oxford_comma]  (apply consistently)
- **Em dashes**: [BLOGS: em_dash_usage]
- **Quotation marks**: [BLOGS: quote_style]
- **Ellipses**: [STANDARD] three dots, no surrounding spaces, used sparingly (mainly for omitted text in quotes). [BLOGS: ellipses]

### Abbreviations & Acronyms  [STANDARD]
- Spell out on first use, then use the acronym: "Applicant Tracking System (ATS)".
- **Common industry acronyms** (define on first use): [BLOGS: acronyms]
- Latin abbreviations: use "e.g.", "i.e.", "etc." sparingly.

## Word Choice & Usage

### Preferred Terms — "Say This → Not That"  [BLOGS + COMPANY]
- [BLOGS: preferred_words — as "say this → not that" pairs]
- [COMPANY: add the terms marketing prefers/avoids — product names, positioning language]

### Words to Avoid  [STANDARD + BLOGS]
- Cut filler: "very", "really", "actually" (usually unnecessary).
- No "click here" / "read more" — use descriptive link text.
- No AI-clichés / hype: [BLOGS: avoided_words] (e.g. seamless, leverage, robust, unlock, delve, elevate).

### Inclusive Language  [STANDARD]
- Gender-neutral where possible; people-first language; avoid idioms that don't translate.

## Formatting Standards  [STANDARD]
### Text Formatting
- Bold for genuine emphasis (sparingly); italics for terms/titles; no underline (reads as a link); no ALL CAPS.
### Lists
- Bulleted for non-sequential items; numbered for steps/rankings; nested lists indented one level; items parallel; one idea each.
### Links
- Descriptive anchor text (never "click here"); link the phrase that names the destination.
### Code & Technical Elements
- `inline code` for short snippets / UI labels; fenced blocks for multi-line code.
### Callout Boxes / Asides
- Use sparingly for tips, warnings, or key takeaways.

## Content Structure  [STANDARD]
### Article Introduction
- Hook → the reader's problem → the promise of the article (≈150–250 words).
### Section Length
- One idea per section; ~200–300 words; clear H2/H3 hierarchy; scannable.
### Conclusion
- Summarize the value + one clear CTA (≈150–200 words).

## SEO-Specific Style  [STANDARD]
### Meta Titles
- ≤ 60 characters, primary keyword near the front.
### Meta Descriptions
- ~150–160 characters, includes the keyword, reads as a benefit.
### URL Slugs
- Short, lowercase, hyphenated, keyword-focused; no stop-words / dates.
### Alt Text
- Describe the image; include the keyword only when natural.

## Dates & Time  [STANDARD]
- Format: "Month DD, YYYY" (e.g. July 4, 2026). Consistent, unambiguous formats; avoid "5/4".

## Statistics & Data  [STANDARD]
### Citing Sources
- Cite the source inline and link it; name the source; don't invent or misround.
### Presenting Numbers
- Numerals for scannability; keep units consistent.

## Images & Media  [STANDARD]
### Image Captions
- Where they add context; brief and specific.
### Screenshots
- Current, legible, annotated where helpful.
### Charts & Graphs
- Labelled axes/units and a clear title; source cited.

## Brand-Specific Guidelines
### [Company] Product References  [COMPANY]
- How to name and refer to the company's products/features in content (exact product names, capitalization,
  when to link to product pages). Fill what the blogs show — *confirm with marketing*.
### Competitor References  [BLOGS + COMPANY]
- How competitors are named and compared — fair, factual, no disparagement (from the comparison blogs);
  *confirm any do/don't rules with marketing*.

## Accessibility  [STANDARD]
### Screen Reader Friendly
- Real heading hierarchy, alt text on images, descriptive link text.
### Plain Language
- Short sentences; define jargon on first use.

## Voice & Tone Reminders  [BLOGS]
### Core Voice Characteristics
- A short reminder of how the company sounds, observed from the blogs: [BLOGS: e.g. confident, second-person,
  proof-backed, plain-spoken]. (The full voice lives in `brand-voice.md`.)
### Tone Variations
- How tone shifts by content type — see `brand-voice.md` (Tone Guidelines).

## Editing Checklist  [STANDARD]
Before publishing: spelling/grammar checked · punctuation consistent (Oxford comma, dashes, quotes) · numbers &
dates consistent · preferred terminology used · formatting consistent · headings hierarchical · strong intro +
CTA · keyword integrated naturally · meta + slug + alt text done · internal/external links working · sources cited
· genuinely useful · ready to publish.

## Updates & Maintenance  [STANDARD]
- Keep the guide current: add new terms/acronyms as they appear, revisit when products or positioning change,
  and keep it aligned with `brand-voice.md`.
```

---

## Agent notes (do NOT put these in the output file)
- For every **`[COMPANY]`** field: fill what the top-30 blogs actually show, then add a short flag like
  *"— confirm with marketing"* so the human knows it's the one place their input is wanted. Don't leave it blank,
  and don't invent brand preferences.
- If a **`[BLOGS]`** signal was ambiguous across the 30 (no clear majority), pick the cleaner editorial option and
  note it rather than forcing a false "the site does X".

---

## Quick gate before shipping
- **No `[BLOGS]` / `[STANDARD]` / `[COMPANY]` / `[…]` tags left** in the output — every one resolved.
- **Every section present** (grammar → editing checklist).
- **The `[BLOGS]` fields match the Step-2 table** (spot-check Oxford comma, quotes, headline case).
