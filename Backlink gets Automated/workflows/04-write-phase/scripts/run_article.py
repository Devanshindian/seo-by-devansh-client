#!/usr/bin/env python3
"""THE SPINE — one command, one article. Researched topic in, finished article out.

  COMPANY=<company> python3 run_article.py --slug <slug>

  planner -> architect -> field -> writer

WHAT IT IS. Four stations already ran as four commands you typed one after another. This runs them in
order, once. It is PURE SEQUENCING: it calls each station's run() and holds no logic of its own, so
every station stays independently runnable and nothing that worked before stops working.

WHAT IT IS NOT. It does not research. It starts from a topic the research phase has already turned
into a bundle. Going from a raw topic to a finished article is still two commands: research, then
this one.

WHY IT EXISTS (2026-08-26). Three things still to build all need the same thing underneath: the
/writer command, the /article command, and the desktop UI each need something to call. Without this
they would each work out their own way to chain four stations, and the three copies would drift apart.

RESUMABLE, for free. Every station already reuses its finished work, so a run killed at 3am by a usage
limit carries on in the morning from where it stopped. It does not repeat a paid call. --redo forces a
full rerun.

THE TWO GATES (Devansh, 2026-08-26):
  · A HARD FREEZE STOPS EVERYTHING. The planner verifies every source before a word is written; a hard
    flag means one failed badly. There is no point building an article on a plan that failed its own
    source checks, so the chain stops and you fix the source.
  · A FIELD FAILURE DOES NOT. write_body treats voices-from-the-field.md as a block that is either
    there or empty, so the writer is fine without it. Losing some Reddit quotes must not cost a
    finished article overnight: it is reported loudly and the chain carries on.
"""
import argparse
import os
import time
import traceback

import config  # noqa: F401  (config first so every station shares one settings hub)
import run_planner
import run_architect
import run_field
import run_writer

# (name, callable, required). The order IS the pipeline. "required" answers one question: does a
# failure here cost you the article?
STATIONS = [
    ("planner",   run_planner.run,   True),
    ("architect", run_architect.run, True),
    ("field",     run_field.run,     False),
    ("writer",    run_writer.run,    True),
]


def _hms(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {s:02d}s"


def _summary(slug, timings, total, tail):
    print(f"\n{'-' * 58}\n  {slug}")
    for name, sec, state in timings:
        print(f"    {name:10} {_hms(sec):>9}   {state}")
    print(f"    {'TOTAL':10} {_hms(total):>9}")
    print(f"{'-' * 58}\n{tail}")


def run(slug, redo=False, start=None, until=None, skip_field=False):
    """Chain the four stations for one slug. Returns True only when the writer finished."""
    names = [n for n, _, _ in STATIONS]
    if start and start not in names:
        raise ValueError(f"unknown station {start!r} — one of {names}")
    begin = names.index(start) if start else 0

    print(f"{'#' * 58}\n#  {slug}\n{'#' * 58}")
    if begin:
        print(f"   starting at {start}, so {', '.join(names[:begin])} must already have run")
    t_run = time.time()
    timings = []

    for name, fn, required in STATIONS[begin:]:
        if name == "field" and skip_field:
            print("\n>>> field — skipped (--skip-field)")
            continue
        print(f"\n>>> {name}")
        t0 = time.time()
        try:
            ok = fn(slug, redo=redo, until=until) if name == "writer" else fn(slug, redo=redo)
        except Exception as e:
            if required:
                print(f"\nX {name} FAILED — {type(e).__name__}: {e}")
                traceback.print_exc()
                _summary(slug, timings + [(name, time.time() - t0, "FAILED")],
                         time.time() - t_run, f"X stopped in {name}. Nothing after it ran.")
                return False
            print(f"\n!! {name} failed, carrying on without it — {type(e).__name__}: {str(e)[:110]}")
            print("   (the writer treats the field file as optional, so the article is not lost)")
            timings.append((name, time.time() - t0, "failed, skipped"))
            continue
        timings.append((name, time.time() - t0, "ok" if ok is not False else "stopped"))
        if ok is False:
            # Two different things return False and they must not read the same. The planner means a
            # hard freeze flag and something is wrong. The writer means --until did what it was told.
            if name == "writer" and until:
                tail = f"·  stopped after the {until} step, as asked."
            else:
                tail = (f"X {name} stopped the chain. Read its message above, fix it, "
                        f"then run the same command again.")
            _summary(slug, timings, time.time() - t_run, tail)
            return False

    _summary(slug, timings, time.time() - t_run,
             f"== ARTICLE DONE ==\n   {config.artifact(slug, 'draft.md')}")
    return True


def main():
    ap = argparse.ArgumentParser(
        description="Run one article end to end: planner -> architect -> field -> writer.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true",
                    help="rerun every step instead of reusing what already finished")
    ap.add_argument("--from", dest="start", choices=[n for n, _, _ in STATIONS],
                    help="start at this station (the earlier ones must already have run)")
    ap.add_argument("--until", choices=[n for n, _ in run_writer.STEPS],
                    help="stop after this WRITER step, to read the writing before it is polished")
    ap.add_argument("--skip-field", action="store_true",
                    help="skip the Reddit/Blind/LinkedIn station")
    a = ap.parse_args()
    if not os.environ.get("COMPANY"):
        print("  (COMPANY is not set — config falls back to its default)")
    raise SystemExit(0 if run(a.slug, redo=a.redo, start=a.start,
                              until=a.until, skip_field=a.skip_field) else 1)


if __name__ == "__main__":
    main()
