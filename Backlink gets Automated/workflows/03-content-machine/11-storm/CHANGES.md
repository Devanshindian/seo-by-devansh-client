# STORM — our modifications

STORM is Stanford's deep-research tool. We run it **free on the Claude Code subscription** (via a local
shim) with **full-article scraping** (deep RAG) instead of its default snippet-only search. Below is every
change we made and why. Our edits live directly in the visible source under `engine/knowledge_storm/`, so
they survive a venv rebuild (`setup.sh` only recreates the environment, never the source).

## Where the edits live
- Our own files (100% ours): `scripts/shim.py`, `scripts/dataforseo_rm.py`, `scripts/run_storm.py`, `scripts/build_steplog.py`,
  `engine/knowledge_storm/brief.py`, `prompts/pick-researchers.md`.
- Edits *inside* STORM's code live directly in the visible source (no patch/copy step):
  `engine/knowledge_storm/storm_wiki/engine.py`, `.../modules/knowledge_curation.py`,
  `.../modules/outline_generation.py`, `.../modules/article_generation.py`, and
  `.../modules/persona_generator.py`. Editing those files *is* editing what runs, because the venv imports via a `.pth`.

**THE ARTICLE BRIEF — STORM is finally pointed at the angle (2026-08-03, IMPROVEMENTS.md change 1)**
- **The problem.** STORM received ONE argument: a truncated title. No angle, no spine, nothing. The hackathon
  article's dossier came back full of venue/food/Wi-Fi event logistics (37 sub-topics + 7 sections later cut
  as off-angle) — not because STORM drifts, but because it was never pointed anywhere.
- **The brief.** `run_storm.py --spine-file <spine.json>` (built by the conductor's new Step 2a from title +
  angle + brand + the DataForSEO competitor read) registers title/angle/spine/about/not-about in
  `engine/knowledge_storm/brief.py` — a set-once/read-many registry, chosen over threading five parameters
  through a dozen vendored signatures. No brief set ⇒ every prompt behaves exactly as before (bare runs unchanged).
- **Folder = slug.** `run_storm.py --folder <slug>` → `engine.py run(folder_name=...)`. The topic string used
  to double as the folder name (the reason the angle was stripped in the first place); now the folder matches
  every other engine (`storm/out/<hub>/<slug>/`) and the topic stays a pure research subject. All 7 existing
  topic folders were renamed to their slugs on 2026-08-03 (one orphaned gap-iteration folder was adopted as
  `strategic-interview-questions-paired-strong/iteration-1` and its manifest repaired — the old newest-dir
  detection had lost it, see rerun_storm.py below). NOTE: a hub's own dossier files and its spokes' folders
  now share `out/<hub-slug>/`; `source_match.load_snippets` (recursive) therefore sees spoke snippets too —
  harmless (it only attaches a URL on a genuine sentence match) but worth knowing.
- **Researcher picker replaces the Wikipedia route** (`persona_generator.py` + `prompts/pick-researchers.md`).
  The old route asked for related Wikipedia pages, scraped their tables of contents, and picked personas from
  them — which is how a HIRING-hackathon article got staffed with a public-prize-event organiser (Wikipedia's
  hackathon page is about prize contests), and which broke a whole run when Wikipedia 403'd. With a brief set,
  `PickResearchTeam` picks exactly N researchers (conductor passes `--perspectives 4`) from title/angle/spine/
  about/not-about: builder · SCEPTIC (costs, failures, who it excludes — the only carrier of that job) ·
  evidence · practitioner. No 'Basic fact writer' default. JSON out, one retry, and on failure it FALLS BACK
  to the old Wikipedia route rather than dying.
- **The brief reaches three prompt families** (same instruction, three files — edit together):
  `knowledge_curation.py` (AskQuestion + AskQuestionWithPersona: the first question and every follow-up),
  `outline_generation.py` (both outline signatures: "every heading must earn its place against the spine"),
  `article_generation.py` (WriteSection rule 5: off-angle material left out; costs/failures ARE on-spine).
  The shared line: *material that does not serve the asset title and the angle does not belong.*
- **DECIDED (with Devansh): the primary keyword is NOT passed to STORM** — it is a ranking target, not a
  research target (this revises IMPROVEMENTS.md change 3's original "primary keyword steers STORM" wording).

**Persona generation — Wikipedia User-Agent fix (`persona_generator.py`, 2026-07-13)**
- `get_wiki_page_title_and_toc()` did a bare `requests.get(url)`. Wikipedia now returns **403** to requests with
  no descriptive User-Agent, so `soup.find("h1")` was `None` → `'NoneType' object has no attribute 'text'`. Every
  related-topic lookup failed → personas degraded to "N/A" → generic questions → few/junk sources → empty outline
  → ~1,000-word stub (vs a healthy ~9,000). Fix: send a real User-Agent + guard the missing-`h1` case. This was
  the root cause of the "thin STORM / testlify-only sources" regression.

**Scrape fallback — DataForSEO content-parsing (`scripts/dataforseo_rm.py`, 2026-07-14)**
- When `trafilatura` extracts < 200 chars from a page (JS-rendered or bot-blocked → "empty HTML tree"), the
  retriever now falls back to DataForSEO's server-side content parser (`on_page/content_parsing/live`,
  `enable_javascript=true`) and lifts the `main_topic`/`secondary_topic` text (header/footer/cookie skipped).
  **Bounded** (`max_dfs_fallbacks=25`/run, logged when hit) so it can't blow up time/cost, and **fail-safe**
  (any error → returns "" → caller uses the SERP snippet exactly as before). Turns ~114 thin snippet-only
  sources into full-text ones. (Chose this over a Playwright browser-agent: no heavy dep, reuses DFS creds.)

**Quieter filename truncation (`engine/knowledge_storm/utils.py`, 2026-07-14)**
- `truncate_filename` logged a WARNING every time it shortened a long topic. gap-check intentionally passes long
  gap-queries as STORM topics (and the run dir is renamed to `iteration-N` afterwards), so that warning was pure
  noise — demoted to `logging.debug`.

**Polish step RENUMBERS citations — card-building must read the pre-polish article (2026-08-01)**
- STORM's Step 5 (`article_polish.py`, `PolishPage`) hands the whole ~34k-word article to the LLM to remove
  repetition. It removes almost nothing (34,230 -> 34,580 words) but **rewrites the `[n]` markers**: 93% of
  shared sentences come back with a different citation number. Measured on running-hiring-hackathon, the
  cited source is the true source **78-88% pre-polish vs 1-6% post-polish** (250 sentences x 3 dossiers).
- Downstream damage before we caught it: wrong URL on the card -> the write phase's source check cuts it ->
  the same wrong URL is shared by 20-30 sibling cards -> propagation drags them all in. One article: 66
  proven-bad URLs, 250 contaminated cards, 374 cut.
- **Fix:** `13-research-structure/scripts/harvest_storm.py` now reads `storm_gen_article.txt`, not
  `storm_gen_article_polished.txt`. Content is identical apart from the polish-written `# summary` lead,
  which `_split_sections` already drops (verified: 0 sentences lost across all 3 dossiers).
- The polished file is still produced and is still what `article.html` and gap-check read — those judge
  CONTENT, not citations, so they are unaffected. Note `article.html`'s clickable citations are therefore
  wrong; it is a preview, not a source of truth.

## The changes

**LLM backend**
- STORM runs on Claude Code, not a paid API — `shim.py` is a local OpenAI-compatible server that forwards
  every request to `claude -p`. Cost: $0 in API fees.

**Search & scrape** (`dataforseo_rm.py`)
- Replaced STORM's default DuckDuckGo search (kept crashing) with a DataForSEO Google retriever.
- Deep RAG: after finding links, we fetch each page ourselves (free) and extract the full article body with
  trafilatura, chunked — always on (the only mode), up to ~2,600 words/article (14 chunks × 1,200 chars).

**Interview** (`engine/knowledge_storm/storm_wiki/modules/knowledge_curation.py`)
- Answer step reads ALL chunks of each source, capped at 2,500 words/article + a 15,000-word global safety
  cap (was: only the first chunk, shared 1,000-word total). — the `DEEP-RAG TWEAK` block.
- Breadth floor: the persona is instructed not to end before asking 3 questions (a strong nudge, not a hard
  block), so rich answers don't starve
  source breadth. — the `BREADTH FLOOR` block.

**Article writing** (`engine/knowledge_storm/storm_wiki/modules/article_generation.py`)
- Each section is written from 8 sources (was 3) and up to 5,000 words of evidence (was 1,500).
- Enriched `WriteSection` prompt: "capture the evidence densely for the downstream write phase" — favor
  concrete specifics, be comprehensive, no length target, every sentence cited. (Format rules left intact.)

**Run settings** (`run_storm.py`)
- outline_gen 400→800 tokens (richer outline / more sections), article_gen 700→4000 (~3,000-word sections),
  article_polish 4000→16000, retrieve_top_k 3→8.

## Proven config (recruiting-metrics benchmark topic, fully fresh)
`--turns 4 --topk 5 --article --polish` → ~10,000 words, 368 citations (1 per 27 words),
111 sources gathered / 45 cited, ~7.4 min. Research-grade, densely-cited dossier.
