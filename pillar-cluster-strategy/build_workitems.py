#!/usr/bin/env python3
"""Partition the 2,972 blog slugs into coherent work-slices for LLM subagents.
Each slice = a thematically-related chunk (<=180 slugs) written to data/work/wNN.txt.
Also writes data/work/manifest.json describing every slice."""
import csv, json, os, re, collections

rows = [r for r in csv.DictReader(open("data/url-clusters.csv")) if r["type"] == "blog"]

# group by (coarse cluster, subcluster) — used only to keep related posts together
groups = collections.defaultdict(list)
for r in rows:
    groups[(r["cluster"], r["subcluster"] or "general")].append(r["slug"])

def role_key(s):
    """Normalize interview-question slugs so same-domain roles sort adjacently."""
    k = s
    for junk in ["interview-questions-for-", "-interview-questions", "interview-questions",
                 "-to-ask-job-applicants", "-to-ask", "questions-for-", "-questions",
                 "top-", "best-", "common-", "essential-", "important-"]:
        k = k.replace(junk, "")
    return k.strip("-")

os.makedirs("data/work", exist_ok=True)
# clear old
for f in os.listdir("data/work"):
    os.remove(os.path.join("data/work", f))

CHUNK = 150
manifest = []
wid = 0
for (cluster, sub), slugs in sorted(groups.items(), key=lambda x: -len(x[1])):
    # sort for coherence
    if "Interview Questions" in cluster:
        slugs = sorted(slugs, key=role_key)
    else:
        slugs = sorted(slugs)
    # chunk
    n = len(slugs)
    nchunks = max(1, (n + CHUNK - 1) // CHUNK)
    size = (n + nchunks - 1) // nchunks
    for i in range(0, n, size):
        wid += 1
        chunk = slugs[i:i + size]
        part = f" (part {i//size+1}/{nchunks})" if nchunks > 1 else ""
        name = f"w{wid:02d}"
        with open(f"data/work/{name}.txt", "w") as f:
            f.write(f"# coarse-theme: {cluster} > {sub}{part}\n")
            for j, s in enumerate(chunk, 1):
                f.write(f"{j}\t{s}\n")
        manifest.append({"id": name, "theme": f"{cluster} > {sub}{part}",
                         "n": len(chunk), "file": f"data/work/{name}.txt"})

json.dump(manifest, open("data/work/manifest.json", "w"), indent=2)
print(f"{len(manifest)} work-slices, {sum(m['n'] for m in manifest)} slugs total")
for m in manifest:
    print(f"  {m['id']}: {m['n']:4d}  {m['theme']}")
