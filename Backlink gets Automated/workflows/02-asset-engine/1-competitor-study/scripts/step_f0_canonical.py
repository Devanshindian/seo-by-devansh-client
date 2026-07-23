#!/usr/bin/env python3
"""Step F0 — merge the format tagger's own label variants into one canonical set.

The tagger runs in independent batches, so it names the same shape differently each time. Measured
2026-07-20: 127 distinct labels for 1,202 pages, including SIX ways to say "product/solution page" and
three ways to say "press release". That splits the signal — one strong format looks like three weak
ones, which is exactly the question Step F exists to answer.

The merge is a JUDGMENT (is "Statistics roundup" the same shape as "Data report"? no — one collects
others' numbers, one is original research), so it is an LLM call with the criteria in the prompt file.
It also flags shapes that are not content assets at all (user profiles, help pages, spam), which the
URL-level filter cannot always catch.

Reads:  _work/formats/*.json + _work/read/*.json
Writes: both, in place, with `format` canonicalised and `format_junk` set
        _work/format-canonical.json — the mapping, so every merge is inspectable
"""
import argparse, collections, json, os, sys
import config as c
sys.path.insert(0, c.SHARED)
import llm


def run(redo=False):
    map_path = os.path.join(c.WORK, "format-canonical.json")
    dirs = [d for d in ("formats", "read") if os.path.isdir(os.path.join(c.WORK, d))]
    if not dirs:
        sys.exit("!! nothing tagged yet — run step_d_format.py first")

    counts = collections.Counter()
    for d in dirs[:1]:                      # count from one source; the labels are the same
        for f in os.listdir(os.path.join(c.WORK, d)):
            if f.endswith(".json"):
                for r in json.load(open(os.path.join(c.WORK, d, f))):
                    counts[r.get("format") or "UNTAGGED"] += 1

    if os.path.exists(map_path) and not redo:
        mapping = json.load(open(map_path))
    else:
        labels = "\n".join(f"{n} — {lab}" for lab, n in counts.most_common())
        mapping = llm.call_json(open(os.path.join(c.PROMPTS, "canonicalize-formats.md"))
                                .read().replace("{{LABELS}}", labels))
        c.write_json(map_path, mapping)

    m, junk = mapping.get("map", {}), set(mapping.get("junk", []))
    changed = 0
    for d in dirs:
        dd = os.path.join(c.WORK, d)
        for f in os.listdir(dd):
            if not f.endswith(".json"):
                continue
            rows = json.load(open(os.path.join(dd, f)))
            for r in rows:
                old = r.get("format") or "UNTAGGED"
                new = m.get(old, old)
                if new != old:
                    changed += 1
                r["format"] = new
                r["format_junk"] = new in junk
            c.write_json(os.path.join(dd, f), rows)

    after = len({m.get(k, k) for k in counts})
    print(f"   {len(counts)} labels -> {after} canonical  ({changed} rows relabelled)")
    print(f"   flagged as NOT a content asset: {len(junk)} shapes")
    for j in sorted(junk)[:10]:
        print(f"     · {j}")
    if mapping.get("note"):
        print(f"   note: {mapping['note']}")
    return mapping


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
