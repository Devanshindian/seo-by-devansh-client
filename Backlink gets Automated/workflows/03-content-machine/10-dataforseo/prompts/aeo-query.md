Pick the term to search in llm_mentions for this article. (llm_mentions matches a keyword and sorts by volume,
so an AMBIGUOUS word — one whose biggest meaning belongs to a different field than ours — returns the word's
biggest meaning, not ours.)

- Primary keyword: {{PRIMARY_KEYWORD}}
- Topic (the correct meaning): {{DISTINCT_ANGLE}}
- Already tried, don't repeat (JSON list of {query, match_type, result}): {{ATTEMPTS}}

Rules:
1. If the primary keyword is unambiguous, use it as-is (phrase_match first).
2. If one word has a bigger non-topic meaning, swap just that word for a clear synonym, keep the rest
   (form illustration: "recruiting metrics" -> "recruitment metrics"). You may also loosen
   phrase_match -> word_match to get volume.
3. Never repeat a query+match_type pair already in "Already tried".
4. If 3 anchored tries each came back off-topic (or empty), STOP — this method has nothing for this topic.

RETURN JSON only, one of:
  { "query": "...", "match_type": "phrase_match" }
  { "stop": true, "why": "one line — why the corpus has no usable signal for this topic" }
