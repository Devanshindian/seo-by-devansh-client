#!/usr/bin/env python3
"""run_model_niches.py — THE ORCHESTRATOR for Method 2 (Model Other Niches). One command, steps A -> E.

Pure sequencing (C4): calls each step's run() in order, nothing else. Each step is a subprocess so config
isolation matches the competitor-study engine. RESUMABLE: a step whose output file exists is skipped unless
--redo (all) or --from <STEP> (that step onward) forces it.

No human gates here (Method 2 is fully agent-doable — no API, no user-in-tool). No paid API. The only inputs
are brand-scope.md (Method 1 / G0) + the brand context, all already on disk.

    COMPANY=<slug> python run_model_niches.py --company <slug>
"""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "scripts")

# (label, script, output-marker-relative-to-model-other-niches-dir)
STEPS = [
    ("A  swipe library", "step_a_swipe.py",   "_work/swipe.json"),
    ("B  adapt formats",  "step_b_adapt.py",   "_work/adaptations.json"),
    ("C  filter (gate)",  "step_c_filter.py",  "_work/filtered.json"),
    ("D  score",          "step_d_score.py",   "_work/scored.json"),
    ("E  deliver",        "step_e_deliver.py", "output/model-other-niches-ideas.csv"),
]


def _dir(company, repo_root):
    return os.path.join(repo_root, "projects", company, "02-asset-engine", "model-other-niches")


def main():
    ap = argparse.ArgumentParser(description="Run Method 2 (model other niches) end to end, A -> E.")
    ap.add_argument("--company", default=os.environ.get("COMPANY", ""), help="company slug (or COMPANY env)")
    ap.add_argument("--redo", action="store_true", help="force every step to re-run")
    ap.add_argument("--from", dest="from_step", default="", help="force from this step onward (e.g. C)")
    args = ap.parse_args()
    if not args.company:
        sys.exit("!! --company is required (or set COMPANY).")

    repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    base = _dir(args.company, repo_root)
    env = dict(os.environ, COMPANY=args.company)
    labels = [s[0].split()[0] for s in STEPS]
    from_idx = labels.index(args.from_step) if args.from_step in labels else -1

    print(f"== model other niches :: {args.company} ==")
    for i, (label, script, marker) in enumerate(STEPS):
        force = args.redo or (from_idx >= 0 and i >= from_idx)
        marker_path = os.path.join(base, marker)
        if os.path.exists(marker_path) and not force:
            print(f"== {label:18s} — cached (skip) ==")
            continue
        cmd = [sys.executable, os.path.join(SCRIPTS, script)] + (["--redo"] if force else [])
        print(f"== {label:18s} — running ==", flush=True)
        r = subprocess.run(cmd, env=env)
        if r.returncode != 0:
            sys.exit(f"!! {label} failed (exit {r.returncode}). Fix it, then re-run — finished steps are cached.")
    print(f"\n== DONE :: {args.company} — deliverable at "
          f"projects/{args.company}/02-asset-engine/model-other-niches/output/model-other-niches-ideas.csv ==")


if __name__ == "__main__":
    main()
