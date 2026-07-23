You are deriving keyword SEEDS for a {{BRAND}} research brief, from an asset's two anchors. Seeds come ONLY
from the anchors below — no free brainstorm.

CONTEXT
- Asset title (verbatim): {{ASSET_TOPIC}}
- Distinct angle (what THIS asset covers, verbatim): {{DISTINCT_ANGLE}}
- Candidate competitor URLs (from the clubbed Proof URLs column — one per line):
{{PROOF_URLS}}

THE COMPANY'S NICHE (what counts as on-angle for this brand): {{NICHE_DEFINITION}}

DERIVE:
- head_seeds: the pillar phrase from the Asset title + 1-2 close variants (form illustration — for an asset
  titled "Recruiting Metrics Benchmark" these would be "recruiting metrics", "recruitment metrics",
  "recruiting metrics benchmark"). These are the article's spine.
- sibling_seeds: the specific sub-topics the DISTINCT ANGLE names (form illustration — an angle listing
  individual metrics would yield one seed per metric, e.g. "time to hire", "cost per hire"). One seed per
  distinct sub-topic the angle covers.
- hygiene: one line flagging any AMBIGUOUS seed that will pull off-topic junk in a keyword-suggestions net
  (form illustration: "time to hire" also pulls car-rental content; a one-word seed pulls unrelated senses of
  the word). Note that it's seeded plain and the Step-3 scorer drops the stragglers on relevance — do NOT
  qualify it here (qualifying starves the core long-tails). If nothing is ambiguous, say so.
- competitor_urls: from the candidate list, DROP only the CLEARLY-unrelated URLs and keep the rest. These feed the
  ranked-net (keywords each page ranks for), which deliberately wants ADJACENT-but-relevant pages — anything inside
  the company's niche above, or its specific sub-topics, is on-angle, KEEP it (adjacency is the point; a bit of
  noise gets re-scored out downstream). Drop ONLY pages whose topic is unrelated to that niche — e.g. an off-niche
  product page, template/boilerplate pages, or generic 101s far below this asset's depth. When unsure, KEEP.
  Keep the verbatim URL strings; invent none.

RETURN JSON only:
{ "head_seeds": ["...", ...], "sibling_seeds": ["...", ...], "hygiene": "one line",
  "competitor_urls": ["https://...", ...] }
