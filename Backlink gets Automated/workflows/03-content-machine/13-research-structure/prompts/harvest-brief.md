You are reading a DataForSEO research brief and pulling out the items that should become "cards" for building
an article's structure. Read by meaning; the brief's exact formatting may vary.

Pull these, each as one card with a tag:
- **competitor** — the common H2s / subtopics the winning pages cover ("What the winners cover"), and the
  subtopics the AI Overview names ("what it covers"). These are table-stakes coverage.
- **gap** — the "gaps we can own" (our differentiators), and any "in-body only" angle-critical items.
- **question** — the on-angle PAA questions and the AEO FAQ candidates (skip off-angle ones).

Do NOT pull: the primary/secondary keywords, off-angle PAA, related searches, the featured-snippet holder,
"cited by AI" lines, the build spec, or the verdict.

For each card, the "gloss" is the item's text itself (a heading, phrase, or question), cleaned up to one line.

Output STRICT JSON, nothing else — an array:
[
  { "gloss": "...", "tag": "competitor" | "gap" | "question" }
]

--- BRIEF ---
{{BRIEF_TEXT}}
