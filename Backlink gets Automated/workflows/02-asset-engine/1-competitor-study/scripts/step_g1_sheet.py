#!/usr/bin/env python3
"""Step G1 — build the working sheet, and FLAG (never delete) redundant-text rows.

Reads:  _work/master.json          (every kept page, with its scraped body from Step E)
Writes: _work/g_sheet.json         (the same rows + a stable Row ID + empty G2 columns + a text flag)

Two jobs, both pure Python — no judgment, so no LLM (the four questions here are mechanical facts
about the text: count it, hash it):

1. ROW ID. Give every master row a stable id so the parallel G2 agents' output stitches back to the
   right row (the recipe: "its line number is fine").

2. THE LIGHT DEDUP FLAG. Rows whose body is BYTE-IDENTICAL to another are redundant for idea-writing —
   G3's merge would collapse them anyway, and handing the same text to G2 four times just writes the
   same idea four times. So flag all-but-one copy `text_dup` and let G2 skip them. Deliberately
   conservative and NON-destructive (Devansh, 2026-07-21, after we talked it through):
     - only EXACT byte-identical bodies (a hash) — never a fuzzy "looks similar", which would risk
       merging genuinely different pages;
     - we KEEP every flagged row and its backlinks (they still count in Step F and stay as evidence in
       G3) — the PROTECT rule: never drop a row that carries hard value (referring domains);
     - nav-heavy and thin rows are NOT flagged here — an LLM reading the page in G2 sees past a menu
       fine, so cutting them would throw away real article text under the chrome for no gain.
   The one survivor per identical-body group is the row with the most follow domains (the strongest
   piece of proof leads; F1 single-source — the survivor is chosen ONCE, here).
"""
import argparse, hashlib, json, os, sys, collections
import config as c

# the empty columns G2/G3 fill — created here so the sheet's shape is fixed up front (F2 traceable)
G_COLUMNS = ["idea_num", "asset", "brand_fit", "angle_gap", "distinct_angle", "g_notes"]


def _readable(r):
    """A row G2 can actually reason over: read ok AND real body text present."""
    return r.get("read_status") == "ok" and (r.get("body") or "").strip()


def run():
    master_path = os.path.join(c.WORK, "master.json")
    if not os.path.exists(master_path):
        sys.exit("!! no _work/master.json — run step_e_read.py first")
    rows = json.load(open(master_path))

    # 1. stable Row ID (F1: assigned once, carried forward everywhere)
    for i, r in enumerate(rows):
        r["row_id"] = i
        for col in G_COLUMNS:
            r.setdefault(col, "")

    # 2. exact-duplicate FLAG — survivor = most follow domains; the rest marked text_dup (kept, not cut)
    groups = collections.defaultdict(list)
    for r in rows:
        if _readable(r):
            h = hashlib.sha256(r["body"].encode()).hexdigest()
            groups[h].append(r)
    flagged = 0
    for h, grp in groups.items():
        if len(grp) < 2:
            continue
        grp.sort(key=lambda r: -(r.get("domains_follow") or 0))     # strongest proof survives
        for dup in grp[1:]:
            dup["text_dup_of"] = grp[0]["row_id"]                   # traceable to its survivor
            flagged += 1

    readable = sum(1 for r in rows if _readable(r))
    uniq = readable - flagged
    c.write_json(os.path.join(c.WORK, "g_sheet.json"), rows)
    print(f"   {len(rows)} master rows")
    print(f"   readable (has real body text): {readable}")
    print(f"   flagged text_dup (redundant, KEPT for evidence): {flagged}")
    print(f"   -> G2 will reason over {uniq} unique-text rows")
    print(f"   -> {c.rel(os.path.join(c.WORK, 'g_sheet.json'))}")
    return rows


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    run()
