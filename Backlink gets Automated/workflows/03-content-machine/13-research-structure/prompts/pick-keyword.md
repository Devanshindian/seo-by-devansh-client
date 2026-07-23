You are choosing ONE target keyword for a section (H2) of an article, from DataForSEO candidates.

You are given the H2 label and a list of candidate keywords with their monthly search volume and difficulty (KD).

Pick the SINGLE best keyword to target for this section:
- Relevance first — it must genuinely match what this section is about.
- Then prefer solid volume with reachable difficulty.
- If NO candidate is both relevant and worth targeting, return null. Some sections are differentiators with no
  good keyword, and that is fine — do not force one.

Only pick from the candidates given. Never invent a keyword.

Output STRICT JSON, nothing else:
{ "keyword": "<chosen keyword or null>", "volume": <int or null>, "kd": <int or null>, "why": "<one line>" }

--- H2 ---
{{H2}}

--- CANDIDATES (keyword | volume | kd) ---
{{CANDIDATES}}
