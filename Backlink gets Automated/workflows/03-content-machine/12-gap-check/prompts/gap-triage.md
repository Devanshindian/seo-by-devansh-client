You are triaging gaps in a research dossier and deciding how to spend a STRICTLY LIMITED number of
follow-up research runs.

Respect this:
- Each follow-up is one run of STORM — a deep research engine that takes a broad research question,
  interviews itself from several angles, and scrapes the open web for grounded evidence.
- You get AT MOST 3 follow-up runs, and FEWER IS BETTER. Treat them as precious. Two good runs beat
  three mediocre ones. Zero is a valid, good answer if nothing important is genuinely missing.

You are given:
1. THE ASSET — the article's title and its distinct angle. This tells you what matters most.
2. THE MISSING / THIN ITEMS — the brief items a coverage judge marked "no" (missing) or "partial"
   (too thin), each with its type and the judge's reason.

Do this, in order:
1. DECIDE which misses are actually worth filling. Drop a miss if it is minor, or if it's really a
   rewording of another miss you're already covering. Not every gap deserves a run.
2. PRIORITISE what remains, filling the most important first:
     (a) gap_we_own  — the article's differentiator, the reason it beats the competition.
         A miss here almost always earns a run.
     (b) in_body / secondary_kw that anchor a whole section of the article.
     (c) winner_h2   — table-stakes subtopics every competitor has.
     (d) paa / aio_subtopic / aeo_faq — answer-level gaps.
3. CLUSTER the chosen misses into AT MOST 3 comprehensive research questions. Group related misses into
   one question — never one question per keyword. Each question must be a broad, well-formed research
   topic (a full sentence or rich phrase STORM can build interviews around), NOT a bare keyword.

If nothing clears the bar of "genuinely important AND genuinely uncovered", return an empty list.
Do NOT invent work to use up the runs.

Output STRICT JSON, nothing else. No markdown, no commentary:
{
  "queries": [
    {
      "query": "<the comprehensive research question for STORM>",
      "fills": ["<item text it covers, copied exactly from the items below>", "..."],
      "why":   "<one line: why this is worth one of the limited runs>"
    }
  ]
}
(Return {"queries": []} if nothing is worth a run.)

--- ASSET ---
title: {{ASSET_TITLE}}
distinct angle: {{DISTINCT_ANGLE}}

--- MISSING / THIN ITEMS ---
{{NO_AND_PARTIAL_ITEMS}}
