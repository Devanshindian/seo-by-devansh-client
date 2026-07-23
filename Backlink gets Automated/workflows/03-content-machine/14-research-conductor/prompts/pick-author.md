You are choosing the ONE author byline for a {{BRAND}} article. The reader persona is ALREADY decided upstream —
you only decide the author. Apply the voices doc's "Auto-route rules" IN ORDER — don't invent new ones.

ARTICLE
- Title: {{ASSET_TITLE}}
- Angle (what it specifically covers): {{ANGLE}}

VOICES DOC (has "Auto-route rules" — follow them exactly):
{{VOICES_DOC}}

Apply the voices doc's auto-route rules IN ORDER, exactly as written there. If no rule fires, use the doc's
default company byline. Do NOT route to any author the doc marks as explicit-request-only — there is no such
request here. The doc is the single source of truth for who exists and when they are used; never invent or
restate authors from anywhere else.

RETURN JSON only:
{ "display_name": "<an author display name exactly as it appears in the voices doc>",
  "byline_line": "<the exact 'Byline line'/'Credential line' from the voices doc for that author>",
  "why": "which auto-route rule fired and why" }
