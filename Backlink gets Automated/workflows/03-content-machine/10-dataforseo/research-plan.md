---
type: plan (validated on 2 live topics; ready to promote to 03-content-machine/research.workflow.md)
stage: content-machine — research (produces the brief that /write consumes)
reads: seo-aeo-geo-checklist.md (the build-spec source); DataForSEO creds (from scripts/.env — DFS_LOGIN / DFS_PW; master copy in ~/.testlify-access.md)
produces: two files per run — research-doc-[asset-slug].md (reader-ready brief) + research-notes.md (agent commentary). Each step writes a section file to <run_dir>/proof/; Step 7 assembles them (nothing is appended live).
last_updated: 2026-07-15
---

# Research plan — asset topic → proof-backed brief

## What this does

Turn one asset topic into a single research brief that `/write` can build a full article from. Every number
comes from a live DataForSEO call (saved as proof), and every *choice* (which keywords, which questions, which
H2s) is made by an LLM sub-agent that scores the candidates, so nothing is hand-picked on vibes.

## The one rule

**No pick without a score, no number without a proof.** DataForSEO returns raw candidates. An LLM sub-agent
scores them against the topic and the Testlify angle. We keep the top N by score, and the scored list is saved
as the proof. If a line in the final brief can't point to a saved proof file, it doesn't belong.

---

## Mandatory webpage-build gate

Apply this gate before creating or changing any workflow, architecture, process or explanatory webpage. It
stays active until the website work is complete. The gate applies to HTML pages and their companion workflow
files. It does not replace the topic-research steps below.

### 1. Read the real source of truth

Before editing, read the page's existing HTML, its workflow or specification file, the upstream workflow that
creates its inputs, the downstream workflow that consumes its outputs, and any relevant `AGENTS.md` or
`SKILL.md` instructions. Identify the page's actual job before writing.

### 2. Write a build brief before implementation

Create a short build brief before changing the page. It must state:

- what the page explains and who uses it;
- inputs, outputs, scripts, files, rules and quality checks;
- upstream and downstream handoffs;
- required details that must appear;
- existing content that is correct and must remain; and
- anything that is uncertain or needs a source check.

Do not implement until this brief is complete.

### 3. Trace claims to real evidence

Every material webpage statement must be supported by a real workflow instruction, source file or verified
script behaviour. Record the supporting file and heading in the build brief. Label a proposal or inference as
such. Do not present it as an established process.

### 4. Keep the mechanisms that matter

Do not replace specific mechanisms with vague summaries. Preserve relevant analyzer outputs, scripts, file
roles, quality gates, manual checks, exceptions and handoffs. If a workflow names six outputs, the page must
explain all six when they are relevant to the page's purpose.

### 5. Preserve correct existing material

Separate what is wrong, what is unclear and what is already correct. Change only the first two. Do not replace
a clear opening, useful structure or detailed explanation merely because another section needs correction.

### 6. Do not create duplicate processes

Before adding a file, step, tracker, handoff or process, check whether an existing workflow already does the
same job. Use the existing mechanism when it exists. Do not create a second source of truth or duplicate work.

### 7. Show where the full source set goes

When a workflow handles many pages, chunks or records, explain the complete route into the next stage. Do not
make it appear that only a few examples survive if a downstream workflow processes the full set. Name the real
handoff and the file it creates for the final writer.

### 8. Build from the verified brief

Only build after the source check and brief are complete. The page must start with a plain explanation of its
purpose, follow the real process order, name files and scripts accurately, retain necessary detail, and avoid
generic process language.

### 9. Run a completeness check before delivery

Compare the finished page against the build brief. Confirm that every required component appears, no required
detail was dropped, no unsupported mechanism was added, upstream and downstream handoffs are correct, and
correct existing content was preserved. Validate the HTML and inspect the rendered page.

### 10. Correct narrowly

When a flaw is reported, identify the exact incorrect statement, re-read the relevant source files, and change
only what the evidence requires. Run the completeness check again. Do not replace the entire mechanism with a
new unverified one.

### 11. Repeat this gate for every webpage

For each future webpage task: read this section, create the build brief, verify the sources and handoffs, build
from the brief, then run the completeness check. A page is not complete until every item above passes.

## Inputs

| Input | What | Default |
|---|---|---|
| Asset (title + distinct angle) | one row from `clubbed-ideas.csv` — BOTH the "Asset" title and the "Distinct angle" column | — |
| Context file | `seo-aeo-geo-checklist.md` (build spec) | — |
| Market | location + language | United States / en |
| Volume floor | drop keywords below this monthly volume | 100 |
| KD ceiling | drop keywords above this difficulty | 40 |
| # secondaries | how many secondary keywords to keep | no fixed cap — follows article type (pillar 8–15, narrow 3–5) |

*(The FAQ count is a **write-phase** parameter, not a research input — the FAQ is scored when the article is written.)*

## What you produce (named output of every step)

**How files flow.** Every step writes to `<run_dir>/proof/` — raw data (JSON/HTML) **and**, for the judgment steps,
a small **section file** (`.md`). **Nothing is appended to a running doc as we go.** Step 7 assembles the section
files into the final brief. This table is the **authoritative file map** (the Traceability table and Completeness
checklist further down are just other views of it):

| Step | Files it writes (under `<run_dir>/proof/`) |
|---|---|
| 0 Anchors + seeds | `00-seeds.md` (anchors + seeds + why), `00-competitor-urls.txt` |
| 1 Expand (tight + ranked nets) | `01-pool.json` (merged), `01a-tight.json`, `01b-ranked.json` |
| 2 Filter (volume + KD) | `02-shortlist.json` (no API) |
| 3 Score → keywords | `03-metrics.json`, `03-verdict-1..N.json` (every scorer verdict), **`03-keywords.md`** (section), `spoke-candidates.md` |
| 4 Live SERP | `04-serp.json`, `04-serp-extract.json`, **`04-serp-snapshot.md`** (section), `04-pages-to-read.txt` (read-list) |
| 5 Read top pages (free) | `05-pages.json`, **`05-winners.md`** (section) |
| 6 AEO (gated) | `06a-query.json` (attempt log), `06-aeo.json`, `06-aeo-extract.json`, **`06-aeo.md`** (section) |
| 7 Assemble | `research-doc-[asset-slug].md` (brief) + `research-notes.md` (commentary) |

---

## How it runs (in `scripts/`)

The whole engine runs as **one command** — `python3 run_dataforseo.py --slug <slug> --asset "<title>"` — which
sequences steps 0-7, resumable (see `README.md`). Every step is scripted: the API/fetch steps are deterministic
code (creds in `scripts/.env`, defaults in `config.py`, low-level caller `dfs.py`), and the **judgment** steps run
through headless Claude (`llm.py`) with their prompts single-sourced in `prompts/*.md` (not inline). The
per-step commands below are the underlying pieces `run_dataforseo.py` calls — useful for debugging one step, not
the normal way to run.

**Credentials.** The only credentials these scripts need are the **DataForSEO** login + API password, kept in
**`scripts/.env`** as `DFS_LOGIN` / `DFS_PW` (chmod 600; master copy in `~/.testlify-access.md`; account
`akash@testlify.com` — use the API password from app.dataforseo.com/api-access, not the dashboard password).

- **Where they're loaded:** `scripts/dfs.py` (`_load_env`) reads `scripts/.env` itself — no export needed. A real
  env var already set in the shell wins over the file (handy for a one-off override); if neither is set, `dfs.py`
  exits loudly with `no DFS_LOGIN / DFS_PW`.
- **Where they're used:** `dfs.py` base64-encodes them into the Basic-auth header on every DataForSEO call. Every
  step script (`s1_expand.py` … `s6_aeo.py`) routes through `dfs.call()`, so `dfs.py` is the single cred chokepoint —
  nothing else reads them.
- `scripts/.env` holds a live secret — keep it in this folder, chmod 600, never commit or share it.


```
RUN=projects/testlify/03-content-machine/dataforseo/out/<slug>
python3 s1_expand.py   $RUN "<seed1>" "<seed2>" ...     # Step 1a tight net   -> proof/01-pool.json
python3 s1b_ranked.py  $RUN "<head seed>"               # Step 1b ranked net  -> merges into 01-pool.json
python3 s2_filter.py   $RUN                             # Step 2              -> proof/02-shortlist.json
python3 s3_metrics.py  $RUN                             # Step 3 (metrics)    -> proof/03-metrics.json  (defaults to shortlist)
python3 s4_serp.py     $RUN "<primary keyword>"         # Step 4              -> proof/04-serp-extract.json
python3 s5_pages.py    $RUN                             # Step 5              -> proof/05-pages.json
python3 s6_aeo.py      $RUN "<query>" "<match_type>"    # Step 6 (6a picks query+match_type; 6a→6b→6c loop)  -> proof/06-aeo-extract.json
```
The judgment steps are also scripted: Step 0 → `s0_seeds.py`, Step 3 scorer/judge → `s3_score.py`, the SERP
snapshot / winners / AEO write-ups → `s4b_snapshot.py` / `s5b_winners.py` / `s6_flow.py`, Step 7 assembly →
`s7_assemble.py` (prompts in `prompts/`).

---

## The steps, in order

### Step 0 — Anchor + seeds + competitor URLs  (from the clubbed-ideas file, no free brainstorm)
**First, capture the two anchors verbatim** from the asset's row in `clubbed-ideas.csv`. These are the north star
of the whole doc and are read by every judgment step downstream (the Step 3 scorer, the Step 4 SERP gate, the
Step 6 query/relevance gates all take them as `{asset_topic}` and `{distinct_angle}`):
- **Asset title** — the **Asset** column, verbatim → becomes `{asset_topic}`.
- **Distinct angle** — the **Distinct angle** column, verbatim → becomes `{distinct_angle}`.

**Then derive** (from those anchors, not free brainstorm):
- **Head seeds** — from the Asset title (the pillar phrase + 1–2 close variants).
- **Sibling seeds** — from the Distinct angle (the specific sub-topics the asset covers; e.g. for a
  recruiting-metrics benchmark: time to hire, cost per hire, quality of hire, offer acceptance rate).
- **Competitor URLs** — from the **Proof URLs** column (semicolon-separated). These feed the ranked-net (Step 1b).

No limit on the seed count.
**Seed hygiene (important):** qualify any *ambiguous* seed. "time to fill" / "time to hire" pull plumbing /
car-rental / timecard junk into the tight net — seed them as "time to fill recruiting" / "time to hire recruiting"
(or drop them, since the ranked-net covers those metrics cleanly).
*Output:*
- `<run_dir>/proof/00-seeds.md` — **opens with the Asset title + Distinct angle (verbatim) as the doc anchor**,
  then the seeds + one-line why. (`<run_dir>` = `runs/<asset-slug>/`.)
- `<run_dir>/proof/00-competitor-urls.txt` — one proof URL per line.

### Step 1 — Expand: tight net + ranked net  (API)
Two sources. **The old wide net (`keyword_ideas`) is dropped** — proven twice to return only off-topic noise
(0 usable of 652). Relevant breadth now comes from the ranked-net.

**Step 1a — tight net.** `s1_expand.py <run_dir> "<seed1>" "<seed2>" ...` — `keyword_suggestions`, run **once per
seed** (the endpoint allows one seed per call, so it loops). Returns phrases that *contain* each seed → on-topic
long-tail for the pillar and each sibling metric. → `proof/01-pool.json`.

**Step 1b — ranked net (the relevance + enrichment workhorse).** `s1b_ranked.py <run_dir> "<head seed>"` — pulls
the keywords that **winning pages already rank for** (`ranked_keywords`), from two URL sources:
1. the **competitor proof-URLs** (`00-competitor-urls.txt`),
2. **SERP-derived links** — SERPs the head seed, takes the top `config.RANKED_SERP_LINKS` organic pages.

For each page it pulls **every keyword that page ranks for** (any position, capped at `config.RANKED_PER_URL`,
ordered by volume). These are proven, on-topic keywords the seed-nets structurally can't reach — adjacent
concepts like "hr metrics", "data-driven recruiting", "hr scorecard", "selection ratio formula". It merges the
ranked-net into `proof/01-pool.json`.

*(This SERP-of-seed is separate from Step 4's SERP-on-primary — two SERPs, on purpose.)*
*Output:* `proof/01-pool.json` (tight + ranked, merged) + `01a-tight.json`, `01b-ranked.json`.
*Gotcha:* the tight net is only as good as the seeds (qualify ambiguous ones — Step 0). The ranked-net is usually
the cleaner, richer source; all this run's junk came from the tight net's ambiguous seeds, none from the ranked-net.

### Step 2 — Filter on volume + KD  (no API)
**Run:** `s2_filter.py <run_dir>` — keeps keywords with volume ≥ floor and KD ≤ ceiling (thresholds in
`config.py`: `VOL_FLOOR`, `KD_CEIL`), using the metrics already attached from Step 1.
*Output:* `proof/02-shortlist.json`.

### Step 3 — Intent, then score, then pick primary + secondaries  (API on shortlist + LLM)
1. **Metrics + intent (API):** `s3_metrics.py <run_dir> "<kw1>" "<kw2>" ...` — runs `keyword_overview`
   (≤700/call) on the **Step-2 shortlist survivors** (the candidates come from the tight + ranked nets, not from
   brainstorm) → volume + KD + **intent** per keyword → `proof/03-metrics.json`. Keep intent ∈
   {informational, commercial}.
2. **Score — batched sub-agents.** Split the shortlist into batches (~60 keywords each) and run the scorer
   prompt over them across sub-agents. **Club every scored row back into one master list** — however many
   batches or passes it took (3, 6, whatever). For a second opinion, run the scorer more than once and keep all
   passes; the judge reconciles whatever comes back, so don't force a fixed count. Fill the placeholders from
   Steps 0–3:

The scorer prompt is single-sourced in **`prompts/score-keywords.md`** (loaded by `s3_score.py`). In brief: it
scores each candidate 0–10 on **relevance · distinctness · brand-fit** (ignoring volume), shortlists on quality
(drop relevance ≤2), then assigns a **role** using volume + KD — `primary` (one) · `variation` (reword, in-body,
no section) · `secondary` (every distinct section-worthy sub-topic) · `spoke` (own future article) · `drop`. It
returns a JSON array `{keyword, relevance, distinctness, brand-fit, reason, role}`.

   Example row:
   `{ "keyword":"skills based hiring vs traditional hiring", "relevance":9, "distinctness":8, "testlify_fit":7, "reason":"real comparison angle; contrasts assessment-based vs resume-based", "role":"secondary" }`

   Each sub-agent's array is a verdict. **Save EVERY verdict to disk before judging** —
   `<run_dir>/proof/03-verdict-1.json`, `-2.json`, … (one file per scorer/batch). This is mandatory: the judge's
   picks must be auditable back to the raw scores. A run where the verdict files are missing is incomplete.

3. **Judge — main agent.** Feed the verdicts + the numbers into this prompt. It reconciles the panel and makes
   the final call, breaking ties by volume:

The judge (editor) prompt is single-sourced in **`prompts/judge-keywords.md`** (loaded by `s3_score.py`). It
reconciles all scorer passes into the final set: **PRIMARY** (one — the highest-*volume* intent-match that clears
KD, NOT necessarily the title phrase) · **VARIATIONS** (rewords, in-body, tracked as a distinct list) ·
**SECONDARY** (every distinct section-worthy sub-topic; prefer ones ≥2 verdicts kept) · **SPOKE CANDIDATES**
(distinct heads for their own future article, saved separately — each also scored on **`relevance` 0–10** = how well
it fits THIS asset's cluster, so a big-but-generic head can't win on volume). Returns JSON `{primary, variations,
secondary, spoke_candidates, notes}`.

*Output:* `03-keywords.md` — scorer verdicts + judged primary + **variations** + secondaries (the proof). **`spoke-candidates.md`**
— the spoke candidates as a table, **ranked best-first** by a composite score `0.5·relevance + 0.25·volume(log) +
0.25·ease(100−KD)` (computed in `s3_score.py`; weights in `config.py`). A **hard relevance floor** first drops any
spoke scoring `< config.SPOKE_MIN_RELEVANCE` (=3, i.e. relevance 0–2) whatever its volume, so an off-cluster giant
can't rank on volume alone. The research conductor then enqueues only the **top `MAX_SPOKES` (=3)**; the rest stay in
the file for the record.
*→ Keywords section (`03-keywords.md`):* the **primary keyword** + the **variations** (rewords of the primary, woven
in-body — a `keyword · vol · KD` table) + the **secondary keywords** (no fixed cap), each with its one-line *why*, an
in-body-only note, and a pointer to `spoke-candidates.md`. Step 7 lifts this into the brief (see the SAMPLE's Keywords section).
*Gotcha:* good secondaries look like siblings ("iced coffee, coffee milkshake"), not "cold coffee recipe easy,
cold coffee recipe simple." If your secondaries are all the primary + a word, the ranked-net or the scorer failed.

### Step 4 — Read the live SERP  (API, primary keyword)
**Run:** `s4_serp.py <run_dir> "<primary keyword>"` — reads the live Google SERP for the primary (with
`load_async_ai_overview=true` + `people_also_ask_click_depth` from `config.py`), then saves the raw SERP **and**
a structured extract. (Run it again for a secondary only if its intent/format clearly differs.)

The extract (`proof/04-serp-extract.json`) pulls all of this from the SERP JSON — **no page visits here:**
- **top organic URLs** — the competitor set. Step 4 vets the best 3 readable ones into the read-list
  (`04-pages-to-read.txt`), and **that read-list is what Step 5 reads** (not raw rank 1–6).
- **featured snippet** — who holds it + its shape (paragraph / list / table).
- **PAA list** — the People-Also-Ask questions.
- **AI Overview** — present or not, plus its cited URLs if present.
- **related searches.**
- **dominant format** — only a *quick provisional* read from the TITLES + snippet shape here ("How to…" =
  how-to; "Top N…" = listicle; "X vs Y" = comparison; "What is…" = definitional). The **confirmed** format comes
  from Step 5's free page read, not from this step.

*Output → `proof/04-serp.json` (raw) + `proof/04-serp-extract.json` (structured: top URLs · snippet · PAA · AI Overview · related).*
**Handoff to Step 5:** the **read-list** — save the 3 vetted URLs to `proof/04-pages-to-read.txt` (one per line);
Step 5's script reads that file (falling back to the raw top-N only if it's absent).
*→ SERP snapshot section (`04-serp-snapshot.md`) via an LLM structuring pass.* Feed the extracted SERP fields to
this prompt. **The PAA + related searches get a relevance pass here** — tagged on-angle (FAQ/H2 candidates) vs
off-angle (kept but flagged, never silently dropped) against the distinct angle. (Top organic is NOT filtered — it
is the literal competitor set. The final FAQ is still scored in the write phase; this pass only separates signal
from trivia.)
The SERP-snapshot prompt is single-sourced in **`prompts/serp-snapshot.md`** (loaded by `s4b_snapshot.py`): it
lists the full competitor set + picks the top-3 read-list, captures the featured snippet and the AI Overview
(what it covers + whether Testlify is cited — the GEO gap), and tags PAA + related searches on- vs off-angle
against the asset's distinct angle. It returns this shape:
```
### SERP snapshot — {primary_keyword}
- Who ranks: one line naming the competitor set + what kind of sites they are.
- Pages to read next (Step 5 read-list — top 3 relevant, readable): url1, url2, url3 — one line why each (and one line on any high-rank page skipped, e.g. "#1 skipped: PDF").
- Featured snippet: <holder> holds it (format: paragraph/list/table), or "none — open to win with a matching-format answer".
- AI Overview: **present-to-a-clean-US-crawler / absent** (say it this way — never "present" flat). AI Overviews
  are personalized + volatile (vary by location, login, device, live experiments), so what we capture may NOT be
  what any given user sees. Treat it as a snapshot, not a guarantee. If present:
  - What it covers: 1-line definition it gives + the metrics/sub-topics it names, in its order (our answer skeleton).
  - Who it cites: domains; **Testlify cited by this AI Overview?** yes/no (GEO gap if no). (This is the *Google AI
    Overview* surface; Step 6 separately reports the *AI-assistant* surface — different places, both worth knowing.)
- PAA — on-angle (FAQ/H2 candidates): one per line, verbatim.
- PAA — off-angle (excluded, noted): one per line, verbatim.
- Related searches — on-angle: one per line.
- Related searches — off-angle: one per line.
- Raw: `<run_dir>/proof/04-serp.json`
```
(Dominant format is added by Step 5, not here.)
*Gotcha:* one Google page = exactly one featured snippet; "multiple snippets" only appears across multiple keyword SERPs.

### Step 5 — Read the top pages  (free fetch; DataForSEO only as a fallback)
**Run:** `s5_pages.py <run_dir>` — reads the **relevance-vetted read-list** (`proof/04-pages-to-read.txt`, the
top-3 chosen in Step 4; falls back to the raw top-N from the extract if that file is absent) and fetches them
with a plain HTTP request, parsing H1–H3 + word count. **No paid call — page reading is
free.** **If a page fails, retry it at least twice** (the script retries with a browser-like User-Agent and a
short backoff before giving up) — many blocks are transient. Only after ≥2 failed tries: fall back to DataForSEO
`content_parsing` for that page, or (if still nothing) swap in the next relevant page from the read-list and
**note the swap + why** in `05-winners.md`.

**What this step produces (per URL):**
- the **H1–H6 heading tree** — the page's real section structure,
- a rough **word count** — how thin or deep the page is,
- and, rolled up across the 2–3 pages: the **subtopics most competitors cover** (a descriptive "common H2s"
  list — what the field tends to include, NOT a prescriptive "must-have"), the **gaps** the winners treat
  thinly, and the **confirmed dominant format** (Step 4's provisional guess checked against the actual structure).

*Output:* `proof/05-pages.json` — parsed headings + word count per URL.

**Refine for the doc (LLM).** The write-up prompt is single-sourced in **`prompts/winners.md`** (loaded by
`s5b_winners.py`): fed the parsed headings, it returns the "What the winners cover" section — confirmed format,
depth, common H2s (descriptive, deduped), where winners drift, and **gaps we can own**.

*→ What the winners cover section (`05-winners.md`).* **Example:**
```
### What the winners cover — skills based hiring
- Confirmed format: definitional guide.
- Depth: #1 (SHRM) ~600 words (thin); deeper winners ~1,500.
- Common H2s (most competitors have):
  - what it is
  - why it's rising
  - how it works
  - vs traditional hiring
  - common mistakes
- Where the winners drift: some pivot into general recruiting advice.
- Gaps we can own:
  - none show HOW to run it with real assessments (the Testlify angle)
- Raw: <run_dir>/proof/05-pages.json
```

### Step 6 — AEO: what AI answers + who it cites  (LLM gate → API → LLM gate)
`llm_mentions` takes only a keyword + match_type — it doesn't understand our asset, so an ambiguous word
(`recruiting` = HR vs college sports) sorted by volume returns the biggest meaning, not ours. We fix that with a
gate on **both sides** of the call: an LLM picks a disambiguated query going in, and an LLM filters homonym drift
coming out. (Same discipline as Steps 3–5.)

**6a — Pre-flight query gate (LLM, before the call).** Pick a query that can't pull a homonym. (Why: llm_mentions
matches a keyword and sorts by volume, so an ambiguous word — "recruiting" = HR vs college sports — returns the
word's biggest meaning, not ours.)
The 6a query-gate prompt is single-sourced in **`prompts/aeo-query.md`** (loaded by `s6_flow.py`): given the
primary keyword + the correct meaning + attempts-so-far, it either returns a disambiguated `{query, match_type}`
or `{stop: true}` after ~3 off-topic tries.
*Loop:* 6a → 6b → 6c. If 6c reports the pull off-topic, re-run 6a with the attempt appended to `{attempts_so_far}`
— bounded to ~3–4 tries, after which 6a returns `stop` and Step 6 yields **no signal** (it does not borrow from
other steps; the AI Overview already lives in the Step 4 SERP snapshot).
*Output:* `proof/06a-query.json` — the chosen query + match_type + the full attempt log (feeds 6b, and is the audit trail).

**6b — Run:** `s6_aeo.py <run_dir> "<query>" "<match_type>"` — queries `llm_mentions` with the 6a query/match_type
→ `proof/06-aeo.json` (raw) + `proof/06-aeo-extract.json` (structured).

**What this step produces:**
- the real **AI questions** for the topic (+ `ai_search_volume` each),
- the **cited source domains** (who AI quotes) and whether **the brand (`config.BRAND`) is among them** (a GEO gap if not),
- `fan_out_queries` — the sub-questions AI split the topic into (candidate H2/FAQ items).

*Output:* `proof/06-aeo.json` (raw) + `proof/06-aeo-extract.json` (structured).

**6c — Post-run relevance gate + structuring (LLM, after the call).** Judge the results against the topic on
their own merit — Step 6 stands alone; it never borrows from other steps. If the pull is off-topic, it reports
**no usable signal** (the AI Overview already lives in the Step 4 SERP snapshot):
The 6c write-up prompt is single-sourced in **`prompts/aeo-writeup.md`** (loaded by `s6_flow.py`): it judges the
`llm_mentions` results against the topic, reporting **no usable signal** if off-topic, else keeping the on-topic
questions as FAQ candidates + the cited domains (and whether Testlify is among them). It returns this shape:
```
### AI answer landscape — {primary_keyword}
- Status: usable / no usable signal (llm_mentions returned off-topic results for this keyword)
- If usable:
  - Testlify cited by AI assistants? yes/no (GEO gap if no) — this is the AI-assistant surface (distinct from Step 4's Google AI Overview)
  - Who AI cites: one domain per line
  - FAQ candidates (on-topic questions, verbatim): one per line
- Raw: 06-aeo.json
```

*→ AI answer landscape section (`06-aeo.md`).* **Templates —**

*Usable pull:*
```
### AI answer landscape — skills based hiring
- Status: usable
- Testlify cited by AI assistants? No — GEO gap, open to own.
- Who AI cites:
  - Coursera
  - Reddit
  - Business Insider
- FAQ candidates:
  - how does skill-based hiring work?
  - is skill-based hiring on the rise?
  - skills vs degrees?
- Raw: <run_dir>/proof/06-aeo.json
```
*No usable signal (off-topic pull):*
```
### AI answer landscape — recruiting metrics
- Status: no usable signal — llm_mentions returned off-topic results for every query tried. This method added nothing for this topic.
- Raw: <run_dir>/proof/06-aeo.json (see 06a-query.json for the attempt log)
```
*Gotcha:* the questions are **candidates only** — the final FAQ is picked (scored) in the write phase, not here.

### Step 7 — Finalize the doc  (no new research)
By now Steps 3–6 have each written their section file (`03-keywords.md`, `04-serp-snapshot.md`, `05-winners.md`,
`06-aeo.md`). Assemble them into the brief: confirm every section is present (a section may legitimately be a
**null result** — e.g. Step 6 "no usable signal"; keep it as-is, never backfill or borrow to fill it), then add the
**build spec** from `seo-aeo-geo-checklist.md` — the word band for the confirmed
content type, the featured-snippet target (format from the SERP snapshot), the external primary sources to cite
({{PRIMARY_SOURCES}}), and the close rule (forward next step + one CTA, not a recap). No new research here.

**Final polish pass (LLM) — do this last, on the WHOLE doc.** The sections were appended step by step, so read
the whole thing top to bottom and turn it into one clean, reader-ready brief:
- fix grammar and tighten wording,
- make the heading levels consistent and order the sections logically,
- remove duplication across sections,
- add a one-line **verdict/summary at the very top** (traffic vs authority · beatable? · the angle).
The output is a single reader-first document (written for the WRITER, not by pipeline-step order; no "[Step N]"
labels). **Follow `research-doc-SAMPLE.md` exactly** for structure and formatting (skeleton in "The deliverable"
below), one item per line, and end with the **completeness checklist** (below) filled in.
*Output (two files):*
- `research-doc-[asset-slug].md` — the reader-ready brief (matches `research-doc-SAMPLE.md`).
- `research-notes.md` — a SEPARATE agent-commentary file: what actually happened this run, judgment calls made,
  anything weak/missing/uncertain, and follow-ups. This keeps opinions/caveats OUT of the clean brief but on record.
*Note:* the final **FAQ, H2 outline, and Testlify angle** are built in the **write phase** from the candidates
this doc already carries — PAA + fan-out for the FAQ; the common H2s + fan-out + secondaries for the outline; the
"gaps we can own" for the angle. They are not decided here.

---

## The deliverable — research doc (what `/write` receives)

A single **reader-first** brief, structured for the writer — **not** by pipeline-step order, and **no "[Step N]"
labels.** Full worked example to copy exactly: **`research-doc-SAMPLE.md`**. Skeleton (top → bottom):

1. **Title + anchor** — `# Research doc — [asset]`, then a blockquote with the **asset title + distinct angle (verbatim)**.
2. **Verdict** — 3 lines: the *play* (traffic vs authority) · *beatable?* (say head vs long-tail separately — be honest) · the *opening*.
3. **Keywords** — primary (1) as a line (kw · vol · KD · intent · why); **secondaries as a table** (kw · vol · KD · section it anchors); an "in-body only (no volume)" note; a spokes pointer.
4. **SERP snapshot** — who ranks · featured snippet · **AI Overview** (say "present to a clean US crawler" + the volatility caveat) · related (on/off-angle).
5. **What the winners cover** — confirmed format · depth · common H2s · gaps we can own.
6. **AI answer landscape** — `usable` / `no usable signal`.
7. **Build spec** — word band · structure rules · snippet target · primary sources · close.
8. **Proof map** — a footer table (each section → its proof file), kept at the very bottom, out of the reader's way.

Plus a separate `research-notes.md` (agent commentary — see Step 7). Formatting rules: proper headers, bullet
lists, small tables; never a run-on block. Lead every section with its single most useful line.

## Traceability (every doc section → its source)

| Doc section | From |
|---|---|
| Keywords (+ spoke candidates) | Step 3 (`03-keywords.md`, `spoke-candidates.md`) |
| SERP snapshot | Step 4 (`04-serp-snapshot.md` ← `04-serp.json`) |
| What the winners cover | Step 5 (`05-winners.md` ← `05-pages.json`, read-list `04-pages-to-read.txt`) |
| AI answer landscape | Step 6 (`06-aeo.md` ← `06-aeo.json`, query log `06a-query.json`) |
| Build spec | `seo-aeo-geo-checklist.md` |

## Completeness checklist (run this before handing off — nothing skipped, everything on disk)

**Step 0 — anchors & seeds**
- [ ] `00-seeds.md` opens with the **asset title + distinct angle (verbatim)**.
- [ ] Head seeds (from title) + sibling seeds (from distinct angle) present; ambiguous seeds qualified.
- [ ] `00-competitor-urls.txt` written (relevant proof-URLs only).

**Step 1–2 — pool & shortlist**
- [ ] `01-pool.json` = tight net + ranked net merged (both ran; ranked-net URL count logged).
- [ ] `02-shortlist.json` after vol/KD filter; pool→shortlist counts recorded.

**Step 3 — keywords**
- [ ] `03-metrics.json` (volume + KD + intent on the shortlist).
- [ ] **Every scorer verdict saved** → `03-verdict-1.json …` (MANDATORY — judge must be auditable).
- [ ] `03-keywords.md`: exactly **1 primary = highest-volume intent-match** (NOT defaulted to the title phrase); secondaries as a table; in-body-only note; judge notes.
- [ ] `spoke-candidates.md` with full metrics.

**Step 4 — SERP**
- [ ] `04-serp.json` + `04-serp-extract.json`.
- [ ] `04-serp-snapshot.md`: who-ranks · snippet · AI Overview (**"present to a clean US crawler" + volatility caveat**) · PAA on/off-angle · related on/off-angle.
- [ ] `04-pages-to-read.txt` = top-3 **relevant, readable** pages (PDFs/forums/homepages skipped; skips noted).

**Step 5 — winners**
- [ ] `05-pages.json`: each read-list URL fetched (**≥2 retries before any swap**; swaps + reasons noted).
- [ ] `05-winners.md`: confirmed format · depth · common H2s · gaps we can own.

**Step 6 — AEO**
- [ ] `06a-query.json` = attempt log (queries tried + drift), ending `stop` or a usable query.
- [ ] `06-aeo.md`: `usable` / `no usable signal` — standalone, **no borrowing from other steps**.

**Step 7 — assembly**
- [ ] `research-doc-[slug].md` matches `research-doc-SAMPLE.md` (reader-first, no step labels, proper headers/tables, verdict on top, proof-map footer).
- [ ] `research-notes.md` written (judgment calls · weak/missing/uncertain · follow-ups).
- [ ] Every section's number traces to a saved proof file (proof-map footer complete).

## Rules shelf (files this leans on, not restated here)
- `seo-aeo-geo-checklist.md` — word bands, snippet rules, primary-source list, close rule.
- `research-doc-SAMPLE.md` — the gold-standard output shape every research doc must match.

## Gotchas (lessons from the live runs)
- **Tight net + ranked net.** Tight net alone gives suffix-only secondaries; the ranked-net (keywords the
  winning pages rank for) adds the distinct, relevant breadth. The old wide net (`keyword_ideas`) is dropped — pure noise.
- **Seeds come from BOTH anchors.** Head seeds from the Asset title, sibling seeds from the Distinct angle — a
  metric named in the title (e.g. Time-to-Hire) must be seeded or it never enters the pool.
- **Ambiguous seeds poison the tight net** ("time to hire" → car-hire junk). Qualify them in Step 0, or let the
  Step 3 scorer drop the stragglers on the relevance axis.
- **Read-list sanity check (Step 4→5).** Don't read the top-N by rank blindly — a #1 PDF or a Reddit thread wastes
  a slot. Step 4 vets the top-3 *relevant, readable* pages into `04-pages-to-read.txt`; Step 5 reads those.
- **llm_mentions homonym-drifts (Step 6).** An ambiguous keyword returns its biggest meaning ("recruiting" →
  college sports, "recruitment" → sororities). The 6a input gate disambiguates the query; the 6c output gate drops
  drift. It may legitimately produce **no usable signal** — record that honestly, never fabricate or borrow from
  another step.
- **SERP flags matter.** Without `load_async_ai_overview` the AI Overview block goes missing.
- **Read pages free.** Fetch the top pages ourselves; DataForSEO `content_parsing` is only a fallback.
- **Cost ≈ $0.50–1 per topic** (Steps 1, 3, 4, 6 are the paid calls; Step 5 page reads are free; Step 6 retries
  add a little). Cheap enough to run per asset.
- **"Cited by AI?" appears on TWO surfaces, on purpose** — the SERP snapshot reports **Google's AI Overview**
  citations (Step 4); the AI answer landscape reports **AI-assistant** citations (Step 6, llm_mentions). Different
  surfaces, not a duplication — label each so the reader isn't confused.
