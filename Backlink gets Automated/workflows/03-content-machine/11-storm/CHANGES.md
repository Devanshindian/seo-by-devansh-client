# STORM — our modifications

STORM is Stanford's deep-research tool. We run it **free on the Claude Code subscription** (via a local
shim) with **full-article scraping** (deep RAG) instead of its default snippet-only search. Below is every
change we made and why. Our edits live directly in the visible source under `engine/knowledge_storm/`, so
they survive a venv rebuild (`setup.sh` only recreates the environment, never the source).

## Where the edits live
- Our own files (100% ours): `scripts/shim.py`, `scripts/dataforseo_rm.py`, `scripts/run_storm.py`, `scripts/build_steplog.py`.
- Edits *inside* STORM's code live directly in the visible source (no patch/copy step):
  `engine/knowledge_storm/storm_wiki/modules/knowledge_curation.py`, `.../article_generation.py`, and
  `.../persona_generator.py`. Editing those files *is* editing what runs, because the venv imports via a `.pth`.

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
