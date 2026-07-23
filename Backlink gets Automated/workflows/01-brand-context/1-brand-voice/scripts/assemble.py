#!/usr/bin/env python3
"""Step 2 — assemble brand-voice.md from the evidence table (the recipe's pure-assembly step).

Reads:  WORK/evidence.json + Appendix A (the schema, pulled live from the recipe MD so the recipe stays
        the single source of truth) + the company record.
Writes: DRAFT_MD (brand-voice-draft.md). NEVER the real brand-voice.md — promotion is the human gate.
        Also WORK/oneliner-draft.json: the machine's DRAFT of brand_oneliner + niche_definition for the
        human to confirm into company.json (revamp plan 1.1 — drafted by the machine, confirmed by the human).
"""
import json, os, re
import config, llm


def _mapping():
    """The recipe's Step-2 'Fill this section <- pull this column / How to write it' table, lifted
    VERBATIM from the recipe MD (F1: the recipe owns the writing instructions; a paraphrase drifts —
    measured 2026-07-19: the paraphrased prompt dropped 'multi-paragraph', 'short label')."""
    text = open(config.RECIPE_MD, encoding="utf-8").read()
    m = re.search(r"(\| Fill this section \|.*?)\n\n\*\*Output:\*\*", text, re.S)
    if not m:
        raise SystemExit("!! could not find the Step-2 mapping table in the recipe MD")
    return m.group(1)


def _schema():
    """Appendix A's fenced skeleton, lifted from the recipe MD (F1: one copy, owned by the recipe)."""
    text = open(config.RECIPE_MD, encoding="utf-8").read()
    m = re.search(r"# Appendix A[^\n]*\n.*?```markdown\n(.*?)```", text, re.S)
    if not m:
        raise SystemExit("!! could not find Appendix A's ```markdown block in the recipe MD")
    return m.group(1)


def _evidence_block(rows):
    out = []
    for r in rows:
        out.append(f"### {r.get('page','')} · {r.get('url','')}" + ("  [THIN PAGE — weigh lightly]" if r.get("thin") else ""))
        for k, label in [("voice_tone", "Voice & tone"), ("positioning", "Positioning"),
                         ("audience_pain", "Audience & pain"), ("quotable", "Quotable (verbatim)"),
                         ("style_format_cta", "Style · format · CTA"), ("company_dimension", "Company dimension")]:
            v = (r.get(k) or "").strip()
            if v:
                out.append(f"- {label}: {v}")
        out.append("")
    return "\n".join(out)


def run(redo_notes=""):
    rows = json.load(open(os.path.join(config.WORK, "evidence.json")))
    prompt = (llm.load_prompt("assemble-voice.md")
              .replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
              .replace("{{ONELINER}}", config.TENANT.get("brand_oneliner", ""))
              .replace("{{SCHEMA}}", _schema())
              .replace("{{MAPPING}}", _mapping())
              .replace("{{EVIDENCE}}", _evidence_block(rows))
              .replace("{{REDO_NOTES}}",
                       f"\nREDO NOTES from the last quality gate (fix these specifically):\n{redo_notes}\n" if redo_notes else ""))
    draft = llm.call_text(prompt)
    if draft.startswith("```"):                       # a fence around the whole doc sneaks in sometimes
        draft = re.sub(r"^```[a-z]*\n|\n```$", "", draft.strip())
    config.write_text(config.DRAFT_MD, draft)
    print(f"   draft -> {config.DRAFT_MD} ({len(draft.split())} words)")

    # the one-liner/niche DRAFT (only on the first assembly — it reads the same evidence)
    one_path = os.path.join(config.WORK, "oneliner-draft.json")
    if not os.path.exists(one_path):
        one = llm.call_json(llm.load_prompt("draft-oneliner.md")
                            .replace("{{BRAND}}", config.BRAND)
                            .replace("{{EVIDENCE}}", _evidence_block(rows)[:20000]))
        config.write_json(one_path, one)
        print(f"   one-liner + niche DRAFT (confirm into company.json at the gate) -> {one_path}")
    return config.DRAFT_MD


if __name__ == "__main__":
    run()
