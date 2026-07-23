You are writing the "SERP snapshot" section of a research doc for a {{BRAND}} article.

CONTEXT (use this to judge relevance)
- Asset topic: {{ASSET_TOPIC}}
- Distinct angle (what THIS asset specifically covers): {{DISTINCT_ANGLE}}
- Primary keyword: {{PRIMARY_KEYWORD}}

INPUT (raw SERP extract, JSON):
{{SERP_EXTRACT}}

DO THIS:
1. Top organic — read ALL of them, no filtering (this is the competitor set). Name the set + what kind of sites
   they are in one line. THEN do a read-list sanity check: from the full top-organic list pick the TOP 3 most
   relevant, READABLE pages for Step 5 to open — real articles on the topic. SKIP: PDFs/downloads (no HTML
   structure), off-topic homonyms, thin stubs (forum threads, wiki, glossary) UNLESS one is genuinely the best
   source. Rank order is a starting point, not the rule — a relevant #4 beats an irrelevant #1. Note any high-rank
   page you skip and why.
2. Featured snippet — holder + format, or "none — open to win with a matching-format answer".
3. AI Overview — capture BOTH substance and cites:
   a. SUBSTANCE — a 1-line summary of how it defines the topic, then the metrics/sub-topics it names and how it
      groups them (verbatim, in its own order — the answer skeleton). Content only; do NOT list its questions.
   b. CITES — the domains it cites; is {{DOMAIN}} among them? If not: GEO gap.
4. RELEVANCE PASS on PAA + related searches. Tag EACH item ON-ANGLE (asks about the sub-topics THIS asset covers,
   per the distinct angle) or OFF-ANGLE (generic trivia adjacent but not what the asset covers). Keep BOTH lists
   verbatim — nothing dropped without a reason.

RETURN markdown, factual, no fluff, ONE item per line, in EXACTLY this shape:
### SERP snapshot — {{PRIMARY_KEYWORD}}

**Who ranks:**
- one line naming the competitor set + what kind of sites they are
- (add lines for notable outliers, e.g. a Reddit thread or Wikipedia)
- one line on the open gap (is any of them the exact angle this asset owns?)

**Featured snippet:**
- <holder> holds it (format), or "none — open to win with a 40-60 word definition"

**AI Overview** — present-to-a-clean-US-crawler / absent *(volatile: personalized, may not show for every user)*:
- What it covers: 1-line definition + the metrics/sub-topics it names, in its order
- Who it cites: domains — {{BRAND}} cited by this AI Overview? No → GEO gap / Yes
  (omit this whole AI Overview block's detail lines if absent; just say "absent")

**PAA — on-angle (FAQ candidates):**
- one per line, verbatim

**PAA — off-angle (excluded):**
- one per line, verbatim (or "none")

**Related searches — on-angle:**
- one per line (or "none")

**Related searches — off-angle:**
- one per line, or "none" + one line on any demand signal worth noting (template/dashboard/pdf etc.)

**Read-list handed to Step 5:**
- the 3 chosen domains (real articles; note what was skipped and why) → `04-pages-to-read.txt`

**Raw:** `<run_dir>/proof/04-serp.json`

THEN, after the markdown, on a NEW line output a fenced block with EXACTLY the 3 read-list URLs (verbatim from the
extract's top_organic urls), one per line, so a script can save them:
```readlist
https://...
https://...
https://...
```
