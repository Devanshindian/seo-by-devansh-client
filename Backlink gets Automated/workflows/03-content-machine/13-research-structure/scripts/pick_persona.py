"""Step 1a — pick the ONE reader persona for this asset (from the brand's persona.md), so the angle-filter
(Step 1b) and the write phase target the SAME reader. Single source of truth: the picked persona is written to
persona.json + embedded in the blueprint, and the bundle step REUSES it (never re-picks).

Reads: config.PERSONA_MD + asset + angle. Writes: persona.json {name, lens, why}. Returns the dict.
Brand-agnostic — the persona library is per-company (persona.md); nothing is hardcoded here.
"""
import os, json
import config, llm

TEMPLATE = llm.load_prompt("pick-persona.md")
_FALLBACK = {"name": "", "lens": "a practitioner making a real decision about what the brand offers "
                                 "(choose / evaluate / use it), not an academic", "why": ""}


def run(asset, angle, run_dir):
    out_path = os.path.join(run_dir, "persona.json")
    doc = open(config.PERSONA_MD).read() if os.path.exists(config.PERSONA_MD) else ""
    if not doc:
        persona = {**_FALLBACK, "why": f"persona.md not found at {config.PERSONA_MD}"}
    else:
        prompt = (TEMPLATE.replace("{{BRAND}}", config.BRAND_ONELINER)
                  .replace("{{ASSET_TITLE}}", asset).replace("{{ANGLE}}", angle or "")
                  .replace("{{PERSONA_DOC}}", doc))
        try:
            persona = llm.call_json(prompt) or {}
            if not persona.get("lens"):
                persona = {**_FALLBACK, **persona, "lens": persona.get("lens") or _FALLBACK["lens"]}
        except Exception as e:
            persona = {**_FALLBACK, "why": f"persona pick failed ({str(e)[:80]}) — using generic reader"}
    config.write_json(out_path, persona)
    return persona
