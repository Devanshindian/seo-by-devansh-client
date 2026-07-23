You are writing the judgment fields for each tension in {{BRAND}}'s niche. The counts (posts, upvotes, comments,
spread) are computed mechanically elsewhere — you only write what needs reading.

## The tensions, each with its phrases and the posts assigned to it
{{TENSIONS}}

## For EACH tension, produce these fields
- **core_pain** — what's actually hurting people, 1 line. Read the phrases and name the hurt *under* them. (Tension
  = the conflict; core pain = why it stings.)
- **audience** — who is speaking: `employer`, `candidate`, or `both`. **Don't default to "both"** — pick "both"
  only when both sides genuinely argue inside the pile; recruiters venting = `employer`.
- **emotion** — pick EXACTLY ONE of: {{EMOTIONS}}. No free-text (map frustration→anger, despair→anxiety, etc.).
- **best_example** — the single post_id (from this tension's post list) that most clearly embodies the tension.
- **representative_quotes** — 2-3 vivid **verbatim** quotes from the posts/comments (the real language people use).
- **sub_questions** — the distinct questions people **actually argue about** in the posts (potential content angles).
  Do NOT include solution/product questions ("would a skills test fix it?") — that is a later step leaking backward.
  **Banned wording in sub_questions (never use these exact phrases — they read as solution-framing):** "skills test",
  "skills tests", "skills screening", "skills-based screening", "skills-based hiring", "objective testing",
  "blind/skills", "{{BRAND}}", "our platform", "our product". Phrase the debate in the people's own neutral terms.
- **implied_data_point** — the measurable number this tension is begging for (e.g. "% of 'remote' listings that are secretly onsite").

## Output — strict JSON only
```
{"records": [
  {"tension_id": "<the tension code EXACTLY as shown, e.g. T01>", "core_pain": "...", "audience": "employer|candidate|both",
   "emotion": "<one of the closed set>", "best_example": "<post_id>",
   "representative_quotes": ["...", "..."], "sub_questions": ["...", "..."], "implied_data_point": "..."}
]}
```
One entry per tension. `emotion` must be exactly one of the closed set; `sub_questions` carry no product/solution wording.
