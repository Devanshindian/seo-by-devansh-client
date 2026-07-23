You are scoring {{BRAND}}'s surviving Method 2 ideas on two axes, using the SAME scales as Method 1. Score
every idea below.

## The ideas to score
{{IDEAS}}

## `beatability` (1-3) — how easy to make the asset itself link-worthy
(Method 2 has no in-niche competitor page to measure against — that comparison is a merge-step concern.)
- **3** — simple format (glossary, listicle, basic calculator), short build, fast win.
- **2** — moderate (interactive tool, data-light index, definitive guide).
- **1** — heavy (proprietary data report, complex interactive, full microsite).

## `effort` (S/M/L)
- **S** — days to a week (a glossary entry, a single calculator, a stats roundup).
- **M** — weeks (a 30-term glossary section, an interactive index with limited data, a definitive guide + template).
- **L** — a month+ (annual research, full microsite, custom-built interactive).

## Output — strict JSON only
```
{"scores": [
  {"id": <idea id, integer>, "beatability": <1-3>, "effort": "<S | M | L>"}
]}
```
One entry per idea, same ids.
