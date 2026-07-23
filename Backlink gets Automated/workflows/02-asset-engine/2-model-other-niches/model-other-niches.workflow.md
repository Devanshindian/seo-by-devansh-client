---
type: workflow-step
parent: asset-engine (Method 2 of 3)
reusable: any company
needs: the approved brand-scope.md (Method 1 / G0 — the shared ownership anchor) · 01-brand-context/{brand-voice,features,stats}.md (to adapt formats on-brand) · the headless LLM CLI (free)
produces: projects/[company]/02-asset-engine/model-other-niches/output/ (deliverables); _work/ alongside
run: `python workflows/02-asset-engine/2-model-other-niches/run_model_niches.py --company <slug>` (the orchestrator; resumable; no API, no gates). Steps A→E are scripted — see README.md.
last_updated: 2026-07-21
---

# Idea Backlog — Method 2: Model What's Worked in Other Niches

> ✅ **FORMAT-HONESTY FIXED (2026-07-22).** This method still imports proven cross-niche *formats*, but it no
> longer forces tools dishonestly. The `b-adapt.md` prompt now applies the same rules as Method 1's G2:
> (1) the `asset` title carries **no shape-words** (Calculator/Quiz/Interactive/etc.) — the subject + angle
> only; (2) anything that needs a real build (an interactive tool, our own original data, new primary
> research) is **flagged in the `tool_escalation` column**, honestly, not hidden. So the write phase can pick
> only the desk-doable ideas, and the genuine tool ideas are labelled for a human to choose. It is **included
> in the merge** (`4-merge` config `INCLUDE_M2=True`). See `../format-honesty-fix-plan.md`.

**Import proven link-bait *formats* from other industries and adapt them to ours.** Many formats earn links
in *any* niche (calculators, indices, generators, awards). If a format pulled huge links in finance or real
estate but **no competitor in our niche has built one**, that's a fresh, ownable link magnet.

> **This is the method that fills the gap** Method 1 can't: formats our competitors *don't* have. Method 1
> finds what works **inside** our niche; Method 2 imports what works **outside** it.

**Fully agent-doable.** No Semrush, no user-in-tool — the agent *is* the "ChatGPT" the research method calls
for. So we build **and** run it in one pass.

> **Confidence note:** these ideas are proven **elsewhere**, not yet in our niche — so they're **higher
> novelty, lower certainty** than Method 1. That's fine: the **D2 validation step** (check linking-root-
> domains of the format in/near our niche) is where we confirm a winner before building. Method 2's job is
> **volume + novelty**, not pre-validation.

> **Whether a competitor already has the format is NOT checked here.** Method 2 doesn't run its own
> competitor study, and it no longer borrows Method 1's. The in-niche overlap check (does Method 1 already
> own this format/topic?) happens **once, at the cross-method merge**, where all three pools sit together —
> not inside this method. Method 2 just outputs its filtered, scored idea pool.

This is **Method 2 of 3**; its output is a **separate** pool that merges with Method 1's and Method 3's
pools. De-duplication and any "who already owns this" call are made at that merge, not here.

---

## Output (under `projects/[company]/02-asset-engine/model-other-niches/output/`)
1. **`format-swipe.md`** — the library of proven cross-niche formats, **brand-fit pre-screened** to the ones
   we can plausibly point at an in-scope subject. Columns: `Format · Real example(s) · Headline template ·
   Why it earns links · In-scope subject · Brand fit`.
2. **`model-other-niches-ideas.csv`** — the `[company]` adaptations that survived the filter, in the
   shared schema:
   `Idea # | Method | Brand fit | Asset | Format | Our topic | Distinct angle | Source niche | Evidence URLs | Beatability | Effort | Notes`.
3. **`RUN-LOG-problems.md`** — entries for any format dropped at Step A or idea dropped at Step C, with the
   reason. Makes the cut audit-able.

> **Schema alignment with Method 1.** The columns above match Method 1's `ideas.csv`, with two
> Method-2-native additions: `Source niche` and `Evidence URLs`. There is **no `Competitor coverage`
> column** — the in-niche overlap check is a merge-step decision, not a per-method one. `Build window`
> (NOW/LATER) is likewise **not** assigned here — it's set at the cross-method merge based on team capacity.

---

# ✅ RUN CHECKLIST
> Copy into `RUN-LOG-problems.md`. A box is only ticked when it's really true.

**Step A — swipe library**
- [ ] The approved `brand-scope.md` (Method 1 / G0) is loaded as the ownership anchor — not a fresh ad-hoc call.
- [ ] Source 1 (the table in this file) reviewed in full, no rows skipped.
- [ ] Source 2 (agent knowledge) produced at least 3 candidate formats beyond the table.
- [ ] Brand-fit pre-screen applied **per format**: each kept format names a plausible in-scope subject
      (CORE / TRANSPLANT / ADJACENT). Only formats with no imaginable in-scope subject are dropped.
- [ ] Dropped formats logged with the reason in `RUN-LOG-problems.md`.
- [ ] `format-swipe.md` written with the kept rows.

**Step B — generate adaptations**
- [ ] One adaptation per surviving format. No padding (no "give me 5 ideas per format").
- [ ] Each adaptation grounded in brand-voice + features + stats — product/audience/data named, not "improve X."

**Step C — filter weak ideas (the real scored gate — same tests as Methods 1 & 3)**
- [ ] Every adaptation run through both shared tests against `brand-scope.md`: **Ownability** (CORE/TRANSPLANT/
      ADJACENT, transplant check before any drop) and **Linkability** (4 questions, needs ≥3/4).
- [ ] Transplant check recorded for every out-of-scope idea before it's dropped.
- [ ] Each KEEP / DROP logged with the reason.

**Step D — score**
- [ ] `Beatability` (1-3) and `Effort` (S/M/L) set on every surviving idea, using the same scales as
      Method 1.

**Step E — deliver**
- [ ] `model-other-niches-ideas.csv` written with all 12 columns in the shared schema (no `Competitor coverage`, no `Unfair advantage`).
- [ ] Sorted: `Brand fit` (CORE → TRANSPLANT → ADJACENT) → `Evidence × Beatability` desc → `Effort`
      (S first) as tiebreaker.
- [ ] No `Build window` column set, and no in-niche overlap check — both are merge-step decisions.

---

# Step A — Build the swipe library, then pre-screen it against the brand scope

A **swipe library** is a menu of *formats that already earned links* — the *shape* of the asset (a
calculator, a quiz, an index), not its subject. Build the menu from two sources, then pre-screen it.

### A0. Load the shared brand scope (the same anchor Methods 1 and 3 use)
Before pre-screening anything, load the **approved `brand-scope.md`** built in Method 1's G0 — it lives at
`projects/[company]/02-asset-engine/competitor-study/output/brand-scope.md`. This is the single ownership anchor all
three methods judge against (CORE / TRANSPLANT / ADJACENT), so Method 2 doesn't invent a fresh ad-hoc test.
If Method 1 hasn't been run yet, distil it from brand-voice + features + the company record exactly as Method 1's G0 describes (and get
the user's sign-off), then proceed.

Each A-step produces **named fields**, so A4 is pure assembly — never invention. The table's columns map
exactly to these step outputs:

| `format-swipe.md` column | Filled by | From |
|---|---|---|
| `Format` | A1 / A2 | lifted verbatim |
| `Real example(s)` | A1 / A2 | lifted verbatim |
| `Headline template` | A1 / A2 | lifted verbatim |
| `Why it earns links` | A1 / A2 | lifted verbatim |
| `In-scope subject` | A3 | the pre-screen decision |
| `Brand fit` | A3 | the pre-screen decision (rough — Step C sets the authoritative tag) |

### A1. Source 1 — the proven-examples table
**"The swipe library — proven formats"** further down this file is the real data: ~20 format families
distilled from 75 real link-bait pieces. **Read every row** — don't skip ahead.

**Output of A1:** every row of that table, carried forward **as-is**, with its four columns intact —
`Format · Real example(s) · Headline template · Why it earns links`. Nothing rewritten or summarised; you're
copying proven rows, not paraphrasing them.

### A2. Source 2 — the agent's own knowledge
This source is non-deterministic on purpose. Recall famous link-magnet formats that **(a)** aren't already
in the table, **(b)** earned *backlinks* (not just traffic or social shares), and **(c)** worked across
**multiple** niches. Aim for 3-5 additions.

> Examples of formats from agent knowledge (don't anchor to these — find your own): the Big Mac Index, the
> HubSpot Website Grader, the Best Places to Work award.

**Output of A2:** the **same four fields** as A1, one row per added format — so they concatenate onto Source
1 with no schema mismatch:
- `Format` — the format name (e.g. "Branded index").
- `Real example(s)` — at least one **named, real** example, with a URL where you can recall it (e.g. "Big Mac Index — economist.com/big-mac-index"). No example you can't name = drop the format.
- `Headline template` — the fill-in headline shape (e.g. `` `The [TOPIC] Index` ``).
- `Why it earns links` — one phrase naming the link mechanism (Utility / Data / Reference / Visual / Ego-bait / Emotion), matching how Source 1's rows are written.

### A3. Pre-screen each format on brand fit (light — the real filter is Step C)

Run **every** format from A1 + A2 through one question against `brand-scope.md`:

> *Can this format plausibly be pointed at a subject inside our brand scope?*

The **transplant check is mandatory before dropping**: if the format's obvious subject is off-brand, look for
an in-scope subject the same *shape* could serve before binning it (a celebrity-style quiz → a "what's your
hiring-bias profile" quiz). **Drop only a format you cannot imagine pointing at any in-scope subject** (log
the drop + reason in `RUN-LOG-problems.md`).

**Output of A3, per surviving format** — two table cells:
- `In-scope subject` — the candidate subject inside our scope, in plain words (e.g. "Cost of a bad hire"). Not a vague theme ("hiring stuff") — a nameable subject a writer could build on.
- `Brand fit` — one tag: **CORE / TRANSPLANT / ADJACENT**. For TRANSPLANT, name the off-brand subject it came from (e.g. "TRANSPLANT — from cost-of-living"). This is a **rough pre-screen call**; Step C's Ownability test sets the authoritative tag once there's a real subject.

> This step is deliberately light. You're judging a bare format with **no topic yet**, so a hard "do we have
> an unfair advantage" test here would be guesswork — that belongs in **Step C**, after the format has an
> actual subject. (Mirrors Methods 1 and 3, which only judge ownability once there's a real subject.) Keep
> most formats; Step C does the real cutting.

### A4. Write the survivors to `format-swipe.md`

**Pure assembly — no new thinking.** Each row = A1/A2's four carried-forward columns + A3's `In-scope subject`
and `Brand fit` cells. If a cell isn't traceable to an A1/A2/A3 output, it doesn't belong in the table.

```markdown
# Format swipe library — [Company] (Method 2)
Proven cross-niche link-bait formats, brand-fit pre-screened to the ones [Company] can plausibly own.
Sources: the link-bait dataset (Source 1) + agent knowledge (Source 2). Date: [YYYY-MM-DD].

| Format | Real example(s) | Headline template | Why it earns links | In-scope subject | Brand fit |
|---|---|---|---|---|---|
| Cost calculator | NerdWallet Mortgage Calculator | `[QUESTION]? [Free Calculator]` | Utility — cited as "see how much it costs" | Cost of a bad hire | CORE |
| Branded index | Big Mac Index | `The [TOPIC] Index` | Data — recurring; cited by name | Cross-industry skills-gap index | CORE |
```

This file is the **input to Step B** — every kept row becomes one generation prompt.

---

# Step B — Generate the [company] adaptation of each surviving format

Run this prompt **once per row** of `format-swipe.md`. One row produces one adaptation. Don't ask for "five
variations" — most formats yield exactly one strong idea.

> **Prompt:**
> *"Proven cross-niche link-bait format: **[Format]** (headline template: `[Headline template]`; earns
> links via **[Why it earns links]**). Source-niche example: **[Real example]**.
>
> Using [Company]'s brand context (brand-voice.md · features.md · stats.md) — product, audience, real data — give me the single strongest [Company]
> adaptation of this format. Borrow the **shape**, not the source niche's subject. Point it at the in-scope
> subject from the swipe row (**[In-scope subject]**, brand fit **[CORE/TRANSPLANT/ADJACENT]**), and name
> the specific **product, data, or authority** that lets us own it.
>
> Return exactly these fields, **in this order — work out the substance before you name the thing:**
> 1. **Our topic**: the specific subject — sharpen A3's in-scope subject (**[In-scope subject]**) to a precise one, grounded in the brand context.
> 2. **Distinct angle**: one line — what makes our version the link-magnet. It **must name the specific product, data, or authority that lets us own it** (this is what makes ours, not a generic version). Anti-generic test: if it could be written without the brand context, it's too generic — rewrite.
> 3. **Asset**: only now, name it — a **real working title for the thing we'd build, with the distinct angle baked into the name** (same rule as Method 1's G2). NOT `[Format] on [topic]` glued together. ❌ "Cost calculator on bad-hire impact" → ✅ "Bad-Hire Cost Calculator (per-role, on real customer cost data)".
> 4. **Headline**: the published H1 in the brand voice (brand-context/brand-voice.md), built from the headline template (the marketing headline, distinct from the build-name Asset).
> 5. **What it'd be**: 1-2 lines — the actual asset, concretely"*

> **Why this order:** the distinct angle — *why ours wins, and what we own that lets it* — is the foundation;
> the Asset name only works once it can bake that angle in. Naming the asset first forces a guess you then
> have to justify backwards. (`Brand fit` is **not** asked here — A3 set the rough tag and Step C's Ownability
> test sets the authoritative one; deciding it a third time in B is wasted motion.)

**Where each Step B field goes** (the rest of the CSV is filled elsewhere — see Step E for the full column map):
`Our topic`, `Distinct angle`, `Asset` are CSV **columns**; `Headline` + `What it'd be` live in **Notes**.
`Format`, `Source niche`, `Evidence URLs` are **carried from the swipe row**; `Brand fit` comes from
**A3 (rough) → Step C (authoritative)**; `Beatability` and `Effort` come from **Step D (scoring)**.

> **Asset-naming rule (same as Method 1's G2 — do not regress).** `Asset` is a real working title a writer
> could open a doc with, with the differentiator visible in the name — **never** `[Format] on [topic]` glued
> together (that's the template-fill trap G2 bans and G6 spot-checks for). ❌ "Branded index on cross-industry
> skill gaps" → ✅ "The Cross-Industry Skills-Gap Index (annual, free, from aggregate test data)".

### What Step B produces — example output

One adaptation per swipe row. Collecting the prompt's five fields across all rows gives this table (the input
to Step C). Two rows shown, in the field order the prompt returns them:

| Our topic | Distinct angle | Asset | Headline | What it'd be |
|---|---|---|---|---|
| Cost of a mis-hire (salary + recruiting + ramp + productivity loss) | Live calc on our anonymised customer cost data (not generic Glassdoor averages), with a per-role breakdown competitors can't match | Bad-Hire Cost Calculator (per-role, on real customer cost data) | "What does a bad hire actually cost you? [Free Calculator]" | 4-input form (role, salary, location, ramp) → live cost output + sourced formula + sharable PDF |
| Cross-industry skill gaps | Annual, free, interactive index on our aggregate test pass-rate data that no consultancy publishes — rivals only sell static paywalled reports | The Cross-Industry Skills-Gap Index (annual, free, from aggregate test data) | "The [YEAR] Skills-Gap Index: which industries are short on what" | Interactive index + downloadable dataset, refreshed yearly, cited by name |

> Each row still carries its swipe-row fields (`Format`, `Real example(s)` → `Evidence URLs`, `Source niche`)
> alongside these five — they're just not re-typed here. `Brand fit` is not in this table; Step C assigns it.
> The "what we own that lets us win" now lives **inside** the Distinct angle, not as a separate column.

---

# Step C — Filter the adaptations (the real scored gate — same tests as Methods 1 & 3)

Step A pre-screened the *formats* on brand fit; this is the real filter, run on the *ideas* the formats
produced — now that each has an actual subject. Use the **same two tests Method 3 runs in its Stage 3**,
against the **same `brand-scope.md`**, so all three methods filter identically. Log every DROP in
`RUN-LOG-problems.md`; expect to drop a material chunk here — that's the filter working.

### Test A — Ownability (can we credibly own it?)
Run the adaptation against `brand-scope.md`:
- Does it sit inside the brand scope (CORE / TRANSPLANT / ADJACENT)?
- Does [Company] have the **data, product, or authority** to speak credibly on it? The idea's `Distinct
  angle` must already name a specific one — if it can't, the idea fails this test.
- Does building it reinforce the brand?

CORE or TRANSPLANT passes; ADJACENT is a maybe. **Out of scope? Run the transplant check before dropping**
(mandatory, same as Method 3): is there a strong, linkable format here we can point at an in-scope subject?
If yes, KEEP as **TRANSPLANT** and record the move; only if the transplant *also* fails does the idea DROP.

> The CORE / TRANSPLANT / ADJACENT verdict here is the **authoritative `Brand fit`** written to the CSV — it
> supersedes A3's rough pre-screen tag (A3 judged a subject-less format; this judges the real adapted idea).

### Test B — Linkability (would anyone cite it?)
Four questions (identical to Method 3's Stage 3 Test A):
1. Is there a citable number an asset could produce that a writer would reference?
2. Would a journalist or blogger reference it when writing about the niche?
3. Is it evergreen — not a one-off that dies in a week?
4. Does it fit a proven link-bait format? *(For Method 2 this is automatically yes — every input is a proven
   format — so in practice you need ≥2 of the other 3.)*

Needs **≥3 of 4 yes** to pass.

Record each idea as **KEEP / DROP / MAYBE** + a one-line reason. Keep only ideas that pass **both** tests.
Quality over volume — Method 2 is expected to produce roughly 8-20 surviving ideas, not 50.

---

# Step D — Score: Beatability and Effort (same scales as Method 1)

Add two columns to every surviving idea.

### `Beatability` (1-3)

Base this on how easy it'll be to make the asset itself link-worthy (Method 2 has no in-niche competitor
page to measure against — that comparison is a merge-step concern):
- **3** — simple format (glossary, listicle, basic calculator), short build, fast win.
- **2** — moderate (interactive tool, data-light index, definitive guide).
- **1** — heavy (proprietary data report, complex interactive, full microsite).

### `Effort` (S/M/L) — identical scale to Method 1
- **S** — days to a week (a glossary entry, a single calculator, a stats roundup).
- **M** — weeks (a 30-term glossary section, an interactive index with limited data, a definitive guide + template).
- **L** — a month+ (annual research, full microsite, custom-built interactive).

---

# Step E — Write the deliverable

Output `model-other-niches-ideas.csv` with all 12 columns of the shared schema:

```
Idea # | Method | Brand fit | Asset | Format | Our topic | Distinct angle | Source niche | Evidence URLs | Beatability | Effort | Notes
```

Column-by-column:

| Column | What goes in it |
|---|---|
| `Idea #` | Sequential, scoped to Method 2 (M2-001, M2-002…) so the merge later doesn't collide with Method 1's numbering |
| `Method` | Always `M2 — Other Niches` (so the merged sheet can be filtered to one method) |
| `Brand fit` | CORE / TRANSPLANT / ADJACENT — A3's rough tag, finalised by Step C's Ownability test |
| `Asset` | A real working title with the angle baked in, from Step B (Method 1's G2 rule — never `[Format] on [topic]` glued) |
| `Format` | The format tag, from the swipe library |
| `Our topic` | The specific subject, from Step B |
| `Distinct angle` | One line, from Step B — what makes our version the link-magnet, naming the product/data/authority that lets us own it |
| `Source niche` | Where this format proved itself (finance, real estate, B2B SaaS…) |
| `Evidence URLs` | The real example URLs from the swipe library — proof inline, same principle as Method 1's `Backing URLs` |
| `Beatability` | 1-3 |
| `Effort` | S / M / L |
| `Notes` | Headline + What it'd be from Step B; anything else (pairs-with-Method-1-idea, validation flag) |

**Sort order:**
1. `Brand fit` — CORE → TRANSPLANT → ADJACENT.
2. `Evidence × Beatability` descending (where Evidence for Method 2 = the number of source-niche examples
   in `Evidence URLs`).
3. `Effort` — S before M before L as tiebreaker.

**No `Build window` column, and no in-niche overlap check.** Both get handled at the cross-method merge,
where Method 1's, Method 2's, and Method 3's pools sit together and compete for the same NOW slots based on
team capacity. Deciding either here would bias the final selection.

---

# Worked example — one format from swipe row to final CSV row

**Swipe row (after A3 brand-fit pre-screen):**

| Format | Real example(s) | Headline template | Why it earns links | In-scope subject | Brand fit |
|---|---|---|---|---|---|
| Cost calculator | NerdWallet Mortgage Calculator; HubSpot ROI Calculator | `[QUESTION]? [Free Calculator]` | Utility — cited as "see how much it costs" | Cost of a bad hire | CORE |

**Step B output (substance first, then the name):**
- Our topic: cost of a mis-hire (salary + recruiting + ramp + productivity loss)
- Distinct angle: live calculator on our anonymised customer cost data (not generic Glassdoor averages), with a per-role breakdown competitors can't match
- Asset: `Bad-Hire Cost Calculator (per-role, on real customer cost data)`
- Headline: "What does a bad hire actually cost you? [Free Calculator]"
- What it'd be: a 4-input form (role family, salary, location, ramp months) → live cost output + sourced formula + a sharable PDF

**C check (the real gate):** Ownability — cost-of-a-bad-hire sits in scope → **Brand fit = CORE** (authoritative), and the angle names aggregate hire-cost data we hold (the product/data we own). Linkability — citable number ✅, journalists cite hiring-cost figures ✅, evergreen ✅, proven format ✅ = 4/4. **KEEP.**

**D scoring:** Beatability = 3 (simple format, fast build). Effort = S (days, not weeks).

**Final CSV row:**

| # | Method | Brand fit | Asset | Format | Our topic | Distinct angle | Source niche | Evidence URLs | Beat. | Effort | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M2-001 | M2 — Other Niches | CORE | Bad-Hire Cost Calculator (per-role, on real customer cost data) | Cost calculator | Cost of a mis-hire | Live calc on our customer cost data, per-role breakdown (data we hold) | finance/B2B SaaS | nerdwallet.com/mortgage-calculator; hubspot.com/roi-calculator | 3 | S | Headline: "What does a bad hire actually cost you?" Pairs with State-of-hiring report. |

Read across one row and the whole logic is visible: shape (from where it works), our topic (from the brand context), why our version wins (the angle, naming what we own), and the proof the format earns links (Evidence URLs). Whether anyone in-niche already has it is settled at the merge, not here.

---

# The swipe library — proven formats (built from 75 real link-bait pieces)

This is **Source 1** for Step A. Each row is a format that earned links; pick the shape, not the subject.

| Format | Real example(s) | Headline template | Why it earns links |
|---|---|---|---|
| **Interactive "how it works" explainer / animation** | Animagraffs: *How a Car Engine Works*, *Inside a Jet Engine* | `How [TOPIC] Works` · `Inside a [TOPIC]` | **Reference/visual** — publishers embed & screenshot it |
| **Calculator** | *Compound Interest Calculator*, *Mortgage Calculator*, *How Much Car Can I Afford?* | `[QUESTION]? [Free Calculator]` | **Utility** — cited as "see how much it costs" |
| **Branded index** *(agent knowledge)* | *Big Mac Index*, *Misery Index* | `The [TOPIC] Index` | **Data** — recurring; journalists cite it **by name** |
| **Original research / "We analyzed X"** | Backlinko: *We Analyzed 11.8M Google Search Results* | `We Analyzed [#] [TOPIC]. Here's What We Learned About [TOPIC]` | **Data (original)** — most-cited format there is |
| **Statistics roundup (curated)** | *161 Cybersecurity Statistics & Trends*, *57 NEW AI Statistics* | `# [TOPIC] Statistics and Trends [Updated YEAR]` | **Reference** — writers grab a stat + link the source |
| **Infographic / data-visual** | *Do Looks Matter? (Infographic)*, *How Much Toilet Paper Every Country Uses, Visualized* | `[HOOK]: [STATISTIC]` · `How Much [TOPIC], Visualized` | **Visual + data** — embeddable, can't copy without crediting |
| **Map / geo data viz** | *Map of Africa*; cost-of-living maps *(agent knowledge)* | `Map of [TOPIC]` | **Visual data** — embed magnet |
| **Generator tool** | *Business Name Generator*, *Citation Generator* | `[TOPIC] Generator` | **Utility** — free reusable tool, shareable |
| **Benchmark / grader** *(agent knowledge)* | *HubSpot Website Grader* | `How does your [TOPIC] compare?` | **Utility** — personalised score → shareable |
| **"Best of" award + badge** *(agent knowledge)* | *Best Places to Work* | `Best [GROUP] for [TOPIC]` | **Ego-bait** — winners embed a badge that **links back** |
| **Definitive guide (+ free template)** | *On-Page SEO: The Definitive Guide + FREE Template* | `[TOPIC]: The Definitive Guide + FREE Template (YEAR)` | **Reference** — the canonical link for the topic |
| **"Complete list" / ranking-of-factors listicle** | *Google's 200 Ranking Factors: The Complete List* | `[TOPIC]: The Complete List (YEAR)` | **Reference** — exhaustive, hard to out-do |
| **Rankings (recurring)** | *Law School Rankings*, *College Football Rankings* | `[TOPIC] Rankings` | **Reference** — updated, cited each cycle |
| **Glossary / terms** | *Poker Terminology*, *37 Must-Know Golf Terms* | `[TOPIC] Terms and Definitions` | **Reference** — definitional pages attract citations |
| **Facts listicle** | *125 Interesting Facts About Practically Everything* | `# Interesting Facts About [TOPIC]` | **Reference** — curiosity + easy citation |
| **Checklist / microsite tool** | *GDPR Compliance Checklist*, *Internet Speed Test* | `The [TOPIC] Checklist` · `[TOPIC] Test` | **Utility** — single-purpose free tool |
| **Quiz / typology** | *Body Type Quiz*; *16Personalities (agent knowledge)* | `What is Your [TOPIC]?` | **Novelty** — shareable; B2B angle only |
| **Controversy / opinion** | *How Google Is Killing Independent Sites* | `How [WELL-KNOWN ENTITY] Is [TOPIC]` | **Emotion** — strong opinion drives shares + links |
| **Case study (results)** | *How I Increased Search Traffic 110% in 14 Days* | `[TOPIC] Case Study: How I [OUTCOME] in [X] Days` | **Proof/data** — concrete results get cited |

> **Data-asset shortcut:** when a format needs real numbers (index, research, stats roundup, map), the same
> dataset has a vetted **data-source list** (~100 URLs: data.gov, Pew, FRED, World Bank, Gallup, OECD…) to
> pull public data from. Use it when a format needs evidence the company doesn't already own.

---

# Gotchas

- **Format not topic** — import the shape, not the other niche's subject.
- **Pre-screen early (Step A), filter hard (Step C)** — Step A is a *light* brand-fit pre-screen on bare
  formats; Step C is the real scored gate (Ownability + Linkability vs `brand-scope.md`), the same two tests
  Methods 1 and 3 use. Most ideas that die, die at Step C's Ownability test — that's correct.
- **No in-niche overlap check here** — Method 2 does not check whether a competitor already has the format.
  That de-duplication against Method 1 (and Method 3) happens once, at the cross-method merge.
- **Lower confidence by design** — validate the top picks in **D2** (linking-root-domains) before building.
- **Don't let the LLM run wild** — every idea's `Distinct angle` must name a specific product feature,
  dataset, or authority that lets us own it. "We're a great team" is not an angle.
- **No `Build window` here** — set at the cross-method merge based on team capacity, not per-method.
- **One adaptation per format** — most formats yield one strong idea, not five. Pad-padding kills the
  filter.