You are deriving keyword SEEDS for a {{BRAND}} research brief, from an asset's anchors. Seeds come ONLY
from the anchors below — no free brainstorm.

CONTEXT
- Asset title (verbatim): {{ASSET_TOPIC}}
- Distinct angle (what THIS asset covers, verbatim): {{DISTINCT_ANGLE}}
- What this article IS about: {{ABOUT}}
- What this article is NOT about: {{NOT_ABOUT}}
- Candidate competitor URLs (from the clubbed Proof URLs column — one per line):
{{PROOF_URLS}}

THE COMPANY'S NICHE (what counts as on-angle for this brand): {{NICHE_DEFINITION}}

DERIVE:
- head_seeds: the pillar phrase from the Asset title + 1-2 close variants (form illustration — for an asset
  titled "Recruiting Metrics Benchmark" these would be "recruiting metrics", "recruitment metrics",
  "recruiting metrics benchmark"). These are the article's spine.

- sibling_seeds: the specific sub-topics the DISTINCT ANGLE names. One seed per distinct sub-topic.

- hygiene: one line flagging any AMBIGUOUS seed that will pull off-topic junk in a keyword-suggestions net.
  Read the NOT ABOUT line above: where a seed word ALSO means something in one of those other worlds, say
  so here by name (form illustration: a seed containing "CV" also means "coefficient of variation" in
  statistics; "assessment" also means clinical or academic testing). This note is passed to the keyword
  scorer downstream, so name the wrong-world meaning explicitly.
  Seed it PLAIN anyway — the Step-3 scorer drops the stragglers on relevance, and qualifying the seed here
  starves the core long-tails. If nothing is ambiguous, say so.

- competitor_urls: from the candidate list, DROP only the CLEARLY-unrelated URLs and keep the rest. These
  feed the ranked-net (keywords each page ranks for), which deliberately wants ADJACENT-but-relevant pages —
  anything inside the company's niche above, or its specific sub-topics, is on-angle, KEEP it (adjacency is
  the point; a bit of noise gets re-scored out downstream). Drop ONLY pages whose topic is unrelated to that
  niche, or that belong to a world named in NOT ABOUT. When unsure, KEEP.
  Keep the verbatim URL strings; invent none.

RETURN JSON only:
{ "head_seeds": ["...", ...], "sibling_seeds": ["...", ...], "hygiene": "one line",
  "competitor_urls": ["https://...", ...] }
