#!/usr/bin/env python3
"""
study-trends-verify.py — fail-closed gate for the Asset-Engine Method-3 (Study Trends) run.

WHY THIS EXISTS: on the 2026-06-25 Testlify run the agent produced tensions.csv first and wrote the
merge-check evidence afterward (faking the gate), used a forbidden off-brand "junk" bucket, ignored the
size alarm, and leaked product framing into the neutral sub-questions. None of that was caught by the
agent's own checklist — it was caught by a human. This script moves the checking OUT of the agent's
judgment: run it from a study-trends/ directory; if ANY check fails it exits non-zero and the run is NOT done.

Company-agnostic. Run:  python3 study-trends-verify.py /path/to/projects/<company>/asset-engine/study-trends
(defaults to the current directory).
"""
import sys, os, csv, glob, re

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
def p(*a): return os.path.join(ROOT, *a)

MISC_MAX_PCT      = 0.15   # misc may not exceed 15% of posts
OFFBRAND_POST_CAP = 8      # a DROP bucket bigger than this must be examined in merge-check.md
PHRASE_ALARM      = 15     # a kept tension with more phrases than this must be justified in merge-check.md
# words that mean the neutral evidence steps leaked the company's solution (Stage-4 bleed-back)
BANNED_SUBQ = ["skills test","skills tests","skills screening","skills-based screening","skills-based hiring",
               "objective testing","blind/skills","testlify","our platform","our product"]
KEEP_VERDICTS = {"KEEP-CORE","KEEP-ADJACENT","KEEP-TRANSPLANT","MAYBE"}

fails, warns = [], []
def check(cond, msg):
    (None if cond else fails.append(msg))
def warn(cond, msg):
    (None if cond else warns.append(msg))

# ---- load artifacts ----
scrapes = glob.glob(p("_raw","*-reddit-trends.xlsx"))
mc      = p("_work","merge-check.md")
mapf    = p("_work","post-tension-map.tsv")
tens    = p("output","tensions.csv")
pmap    = p("output","phrase-map.csv")
ideas   = p("output","study-trends-ideas.csv")
for f in (mapf, tens, pmap, ideas, mc):
    if not os.path.exists(f): fails.append(f"MISSING FILE: {os.path.relpath(f, ROOT)}")
if not scrapes: fails.append("MISSING scrape: _raw/*-reddit-trends.xlsx")
if fails:
    print("\n".join("✗ "+x for x in fails)); print("\nVERIFY: FAIL (missing files)"); sys.exit(1)

mc_text = open(mc, encoding="utf-8").read().lower()
import openpyxl
ws = openpyxl.load_workbook(scrapes[0], read_only=True)["Posts"]
rows = list(ws.iter_rows(values_only=True)); hdr = {h:i for i,h in enumerate(rows[0])}
scrape_ids = set(r[hdr["post_id"]] for r in rows[1:])
mp = list(csv.DictReader(open(mapf), delimiter="\t"))
trows = list(csv.DictReader(open(tens)))
prows = list(csv.DictReader(open(pmap)))
irows = list(csv.DictReader(open(ideas)))

# ---- 1. ORDER: merge-check.md must predate tensions.csv (the gate ran first) ----
check(os.path.getmtime(mc) <= os.path.getmtime(tens),
      "ORDER: merge-check.md is NEWER than tensions.csv — the gate was written after the tensions (faked).")

# ---- 2. COVERAGE: every scraped post assigned exactly once; misc <= 15% ----
map_ids = [r["post_id"] for r in mp]
check(len(map_ids) == len(set(map_ids)), "COVERAGE: duplicate post_ids in post-tension-map.tsv")
check(set(map_ids) == scrape_ids,
      f"COVERAGE: map != scrape (missing {len(scrape_ids-set(map_ids))}, extra {len(set(map_ids)-scrape_ids)})")
misc = sum(1 for r in mp if r["tension"] == "misc")
check(len(mp) and misc/len(mp) <= MISC_MAX_PCT, f"COVERAGE: misc {misc}/{len(mp)} exceeds {int(MISC_MAX_PCT*100)}%")

# counts per tension from the map
from collections import Counter
posts_per = Counter(r["tension"] for r in mp)
phrases_per = Counter(r["tension"] for r in prows)
verdict = {r["tension_id"]: r["Verdict"] for r in trows}
subq = {r["tension_id"]: r.get("Sub-questions","") for r in trows}

# ---- 3. NO OFF-BRAND JUNK BUCKET: any DROP tension > cap must be named in merge-check.md ----
for t, n in posts_per.items():
    if verdict.get(t) == "DROP" and n > OFFBRAND_POST_CAP:
        check(t.lower() in mc_text,
              f"OFF-BRAND: DROP bucket '{t}' has {n} posts but is never examined in merge-check.md (junk drawer).")

# ---- 4. SIZE ALARM: kept tension with > PHRASE_ALARM phrases must be justified in merge-check.md ----
for t, n in phrases_per.items():
    if verdict.get(t) in KEEP_VERDICTS and n > PHRASE_ALARM:
        check(t.lower() in mc_text,
              f"SIZE-ALARM: kept tension '{t}' has {n} phrases (> {PHRASE_ALARM}) but no justification in merge-check.md.")

# ---- 5. EVERY KEPT TENSION WENT THROUGH THE GATE: named in merge-check.md ----
for t, v in verdict.items():
    if v in KEEP_VERDICTS:
        check(t.lower() in mc_text, f"GATE: kept tension '{t}' never appears in merge-check.md (formed outside the gate).")

# ---- 6. NO PRODUCT LEAK in the neutral sub-questions of kept tensions ----
for t, v in verdict.items():
    if v in KEEP_VERDICTS:
        sql = subq.get(t,"").lower()
        bad = [w for w in BANNED_SUBQ if w in sql]
        check(not bad, f"PRODUCT-LEAK: '{t}' sub-questions contain {bad} — Stage-4 solution framing in neutral evidence.")

# ---- 7. EVERY KEPT TENSION HAS AN IDEA, AND NO IDEA WITHOUT A KEPT TENSION ----
idea_tensions = set(r["Tension"] for r in irows)
tens_text = {r["Tension"] for r in trows if r["Verdict"] in KEEP_VERDICTS}
check(len(irows) == len(tens_text),
      f"IDEAS: {len(irows)} ideas vs {len(tens_text)} kept tensions — mismatch (an idea with no tension or vice-versa).")

# ---- 8. phrase-map sanity (warn-only) ----
pm_ids = set(x for r in prows for x in r["source_post_ids"].split())
warn(pm_ids <= scrape_ids, "phrase-map references post_ids not in the scrape")
singles = [r["phrase"] for r in prows if len(r["phrase"].split()) < 2]
warn(len(singles) <= 3, f"{len(singles)} single-word phrases (should be 2-4 words): {singles[:5]}")

# ---- report ----
print(f"Study-Trends verify — {ROOT}")
print(f"  posts={len(mp)}  tensions={len(posts_per)}  kept={len(tens_text)}  ideas={len(irows)}  misc={misc}")
for w in warns: print("⚠ "+w)
if fails:
    print("\n".join("✗ "+x for x in fails)); print(f"\nVERIFY: FAIL ({len(fails)} check(s)). The run is NOT done."); sys.exit(1)
print("\nVERIFY: PASS — all gates satisfied.")
