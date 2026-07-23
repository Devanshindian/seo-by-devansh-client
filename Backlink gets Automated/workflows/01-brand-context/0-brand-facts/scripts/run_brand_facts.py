#!/usr/bin/env python3
"""0-brand-facts orchestrator — pure sequencing, resumable. Run at its SKILL.md stage (Layer 01, step 0).

  COMPANY=<slug> python3 run_brand_facts.py [--redo-drafts]

Step 1  instantiate the three templates into brand-context/  (existing files = SEED, never overwritten)
Step 2  machine-draft stats candidates   -> brand-context/stats.md    (⚠️ on every drafted row)
Step 3  machine-draft story candidates   -> brand-context/stories.md  (⚠️ on every drafted entry)
THE GATE (human, not this script): review the drafts; merge confirmed rows into stats.md / stories.md
and drop their ⚠️; answer opinions.md's interview questions. Confirmed files are SEED — preserved forever.
"""
import argparse, os, sys
import config
import instantiate, classify_types, draft_stats, draft_stories


def _already_drafted(name):
    """Has the draft step already filled the REAL file? True once it carries a ⚠️ candidate row.
    (The resume check used to look at the retired _drafts path, so the step was skipped while its
    output sat unused — TestGorilla's stats.md was left as the bare template. Devansh, 2026-07-20.)"""
    p = os.path.join(config.BRAND_CTX, f"{name}.md")
    return os.path.exists(p) and any("⚠️" in ln and ln.strip().startswith(("|", "###"))
                                     for ln in open(p, encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo-drafts", action="store_true", help="rebuild both draft files even if they exist")
    a = ap.parse_args()

    if not os.path.exists(config.CATALOGUE_CSV):
        sys.exit(f"!! no site catalogue at {config.CATALOGUE_CSV} — run Layer 00 (site-catalogue) first")

    print(f"company: {config.COMPANY} ({config.BRAND})")
    print("== Step 0: classify this company's page types ==")
    classify_types.run()

    print("== Step 1: instantiate templates ==")
    instantiate.run()

    for label, step, name in (("Step 2: draft stats", draft_stats, "stats"),
                              ("Step 3: draft stories", draft_stories, "stories")):
        print(f"== {label} from the catalogue ==")
        if _already_drafted(name) and not a.redo_drafts:
            print(f"   done already -> {name}.md carries drafted rows (use --redo-drafts to force)")
        else:
            step.run()

    print("== THE GATE (yours) ==")
    print("   review _drafts/, merge confirmed rows into stats.md / stories.md (drop their ⚠️),")
    print("   and answer opinions.md's interview questions. Confirmed files are SEED.")


if __name__ == "__main__":
    main()
