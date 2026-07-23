You are tagging Reddit posts from {{BRAND}}'s niche with the phrases that capture what each post is about.
This feeds a later step that finds recurring pains across many posts, so faithfulness matters more than cleverness.

## The posts (each is one content card: id + subreddit + score/comments + title + body + image text + top comments)
{{CARDS}}

## For EACH post, pull the 2-3 phrases that best capture it
- (1) the post's **core complaint or claim** (what the OP is actually angry or anxious about), plus
- (2) **any point multiple *different* commenters converge on** (several independent voices on one thing = real signal).
- Always **tight phrases of 2-4 words** — never single words ("remote" is noise; "fake remote listings" is signal).
- Prune filler ("at the end of the day", "in this economy") — don't write it down.
- Thin posts may yield one phrase or none — that's fine, don't invent.
- Do NOT measure recurrence inside one post; just capture this post faithfully.

## Output — strict JSON only
```
{"posts": [
  {"post_id": "<the id, verbatim>", "phrases": ["<phrase 1>", "<phrase 2>", "<phrase 3>"]},
  {"post_id": "<id>", "phrases": []}
]}
```
One entry per input post, **every post_id included even with an empty list**. Phrases 2-4 words each.
