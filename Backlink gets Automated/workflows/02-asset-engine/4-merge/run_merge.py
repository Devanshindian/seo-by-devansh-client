#!/usr/bin/env python3
"""run_merge.py — THE ORCHESTRATOR for the cross-method merge. Clubs M1 + M2 + M3 into one deduped sheet.

Two steps: STACK (map the three pools into one schema) -> DEDUP (merge the ideas that repeat across methods,
recording which methods found each). Output: clubbed-ideas.csv, which the research phase reads directly.
Reuse-check (Method 5) runs AFTER this, on the merged sheet.

    COMPANY=<slug> python run_merge.py --company <slug>
"""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "scripts")

STEPS = [
    ("1 stack", "step_1_stack.py", "_work/stacked.json"),
    ("2 dedup", "step_2_dedup.py", "output/clubbed-ideas.csv"),
    # Step 3 runs in PROPOSE mode here (writes the drop list, changes nothing). It is a GATED step: review
    # _work/relevance-drops.json, then apply the approved drops with `step_3_relevance.py --apply`.
    ("3 relevance", "step_3_relevance.py", "_work/relevance-drops.json"),
]


def main():
    ap = argparse.ArgumentParser(description="Merge the 3 method pools into clubbed-ideas.csv.")
    ap.add_argument("--company", default=os.environ.get("COMPANY", ""))
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--from", dest="from_step", default="")
    args = ap.parse_args()
    if not args.company:
        sys.exit("!! --company is required (or set COMPANY).")

    repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    base = os.path.join(repo_root, "projects", args.company, "02-asset-engine", "clubbed")
    env = dict(os.environ, COMPANY=args.company)
    labels = [s[0].split()[0] for s in STEPS]
    from_idx = labels.index(args.from_step) if args.from_step in labels else -1

    print(f"== merge pools :: {args.company} ==")
    for i, (label, script, marker) in enumerate(STEPS):
        force = args.redo or (from_idx >= 0 and i >= from_idx)
        if marker and os.path.exists(os.path.join(base, marker)) and not force:
            print(f"== {label:8s} — cached (skip) =="); continue
        print(f"== {label:8s} — running ==", flush=True)
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + (["--redo"] if force else []), env=env)
        if r.returncode != 0:
            sys.exit(f"!! {label} failed (exit {r.returncode}).")
    print(f"\n== DONE :: {args.company} — merged pool at "
          f"projects/{args.company}/02-asset-engine/clubbed/output/clubbed-ideas.csv ==")
    print("   NOTE: relevance recheck ran in PROPOSE mode — review _work/relevance-drops.json, then apply the")
    print("   approved drops with:  COMPANY=%s python scripts/step_3_relevance.py --apply" % args.company)


if __name__ == "__main__":
    main()
