#!/usr/bin/env python3
"""Assemble consolidated domain outputs into the final themed pillar map + validate."""
import json, glob, csv, collections

blog = set()
for r in csv.DictReader(open("data/url-clusters.csv")):
    if r["type"] == "blog":
        blog.add(r["slug"])

THEMES = ["Interview Questions by Role","Skills & Job Assessments","Personality & Aptitude Testing",
    "Candidate Screening & Proctoring","Recruiting & Talent Acquisition","Hiring by Role & Use-case",
    "Employee Experience & Development","HR Operations & Compliance","Workplace Culture & Future of Work",
    "Skills Management","Competitor Alternatives"]

pillars, orphans = [], []
seen = collections.Counter(); invented = []
for fn in sorted(glob.glob("data/consolidate/out/*.json")):
    d = json.load(open(fn))
    for p in d.get("pillars", []):
        th = p.get("theme", "").strip()
        if th not in THEMES: th = "Recruiting & Talent Acquisition"  # safety
        sp = sorted(set(p["spokes"]))
        for s in sp:
            seen[s]+=1
            if s not in blog: invented.append(s)
        pillars.append({"pillar": p["pillar"].strip(), "theme": th,
                        "intent": p.get("intent","informational"), "spokes": sp, "n": len(sp)})
    for s in d.get("orphans", []):
        seen[s]+=1; orphans.append(s)
        if s not in blog: invented.append(s)

covered=set(seen); missing=blog-covered; dupes=[s for s,n in seen.items() if n>1]
pillars.sort(key=lambda p:(THEMES.index(p["theme"]), -p["n"]))

# existing Testlify hub page per theme (from the page inventory)
HUBPAGE = {
 "Interview Questions by Role": ("BUILD", "/interview-questions/ — 400+ role-Q posts, no hub today"),
 "Skills & Job Assessments": ("EXISTS", "/skills-assessment-platform/ + test-type pages (/coding-tests/, /programming-tests/ …)"),
 "Personality & Aptitude Testing": ("EXISTS", "/psychometric-tests/, /cognitive-ability-tests/"),
 "Candidate Screening & Proctoring": ("EXISTS", "/anti-cheating-and-proctoring/, /ai-resume-screener/"),
 "Recruiting & Talent Acquisition": ("BUILD", "/recruitment-guide/ — only partial via HR Guide ch.03"),
 "Hiring by Role & Use-case": ("EXISTS", "/hiring-guides/ (88) + use-case pages (/remote-hiring/ …)"),
 "Employee Experience & Development": ("BUILD", "/employee-engagement-guide/ (or HR Guide ch.04/05)"),
 "HR Operations & Compliance": ("EXISTS", "/hr-guide/ (12 chapters)"),
 "Workplace Culture & Future of Work": ("BUILD", "/future-of-work/"),
 "Skills Management": ("EXISTS", "/skills-management/ (your model cluster)"),
 "Competitor Alternatives": ("EXISTS", "/[competitor]-alternatives/ pages + /hr-tools/"),
}

by_theme=collections.OrderedDict()
for th in THEMES:
    tp=[p for p in pillars if p["theme"]==th]
    if tp: by_theme[th]={"status":HUBPAGE[th][0],"hub":HUBPAGE[th][1],
                         "pillars":tp,"n_pillars":len(tp),"n_posts":sum(p["n"] for p in tp)}

json.dump({"themes":by_theme,"orphans":sorted(set(orphans)),
           "totals":{"blog":len(blog),"pillars":len(pillars),
                     "posts_in_pillars":len(blog)-len(set(orphans)),"orphans":len(set(orphans))}},
          open("data/final-clusters.json","w"), indent=2)

print(f"blog {len(blog)} | covered {len(covered)} | missing {len(missing)} | dupes {len(dupes)} | invented {len(invented)}")
print(f"FINAL: {len(pillars)} pillars across {len(by_theme)} themes | orphans {len(set(orphans))}")
print()
for th,v in by_theme.items():
    print(f"  [{v['status']:6}] {v['n_pillars']:3d} pillars / {v['n_posts']:4d} posts  {th}")
if missing: print("MISSING:", list(missing)[:10])
if invented: print("INVENTED:", invented[:10])
if dupes: print("DUPES:", dupes[:10])
