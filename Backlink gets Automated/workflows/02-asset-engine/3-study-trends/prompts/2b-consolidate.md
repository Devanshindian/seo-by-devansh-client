You are grouping Reddit phrases into **tensions** for {{BRAND}}'s niche.
A **tension = ONE sentence stating a specific shared pain** (who is frustrated with what) — never a topic label.

## The rule — group by SHARED PAIN, not shared topic
Two phrases belong together only if *one honest conflict sentence* describes the pain behind both — the same
*who is frustrated with what*. If you'd need two different conflict sentences, they are two tensions.
- ✅ "fake remote listings" + "secretly onsite" + "remote then RTO" → ONE tension: *"Candidates apply for roles advertised as remote that turn out to be onsite."*
- ❌ "ghosted after interview" (pain = silence) + "endless interview rounds" (pain = process length) → TWO tensions, even though both are "about interviews".
Don't lean on vague stretch-words ("broken / doesn't work / unfair / outdated") to stretch one sentence over
unrelated phrases — that's a topic, split it.

## The phrases (each with its source post_id)
{{PHRASES}}

## Output — strict JSON only
```
{"tensions": [
  {"tension": "<one specific shared-pain sentence — who is hurt because of what>",
   "phrases": [{"phrase": "<phrase>", "post_ids": ["<id>", "<id>"]}]}
],
 "orphans": [{"phrase": "<phrase>", "post_ids": ["<id>"]}]}
```
Any phrase that fits no clear shared pain goes in `orphans` — do NOT force it into a tension. Every tension
sentence must be specific (a real conflict), never a category verdict like "interviews are broken".
