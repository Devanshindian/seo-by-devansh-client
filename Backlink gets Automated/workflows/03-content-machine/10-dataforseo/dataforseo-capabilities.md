# DataForSEO Capabilities Map — Testlify Content-Research Pipeline

> Reference / research map of what the API *can* do — NOT the spec of what shipped. The built engine diverges
> where live runs proved better: keyword expansion uses the **tight net (`keyword_suggestions`) + ranked net
> (`ranked_keywords`)**, and the wide net (`keyword_ideas` / Keywords-For-Keywords) was **dropped as noise**. The
> orchestrator's real step order is `run_dataforseo.py` (steps 0-7); treat the ⭐/shortlist below as options, not
> the recipe.

One map, organized by pipeline step. Per step: the exact endpoints to use (name + path), **ONE recommended primary** per job (marked ⭐), and any capability we hadn't considered (marked 💡). Ends with a must-use shortlist and a skip list.

Defaults for every call: `location_code=2840` (US), `language_code=en`.

---

## 1) Seed + Expand keywords

Goal: turn 1-3 seed keywords from the asset topic into a broad candidate pool. Run several expansion mechanics together — they surface different things — then dedupe.

| Endpoint | Path | Role |
|---|---|---|
| ⭐ **Google Ads — Keywords For Keywords** | `/v3/keywords_data/google_ads/keywords_for_keywords/live` | **Primary expansion.** Up to 20 seeds → ~20,000 suggestions with volume/CPC/competition already attached — one call both expands AND pre-filters. |
| DataForSEO Labs — Keyword Ideas | `/v3/dataforseo_labs/google/keyword_ideas/live` | Category/relevance expansion (need not contain seed) — widest thematic net. |
| DataForSEO Labs — Keyword Suggestions | `/v3/dataforseo_labs/google/keyword_suggestions/live` | Full-text expansion (must contain seed) — long-tail modifiers + question phrasings → H2/H3 subtopics. |
| DataForSEO Labs — Related Keywords | `/v3/dataforseo_labs/google/related_keywords/live` | Google's own "searches related to" as a depth tree (use depth 2-3); the tree reveals topic-cluster structure for internal linking. |
| Google Autocomplete — Live Advanced | `/v3/serp/google/autocomplete/live/advanced` | Live alphabet-soup autosuggest; vary `cursor_pointer` for real user phrasings. Cheap ($0.002). |
| Google Trends — Explore | `/v3/keywords_data/google_trends/explore/live` | Rising/related queries & topics — breakout terms the volume-lagged Ads planner misses. |

💡 **Not considered:** `keyword_annotations` / concept groupings returned by Keywords For Keywords are effectively **free topic-cluster labels** — auto-group the pool into secondary-keyword sets with no separate clustering step. `date_from/date_to` on the Ads endpoints pulls **up to 4 years** of monthly history for real seasonality, not just 12 months.

---

## 2) Metrics + Filter (volume / difficulty)

Goal: attach authoritative volume + KD to the candidate pool, then apply thresholds.

| Endpoint | Path | Role |
|---|---|---|
| ⭐ **DataForSEO Labs — Keyword Overview** | `/v3/dataforseo_labs/google/keyword_overview/live` | **Primary filter workhorse.** One call per ≤700 keywords returns volume + KD + intent + CPC (+ optional SERP info) together — collapses three separate calls (volume, difficulty, intent). |
| Google Ads — Search Volume | `/v3/keywords_data/google_ads/search_volume/live` | Authoritative Google Ads volume + 12-mo `monthly_searches` trend for ≤1,000 keywords. Use when you want true Ads volume + seasonality as the volume gate. |
| Labs — Bulk Keyword Difficulty | `/v3/dataforseo_labs/google/bulk_keyword_difficulty/live` | Lean KD-only pass for ≤1,000 keywords (fallback/scale when Overview's 700 cap or full bundle isn't needed). |
| Labs — Historical Keyword Data | `/v3/dataforseo_labs/google/historical_keyword_data/live` | Seasonality/trajectory check on the shortlisted primary (rising/flat/declining) before committing. |
| Google Trends — Explore | `/v3/keywords_data/google_trends/explore/live` | Relative-interest momentum cross-check (never a volume replacement). |

💡 **Not considered:** `include_serp_info` on the Labs expansion/overview endpoints appends SERP-feature presence + result count **per keyword without a live SERP call** — cheap pre-screen before step 4. `include_clickstream_data` swaps Ads-estimate volumes for real user-panel volumes (~2x cost).

---

## 3) Search intent

Goal: keep informational/commercial-investigation terms (blog-appropriate), drop pure navigational/transactional; confirm the primary matches the article format.

| Endpoint | Path | Role |
|---|---|---|
| ⭐ **DataForSEO Labs — Search Intent** | `/v3/dataforseo_labs/google/search_intent/live` | **Primary.** ML intent (+ secondary intents w/ probabilities) for ≤1,000 keywords. **Location-free (language only)**, so one cheap call covers a whole list. |

Note: if you already ran **Keyword Overview** (step 2), intent is bundled there — only call this standalone for a large list you didn't put through Overview.

---

## 4) Live SERP (features / PAA / AI Overview / top pages)

Goal: read the live SERP for the primary keyword — organic top pages, featured snippet, PAA, AI Overview, related searches — populating the SERP section of the brief.

| Endpoint | Path | Role |
|---|---|---|
| ⭐ **Google Organic — Live Advanced** | `/v3/serp/google/organic/live/advanced` | **THE core SERP read.** One response = top organic pages (competitor set), `featured_snippet`, `people_also_ask`, `ai_overview`, `related_searches`, video/images/knowledge_graph, `discussions_and_forums`. |
| Google Organic — Task Post/Ready/Get | `/v3/serp/google/organic/task_post` (+ `/tasks_ready`, `/task_get/advanced`) | Cheaper async variant for **bulk** overnight SERP reads (whole content calendar). |
| SERP Locations / Languages | `/v3/serp/google/locations`, `/v3/serp/google/languages` | One-time lookup for correct location/language codes. |

💡 **Must-set flags (easy to miss):** `load_async_ai_overview=true` is **required** to reliably capture the AI Overview block (it loads async and is otherwise missing). `people_also_ask_click_depth` (1-4) expands the **nested** PAA tree. Both directly control whether the brief captures AIO and full PAA.

---

## 5) Competitor content gaps

Goal: find who actually wins our keyword cluster, which keywords/pages they cover that we don't, and read their page structure.

| Endpoint | Path | Role |
|---|---|---|
| ⭐ **Labs — SERP Competitors** | `/v3/dataforseo_labs/google/serp_competitors/live` | **Primary "who competes."** Feed our primary + secondary set → the domains actually winning THIS cluster (not generic brand rivals). Their pages become the read/beat targets. |
| ⭐ **Labs — Domain Intersection** (`intersections=false`) | `/v3/dataforseo_labs/google/domain_intersection/live` | **Primary gap engine.** target1=strong competitor, target2=testlify.com → keywords the competitor ranks for that Testlify does NOT, in one call. |
| Labs — Ranked Keywords | `/v3/dataforseo_labs/google/ranked_keywords/live` | Full keyword footprint of a competitor domain/URL; filter rank≤10 + volume for proven candidates. `item_types` incl. `ai_overview_reference` (see step 6). |
| Labs — Page Intersection | `/v3/dataforseo_labs/google/page_intersection/live` | Give it the top-ranking URLs for our primary + `exclude_pages`=our page → the exact keyword coverage the winning pages share but we miss. |
| Labs — Relevant Pages | `/v3/dataforseo_labs/google/relevant_pages/live` | A rival's best-performing pages by traffic/keyword count → which assets to read and out-build; also our own internal-link targets. |
| Labs — Bulk Traffic Estimation | `/v3/dataforseo_labs/google/bulk_traffic_estimation/live` | Page-level ETV for ≤1,000 URLs in one call → only teardown-read the pages that actually get traffic. |
| ⭐ **On-Page — Content Parsing (live)** | `/v3/on_page/content_parsing/live` | **Primary competitor-page reader.** Live, no crawl: exact H1-H6 tree, main/secondary content blocks, links; `markdown_view=true` for clean text. |
| On-Page — Instant Pages | `/v3/on_page/instant_pages` | Quantified benchmarks per competitor URL: word count, 3 readability indices, 100-pt `onpage_score`, title/desc patterns. Also our own post-write QA gate. |
| SERP AI Summary | `/v3/serp/ai_summary` | Feed a prior SERP `task_id` + prompt with `fetch_content=true`, `include_links=true` → an LLM reads the ranking pages and returns a cited content-gap summary. Collapses "read pages + assemble" into one $0.01 call. |
| Backlinks — Bulk Pages Summary | `/v3/backlinks/bulk_pages_summary/live` | rank + referring domains + backlinks + spam score for every SERP URL in ONE call → turns "keyword difficulty" into concrete per-competitor authority (the difficulty block of the brief). |

💡 **Not considered:** Domain Intersection with `intersections=false` is a purpose-built gap finder — cheaper/faster than diffing two Ranked Keywords pulls yourself. Page Intersection + `exclude_pages` gives a **per-article coverage checklist**. On-Page's Content Parsing/Instant Pages are **live single-URL** (no crawl task), so they're genuine competitor readers, not just site-audit crawlers.

---

## 6) AEO / GEO (AI answers / citations)

Goal: see which questions LLMs answer for our topic, which domains/pages they cite, and the sub-queries our article must cover to be citation-eligible.

| Endpoint | Path | Role |
|---|---|---|
| ⭐ **LLM Mentions — search (live)** | `/v3/ai_optimization/llm_mentions/search/live` | **Primary AEO research.** Queries a pre-built DB of real ChatGPT/Google-AIO prompts+answers → question text, markdown answer, ranked `sources[]`, and `ai_search_volume` per question — WITHOUT paying per live prompt. PAA-mining + citation-gap combined. |
| LLM Mentions — top_pages (live) | `/v3/ai_optimization/llm_mentions/top_pages/live` | The exact competitor URLs LLMs cite most for our topic — pages to match/beat. |
| LLM Mentions — top_domains (live) | `/v3/ai_optimization/llm_mentions/top_domains/live` | The authority domains dominating AI citations in our niche; shows whether testlify.com appears. |
| LLM Mentions — cross_aggregated_metrics (live) | `/v3/ai_optimization/llm_mentions/cross_aggregated_metrics/live` | Benchmark Testlify vs named competitors' AI share-of-voice in a single call — prioritizes which asset closes the biggest AI-visibility gap. |
| LLM Scraper — ChatGPT (live/advanced) | `/v3/ai_optimization/chat_gpt/llm_scraper/live/advanced` | Live ChatGPT Search answer for the primary keyword: ranked `sources[]`, `fan_out_queries` (H2/FAQ outline), `brand_entities[]` (are competitors/us named?). |
| LLM Scraper — Gemini (live/advanced) | `/v3/ai_optimization/gemini/llm_scraper/live/advanced` | Closest proxy for Google AI Overview sourcing; diff its `sources[]` vs ChatGPT's (both = must-beat, one = opportunity). |
| Google AI Mode — Live Advanced | `/v3/serp/google/ai_mode/live/advanced` | Google's full conversational AI answer + its citation URLs/snippets — exactly which pages Google's AI cites for our query. |
| AI Keyword Data — search volume (live) | `/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live` | `ai_search_volume` (from PAA frequency) for question-shaped keywords that classic Ads volume undercounts — feeds the expand/filter step for AEO. |
| LLM Responses — ChatGPT / Claude / Gemini / Perplexity (live) | `/v3/ai_optimization/{chat_gpt|claude|gemini|perplexity}/llm_responses/live` | Run our target question through each engine with `web_search` on → read `annotations[]` for cross-model citation coverage so AEO isn't tuned to one engine. |

💡 **Not considered:** `fan_out_queries` on both Scraper and Mentions responses is a **ready-made H2/FAQ outline** — the sub-questions the AI decomposed our query into, i.e. exactly what the article must answer. Mentions gives all this from a **database** (no per-prompt cost); ChatGPT mention data is US/English only.

---

## 7) Other useful (situational, not per-article)

| Endpoint | Path | When |
|---|---|---|
| Labs — Competitors Domain | `/v3/dataforseo_labs/google/competitors_domain/live` | One-time: build the standing list of content competitors to monitor. |
| Labs — Keywords For Site | `/v3/dataforseo_labs/google/keywords_for_site/live` | Lightweight content-gap probe on a competitor domain/subfolder. |
| Labs — Top Searches | `/v3/dataforseo_labs/google/top_searches/live` | Top-of-funnel demand sizing / whitespace discovery when seeding a new topic. |
| Content Analysis — Search + Summary | `/v3/content_analysis/search/live`, `/summary/live` | Harvest quotable, attributable third-party mentions (author/domain/snippet/date) to cite; sentiment landscape for the article angle. Brand/competitor monitoring. |
| Backlinks — Bulk Ranks / Bulk Referring Domains | `/v3/backlinks/bulk_ranks/live`, `/bulk_referring_domains/live` | Standalone SERP-authority signals if not using Bulk Pages Summary. |
| Domain Analytics — Domain Technologies (live) | `/v3/domain_analytics/technologies/domain_technologies/live` | Side lookup: a competitor's CMS + title + meta desc + domain rank in one call. |
| On-Page — Microdata / Raw HTML | `/v3/on_page/microdata`, `/raw_html` | Which schema types (FAQPage/HowTo/Article) winning pages deploy — an AEO lever. Requires a prior crawl task. |
| On-Page — Lighthouse (live) | `/v3/on_page/lighthouse/live/json` | Optional technical/perf QA on our own published article. |

---

## Must-use shortlist (minimal set to run the pipeline)

Run these seven, in order, and you have a complete per-asset brief:

1. **Google Ads — Keywords For Keywords** `/v3/keywords_data/google_ads/keywords_for_keywords/live` — expand (volume attached).
2. **Labs — Keyword Overview** `/v3/dataforseo_labs/google/keyword_overview/live` — volume + KD + intent bundle; filter, pick 1 primary + 3-5 secondary. (Absorbs step 3 intent.)
3. **Google Organic — Live Advanced** `/v3/serp/google/organic/live/advanced` — SERP features + PAA + AI Overview + competitor set. Set `load_async_ai_overview=true` and `people_also_ask_click_depth`.
4. **Labs — Domain Intersection** (`intersections=false`) `/v3/dataforseo_labs/google/domain_intersection/live` — competitor keyword gaps.
5. **On-Page — Content Parsing (live)** `/v3/on_page/content_parsing/live` — read the top competitor pages' structure.
6. **LLM Mentions — search (live)** `/v3/ai_optimization/llm_mentions/search/live` — AEO questions + citation gaps + fan-out outline.
7. **Backlinks — Bulk Pages Summary** `/v3/backlinks/bulk_pages_summary/live` — per-competitor authority = concrete difficulty.

(Add Labs — SERP Competitors before #4 if you don't already know the competitor domains; add Gemini/ChatGPT Scraper for cross-model AEO depth.)

---

## Skip list (confirmed none/low — do not wire into the pipeline)

- **SERP: Regular / HTML variants** (`/organic/live/regular`, `/live/html`) — Advanced supersedes; Regular omits the feature blocks we need.
- **SERP: all non-Google engines** — Bing, Yahoo, Baidu, Seznam, Naver (Google is our sole target; Bing only if we later chase Copilot).
- **SERP verticals: Maps, Local Finder, Events, Jobs, Dataset, Finance, Search-by-Image, Images/News verticals** — the organic response already carries the in-SERP image/news/top-stories packs.
- **SERP: YouTube (all)** — outside the blog pipeline.
- **Keywords Data: all Bing endpoints; Ad Traffic By Keywords; Status/Locations/Languages helpers (beyond one-time)** — paid-ad forecasting / redundant with Google-side tools.
- **DataForSEO Trends: Demography, Subregion Interests, Merged Data** — demographics/geo out of scope.
- **Labs: Categories For Keywords, Keywords For Categories, Domain Rank Overview, Subdomains, Historical Rank Overview** — low/summary-level, not keyword-level inputs.
- **Content Analysis: Sentiment, Rating Distribution, Phrase/Category Trends, taxonomy/helper/appendix endpoints** — colour-only or reference; Search + Summary cover our need.
- **Backlinks: History, Anchors, Referring Domains/Networks, Competitors, Domain/Page Intersection, Timeseries, Bulk Spam Score** — link-building/outreach tools, not content research. (Keep only the Bulk authority calls.)
- **On-Page: full-crawl chain** (`task_post`, `pages`, `resources`, `duplicate_*`, `links`, `redirect_chains`, `waterfall`, screenshots, `keyword_density`) — live Content Parsing + Instant Pages cover ~90% without a crawl.
- **Entire groups — Domain Analytics (beyond the one tech lookup), Business Data, Merchant (Amazon/Google), App Data (Google/Apple)** — entity/review/product/app databases; zero keyword/SERP/AEO capability. Skip wholesale.
