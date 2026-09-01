#!/usr/bin/env python3
"""Format router — slug -> archetype, decided by ONE AI call (prompts/route-archetype.md).

Reads:  research-log.csv (the queue): `format` + `asset` (title) + `angle`, looked up by slug.
Returns: one archetype label (a string). Writes NO file.

The whole routing brain — the 8 archetype definitions, the usual label->archetype table, and the
news-vs-data care rule — lives in the prompt, not here. This file only fills the prompt's blanks,
makes the one call, and validates the answer against ARCHETYPES.

(interactive-tool and case-study articles never reach the write phase — filtered/gated upstream —
so the prompt carries no mapping for them.)

Standalone proof:
    python fmt_router.py --slug the-type-d-personality-label     # -> answer-bait-definitional
    python fmt_router.py --format "Rankings / comparison"        # route a raw name (no title/angle context)
"""
import argparse
import csv
import os
import config
import llm

# The 8 archetypes — the canonical set the AI must return one of.
ARCHETYPES = {
    "answer-bait-definitional",
    "how-to-guide",
    "listicle",
    "comparison-rankings",
    "glossary",
    "data-benchmark-report",
    "template-resource",
    "common-spine",   # news / opinion / trends / framework — runs on the common spine, no format overlay
}


def _queue_row(slug):
    with open(config.LOG_CSV) as f:
        for row in csv.DictReader(f):
            if row.get("slug") == slug:
                return row
    raise SystemExit(f"!! slug {slug!r} not found in {config.LOG_CSV}")


def route(format_name, title="", angle="", winners_study=""):
    """format label (+ title/angle/winners context) -> archetype. ONE AI call, validated against ARCHETYPES."""
    prompt = (llm.load_prompt("route-archetype.md")
              .replace("{{FORMAT}}", (format_name or "").strip() or "(none given)")
              .replace("{{TITLE}}", (title or "").strip() or "(none given)")
              .replace("{{ANGLE}}", (angle or "").strip() or "(none given)")
              .replace("{{WINNERS}}", (winners_study or "").strip() or "(not available)"))
    out = llm.call_json(prompt) or {}
    arch = (out.get("archetype") or "").strip()
    if arch not in ARCHETYPES:
        raise ValueError(f"router returned an unknown archetype {arch!r} for format {format_name!r}")
    return arch


def _winners_study(slug):
    """The router's OWN read of the winners study (proof/05-winners.md). Empty when the file is absent."""
    p = os.path.join(config.proof_dir(slug), "05-winners.md")
    try:
        return open(p).read()
    except FileNotFoundError:
        return ""


def route_slug(slug):
    """slug -> archetype: read format + title + angle from the queue AND the winners study from proof/,
    then route (one AI call). An empty format label is allowed — the AI decides from the rest."""
    row = _queue_row(slug)
    fmt = (row.get("format") or "").strip()
    if not fmt:
        print(f"    - note: slug {slug!r} has no `format` in the queue -- routing on title/angle/winners alone")
    return route(fmt, title=row.get("asset", ""), angle=row.get("angle", ""), winners_study=_winners_study(slug))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Map one article to a write-phase archetype (one AI call).")
    ap.add_argument("--slug", help="look format + title + angle up in research-log.csv by slug, then route")
    ap.add_argument("--format", help="route a raw format name directly (no title/angle context)")
    a = ap.parse_args()
    if a.slug:
        print(route_slug(a.slug))
    elif a.format:
        print(route(a.format))
    else:
        ap.error("give --slug or --format")
