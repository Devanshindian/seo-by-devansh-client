#!/usr/bin/env python3
"""THE one entry point — catalogue a company's website + its search traffic.

Pure sequencing: calls each stage's run() in order and nothing else. Every stage writes a
named output file; on re-run an existing output is reused unless --redo forces it. So a
crash resumes where it left off and no paid call is ever repeated by accident.

Usage:
  COMPANY=<slug> python3 run_catalogue.py            # full run (resumes past finished stages)
  python3 run_catalogue.py --company <slug>          # same, flag instead of env
  ... --check                                        # validate the record, print paths, exit
  ... --from extract                                 # start at a stage (earlier outputs reused)
  ... --redo                                         # ignore existing outputs, rerun everything
"""
import argparse
import csv
import importlib
import os
import re
import sys


def _write_viewer(config):
    """Write a spreadsheet-friendly PREVIEW of content-database.csv. The real file keeps each
    page's line breaks (the pipeline splits on them); those same breaks make Excel/Numbers scatter
    the rows and show blanks. This flattens every cell to ONE line so a human can open it. Nothing
    in the pipeline reads it — it exists only so the output can be eyeballed.

    It lives in _work/, NOT output/: flattening destroys the line structure every downstream step
    counts on, so a preview sitting beside the real file in output/ is an invitation to wire the
    wrong one in. output/ holds deliverables; this is a convenience copy."""
    src = config.CATALOGUE_CSV
    if not os.path.exists(src):
        return
    viewer = os.path.join(config.WORK, "content-database-preview.csv")
    csv.field_size_limit(sys.maxsize)
    with open(src, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return
    cols = list(rows[0].keys())
    flat = lambda s: re.sub(r"\s+", " ", (s or "").replace("\n", " ").replace("\r", " ")).strip()

    def write(fh):
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            r = dict(r)
            for c in ("Full content", "Description", "Title"):
                if c in r:
                    r[c] = flat(r[c])
            w.writerow(r)
    config._atomic_write(viewer, write)
    print(f"   preview (open this in a spreadsheet; NOT the deliverable) -> "
          f"{os.path.relpath(viewer, config.REPO_ROOT)}")

# stage name -> (module, the output file that marks it done)  [file names live in config]
STAGES = [
    ("enumerate-wp",      "enumerate_wp",      "URLS_WP"),
    ("enumerate-sitemap", "enumerate_sitemap", "URLS_SITEMAP"),
    ("enumerate-archive", "enumerate_archive", "URLS_ARCHIVE"),
    ("enumerate-crawl",   "enumerate_crawl",   "URLS_CRAWL"),
    ("reconcile",         "reconcile",         "RECONCILED"),
    ("extract",           "extract",           "CATALOGUE_CSV"),
    ("traffic",           "traffic",           "TOP_PAGES_CSV"),
    ("gates",             "gates",             "REPORT_MD"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--company", help="company slug (overrides the COMPANY env var)")
    ap.add_argument("--check", action="store_true", help="validate the company record, print the resolved paths, exit")
    ap.add_argument("--from", dest="from_stage", metavar="STAGE",
                    choices=[name for name, _, _ in STAGES],
                    help="start at this stage (earlier stages' existing outputs are reused)")
    ap.add_argument("--redo", action="store_true", help="rerun every stage even if its output exists")
    args = ap.parse_args()

    if args.company:
        os.environ["COMPANY"] = args.company
    import config   # AFTER --company lands in the env; import fails closed on a bad/missing record

    print(config.describe())
    if args.check:
        print("\nrecord OK — ready to run.")
        return

    start = 0
    if args.from_stage:
        start = [name for name, _, _ in STAGES].index(args.from_stage)

    for i, (name, module_name, out_attr) in enumerate(STAGES, 1):
        print(f"\n== Stage {i}: {name} ==")
        if i - 1 < start:
            print(f"   (before --from {args.from_stage}; reusing existing output)")
            continue
        out_path = getattr(config, out_attr)
        if not args.redo and os.path.exists(out_path):
            print(f"   done already -> {os.path.relpath(out_path, config.REPO_ROOT)} (use --redo to force)")
            continue
        try:
            mod = importlib.import_module(module_name)
        except ImportError as e:
            sys.exit(f"!! stage '{name}' is not built yet ({e}) — stopping here.")
        mod.run()
        if not os.path.exists(out_path):
            sys.exit(f"!! stage '{name}' finished without writing {out_path} — a stage's output "
                     f"file is its done-marker; refusing to continue on a silent no-op.")

    print("\n== all stages complete ==")
    _write_viewer(config)     # a spreadsheet-friendly copy for a human to open


if __name__ == "__main__":
    main()
