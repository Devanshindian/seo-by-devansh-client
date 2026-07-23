#!/usr/bin/env python3
"""5-persona orchestrator — the runnable twin of persona.workflow.md.

  COMPANY=<slug> python3 run_persona.py

One LLM call: the recipe's EXACT prompt (lifted verbatim from the recipe MD — F1) with brand-voice.md
pasted in -> 3-4 distinct READER personas + the how-to-pick rule -> _drafts/persona-draft.md.
The human gate (recipe Step 3) = the promotion: the user edits/approves the draft, then copies it over
persona.md by hand. The engine never writes the real file.
"""
import json, os, re, sys
import config, llm


def _recipe_prompt():
    text = open(config.RECIPE_MD, encoding="utf-8").read()
    m = re.search(r"\*\*The exact prompt:\*\*\n```\n(.*?)```", text, re.S)
    if not m:
        raise SystemExit("!! could not lift the Step-2 prompt from the recipe MD")
    return m.group(1)


def main():
    voice_p = os.path.join(config.BRAND_CTX, "brand-voice.md")
    if not os.path.exists(voice_p):
        sys.exit("!! no brand-voice.md — build builder 1 first (personas derive from its Audience section)")
    voice = open(voice_p, encoding="utf-8").read()
    print(f"company: {config.COMPANY} ({config.BRAND})")
    print("== Step 1+2: propose personas (the recipe's exact prompt) ==")
    notes = ""
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--notes-file", default=""); a = ap.parse_args()
    if a.notes_file:
        notes = "\n\nREVIEWER FINDINGS — implement each concretely in the personas you return:\n" + open(a.notes_file).read()
    out = llm.call_json(_recipe_prompt().replace("{{BRAND_VOICE}}", voice) + notes)
    personas = out.get("personas", [])
    if not (3 <= len(personas) <= 4):
        print(f"   !! {len(personas)} personas returned (recipe wants 3-4) — review at the gate")

    lines = [f"# {config.BRAND} Reader Personas", "",
             "> A persona is the READER we write TO — never the author byline. Think about the persona;",
             "> NEVER name or address them explicitly in the article. (persona.workflow.md, the one rule)", "",
             "| Persona | Who | Reads | Cares about | Depth & angle | Not this |",
             "|---|---|---|---|---|---|"]
    for p in personas:
        lines.append("| **{name}** | {who} | {reads} | {cares_about} | {depth_and_angle} | {not_this} |".format(
            **{k: str(p.get(k, "")).replace("|", "/") for k in
               ("name", "who", "reads", "cares_about", "depth_and_angle", "not_this")}))
    htp = out.get("how_to_pick", "")
    if not isinstance(htp, str):                     # the model sometimes returns a structured object
        htp = "\n".join(f"- {k}: {v}" for k, v in htp.items()) if isinstance(htp, dict) else "\n".join(map(str, htp))
    lines += ["", "## How to pick the persona for an article", htp, ""]
    config.write_text(config.DRAFT_MD, "\n".join(lines))
    config.write_text(os.path.join(config.WORK, "personas.json"), json.dumps(out, indent=1))
    print(f"   {len(personas)} personas -> {config.DRAFT_MD}")
    print("== WRITTEN IN PLACE: persona.md — recipe Step 3 gate = review/edit it; `git diff` shows the change ==")


if __name__ == "__main__":
    main()
