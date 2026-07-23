You are de-duplicating a CLUSTER of content-asset ideas for {{BRAND}} that a similarity search flagged as
possibly the same. These ideas came from THREE different methods (M1 = competitor study, M2 = other-niche
formats, M3 = Reddit trends), so the SAME idea can appear worded quite differently. Be CONSERVATIVE — when
unsure, keep them separate.

## The cluster (each: id · source method · asset title · format · angle)
{{CLUSTER}}

## Your THREE actions
**1. SAME — they are the same asset to build**, just surfaced by different methods or worded differently
("State of Skills-Based Hiring report" from M1 and "annual hiring-trends report" from M3 = the same build).
NOT merely the same topic. When SAME: pick the id whose entry is clearest/richest to KEEP; the others merge
into it. **Do not edit text.** (Their source tags and proof get pooled automatically — an idea two methods
found is a STRONGER bet, so the merged row records it came from both.)

**2. COMBINE — two DIFFERENT but complementary ideas that built as ONE make a richer asset.** Cross-method
this is powerful: M2's proven FORMAT + M3's timely TENSION on one topic can fuse into a stronger asset than
either. Write a new `new_asset` title + `new_angle`. Use sparingly, only when clearly stronger.

**3. SEPARATE — genuinely different builds.** The default. Most pairs, even across methods, are SEPARATE.

## Output — strict JSON only
```
{"groups": [
   {"action": "same",    "ids": [<id>, <id>], "keep": <id>},
   {"action": "combine", "ids": [<id>, <id>], "new_asset": "<title>", "new_angle": "<one-line angle>"}
]}
```
List a group ONLY for ids you act on; any id not listed stays separate. `keep` must be one of its own ids.
When unsure, choose SEPARATE — keep more, not less.
