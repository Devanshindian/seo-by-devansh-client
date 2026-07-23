# Testlify — Do we actually have working pillar-clusters? (live, two-step check)

**Date:** 2026-07-07 · Corrected after a fair challenge: my earlier "hub built" verdict only checked that a *page existed at the URL* — not whether that page **links down to its cluster posts**. A pillar that doesn't link to its children is not a working pillar. This version checks **both**.

## Method (two live checks per pillar)
1. **Does a hub page exist?** Guessed the likely hub URL for each of the 373 pillars, hit it live (redirects followed), classified where it lands. → 110 had a real page.
2. **Does that hub link to its cluster?** Downloaded the actual HTML of all 42 unique hub pages, extracted every outbound link, and intersected with each pillar's spoke-post slugs. → this is the decisive test.

Raw evidence: `data/hubhtml/` (the fetched pages), `data/linkcheck-results.json` (per-pillar link match), `data/pillar-coverage.csv` (all 373 with status + how many cluster posts the hub links to).

## The honest verdict

| Status | Meaning | Pillars |
|---|---|---:|
| ✅ **Pillar working** | hub page exists **and** links to a real share of its cluster posts | **1** |
| 🟩 **Pillar, weak links** | hub exists but links to only 1–few of its posts | **3** |
| 🟧 **Page exists · 0 cluster links** | a page exists at the topic URL, but it links to **none** of its cluster's posts | **106** |
| 🔵 **Lead article only** | just one cornerstone post, no structured hub | **156** |
| 🟡 **Thin page only** | only a glossary/tools page | **44** |
| 🔴 **No hub** | nothing exists | **63** |

### One line
**Out of 373 clusters, essentially ZERO are working pillar-clusters** — only 1 clearly links to its children (and it's the `/alternatives/` page linking to 2 competitor-comparison posts). **You were right:** the pages I'd marked "built" are real pages, but they do **not** link down to the article clusters beneath them.

## Why the 110 "built" pages fail the real test

They are **product / landing / test-library pages**, not content hubs. Each has ~107–120 outbound links — but those are almost entirely the **global nav menu and footer** (identical on every page). When you subtract the template and look at links to actual blog posts:

| Hub page | Total links | Links to *blog posts* | Links to *its own cluster* |
|---|---:|---:|---:|
| `interview-questions-bank` | 120 | 14 (generic recruitment posts) | **0** of its role-interview posts |
| `coding-tests` | 108 | 2 (incl. the `/blog/` index) | **0** |
| `cognitive-ability-tests` | 108 | 2 | **0** |
| `psychometric-tests` | 109 | 2 | **0** |
| `test-library/*` (every category) | 110 | 1 (the `/blog/` index) | **0** |
| `skills-assessment-and-interviewing-platform` | 112 | 1 | **0** |

So even the best case (`interview-questions-bank`) links to a handful of *general* articles, none of which are the role-based interview-question posts that make up its cluster. Every test-library category page links to exactly one blog URL — the blog index — and none of its topic articles.

*(This is not a crawler artifact: the pages render server-side; the links simply aren't there. A JS-loaded "related posts" widget, if any, would add a few generic links at most — not the structured cluster.)*

## What this means

Testlify has **content** (2,972 posts) and **landing pages** (product/test-library/use-case) — but the two are **not wired together**. There is no layer of hub pages that gather a topic's articles and link to them. So:

- **Google can't see topic authority clusters** — the posts float as ~3,000 individual pages with no pillar tying them together.
- The "pillars" that exist are conversion pages, pointed at signup, not at the blog.

## What to build (revised priority)

1. **This is a build-from-near-zero, not a cleanup.** Plan for ~370 pillar hubs (or hub *sections*), because almost none function today.
2. **Fastest wins — the 106 "orphan pages":** the page already exists and ranks; just **add a cluster-links section** to it (link its ≤15 posts). Cheapest way to create ~106 working pillars. Start with `interview-questions-bank`, `coding-tests`, the `test-library/*` category pages.
3. **156 "lead article only":** promote each cornerstone post into a hub by adding its cluster links, or build a dedicated hub above it.
4. **63 "no hub" + 44 "thin":** build the hub page from scratch.
5. **Every case also needs the reverse link** — each spoke post should link *up* to its pillar. (Not measured here; that's the spoke→pillar direction — a natural next crawl.)

## Limitations (still honest)
- Cluster membership is judged from post **titles**; a few posts sit in a debatable pillar.
- Hub URLs were **guessed then verified**; a hub at a totally unguessed slug could be missed (would understate "exists" — but the link-check result would be the same: they don't link to clusters).
- Only **pillar → spoke** links were checked. The **spoke → pillar** direction wasn't crawled yet.
