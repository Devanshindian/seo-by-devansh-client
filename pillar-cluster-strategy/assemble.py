#!/usr/bin/env python3
"""Assemble all data/fine/*.json into one validated pillar map.
Validates coverage against blog slugs, merges same-title pillars, flags issues."""
import json, os, glob, re, collections, csv

blog = set()
for r in csv.DictReader(open("data/url-clusters.csv")):
    if r["type"] == "blog":
        blog.add(r["slug"])

pillars = []       # {pillar,intent,slice,spokes[]}
orphans = []
seen = collections.Counter()
invented = []

for fn in sorted(glob.glob("data/fine/w*.json")):
    d = json.load(open(fn))
    sid = d.get("slice_id", os.path.basename(fn)[:-5])
    for c in d.get("clusters", []):
        sp = [s for s in c["spokes"]]
        for s in sp:
            seen[s] += 1
            if s not in blog: invented.append((sid, s))
        pillars.append({"pillar": c["pillar"].strip(),
                        "intent": c.get("intent", "informational"),
                        "slice": sid, "spokes": sp})
    for s in d.get("orphans", []):
        seen[s] += 1
        orphans.append(s)
        if s not in blog: invented.append((sid, s))

covered = set(seen)
missing = blog - covered
dupes = [s for s, n in seen.items() if n > 1]

# merge pillars with identical normalized title
def norm(t):
    t = re.sub(r"[^a-z0-9 ]", " ", t.lower())
    return " ".join(sorted(t.split()))
merged = {}
for p in pillars:
    k = norm(p["pillar"])
    if k in merged:
        merged[k]["spokes"] += p["spokes"]
        merged[k]["slices"].add(p["slice"])
    else:
        merged[k] = {"pillar": p["pillar"], "intent": p["intent"],
                     "slices": {p["slice"]}, "spokes": list(p["spokes"])}
final = list(merged.values())
for p in final:
    p["spokes"] = sorted(set(p["spokes"]))
    p["n"] = len(p["spokes"])
    p["slices"] = sorted(p["slices"])
final.sort(key=lambda p: -p["n"])

oversized = [p for p in final if p["n"] > 15]

print(f"blog slugs:            {len(blog)}")
print(f"covered:               {len(covered)}  (missing {len(missing)}, dupes {len(dupes)})")
print(f"invented slugs:        {len(invented)}")
print(f"raw pillars:           {len(pillars)}")
print(f"after title-merge:     {len(final)} pillars")
print(f"orphans:               {len(orphans)}")
print(f"oversized (>15):       {len(oversized)}")
if missing: print("  MISSING sample:", list(missing)[:10])
if invented: print("  INVENTED sample:", invented[:10])
if dupes: print("  DUPLICATE sample:", dupes[:10])
if oversized: print("  OVERSIZED:", [(p['pillar'], p['n'], p['slices']) for p in oversized][:20])

json.dump({"pillars": final, "orphans": sorted(set(orphans))},
          open("data/fine-clusters.json", "w"), indent=2)
print("\nwrote data/fine-clusters.json")
print(f"\nsize distribution: "
      f">=10: {sum(1 for p in final if p['n']>=10)}, "
      f"7-9: {sum(1 for p in final if 7<=p['n']<=9)}, "
      f"4-6: {sum(1 for p in final if 4<=p['n']<=6)}, "
      f"3: {sum(1 for p in final if p['n']==3)}")
