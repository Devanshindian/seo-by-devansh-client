You are writing `research-notes.md` — the SEPARATE agent-commentary file that sits beside the clean brief. It
holds what actually happened this run: judgment calls, anything weak/uncertain, and follow-ups. Opinions and
caveats live HERE, never in the clean brief.

ANCHORS
- Asset: {{ASSET_TOPIC}}
- Distinct angle: {{DISTINCT_ANGLE}}

WHAT HAPPENED THIS RUN (raw material — read it and comment; do not just restate):
- Keyword decision (03-keywords.md + judge notes):
{{KEYWORDS}}
- Pool → shortlist sizes: {{POOL_STATS}}
- SERP snapshot:
{{SERP_SNAPSHOT}}
- Winners:
{{WINNERS}}

RETURN markdown in this shape:
# Research notes — <short asset name> (agent commentary)

*Separate from the clean brief. What happened, calls made, what's weak, follow-ups.*

## Judgment calls
- <the real calls: why this primary; anything folded; any homonym the scorer had to drop; in-body-only choices>

## Weak / uncertain
- <honest weaknesses: is the head small? incumbents strong? any parse cap? any API hiccup noted upstream?>

## Step 6

## Follow-ups
1. <concrete next action for the write phase — e.g. protect the in-body differentiators>
2. <...>

Be specific and honest. One item per line. Output ONLY the markdown.
