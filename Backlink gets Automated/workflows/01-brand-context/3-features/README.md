# 3-features — how to run

Runnable twin of `features.workflow.md` (Appendix A, the consolidation method and the mapping table are
lifted verbatim from it at runtime).

```bash
cd workflows/01-brand-context/3-features
COMPANY=<slug> python3 scripts/run_features.py    # resumable; --redo to rediscover
```

Deviations from the recipe's letter, by design (2026-07-19):
- Step 1's URL-chunk sub-agents are replaced by the classified commercial types + the recipe's URL signals
  (the recipe predates the catalogue's Type column). Big kinds are capped per kind by traffic (FT_KIND_CAP,
  default 25) — a 3,600-page test library is near-duplicate templates; a traffic-ranked sample carries the facts.
- No live-fetching for pricing/integrations: the new catalogue's keep-everything extraction retains those
  tables (the old extractor stripped them — that reason is gone).

Output: `brand-context/_drafts/features-draft.md` — never the real `features.md`.
