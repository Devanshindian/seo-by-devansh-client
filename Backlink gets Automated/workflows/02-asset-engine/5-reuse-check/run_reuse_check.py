#!/usr/bin/env python3
"""run_reuse_check.py — THE ORCHESTRATOR for the reuse check (Method 5). Fills the 6 reuse columns of
clubbed-ideas.csv: RAG candidates / Topic pages we own / Reference links (Stage 2), then Reuse verdict /
Chosen links / Why (Stage 3). Runs AFTER 4-merge, on the merged sheet.

Two steps: RETRIEVE (build/load the two-vector index, blended retrieve -> rerank-2.5, topic catalogue) ->
JUDGE (parallel LLM verdict per idea, reading candidate text fetched on demand). Pure sequencing.
Resumable: the clubbed CSV is edited in place, so each step drops a _work sentinel; a done step is skipped
unless --redo (all) or --from <step> forces it. Both steps are also internally resumable (index state,
per-idea RAG cells, judge jsonl), so a crash resumes without repeating paid work.

    COMPANY=<slug> python run_reuse_check.py --company <slug>
"""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "scripts")

STEPS = [
    ("1 retrieve", "step_1_retrieve.py", os.path.join("_work", ".stage2-retrieved.done")),
    ("2 judge",    "step_2_judge.py",    os.path.join("_work", ".stage3-judged.done")),
]


def main():
    ap = argparse.ArgumentParser(description="Reuse check: fill the clubbed sheet's reuse columns (RAG + verdict).")
    ap.add_argument("--company", default=os.environ.get("COMPANY", ""))
    ap.add_argument("--redo", action="store_true", help="force both steps (re-retrieve + re-judge)")
    ap.add_argument("--reindex", action="store_true", help="also rebuild the content index (content changed)")
    ap.add_argument("--from", dest="from_step", default="", help="run from this step onward (e.g. '2')")
    args = ap.parse_args()
    if not args.company:
        sys.exit("!! --company is required (or set COMPANY).")

    repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    base = os.path.join(repo_root, "projects", args.company, "02-asset-engine", "clubbed")
    env = dict(os.environ, COMPANY=args.company)
    labels = [s[0].split()[0] for s in STEPS]
    from_idx = labels.index(args.from_step) if args.from_step in labels else -1

    print(f"== reuse check :: {args.company} ==")
    for i, (label, script, marker) in enumerate(STEPS):
        force = args.redo or (from_idx >= 0 and i >= from_idx)
        if marker and os.path.exists(os.path.join(base, marker)) and not force:
            print(f"== {label:11s} — cached (skip) =="); continue
        print(f"== {label:11s} — running ==", flush=True)
        extra = (["--redo"] if force else [])
        if script == "step_1_retrieve.py" and args.reindex:
            extra.append("--reindex")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + extra, env=env)
        if r.returncode != 0:
            sys.exit(f"!! {label} failed (exit {r.returncode}).")
    print(f"\n== DONE :: {args.company} — reuse columns filled in "
          f"projects/{args.company}/02-asset-engine/clubbed/output/clubbed-ideas.csv ==")


if __name__ == "__main__":
    main()
