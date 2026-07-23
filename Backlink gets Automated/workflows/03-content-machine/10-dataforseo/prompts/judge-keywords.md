You are the lead editor choosing the final keyword set for a {{BRAND}} article, from the independent scorer
verdicts (there may be any number of them).

CONTEXT
- Asset topic: {{ASSET_TOPIC}}
- Distinct angle: {{DISTINCT_ANGLE}}
- The scored verdicts, clubbed from all batches/passes (JSON arrays of
  {keyword, relevance, distinctness, brand_fit, role}):
  {{VERDICTS}}
- Numbers per keyword (keyword | volume | KD | intent):
{{METRICS_TABLE}}

DECIDE the final set:
- PRIMARY (exactly 1): from the heads that match the asset's intent AND clear KD, pick the **HIGHEST-VOLUME** one.
  Do NOT default to the exact article-title phrase if a higher-volume intent-match exists — the title can still be
  the H1, but the tracked primary is the strongest keyword by volume.
- VARIATIONS (0..n): rewords / synonyms of the PRIMARY — SAME intent + SAME topic — that clear KD ceiling + volume
  floor. Woven in-body; NO section of their own. Capture them as a distinct list (don't fold them into the primary).
  Never list a term of different intent (e.g. job-seeker vs employer) here.
- SECONDARY (NO fixed cap): every DISTINCT sub-topic that would be a SECTION INSIDE THIS article. Prefer keywords
  kept by more than one verdict; no two near-duplicates (fold word-order dups + "calculate X"/"calculating X" into
  the parent). Pillar 8–15; narrow 3–5. Tell: "could this be one H2 of this exact article?" → yes = secondary.
- SPOKE CANDIDATES: NOT a section of this article — its own future article. Three tells, any one → spoke, not
  secondary: (a) TOOL/utility intent (a "…calculator", "…template", "…dashboard"); (b) an ADJACENT PILLAR big
  enough to be its own guide (a broad neighbouring head term that deserves a full guide of its own); (c) clearly
  DIFFERENT intent/audience from the primary. When a term could be a stretch section OR a spoke, and
  it's a broad head in its own right, prefer SPOKE — keep the secondary list to true in-article sections.
  For EACH spoke, also give **`relevance` 0–10** = how strongly it belongs to the SAME content cluster as this asset —
  a natural COMPANION article a reader of this piece would click next — NOT how close it is to the article itself
  (a spoke is distinct by design). 8–10 = tightly in the pillar (a sibling topic the same reader needs next);
  4–7 = related but broader; 0–3 = a generic/off-cluster head whose intent overshoots this asset (form
  illustration: a one-word industry-agnostic head with huge volume — big but generic). This score decides which
  spokes we keep — anything you score **0–2 is dropped outright**, whatever its volume — so a big volume must NOT
  rescue an off-cluster head.
- IN-BODY (0..n): angle-critical terms worth covering even though they didn't clear the volume floor (if you know
  any from the topic/angle). Not ranking targets.
- Ignore any keyword every verdict dropped.

RETURN JSON:
{ "primary":     { "keyword", "volume", "kd", "intent", "why" },
  "variations":  [ { "keyword", "volume", "kd" }, ... ],
  "secondary":   [ { "keyword", "volume", "kd", "why" }, ... ],
  "spoke_candidates": [ { "keyword", "volume", "kd", "intent", "relevance", "why" }, ... ],
  "in_body":     [ "term", ... ],
  "notes": "any scorer disagreement you resolved" }
Return ONLY the JSON object.
