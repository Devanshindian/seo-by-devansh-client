# 5-persona — how to run
Runnable twin of `persona.workflow.md` — one LLM call with the recipe's exact prompt (lifted verbatim),
reading brand-voice.md's Audience section. Output: `_drafts/persona-draft.md`; the recipe's Step-3 human
gate IS the promotion.
```bash
COMPANY=<slug> python3 scripts/run_persona.py
```
