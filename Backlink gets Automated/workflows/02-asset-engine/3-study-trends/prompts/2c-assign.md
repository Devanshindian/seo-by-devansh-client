You are assigning Reddit posts to the tension whose pain they most embody, for {{BRAND}}'s niche.

## The tensions (assign each post to ONE, by id)
{{TENSIONS}}

## The posts (content cards)
{{CARDS}}

## Rules
- Pick the tension by the **dominant pain**, not surface words or an incidental detail. (A post about a marathon
  interview that also mentions pay belongs in the interview-rounds tension — don't let the pay mention drag it
  into a salary pile.)
- One **primary** tension per post. Optionally note one secondary tension id as a cross-reference (it does not
  move the post).
- **No "off-brand" or "ignore" bucket** — brand fit is decided later. Every coherent pain gets its real tension.
- Use `misc` **only** for a post that shares no pain with any tension — never as a dump for off-brand-but-coherent
  posts.

## Output — strict JSON only
```
{"assignments": [
  {"post_id": "<id>", "tension_id": "<the tension code shown, e.g. T01, or 'misc'>", "secondary_id": "<a code or empty>"}
]}
```
One entry per input post, every post_id included. `tension_id` must be one of the codes shown above, or `misc`.
