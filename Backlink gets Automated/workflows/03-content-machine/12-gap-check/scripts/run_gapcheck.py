"""Gap-check orchestrator — one topic, end to end.

  python3 run_gapcheck.py --slug <topic> --brief <research-doc.md> --dossier <polished.txt>

Steps:
  0 read brief   -> coverage-items.json
  1 judge        -> coverage-verdicts.json
  2 triage       -> gap-queries.json
  3 re-run STORM -> projects/testlify/content-machine/storm/out/<Topic>/iteration-<n>/  (fires only if there are gap queries; shim auto-starts)
  4 report       -> gap-check.md
Resumable: each step reuses its existing output; Step 3 skips iterations already completed (so a crash mid-run
resumes instead of re-firing every ~7-min STORM run). `--redo` forces a full rerun.
"""
import os, argparse, json
import config, parse_brief, judge, triage, rerun_storm, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--hub", default="", help="hub slug — nest a spoke's output under its pillar: config.RUNS/<hub>/<slug>/ (empty = flat)")
    ap.add_argument("--brief", required=True)
    ap.add_argument("--dossier", required=True)
    ap.add_argument("--redo", action="store_true", help="ignore cached step outputs; rerun everything")
    ap.add_argument("--provider", choices=["claude", "codex"], default=None,
                    help="headless LLM provider for the judgment steps (default: env LLM_PROVIDER, else claude)")
    ap.add_argument("--model", default=None, help="model for the chosen provider (blank = that CLI's default)")
    a = ap.parse_args()
    if a.provider:                    # None => inherit the env (e.g. the conductor's choice); else override
        os.environ["LLM_PROVIDER"] = a.provider; config.LLM_PROVIDER = a.provider
    if a.model:
        os.environ["LLM_MODEL"] = a.model; config.LLM_MODEL = a.model

    run_dir = os.path.join(config.RUNS, a.hub, a.slug)   # a.hub="" → flat RUNS/<slug>
    os.makedirs(run_dir, exist_ok=True)
    items_p = os.path.join(run_dir, "coverage-items.json")
    verdicts_p = os.path.join(run_dir, "coverage-verdicts.json")
    queries_p = os.path.join(run_dir, "gap-queries.json")
    have = lambda p: os.path.exists(p)

    print("== Step 0: read brief ==")
    if a.redo or not have(items_p):
        config.write_json(items_p, parse_brief.parse(open(a.brief).read())); print(f"  -> {items_p}")
    else:
        print("  · cached")

    print("== Step 1: coverage judge ==")
    if a.redo or not have(verdicts_p):
        judge.run(items_p, a.dossier, verdicts_p)
    else:
        print("  · cached")

    print("== Step 2: gap triage ==")
    if a.redo or not have(queries_p):
        triage.run(verdicts_p, queries_p)
    else:
        print("  · cached")

    print("== Step 3: STORM re-run ==")
    rerun_storm.run(queries_p, run_dir, a.dossier, redo=a.redo)

    print("== Step 4: report ==")
    report.run(run_dir)
    print(f"\nDONE -> {run_dir}")


if __name__ == "__main__":
    main()
