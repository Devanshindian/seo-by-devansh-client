#!/usr/bin/env python3
"""run_competitor_study.py — THE ORCHESTRATOR. One command runs the whole study, A -> H.

Pure sequencing (C4): it calls each step in order and nothing else. Every step is a subprocess
(`python scripts/step_x.py`), so each keeps its own venv/config isolation (Step E re-execs into Layer
00's venv, etc.) and the orchestrator never imports business logic.

RESUMABLE: each step writes a named output; the orchestrator skips a step whose output already exists
(so a re-run of a finished company is near-instant, and a crash resumes where it stopped). `--redo`
forces everything; `--from <STEP>` forces from one step onward.

TWO HUMAN GATES (recipe): after A (competitors) and G0 (brand scope), a FRESH run STOPS so a human
approves the file, then re-runs to continue. If the approved file already exists, the gate auto-passes.

Company-agnostic: `--company <slug>` (or COMPANY env) is the only per-company input.

    python run_competitor_study.py --company testlify
    python run_competitor_study.py --company testgorilla --add "wecp.io,maki.people"
"""
import argparse, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "scripts")
sys.path.insert(0, SCRIPTS)

# (label, script, [extra args], marker-relative-to-project-study-dir, is_gate, is_paid)
STEPS = [
    ("A  competitors",   "step_a_competitors.py", [], "output/competitors.md",           True,  True),
    ("B  pull pages",    "step_b_pages.py",       [], "_raw",                             False, True),
    ("C  filter",        "step_c_filter.py",      [], "_work/candidates",                 False, False),
    ("D  tag format",    "step_d_format.py",      [], "_work/formats",                    False, False),
    ("F0 canonicalise",  "step_f0_canonical.py",  [], "_work/format-canonical.json",      False, False),
    ("E  read pages",    "step_e_read.py",        [], "_work/master.json",                False, False),
    ("F  format table",  "step_f_formats.py",     [], "output/format-summary.csv",        False, False),
    ("G0 brand scope",   "step_g0_scope.py",      [], "output/brand-scope.md",            True,  False),
    ("G1 sheet",         "step_g1_sheet.py",      [], "_work/g_sheet.json",               False, False),
    ("G2 reasoning",     "step_g2_reason.py",     [], "_work/g2_sheet.json",              False, False),
    ("G2.5 dedup",       "step_g25_dedup.py",     [], "_work/dedup-report.json",          False, False),
    ("G3 ideas",         "step_g3_ideas.py",      [], "output/ideas.csv",                 False, False),
    ("H  deliver",       "step_h_deliver.py",     [], "output/competitor-study-ideas.xlsx", False, False),
]


# steps that take no --redo flag (they recompute cheaply from their inputs every time)
_NO_REDO = {"step_f_formats.py", "step_g0_scope.py", "step_g1_sheet.py"}


def _study_dir(company, repo_root):
    return os.path.join(repo_root, "projects", company, "02-asset-engine", "competitor-study")


def _n_json(d):
    """Count *.json files directly in a directory (subdirs are not counted)."""
    return len([f for f in os.listdir(d) if f.endswith(".json")]) if os.path.isdir(d) else 0


def _n_competitors(study):
    """Approved competitors, counted with the SAME regex step_b_pages.approved() uses,
    so the completeness threshold matches exactly what the run will process."""
    path = os.path.join(study, "output", "competitors.md")
    if not os.path.exists(path):
        return 0
    doms = set()
    for line in open(path):
        m = re.match(r"^- \*\*([a-z0-9][a-z0-9.\-]*\.[a-z]{2,})\*\*", line.strip(), re.I)
        if m:
            doms.add(m.group(1).lower())
    return len(doms)


# Per-competitor directory steps write ONE json per competitor. A dir with >=1 json is NOT
# proof the step finished — a prior interrupted run (crash, Ctrl-C, sleep) leaves a PARTIAL
# dir that the old "any json = done" check wrongly treated as cached, silently building the
# whole study from a single competitor. A marker like this is only complete when it COVERS
# its upstream set. Map each per-competitor marker to the count it must reach.  (C5: a marker's
# existence must GUARANTEE completeness.)
_PER_COMP_UPSTREAM = {
    "_raw":             lambda study: _n_competitors(study),
    "_work/candidates": lambda study: _n_json(os.path.join(study, "_raw")),
    "_work/formats":    lambda study: _n_json(os.path.join(study, "_work", "candidates")),
}


def _complete(study, marker, marker_path):
    """Is this step's output complete? For per-competitor directory steps, completeness means
    'one output per upstream competitor', not merely 'the directory exists'."""
    if marker in _PER_COMP_UPSTREAM:
        need = _PER_COMP_UPSTREAM[marker](study)
        return need > 0 and _n_json(marker_path) >= need
    if os.path.isdir(marker_path):
        return any(f.endswith(".json") for f in os.listdir(marker_path))
    return os.path.exists(marker_path)


def main():
    ap = argparse.ArgumentParser(description="Run the competitor study end to end (A -> H).")
    ap.add_argument("--company", default=os.environ.get("COMPANY", ""), help="company slug (or COMPANY env)")
    ap.add_argument("--add", default="", help="operator-named competitors, comma-separated (passed to Step A)")
    ap.add_argument("--redo", action="store_true", help="force every step to re-run")
    ap.add_argument("--from", dest="from_step", default="", help="force from this step onward (e.g. G2)")
    ap.add_argument("--yes-gates", action="store_true", help="do not stop at the human gates (already approved)")
    args = ap.parse_args()
    if not args.company:
        sys.exit("!! --company is required (or set COMPANY). This orchestrator has no default company.")

    # repo root = up from workflows/02-asset-engine/1-competitor-study
    repo_root = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    study = _study_dir(args.company, repo_root)
    env = dict(os.environ, COMPANY=args.company)

    forcing = args.redo
    labels = [s[0].split()[0] for s in STEPS]
    from_idx = labels.index(args.from_step) if args.from_step in labels else -1

    print(f"== competitor study :: {args.company} ==")
    for i, (label, script, extra, marker, gate, paid) in enumerate(STEPS):
        force = forcing or (from_idx >= 0 and i >= from_idx)
        marker_path = os.path.join(study, marker)
        existed = _complete(study, marker, marker_path)
        if existed and not force:
            print(f"== {label:18s} — cached (skip) ==")
            continue
        cmd = [sys.executable, os.path.join(SCRIPTS, script)] + extra
        if script == "step_a_competitors.py" and args.add:
            cmd += ["--add", args.add]
        # only pass --redo to steps that DEFINE it — F / G0 / G1 recompute cheaply and take no flags,
        # so passing --redo would crash their argparse.
        if force and script not in _NO_REDO:
            cmd += ["--redo"]
        print(f"== {label:18s} — running{' [PAID]' if paid else ''} ==", flush=True)
        r = subprocess.run(cmd, env=env)
        if r.returncode != 0:
            sys.exit(f"!! {label} failed (exit {r.returncode}). Fix it, then re-run — finished steps are cached.")
        # a FRESH gate stops for human approval
        if gate and not existed and not args.yes_gates:
            print(f"\n   ⛔ GATE — human approval needed.")
            print(f"      Open and approve/edit:  {os.path.relpath(marker_path, repo_root)}")
            print(f"      Then continue with:      python {os.path.basename(__file__)} --company {args.company}")
            return
    print(f"\n== DONE :: {args.company} — deliverable at "
          f"projects/{args.company}/02-asset-engine/competitor-study/output/competitor-study-ideas.xlsx ==")


if __name__ == "__main__":
    main()
