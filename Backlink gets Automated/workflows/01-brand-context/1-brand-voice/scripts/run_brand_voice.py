#!/usr/bin/env python3
"""1-brand-voice orchestrator — pure sequencing, resumable. The runnable twin of brand-voice.workflow.md.

  COMPANY=<slug> python3 run_brand_voice.py [--redo-evidence] [--redo-draft]

Step 0  shortlist the voice pages  (skipped if page-shortlist.md exists — a curated shortlist is input)
Step 1  read each page -> evidence row   (resumable per page)
Step 2  assemble the draft from the evidence (pure assembly per the recipe's mapping)
Step 3  quality gate vs the recipe's bar; FAIL -> back to Step 2 with redo notes (max GATE_MAX_ROUNDS)
THE GATE (human): compare _drafts/brand-voice-draft.md against the current brand-voice.md; the loop only
breaks when the draft matches the current file's quality — then promote it BY HAND (the engine never
writes brand-voice.md). Also confirm _work/brand-voice/oneliner-draft.json into company.json.
"""
import argparse, os, sys
import config
import shortlist, read_pages, assemble, quality_gate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo-evidence", action="store_true", help="re-read every page (drop the evidence cache)")
    ap.add_argument("--redo-draft", action="store_true", help="re-assemble even if a draft exists")
    a = ap.parse_args()

    if not os.path.exists(config.CATALOGUE_CSV):
        sys.exit(f"!! no site catalogue at {config.CATALOGUE_CSV} — run Layer 00 (site-catalogue) first")

    print(f"company: {config.COMPANY} ({config.BRAND})")
    print("== Step 0: shortlist ==")
    shortlist.run()

    print("== Step 1: read pages -> evidence ==")
    ev = os.path.join(config.WORK, "evidence.json")
    if a.redo_evidence and os.path.exists(ev):
        os.remove(ev)
    read_pages.run()

    print("== Step 2+3: assemble <-> quality gate ==")
    if os.path.exists(config.DRAFT_MD) and not a.redo_draft:
        print(f"   draft exists -> {config.DRAFT_MD} (use --redo-draft to rebuild); running the gate on it")
    else:
        assemble.run()
    for round_n in range(1, config.GATE_MAX_ROUNDS + 1):
        verdict = quality_gate.run(round_n)
        if verdict.get("overall_pass"):
            break
        if round_n == config.GATE_MAX_ROUNDS:
            print(f"   !! still failing after {round_n} rounds — the draft ships with its gate verdict; decide at the human gate")
            break
        assemble.run(redo_notes=verdict.get("redo_notes", ""))

    print("== WRITTEN IN PLACE ==")
    print(f"   {os.path.relpath(config.DRAFT_MD, config.REPO_ROOT)} — review with `git diff`; confirm oneliner-draft.json into company.json.")


if __name__ == "__main__":
    main()
