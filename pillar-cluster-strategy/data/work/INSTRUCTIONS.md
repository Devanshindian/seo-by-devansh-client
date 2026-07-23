# Subagent task — fine-grained pillar/cluster grouping

You are grouping Testlify blog posts into **tight topic clusters** for an SEO pillar/cluster strategy.

## Input
Your slice file is a tab-separated list: `index <TAB> slug`. **The slug IS the article title in URL form** — read it as the title (e.g. `top-9-benefits-of-skills-mapping` = "Top 9 Benefits of Skills Mapping"). The first line `# coarse-theme:` is just context for where this slice came from.

## What a cluster is (the core test)
A cluster = a set of posts that a reader and Google would see as **one focused sub-topic**, such that they could **all be linked from a single pillar hub article without feeling random or padded.**

Ask for each group: *"If I wrote ONE hub article on topic X, would linking to all these posts feel natural and on-topic?"* If yes → cluster. If a post only loosely relates → it does not belong.

## Hard rules
1. **Cap = 15 spokes per cluster.** If a natural topic has more than 15 posts, SPLIT it into more specific pillars (e.g. by role family, by sub-angle, by seniority, by industry). Never exceed 15.
2. **Minimum = 3 spokes** for a cluster to exist. A topic with only 1–2 posts goes to `orphans`.
3. **Name each pillar like a real hub article / topic**, specific not vague. Good: "React & Frontend Developer Interview Questions", "DISC & Personality Assessments", "Reducing Time-to-Hire". Bad: "Assessments", "Hiring stuff", "General".
4. **Use only slugs from your file. Never invent a slug.** Every slug must land in exactly one cluster OR in `orphans` — nothing dropped, nothing duplicated.
5. Prefer **more, tighter clusters** over fewer broad ones. It is fine to produce many small clusters. Precision over coverage.

## Output
Write a JSON file to `data/fine/<slice_id>.json` (slice_id is your filename without extension, e.g. `w07`). Shape:

```json
{
  "slice_id": "w07",
  "clusters": [
    {
      "pillar": "Reducing Time-to-Hire",
      "intent": "informational",
      "spokes": ["how-to-reduce-the-time-to-hire", "make-faster-hiring-decisions-with-real-time-analytics"]
    }
  ],
  "orphans": ["some-one-off-slug"]
}
```

`intent` = one of `informational`, `commercial`, `comparison`, `mixed`.

After writing the file, reply with ONE line: `<slice_id>: N clusters, M orphans`. Do not paste the JSON back.

## Sanity check before writing
- Count: total spokes across all clusters + orphans MUST equal the number of slugs in your file.
- No cluster > 15 spokes. No cluster < 3 spokes (those become orphans).
