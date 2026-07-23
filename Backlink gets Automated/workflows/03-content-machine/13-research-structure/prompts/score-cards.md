You are curating research "cards" for ONE blog article. Judge each card ONLY by usefulness to THIS article's
reader, and whether it must be protected from deletion. Read the card TEXT, not just its topic.

THE READER (judge every card through THIS person's eyes):
{{PERSONA}}
They are a practitioner making a real decision about what the brand offers — they want to choose, evaluate,
interpret, and use it. They do NOT want the field's academic history or its deep underlying theory.

ARTICLE
- Title: {{ASSET}}
- Distinct angle (what THIS article specifically does): {{ANGLE}}
- Brand (what the reader is deciding about): {{BRAND}}

For EACH card (given as "id | tag | text"), output:
- relevance: integer 0-5 — how directly it helps the reader CHOOSE / EVALUATE / INTERPRET / USE the thing.
  5 = a decision-maker needs it to make or defend a choice (a coefficient / threshold / benchmark; WHICH option
      fits WHICH case; a rule they must follow; a concrete sample / example they can act on).
  3 = useful practical context (how it works in practice; what a type/option actually does; how to pick a vendor).
  1 = general field knowledge the reader wouldn't miss (an academic origin story, a naming debate, light theory).
  0 = off-domain for this reader (the field's HISTORY, off-topic/unrelated uses, pure academic theory or math,
      scholarly debates).
- protected: true ONLY if the card carries HARD data the article promises — a number / % / coefficient /
  threshold / statistic, OR a concrete sample/example item, OR it ties a SPECIFIC named option to a case or
  outcome. Otherwise false. (Do NOT mark protected just because it contains a year like 1884.)
- reason: one short line.

Return STRICT JSON, nothing else:
{"scores":[{"id":1,"relevance":0,"protected":false,"reason":"..."}]}

CARDS
{{CARDS}}
