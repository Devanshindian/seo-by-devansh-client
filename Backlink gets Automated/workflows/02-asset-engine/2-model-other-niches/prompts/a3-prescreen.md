You are pre-screening proven cross-niche link-bait FORMATS for {{BRAND}} on brand fit. This is a LIGHT
pre-screen — the real scored filter comes later, once each format has a real subject. Your only job here: for
each bare format, decide whether it can *plausibly* be pointed at a subject inside {{BRAND}}'s scope.

## {{BRAND}}'s brand scope (the ownership anchor — judge against THIS)
{{BRAND_SCOPE}}

## The formats to pre-screen (each is a shape, no subject yet)
{{FORMATS}}

## For EACH format, answer one question
> *Can this format plausibly be pointed at a subject inside {{BRAND}}'s brand scope?*

- **The transplant check is MANDATORY before dropping.** If the format's obvious subject is off-brand, look for
  an in-scope subject the same *shape* could serve before binning it (a celebrity quiz → a "what's your hiring-
  bias profile" quiz).
- **Drop only a format you cannot imagine pointing at ANY in-scope subject.** Keep most — the real cut is later.

## Output — strict JSON only
```
{"screened": [
  {"format": "<the format name, verbatim from the input>",
   "keep": true,
   "in_scope_subject": "<a nameable subject inside scope a writer could build on, e.g. 'Cost of a bad hire'. Not a vague theme.>",
   "brand_fit": "<CORE | TRANSPLANT | ADJACENT>",
   "transplant_from": "<if TRANSPLANT: the off-brand subject it came from, e.g. 'cost-of-living'. else empty.>"},
  {"format": "<name>", "keep": false, "drop_reason": "<why no in-scope subject exists, even after the transplant check>"}
]}
```
Rules: one entry per input format, same order. `brand_fit` here is a ROUGH tag (the later Ownability test sets
the authoritative one). `in_scope_subject` must be a specific nameable subject, never "hiring stuff".
