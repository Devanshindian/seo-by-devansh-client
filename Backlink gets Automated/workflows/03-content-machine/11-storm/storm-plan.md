---
type: plan (working; validated on recruiting-metrics + onboarding-metrics topics)
stage: content-machine — research (produces the EVIDENCE DOSSIER the /write phase draws from, alongside the DataForSEO brief)
reads: an asset topic (title + distinct angle, from clubbed-ideas.csv); DataForSEO creds (from storm/.env — DFS_LOGIN / DFS_PW; master copy in ~/.testlify-access.md)
produces: one dossier per run under out/<topic-slug>/ — storm_gen_article_polished.txt (densely-cited research), plus the full research pool (raw_search_results.json), the interviews (conversation_log.json), the outline, the call log, and a viewable article.html (the dossier rendered with clickable citations).
last_updated: 2026-07-14
---

# STORM plan — asset topic → densely-cited evidence dossier

## What this does

Turn one asset topic into a **research dossier**: a long, densely-cited write-up of everything the open web
says about the topic, with every claim traceable to a scraped source. It is the deep-evidence half of the
research phase — the DataForSEO `research-plan.md` gives keywords + SERP + the competitor outline; STORM gives
the **grounded facts** to write from. Both feed `/write`. STORM never writes the final article; it manufactures
the evidence that makes our article non-generic.

## The one rule

**Every sentence is grounded in a scraped source, and the output is evidence — never the published article.**
STORM answers only from what it actually retrieved and read (its interview prompt enforces "every sentence
supported by the gathered information"). The dossier is structured by STORM's own encyclopedic outline, which
is *research scaffolding*, not our article's outline. If a claim can't point to a source in `raw_search_results.json`,
it doesn't belong.

## How STORM runs on a headless CLI (Claude or Codex) for $0

Every LLM call goes through `scripts/shim.py`, a local OpenAI-compatible server that forwards each request to a
headless CLI — `claude -p` (default) or `codex exec`, chosen with `--provider` / `SHIM_PROVIDER`. So STORM's five
model slots all run on the subscription — no paid API, no key. DataForSEO (SERP + our free page scrape) is the only
outside cost (~$0.10–0.20/run).

## Credentials (the `.env`)

The only credentials STORM needs are the **DataForSEO** login + API password. They live in **`storm/.env`**
as `DFS_LOGIN` / `DFS_PW` (master copy in `~/.testlify-access.md`; account `akash@testlify.com`).

- **Where they're loaded:** `scripts/run_storm.py` calls `load_dotenv(storm/.env)` at startup — before it builds
  the retriever — so you never `export` anything by hand. A real env var already set in the shell still wins over
  the file (useful for a one-off override).
- **Where they're used:** `scripts/dataforseo_rm.py` reads `os.environ['DFS_LOGIN']` / `os.environ['DFS_PW']`,
  base64-encodes them, and sends them as the Basic-auth header on every DataForSEO SERP call. Nothing else touches them.
- **The shim needs no creds** — all LLM calls run free through `scripts/shim.py` on the local subscription.
- Optional `SHIM_URL` in the same `.env` overrides the bridge URL (default `http://127.0.0.1:8081/v1`).

`.env` holds a live secret — keep it in this folder, never commit or share it.

## Inputs

| Input | What | Default |
|---|---|---|
| Asset topic | the STORM `topic` string — built from the **Asset title + Distinct angle** (same two anchors as `research-plan.md`) | — |
| `--turns N` | max questions per persona (breadth floor forces ≥3) | 4 |
| `--topk N` | links kept per search | 5 |
| `--perspectives N` | persona count = N + 1; **the breadth dial** | 3 |
| `--article --polish` | write + polish the dossier (omit for research-only) | on |
| Creds | `DFS_LOGIN` / `DFS_PW` — kept in `storm/.env`, auto-loaded by `run_storm.py` (no manual export). Master copy in `~/.testlify-access.md`. Consumed by `scripts/dataforseo_rm.py`. | — |

## What you produce (named output of every step)

Everything lands under `out/<topic-slug>/`. This table is the authoritative file map (the Traceability table
below is another view of it):

| Step | Files it writes (under `out/<topic-slug>/`) |
|---|---|
| 0 Set up the run | *(no file — STORM is just configured in memory)* |
| 1 Personas | persona list (kept in memory; it lands inside `conversation_log.json` at Step 2) |
| 2 Interviews (research) | `conversation_log.json` (every Q&A + its sources), `raw_search_results.json` (**the full research pool** — all scraped chunks) |
| 3 Outline | `direct_gen_outline.txt` (first pass), `storm_gen_outline.txt` (refined) |
| 4 Write sections | `storm_gen_article.txt` (drafted dossier, pre-polish), `url_to_info.json` (the article's cited-source map) |
| 5 Polish | **`storm_gen_article_polished.txt`** (THE dossier `/write` receives) |
| end (auto, after Step 5) | `run_config.json` (the knobs used), `llm_call_history.jsonl` (every LLM call) |
| 6 Step log | `STEP-LOG.md` |
| 7 Preview (viewable) | `article.html` (the dossier rendered with clickable citations + references) |

---

## How to run (per topic)

```
cd "<this folder>"
# DataForSEO creds auto-load from storm/.env — no export needed (see "Credentials" above).
nohup venv/bin/python scripts/shim.py > logs/shim.out 2>&1 &      # start the Claude bridge (once)
venv/bin/python scripts/run_storm.py "<ASSET TOPIC>" --turns 4 --topk 5 --article --polish
python  scripts/build_steplog.py out/<topic-slug>                 # render STEP-LOG.md
python  preview/view-article.py  out/<topic-slug>                 # render viewable article.html
```
One `run_storm.py` call runs Steps 1–5 end to end, and every run is genuinely fresh — it re-scrapes the web
each run.

---

## The steps, in order

### Step 0 — Set up the run  (shim + knobs)
Two things happen here, both run by hand:

**a) Start the Claude bridge** = run `scripts/shim.py`:
```
nohup venv/bin/python scripts/shim.py > logs/shim.out 2>&1 &
```
This launches a small local server on port 8081. STORM will send its LLM calls there; the server forwards each
one to `claude -p` (headless Claude Code) and hands the answer back. It stays running in the background — this
is what lets STORM run on Claude for free. **Nothing auto-starts it; you must start it before `run_storm.py`.**

**b) Run STORM** — fill in your choices from the **Inputs** table above (the `<...>` bits) and run:
```
venv/bin/python scripts/run_storm.py "<topic>" --turns <N> --topk <N> --perspectives <N> --article --polish
```
Fill in: **topic**, **--turns**, **--topk**, **--perspectives** (take them from the Inputs table). Everything
else is already set inside the script. This connects the models to the shim, plugs in our scraper, and starts the run.
- **Files:** `scripts/shim.py` (bridge), `scripts/run_storm.py` (control panel), `scripts/dataforseo_rm.py` (retriever), `engine/knowledge_storm/lm.py` (LM wrapper), `engine/knowledge_storm/storm_wiki/engine.py` (the conductor).
- **Output:** *no file.* Step 0 just gets STORM set up and ready — there's nothing to save yet.
- **Gotcha:** the shim must be up on port 8081 first (you start it by hand — `run_storm.py` does not), and `storm/.env` must hold valid `DFS_LOGIN`/`DFS_PW` (auto-loaded) — otherwise every call fails silently.

### Step 1 — Personas  (the viewpoints)
Invent the different "editors" who will interview the expert, so the topic is researched from multiple angles.
An LLM lists related topics, tries to read their Wikipedia tables-of-contents, then generates N diverse personas
plus a default "basic fact writer." Persona count = `--perspectives` + 1.
- **Files:** `engine/knowledge_storm/storm_wiki/modules/persona_generator.py`.
- **Output:** the persona list (recorded per-perspective inside `conversation_log.json`).
- **Gotcha:** the Wikipedia-TOC scrape used to 403 → `'NoneType' … text`, which starved persona generation (the root cause of the old "thin STORM" runs). Fixed 2026-07-13 (real User-Agent + a missing-`h1` guard — see `CHANGES.md`); the TOCs are only optional *inspiration*, so even a miss now leaves strong, diverse personas. Want more breadth? Raise `--perspectives`, **not** `--turns`.

### Step 2 — Grounded interviews  (the research — where all evidence is gathered)
**Input:** the personas from Step 1 + the topic.

**Process:** each persona asks up to `--turns` questions (at least 3 — our breadth-floor edit). For each
question, the "expert" — all the interview logic lives in `engine/knowledge_storm/storm_wiki/modules/knowledge_curation.py` —
turns the question into Google search queries, hands them to our retriever `scripts/dataforseo_rm.py`, which
runs the DataForSEO search and **scrapes the full articles** it finds. The expert then answers using **only**
what was scraped ("every sentence supported by the gathered information"). Every scraped chunk is collected into
the information table by `engine/knowledge_storm/storm_wiki/modules/storm_dataclass.py`.

**Output:**
- `conversation_log.json` — every Q&A + the sources behind each answer.
- `raw_search_results.json` — the full research pool (all scraped chunks). *(`url_to_info.json` is NOT written here — it comes at Step 4.)*

**Gotcha:** some pages block our scraper and silently drop out, so the pool can be thinner than the search suggested.

### Step 3 — Outline
Draft the dossier's section structure from what the interviews surfaced. An LLM writes a first "direct" outline,
then a refined one informed by the conversations.
- **Files:** `engine/knowledge_storm/storm_wiki/modules/outline_generation.py`.
- **Output:** `direct_gen_outline.txt` (first pass) → `storm_gen_outline.txt` (refined).

### Step 4 — Write the sections  (RAG over the pool)
**Input:** the outline from Step 3 + the research pool (`raw_search_results.json` from Step 2).

**Process:** for each outline heading, `engine/knowledge_storm/storm_wiki/modules/storm_dataclass.py` embeds the
heading (embeddings from `engine/knowledge_storm/encoder.py`) and semantic-searches the pool for the top **8**
most-relevant chunks (`retrieve_top_k=8`), capped at 5,000 words. Those chunks go to
`engine/knowledge_storm/storm_wiki/modules/article_generation.py`, whose **enriched WriteSection prompt** writes
a dense, fully-cited section from them ("favor concrete specifics, no length target, every sentence cited"). No
re-scraping — it writes only from the pool.

**Output:**
- `storm_gen_article.txt` — the drafted dossier (pre-polish).
- `url_to_info.json` — the article's cited-source map (the sources that made it in, with their citation numbers).

**Gotcha:** a source never in any section's top-8 is dropped, so only ~40% of gathered sources get cited — the rest stay in `raw_search_results.json` as surplus the write phase can still mine.

### Step 5 — Polish  (lead + assemble)
Add a 4-paragraph lead/summary and finalize. `remove_duplicate` is **off**, so the body passes through unchanged
(no truncation) and only the lead is generated.
- **Files:** `engine/knowledge_storm/storm_wiki/modules/article_polish.py`.
- **Output:** **`storm_gen_article_polished.txt`** — the dossier `/write` receives.
- **Gotcha:** with dedup off there is **no total-length cap** — the dossier = sum of all sections. The polish token cap only bites if dedup is ever turned on.

### After Step 5 — automatic wrap-up  (no action needed)
When the run finishes, STORM writes two housekeeping files by itself — you don't trigger them:
- **`run_config.json`** — the exact knobs this run used.
- **`llm_call_history.jsonl`** — a log of every LLM call (this is the file Step 6 reads).
- **Files:** `engine/knowledge_storm/storm_wiki/engine.py` (the `post_run` function).

### Step 6 — Step log  (for inspection)
Render a human-readable trace of every LLM call, labelled by what STORM was doing.
- **Files:** `scripts/build_steplog.py`.
- **Output:** `STEP-LOG.md`.
- **Gotcha:** the labeller is heuristic — good enough to audit the run, not exact.

### Step 7 — Render a viewable version  (the preview)
**Input:** the finished dossier (`storm_gen_article_polished.txt`) + the cited-source map (`url_to_info.json`), both under `out/<topic-slug>/`.

**Process:** `preview/view-article.py` reads both and renders one self-contained HTML. It reuses STORM's own citation mapping (`url_to_unified_index` → `[n]` → source URL) to make every citation clickable, builds a numbered References list from each source's title + URL, and adds a table-of-contents sidebar. It's a pure read-only viewer — it never touches the pipeline.

**Output:** `out/<topic-slug>/article.html` — open in VS Code (Live Preview) or any browser; self-contained and shareable.

**Gotcha:** it only re-renders what's already on disk — to change the content, regenerate the article (Steps 0–5), then re-run the viewer.

---

## Traceability (every output file → the code that produced it)

| Output file | Produced by |
|---|---|
| `conversation_log.json`, `raw_search_results.json` (full pool) | Step 2 — `engine/knowledge_storm/storm_wiki/modules/knowledge_curation.py` + `scripts/dataforseo_rm.py` + `engine/knowledge_storm/storm_wiki/modules/storm_dataclass.py` |
| `direct_gen_outline.txt`, `storm_gen_outline.txt` | Step 3 — `engine/knowledge_storm/storm_wiki/modules/outline_generation.py` |
| `storm_gen_article.txt`, `url_to_info.json` (cited-source map) | Step 4 — `engine/knowledge_storm/storm_wiki/modules/article_generation.py` (+ `engine/knowledge_storm/storm_wiki/modules/storm_dataclass.py`, `engine/knowledge_storm/encoder.py`) |
| `storm_gen_article_polished.txt` | Step 5 — `engine/knowledge_storm/storm_wiki/modules/article_polish.py` |
| `run_config.json`, `llm_call_history.jsonl` | after Step 5 — `engine/knowledge_storm/storm_wiki/engine.py` (`post_run`) |
| `STEP-LOG.md` | Step 6 — `scripts/build_steplog.py` |
| `article.html` (viewable, clickable citations) | Step 7 — `preview/view-article.py` |

## The files that participate in a run (nothing else is touched)

**In `scripts/` (ours):** `shim.py` (Claude bridge) · `dataforseo_rm.py` (search + scrape) · `run_storm.py` (control panel) · `build_steplog.py` (readable log).

**In `engine/knowledge_storm/storm_wiki/`:** `engine.py` (the conductor).

**In `engine/knowledge_storm/storm_wiki/modules/`:** `persona_generator.py` · `knowledge_curation.py` · `outline_generation.py` · `article_generation.py` · `article_polish.py` · `storm_dataclass.py` · `retriever.py` · `callback.py`.

**In `engine/knowledge_storm/`:** `lm.py` · `interface.py` · `encoder.py` · `dataclass.py` · `utils.py` · `logging_wrapper.py`.

**Unused (present but never called):** `engine/knowledge_storm/rm.py` (STORM's built-in retrievers — ours replaces them).

Our edits to any of this engine code are documented in `CHANGES.md` (the single source of truth for what we changed and why).

## The dossier — what /write receives

A single long, densely-cited research write-up (`storm_gen_article_polished.txt`): STORM's neutral outline, each
section grounded in scraped sources, ~1 citation per ~27 words. The write phase treats it as an **evidence pool**
— it reads the cited synthesis for the important claims, and can drill into `raw_search_results.json` (the full
scraped pool) — or `url_to_info.json` (just the cited sources) — for the full passages behind any source. It is
mapped onto **our** DataForSEO outline and **our** angle at write time; STORM's structure and prose are never published.

## Rules shelf (files this leans on, not restated here)
- `README.md` — how to run + the folder layout + rebuilding the venv.
- `CHANGES.md` — every modification we made to STORM and why + the proven config.
- `../10-dataforseo/research-plan.md` — the sibling research recipe; same asset anchors, same `/write` consumer.

## Gotchas (lessons from the live runs)
- **Deep RAG trades breadth for depth.** Fuller answers make personas quit sooner — the **breadth floor** (≥3 questions) is what keeps the source count up. Widen further with `--perspectives`, never `--turns` (the floor already saturates turns).
- **Only ~40% of gathered sources get cited.** The section writer keeps the top-8 per heading; the rest stay in `raw_search_results.json` (the full pool). That's a healthy funnel, not waste — it's the dossier's second (raw) layer.
- **STORM's outline is not our outline.** It's encyclopedic scaffolding for research; the article's real structure comes from the DataForSEO brief at write time. Never publish STORM's sections.
- **The shim must be running.** No shim = every LLM call fails. Check `curl -s http://127.0.0.1:8081/health`.
- **Self-contained.** venv + full source both live in this folder; if the venv breaks, `./setup.sh` rebuilds it.
- **Cost ≈ $0.10–0.20 per topic** (DataForSEO SERP only; page scraping and all LLM calls are free via the subscription).

## Completeness checklist (run this for every asset — nothing skipped, everything on disk)

Everything lands under `out/<topic-slug>/`. Tick each box; if one can't be ticked, the run isn't done.

**Before the run**
- [ ] Shim is up — `curl -s http://127.0.0.1:8081/health` returns ok.
- [ ] `storm/.env` exists with valid `DFS_LOGIN` / `DFS_PW` (auto-loaded by `run_storm.py`).
- [ ] Topic = the asset's **title + distinct angle** (from `clubbed-ideas.csv`), not a vague keyword.

**Step 2 — interviews (research)**
- [ ] `conversation_log.json` written; personas are **diverse** (not just the default "Basic fact writer").
- [ ] Each persona asked **≥3 questions** (breadth-floor nudge held — spot-check the log).
- [ ] `raw_search_results.json` written, and the pool is **healthy breadth** (dozens of sources, not a thin handful).
- [ ] Deep scrape worked — sources carry **full-article chunks**, not 1-line blurbs.

**Step 3 — outline**
- [ ] `storm_gen_outline.txt` + `direct_gen_outline.txt` written; the outline has a sensible spread of sections.

**Step 4 — sections**
- [ ] `storm_gen_article.txt` + `url_to_info.json` written.
- [ ] Sections are **densely cited** (~1 citation per 25–35 words) and carry **concrete specifics** (numbers, $, %, dates) — not padding.

**Step 5 — polish**
- [ ] `storm_gen_article_polished.txt` written — the final dossier (lead + all sections).

**After the run (auto)**
- [ ] `run_config.json` + `llm_call_history.jsonl` written.
- [ ] `STEP-LOG.md` built — `python scripts/build_steplog.py out/<topic-slug>`.

**Step 7 — preview**
- [ ] `article.html` rendered — `python preview/view-article.py out/<topic-slug>` — citations are clickable and the References resolve to real sources.

**Grounding sanity (the one rule)**
- [ ] Every claim in the dossier traces to a scraped source in `raw_search_results.json` — no uncited assertions.
