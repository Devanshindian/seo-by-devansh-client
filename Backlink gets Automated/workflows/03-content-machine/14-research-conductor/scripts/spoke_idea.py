#!/usr/bin/env python3
"""Turn a bare SPOKE KEYWORD into a real article idea (title + angle) — the raw material a normal idea has
and a spoke was missing. Then it flows through the same checks as any idea (reuse / cannibalisation / write).

mint()  — LLM makes {title, angle} from the keyword + its pillar + brand, with a retry note for iteration.
accept() — the 2-3 iteration loop: mint, check it isn't a near-duplicate of what we already have, re-mint a
           fresher angle if it is, up to N tries. Cannibalisation is a FLAG (handled in the conductor), not a drop.
"""
import config, llm
import reuse_one                                    # the proper semantic reuse check (Voyage index + judge)


def mint(keyword, pillar_asset, pillar_angle, signals="", retry_note=""):
    p = (llm.load_prompt("spoke-idea.md").replace("{{BRAND}}", config.BRAND)
         .replace("{{PILLAR_ASSET}}", pillar_asset or "").replace("{{PILLAR_ANGLE}}", pillar_angle or "")
         .replace("{{KEYWORD}}", keyword or "").replace("{{SIGNALS}}", signals or "decent volume, low difficulty")
         .replace("{{BRAND_ONELINER}}", config.TENANT.get("brand_oneliner", ""))
         .replace("{{NICHE}}", config.TENANT.get("niche_definition", ""))
         .replace("{{RETRY_NOTE}}", retry_note))
    out = llm.call_json(p)
    return {"title": (out.get("title") or "").strip(), "angle": (out.get("angle") or "").strip()}


def accept(keyword, pillar_asset, pillar_angle, signals="", tries=3):
    """Mint an idea; run the PROPER semantic reuse check; if we ALREADY have it, re-angle up to `tries` times.
    Returns {'title','angle','verdict','chosen'} — verdict is the real reuse verdict for the accepted idea
    (Brand new / Build from parts / Improve existing all proceed; only 'Already have it' triggers a re-angle)."""
    note, last = "", None
    for _ in range(max(1, tries)):
        idea = mint(keyword, pillar_asset, pillar_angle, signals, note)
        if not idea["title"]:
            continue
        v = reuse_one.check(idea["title"], idea["angle"]) or {}
        last = {**idea, "verdict": v.get("verdict", ""), "chosen": v.get("chosen", "")}
        if v.get("verdict") != "Already have it":
            return last
        note = (f"\nNOTE: we ALREADY have a page covering this ({v.get('chosen','')}). Find a genuinely different, "
                f"sharper angle on '{keyword}' that we do NOT already cover.")
    # never return None — if every mint came back empty, fall back to the keyword itself so the caller can't crash
    return last or {"title": keyword.strip().title(), "angle": "", "verdict": "", "chosen": ""}


if __name__ == "__main__":
    import sys, json
    kw = sys.argv[1] if len(sys.argv) > 1 else "benchmarking"
    print(json.dumps(accept(kw, "Testlify State of Skills-Based Hiring 2026",
                            "Original benchmark data on skills-based hiring adoption"), indent=2))
