# 4-writing-examples — how to run

Runnable twin of `writing-examples.workflow.md`. Pool + Traffic + Top Keyword from `top-pages.csv` (as-is,
never recomputed); bodies from the catalogue (no web-fetch — everything is already on disk); voice scored
per article against `brand-voice.md` only; rounds continue until 5 on-voice articles survive.

```bash
cd workflows/01-brand-context/4-writing-examples
COMPANY=<slug> python3 scripts/run_writing_examples.py    # --redo to rescore
```

Output: `brand-context/_drafts/writing-examples-draft.md` — never the real file.
