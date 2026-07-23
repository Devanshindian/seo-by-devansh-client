#!/usr/bin/env python3
"""Merge live-probe results and classify each pillar: built / partial / missing,
based on where its best candidate hub URL actually resolves."""
import csv, json, glob, collections

blog = set(l.strip().rstrip("/") for l in open("data/blog-urls.txt") if l.strip())

# merge probe results, best code wins (200 > 404 > other)
best = {}
def add(fn):
    try: rows = list(csv.reader(open(fn), delimiter="\t"))
    except FileNotFoundError: return
    for r in rows:
        if len(r) < 3: continue
        slug, code, url = r[0], r[1], r[2]
        rank = {"200": 3, "404": 2}.get(code, 1)
        if slug not in best or rank > best[slug][0]:
            best[slug] = (rank, code, url)
for fn in ["data/probe/results.tsv", "data/probe/results-retry.tsv", "data/probe/results-retry2.tsv"]:
    add(fn)

def kind(slug):
    if slug not in best: return ("unknown", None)
    _, code, url = best[slug]
    u = url.rstrip("/")
    if code != "200": return ("dead", None)
    if u in ("https://testlify.com", "http://testlify.com"): return ("dead", None)  # bounced to homepage
    if "/hr-glossary/" in u: return ("glossary", u)
    if "/hr-tools/" in u: return ("tools", u)
    if u in blog: return ("post", u)
    if u.endswith("-alternatives") or u.endswith("-alternative"): return ("alternatives", u)
    return ("page", u)

# load candidate slugs per pillar
cand = {}  # (key,pillar) -> [slugs]
for fn in glob.glob("data/probe/in/c*.json"):
    d = json.load(open(fn))
    for c in d["candidates"]:
        cand[(d["key"], c["pillar"])] = [s.strip().strip("/") for s in c["slugs"]]

# theme order + names
final = json.load(open("data/final-clusters.json"))
themes = list(final["themes"].keys())
keymap = {f"c{i+1:02d}": th for i, th in enumerate(themes)}

# A topical cornerstone article (post) ranks above a generic glossary/tools proxy.
PRIORITY = {"page": 5, "alternatives": 5, "post": 4, "glossary": 3, "tools": 3, "dead": 1, "unknown": 0}
# interview-questions-bank is functionally a hub even though WP serves it as a post
HUB_POSTS = {"https://testlify.com/interview-questions-bank"}
def status_of(k, url):
    if k in ("page", "alternatives"): return "built"
    if k == "post" and url and url.rstrip("/") in HUB_POSTS: return "built"
    if k in ("glossary", "tools"): return "partial"
    if k == "post": return "article"
    return "missing"

out = collections.OrderedDict()
tally = collections.Counter()
for i, th in enumerate(themes):
    key = f"c{i+1:02d}"
    pills = []
    for p in final["themes"][th]["pillars"]:
        slugs = cand.get((key, p["pillar"]), [])
        results = [(kind(s), s) for s in slugs]
        # pick best by priority
        best_k = max(results, key=lambda x: PRIORITY[x[0][0]]) if results else (("unknown", None), None)
        (k, url), matched_slug = best_k
        st = status_of(k, url)
        tally[st] += 1
        pills.append({"pillar": p["pillar"], "n": p["n"], "status": st, "kind": k,
                      "hub_url": url, "probe_slug": matched_slug})
    out[th] = {"pillars": pills,
               "built": sum(1 for x in pills if x["status"]=="built"),
               "article": sum(1 for x in pills if x["status"]=="article"),
               "partial": sum(1 for x in pills if x["status"]=="partial"),
               "missing": sum(1 for x in pills if x["status"]=="missing")}

json.dump({"themes": out, "tally": dict(tally)}, open("data/coverage-final.json", "w"), indent=2)

print("=== LIVE COVERAGE (373 pillars) ===")
print(f"  built   (dedicated hub page):        {tally['built']}")
print(f"  article (cornerstone post, no hub):  {tally['article']}")
print(f"  partial (glossary/tools proxy only): {tally['partial']}")
print(f"  missing (nothing / 404):             {tally['missing']}")
print()
print(f"{'theme':<40} {'built':>5} {'art':>5} {'part':>5} {'miss':>5}")
for th, v in out.items():
    print(f"{th:<40} {v['built']:>5} {v['article']:>5} {v['partial']:>5} {v['missing']:>5}")
