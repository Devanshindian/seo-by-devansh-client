#!/usr/bin/env python3
"""Step 3 — the quality gate (the recipe's completeness/depth/specificity check, as an LLM judge).

Reads:  DRAFT_MD. The judge sees the full bar in prompts/quality-gate.md (J2: criteria in the prompt);
        code adds the one check an LLM can miss: leftover [BRACKET] placeholders.
Writes: WORK/gate-round-<n>.json (verdict per section + consolidated redo notes).
"""
import json, os, re
import config, llm


def run(round_n):
    draft = open(config.DRAFT_MD, encoding="utf-8").read()
    verdict = llm.call_json(llm.load_prompt("quality-gate.md")
                            .replace("{{BRAND}}", config.BRAND)
                            .replace("{{DRAFT}}", draft))
    # the deterministic check code owns: no [BRACKET] placeholder may survive (Appendix A's own rule)
    leftovers = [b for b in re.findall(r"\[[A-Z][A-Z /·&-]{2,}\]", draft)
                 if b not in ("[BRACKET]",)]
    if leftovers:
        verdict["overall_pass"] = False
        verdict["redo_notes"] = (verdict.get("redo_notes", "") +
                                 f"\nUnfilled placeholders survive: {', '.join(set(leftovers))} — fill every one.")
    out = os.path.join(config.WORK, f"gate-round-{round_n}.json")
    config.write_json(out, verdict)
    n_fail = sum(1 for s in verdict.get("sections", []) if not s.get("pass"))
    print(f"   gate round {round_n}: overall {'PASS' if verdict.get('overall_pass') else 'FAIL'} "
          f"({n_fail} failing sections{', placeholders left' if leftovers else ''})")
    return verdict


if __name__ == "__main__":
    run(0)
