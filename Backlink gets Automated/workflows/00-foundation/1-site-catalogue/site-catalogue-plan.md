---
type: recipe (runnable process — the site-catalogue engine)
reusable: any company (the tool never knows which — everything company-specific comes from the record)
reads: projects/<COMPANY>/company.json · the live site · the Wayback CDX index · DataForSEO ranked_keywords (paid)
produces: content-database.csv · top-pages.csv · catalogue-report.md under projects/<company>/00-foundation/output/
last_updated: 2026-07-19
---

# Site catalogue — every page a company has, plus its search traffic, in one command

## What this does

Catalogues a company's whole website (every page, with its full text) and how it earns search
traffic, from nothing but the company record. One command, resumable, with hard coverage gates
that fail the run rather than ship a short catalogue.

## The one rule that governs everything

**Ask the site, never assume the site — and no silent shortfall.** Every list is derived at
runtime (content types, sitemaps, pages); every count is asserted against an authority the
source itself publishes; anything that can't be verified is REPORTED as lower-confidence, never
claimed. A failure and "no more data" never share a code path.

## Branch table (one spine, two site kinds)

| Site kind | Enters | Skips | Exits with |
|---|---|---|---|
| WordPress (`wordpress_url` in the record) | all 8 stages | — | FULL confidence (CMS count headers asserted per type) |
| Non-WordPress (`wordpress_url` empty) | stage 2 onward | stage 1 (recorded as skipped, not empty) | LOWER-CONFIDENCE stamp (sitemap-accounting + traffic cross-check only) |

## What you produce

| Stage | Named output |
|---|---|
| 1 enumerate-wp | `_work/urls-wp.json` — every URL the CMS lists, per derived type, totals asserted |
| 2 enumerate-sitemap | `_work/urls-sitemap.json` — every URL the sitemaps declare (+ blocked/not-sitemap evidence) |
| 3 enumerate-archive | `_work/urls-archive.json` — archive-remembered URLs, liveness-checked |
| 4 enumerate-crawl | `_work/urls-crawl.json` — link-crawl URLs (last resort; usually `skipped`) |
| 5 reconcile | `_work/reconciled.json` — union + provenance + canonical collapse + drop buckets |
| 6 extract | `output/content-database.csv` — the catalogue (Traffic/Intent still blank) |
| 7 traffic | `_work/traffic-raw.json` + `output/top-pages.csv` + the catalogue's Traffic/Intent filled |
| 8 gates | `output/catalogue-report.md` — gates verdict, per-type coverage, provable gaps |
| (after 8) | `_work/content-database-preview.csv` — a flattened, Excel-openable copy for eyeballing. **Never read it downstream:** flattening removes the line breaks the pipeline counts on. |

`output/` holds the three deliverables and nothing else. Every downstream engine reads
`output/content-database.csv`.

## Inputs

- `COMPANY` env var (or `--company`) → `projects/<company>/company.json` — fail-closed, no default.
- Record fields used: `company` `brand` `domain` `wordpress_url` `location` `language`.
- `DFS_LOGIN`/`DFS_PW` in the environment or the canonical repo `.env` (stage 7 only, paid).
- Engine knobs (rate, thresholds, gate bars) live in `scripts/config.py` — never in the record.

## The steps, in order

Run: `COMPANY=<slug> venv/bin/python scripts/run_catalogue.py` (add `--check` to validate the
record and paths without running; `--from <stage>` / `--redo` to resume or force).

1. **enumerate-wp** — asks `/wp-json/wp/v2/types` what content types exist (never a typed-in
   list), paginates each at `per_page=100`, asserts every type's collected count against its
   `X-WP-Total`. Output: `urls-wp.json`. *Gotcha: only `rest_post_invalid_page_number` ends a
   type; an HTML body on the JSON endpoint means BLOCKED, not empty.*
2. **enumerate-sitemap** — every `Sitemap:` line in robots.txt plus a platform probe list;
   branches on the document's root element, follows `<loc>` literally, gzip by magic number,
   depth-capped recursion with cycle detection through redirects. Output: `urls-sitemap.json`.
   *Gotcha: a DECLARED sitemap answering HTML is a loud block; a PROBE answering HTML is just an
   SPA catch-all.*
3. **enumerate-archive** — the CDX index filtered to 200+text/html, own hosts only, then every
   candidate HEAD-checked against the live site (history ≠ existence). Output: `urls-archive.json`.
4. **enumerate-crawl** — BFS from the homepage, only when the other layers are thin. Output:
   `urls-crawl.json` (usually `{"skipped": …}`).
5. **reconcile** — unions all sources keeping `source` per URL; stored URL (minimal
   normalisation) and match key (aggressive, tracking-param blocklist) kept separate; fetches
   every page once through the raw cache (frontier-resumable); collapses redirect+canonical
   chains with a hop cap (loops = UNRESOLVED); flags fan-in anomalies instead of collapsing
   them; drops soft 404s by content signature. Output: `reconciled.json`. *Gotcha: a page-level
   403 is recorded; a site-wide block stops the stage — the homepage probe decides which.*
6. **extract** — offline over the cache: CMS body → the four-extractor stack (longest wins,
   winner recorded) → JSON-LD/`<article>` → Playwright for SPA roots → `body_status=failed`,
   never silently blank. Headings kept inline as `#`/`##`/`###`. Output: the catalogue CSV.
   *Gotcha: the DOM pruner reverts itself if it removed >60% of the text.*
7. **traffic** — one bulk DataForSEO `ranked_keywords` pull (credit-guarded, cached in
   `traffic-raw.json`, short pages re-asked once), grouped per URL into raw `Traffic` and
   cleaned `Traffic_clean`; joins the CLEANED figure into the catalogue. Output: `top-pages.csv`.
   *Gotcha: the vendor's `total_count` overstates what it will serve; the tail is etv≈0.*
8. **gates** — the three run-failing gates (enumeration totals + sitemap accounting; response
   integrity; per-type extraction coverage ≥95%/≥90%) plus the ranking-pages cross-check.
   Output: `catalogue-report.md`, written even on failure. *Gotcha: a failed gate exits 1 — a
   short catalogue must never look like success.*

## Mapping table (where each step's rules come from)

| Step | Grounded in |
|---|---|
| 1-4 enumeration | `site-catalogue-BUILD.md` Stage 3 + `temp-workflow-learnings.md` (union of sources, magic numbers, literal `<loc>`, blocked ≠ empty) |
| 5 reconcile | BUILD Stage 3 (reconcile) — store vs match key, canonical-as-hint, fan-in, soft 404 |
| 6 extract | BUILD Stage 4 — the ladder, the stack, the prune guard, processes-not-threads |
| 7 traffic | BUILD Stage 5 + section 2 (column contract) — bulk pull, raw+clean, credit guard |
| 8 gates | BUILD Stage 6 — the three gates, per-type bars, the honest cross-check |
| fetch (under all) | BUILD Stage 2 — token bucket, honest UA, raw cache, conditional GET, frontier |

## Rules shelf

- `workflows/company-record.md` — the record schema this engine reads (extend it there FIRST).
- `site-catalogue-BUILD.md` (repo root) — the approved build spec this engine implements.
- `~/.claude/conventions/building-workflows.md` + `project-structure-conventions.md` — the
  recipe/code standards (C1 config hub, C5 atomic saves, C6 paid-API chokepoint).

## Gotchas (the ones that cost a day each)

- The site's firewall (MalCare/Cloudflare) blocks bursts and the block ESCALATES; the engine
  cools down and slows permanently on any 403 — do not "help" by raising the rate.
- June's safe request rate is not July's: react to live signals, never to history.
- The raw cache means extractor changes NEVER need refetching — re-run stage 6 alone (`--from extract --redo`).
- Deleting `_work/traffic-raw.json` re-SPENDS the DataForSEO pull. Don't, unless you mean to.

## Run checklist

- [ ] `company.json` exists and `--check` prints the right domain/market/paths
- [ ] `DFS_LOGIN`/`DFS_PW` present (canonical `.env`)
- [ ] `COMPANY=<slug> venv/bin/python scripts/run_catalogue.py` (caffeinate it — hours on a 10k-page site)
- [ ] every stage printed `== Stage N ==` and its output file exists
- [ ] `catalogue-report.md` says all gates PASS (or fix and `--from` the failed stage)
- [ ] downstream smoke: reuse-check/features/style-guide can read the CSV; harvest finds markers
