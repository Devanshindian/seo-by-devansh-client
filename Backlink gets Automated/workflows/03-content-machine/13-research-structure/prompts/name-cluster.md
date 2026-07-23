You are turning ONE cluster of research cards into a section of an article: a working H2 label, plus H3
sub-sections if the cluster covers several distinct sub-points.

You are given the cluster's cards as "id: gloss" lines.

Do this:
- Write a working H2 label — a plain, descriptive heading. It is a DRAFT, not final polished wording (final
  wording is decided later by the writer). Phrase it as a question if the subtopic is naturally a question.
- If the cluster clearly splits into 2+ distinct sub-points, create H3s and assign EACH card id to exactly one
  H3. If the cluster is one tight idea, use no H3s and list all card ids directly under the H2.
- Every card id you were given must appear exactly once — either directly under the H2 or under one H3.

Output STRICT JSON, nothing else:
{
  "h2": "<working H2 label>",
  "h3": [ { "h3": "<working H3 label>", "card_ids": [1, 2] } ],
  "card_ids": [3, 4]
}
(`h3` is [] if there's no split; `card_ids` is the cards that sit directly under the H2.)

--- CLUSTER CARDS (id: gloss) ---
{{CARDS}}
