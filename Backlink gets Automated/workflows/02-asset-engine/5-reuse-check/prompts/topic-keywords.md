You label content-asset ideas with their DISTINCTIVE topic terms, for a deterministic keyword catalogue.

For each asset title below, emit 1-3 topic keywords that a page on this exact subject would carry in its
title or URL. The keywords drive a literal substring match, so:

- Pick SPECIFIC, distinctive terms: `psychometric`, `resume screening`, `time to hire`, `cognitive ability`.
- AVOID generic filler that would match everything: `hiring`, `test`, `assessment`, `guide`, `template`,
  `report`, `free`, `online`, `best`, `top`, `checklist`, `tool`, `software`, `platform`, `2024`, `2025`.
- 1-3 keywords per asset. Prefer the noun phrase that names the subject, not the format.
- Keep them short (1-3 words each) and lowercase.

THE ASSETS (numbered):
{{ASSETS}}

Return ONLY a JSON array, one object per asset, using the SAME index number shown:
[{"i": 0, "keywords": ["skills-based hiring", "quality of hire"]}, {"i": 1, "keywords": ["time to hire"]}]
