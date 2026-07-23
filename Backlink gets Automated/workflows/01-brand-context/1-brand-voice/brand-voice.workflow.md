---
type: workflow-recipe
stage: content-machine (Stage 0 — brand context)
reusable: any company
reads:
  - projects/[company]/01-brand-context/_pages/*.md        # the ~30 already-saved cornerstone pages
  - projects/[company]/01-brand-context/page-shortlist.md  # the page list + live URLs (for dispatch)
produces:
  - projects/[company]/01-brand-context/brand-voice.md                # the filled brand-voice document (the deliverable)
last_updated: 2026-07-03
---

# Brand Voice — build workflow

> **SCRIPTED (2026-07-19).** This recipe has a runnable twin: `scripts/run_brand_voice.py` executes the
> steps below in order (shortlist → evidence → assemble → quality-gate loop), reading Appendix A from THIS
> file so the recipe stays the single source of truth. The engine writes `_drafts/brand-voice-draft.md`;
> promoting it to `brand-voice.md` is the human gate. See `README.md` for the command.

> **Where this lives:** this recipe lives at `Backlink gets Automated/workflows/03-content-machine/`. It
> reads the pages from `Backlink gets Automated/projects/[company]/01-brand-context/_pages/`, and writes its
> output `brand-voice.md` to `Backlink gets Automated/projects/[company]/03-content-machine/`.

---

## What this does

Turn a company's **already-saved cornerstone pages** into a complete, richly-filled `brand-voice.md` —
the same shape and depth as the Castos reference in Appendix B — where **every line is drawn from the
company's own pages**, not invented. This document is Stage 0 of the content machine: it feeds every later
write / rewrite / optimize pass.

---

## The one rule that governs everything

**Every cell in `brand-voice.md` must trace to a real page we read** — either a trait we observed in the
prose, or a verbatim excerpt we can quote — **or to a stated brand fact.** Nothing is invented.

- If the company's pages don't evidence a section, **flag it as a decision for the human** — never fabricate
  a pillar, a message, or a segment to fill space.
- **The Castos example (Appendix B) is a COMPLETENESS + DEPTH BAR and a REFERENCE ONLY.** You may look at it
  to judge *how thorough* your document should be — never to borrow its words, pillars, messages, segments,
  or examples. Testlify is not a podcast host; copying any Castos content is an automatic fail (see Step 3).

---

## What you produce (named output of each step)

| Step | Produces |
|------|----------|
| 1. Read each page & extract its row (sub-agent per page) | **the page-evidence table** (one row per page) |
| 2. Fill the schema section-by-section, each from its mapped column (pure assembly) | **`projects/[company]/01-brand-context/brand-voice.md` (draft)** |
| 3. Quality gate vs the Castos bar | **pass/fail per section + redo instructions** (loops back to 2) |

---

## Inputs

- **`projects/[company]/01-brand-context/_pages/*.md`** — ~30 clean markdown pages, already saved.
- **`projects/[company]/01-brand-context/page-shortlist.md`** — the list of those pages with their live URLs
  (used only to get each page's file + URL for dispatch).
- **Appendix A** (in this file) — the raw schema (every header, placeholders). This is the skeleton to fill.
- **Appendix B** (in this file) — the Castos filled example. **Reference/quality bar only.**

> **Gotcha — thin pages:** the extractor is article-tuned. On a **homepage / pricing / landing page** it can
> strip feature grids and pricing tables — exactly where positioning lives. If a page file reads thin or
> truncated, **web-fetch the live URL** and read that instead. Do not classify a page you couldn't actually read.

---

## The steps (in order)

### Step 1 — Read each page and extract its row (one sub-agent per page)
**What it does:** turns the ~30 pages into the evidence table — each page read in full and reduced to one
row — using a fresh sub-agent per page so the main context never bloats and no page gets skimmed.

**Process:**
1. Read `page-shortlist.md` to get, for each page, its **file** and **URL**.
2. For **each** page, spawn **one sub-agent** with the exact prompt below (fill in `<FILE>`, `<URL>`).
   The sub-agent reads that one page end to end and returns its row. **One page = one sub-agent =
   one row.** These can run in parallel.
3. Collect every returned row into the evidence table. The main context does no page-reading itself — it only
   dispatches sub-agents and assembles their rows.

**The exact sub-agent prompt (send one per page):**
```
Extract brand-voice evidence from ONE page.

Read this file end to end:
  Backlink gets Automated/projects/[company]/01-brand-context/_pages/<FILE>
The page's live URL is <URL>.
If the file reads thin or truncated (common for homepage/pricing), web-fetch <URL> and read that instead.

Return ONLY the fields below. Draw everything from THIS page only.
Invent nothing. Leave a field blank if the page does not evidence it. Quote excerpts verbatim.
There is no length limit — write as much as the page genuinely supports; the more detail per field, the better.

- Page: <FILE> · <URL>
- Voice & tone observed: how it sounds (warm / blunt / confident / formal…) + one short cue phrase copied from the text
- Positioning / messaging claim: what the company says it IS / stands for / promises, on this page
- Audience & pain signals: who this page speaks to + the pain it names
- Quotable excerpt (verbatim): 1–2 real lines worth using as a ✅ voice example — copied exactly
- Style · format · exact CTA: sentence feel, headline shape, list use, and the EXACT CTA button text
- Company-specific dimension (only if a distinct theme recurs that the fields above miss): name it + what it says
```

Each returned row fills the table below. **Columns (fixed):**

| Column | What goes in it | Feeds |
|--------|-----------------|-------|
| **Page** | file name · URL | traceability |
| **Voice & tone observed** | how it *sounds* (warm/blunt/confident/formal…) + a one-phrase cue from the text | Tone, Pillars |
| **Positioning / messaging claim** | what the company says it *is* / stands for / promises, here | Pillars, Messaging, Value Props |
| **Audience & pain signals** | who this page talks to + the pain it names | Audience Understanding |
| **Quotable excerpt (verbatim)** | 1–2 real lines worth using as a ✅ voice example | Voice Examples ✅ |
| **Style · format · exact CTA** | sentence feel, headline shape, list use, and the **exact** CTA button text | Writing Style, Content Formatting |

**Column (open — add only if the pages demand it):**

| Column | When to add it |
|--------|----------------|
| **[Company-specific dimension]** | If a distinct theme recurs that the fixed columns miss, add a named column for it. *(Castos needed a "Monetization" dimension; Testlify might need e.g. "assessment library / anti-cheating".)* Do **not** invent one to look thorough — add it only if ≥2 pages evidence it. |

**Output:** the page-evidence table (≈30 rows).

**Gotchas:**
- **Never classify from the title or URL** — the sub-agent must read the body; that's the whole point.
- **Blanks are allowed** — if a cell has no evidence on that page, leave it blank. A blank is information
  (this page doesn't speak to that section); don't pad it.
- **Add the company-specific column only if ≥2 pages evidence it** — never to look thorough.

**Example row (illustrative format — real values come from the sub-agent's read):**

| Page | Voice & tone observed | Positioning / messaging claim | Audience & pain signals | Quotable excerpt | Style · format · exact CTA |
|------|----------------------|-------------------------------|-------------------------|------------------|----------------------------|
| `002-…hire-the-best…` · testlify.com/ | Confident, direct, second-person; no hype | "Hire the best, not just hire" — quality-of-hire over speed | Hiring teams afraid of bad hires | *"Don't just hire — hire the best."* | Short punchy H1s; colon-led lead-ins; CTA: **"Try for Free"**, **"Book a Demo"** |

---

### Step 2 — Fill the schema, section by section (pure assembly)
**What it does:** writes `brand-voice.md` by filling **Appendix A's skeleton** one header at a time. Each
section names the **exact Step-1 column** it draws from — so the mapping isn't just declared, it's the thing
you act on. **You don't write a section until you've pulled its column across all ~30 rows.**

**Process:** work down this table. For **every** header in Appendix A (no `[BRACKET]` may survive), pull the
mapped column from all rows, then write the section as instructed:

> **How the "How to write it" column was built:** it mirrors the *structure* of each section in the Castos
> example (Appendix B) — the counts, sub-fields, and format only. **None of Castos's wording or content is
> reproduced here** (that stays fenced in Appendix B). You are copying its *skeleton*, never its answers.

| Fill this section | ← Pull this column (across all ~30 rows) | How to write it (structure to match) |
|-------------------|------------------------------------------|--------------------------------------|
| **Brand Voice Pillars** | Positioning/messaging **+** Voice&tone | **3–5 pillars.** Cluster the pulled cells first, then name each pillar **last** (substance before label). Each pillar has four sub-fields: **What it means** (1-line concept) · **How it sounds** (1–2 lines on execution/tone; an analogy is fine) · **Example** (one short in-voice sentence in quotes — real or faithful) · **Avoid** (a comma-list of anti-patterns, optionally ending in one punchy rule). |
| **Tone Guidelines** | Voice & tone observed | **Two parts.** (a) **General tone:** a short persona *label* + a 2–3 sentence "imagine you're…" paragraph. (b) **Variations by content type:** for each type present — How-To Guides, Strategy/Advice, Industry News/Trends, Product/Feature — a few tone adjectives **plus 3–4 real example phrases** (in quotes) that sound like that page type. |
| **Messaging Framework** | Positioning/messaging claim | **3–5 core messages.** Each = a short **Title** · **Concept** (1 sentence) · **Key Points** (2–3 bullets) · **Usage** ("When discussing …"). Each must be backed by a real page; **flag** any unevidenced message for the human. |
| **Value Propositions** | Positioning/messaging claim | **One line per real customer segment** (~4–5). Format: **For [segment]:** + a single punchy benefit sentence in quotes. **Flag** a segment the site doesn't address rather than inventing it. |
| **Writing Style Guidelines** | Style · format · CTA | **Four sub-blocks, ~4 rules each.** **Sentence structure** (vary length; active voice with a real *active vs passive* example; an average word-count range; a clarity rule). **Paragraph structure** (a sentence-count range; one idea per paragraph; transitions; white space). **Word choice** (conversational; specific-with-a-real-number example; an active-verb list; a fluff-words-to-cut list). **Terminology:** a **Say This → Not That** list of ~5 pairs, each with a short reason in parens. |
| **Content Formatting** | Style · format · CTA | **Four sub-blocks, ~4 rules each:** **Headlines** (be specific with a real example; include benefit; use numbers; a length/character cap) · **Subheadings** · **Lists** (numbered vs bulleted; parallel structure) · **Calls-to-Action** (clear action with a real example; value-focused; timing; placement) — and quote the **exact** on-site CTA button text. |
| **Voice Examples ✅** | Quotable excerpt | A **real, multi-paragraph excerpt** (2–4 short paragraphs) pasted **verbatim** from a strong page, followed by a **"Why this works"** list of ~5 bullets naming the specific moves (pain acknowledged, active language, clear expectation…). |
| **Voice Examples ❌** | *(constructed — not from a page)* | A **constructed** 2–3 paragraph anti-example showing the failure modes (corporate-speak, feature-dump, generic CTA, AI clichés), then a **"Why this fails"** list of ~5 bullets. **Label it clearly as constructed.** |
| **Audience Understanding** | Audience & pain signals | **Three sub-blocks.** **Who we write for:** a named **Primary audience** + ~5 characteristics, then ~3–4 **Secondary audiences** (name + one line each). **What they care about:** ~5 **Top priorities** + ~5 **Pain points**. **How to serve them:** ~5 principles (principle name + how). |
| **Quality Checklist** | derived from all the above | **~10 checkboxes**, one per quality dimension (voice, tone, value, clarity, accuracy, examples, action, messaging, terminology, empowerment), each with a short descriptor tied to *this* company's voice. Close with a one-line **"Remember:"** mission statement. |

**Output:** `projects/[company]/01-brand-context/brand-voice.md` (draft).

**Gotchas:**
- **Pure assembly — no new thinking.** If a cell isn't traceable to a Step-1 row (or a flagged human
  decision), it doesn't belong in the document.
- **The ❌ example is the one thing not pulled from a page** — it's a constructed anti-example; label it clearly.

---

### Step 3 — Quality gate vs the Castos bar (loop)
**What it does:** checks the draft is as **complete and deep** as the Castos reference — *without having copied
any of it.*

**Process — check three things:**
1. **Completeness:** every Appendix-A header present and filled; zero `[BRACKET]` placeholders left.
2. **Depth (match Castos's thoroughness, section by section):** 3–5 pillars each with What/How/Example/Avoid ·
   3–5 core messages · a value prop per real segment · tone variations for each content type · real ✅ excerpt +
   constructed ❌ · terminology pairs · audience priorities *and* pain points · full quality checklist.
3. **Specificity:** uses the company's **real** numbers, product names, competitor names, and CTA text — not
   vague filler.

**Two HARD RULES (non-negotiable):**
- 🚫 **Castos is a reference for depth/completeness ONLY.** If *any* wording, pillar, message, segment, or
  example has been borrowed from Castos (Appendix B), it is an **automatic fail** — rewrite that part from the
  company's own pages. We are matching *how thorough* Castos is, never *what* Castos says.
- 🔁 **If any section is thinner or vaguer than the Castos equivalent, that section fails** → return to Step 2
  and rebuild it from the table. Repeat until every section passes.

**Output:** pass/fail per section + specific redo instructions. Only a full pass ships the document.

---

## Traceability map (every section ← a named upstream source)

*Pure-assembly guarantee: if a section can't be traced to a column below, it isn't sourced and must be
flagged, not written.*

| `brand-voice.md` section | Step-1 column(s) | Notes |
|--------------------------|------------------|-------|
| Brand Voice Pillars | Positioning + Voice&tone | cluster then name |
| Tone Guidelines | Voice & tone | one variation per content type |
| Messaging Framework | Positioning/messaging | flag unevidenced messages |
| Value Propositions | Positioning/messaging | one per real segment; flag gaps |
| Writing Style | Style·format·CTA | real observed rules |
| Content Formatting | Style·format·CTA | incl. exact CTA text |
| Voice Examples ✅ | Quotable excerpt | real verbatim only |
| Voice Examples ❌ | — (constructed) | anti-example, clearly labelled |
| Audience Understanding | Audience & pain | real pains from pages |
| Quality Checklist | derived | from all above |

---

## Rules shelf (what this recipe points to, not restates)

- **Raw schema to fill:** Appendix A (below) — mirror of `seomachine/context/brand-voice.md`.
- **Quality/depth bar:** Appendix B (below) — the Castos example. Reference only.
- **Page provenance / thin-page caveat:** the saved pages in `brand-context/_pages/` were extracted per-page; a few are thin (JS-heavy pages that yielded little text) — check word counts before leaning on one. (Carried inline from the retired brand-brain recipe, 2026-07-19.)

---

## Gotchas (top of mind)

1. **Read the body, never classify from titles** (Step 1).
2. **Thin homepage/pricing pages** — web-fetch the live URL if the saved file is stripped.
3. **Blanks are allowed** — don't pad an unevidenced cell.
4. **The ❌ example is the only constructed content** — everything else is from the pages.
5. **Castos is a mirror for depth, never a source of content** — copying = automatic fail.
6. **Flag, don't fabricate** — unevidenced messages/segments go to the human.

---
---

# Appendix A — Raw schema (fill every header; reference template)

> Mirror of `seomachine/context/brand-voice.md`. This is the skeleton Step 2 fills. No `[BRACKET]` may survive.

```markdown
# [YOUR COMPANY] Brand Voice & Messaging

This document defines the [YOUR COMPANY] brand voice, tone, and messaging framework. Reference this when writing all content to ensure consistency.

## Brand Voice Pillars
<!-- 3–5 pillars. Each: What it means · How it sounds · Example · Avoid -->

### 1. [VOICE PILLAR NAME]
- **What it means**: [core concept]
- **How it sounds**: [tone, style, approach]
- **Example**: "[a sentence in this voice]"
- **Avoid**: [opposite tones/styles]

### 2. [VOICE PILLAR NAME]
- **What it means**: …
- **How it sounds**: …
- **Example**: "…"
- **Avoid**: …

### 3. [VOICE PILLAR NAME]
- **What it means**: …
- **How it sounds**: …
- **Example**: "…"
- **Avoid**: …

### 4. [VOICE PILLAR NAME] (Optional)
### 5. [VOICE PILLAR NAME] (Optional)

## Tone Guidelines

### General Tone: [DESCRIBE YOUR GENERAL TONE]
[A paragraph describing the overall tone.]

### Tone Variations by Content Type
**How-To Guides**: [adjectives]
- "[example phrase]" ×3
**Strategy/Advice Content**: [adjectives]
- "[example phrase]" ×3
**Industry News/Trends**: [adjectives]
- "[example phrase]" ×3
**Product/Feature Content**: [adjectives]
- "[example phrase]" ×3

## Messaging Framework

### Core Brand Messages
#### Message 1: [MESSAGE TITLE]
- **Concept**: [one sentence]
- **Key Points**: [point ×3]
- **Usage**: When discussing [topics]
#### Message 2 … #### Message 3 … #### Message 4 (Optional)

### Value Propositions
**For [TARGET SEGMENT 1]**: "[value proposition]"
**For [TARGET SEGMENT 2]**: "…"
**For [TARGET SEGMENT 3]**: "…"
**For [TARGET SEGMENT 4]** (Optional) … **For [TARGET SEGMENT 5]** (Optional)

## Writing Style Guidelines
### Sentence Structure
- **Vary length**: … · **Active voice preferred**: [ex] not [counter] · **Average length**: [X–Y words] · **Clarity first**: …
### Paragraph Structure
- **Length**: [X–Y sentences] · **One idea per paragraph** · **Transitions** · **White space**
### Word Choice
- **[CHARACTERISTIC 1–3]** … · **[WHAT TO AVOID]**
### Terminology
**Say This** → **Not That**
- [Preferred] → [Avoid] ([reason]) ×5

## Content Formatting
### Headlines — [RULE ×4]
### Subheadings — [RULE ×4]
### Lists — [RULE ×4]
### Calls-to-Action — [RULE ×4]

## Voice Examples
### Excellent [YOUR COMPANY] Voice ✅
"[a full real multi-sentence excerpt]"
**Why this works**: [reason ×5]
### Not [YOUR COMPANY] Voice ❌
"[a constructed anti-example — corporate/AI/feature-dump]"
**Why this fails**: [reason ×5]

## Audience Understanding
### Who We Write For
**Primary Audience**: [name] — [characteristic ×5]
**Secondary Audiences**: [segment: description] ×4
### What They Care About
**Top Priorities**: [×5] · **Pain Points**: [×5]
### How to Serve Them
- **[PRINCIPLE 1–5]**

## Quality Checklist
- [ ] Voice · [ ] Tone · [ ] Value · [ ] Clarity · [ ] Accuracy · [ ] Examples · [ ] Action · [ ] Messaging · [ ] Terminology · [ ] Empowerment

---
**Remember**: [a memorable closing statement capturing the brand's essence and mission.]
```

---
---

# Appendix B — Reference example (Castos) — REFERENCE ONLY · DO NOT COPY

> This is a **filled** example for a *different* company (Castos, a podcast host). Use it **only** to judge
> whether your document is as **complete and detailed** as this — its structure, its depth, the fact that no
> header is missing and every section is specific. **Do not borrow any of its wording, pillars, messages,
> segments, or examples.** Copying any of this into a real `brand-voice.md` is an automatic fail (Step 3).

```markdown
# Castos Brand Voice & Messaging
This document defines the Castos brand voice, tone, and messaging framework. Reference this when writing all content to ensure consistency.

## Brand Voice Pillars
### 1. Professional Yet Approachable
What it means: We're experts in podcasting, but we're not stuffy or overly formal
How it sounds: Conversational, warm, knowledgeable without being condescending. Like talking to a really knowledgeable, experienced friend on a topic.
Example: "Podcast hosting doesn't have to be complicated. Here's what you actually need to know."
Avoid: Overly technical jargon without explanation, corporate-speak, talking down to readers, vague and fluffy speak that doesn't convey any real message. Never be boring.
### 2. Educational & Empowering
What it means: We teach podcast creators to succeed on their own terms
How it sounds: Encouraging, instructive, focused on building capability
Example: "You've got this. Let's walk through how to optimize your podcast for growth."
Avoid: Gatekeeping knowledge, making podcasting seem harder than it is, creating dependency
### 3. Podcast Creator Advocate
What it means: We're on the side of independent creators, not big media
How it sounds: Supportive of creator goals, understanding of challenges
Example: "We built Castos because podcast creators deserve better tools and support."
Avoid: Speaking from platform/company perspective only, ignoring creator pain points
### 4. Technically Accurate but Accessible
What it means: We get the technical details right while explaining clearly
How it sounds: Precise when needed, simple explanations for complex concepts
Example: "RSS feeds are how podcast apps discover your show. Think of it like a menu that updates automatically."
Avoid: Dumbing down to the point of inaccuracy, unnecessary complexity
### 5. Focused on Results & Growth
What it means: We care about podcast creator success metrics and outcomes. this is audience growth, monetization as well
How it sounds: Action-oriented, results-focused, growth-minded
Example: "These strategies helped podcast creators increase their downloads by 40%."
Avoid: Vague promises, hype without substance, ignoring practical application
## Tone Guidelines
### General Tone: Helpful Expert Friend
Imagine you're an experienced podcaster helping a friend succeed. You know what you're talking about, you genuinely want them to succeed, and you explain things clearly without being patronizing.

### Tone Variations by Content Type
How-To Guides: Instructive, step-by-step, encouraging
"First, you'll want to..."
"Now that you've completed X, let's move on to Y."
"Don't worry if this seems confusing at first—it'll click once you try it."
"I like to start by..."
Strategy/Advice Content: Authoritative, experienced, actionable
"Here's what successful podcasters do differently..."
"The most effective approach is..."
"Based on our analysis of 10,000+ podcasts..."
"When I am facing a decision like this, I always..."
Industry News/Trends: Insightful, analytical, forward-looking
"This shift means podcast creators need to..."
"The podcasting landscape is evolving toward..."
"Here's why this matters for your show..."
"This is the really crazy part, that nobody is talking about..."
Product/Feature Content: Benefit-focused, clear, honest
"This feature solves the problem of..."
"You can use this to..."
"Here's how it works in practice..."
## Messaging Framework
### Core Brand Messages
#### Message 1: Podcasting Made Simple
Concept: Podcast hosting and growth shouldn't require technical expertise
Key Points: Intuitive tools that just work / No steep learning curve / Focus on creating, not troubleshooting
Usage: When discussing platform features, ease of use, user experience
#### Message 2: Built for Serious Creators
Concept: Professional-grade tools for creators who take podcasting seriously
Key Points: Advanced features when you need them / Scales with your ambitions / Trusted by successful podcasters
Usage: When discussing capabilities, advanced features, scalability
#### Message 3: Your Podcast's Growth Partner
Concept: We're invested in your success, not just hosting your files
Key Points: Analytics that drive decisions / Features that support growth / Resources to level up skills
Usage: When discussing analytics, growth strategies, educational content
#### Message 4: Monetization Options
Concept: We have the most tools to help you make money from your podcast in the industry
Key Points: Castos Ads: one-click dynamic ad insertion / Paid private (or Hybrid) podcasts / Castos Commerce: one-time or recurring donations
Usage: When discussing making money from a podcast
### Value Propositions
For New Podcasters: "Start your podcast the right way with tools that grow with you."
For Established Podcasters: "Take your podcast to the next level with analytics and features that drive growth."
For Business Podcasters: "Professional podcast hosting with the tools and support your brand deserves."
For Podcast Networks: "Manage multiple shows with ease using enterprise-grade features."
For Podcasters Who Want To Monetize: "More ways to make money from your content."

## Writing Style Guidelines
### Sentence Structure
Vary length: Mix short punchy sentences with longer explanatory ones
Active voice preferred: "Castos helps you grow" not "Growth is helped by Castos"
Average length: 15-20 words per sentence
Clarity first: If a sentence is confusing, rewrite it
### Paragraph Structure
Length: 2-4 sentences typically / One idea per paragraph / Transitions: Connect logically / White space: Break up long blocks
### Word Choice
Conversational / Specific: "Increase downloads by 40%" not "Improve performance" / Active verbs: "Launch", "Create", "Grow", "Build", "Optimize" / Avoid fluff: Cut "very", "really", "actually" unless needed
### Terminology
Say This → Not That
Podcast hosting → Podcast storage (hosting is industry standard)
Analytics → Stats (analytics sounds more professional)
RSS feed → Podcast feed (RSS for technical accuracy when needed)
Listener → Subscriber (listener is more accurate)
Episode → Show (episode is the unit, show is the series)
## Content Formatting
### Headlines
Be specific: "How to Grow Your Podcast Audience in 2025" not "Podcast Growth Tips" / Include benefit / Use numbers / Keep concise: 60 characters or less for SEO
### Subheadings
Descriptive / Scannable / Keyword-rich / Parallel structure
### Lists
Numbered for sequential steps / Bulleted for multiple items / Keep consistent (parallel structure) / Scannable
### Calls-to-Action
Clear action: "Start your free trial" not "Learn more" / Value-focused / Appropriate timing / Natural placement
## Voice Examples
### Excellent Castos Voice ✅
"A lot of people think creating a podcast is too complicated for them – it seems like a lot of work, you need a lot of equipment, time and even getting the right guests on seems like a lot of effort.

Or sometimes, they think that it's way too simple to be taken seriously as a business or marketing channel.

But we've helped thousands of people start podcasts, and here's what we've learned:

This misconception keeps thousands of experts, entrepreneurs, and passionate individuals from sharing their knowledge and building audiences."

Why this works: Acknowledges reader's pain point / Conversational and approachable / Promises practical value / Sets clear expectations / Active, direct language
### Not Castos Voice ❌
"Podcast analytics represent a comprehensive suite of metrics available to content creators for evaluating performance across multiple dimensions of listener engagement and content efficacy.

At Castos, we provide industry-leading analytics capabilities that enable sophisticated analysis of podcast performance through our proprietary dashboard interface.

Click here to learn more about our analytics features."

Why this fails: Overly formal and corporate / Features-focused not benefit-focused / Doesn't acknowledge creator needs / Generic CTA / Reads like marketing copy
## Audience Understanding
### Who We Write For
Primary Audience: Independent Podcast Creators — side projects/businesses/passions / beginners to experienced / want professional results without complexity / value their time / ambitious but realistic about resources
Secondary Audiences: Marketing Teams / Content Creators / Agencies / Educators
### What They Care About
Top Priorities: Growing audience & downloads / Creating quality content efficiently / Understanding what's working / Monetizing / Standing out
Pain Points: Limited time for technical aspects / Confusion about best practices / Difficulty measuring success / Consistent publishing / Uncertainty about growth
### How to Serve Them
Respect their time / Make it actionable / Explain the "why" / Acknowledge challenges / Celebrate progress
## Quality Checklist
☐ Voice ☐ Tone ☐ Value ☐ Clarity ☐ Accuracy ☐ Examples ☐ Action ☐ Messaging ☐ Terminology ☐ Empowerment
Remember: Every piece of content should make podcast creators feel more capable and confident. We're not just providing information—we're empowering success.
```
