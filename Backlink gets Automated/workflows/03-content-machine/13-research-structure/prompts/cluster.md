You are grouping "cards" (small research ideas) into the sections of ONE article. Each card belongs to exactly
ONE cluster. Group by MEANING: cards about the same subtopic go together, even when they come from different
sources or use different words.

You are given cards as "id: gloss" lines. Produce clusters that are:
- COMPLETE — every card id is placed in exactly one cluster (do not leave any card out).
- NON-OVERLAPPING — no card id appears in two clusters.
- COHERENT — each cluster is one clear subtopic that could be a section of the article.

Aim for a sensible number of clusters (roughly 8-18 for a large set); merge near-duplicate subtopics into one
cluster. Mark `is_differentiator: true` when a cluster is mainly our unique angle or a gap competitors don't cover.

Output STRICT JSON, nothing else:
{ "clusters": [ { "label": "<short subtopic label>", "card_ids": [1, 2, 3], "is_differentiator": false } ] }

--- CARDS (id: gloss) ---
{{CARDS}}
