# 0-brand-facts — how to run

The brand-facts intake builder: instantiates `stats.md` / `opinions.md` / `stories.md` for a company and
machine-drafts the stats + stories its own website already publishes. Human confirms at the gate.
Full recipe: `0-brand-facts-plan.md`.

## Run (at its SKILL.md stage — Layer 01, step 0; Layer 00's catalogue must exist)

```bash
cd workflows/01-brand-context/0-brand-facts
COMPANY=<slug> python3 scripts/run_brand_facts.py            # resumable; --redo-drafts to rebuild drafts
```

## File map

| File | What it is |
|---|---|
| `templates/stats.md` · `opinions.md` · `stories.md` | the generalized templates ({{BRAND}}/{{NICHE}} slots) |
| `scripts/config.py` | every path + tunable (BF_STAT_TYPES, BF_STORY_TYPES, BF_STAT_TOP, BF_WORKERS) |
| `scripts/llm.py` | the shared headless-CLI caller (claude \| codex via LLM_PROVIDER) |
| `scripts/instantiate.py` | step 1 — templates → brand-context/ (existing files = SEED, never overwritten) |
| `scripts/draft_stats.py` | step 2 — catalogue → `_drafts/stats-draft.md` (⚠️ + source URL per row) |
| `scripts/draft_stories.py` | step 3 — catalogue → `_drafts/stories-draft.md` (⚠️ per entry) |
| `scripts/run_brand_facts.py` | the orchestrator (pure sequencing) |
| `prompts/extract-stats.md` · `extract-stories.md` | one prompt file per LLM call |

Output lands in `projects/<company>/01-brand-context/` (+ `_drafts/`), never in this folder.
