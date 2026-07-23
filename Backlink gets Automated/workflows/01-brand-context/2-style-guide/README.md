# 2-style-guide — how to run

The runnable twin of `style-guide.workflow.md` (the recipe stays the source of truth — the Step-3
template is lifted verbatim from it at runtime).

```bash
cd workflows/01-brand-context/2-style-guide
COMPANY=<slug> python3 scripts/run_style_guide.py    # resumable; --redo to rebuild
```

Steps: pick top editorial blogs (script, classified types) → analyze in batches (LLM × 3, the recipe's
sub-agents) → fill the template (LLM, verbatim template). Output: `brand-context/_drafts/style-guide-draft.md`
— never the real `style-guide.md`; promotion is the human gate.
