#!/usr/bin/env python3
"""THE PLANNER — one command, one article. Pure sequencing, resumable.

  gather -> select -> verify-sources -> freeze -> plan-view

  python3 run_planner.py --slug <slug>          # run/resume one article's plan
  python3 run_planner.py --slug <slug> --redo   # force every step to rerun

A freeze HARD flag stops the chain (fix, rerun). The queue-driven batch layer (auto-picking pending
articles from research-log.csv) comes later and will call this same run().
"""
import argparse
import config  # noqa: F401  (import order: config first so every step shares one settings hub)
import gather_inputs
import plan_select
import verify_sources
import freeze
import plan_view
import eval_pages
import time as _time
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))))
try:
    import usage_meter as _meter
except Exception:
    _meter = None


STEPS = [("gather", gather_inputs.run), ("select", plan_select.run),
         ("verify-sources", verify_sources.run), ("freeze", freeze.run), ("plan-view", plan_view.run)]


def run(slug, redo=False):
    print(f"====================  PLANNER — {slug}  ====================")
    for i, (name, fn) in enumerate(STEPS, 1):
        print(f"== planner · Step {i} of {len(STEPS)}: {name} ==")
        _t0 = _time.time()
        out = fn(slug, redo)
        if _meter:
            _meter.record_step(name, _time.time() - _t0, "planner", slug)
        if name == "freeze" and out and out.get("hard"):
            print("X stopped at freeze — fix the hard flags above, then rerun.")
            return False
    for page in ("gather", "selection", "sources", "index"):
        dict(eval_pages.BUILDERS)[page](slug)          # views only — rebuilt every run
    print(f"== PLANNER DONE -> {config.artifact(slug, 'article-plan.json')} ==")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run the whole Planner for one article.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    run(a.slug, a.redo)
