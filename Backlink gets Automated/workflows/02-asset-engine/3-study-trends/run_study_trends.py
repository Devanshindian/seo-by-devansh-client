#!/usr/bin/env python3
"""run_study_trends.py — THE ORCHESTRATOR for Method 3 Phase B (mine the scrape into tensions -> ideas).

Phase A (the Reddit scrape) is a separate tool with a human gate (choosing subreddits) — run it first via
scripts/reddit/reddit-scrape.py and save `_raw/<company>-reddit-trends.xlsx`. THIS command runs Phase B:
stages 2a -> 4, then the Stage-5 fail-closed verify gate. No human gate in Phase B (Stage 3 filters
automatically, like Methods 1 & 2).

Pure sequencing (C4). RESUMABLE: a stage whose output exists is skipped unless --redo / --from.

    COMPANY=<slug> python run_study_trends.py --company <slug>
"""
import argparse, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "scripts")

# (label, script, output-marker-relative-to-study-trends-dir)
STEPS = [
    ("2a phrases",  "step_2a_phrases.py", "_work/all-phrases.tsv"),
    ("2b tensions", "step_2b_tensions.py", "_work/tensions_base.json"),
    ("2c assign",   "step_2c_assign.py",  "_work/post-tension-map.tsv"),
    ("2d records",  "step_2d_records.py", "output/tensions.csv"),
    ("3  filter",   "step_3_filter.py",   None),                       # edits tensions.csv in place — always run
    ("4  ideas",    "step_4_ideas.py",    "output/study-trends-ideas.csv"),
]


def _dir(company, repo_root):
    return os.path.join(repo_root, "projects", company, "02-asset-engine", "study-trends")


def main():
    ap = argparse.ArgumentParser(description="Run Method 3 Phase B (study trends) end to end.")
    ap.add_argument("--company", default=os.environ.get("COMPANY", ""))
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--from", dest="from_step", default="", help="force from this stage onward (e.g. 2b)")
    args = ap.parse_args()
    if not args.company:
        sys.exit("!! --company is required (or set COMPANY).")

    repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    base = _dir(args.company, repo_root)
    env = dict(os.environ, COMPANY=args.company)
    labels = [s[0].split()[0] for s in STEPS]
    from_idx = labels.index(args.from_step) if args.from_step in labels else -1

    scrape = os.path.join(base, "_raw", f"{args.company}-reddit-trends.xlsx")
    if not os.path.exists(scrape):
        sys.exit(f"!! no scrape at {scrape}\n   Run Phase A first (scripts/reddit/reddit-scrape.py) — that has the subreddit human gate.")

    print(f"== study trends (Phase B) :: {args.company} ==")
    for i, (label, script, marker) in enumerate(STEPS):
        force = args.redo or (from_idx >= 0 and i >= from_idx)
        if marker and os.path.exists(os.path.join(base, marker)) and not force:
            print(f"== {label:12s} — cached (skip) ==")
            continue
        print(f"== {label:12s} — running ==", flush=True)
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + (["--redo"] if force else []), env=env)
        if r.returncode != 0:
            sys.exit(f"!! {label} failed (exit {r.returncode}). Fix it, then re-run — finished stages are cached.")

    # Stage 5 — the fail-closed verify gate (script, not self-attestation)
    print(f"== 5  verify     — running (fail-closed gate) ==", flush=True)
    v = subprocess.run([sys.executable, os.path.join(SCRIPTS, "study-trends-verify.py"), base], env=env)
    if v.returncode != 0:
        sys.exit("!! VERIFY: FAIL — the run is NOT done. Fix the flagged gate(s) and re-run the affected stage.")
    print(f"\n== DONE :: {args.company} — deliverable at "
          f"projects/{args.company}/02-asset-engine/study-trends/output/study-trends-ideas.csv ==")


if __name__ == "__main__":
    main()
