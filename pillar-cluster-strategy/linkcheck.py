#!/usr/bin/env python3
"""For each 'built' pillar, check whether its hub page actually links to its cluster's
spoke posts. Parses fetched hub HTML, extracts testlify links, intersects with spokes."""
import json, re, os, collections

built = json.load(open("data/linkcheck-built.json"))
hubs = [l.strip() for l in open("data/linkcheck-hubs.txt") if l.strip()]

# map hub URL -> fetched file (written in sorted order h01..hNN)
hubfile = {}
for i, u in enumerate(hubs, 1):
    fn = f"data/hubhtml/h{i:02d}.html"
    if os.path.exists(fn): hubfile[u] = fn

href_re = re.compile(r'href=["\']([^"\']+)["\']', re.I)
def links_of(fn):
    html = open(fn, encoding="utf-8", errors="ignore").read()
    out = set()
    for h in href_re.findall(html):
        h = h.split("#")[0].split("?")[0]
        m = re.match(r'^(?:https?://(?:www\.)?testlify\.com)?/([^/][^"\']*?)/?$', h)
        if m:
            slug = m.group(1).strip("/")
            if slug and "/" not in slug:   # top-level slug = a post or page
                out.add(slug)
    return out

hub_links = {u: links_of(fn) for u, fn in hubfile.items()}

rows = []
for b in built:
    hub = b["hub"]
    linked = hub_links.get(hub, set())
    spokes = set(b["spokes"])
    matched = sorted(spokes & linked)
    rows.append({**b, "n_spokes": len(spokes), "n_linked": len(matched),
                 "pct": round(100*len(matched)/len(spokes)), "matched": matched,
                 "total_blog_links_on_hub": len(linked)})

# verdict per pillar
def verdict(r):
    if r["n_linked"] == 0: return "hub_orphaned"      # hub exists but links to 0 of its cluster
    if r["pct"] >= 40 or r["n_linked"] >= 5: return "true_pillar"
    return "weakly_linked"                              # links to a few
for r in rows: r["verdict"] = verdict(r)

json.dump(rows, open("data/linkcheck-results.json", "w"), indent=2)

tally = collections.Counter(r["verdict"] for r in rows)
print("=== Do the 110 'built' hubs actually link to their cluster posts? ===")
print(f"  true_pillar   (links to a real share of its spokes): {tally['true_pillar']}")
print(f"  weakly_linked (links to only 1–few spokes):          {tally['weakly_linked']}")
print(f"  hub_orphaned  (links to ZERO of its spokes):         {tally['hub_orphaned']}")
print()
# show how many blog links each unique hub even has
print("=== outbound top-level links per hub page (does it link to blog posts at all?) ===")
seen=set()
for r in sorted(rows, key=lambda x:-x['total_blog_links_on_hub']):
    if r['hub'] in seen: continue
    seen.add(r['hub'])
    print(f"  {r['total_blog_links_on_hub']:4d} links  {r['hub'].replace('https://testlify.com/','')}")
print()
print("=== sample: pillars whose hub links to some of their spokes (true_pillar) ===")
for r in [x for x in rows if x['verdict']=='true_pillar'][:12]:
    print(f"  {r['n_linked']}/{r['n_spokes']} ({r['pct']}%)  {r['pillar']}  <- {r['hub'].replace('https://testlify.com/','')}")
