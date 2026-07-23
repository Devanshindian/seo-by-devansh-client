# Subagent task — propose likely HUB URLs for each pillar (for live probing)

For each content pillar, propose the URL slugs where Testlify would most plausibly host a **hub/pillar page** for that topic. We will hit these URLs live and follow redirects, so good guesses matter.

## Input
`data/probe/in-src/<key>.json` — your theme's pillars (name + sample spokes). Slugs there are article titles in URL form.

## How Testlify's URLs look (match this style)
Short, topical, hyphenated slugs, e.g.: `coding-tests`, `psychometric-tests`, `situational-judgment`, `campus-hiring`, `remote-hiring`, `skills-management`, `skills-mapping`, `succession-planning`, `employee-onboarding`, `interview-questions-bank`, `sales-hiring`. Interview-question pillars usually map to `<role>-interview-questions` or the generic `interview-questions`.

## Rules
- Propose **1–3 candidate slugs per pillar**, ordered best-guess first.
- Prefer **short canonical topical slugs**, NOT the long descriptive pillar name. (Pillar "Hiring Developers with Programming Skill Tests" → candidates `programming-tests`, `coding-tests` — not `hiring-developers-with-programming-skill-tests`.)
- Always include the most generic sensible form as one candidate (e.g. for any interview-questions pillar include `interview-questions`).
- Slugs only: lowercase, hyphens, no domain, no slashes, no trailing slash.

## Output
Write JSON to `data/probe/in/<key>.json`:
```json
{"key":"c01","candidates":[
  {"pillar":"Sales Role Interview Questions","slugs":["sales-interview-questions","interview-questions"]},
  {"pillar":"Coding & Programming Tests","slugs":["coding-tests","programming-tests","coding-assessment"]}
]}
```
Every input pillar must appear exactly once. After writing, reply ONE line: `<key>: N pillars, M candidate slugs`.
