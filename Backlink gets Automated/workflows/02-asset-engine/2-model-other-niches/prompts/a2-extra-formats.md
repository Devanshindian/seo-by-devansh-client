You are building a **swipe library** of proven cross-niche link-bait FORMATS for {{BRAND}} — the *shape* of an
asset (a calculator, an index, a generator), never a subject. You already have this set of formats from a
curated dataset:

{{EXISTING_FORMATS}}

## Your job
From your own knowledge, add **{{N}} more** famous link-magnet formats that are **NOT already in the list
above**. Each addition must satisfy all three:
- (a) it earned real **backlinks** (not just traffic or social shares),
- (b) it worked across **multiple** niches (not a one-industry fluke),
- (c) you can name at least one **real, specific example** with a recallable URL.

Examples of the kind of thing (do NOT reuse these — find your own): the Big Mac Index, the HubSpot Website
Grader, the Best Places to Work award.

## Output — strict JSON only, nothing else
```
{"formats": [
  {"format": "<format name, e.g. 'Branded index'>",
   "example": "<real named example + URL, e.g. 'Big Mac Index — economist.com/big-mac-index'>",
   "headline_template": "<fill-in headline shape, e.g. 'The [TOPIC] Index'>",
   "why_links": "<one phrase naming the link mechanism: Utility / Data / Reference / Visual / Ego-bait / Emotion>"}
]}
```
Rules: exactly {{N}} formats. No example you cannot name = drop that format and pick another. No format already
in the list above. Match the four-field shape exactly so these rows concatenate onto the existing table.
