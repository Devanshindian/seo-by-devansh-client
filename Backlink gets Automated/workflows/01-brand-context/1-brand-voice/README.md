# 1-brand-voice — how to run

The brand-voice engine: shortlists the company's voice pages, reads each into an evidence row, assembles
`brand-voice.md` from the evidence (pure assembly), and quality-gates the draft against the recipe's bar.
**The recipe is `brand-voice.workflow.md`** (the schema in Appendix A and the Castos depth bar in Appendix B
live there — the scripts read Appendix A from it, so the recipe stays the single source of truth).

## Run (at its SKILL.md stage — Layer 01, step 1; Layer 00's catalogue must exist)

```bash
cd workflows/01-brand-context/1-brand-voice
COMPANY=<slug> python3 scripts/run_brand_voice.py     # resumable; --redo-evidence / --redo-draft to force
```

The engine writes `_drafts/brand-voice-draft.md` — it NEVER touches the real `brand-voice.md`.
Promotion is the human gate: compare the draft against the current file; promote by hand when it matches.

## File map

| File | What it is |
|---|---|
| `brand-voice.workflow.md` | THE RECIPE — steps, schema (Appendix A), depth bar (Appendix B) |
| `scripts/config.py` | every path + tunable (BV_CAND_TOP, BV_WORKERS, BV_GATE_ROUNDS…) |
| `scripts/llm.py` | the shared headless-CLI caller (+ `call_text` for whole-document output) |
| `scripts/shortlist.py` | step 0 — candidates from the catalogue (script) · the pick (LLM) · bodies saved from `Full content` (no refetch) |
| `scripts/read_pages.py` | step 1 — one evidence row per page (LLM per page, resumable, thin-page fallback) |
| `scripts/assemble.py` | step 2 — the draft from the evidence (LLM, pure assembly) + the oneliner/niche draft |
| `scripts/quality_gate.py` | step 3 — completeness/depth/specificity judge + a code check for leftover placeholders |
| `scripts/run_brand_voice.py` | the orchestrator (assemble<->gate loop, capped) |
| `prompts/pick-pages.md` · `extract-evidence.md` · `assemble-voice.md` · `quality-gate.md` · `draft-oneliner.md` | one file per LLM call |

Output lands in `projects/<company>/01-brand-context/` (+ `_drafts/`, `_work/brand-voice/`),
never in this folder.
