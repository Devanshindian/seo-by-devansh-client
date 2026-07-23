---
type: content-standard
stage: content-machine (Stage 0 — SEO / AEO / GEO standard)
scope: reusable across companies — fill the 6 slots in §1
role: context file — read by /research, /write, and every SEO agent. Not a command you run per article.
last_updated: 2026-07-05
---

# SEO / AEO / GEO Guidelines

The single standard for writing and refreshing content. Goal: **rank #1 on Google and get cited by AI**
(AI Overview, ChatGPT, Perplexity, Gemini, Claude). SEO serves the reader, never the algorithm — the best
SEO is genuinely helpful content.

Read the doc in order: **§2 principles** (internalize) → **§3 workflow** (execute, in sequence) → **§4 the
quality bar** (the reference specs each workflow step points to) → **§5 governance** → **§6–§7 the gate**.
Everything below the `BUILD NOTES` divider is provenance for humans; agents can stop at §8.

---

## 1. How to specialize per company — ask the user these questions

This standard is universal. Before using it for a company, **ask the user these six questions** and fill the
slots with their answers (swap any native examples for the company's domain). Nothing else changes.

| Slot | What it is | Example |
|---|---|---|
| `{{BRAND}}` | Company name | Testlify |
| `{{PRODUCT}}` | What it sells (for natural mentions + CTA) | skills assessments & AI interviews |
| `{{AUDIENCE}}` | The reader the content targets | enterprise HR / People Ops at 1000+-employee companies |

> **Never-cite-a-competitor** is enforced upstream by the research-structure filter — the list is owned by the
> company's competitor study (`02-asset-engine/competitor-study/output/competitors.md`), not a slot here.

**Company inputs this standard defers to** (set once per company, not re-decided here): author-box rendering
(theme) and the editorial AI-disclosure policy.

---

## 2. Principles — the spine

### 2.1 The three engines

| Attribute | SEO | AEO | GEO |
|---|---|---|---|
| Engine | Google / Bing crawlers | Answer engines, AI Overviews, voice | Generative AI (ChatGPT, Claude, Gemini, Perplexity) |
| Intent | Navigational / informational / transactional | Quick, conversational, voice-first | Deep synthesis, multi-step reasoning |
| Output | Ranked links | Featured snippet / spoken answer | Generated prose citing sources |
| Primary signal | Backlinks, E-E-A-T, Core Web Vitals | Concise structured answers | In-body stats + quotes + outbound citations to named primaries |
| Win condition | Drive organic traffic | Be the lifted answer | Get quoted / cited in AI output |

### 2.2 The five levers that compound

Spend effort top-down — lever 1 first, densely.

| # | Lever | Why it matters | Detailed spec |
|---|---|---|---|
| 1 | **Inline stats + direct quotes + outbound citations to named primary sources** | Strongest causal AI-citation lift (Princeton GEO study: each ~+30–40% citation likelihood) | §4.4 |
| 2 | **E-E-A-T on page** | Google's trust gate; AI weighs source authority. Author box rendered **natively by the theme** from the author field — never written into the body | §4.4 |
| 3 | **Direct 40–60 word answers under question H2s** | Featured-snippet + AI-Overview eligibility. One clean liftable answer per section | §4.2 |
| 4 | **Topical authority** | 3+ internal links to related {{BRAND}} posts, varied anchors (<30% exact-match), semantic coverage | §4.5 |
| 5 | **Freshness + substantive change** | `dateModified` current, current-year framing where natural, post-2022 sources. Must be a *real* update | §4.1, §5.2 |

---

## 3. The authoring workflow (execution order)

**Brief → Skeleton → Draft → Meta → Score.** Each step is procedural and points to the reference specs in §4;
it does not restate them.

### 3.1 Step 1 — SERP brief (run BEFORE building anything)

Read the **live** top-ranking pages for the primary keyword and produce a brief the skeleton must satisfy:

- **Intent** — informational / commercial / transactional / navigational. Match the post type to it.
- **Dominant format** of the top 5–10 — how-to / listicle / comparison / definition / tool. Match it.
- **Required subtopics** recurring across top results → these become the H2s (as real queries). Off-intent
  H2s are a fail.
- **SERP features** — featured snippet (note its format), PAA, AI Overview, image/video pack.
- **PAA → FAQ** — harvest 3–5 People-Also-Ask questions as the FAQ + section-lead answers.
- **Featured-snippet target** — plan the lead answer (40–60 words) in the snippet's format.
- **Word count** — pick the target band for the content type (§3.2). Top-results length is a sanity check for
  completeness, not the rule.
- **Table** — if the top results use a data/comparison table, include one.
- **Differentiation angle** — what the top results miss that {{BRAND}} can add (first-hand data, the
  {{PRODUCT}} angle).

**Keyword research (part of the brief):** identify the **primary keyword**; research volume + difficulty;
analyze the top-10 competitors; identify **3–5 secondary/related keywords**; list semantic/LSI terms.

Build the skeleton from this brief and validate against it before writing.

### 3.2 Step 2 — Skeleton (heading hierarchy, template, length)

**Heading hierarchy**
- **H1 (title):** one per article; primary keyword natural and near the start; ≤60 chars (SERP display);
  benefit-focused (answers "what will I gain?"); intent-matched, not merely catchy.
- **H2 (main sections):** 4–7 total; ≥2–3 include keyword variations; descriptive; logical progression;
  standalone-readable (the flow makes sense from the H2s alone). Phrase per §4.2 (questions where the subtopic
  is question-intent; ≥50% questions overall).
- **H3 (subsections):** nested under H2 — never skip H2→H4; break complex sections into digestible chunks;
  more specific than the H2.

**Article skeleton** (composition rules for each part live here — one home)
```markdown
# H1 — benefit-focused, intent-matched title with the primary keyword

[Intro — ANSWER-FIRST]  First 1–2 sentences directly answer the core query the searcher typed — no
scene-setting, no "in today's world", no throat-clearing. Then hook → problem → promise. Primary keyword in
the first 100 words. (Answer-first is AEO-critical: context comes AFTER the answer.)

> **Key Takeaways (TL;DR)** — 4–6 plain-language bullets summarizing the key answers/takeaways (what the
> reader will learn + do), one idea per bullet. Weave a number in only where it supports the point. A reader
> who reads ONLY the TL;DR should grasp the argument. It is a SUMMARY, not a stat dump. Place above the fold,
> after the intro, before the first H2.

## H2 — main section (phrased per §4.2)
40–60 word liftable lead answer (§4.2), then depth / examples / data.
### H3 — subsection if needed
## H2 — main section …            [4–7 H2s; ≥2–3 carry keyword variations; ≥50% question-phrased]
## FAQ                             [5 Q&As — see §4.2 for the full FAQ spec]
## Close — forward-looking next step + ONE specific CTA (the relevant {{PRODUCT}} + demo link).
                                   NOT a recap. "In conclusion, we covered…" is banned. The CTA block IS the
                                   deliberate, allowed ending.
```

**Content length — fixed target bands by content type**
- Standard blog post: **1,500–3,000** words (target 2,000–2,500)
- Pillar / comprehensive guide: **3,000–5,000** (max)
- How-to guide: **1,500–2,500**
- News / update: **800–1,200** (exception to the standard)

Aim for the **lower end** when you can — concise, focused content often performs better. If a topic needs more
than the max, **split it into a series.** The band is a target, not a licence to inflate: never pad to hit a
count. Better 2,000 valuable words than 3,000 padded — density (claims/stats/citations) is the real goal.

### 3.3 Step 3 — Draft to standard

Write the body, applying the levers in priority order (§2.2) and meeting every dimension bar in §4. Two
drafting concerns own their home here:

**Keyword placement in the draft** — the primary keyword should appear in: the H1 (near the start) · the
first 100 words · 2–3 H2s · the conclusion · (plus the meta fields + slug, handled in §3.4). Write for humans
first: use variations, not robotic repetition; include conversational/question forms; support with
semantic/related terms for topical authority.

**No density quota.** Keyword-density percentages are dead — stuffing is penalized. Optimize for semantic
coverage (§4.1 topical authority), not a percentage.
- ❌ "Skills testing is important. Skills testing helps teams. Our skills testing platform offers skills
  testing for skills testing needs."
- ✅ Write naturally, with related terms.

### 3.4 Step 4 — Meta

**Meta title** — 50–60 chars (incl. "| {{BRAND}}" if used); primary keyword included; compelling; unique
across the site; accurate to the page.
- Formats: `[Primary Keyword]: [Benefit]` · `How to [Goal] | [Qualifier]` · `[Number] Ways to [Benefit]` ·
  `[Topic] Guide for [Audience] | {{BRAND}}`.
- ✅ "How to Run Skills Assessments in 2026: Complete Guide"  ✅ "12 Proven Pre-Hire Testing Strategies | {{BRAND}}"
- ❌ "Hiring Tips and Tricks" (vague, no keyword)  ❌ a 90-char everything-title.

**Meta description** — **140–160 chars, never >160** (Google truncates ~155–160). Lead with the primary
keyword **and** the core value/intent term directly (e.g. "reduce time-to-hire", "cut cost-per-hire", "ROI") —
not a vague benefit line. Include a CTA verb (Learn, Discover, Get). Complete sentence, unique per page.
- Formula: `[Problem/Question]? [Solution/Benefit]. [Unique angle]. [CTA].`
- ✅ "Cut time-to-hire with role-based skills assessments. See how {{BRAND}} scores candidates objectively and
  reduces mis-hires. Book a demo."
- ❌ "This post discusses hiring and assessments." (no keyword/value/CTA).

**URL slug** — include the primary keyword; lowercase; hyphens (not underscores); short (3–5 words); drop
stop-words unless needed. Format `/blog/[primary-keyword-phrase]`.
- ✅ `/blog/skills-assessment-guide`
- ❌ `/blog/how-to-run-a-skills-assessment-in-2026-the-complete-guide` (too long).
- Slug governance (keep vs change, 301s) → §5.1.

### 3.5 Step 5 — Score & gate

Run the master checklist (§6) and the scoring rubric (§7). **Publish when Overall ≥ 80** with no P0 failures.
Rework the lowest-scoring items and re-score, **cap 3 passes**; if it still can't reach 80 without fabricating
or padding, ship it as a **draft** and report it.

---

## 4. The quality bar — reference specs (each rule stated once)

### 4.1 Google 2026 ranking bar

**Helpful Content (HCU)** — people-first writing; first-hand experience shown; original insight not available
elsewhere; specific numbers + named entities; author credibility visible; single-topic focus; **no
scaled/templated/thin content.** Canonicalise duplicate content.

**AI Overview eligibility** (50%+ of SERPs in 2026) — clear topic definition in the first 100 words;
listicle/structured format; **citation density 4+ inline** (lever 1); brand mention 3–5× natural; direct
factual claims with cited sources; Q&A at section breaks; no hedging; `dateModified` ≤6 months.
> In-body density (stats/quotes/citations) drives eligibility — **not markup.** Schema gives ~zero independent
> AI-citation lift (see §5.3).

**Featured snippet** — a 40–60 word answer in the first 200 words; paragraph/list/table matching the current
SERP format; question phrasing in the H2 above the answer; definition box for "what is", comparison table for
"X vs Y". (Answer mechanics: §4.2.)

**Site reputation** — no scaled-content site references; no parasitic subdomains.

**Core Web Vitals (INP)** — avoid heavy inline images; keyword-aware alt text (§4.6).

**Topical authority** — 3+ internal links to related {{BRAND}} posts; internal anchor varies (no exact-match
>30%); **semantic coverage:** include related subtopics, entities, and semantic keywords — not just the exact
keyword. (Linking mechanics: §4.5.)

**Freshness** — current year in the title where natural; `dateModified` updated quarterly minimum; current-year
data + post-2022 sources only. (Refresh rules: §5.2.)

**Conclusion / close** — forward-looking next step + one specific CTA, **not a recap.** Recap-style wrap-ups
and "In conclusion, we covered…" are banned. The CTA block is the deliberate, allowed ending. (Skeleton: §3.2.)

### 4.2 AEO — the liftable answer

- **Answer immediately** in the first sentence below the heading, **40–60 words**, especially under question
  H2s. Follow with a numbered list (steps) or a table (comparison).
- **Phrase H2s as real search queries** — questions where the subtopic is question-intent, concise keyword
  phrases otherwise. Keep the core answer-target sections as questions (**≥50% of H2s**), phrased how people
  actually search. Don't force every heading into a question.
- Conversational, jargon-free tone; sentences readable aloud in <10 seconds.

**Featured-snippet formats** (match the format the live SERP rewards — §3.1)
- **Question snippet:** question as the H2, then a concise 40–60 word answer immediately after.
- **List snippet:** numbered/bulleted, 5–8 items, each 1–2 sentences.
- **Table snippet:** markdown/HTML table for comparisons, pricing, specs; clear headers.
- **Definition snippet:** define the term in the first sentence after the heading (40–60 words), then expand.

**FAQ** (one home for the full spec) — **5 Q&As.** Write the questions in natural prompt language (how people
ask an AI); source them from real research (PAA, Reddit, YouTube comments — §3.1). Answer directly in the
first sentence, then expand. Render as an accordion for **UX only** — expect no snippet or ranking lift from
FAQ schema (§5.3).

### 4.3 GEO — become a source AI trusts enough to cite

- Include **≥1 original/proprietary stat** (your own first-party data or a named scenario) **where available** —
  aspirational (a GEO booster), **not a hard gate**: most articles won't have one, and that's fine.
- Write **quotable, self-contained sentences** that make sense out of context. Precise numbers, dates, named
  entities — vague claims are not cited. Lead each section with its most citation-worthy claim.
- Structured formats: tables, numbered lists, definition lists. Cover the topic exhaustively; anticipate
  follow-ups. **Original frameworks / named methodologies** — named things get cited.
- Author credentials clear: name, title, years, certifications (rendering: §4.4).

**E-A-T in practice**
- *Expertise:* accurate, detailed info; back claims with data + examples; give actionable advice.
- *Authoritativeness:* cite credible sources; reference industry data/trends; use expert quotes; leverage
  {{BRAND}}'s position.
- *Trustworthiness:* transparent and honest; acknowledge limitations; don't overpromise; cite every stat;
  update outdated content.

**Originality & factual accuracy**
- Never plagiarize — all content original; add a **unique angle** vs competitor content; use fresh, current
  examples and the most-recent data available.
- Verify every statistic and data point; ensure processes/practices are current; keep terminology and
  **{{BRAND}} product references accurate.**

### 4.4 E-E-A-T & citation integrity

**Author & authority signals** — render via the **theme-native author field / frontmatter, NEVER authored into
the body:**
- Named author (never "Team") with bio + credentials + LinkedIn + years; the author has 3+ prior posts in the
  same topic area.
- A "Reviewed by [name, title]" editor credit where possible; a visible last-updated date; an
  expert-verification note where applicable; the current year in the title for time-sensitive topics.
- First-hand markers in the body: "In my work with…", "A pattern I keep seeing…".
- `datePublished` + `dateModified` visible; Organization schema linked.

**Cite credible primary sources** — .gov, .edu, peer-reviewed, original research, and recognised
industry/analyst research. **No fixed allow-list** — judge each source on credibility + freshness (prefer the
most recent primary). **Never a competitor** (below).
- **NEVER cite or link a direct competitor** (list: `02-asset-engine/competitor-study/output/competitors.md`;
  auto-enforced upstream by the research-structure filter). If the only source for a stat is a
  competitor, drop the stat or use a neutral primary. Critique competitor approaches **generically, never by
  name.**

**Citation integrity (P0)** — every stat links to its SPECIFIC source (the report/page, not a category hub),
returns 200, and the year matches; no stat uncited, none repeated; verify each figure (entity + number + year)
by web search, never from memory; aim for **≥2–3 distinct citation domains** per post.

**Stat freshness + precise framing** — prefer the most recent primary figure; if you keep an older-but-canonical
stat, attribute its correct year (don't imply it's newer). Frame ranges/sub-segments to match the source's
exact wording, not a convenient rounding.

### 4.5 Linking

**Internal** *(dofollow)*
- **≥3 internal links** to related {{BRAND}} posts (optimal 4–5; ceiling ~7 unless a 3,000+ word piece).
- **Anchor text:** descriptive + keyword-aware ("our guide to structured interviews"), natural in flow;
  **vary anchors — no exact-match >30%**; never "click here" / "read more".
- **Placement:** within body paragraphs, natural context; ≤2 links per paragraph; distributed, not clustered.
- **Link types:** related blog posts (2–3); one **product/feature page** when contextually relevant (natural
  {{PRODUCT}} mention, never forced); a resource page (template/tool/checklist) when mentioned.

**External / citations**
- **≥2 external links** (optimal 3–4) to authoritative primary sources (credible .gov/.edu/peer-reviewed/original/industry research; never a competitor) — cite
  statistics/data, research/studies, recommended tools, industry authorities.
- **Quality bar:** credible, well-known sources only; relevant and directly supporting the claim; recent (data
  within 1–2 years); all links functional. Citation integrity (P0) + never-cite-a-competitor govern — §4.4.

**rel policy** — internal = **dofollow**; editorial citation = **`nofollow noopener`**; paid/partner/affiliate =
**`sponsored`**; UGC = **`nofollow`**. Never ship a paid link as dofollow.

### 4.6 Page-craft — readability, images, mobile

**Readability**
- Write for a professional {{AUDIENCE}} — precise, not dumbed-down, but never needlessly dense (target
  ~8th–10th grade Flesch-Kincaid for accessibility).
- **Sentences:** ~15–20 words average; max ~25 (split longer); mix short + long; **80%+ active voice.**
- **Paragraphs:** 2–4 sentences, one idea each; white space; mobile-friendly.
- **Scannability:** a subheading every ~300–400 words; lists for sequences/multiples; bold key takeaways.
- **Transitions:** ~one per paragraph (Additionally, However, Therefore, For example, First/Next/Finally).
- **No horizontal dividers in the article body.** Never `<hr>`, a markdown `---` rule, or a `wp:separator`
  between sections, tools, FAQs, or pros/cons. Separate with heading hierarchy (H2/H3/H4), spacing, lists, and
  tables only — dividers read as AI-generated, add whitespace, and hurt mobile flow. Aim for clean editorial
  flow (HubSpot / SHRM / McKinsey / Gartner).

**Images**
- Relevant, high-quality, compressed (fast load), mobile-friendly.
- **File names:** descriptive + keyword-rich (`skills-assessment-dashboard.jpg`, not `IMG_1234.jpg`).
- **Alt text:** describe what the image shows (accessibility + SEO); keyword natural; ≤125 chars.
- **Placement:** break up long text; illustrate the concept *after* explaining it.

**Mobile** (Google indexes mobile-first)
- Short paragraphs (2–3 sentences); heavy subheadings/lists; readable fonts; tap-friendly link spacing; fast
  loading (optimized images).

### 4.7 AI-search extras

AI search (ChatGPT / Perplexity / Gemini / Claude) is a real channel — roughly **5–15% of site traffic** can
come from AI sources, and most buyers consult AI before deciding. Most of it is covered by the levers (§2) and
§4.2–§4.4. The extras worth keeping:

- **One idea per section** — AI parses by section; a single concept per H2/H3 raises the chance the section
  gets cited. Avoid paragraphs that blend topics.
- **Embedded media** — embed ≥1 relevant YouTube video where it adds context (cross-validation for
  Perplexity/Gemini, time-on-page signal). Prefer your own, then an authoritative third party.
- **Repurposing surface** — AI pulls from Medium, LinkedIn, Reddit, Quora, YouTube transcripts; the more
  surfaces the content appears on (with attribution back), the higher the AI-recommend chance. *(Owned by a
  `/repurpose` step, not this file.)*
- **AI citation audit** — for competitive topics, audit which sources AI actually cites (prompt-based) and
  target those surfaces. *(Owned by the `ai-citation-targets` file + a `/research-ai-citations` step, not this
  file.)*

---

## 5. Governance

### 5.1 URL / slug policy + 301 redirects — REMOVED (not applicable)

This pipeline writes **new** articles only; it never rewrites or re-slugs existing pages, so slug/301 governance
doesn't apply. (How to *choose* a new article's slug is a write-phase concern — see the write-phase plan.)

### 5.2 Content refresh

- **When to update:** 12+ months old · outdated stats/data · changed best practices · a competitor surpassed
  us · rankings declined · new relevant info.
- **What to update:** the "Last Updated" date · stats with current data · screenshots · examples/case studies ·
  SEO elements (keyword focus may have shifted) · internal links to newer content.
- **Scaled-content guardrails (Google, per page):**
  - *Human value gate:* every updated page must add net-new value; if you can't name what improved, don't
    publish.
  - *Substantive-change minimum:* new data, new sections, corrected claims, restructured answers.
  - *Cosmetic-only = HARD STOP:* a date bump / typo fix / image swap alone is **not** a refresh.
  - *Pace publishing:* don't mass-deploy refreshed pages in one burst.
  - *Disclose AI use* where non-obvious, per editorial policy.

### 5.3 Low / no SEO lift — don't RELY on these for ranking (but building them is fine)

These give little-to-no independent ranking lift. **We still build the harmless ones** (FAQ/schema markup,
etc.) — they cost almost nothing, aid UX, and there's no downside; just don't count on them to rank. The
**penalised** ones (stuffing, density, spammy anchors) we genuinely avoid.

| Item | SEO reality | Our stance |
|---|---|---|
| FAQPage / HowTo / Speakable schema | No rich result for general sites since Aug 2023 | **Build it anyway** (cheap, aids parsing/UX) — just don't expect a ranking lift |
| Schema for AI citations | ~0 independent lift | **Build it anyway** — citations really come from in-body stats/quotes/sources (lever 1) |
| `llms.txt` | No AI engine reads it | Optional — harmless if added, don't spend real effort |
| Keyword stuffing / exact-match anchor spam | **Penalised** | **Avoid** — natural keyword + varied anchors |
| Keyword-density % target | **Penalised**; obsolete | **Avoid** — semantic coverage (§4.1) instead |
| "Longer ranks higher" | False | Target band for the type (§3.2); density over volume |
| Cosmetic-only "refreshes" | Scaled-content abuse | Substantive change or don't touch (§5.2) |

---

## 6. Master pre-publish checklist (the gate)

> **This checklist is extracted, standalone, into `seo-aeo-geo-checklist.md`** — that file is the per-company
> ship artifact (copied to `projects/<company>/01-brand-context/`). This full standard STAYS in
> workflows as the reasoning behind it. The two are kept in sync; edit the checklist file, mirror the change here.

**Content** · [ ] length within the target band for the type (not padded) · [ ] primary keyword identified ·
[ ] 3–5 secondary + semantic terms · [ ] unique value vs competitors · [ ] factually accurate + current ·
[ ] no scaled/thin content · [ ] duplicate content canonicalised.

**Structure** · [ ] one H1 w/ keyword · [ ] 4–7 H2s, 2–3 with keyword variations · [ ] H1>H2>H3 hierarchy ·
[ ] keyword in first 100 words + conclusion · [ ] answer-first intro · [ ] TL;DR block · [ ] no body dividers ·
[ ] (soft — include if it fits, not compulsory) a data/comparison table where the topic warrants one.

**Meta** · [ ] title 50–60 chars w/ keyword · [ ] description 140–160 chars w/ keyword+value+CTA · [ ] slug has
keyword · [ ] all meta unique + intent-matched.

**Links** · [ ] ≥3 internal, varied descriptive anchors (<30% exact) · [ ] ≥2 external primary sources, linked ·
[ ] rel policy applied · [ ] no competitor cited · [ ] all links 200 · [ ] one internal link to a product/feature page where natural (reverse-silo).

**AEO / GEO** · [ ] direct 40–60w answer under question H2s · [ ] ≥50% H2s are questions · [ ] 4+ inline
citations · [ ] FAQ = 5 Q&As (prompt-language, direct-answer) · [ ] quotable
self-contained sentences · [ ] ≥1 embedded video · [ ] one idea per section · (bonus, not a gate) ≥1 original/proprietary stat.

**E-E-A-T** · [ ] theme-native author box (not body) · [ ] named author + credentials · [ ] datePublished +
dateModified visible · [ ] first-hand markers · [ ] citation integrity (P0) verified.

**Readability / Images** · [ ] 15–20w sentences, 2–4-sentence paragraphs, 80%+ active · [ ] subheading every
~350w · [ ] images relevant, compressed, keyword-aware alt + descriptive filenames.

**Quality** · [ ] no spelling/grammar errors · [ ] sources cited · [ ] brand voice maintained (see
brand-voice.md) · [ ] actionable value delivered.

**Ship** · [ ] Overall score ≥ 80 (§7) · [ ] no P0 failures · [ ] close = forward next step + 1 CTA (not a
recap).

---

## 7. Scoring rubric

Score each post 0–100 across five dimensions; **publish when Overall ≥ 80.**

```
Overall = SEO ×0.25  +  Structure ×0.15  +  Content ×0.25  +  EEAT ×0.15  +  AEO/GEO ×0.20
```

A **P0 checklist failure caps Overall below threshold** until fixed. Rework the lowest-scoring items and
re-score, **cap 3 passes**; if it still can't reach 80 without fabricating or padding, ship as a **draft** and
report it.

---

## 8. Tools & resources

- **Keyword research:** DataForSEO (wired in), Ahrefs, SEMrush, Google Keyword Planner.
- **Content analysis:** Clearscope, Surfer SEO, MarketMuse.
- **Readability:** Hemingway, Grammarly.
- **Technical:** Screaming Frog, Google Search Console.
- **Rank tracking:** GSC, Ahrefs.
- **Reference:** Google Search Quality Evaluator Guidelines, Moz Beginner's Guide, Backlinko, Search Engine
  Journal.