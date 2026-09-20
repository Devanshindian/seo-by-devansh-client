#!/usr/bin/env python3
"""Reattach the real source URL to STORM cards whose sentence lost its [n] footnote — IN PLACE, no re-harvest.

For an EXISTING article's bundle (cards + structure JSON already built), recover each numeric unsourced STORM
card's source from that article's url_to_info.json (via source_match) and write it back into the files the
downstream reads. Numeric cards that still can't be sourced are flagged `needs_source` (for the DataForSEO
fallback, or a final cut). Non-numeric claims are left alone (they are general statements, not stats).

Patches, per slug:
  1. research-bundle/<slug>/structure-<slug>.json   <- the WRITE PHASE reads this (critical)
  2. research-structure/out/<slug>/structure-<slug>.json + cards.json  <- the origin (kept consistent)

Reads: url_to_info.json under STORM_OUT/<topic>/. Writes: the three files above, atomically.
    python3 reattach_sources.py --slug the-real-cost-recruitment-2026
    python3 reattach_sources.py --all
"""
import argparse
import glob
import json
import os
import re
import config
import source_match as sm

SLUGS = [
    "the-type-d-personality-label", "running-hiring-hackathon-that-screens",
    "strategic-interview-questions-paired-strong", "video-interview-software-that-actually",
    "the-real-cost-recruitment-2026",
]


def _resolve_storm_dir(h1, slug=""):
    """Find the article's STORM folder. Since 2026-08-03 STORM folders are named by the SLUG (same as
    every other engine), so the direct lookup wins; the token-overlap fuzzy match against the H1 is kept
    only for pre-rename legacy folders."""
    if slug:
        p = os.path.join(config.STORM_OUT, slug)
        if os.path.isdir(p) and glob.glob(os.path.join(p, "**", "url_to_info.json"), recursive=True):
            return p
    want = set(re.findall(r"[a-z0-9]+", (h1 or "").lower()))
    best, best_ov = None, 0
    for d in sorted(os.listdir(config.STORM_OUT)):
        p = os.path.join(config.STORM_OUT, d)
        if not os.path.isdir(p) or not glob.glob(os.path.join(p, "**", "url_to_info.json"), recursive=True):
            continue
        ov = len(set(re.findall(r"[a-z0-9]+", d.lower())) & want)
        if ov > best_ov:
            best, best_ov = p, ov
    return best


def _patch_card(c, idx, stats):
    """One card dict -> recover a source if it's a numeric unsourced STORM card. Mutates c; updates stats."""
    if c.get("tag") != "storm" or c.get("source_urls"):
        return
    vb = c.get("verbatim") or c.get("gloss") or ""
    if not sm.has_number(vb):
        return
    stats["numeric_unsourced"] += 1
    url, _phrase = sm.recover(vb, idx)
    if url:
        c["source_urls"] = [url]
        c["source_recovered"] = True
        stats["recovered"] += 1
    else:
        c["needs_source"] = True            # for the DataForSEO fallback / final cut
        stats["still_unsourced"] += 1


def _walk_structure(struct, idx, stats):
    for s in struct.get("sections", []):
        for c in s.get("evidence", []):
            _patch_card(c, idx, stats)
        for h in s.get("h3", []):
            for c in h.get("evidence", []):
                _patch_card(c, idx, stats)


def _patch_file(path, idx, kind):
    if not os.path.exists(path):
        return None
    data = json.load(open(path))
    stats = {"numeric_unsourced": 0, "recovered": 0, "still_unsourced": 0}
    if kind == "cards":
        for c in data:
            _patch_card(c, idx, stats)
    else:
        _walk_structure(data, idx, stats)
    config.write_json(path, data)
    return stats


def run(slug):
    rs_dir = os.path.join(config.OUT, slug)
    struct_rs = os.path.join(rs_dir, f"structure-{slug}.json")
    cards_rs = os.path.join(rs_dir, "cards.json")
    struct_bundle = os.path.join(config.PROJ, "research-bundle", slug, f"structure-{slug}.json")

    h1 = ""
    for p in (struct_bundle, struct_rs):
        if os.path.exists(p):
            h1 = json.load(open(p)).get("h1", ""); break
    storm_dir = _resolve_storm_dir(h1, slug=slug)
    if not storm_dir:
        print(f"  [{slug}] !! no STORM dir matched — skipped"); return
    idx = sm.load_snippets(storm_dir)
    print(f"  [{slug}] storm='{os.path.basename(storm_dir)}'  snippets={len(idx)}")

    for label, path, kind in [("bundle-structure", struct_bundle, "struct"),
                              ("rs-structure", struct_rs, "struct"),
                              ("rs-cards", cards_rs, "cards")]:
        st = _patch_file(path, idx, kind)
        if st is None:
            print(f"     {label:16} (absent)")
        else:
            print(f"     {label:16} numeric-unsourced={st['numeric_unsourced']:4}  recovered={st['recovered']:4}  "
                  f"still-unsourced={st['still_unsourced']:3}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Reattach STORM source URLs in place.")
    ap.add_argument("--slug")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    targets = SLUGS if a.all else [a.slug]
    for s in targets:
        run(s)
