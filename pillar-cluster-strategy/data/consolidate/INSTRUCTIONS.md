# Subagent task — CONSOLIDATE fine pillars within one domain

Parallel agents each fine-clustered a slice of Testlify's blog. Because they worked independently, the same topic sometimes became 2–3 near-duplicate pillars (e.g. "Coding & Programming Tests" + "Coding & Programming Tests for Tech Hiring" + "Coding & Technical Assessments in Hiring"). Your job: **merge the duplicates within your domain into a clean canonical set of pillars.**

## Input
Your file `data/consolidate/<job>.json` has `pillars: [{pillar, intent, spokes:[slug,...]}]`. Slugs are article titles in URL form.

## Do this
1. **Merge pillars that cover the same topic** into one canonical pillar with the clearest name. Combine their spokes.
2. **Respect the cap: max 15 spokes per pillar.** If a merged topic would exceed 15, split it into clearly-named sibling pillars by a real sub-angle — by role family, seniority, language/tool, sub-topic, or industry (e.g. "Coding Tests — by Language" vs "Coding Tests — Hiring Strategy"). Never exceed 15.
3. **You may move a spoke** to a better-fitting pillar within your domain if it was misplaced.
4. **Minimum 3 spokes** per pillar. Anything that ends up with <3 and no good home → `orphans`.
5. **Every input slug must appear exactly once** in your output (across spokes + orphans). Never invent, drop, or duplicate a slug.
6. Assign each canonical pillar a `theme` from this FIXED list (pick the single best fit):
   - `Interview Questions by Role`
   - `Skills & Job Assessments`
   - `Personality & Aptitude Testing`
   - `Candidate Screening & Proctoring`
   - `Recruiting & Talent Acquisition`
   - `Hiring by Role & Use-case`
   - `Employee Experience & Development`
   - `HR Operations & Compliance`
   - `Workplace Culture & Future of Work`
   - `Skills Management`
   - `Competitor Alternatives`

## Output
Write JSON to `data/consolidate/out/<job>.json`:
```json
{
  "job": "<job>",
  "pillars": [
    {"pillar": "DISC & Personality Assessments", "theme": "Personality & Aptitude Testing",
     "intent": "informational", "spokes": ["slug-a","slug-b","slug-c"]}
  ],
  "orphans": ["one-off-slug"]
}
```
After writing, reply with ONE line: `<job>: X canonical pillars (was Y), Z orphans, N slugs total`.

## Sanity check before writing
- total spokes across pillars + orphans == total input slugs (sum of all input spokes).
- no pillar > 15 spokes, no pillar < 3 spokes.
