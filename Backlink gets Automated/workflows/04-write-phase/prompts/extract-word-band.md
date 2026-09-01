Extract the target word band from this research brief. The brief has a line labelled **Word band:**.

BRIEF:
{{DOC}}

Rules:
- "3,000-4,000 words" -> min 3000, max 4000. Strip commas.
- If only ONE number is given: min = that number, max = round(min * 1.2).
- If genuinely absent: {"min": 0, "max": 0}. Never invent.

Return ONLY this JSON, nothing else:
{"word_band": {"min": <integer>, "max": <integer>}}
