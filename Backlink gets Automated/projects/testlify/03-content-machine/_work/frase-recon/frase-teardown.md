# Frase — full product teardown (from 4 captured workflows)

> **Source:** 4 Tango screen-recordings you captured, reconstructed click-by-click from Tango's embedded JSON
> (every clicked element's real UI text + the page URL). Raw transcripts: `01-…` to `04-…` in this folder.
> App lives at **`next.frase.io`**. Purpose of this doc: capture *everything* Frase does so we can borrow the
> good parts and confirm where we differentiate. `[fillable]` = user inputs it · `[auto]` = Frase generates it.

---

## 0. What Frase is (one paragraph)
A **"content operating system"** that runs the whole lifecycle on `next.frase.io`: onboard a site → **audit** it →
track **site health + AI visibility** → build a **brand knowledge base (Brand Hub)** → research a topic into a
**GEO/AEO content brief** → generate the article → gate it on **quality rules** at publish. It has productized
**GEO/AEO** (AI-citation optimization) far more than we have, and it *does* carry an **evidence layer** (stats +
citations) in its brief — but that evidence is **aggregated from the ranking SERP**, not original/first-party.

---

## 1. The module map (every page seen, by URL)

| Module | URL | What it does |
|---|---|---|
| **Onboarding** | `/onboarding` | Enter a website → auto-analyzes content, target audience, competitors, opportunities (1–2 min) → "Create Workspace & Start Audit" |
| **Auditor** | `/auditor` | Technical + content SEO audit; issues by severity; auto "Fix Pack"; internal-link authority; CSV export |
| **Site Health** | `/site/health` | Health score, Technical Health %, GEO Health, Top Performers, "Intelligence Report" narrative |
| **Issues** | `/site/issues` | All issues as a list/board |
| **SEO Analytics** | `/analytics` | Connect Google Search Console |
| **AI Visibility** | `/ai-visibility` | Tracks how AI platforms (ChatGPT/Perplexity/etc.) surface your content + competitors |
| **Competitive Analysis** | `/competitive-analysis` | Paste a competitor URL → Analyze |
| **Brand Hub (Brand DNA)** | `/brand-dna` | Brand knowledge base + governance (voice, terms, docs, templates, rules, playbooks) |
| **Research** | `/research` | The brief-builder: topic → keywords + SERP + questions + **evidence** + GEO → brief |
| **Opportunities** | `/content/opportunities` | Content-gap opportunities, blind spots, competitor gaps, uncovered topics |
| **Clusters** | `/content/clusters` | Topic-cluster management |
| **Content** | `/content`, `/content/new`, `/content/create` | Article library + article generation from brief/playbook |

---

## 2. Workflow 1 — Run SEO Audit (`/auditor`, `/site/health`, `/ai-visibility`)

**Onboarding `[fillable]`:** your website URL. Frase then `[auto]` detects: target audience (it pulled *"Talent
acquisition teams, hiring managers, HR leaders at fast-scaling startups & enterprise (Shell, Apollo, NSE)"*),
key facts (*"3,500+ validated tests"*), competitors → "Create Workspace & Start Audit."

**Auditor:**
- **Audit-pages credit:** metered — "A 50-page audit uses 50 audit pages. Resets monthly." (a plan limit)
- **Issue types found** (each with severity **Critical / High / Medium / Low / Warning / Info**): Missing Viewport
  Meta, Missing Open Graph Tags, Missing OG Image, Orphan Page, Keyword Cannibalization (detected / "none"), No
  FAQ schema markup, "Content lacks clear definitions", missing/duplicate meta descriptions & H1s.
- **Fix Pack `[auto]`:** "Generate Full Fix Pack" / "Generate All Fixes" — auto-writes the fixes (e.g. the missing
  viewport/OG tags). "+7 more actions available."
- **Internal Link Authority:** Avg Authority Score · Top Authority Pages · **Orphan Pages** (nothing links to them)
  · **Dead-End Pages** (no outgoing links). ← this is their internal-linking intelligence.
- **Export → Download CSV.** Per-page "Summary". "View all 152 info issues."

**Site Health / Intelligence Report `[auto]`:** narrative like *"audit of 49 pages, avg health score 85, 0 critical,
93 warning-level items… +37-point uplift by resolving the top 7 issues (0 critical, 6 high, 0 medium, 1 low)."*
Tabs: Technical Health (57%), Top Performers, **GEO Health**, Site Health.

**SEO Analytics:** Connect Google Search Console. **AI Visibility:** "Gathering visibility data" — AI-platform
surfacing. **Competitive Analysis:** paste competitor URL (they pasted `testgorilla.com`) → Analyze.

---

## 3. Brand Hub / Brand DNA (`/brand-dna`) — the knowledge base + governance engine

This is Frase's version of *our context files*, and it's deep.

- **Brand Profile `[fillable, auto-seeded]`:** description, tagline (*"Know Who Can Actually Do the Job Before You
  Hire Them"*), category (*"B2B SaaS for skills-based pre-hire assessments"*), positioning (*"Mid-market to
  Enterprise specialist…"*), brand name, product line.
- **Assets** (`section=assets`): Identity & Logos.
- **Competitors** (`section=competitors`): tracked competitor set (feeds gap analysis).
- **Governance** (the rules/templates engine, `section=governance`):
  - **Brand Voice** (`tab=voice`) — searchable brand-voice profiles.
  - **Terminology** (`tab=terms`) — term rules (preferred/banned terms), "All Types."
  - **Reference Docs** (`tab=docs`) — reference documents that shape briefs.
  - **Templates** (`tab=templates`) — content-structure templates (§4).
  - **Rules** (`tab=rules`) — quality rule sets / publish gate (§5).
  - **Playbooks** (`tab=playbooks`) — multi-step content pipelines (§6).

---

## 4. Templates (Brand Hub → Governance → Templates)

Pre-built **section-structure templates**, one per content type. Seen (plan shows "2/5" → limit on custom ones):

| Template | First section (H2) shown |
|---|---|
| **Blog Post** | (generic headings) |
| **Product Review** | Introduction |
| **How-To Tutorial** | Introduction |
| **Listicle (Top N)** | Introduction & Selection Criteria |
| **Case Study** | The Challenge |
| **Comparison Post** | Introduction & Comparison Criteria |
| **Quick Start Guide** | Prerequisites |
| **Pillar Page Hub** | What Is [Topic] |
| **Feature Announcement** | Headline & Hook |

Each template = an ordered list of **Headings (H2s)**, and per heading you set `[fillable]`: **Content Type**,
**Level** (H2/H3…), **Required** (toggle). You can **copy** ("Product Review (Copy)"), edit, cancel. → *This is
exactly our "recommended outline / format playbook" idea, productized as reusable per-type skeletons.*

---

## 5. Rules / Rule Sets (Brand Hub → Governance → Rules) — the Publish Gate

Quality gates evaluated automatically at publish. Pre-built **rule sets**: **Publish-Ready**, **AI Citation
Ready**, **Quality Baseline**. Each rule has `[fillable]`: a **Score Threshold** ("Require minimum SEO or GEO
score"), a Description (optional), and a **severity** (e.g. WARNING). "Create Rule Set" = *"Group related checks
into a rule set. Rules are automatically evaluated when you publish content — passing rules are shown in the
**Publish Gate**."* → *Frase's version of our quality-score gate, but with a distinct **GEO** score alongside SEO.*

---

## 6. Playbooks (Brand Hub → Governance → Playbooks) — configurable pipelines

Multi-step content **workflows** = *Frase's orchestration, mirroring our research→write→QA.* Pre-built:
**SEO Blog Post · Product Page · Comparison Article · Listicle · Quick Update**. "New Playbook from Template."

Each playbook = ordered **Steps**, each with `[fillable]` a **Step Type / Action** + **Instructions (optional)**.
Step types seen: **Research Topic · Create Brief · Get Content · Quality Check** (with "Instructions for the
reviewer") · **Quick Update**. So a playbook literally chains: Research Topic → Create Brief → Get Content →
Quality Check. Name `[fillable]`.

---

## 7. Workflow 3+4 — the Research → Brief → Article engine (most relevant to us)

### 7a. Research (`/research`) — "Build a Brief from a Topic"
A guided wizard. `[fillable]` inputs, step by step:
1. **Target topic** (the query analyzed "across the SERP and LLMs").
2. **"What should this piece accomplish?"** — the goal (they typed *"lead generation"*).
3. **Audience** (they typed *"HR professionals"*).
4. **Language & market** (🇺🇸 English US).
5. **Brand voice** — "Reuse your Brand Hub voice" (shows *how many term rules + reference docs will shape the
   brief*). → "Start research."

Then `[auto]`: *"Running keywords, SERP, gaps, and evidence together"* (one pass). Results, organized as **Steps**:
- **Recommended keywords** — with **Keyword difficulty**, **Keyword Opportunities**.
- **Recommended headers** — the H2 structure, pulled from ranking competitors (e.g. `testlify.com`).
- **Visitor Questions** — the PAA/question set.
- **Suggested for Evidence & Opportunities** → **EVIDENCE** blocks = *statistics with inline citations*, e.g.
  *"Job descriptions: 81% use skills-based practices when creating job descriptions [4]."* Plus **AI Opportunity**
  and **Strong signal** tags, with **Citation Sources** and **Details**.
- **SERP competitors** — "Open SERP"; lists the actual ranking articles (e.g. *"65 key skills-based hiring
  statistics for 2026"*, *"Recruitment Statistics 2026: 155 Verified Stats"*).
- **AI Visibility → AI Platform Analysis** — *"How AI platforms surface content and competitors for [topic]. Use
  these insights to shape your brief for GEO and AEO."* (STRONG SIGNAL / Details / Citation sources).
- **Opportunities** — **Blind Spots · Content Gap Opportunities · Uncovered Topic · Competitor Gap**.

→ **So Frase's brief = keywords + SERP headers + visitor questions + EVIDENCE (stats w/ citations) + AI/GEO
analysis + gap opportunities.** It's *the same brief we're building* — and it already includes an evidence layer.

### 7b. Content / Article generation (`/content/new` → `/content/create`)
"New Content" → "How can I help you today?" → **OR START FROM A PLAYBOOK** → **Generate Article**.
- Paste topic → "Generate article" → **QUERY** → "Approve and continue" → "Switch to Data Report" → "Quick check
  before generating" → **Generate** → *"Running keywords, SERP, gaps, and evidence together."*
- **Set-up fields `[fillable]`:** **Content type · Content focus · Article length · Brand voice · Language &
  market · Smart context** → "Approve and continue" → **Write**.
- The generated **brief/outline** carries: **Topic**, the **keyword set** to target, the **SERP structure +
  audience questions**, the **AI-platform analysis** (who keeps getting cited), and **Evidence**.
- Per-section metadata `[auto]`: each section has **What the reader wants · What makes this different** and a
  **purpose line**, e.g. *"Provide a high-density data section that anchors the report's credibility,"* *"ensure
  EEAT compliance,"* *"Full list of sources to drive GEO 'citations' scoring and reader trust."*
- Example generated report sections: Executive Summary · high-density data section · The AI Fraud Crisis (with
  **STAT** blocks) · methodology comparison (business case) · deployment detail · technical foundation (EEAT) ·
  **References and Citations / Sources**.
- **Export** at multiple points (brief, data report, article).

---

## 8. What's fillable vs auto (quick reference)
- **Fillable:** website URL · topic · goal · audience · language/market · brand voice selection · content type ·
  content focus · article length · brand profile fields · terminology rules · reference docs · template headings
  (+Content Type/Level/Required) · rule-set score thresholds + severity · playbook steps + instructions.
- **Auto-generated:** the audit + issues + Fix Pack · site-health/intelligence narrative · AI-visibility data ·
  recommended keywords/headers/visitor-questions · **evidence (stats + citations)** · SERP competitor list · GEO
  analysis · gap opportunities · the outline with per-section purpose · the drafted article · scores (SEO + GEO).

---

## 9. What to steal (and what confirms our edge)

**Borrow (genuinely good ideas):**
1. **The Brand Hub governance model** — Voice + Terminology + Reference Docs + Templates + Rules + Playbooks is a
   clean way to organize *our* context files + orchestration. Especially **Terminology** (preferred/banned terms)
   and **Reference Docs** "shaping the brief."
2. **Per-section purpose lines** — every H2 carries *what the reader wants · what makes this different · its job*
   ("anchor credibility with data", "ensure EEAT"). Adopt directly into our recommended-outline (Stage 3).
3. **A distinct GEO score + "AI Citation Ready" rule set** — they treat GEO as a first-class, separately-scored
   thing with its own publish gate. Our AEO is weaker; worth productizing this way.
4. **Templates as per-content-type skeletons** with Required flags — our "format playbooks," formalized.
5. **Playbooks = Research Topic → Create Brief → Get Content → Quality Check** — validates our stage pipeline.
6. **Internal-link authority (Orphan / Dead-End pages)** — a concrete internal-linking intelligence for the audit.

**Confirms our differentiation (where Frase stops):**
- Its **EVIDENCE is aggregated from the ranking SERP** (stats other articles already cite) — i.e. *synthesis of
  what's already out there*, **not original or first-party data.** That's exactly the "me-too evidence" ceiling.
  Our **Evidence Engine** (first-party Testlify data + micro-research + original synthesis) is still the unclaimed
  moat — Frase proves even the best-funded tool doesn't cross that line.
- It optimizes toward **matching the SERP** (scores vs top-rankers) → structurally nudges toward parity, same as
  Surfer/Clearscope.

**Net:** Frase is a *more complete commodity platform* than we have (audit + health + AI-visibility + governance +
publish gate), and we should borrow its **structure/governance/GEO-scoring** ideas — but it does **not** manufacture
distinctness, which remains our reason to build.
