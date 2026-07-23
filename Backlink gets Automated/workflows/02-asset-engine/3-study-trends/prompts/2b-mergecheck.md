You are running the **merge check** — the gate that stops phrases being merged by shared *topic* instead of
shared *pain*. For {{BRAND}}'s niche. This is the most important quality step; do it honestly, per phrase.

## The candidate tensions (first-pass grouping — some may be over-merged topic-blobs)
{{TENSIONS}}

## For EACH candidate tension, run the check
1. **Write the one shared-pain sentence.** State the *specific* pain behind ALL its phrases:
   "[who] [is hurt because / can't / is dragged through] [one specific thing]."
2. **Test every phrase against it.** For each: does that exact sentence describe the pain behind THIS phrase,
   specifically (not loosely)? Every phrase a clear YES → **PASS**. Had to stretch to fit any → **SPLIT**.
3. **Vague-predicate tripwire.** If the sentence only holds because it leans on a stretch-word — *doesn't work,
   is broken, is a mess, is frustrating, is flawed, barely predicts, is unfair, is outdated, struggles with* —
   it's a topic, not a tension → **SPLIT**.
4. **Size alarm.** A tension with **> {{MAX_POSTS}} posts OR > {{MAX_PHRASES}} phrases** is *presumed merged-by-
   topic* → SPLIT, unless one specific shared-pain sentence honestly covers all of them (say so).
5. **On SPLIT** — re-derive the correct tensions hiding inside: for each, its specific shared-pain sentence +
   exactly which phrases belong. Any phrase fitting none → `orphans` (don't force it).

## Output — strict JSON only
```
{"checked": [
  {"original": "<the candidate tension sentence>",
   "verdict": "PASS" | "SPLIT",
   "shared_pain": "<the one sentence you wrote in step 1>",
   "per_phrase": [{"phrase": "<phrase>", "fits": true}],
   "result_tensions": [
     {"tension": "<final specific shared-pain sentence>", "phrases": [{"phrase": "<phrase>", "post_ids": ["<id>"]}]}
   ]}
],
 "orphans": [{"phrase": "<phrase>", "post_ids": ["<id>"]}]}
```
On PASS: `result_tensions` is the single tension unchanged. On SPLIT: `result_tensions` is the 2+ correct ones.
`per_phrase` records the PASS/SPLIT evidence per phrase (this becomes the audit file). Be strict — when a
sentence needs a stretch-word to hold, SPLIT.
