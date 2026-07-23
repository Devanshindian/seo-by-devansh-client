#!/usr/bin/env python3
"""
Rebuild the review viewer (index.html) from clubbed-ideas-review.csv, reusing the
existing HTML/CSS/JS shell and only swapping the `const DATA = [...]` array.
Writes both the published copy (output/_pages-repo/index.html) and the local standalone.

Run from the asset-engine/clubbed dir (or pass it as argv[1]).
"""
import csv, json, re, sys, os
csv.field_size_limit(1 << 24)

B = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else "."
REVIEW = os.path.join(B, "output", "clubbed-ideas-review.csv")
PAGES = os.path.join(B, "output", "_pages-repo", "index.html")     # template + published output (same file)
LOCAL = os.path.join(B, "output", "clubbed-ideas-review.html")     # local standalone copy

def parse_rag(cell):
    out = []
    for seg in (cell or "").split(";"):
        seg = seg.strip()
        if not seg:
            continue
        m = re.match(r'^(.*?) — (https?://\S+) \(([\-\d.]+)\)$', seg)
        if m:
            out.append({"title": m.group(1), "url": m.group(2), "score": m.group(3)})
        else:
            mu = re.search(r'(https?://\S+)', seg)
            out.append({"title": seg, "url": mu.group(1) if mu else "", "score": ""})
    return out

def urls(cell):
    return [u.strip() for u in (cell or "").split(";") if u.strip()]

def parse_cat(cell):   # "Title — url; Title — url" -> rag-like objects (no score)
    out = []
    for seg in (cell or "").split(";"):
        seg = seg.strip()
        if not seg:
            continue
        m = re.match(r'^(.*?) — (https?://\S+)$', seg)
        if m:
            out.append({"title": m.group(1), "url": m.group(2), "score": ""})
    return out

data = []
for i, r in enumerate(csv.DictReader(open(REVIEW, encoding="utf-8"))):
    data.append({
        "i": i, "src": r["Source method"], "fit": r["Brand fit"], "asset": r["Asset"],
        "format": r["Format"], "angle": r["Distinct angle"], "domains": r["Total domains"],
        "comps": r["# comps"], "posts": r["# posts"], "beat": r["Beatability"], "effort": r["Effort"],
        "verdict": r["Reuse verdict"], "why": r["Why"],
        "rag": parse_rag(r["RAG candidates"]), "chosen": urls(r["Chosen links"]), "proof": urls(r["Proof URLs"]),
        "cat": parse_cat(r.get("Topic pages we own", "")),
    })

blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")   # safe to inline in <script>
lines = open(PAGES, encoding="utf-8").read().split("\n")
for idx, l in enumerate(lines):
    if l.startswith("const DATA ="):
        lines[idx] = "const DATA = " + blob + ";"
        break
else:
    sys.exit("could not find 'const DATA =' line in template")
html = "\n".join(lines)
open(PAGES, "w", encoding="utf-8").write(html)
open(LOCAL, "w", encoding="utf-8").write(html)
print(f"rebuilt viewer with {len(data)} ideas  ({len(html)/1e6:.2f} MB)")
