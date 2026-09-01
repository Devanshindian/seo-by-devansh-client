You have web search. Run the queries below and return the best result page URLs.

QUERIES:
{{QUERIES}}

Rules:
- Run every query. Collect the strongest organic results across all of them (skip ads/sponsored).
- Return up to {{MAX}} unique page URLs, most relevant first.
- Only REAL URLs that actually appeared in results — never constructed or guessed.

Return ONLY this JSON, nothing else:
{"urls": ["https://...", ...]}
