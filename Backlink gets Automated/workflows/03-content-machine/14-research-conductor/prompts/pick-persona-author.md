You are tagging a {{BRAND}} article with its ONE reader persona and ONE author byline, for the research bundle
handed to the writer. Apply the rules that ALREADY live in the two docs below — don't invent new ones.

ARTICLE
- Title: {{ASSET_TITLE}}
- Angle (what it specifically covers): {{ANGLE}}

PERSONA DOC (has a "How to pick one per article" section — follow it exactly):
{{PERSONA_DOC}}

VOICES DOC (has "Auto-route rules" — follow them exactly):
{{VOICES_DOC}}

DECIDE:
1. PERSONA — match the article's topic + intent to the ONE best-fit persona using the persona doc's "How to pick"
   rules. If it could fit two, pick the one who decides/acts on it. (This sets depth/angle only — it is NEVER named
   in the article.)
2. AUTHOR — apply the voices doc's "Auto-route rules" IN ORDER, exactly as written there. If no rule fires,
   use the doc's default company byline. Do NOT route to any author the doc marks as explicit-request-only —
   there is no such request here. The doc is the single source of truth for who exists and when they are used.

RETURN JSON only:
{ "persona": { "name": "<exact persona name from the doc>", "why": "one line tying it to the topic/intent" },
  "author":  { "display_name": "<an author display name exactly as it appears in the voices doc>",
               "byline_line": "<the exact 'Byline line'/'Credential line' from the voices doc for that author>",
               "why": "which auto-route rule fired and why" } }
