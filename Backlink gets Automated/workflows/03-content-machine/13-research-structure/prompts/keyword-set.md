You are extracting the KEYWORD SET from an SEO research brief, so the write phase can later check the article
actually covers every keyword. Read ONLY the brief's "## Keywords" section.

Brief:
<<<
{{BRIEF_TEXT}}
>>>

Return ONLY this JSON (no prose):
{
  "primary": "the single primary keyword (the article's spine)",
  "variations": ["rewords / synonyms of the SAME primary topic that get woven into the wording (no own section). Take these from the 'Variations' subsection if present; otherwise pull them from the Primary entry's notes (the 'folds in' synonyms, the easiest-variant, etc.). NOT the primary itself; NOT the secondaries"],
  "secondaries": ["each distinct secondary keyword — the ones that anchor their own section (from the Secondary table's keyword column)"],
  "in_body": ["the in-body-only items (angle-critical terms with little/no search volume)"]
}

Rules:
- variations = reword of the same topic (woven in, NO own section). secondaries = distinct sub-topic (own section). Keep them separate.
- Deduplicate. If a field has nothing, return [].
- Return ONLY the JSON object.
