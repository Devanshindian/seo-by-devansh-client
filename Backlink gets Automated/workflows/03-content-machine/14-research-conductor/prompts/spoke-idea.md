You are {{BRAND}}. A "spoke" is a supporting article under a PILLAR article. We have a validated search keyword
for the spoke (decent volume, low difficulty), but it's just a bare keyword — it has no title and no angle yet.
Your job: turn it into a real, buildable article idea, the same shape a normal idea has.

## The pillar this spoke sits under
- Pillar title: {{PILLAR_ASSET}}
- Pillar angle: {{PILLAR_ANGLE}}

## The spoke keyword (the search demand we're answering)
- Keyword: {{KEYWORD}}
- Signals: {{SIGNALS}}

## {{BRAND}} in one line
{{BRAND_ONELINER}} — on-topic scope: {{NICHE}}

## Rules
- The idea must target the SPOKE KEYWORD's search intent (that's the validated demand), and support the pillar.
- Give it a real working title a writer could open a doc with — subject + angle, NO shape-words (no "Calculator",
  "Quiz", "Interactive", etc.).
- The distinct angle = what makes OUR version worth linking/reading, deliverable by a writer with public sources
  (a content angle — not "add a tool" or "our own proprietary data").
{{RETRY_NOTE}}

Return strict JSON only:
{"title": "<real working title, subject + angle, no shape-words>",
 "angle": "<one line: what makes ours the best answer to this keyword, within our scope>"}
