You are reading a DataForSEO research brief for an article and pulling out the items the article must
cover, so a later step can check whether our research dossier covers each one.

Read by MEANING, not by exact formatting. The brief usually follows a fixed shape, but headings, labels,
and layout can drift — find the right content even if the wording or structure varies.

Capture from the top of the brief:
- asset_title    — the article/asset title.
- distinct_angle — the "distinct angle" line (what makes this article different).
- primary        — the primary keyword.

Then pull these ITEMS, each tagged with a type. One entry per item — never several on one line.

| type          | pull from                                              | context to attach |
|---------------|--------------------------------------------------------|-------------------|
| secondary_kw  | the Secondary keywords table — each keyword            | the section it anchors, if given |
| in_body       | the "In-body only" list — each phrase                  | — |
| winner_h2     | "What the winners cover" → the common H2s / subtopics  | — |
| gap_we_own    | "What the winners cover" → "Gaps we can own"           | — |
| paa           | SERP snapshot → PAA **on-angle** questions             | — |
| aio_subtopic  | SERP snapshot → AI Overview "what it covers"           | — (capture the subtopics it names as ONE item) |
| aeo_faq       | AI answer landscape → FAQ candidates                   | ONLY if that section shows a usable signal; if it says "no usable signal", pull NOTHING for aeo_faq |

EXCLUDE entirely (do not output these): spokes, PAA off-angle, related searches, the featured-snippet
holder, "cited by AI / GEO gap" lines, the build spec, the verdict, and the proof map. These are
positioning notes, not things the dossier must cover.

Output STRICT JSON, nothing else. No markdown, no commentary:
{
  "asset_title": "...",
  "distinct_angle": "...",
  "primary": "...",
  "items": [
    { "type": "secondary_kw", "item": "<the item text>", "context": "<context or empty string>" }
  ]
}

--- BRIEF ---
{{BRIEF_TEXT}}
