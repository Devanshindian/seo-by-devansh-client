---
type: workflow-recipe
stage: content-machine (Stage 0 — brand context)
reusable: any company
reads:
  - projects/[company]/00-foundation/output/content-database.csv   # ALL page URLs (to discover) + each page's Full content (facts)
  - projects/[company]/01-brand-context/brand-voice.md          # so the pitch/messaging wording stays on-voice
produces:
  - projects/[company]/01-brand-context/features.md             # the product features / benefits / differentiators doc
last_updated: 2026-07-03
---

# Features — build workflow

> **Where this lives:** this recipe lives at `Backlink gets Automated/workflows/03-content-machine/`. It
> reads the content database, the brand-brain evidence table, and `brand-voice.md` from
> `Backlink gets Automated/projects/[company]/…`, and writes `features.md` to `projects/[company]/03-content-machine/`.

---

## What this does

Turn a company's **real product pages** into a complete `features.md` — its value propositions, technical
features, integrations, competitive differentiators, use cases, pricing, conversion messaging, and objection
answers — so the writer can make **accurate product mentions** in content. Same shape and depth as the Castos
reference (Appendix B).

This is a **facts** document. Its whole value is accuracy.

---

## The one rule

**Every fact in `features.md` comes from a real page. Nothing is invented.**

(If a fact isn't on a page, flag it — don't make it up. The Castos file is a reference for *how thorough* to be,
never something to copy from.)

---

## What you produce (named output of each step)

| Step | Produces |
|------|----------|
| 1. Discover the commercial/product pages (chunk all content-database URLs → sub-agents) | **`_work/features-source-pages.md`** — the list of relevant pages, by kind |
| 2. Collect the product facts (~7–10 sub-agents in parallel, each a batch of pages) | **`_work/features-facts.md`** — the raw facts pool |
| 3. Fill the schema section by section (pure assembly) | **`features.md` (draft)** |
| 4. Quality gate vs the Castos bar | **pass/fail + redo instructions** (loops back to 1/2) |

---

## Inputs

- **`content-database.csv`** — every page on the site: its `URL` (used in Step 1 to *find* the commercial pages)
  and its `Full content` (used in Step 2 for the facts).
- **`brand-voice.md`** — so the written pitch lines (Conversion Angles, trial messages) sound on-brand.
- **Appendix A** — the raw schema to fill. **Appendix B** — the Castos reference (depth bar only).

---

## The steps (in order)

### Step 1 — Discover the commercial/product pages (from the URLs only)
**What it does:** finds, out of the whole content database, which pages actually describe the product — its
pricing, plans, features, integrations, and competitor comparisons — **judging from the URL/slug alone, no fetching.**

**Process:**
1. Pull **all** `URL`s from `content-database.csv`.
2. Split the URLs into **chunks of ~200–300**. Spawn **one sub-agent per chunk** with the prompt below —
   **filling `<COMPANY_ONE_LINER>` from `brand-voice.md`** so each sub-agent judges relevance for *this*
   company/industry, not a fixed list.
3. Each sub-agent reads its chunk of URLs and returns only the **commercial/product** ones, each labelled by kind.
4. Collect and **de-duplicate** the returns into **`_work/features-source-pages.md`** — the master source list.

**The exact sub-agent prompt (send one per chunk):**
```
Classify a chunk of one company's page URLs — from the URL/slug ONLY. Do NOT fetch any page.

The company: <COMPANY_ONE_LINER> (what it sells / who it's for). Judge relevance for THIS company and industry.

Return ONLY the URLs that are COMMERCIAL / PRODUCT pages for this company — pages that describe what the product
IS, what it does, what it costs, who it's for, or what it integrates with. Label each by kind:
- homepage
- pricing / plans / compare
- product or feature page (a capability of the product)
- integrations (an integration / app page)
- competitor comparison ("… vs …", "… alternatives")
- other commercial page (anything else that markets the product/offering in this industry — label what it is)

Skip anything that is NOT about the product itself: editorial/informational content (blog posts, guides,
glossaries, definitions, Q&A / interview-question pages), free tools/calculators/templates/downloads,
company-info pages (about, team/leadership, press, careers, legal), and any non-English or localized duplicate URLs.

Output one line per kept URL:  <URL> — <kind>   (nothing else).

URLs:
<the ~200–300 URLs in this chunk>
```

**Output:** `_work/features-source-pages.md` — the de-duplicated list of commercial/product pages, by kind.

**What `_work/features-source-pages.md` looks like** (one row per kept page — this is the list Step 2 works from):

| URL | Kind |
|-----|------|
| https://testlify.com/ | homepage |
| https://testlify.com/pricing/ | pricing / plans / compare |
| https://testlify.com/compare-plans/ | pricing / plans / compare |
| https://testlify.com/test-library/bricklayer/ | product or feature page |
| https://testlify.com/integrations/engage-talent/ | integrations |
| https://testlify.com/vervoe-alternatives/ | competitor comparison |
| … *(every commercial page found, one per row)* | |

**Gotchas:**
- **URL-only** at this step — no fetching, no reading bodies.
- **De-dupe** the combined returns.
- If a kind has zero hits (e.g. no integrations pages found), note it — Step 3 will flag that section.

---

### Step 2 — Collect the product facts (a pool of ~7–10 sub-agents, in parallel)
**What it does:** pulls the real facts out of **all** the discovered commercial pages, into one pool — fast, by
splitting the work across a handful of sub-agents running at once.

**Process:**
1. Take the **full list** from `_work/features-source-pages.md` (there may be 50+ — every pricing, product,
   feature, integration, and competitor page).
2. **Split the list across ~7–10 sub-agents** (each gets a batch of URLs), and run them **in parallel**. Keep
   handing out batches until every discovered page has been processed. Each sub-agent extracts the facts from
   **each page in its batch** using the prompt below — it gets a page's body from `content-database.csv` by
   **finding the one row whose `URL` column equals the page's URL and reading that row's `Full content` column**;
   **for a pricing / compare / integrations page it web-fetches the live URL instead** (the saved copy strips
   those tables/lists).
3. Collect all returns into **`_work/features-facts.md`**.

**The exact sub-agent prompt (send one per relevant page):**
```
Extract product FACTS from EACH of these Testlify pages for the features.md file. Here is your batch of URLs:
<the batch of page URLs assigned to this sub-agent>

For each URL: get the page's full text from  content-database.csv  — open the CSV, find the ONE row whose `URL`
column exactly equals that URL, and read that row's `Full content` column (that is the page body). BUT if it is a
PRICING, COMPARE-PLANS, or INTEGRATIONS page, web-fetch the live URL instead — the saved copy may have stripped
the tables/lists.

For each page, return ONLY real facts found on THAT page — verbatim numbers, names, prices — under a heading with
the page URL. Invent nothing; leave a line blank if the page doesn't have it. Organise each page's facts into
these fixed categories (the same categories every page uses, so they can be gathered across all pages later):
- Features: each feature + what it does (+ the user benefit, if stated)
- Integrations: every named tool/platform it integrates with (+ category, e.g. ATS)
- Pricing: plan names, what each tier includes, the pricing model, any trial / guarantee / discount
- Competitive: advantages vs a NAMED competitor (only if this page names one) — keep it fair
- Social proof: real numbers (customers/teams, outcome stats, ratings, certifications, awards)
- Audience / segments: who the page says the product is for (segments) + the pains/needs it names
- CTAs: the exact call-to-action button/link text on the page (e.g. "Try for Free", "Book a Demo")
- FAQ: any question + answer pairs on the page (verbatim)
```

**Output:** `_work/features-facts.md` — the facts pool.

**What `_work/features-facts.md` looks like** (each page's facts grouped under its URL — this is what Step 3 fills from):

```
## https://testlify.com/  (homepage)
- Features: 3,000+ ready-to-use test templates; conversational AI interviews (chat / voice / video); video interviews; white-label; multilingual
- Integrations: —
- Pricing: —
- Competitive: —
- Social proof: reduce time-to-hire 55%; cut hiring costs 72%; candidate satisfaction 94%; 4,000+ roles
- Audience / segments: recruiters & hiring/talent teams, SMB → enterprise; pains: slow/expensive hiring, bias, cheating
- CTAs: "Try for Free"; "Book a Demo"
- FAQ: —

## https://testlify.com/pricing/  (live-fetched)
- Features: credit-based assessments (1 credit per candidate)
- Pricing: Standard plan — pay only when a qualified candidate starts an assessment; Custom/Enterprise; 30-day money-back guarantee; 24-month price lock; 25% nonprofit discount
- Social proof: Trusted by 1,500+ teams; SOC 2 Type II, ISO 27001, GDPR, CCPA
- Audience / segments: enterprises, HRtech resellers, nonprofits; pain: paying for unused capacity, lock-in
- CTAs: "Learn more"
- FAQ: "Can I cancel anytime?" → Cancel anytime, no contract, no conditions
```
*(…one block like this per page in the source list.)*

**Gotchas:**
- **Live-fetch pricing / compare / integrations** — the saved `Full content` loses those tables.
- **Verbatim numbers, names, prices** — a wrong integration name or price is worse than a blank.

---

### Step 3 — Fill the schema section by section (pure assembly)
**What it does:** writes `features.md` by filling **Appendix A's skeleton** one section at a time. **Everything you
fill comes from `_work/features-facts.md` (Step 2's pool).** The middle column names the **fact category** each
section is built from — **gather that category's lines from across *all* the page blocks in the pool** (a feature
can appear on the homepage, a pricing page, *and* a competitor page — collect them all, don't look at just one
page). Don't write a section until you've gathered its whole category.

**The core method — consolidate (this is the real work; slow down here).** Turning a big, repetitive pool into a
tight doc is done by *consolidation*, not by picking-and-dropping. The pool is dozens of near-duplicate pages
restating the same facts (e.g. "3,500+ tests" can appear 30–40 times). For **each category**, do this in order:

1. **Merge duplicates into one canonical line.** Gather every instance of a fact across all pages and collapse
   them into a **single** statement — keep the **most specific / complete** version (the one with the real number
   or the fullest list). List each **distinct** fact **once**. *(This step does ~90% of the size reduction.)*
2. **Keep the fact, drop the packaging.** Carry the fact; leave behind the marketing prose that wraps it on each
   page. Dropping prose is **not** dropping facts.
3. **Curated views vs the exhaustive home.** *Core Value Propositions* and *Competitive Differentiators* are
   **curated views** (the strongest / top few). The **exhaustive** home for every fact is *Technical Features +
   Integrations + Pricing*. A top feature therefore appears **twice** — once in Core Value Props (with a pitch)
   and once in the Technical Features full list. **Nothing is dropped — only re-surfaced.**
4. **"Strongest" is measured, not taste.** For Core Value Props, pick the features that (a) **recur most** across
   the pool and (b) show up as **advantages on the competitor pages** — those are the deal-winners.

*Because this is the deliberate step, it should feel like the slowest part — if the fill was instant, the merge
was probably done by instinct, not by rule. Verify each distinct fact is placed (the hard stop below).*

| Fill this section | ← Category (gathered across ALL pages) | How to write it |
|-------------------|-------------|-----------------|
| **Core Value Propositions** | **Features** | *curated view.* Pick the **5–10 strongest** by the measured rule above (most-recurring + cited as advantages vs competitors), each with **Feature** (what it is) · **Benefit** (why it matters) · **Conversion Angle** (a one-line quoted pitch, written **on-voice** from the real benefit) |
| **Technical Features** | **Features** (the full set) | group **all** the features into **3–5 named categories** (e.g. Assessments · Interviews · Anti-cheating/Proctoring · Integrations · Security), bulleted `**name**: brief description` |
| **Integrations & Ecosystem** | **Integrations** | **Direct Integrations** (named tool + what it does) + any partners |
| **Competitive Differentiators** | **Competitive** | *curated view.* Grouped **vs. named competitors**, each 3–4 real advantages **+ one fair note on where the rival is genuinely strong** — grounded in the facts, never invented |
| **Use Cases by Customer Segment** | **Audience / segments** | **3–5 segments** (SMB · enterprise · high-volume · technical · blue-collar…), each with 3–4 real needs |
| **Pricing & Plan Benefits** | **Pricing** | each real plan tier + what's included; the real model (credit-based, 24-mo lock, 30-day refund…) |
| **Key Messaging for Conversions** | **Social proof** + **CTAs** + **Audience/pains** (+ voice from `projects/[company]/01-brand-context/brand-voice.md`) | **Trial messages** (real CTAs) · **Pain Point → Solution** pairs · **Social Proof** (real stats) — worded on-voice |
| **Common Questions & Objections** | **FAQ** | real Q + benefit-focused **Answer** pairs |
| **Content Creation Guidelines** | template (static) | keep the standard guidance; tailor the bracketed bits to this company's segments/competitors |

> **🛑 HARD STOP — use every fact.** Every fact gathered in `features-facts.md` (across **all** the pages) must
> end up somewhere in `features.md`. **Do not cherry-pick or drop anything:** the **full** Features list goes into
> **Technical Features** (Core Value Propositions just *elevates* the strongest 5–10 of those same features — it
> doesn't replace the full list); and **every** Integration, **every** Competitive point, **every** Social-proof
> stat, **every** segment, **every** CTA, and **every** FAQ from **every** page must appear in its section. If a
> fact genuinely has no home, flag it — never silently discard it.

**Output:** `projects/[company]/01-brand-context/features.md` (draft).

**Gotchas:**
- The facts come from Step 2 — the only *written* parts are the Conversion Angles / trial messages / pain-point
  solutions, and those must be **on-voice and grounded in a real fact** (no new features).
- **Flag, don't fabricate** — a section with no real facts gets a "[needs: fetch X page]" flag for the human.

---

### Step 4 — Quality gate vs the Castos bar (loop)
**Check five things:**
1. **Completeness:** every Appendix-A section filled; no `[BRACKET]` placeholders.
2. **Every fact used (HARD STOP):** walk `features-facts.md` top to bottom and confirm **each** fact — every
   Feature, Integration, Competitive point, Social-proof stat, segment, CTA, and FAQ from **every** page — appears
   somewhere in `features.md` (or is explicitly flagged). If any fact was silently dropped, the gate fails.
3. **Depth:** 5–10 value props (each Feature/Benefit/Conversion Angle) · technical features in named categories ·
   integrations · competitive diffs vs **named** competitors · use-case segments · real pricing tiers ·
   conversion messaging · ≥5 objection Q&As.
4. **Accuracy:** real numbers, integration names, competitor names, prices — spot-check each against the facts
   pool; **any unverifiable fact is cut or flagged.**
5. **On-voice pitch:** Conversion Angles and messaging read on-brand per `brand-voice.md`.

**Two HARD RULES:**
- 🚫 **Castos is a depth bar only** — copying any feature, wording, or number from Appendix B = automatic fail.
- 🔁 **Any invented/unverifiable fact, missing section, or off-voice pitch fails** → back to Step 1/2 (fetch the
  missing facts) or Step 3 (re-fill). Repeat until all four pass.

**Output:** pass/fail per check + redo instructions. Only a full pass ships.

---

## Traceability map (every section ← a fact category, gathered across ALL pages)

| `features.md` section | Category in `features-facts.md` |
|-----------------------|--------------------------------|
| Core Value Propositions | **Features** (pick the 5–10 strongest) |
| Technical Features | **Features** (the full set, grouped into categories) |
| Integrations & Ecosystem | **Integrations** |
| Competitive Differentiators | **Competitive** |
| Use Cases by Segment | **Audience / segments** |
| Pricing & Plan Benefits | **Pricing** |
| Key Messaging (Trial/Pain/Social Proof) | **Social proof** + **CTAs** + **Audience/pains**; wording per `brand-voice.md` |
| Common Questions & Objections | **FAQ** |
| Conversion Angles / pitch wording | the section's facts + `brand-voice.md` (on-voice phrasing only) |
| Content Creation Guidelines | template (static) + light company tailoring |

---

## Rules shelf

- **Source list:** `_work/features-source-pages.md` (Step 1). **Facts pool:** `_work/features-facts.md` (Step 2).
- **Voice for the pitch lines:** `projects/[company]/01-brand-context/brand-voice.md`.
- **Raw schema:** Appendix A. **Depth bar:** Appendix B + the full file at `seomachine/examples/castos/features.md`.

---

## Gotchas (top of mind)

1. **Discover the pages from the content database, by URL** — not from Semrush, not by fetching.
2. **Live-fetch pricing / compare / integrations** — the saved `Full content` drops the tables.
3. **Facts only — never invent a feature.** Flag gaps.
4. **Verbatim numbers, names, prices** — accuracy beats polish.
5. **Only the pitch wording is written** — on-voice, from real facts.
6. **Castos is a ruler, never a source.**

---
---

# Appendix A — Raw schema (fill every section; reference template)

> Mirror of `seomachine/context/features.md`. This is the skeleton Step 3 fills. No `[BRACKET]` may survive.

```markdown
# [YOUR COMPANY] Features & Benefits

This document outlines [YOUR COMPANY]'s key features, benefits, and differentiators to inform content creation that drives trial conversions and customer acquisition.

## Core Value Propositions
<!-- 5–10 features. Each: Feature (what it is) · Benefit (why it matters) · Conversion Angle (a one-line pitch) -->
### 1. **[FEATURE NAME]**
- **Feature**: [what it does]
- **Benefit**: [the user outcome]
- **Conversion Angle**: "[one-line pitch, on-voice]"
### 2 … through … ### 8 (repeat)

## Technical Features
### [CATEGORY] — **[feature]**: [desc] ×~5   (3–5 categories)

## Integrations & Ecosystem
### Direct Integrations — **[tool]**: [what the integration does] ×~5
### Distribution / Partners (if any)

## Competitive Differentiators
### vs. [COMPETITOR] — **[advantage]** ([what they lack]) ×~4   (per named competitor)

## Use Cases by Customer Segment
### [SEGMENT] — [need] ×~4   (3–5 segments)

## Pricing & Plan Benefits
### [PLAN] Benefits — [benefit] ×~5   (per real tier; "Everything in [prev], plus:")

## Key Messaging for Conversions
### Trial Conversion Messages — "[CTA]" ×~4
### Pain Point Solutions — **"[concern]"** → "[solution]" ×~5
### Social Proof Elements — "[real number/stat/rating/award]" ×~4

## Common Questions & Objections
### "[question]?"
**Answer**: [clear, benefit-focused answer]   (×5)

## Content Creation Guidelines
1. Lead with benefits, not features   2. Use specific examples   3. Include proof points
4. Address objections proactively   5. Clear CTAs   6. Emphasize uniqueness   7. Match audience to use case

---
*Note: Update as new features launch or positioning changes. Keep aligned with current homepage/pricing copy.*
```

---
---

# Appendix B — Reference example (Castos) — REFERENCE ONLY · DO NOT COPY

> The **complete** filled Castos `features.md` is embedded below as the **depth bar** — this is *how thorough* a
> real one looks (11 value props each with Feature/Benefit/Conversion Angle, technical features grouped by
> category, a real integrations list, competitive diffs vs named rivals, segment use cases, per-tier pricing,
> conversion messaging, and objection Q&As). **Do not copy any of it** — its features, wording, or numbers are
> Castos's (a podcast host), not the company's. Copying anything from here into a real `features.md` is an
> automatic fail (Step 4). Use it only to judge whether yours is as complete and specific.

```markdown
# Castos Features & Benefits

This document outlines Castos's key features, benefits, and differentiators to inform content creation that drives trial conversions and customer acquisition.

## Core Value Propositions

### 1. **Private Podcast Hosting**
- **Feature**: Secure, unlimited hosting for private podcasts
- **Benefit**: Companies can host internal communications, training content, and member-exclusive shows without worrying about storage limits
- **Conversion Angle**: "Host unlimited private content without bandwidth caps or surprise overage fees"

### 2. **YouTube Repurposing**
- **Feature**: Automated video-to-podcast conversion from YouTube
- **Benefit**: Extract audio from YouTube videos and automatically publish as podcast episodes
- **Conversion Angle**: "Expand your reach by repurposing existing YouTube content into podcast format—no extra work required"

### 3. **Advanced Analytics**
- **Feature**: IAB-certified download statistics and listener insights
- **Benefit**: Accurate, industry-standard metrics for understanding audience behavior and demonstrating ROI
- **Conversion Angle**: "Know exactly who's listening with certified analytics that sponsors trust"

### 4. **WordPress Integration**
- **Feature**: Native WordPress plugin with seamless integration
- **Benefit**: Manage podcasts directly from WordPress dashboard—no need to leave your website
- **Conversion Angle**: "Already use WordPress? Manage your entire podcast workflow without switching platforms"

### 5. **Podcast Website Builder**
- **Feature**: Built-in website creation tools with customizable templates
- **Benefit**: Launch a professional podcast website without hiring a developer
- **Conversion Angle**: "Get your podcast online in minutes with a beautiful, mobile-responsive website"

### 6. **Monetization Options**
- **Feature**: Castos offers ads, donations, and paid private podcasting to help podcasters make money from their content
- **Benefit**: You can make money from your podcast regardless of the style of monetization you're looking for
- **Conversion Angle**: "Make money directly from your content, no extra tools required"

### 7. **Unlimited Podcasts & Episodes**
- **Feature**: Castos offers unlimited podcasts and episodes on all plans. Most of the competitors charge for this.
- **Benefit**: You can experiment with different formats, publish more content without it costing extra.
- **Conversion Angle**: "Publish all you want, one simple, low cost."

### 8. **One Click Distribution**
- **Feature**: One click gets your podcast live in all of the major podcasting directories.
- **Benefit**: You don't need to understand the technical setup of Apple Podcats, Spotify, etc. We handle it for you.
- **Conversion Angle**: "Get your podcast live, everywhere your listeners already are, in just a few minutes, without the technical headaches."

### 9. **Apple Podcast Subscriptions Integration**:
- **Feature**: Through a direct integration and partnership with Apple Podcasts Castos enables hybrid podcasting where creators can "offer free or paid access to content and free kind of subscriber benefits to your audience." This includes features like early access to episodes, private episodes for paying subscribers, access to back catalogs, and ad-free episodes.
- **Benefit**: Castos custoemrs can offer several ways to offer Subscriber Benefits to their audience, both in Free and Paid options.
- **Conversion Angle**: Give your best audience members some perks, it doesn't cost you (or them potentially) any extra

### 10. **Castos Ads (Dynamic Ad Insertion)**:
- **Feature**: Castos provides monetization through dynamic ad insertion where users can monetize all of your episodes – even the old ones – with a press of a button.
- **Benefit**: The system "will dynamically stitch short, brand-appropriate ads to the beginning and end of each episode" with ZERO technical setup needed" and "zero transaction fees.
- **Conversion Angle**: You don't need to sell to sponsors or figure out any technical jargon.

### 11. **Castos Commerce (Listener Donations)**:
- **Feature**: A native listener donation system built into Castos websites that allows creators to accept either one-time or recurring donations with "Zero transaction fees" beyond standard Stripe processing fees (2.9% and $.30). The system includes "a customizable, conversion-optimized page where they can select the amount they'd like to donate."
- **Benefit**: Castos users can accept listener donations without having to integrate another third party website or tool.
- **Conversion Angle**: Ads don't need to be the only way you make money from your podcast. Accept listener donations instead.

## Technical Features

### Hosting & Distribution
- **Unlimited hosting**: No storage or bandwidth limits on any plan
- **Automatic distribution**: Push episodes to Apple Podcasts, Spotify, Google Podcasts, and 20+ platforms
- **RSS feed management**: Customizable feeds with full control
- **Global CDN**: Fast, reliable delivery worldwide
- **99.9% uptime guarantee**: Enterprise-grade reliability

### Content Management
- **Episode scheduling**: Plan content releases in advance
- **Draft mode**: Preview episodes before publishing
- **WordPress Integration**: Manage all of your content from your WordPress site, Castos does the file storage and delivery
- **Transcription services**: Free transcripts included in all plans
- **Video podcasting**: Publish audio or video podcasts, all from the same account

### Audience Growth
- **SEO optimization**: Episode pages optimized for search engines
- **Social sharing**: Built-in tools to promote episodes on social media
- **Embeddable player**: Add podcast player to any website
- **Private podcasting**: Gated content for members or employees

### Monetization & Business
- **Dynamic ad insertion**: Insert ads into past episodes without re-uploading
- **Member-only content**: Restrict episodes to paying subscribers
- **Multiple shows**: Host unlimited podcasts under one account
- **Team collaboration**: Multiple user access with role permissions

### Analytics & Insights
- **IAB v2 compliant stats**: Industry-standard download metrics
- **Listener demographics**: Understand your audience location and how they listen
- **Episode performance**: See which content resonates most
- **Listening trends**: Track growth over time
- **Export capabilities**: Download data for custom reporting and custom analytics reports for sponsors or stakeholders

## Integrations & Ecosystem

### Direct Integrations
- **WordPress**: Native plugin for seamless management
- **YouTube**: Automatic video-to-podcast conversion
- **Zapier**: Connect to 5,000+ apps and workflows
- **Seriously Simple Podcasting**: Migration and compatibility support
- **Kit.com**: Automate private subscriber management through Kit (formerly Convertkit)
- **Paid Memberships Pro**: Sync your private subscribers and gated content from Paid Memberships Pro to your Castos account
- **API**: Create your own custom integration with our REST API

### Distribution Partners
- Apple Podcasts
- Spotify
- Amazon Music/Audible
- iHeartRadio
- Pandora
- Player.fm
- And 15+ more directories

## Competitive Differentiators

### vs. Buzzsprout/Transistor/Libsyn
- **Unlimited hosting on all plans** (competitors often cap uploads or storage)
- **Private podcasting built-in** (competitors charge extra or don't offer it)
- **YouTube repurposing** (unique feature most competitors lack)
- **WordPress-first approach** (tighter integration for WordPress users)

### vs. Anchor/Spotify for Podcasters
- **Professional analytics** (IAB-certified, not just platform metrics)
- **Full RSS control** (own your feed, easy to migrate)
- **No platform lock-in** (maintain independence from streaming platforms)
- **Advanced monetization** (dynamic ad insertion, private podcasting)

### vs. Generic Hosting (Libsyn, PodBean)
- **Modern interface** (intuitive, not outdated)
- **Built-in website** (don't need separate hosting)
- **Active development** (regular updates and new features)
- **Superior support** (responsive, podcast-focused team)

## Use Cases by Customer Segment

### Professional Podcasters
- Need reliable hosting with professional analytics
- Want monetization tools (ads, sponsorships, memberships)
- Require consistent uptime and fast delivery
- Value clean, branded podcast websites

### Content Creators/Influencers
- Already creating YouTube content
- Want to repurpose existing work into podcast format
- Need simple tools to expand reach across platforms
- Looking for growth and audience insights

### WordPress Site Owners
- Already invested in WordPress ecosystem
- Want seamless integration with existing website
- Prefer managing everything from one dashboard
- Value plugins and familiar workflows

### Businesses & Organizations
- Need private podcasting for internal comms or training
- Require team collaboration features
- Want professional branding and control
- Need reliable, scalable hosting

### Educational Institutions
- Distribute course content as podcasts
- Need private podcasting for student-only content
- Want transcription and accessibility features
- Require reliable hosting for large audiences

## Pricing & Plan Benefits

### Growth Plan Benefits
- Unlimited hosting and bandwidth
- Unlimited podcasts
- IAB-certified analytics
- WordPress plugin
- Website builder
- YouTube repurposing
- Basic support

### Pro Plan Benefits
- Everything in Growth, plus:
- Private podcasting
- Advanced analytics
- Team members
- Priority support
- Custom branding options

### Enterprise Plan Benefits
- Everything in Pro, plus:
- Dedicated account manager
- Custom integrations
- SLA guarantee
- White-label options
- Volume discounts

## Key Messaging for Conversions

### Trial Conversion Messages
- "Start your 14-day free trial—no credit card required"
- "See why thousands of podcasters trust Castos"
- "Set up your podcast in less than 10 minutes"
- "Try all features free for 14 days"

### Pain Point Solutions
- **"Worried about bandwidth costs?"** → "Unlimited hosting means no surprise bills"
- **"Already creating YouTube content?"** → "Repurpose it automatically into podcast episodes"
- **"Using WordPress?"** → "Manage your podcast without leaving your dashboard"
- **"Need accurate stats?"** → "IAB-certified analytics sponsors trust"
- **"Want to monetize?"** → "Dynamic ad insertion, listener donations, and private podcasting built-in"

### Social Proof Elements
- "Trusted by 50,000 podcasters worldwide"
- "Hosting 10 million downloads per month"
- "Rated 4.8/5 stars by customers"
- "Featured in Forbes, Entrepreneur, and dozens of leading tech publications"

## Common Questions & Objections

### "Is it easy to migrate from another host?"
**Answer**: Yes, we provide free migration assistance and handle the technical details to ensure zero downtime.

### "What if I outgrow my plan?"
**Answer**: Upgrade anytime with pro-rated pricing. All plans include unlimited hosting, so you'll never hit bandwidth limits.

### "Can I cancel anytime?"
**Answer**: Yes, no long-term contracts required. Cancel anytime with no penalties.

### "Do you offer a money-back guarantee?"
**Answer**: No but there is a free 14-day trial available to everyone

### "Will this work with my existing website?"
**Answer**: Yes, Castos works with any website platform. WordPress users get extra integration benefits.

## Content Creation Guidelines

When writing about Castos features:

1. **Lead with benefits, not features**: Don't just say "unlimited hosting"—explain "never worry about bandwidth overages"
2. **Use specific examples**: Show how features solve real problems
3. **Include proof points**: Stats, testimonials, certifications
4. **Address objections proactively**: Answer concerns before they ask
5. **Create clear CTAs**: Make next steps obvious (start trial, see pricing, contact sales)
6. **Emphasize uniqueness**: Highlight what makes Castos different from competitors
7. **Match audience to use case**: Tailor messaging to segment (creator vs. business vs. WordPress user)

---

*Note: Update this document as new features launch or positioning changes. Keep messaging aligned with current marketing campaigns and homepage copy.*
```
