You are naming the **tension(s)** inside one cluster of Reddit pain-phrases from {{BRAND}}'s niche. A similarity
search grouped these phrases because they *sound* related — your job is to state the shared pain precisely, and
to SPLIT the cluster if it actually holds more than one distinct pain.

A **tension = ONE sentence stating a specific shared pain** (who is frustrated with what) — never a topic label.

## The cluster of phrases
{{PHRASES}}

## Rules
- Group by **shared pain, not shared topic.** Phrases belong to one tension only if *one honest conflict sentence*
  describes the pain behind all of them. If you'd need two different conflict sentences, return TWO tensions.
  (E.g. "ghosted after interview" = silence; "endless interview rounds" = process length → two tensions.)
- Don't lean on vague stretch-words ("broken / doesn't work / unfair / outdated") to force phrases together — SPLIT instead.
- A phrase that shares no pain with the others → put it in `orphans` (don't force it).

## Output — strict JSON only
```
{"tensions": [
  {"tension": "<one specific shared-pain sentence>", "phrases": ["<phrase>", "<phrase>"]}
],
 "orphans": ["<phrase>"]}
```
Usually one tension per cluster; return 2+ only when genuinely distinct pains are bundled. Phrases must be
copied verbatim from the cluster above.
