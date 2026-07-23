You are scoring keyword candidates for a {{BRAND}} blog article. Goal: choose ONE primary keyword and a set of
DISTINCT secondary keywords (no fixed cap — follows article type: pillar 8–15, narrow 3–5), plus variations and spokes.

CONTEXT
- Asset topic: {{ASSET_TOPIC}}
- Distinct angle (what THIS asset specifically covers): {{DISTINCT_ANGLE}}
- {{BRAND}} angle (what we sell): {{BRAND_ONELINER}}
- Candidates (keyword | volume | KD | intent):
{{CANDIDATE_TABLE}}

Work in three steps.

STEP 1 — Score each candidate 0–10 on three QUALITY axes (ignore volume here):
- relevance    : how directly it matches the asset topic AND its distinct angle. 10 = dead on (a sub-topic /
                 benchmark / formula the angle covers); 0 = off-topic noise (a keyword about an unrelated
                 subject that merely shares a word with the topic).
- distinctness : is it its own sub-topic, or just the seed/primary + a filler word ("...guide", "...2024")?
                 Score it on its own merit — two genuine siblings CAN both score high; dropping actual
                 near-duplicates is the judge's job. 10 = a distinct sub-topic / sibling; 0 = a suffix-modifier.
- brand_fit    : does writing on it let us naturally use the {{BRAND}} angle? 10 = strong; 0 = none.

STEP 2 — Shortlist on quality only. Drop off-topic rows (relevance ≤2) and weak ones; keep the relevant,
distinct, good-fit candidates. Do NOT look at volume yet.

STEP 3 — Assign roles using VOLUME. From the shortlist only, now bring in volume + KD (the 3 scores break ties):
- "primary"   : exactly ONE — the strongest head term for the pillar; good volume, clears KD.
- "variation" : a REWORD / synonym of the primary — SAME intent + SAME topic, clears KD ceiling + volume floor.
                Woven into the wording in-body; NO section of its own. (A genuinely different sub-topic is a "secondary".)
- "secondary" : EVERY distinct, section-worthy sub-topic — NO fixed cap (pillar 8–15; narrow 3–5). Each a genuinely
                different concept; the judge dedupes near-duplicates.
- "spoke"     : a strong DISTINCT head with different intent that deserves its OWN future article, not this one.
- "drop"      : off-topic or weak.

RETURN a JSON array, one object per candidate, sorted by relevance desc:
{ "keyword": "...", "relevance": 0-10, "distinctness": 0-10, "brand_fit": 0-10,
  "reason": "one line", "role": "primary" | "variation" | "secondary" | "spoke" | "drop" }
Return ONLY the JSON array.
