---
type: workflow-step
parent: asset-engine / D2 (reuse check)
reusable: any company
needs: clubbed-ideas.csv (the merged pool) · content-database.csv WITH the Full content column · Voyage embeddings API (free tier)
produces: RAG candidates + Topic-catalogue + Reference links (Stage 2, links only) and Reuse verdict / Chosen links / Why (Stage 3), all in clubbed-ideas.csv
last_updated: 2026-06-30
---

# Reuse Check — do we already have this asset?

After the three pools are merged into `clubbed-ideas`, and **before building anything**, check every asset
idea against the company's **existing content**. Two payoffs:

1. **Don't rebuild what we already own.** If a page already does the job, building it again is wasted effort.
2. **Don't research from scratch.** Even when no single page matches, related pages we already have are
   reusable research for the new asset.

The check is **RAG (find the closest existing pages) → LLM judgment (decide what to do)**. RAG alone only
says "these look similar"; it can't decide *improve vs. already-have vs. build-from-parts* — that's a read +
judgment call, which is the LLM's job.

---

## What the reuse check fills in `clubbed-ideas.csv`

`clubbed-ideas` is a **single CSV**, built at the merge with every column already present and the reuse columns
empty. The reuse check fills them — each produced by exactly one stage, so the file stays auditable:

| Column | What it holds | Produced by |
|---|---|---|
| **RAG candidates** | the top-15 best existing pages (blended retrieve → reranked), each as `Title — link (rerank score)` | Stage 2 — retrieval |
| **Topic pages we own** | the **complete** list of existing pages on the asset's topic (deterministic keyword catalogue) | Stage 2 — catalogue |
| **Reference links** | one consolidated, de-duped list of every link above — the set to fetch when building the asset | Stage 2 — assembly |
| **Reuse verdict** | one of: 🟢 Already have it · 🟡 Improve existing · 🟠 Build from parts · 🔴 Brand new | Stage 3 — LLM |
| **Chosen links** | the verdict's actual link(s) — **a subset of RAG candidates**; blank for Brand new | Stage 3 — LLM |
| **Why** | a short paragraph explaining the verdict, citing what the page has/lacks | Stage 3 — LLM |

> **Single source of truth.** `Chosen links` can only contain links that appear in `RAG candidates`/`Reference
> links` — Stage 3 picks from what retrieval found, it never invents a URL. The verdict is decided once, in Stage 3.

> **🔑 Links, not content — fetch on demand.** We do **NOT** store page text in the clubbed file (no
> `Candidate N content` columns). Storing ~15–40 full pages per idea inline would balloon the file to tens of MB
> for no reason — **we already hold every page's `Full content` in `content-database.csv`.** So the clubbed file
> keeps only **links**; any step that needs the actual text fetches it on demand:
> - **Stage 3 (judge)** and **content creation** look each candidate up **by URL in `content-database.csv`**, or
>   **web-fetch the live page** when the freshest copy matters.
> This keeps the clubbed file small (links only) and the content in exactly one place.

---

## Inputs

- **`clubbed-ideas.csv`** — the merged pool. The query for each idea = its **Asset title only** (the verbose
  Distinct angle is deliberately left out — it drags the search off-topic; see Stage 2).
- **`content-database.csv`** — must include the **`Full content`** column (see
  `00-foundation/1-site-catalogue/` (the site-catalogue engine)). We index both the page **`Title`** and its **`Full content`**.
- **Voyage** — `voyage-4-large` for embeddings (best general model, free tier) + `rerank-2.5` for reranking
  (best reranker, free tier). Key from `VOYAGE_API_KEY`, else the first `pa-…` token in `~/.testlify-access.md`.

---

## Stage 1 — Build the content index (once per company)

Index every page in **`content-database.csv`** twice, so the title isn't drowned out by the long body (the v1
failure — see Gotchas):

1. **Title vector** — embed the page's **`Title` column (from `content-database.csv`)** on its own: one short,
   clean fingerprint per page. The title is the strongest topic signal, so it gets its own vector.
2. **Body vectors** — embed the page's **`Full content` column (from `content-database.csv`)**, split into
   chunks for long pages; each chunk tagged to its page link (resumable).
3. Both sets are tagged with the page `link` + `Title` and saved under
   `02-asset-engine/clubbed/_work/content-index/` (`title/` and `body/`). Only pages **with** full content are
   indexed — a page with no body can't be a useful reuse candidate.

> **Two different "titles" — don't confuse them.** The **page `Title`** (from `content-database.csv`) is what
> we embed *here* in Stage 1, into the title vector. The **Asset title** (the *idea's* name, the `Asset`
> column in `clubbed-ideas.csv`) is the *search query* in Stage 2. Same word, opposite sides of the search.

Refresh only when the content database is rebuilt. The asset ideas are embedded fresh, per idea, in Stage 2.

---

## Stage 2 — Retrieve the top 15 candidates per idea (mechanical, no judgment)

For each asset idea in `clubbed-ideas`:

1. **Query = the Asset title, with parenthetical detail stripped** (the `Asset` column from `clubbed-ideas.csv`).
   Do NOT append the Distinct angle — it's a competitor-gap / workflow-note paragraph that drags the search
   toward tangents. **Also strip the title's own `(…)` qualifier** — e.g. *"… Benchmark Report (Adoption, AI
   Cheating, …)"* → *"… Benchmark Report"*; that detail is mini-angle noise too (in testing it pushed the right
   page from rank #1 down to #21). It's a *selection*, not a scrub: take the Asset title, drop the angle and any
   parenthetical.
2. Embed the query with the same Voyage model.
3. **Blended dense score per page:** `score = α·(query↔title) + (1−α)·(best query↔body chunk)`, with **α = 0.5**
   (title slightly favored; tunable). Take the **top 40** pages by this blended score.
4. **Rerank** those 40 with **Voyage `rerank-2.5`** — a cross-encoder that reads the query + each page and
   scores true relevance far better than cosine — and keep the **top 15** (exclude foreign-language pages).
5. **Build the topic catalogue** (separate, deterministic — see the "Topic catalogue" section): every existing
   English page whose title/URL contains the asset's topic keyword(s).
6. Write into `clubbed-ideas.csv`, one pass — **links only, no page content**:
   - **RAG candidates** = the top-15 as `Title — link (rerank score)`;
   - **Topic pages we own** = the catalogue as `Title — link`;
   - **Reference links** = the de-duped union of the two (plain URLs) — the fetch list for content creation.

> **Why 40 → 15?** Dense retrieval is approximate, so cast a wide net (**40**) for recall, then let the reranker
> keep the genuinely relevant **15** (was 7 — widened so the reviewer sees more of the neighbourhood). 40, 15,
> and α are all tunable. **No page content is stored** — only links (see "Links, not content" above).

### End of Stage 2 — what `clubbed-ideas.csv` now holds (17 columns, links only)

So Stage 3 knows exactly what to read and what to fill:

| # | Column | State at end of Stage 2 | Filled by |
|---|---|---|---|
| 1 | Source method | filled — `Competitor` / `Reddit` / `Other-niche` (which pool the idea came from) | merge |
| 2 | Brand fit | filled | merge |
| 3 | Asset | filled | merge |
| 4 | Format | filled (M1/M2; blank for M3) | merge |
| 5 | Distinct angle | filled | merge |
| 6 | Total domains | filled (M1 only) | merge |
| 7 | # comps | filled (M1 only) | merge |
| 8 | # posts | filled (M3 only) | merge |
| 9 | Beatability | filled (M1/M2) | merge |
| 10 | Effort | filled (M1/M2) | merge |
| 11 | Proof URLs | filled (M1/M2) | merge |
| 12 | RAG candidates | filled (links + scores) | Stage 2 |
| 13 | Topic pages we own | filled (catalogue links) | Stage 2 |
| 14 | Reference links | filled (de-duped union of the above) | Stage 2 |
| 15 | Reuse verdict | **EMPTY** | Stage 3 |
| 16 | Chosen links | **EMPTY** | Stage 3 |
| 17 | Why | **EMPTY** | Stage 3 |

> **Source method** is set at the merge by which block a row came from — the merge stacks the three pools
> contiguously (M1 Competitor → M3 Reddit → M2 Other-niche), so each block is tagged as it's written. It's
> carried for review only; Stage 3 ignores it.

**Stage 3 reads:** Asset · Distinct angle · Format · RAG candidates — and **fetches each candidate's page text
on demand** (look it up by URL in `content-database.csv`, or web-fetch the live page); nothing is stored inline.
**Stage 3 writes:** Reuse verdict · Chosen links · Why (the only empty columns).

---

## Stage 3 — LLM judgment per idea (the core)

**Run as parallel sub-agents — one idea per sub-agent.** Each sub-agent judges its one idea against its top
candidate pages (a sensible read-window — e.g. the top ~7 RAG candidates), passed in full. **The page text is
NOT stored in the clubbed file** — the runner **fetches each candidate's content on demand** from that idea's
`RAG candidates` links (look up the URL in `content-database.csv`, which holds `Full content`, or web-fetch the
live page) and fills the `[BRACKETS]` with the asset fields + the fetched candidate text, then sends the prompt
below **verbatim**. Everything between the rules *is* the prompt; keeping the whole thing here is the point, so
there's no gap between this recipe and what the agent actually gets.

> **How many sub-agents.** One per idea, so **N agents total** = rows in `clubbed-ideas.csv` (~505 for
> Testlify). They do **not** all run at once — keep roughly **10–16 in flight** and let the rest queue and
> drain as slots free. Don't fire 30+ simultaneously: each agent reads up to 7 full pages, so a big burst hits the
> model's tokens-per-minute rate limit and just thrashes on retries (slower, not faster) — and the
> orchestration layer caps concurrency around `min(16, cores − 2)` anyway. Bounded concurrency + a queue
> finishes the whole batch fastest.

> **Note — no similarity scores in the prompt.** The agent is given the candidates' **full text only**, never
> the match scores, so its verdict comes purely from reading — the score can't bias it. (Scores stay in the
> CSV for humans; they're just not passed to the model.)

### The sub-agent prompt — send this verbatim

> You are helping **[COMPANY]** decide one thing about a proposed content asset: should we **build it**, or does
> our **existing content already cover it** (fully or partly)? Read the existing pages and return one verdict,
> the links it points to, and why.
>
> **THE PROPOSED ASSET**
> - Asset (working title): **[ASSET]**
> - Distinct angle (the twist that makes it link-worthy): **[DISTINCT ANGLE]**
> - Format (its shape): **[FORMAT]**
>
> **OUR CLOSEST EXISTING PAGES (up to 7)** — full text of each; these are the **only** pages you may cite:
> ```
> [CANDIDATE 1 — title · link, then the full page text]
> [CANDIDATE 2 — …]
> … through …
> [CANDIDATE 7 — …]   (fewer may be present)
> ```
>
> **STEP 1 — run three tests on EACH candidate, judging by what you READ, not keyword overlap:**
> - **Topic test** — is the page actually about this asset's subject (not just sharing a word)?
> - **Format test** — is it the SAME SHAPE as the asset? A text article is NOT a calculator / quiz / index /
>   data report / template.
> - **Angle test** — does it already have the asset's distinct angle (above)?
>
> **STEP 2 — pick exactly ONE verdict, top-down, first match wins:**
>
> 🟢 **Already have it** — a page that already delivers this asset: SAME topic + SAME format + ALREADY has the
> angle, at good quality. Building again would just duplicate.
>   - Counts: asset *"Free Python skills test with public sample questions"* and we already publish exactly that.
>   - Does NOT count: same topic but a text article when the asset is a tool → Improve; same topic but missing
>     the angle → Improve.
>   - This is RARE — the angle is usually new. Don't reach for it.
>
> 🟡 **Improve existing** — ONE page is clearly this same topic but WEAKER than the asset would be (missing the
> angle, wrong/old format, thin, outdated). Building means upgrading THAT page, not making a second one.
>   - Counts: asset *"Bad-Hire Cost Calculator (per-role)"*; we have a 700-word text article *"what a bad hire
>     costs"* — same topic, no calculator. Upgrade it.
>   - Does NOT count: the page already has the angle → Already have it; no single page is on this topic, only
>     scattered bits → Build from parts.
>
> 🟠 **Build from parts** — NO single page is this asset, but ≥2 candidates each hold reusable material (data,
> definitions, sections) you'd pull from to build it. Build new, reuse the research.
>   - Counts: asset *"Cross-Industry Skills-Gap Index"*; we have *"top in-demand skills"* + *"skills gap
>     explained"* — neither is an index, but both feed one.
>   - Does NOT count: one page is basically the asset → Improve; nothing useful → Brand new.
>
> 🔴 **Brand new** — NO candidate is genuinely relevant: none really covers the topic, or only touches it
> superficially. Build from scratch.
>   - Counts: asset *"Annual State-of-Hiring Benchmark Report (original data)"*; candidates are only generic
>     hiring tips, none holds data.
>   - Does NOT count: any candidate that actually covers the topic or feeds the build → Improve / Build from parts.
>
> **RULES**
> - Cite ONLY links from the candidates above — never invent a URL.
> - Base the verdict on the FULL TEXT you actually read, not the title.
> - Be strict about 🟢: if a page lacks the asset's angle OR its format, it is at most 🟡 Improve, never 🟢.
>
> **RETURN EXACTLY THESE THREE FIELDS — nothing else:**
> - `Reuse verdict:` one of — Already have it / Improve existing / Build from parts / Brand new
> - `Chosen links:` the link(s) the verdict points to — 1 for Already-have; 1–3 for Improve; the source links
>   for Build from parts; **BLANK** for Brand new. Links only, drawn from the candidates.
> - `Why:` a short paragraph citing concrete evidence — what the page(s) have or lack that drove the verdict.

— end of the verbatim prompt —

The runner writes the three returned fields straight into the idea's `Reuse verdict`, `Chosen links`, and
`Why` columns.

---

## Output mapping (the assembly is traceable)

| `clubbed-ideas.csv` column | Filled from |
|---|---|
| RAG candidates | Stage 2 — top-15 links + titles + scores |
| Topic pages we own | Stage 2 — deterministic keyword catalogue (all topic pages) |
| Reference links | Stage 2 — de-duped union of the two link sets |
| Reuse verdict | Stage 3 — the decision tree (reads candidate text fetched on demand) |
| Chosen links | Stage 3 — subset of RAG candidates |
| Why | Stage 3 — the reasoning paragraph |

---

## Example output (illustrative)

| Asset | RAG candidates | Reuse verdict | Chosen links | Why |
|---|---|---|---|---|
| Free DISC Personality Test (interactive, shareable result) | DISC personality test — /tests/disc-personality (0.89); 16-personalities test — /tests/16-personalities (0.71); … | 🟢 Already have it | /tests/disc-personality | We already publish exactly this — a free, interactive DISC test with a shareable result. Same topic, same format, same angle, good quality. A second one would just duplicate; point internal links at the existing page instead. |
| Bad-Hire Cost Calculator (per-role) | What a wrong hire really costs — /blog/cost-of-bad-hire (0.81); Hiring mistakes guide — /blog/hiring-mistakes (0.62); … | 🟡 Improve existing | /blog/cost-of-bad-hire | Same topic, but the page is a 700-word text explainer with a static example — no interactive calculator and no per-role breakdown. The asset is that topic upgraded into a live tool, so improve this page rather than start fresh. |
| The Cross-Industry Skills-Gap Index | Top in-demand skills 2025 — /blog/in-demand-skills (0.49); Skills gap explained — /blog/skills-gap (0.47); … | 🟠 Build from parts | /blog/in-demand-skills; /blog/skills-gap | No single page is an index, but these two cover the underlying data and definitions — reuse them as research for the new index instead of starting from zero. |
| Annual State-of-Hiring Benchmark Report | (matches are only generic hiring tips, none holds data) | 🔴 Brand new | | Nothing in our library covers original benchmark data — the candidates only touch hiring tangentially. Build from scratch. |

---

## Gotchas

- **Weight the title, and search on the title — not the full angle (the v1 lesson).** v1 embedded only the
  body (so titles were drowned out) and queried with *Asset + the long Distinct angle* (which dragged results
  to tangents), so obvious pages like *"65 key skills-based hiring statistics"* never surfaced. Fix: a separate
  **title vector** blended with the body (α), plus a **title-only query**.
- **Boilerplate was a red herring** — the WordPress API's `content` field is the article body only (no nav /
  footer / related-posts), so there's almost nothing to strip. Don't burn a re-scrape chasing it; the real wins
  are title-weighting + clean query + reranker.
- **The reranker does the precision work** — dense retrieval just casts a wide net (top 30); `rerank-2.5` reads
  query + page and picks the real 7. Tune α / N / TOPK before blaming the model.
- **Index once, re-embed only on content change** — don't re-embed the whole site every run.
- **The score shortlists; the read decides** — Stage 3's verdict comes from reading the candidate pages, never
  from the retrieval score (the score isn't even shown to the judging agent).

### Retrieval tuning — what we tested and REJECTED (2026-06-30, 49-asset eval vs LLM ground truth)

Don't re-try these; they were measured on 49 sampled assets against independent LLM relevance labels and lost.
The **baseline above (full asset-title query → blended dense top-30 → rerank-2.5 → top-7) won every time.**

| Idea tried | Result | Why it lost |
|---|---|---|
| **Best-chunk rerank** (feed reranker the page's winning chunk, not its head) | ❌ worse | A long pillar page's *best* passage is an even stronger keyword match, so it promoted broad landing pages and buried focused blogs (aptitude guide #9→#1). Page-head is better. |
| **Short query** (cut the title at the colon) | ❌ overfit | Won the 2 hand-picked examples, lost across 50. |
| **LLM-crafted short query** (LLM rewrites the title to a clean topic) | ❌ worse | Full title beat it **recall@15 0.644 vs 0.530, precision 0.81 vs 0.69, head-to-head 28–6**. Shortening drops signal — the title's qualifiers/angle help the embedder+reranker. |
| **BM25 + RRF hybrid** (add lexical search, fuse rankings) | ❌ no gain | No measurable improvement on the cases; added moving parts. |
| **MMR diversity re-rank** | ❌ no gain | Re-introduced off-topic pages (an HRM page into psychometric) without lifting recall. |

> **The one real, still-open gap:** judges marked ~19 relevant pages/asset on average; the baseline surfaces
> ~64% of them at top-15 (recall@15 ≈ 0.64). Since query changes are a proven dead-end, the *only* lever worth
> testing for recall is **showing more results** (top-20/25) — and only if A/B'd on the same 49-asset harness.

> **Foreign-language pages:** exclude translation duplicates (URLs whose first path segment is an ISO language
> code — `/de/`, `/fr/`, `/ja/`, … — confirmed by a matching English-slug twin). They waste result slots. This
> is validated and safe to add to retrieval; not yet in the baseline script.

---

## Review output — always ship these two formats

Once `clubbed-ideas.csv` is filled, it's a wide, multi-thousand-character-per-cell file that no spreadsheet
renders cleanly. So the finished pool is **always delivered for review in two forms**, not just the raw CSV:

1. **A self-contained HTML viewer** — one offline `.html` file (no server, no internet) that holds all ideas
   inline. It must: show the at-a-glance columns (Source method, Brand fit, Asset, Format, Reuse verdict,
   Beatability, Effort, domains) with click-to-expand rows revealing Distinct angle, the full Why, and **every
   link group rendered clickable** — RAG candidates (with match scores), **Topic pages we own** (the catalogue),
   Chosen links, and Proof URLs; carry **search + per-column filters** (at minimum Source method, Brand fit,
   Reuse verdict, Format); and let a reviewer mark **Keep / Maybe / Cut + notes per idea** (saved in their
   browser, exportable to CSV). The file is link-only — there's no page content to drop.
2. **A public GitHub Pages link** — publish that HTML so a reviewer opens one URL, nothing to install. Use a
   personal GitHub account (never the client's own infra/org) and a **randomised, non-descriptive repo name**
   so the link isn't guessable or searchable; the repo is public (free-plan Pages requirement), so treat the
   URL as shareable-to-trusted-reviewers only, and **take it down when the review window closes**.
3. **Update the same page in place — never spin up a new one once it's shared.** The HTML viewer is a
   **mandatory output of every run** (build it even if you don't host it). But the moment its Pages link has
   been sent to anyone, re-runs must push to the **same repo / same URL** so the shared link never breaks —
   regenerate the HTML, copy it over the repo's `index.html`, commit, push. Do **not** create a second repo.
   Keep the push clone **inside the project** (e.g. `02-asset-engine/clubbed/output/_pages-repo/`), never in `/tmp`
   (it's wiped on reboot). Record the live URL + repo + push-clone path so the next session updates the right one.

> The viewer is built from the **review CSV** (the same link-only clubbed file), so the two stay in sync.
> Decisions live in the reviewer's browser — they hit **Export** to send marks back.

---

## Topic catalogue — the complete-list companion to the RAG match

The RAG match (Stage 2–3) answers *"is THIS exact asset already covered?"* — it's a **precision** tool that ranks the best few matches, so it deliberately leaves out same-topic pages that don't fit the asset's specific angle. Reviewers also want the opposite: *"show me EVERY page we already own on this topic."* That's a **recall/completeness** need, and no reranker can guarantee it (proven — see the rejected-experiments table). So ship a second, **deterministic** column alongside the RAG candidates.

**Column: `Topic pages we own`** — for each asset, *every* existing English page whose title/URL contains the asset's topic term(s). It's a plain keyword filter, so it **cannot silently drop a page** — if you own 15 "psychometric" pages, all 15 appear, every time.

How it's built (two parts — smart label, dumb match):
1. **Topic keywords (LLM, one pass):** an agent reads each asset title and emits 1–3 **distinctive** topic terms (e.g. `psychometric`, `resume screening`, `time to hire`) — *avoiding* generic words (`hiring/test/assessment/guide`) that would match everything.
2. **Deterministic match (no AI):** list every English page whose title/URL contains a keyword, with:
   - **light stemming** so `screening`/`screener`/`screen` all match (this is what catches `/ai-resume-screener/` for a "resume screening" asset);
   - **foreign-language pages excluded** (ISO-code first path segment — `/de/`, `/fr/`…);
   - **over-generic keywords dropped** (if one keyword matches > ~80 pages it's too broad — skip it), and the displayed list capped (~30) with the true count shown.

This is a **companion, not a replacement**: the RAG verdict still decides build/reuse; the catalogue gives the human the full neighbourhood. The one honest limit — it's literal: a relevant page whose title shares *no* keyword (e.g. a psychometric page titled only "Personality Assessment") won't appear under that term; search the sibling term too.
