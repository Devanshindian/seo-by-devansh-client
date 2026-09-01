You are building evidence cards for ONE sub-topic (an H3) of an article, from freshly scraped web pages.

THE COMPANY publishing this article: {{BRAND}} — {{ABOUT}}
THE ARTICLE: {{TITLE}} — distinct angle: {{ANGLE}}
THE SECTION this belongs to: {{SECTION_HEADLINE}}
The section flagged this H3 as a research need. The H3 stays EXACTLY as written — you are filling it,
not renaming it:
H3: {{H3}}

THE SCRAPED PAGES (each labelled with its link; top slice of the article text):
{{PAGES}}

────────────────────────────────────────────────────────────────────────
THE CARD IS ALL THE WRITER WILL EVER SEE.

Your cards go straight to the writer of this article, exactly as you write them. That writer CANNOT
open the source link, CANNOT search the web, and CANNOT see the page you are reading now. If a fact
is not written inside the card, it does not exist as far as this article is concerned.

So every card has to stand completely on its own:
- THE ACTUAL NUMBER, never a promise of one. "The report gives an average cost per hire" is worth
  nothing. "The average cost per hire was $4,700" is the card.
- WHO SAID IT, AND WHEN. Name the publisher and the year inside the card, so the writer can credit
  the source in a sentence without looking anything up.
- WHAT IT COVERS. A figure means little without its scope — the sample size, the country, the
  industry, the period it measures. Where the page states it, the card carries it.
- NO POINTERS. Never write "see the source", "as detailed in the report", "the full methodology is
  available there". The writer cannot follow any of those.

One downstream rule makes this unforgiving: the writer is FORBIDDEN from writing a vague quantity
when its card does not hold the specific one, and is told to drop the claim instead. So a card that
gestures at a number does not produce a woolly sentence — it loses the fact altogether, after we
have already paid to go and find it.
────────────────────────────────────────────────────────────────────────

Create as many cards as the material honestly supports. The rules:
- Build ONLY from what these pages actually say — never your own knowledge, never fabricated.
  Joining and phrasing is fine; inventing is not.
- A card summarizes material from ONE page only. NO cross-page summarization — never blend two
  sources into one card. Multiple cards from the same page are fine.
- Each card: "gloss" (a one-line summary of the fact), "summary" (the card's content — a faithful
  summary of that page's relevant material, with the concrete numbers kept), "source_url" (that
  page's link, exactly as labelled above).
- If the pages turned up nothing genuinely useful for this H3, return an empty list. Never force
  weak cards.

Return ONLY this JSON, nothing else:
{"cards": [{"gloss": "...", "summary": "...", "source_url": "..."}]}
