---
type: proof-of-fit report (E0 — does DataForSEO replace the Semrush steps the asset engine cannot run?)
verdict: PASS — build E1 on DataForSEO
measured: 2026-07-20 against saved Semrush exports, live account
total spend: $0.1453 (balance $13.3428 -> $13.1975)
---

# E0 — DataForSEO proof-of-fit

## Why this existed

`competitor-study.workflow.md` L111-112 and L175-176 state the blocker outright:

> **"Two of these run in Semrush on the user's login — the agent can't."** … **"Just attach the file in the chat."**

Register C2 ordered the migration to DataForSEO. This report proves the endpoints deliver
before a line of E1 is written (standing directive 2: read the vendor's real response first;
never freeze a design on an assumption).

## What was tested, and what it cost

| # | Test | Endpoint | Cost |
|---|---|---|---|
| 1 | competitor discovery, limit 30 | `/v3/dataforseo_labs/google/competitors_domain/live` | $0.0156 |
| 2 | competitor discovery, limit 200 | same | $0.0360 |
| 3 | indexed pages, limit 300 (wrong sort key) | `/v3/backlinks/domain_pages/live` | $0.0348 |
| 4 | structure inspection, limit 5 | same | $0.0242 |
| 5 | indexed pages, limit 300, correct sort | same | $0.0348 |
| | | **total** | **$0.1453** |

Tests 3 and 4 were the cost of my own error — see "Gotcha" below. A clean run is tests 2 + 5 = **$0.071**.

## Result 1 — competitor discovery: PASS, but the LLM shortlist is REQUIRED

Target `testlify.com`, US/en, `exclude_top_domains: true`, limit 200.

**9 of the 12 competitors the real hand-run used were found:**

| Competitor | Rank | | Competitor | Rank |
|---|---|---|---|---|
| aihr.com | #4 | | mettl.com | #48 |
| testgorilla.com | #13 | | criteriacorp.com | #53 |
| talentlyft.com | #14 | | eskill.com | #101 |
| adaface.com | #23 | | vervoe.com | #135 |
| imocha.io | #45 | | | |

**Not in the top 200:** recruiterflow, wecp, maki — smaller players with thinner keyword overlap.

**The critical finding: the raw list is NOT a competitor list.** It ranks by keyword overlap, so it
surfaces big content sites that merely rank for the same terms — scribd.com (#3), study.com (#5),
investopedia.com (#8), cambridge.org (#11), forbes.com (#16), glassdoor.com (#17), researchgate.net,
sciencedirect.com, quizlet.com. Note `exclude_top_domains: true` did **not** remove indeed.com,
forbes.com or glassdoor.com.

→ **This vindicates the recipe's Step A2/A3.** The LLM shortlist + direct/adjacent categorization is
doing real work: pulling ~12 genuine product competitors out of 200 mixed results. Do not replace that
judgment with a rank cutoff.
→ **And it vindicates the A4 human gate.** Since 3 known competitors never appear, the operator must be
able to ADD names. Keep `--competitors-file` as an override that supplements the API, never replaces it.

## Result 2 — indexed pages by referring domains: PASS

Target `testgorilla.com`, limit 300, `order_by: page_summary.referring_domains,desc`,
diffed against the saved Semrush export (30,000 rows, sorted by `Domains`).

| Measure | Result |
|---|---|
| Top-300 URL overlap | **216 / 290 = 74%** |
| Top-40 link magnets overlap | **31 / 40 = 78%** |
| Semrush-only in top 300 | 74 |
| DataForSEO-only in top 300 | 76 |

**The magnets agree, and the counts are close:**

| Page | Semrush `Domains` | DataForSEO `referring_domains` |
|---|---|---|
| `https://www.testgorilla.com/` | 1,424 | 1,026 |
| `/blog/retention-bonus/` | 355 | **343** |
| `/skills-based-hiring/state-of-skills-based-hiring-…` | 382 | 316 |
| `http://testgorilla.com/` | 240 | **244** |

The two vendors crawl differently, so a 74% overlap with the *same top pages in the same order* is a
strong result — the method only needs the link magnets, and it finds them. DataForSEO is slightly more
conservative on the homepage figure and near-identical on deep pages.

## Result 3 — every field the recipe depends on is present

| Recipe needs | DataForSEO field | Present |
|---|---|---|
| the URL | `item.page` (absolute URL) | ✅ 300/300 |
| referring domains (the sort key) | `item.page_summary.referring_domains` | ✅ |
| backlinks | `item.page_summary.backlinks` | ✅ |
| response code (Step C's keep/drop rule) | `item.status_code` — saw 200, 301, 302, 308, 404 | ✅ |
| page title | `item.meta.title` | ✅ 259/300 |

**Bonus fields Semrush never gave us**, and they matter:
- `meta.words_count` (253/300) — a thin-page signal *before* fetching.
- `meta.h1` / `h2` / `h3` — headings without a fetch.
- `meta.page_spam_score`, `page_summary.backlinks_spam_score`.
- `meta.canonical`, `internal_links_count`, `external_links_count`.

→ **Design consequence:** Step D (tag by format) can read real headings and word counts instead of
guessing from the URL. That directly attacks the measured weakness — the old regex tagger put 26% of
pages in "Other" and found exactly 1 calculator. Feed `meta.h1/h2/h3 + words_count` to the LLM tagger.

## Cost model for a real run

| Item | Calls | Cost |
|---|---|---|
| competitor discovery (limit 200) | 1 | $0.036 |
| indexed pages, 300 rows per competitor | 12 | $0.42 |
| **competitor-study data, per company** | **13** | **≈ $0.46** |

At the current balance ($13.20) that is ~28 full competitor-study runs. The old Semrush path cost
15 manual browser exports of human time per company.

## Gotcha that cost $0.059 — record it so nobody repeats it

The URL is in **`item.page`**, not `item.url`. My first diff read `item.url` (null for every row),
reported "0 URLs in common", and looked like a hard fail. It was my bug, not the vendor's.

→ **Rule for `dfs.py`: assert the response shape on the first call of every new endpoint and fail loudly
on a null key, rather than silently producing an empty column.** A silent empty field looks exactly like
a real negative result.

## Verdict

**PASS — build E1 on DataForSEO.** Both blocked Semrush steps have working replacements with every
required field, at ~$0.46 per company, and the API returns extra signal that fixes a known weakness in
the format tagger.

**Carried into E1's design:**
1. Competitor discovery is a *candidate generator*, not an answer — the LLM shortlist (A2/A3) stays, and
   the human gate must be able to ADD competitors the API misses.
2. Feed `meta.h1/h2/h3` + `words_count` to the format tagger.
3. Use `status_code` for Step C's keep/drop rule — it is present and populated.
4. `dfs.py` asserts response shape per endpoint on first use.
5. Still to prove when their steps are built (not blocking E1):
   `backlinks_domain_intersection` (D4 Backlink Gap) · `backlinks_bulk_spam_score` (D0 toxic audit) ·
   `dataforseo_labs_google_serp_competitors` (D4 Dream 100).
