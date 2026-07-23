You are merging provisional subtopic labels into the final sections of ONE article. The labels came from
several batches, so many are duplicates or near-duplicates of the same subtopic.

You are given provisional labels as "index: label" lines. Group the indices that are the SAME (or clearly the
same) subtopic into one final theme. Every index must go into exactly one theme. Aim for roughly 10-18 final
themes for a large article. Mark `is_differentiator: true` when a theme is mainly our unique angle or a gap.

Output STRICT JSON, nothing else:
{ "themes": [ { "label": "<final subtopic label>", "member_indices": [0, 3, 7], "is_differentiator": false } ] }

--- PROVISIONAL LABELS (index: label) ---
{{LABELS}}
