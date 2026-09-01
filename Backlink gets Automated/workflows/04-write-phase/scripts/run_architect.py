#!/usr/bin/env python3
"""THE ARCHITECT — one command, one article. Pure sequencing, resumable.

  shape (design the body structure) -> enrich (research what it asked for) -> brand-cards
  (place the company's own material, if any of it earns a place) -> allocate (word target per
  section) -> section-keywords (which sections deserve a keyword, and which one) -> headings (write every
  final heading + the H1)

  python3 run_architect.py --slug <slug>          # run/resume
  python3 run_architect.py --slug <slug> --redo   # force both steps to rerun

Reads the frozen planner/article-plan.json; produces architect/structure.json (+ structure.md,
enriched-cards.json, _work/). Run run_planner.py first.
"""
import argparse
import config  # noqa: F401  (config first so every step shares one settings hub)
import shape
import enrich
import brand_cards
import allocate_words
import section_keywords
import headings
import eval_pages
import time as _time
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))))
try:
    import usage_meter as _meter
except Exception:
    _meter = None


STEPS = [("shape", shape.run), ("enrich", enrich.run), ("brand-cards", brand_cards.run),
         ("allocate", allocate_words.run),
         ("section-keywords", section_keywords.run), ("headings", headings.run)]


def run(slug, redo=False):
    print(f"====================  ARCHITECT — {slug}  ====================")
    for i, (name, fn) in enumerate(STEPS, 1):
        print(f"== architect · Step {i} of {len(STEPS)}: {name} ==")
        _t0 = _time.time()
        fn(slug, redo)
        if _meter:
            _meter.record_step(name, _time.time() - _t0, "architect", slug)
    eval_pages.build_blueprint(slug)                 # view only — rebuilt every run
    eval_pages.build_index(slug)                     # the front door picks up the new page
    print(f"== ARCHITECT DONE -> {config.artifact(slug, 'structure.json')} ==")
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run the whole Architect for one article.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    run(a.slug, a.redo)
