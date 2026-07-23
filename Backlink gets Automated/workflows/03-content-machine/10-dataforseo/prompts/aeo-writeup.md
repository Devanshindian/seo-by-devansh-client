Judge the llm_mentions results for this article and write the "AI answer landscape" section. Keep ONLY what's
about our topic — Step 6 stands alone and never borrows from other steps.

- Primary keyword: {{PRIMARY_KEYWORD}}
- Topic (correct meaning): {{DISTINCT_ANGLE}}
- Brand to check for citation: {{BRAND}}
- llm_mentions returned (JSON): questions {{QUESTIONS}}; fan-out {{FAN_OUT}}; cited domains {{CITED_DOMAINS}};
  brand cited? {{BRAND_CITED}}
- Attempt log (if the query gate stopped without a usable pull): {{ATTEMPTS}}

Judge each question/fan-out against the topic: on-topic, or a wrong meaning of the keyword?
- If MOST are off-topic (or there was no usable pull at all) → report this method produced nothing usable. Do NOT
  invent or borrow content. Use the "no usable signal" shape.
- If on-topic → keep the relevant questions as FAQ candidates; note cited domains + whether the brand is among them.

RETURN markdown, ONE item per line.

If USABLE:
### AI answer landscape — {{PRIMARY_KEYWORD}}
- Status: usable
- {{BRAND}} cited by AI assistants? No — GEO gap, open to own. / Yes
- Who AI cites:
  - <domain>
  - <domain>
- FAQ candidates:
  - <on-topic question, verbatim>
  - <question>
- Raw: `<run_dir>/proof/06-aeo.json`

If NO USABLE SIGNAL:
### AI answer landscape — {{PRIMARY_KEYWORD}}
- Status: no usable signal — llm_mentions drifted off-topic on every query tried (<one clause naming what it drifted to>). The corpus lacks this topic; this method added nothing.
- Raw: `<run_dir>/proof/06-aeo.json` (attempt log: `06a-query.json`)
