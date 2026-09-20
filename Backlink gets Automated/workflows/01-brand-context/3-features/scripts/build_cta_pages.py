#!/usr/bin/env python3
"""THE CTA PAGES — the short list of product pages a call to action is allowed to link to.

  COMPANY=<slug> python3 build_cta_pages.py

Reads:  _work/features/facts.json + source-pages.json   (both already written by run_features.py)
Writes: 01-brand-context/cta-pages.md

WHY THIS IS A SEPARATE FILE FROM features.md.
features.md is prose: what we sell and why it matters, written by a model for a writer to read.
This is a lookup: which URL a capability points at. The writer needs both, and they fail
differently — a clumsy sentence in features.md costs nothing, a wrong URL in a call to action
sends a reader to the wrong page. So this one is built by CODE from the crawl, never by a model,
and it can be regenerated in a second without a paid rerun.

WHY IT IS FILTERED, NOT RANKED BY TRAFFIC.
The single highest-traffic product page on testlify.com is a bricklayer test (1,198 a month). It
is a real page and a terrible thing to end an article about interview costs with. Traffic finds
the page people land on; it cannot tell you which page a reader who just finished THIS article
should go to next. So the rules below are about SHAPE — hub pages in, leaf pages out — and the
traffic number is carried through only as a tie-breaker the writer can see.
"""
import argparse
import json
import os
import re

import config

# A leaf page sells one test to one role. A CTA wants the hub above it.
LEAF = ("/test-library/",)

# Kinds worth linking from a close. Competitor comparisons are deliberately absent: they belong in
# a comparison article's own body, chosen by the links step, not bolted onto every article's ending.
KINDS = ("homepage", "product or feature page", "pricing / plans / compare")

# Localised and superseded duplicates of a page we already list.
SKIP = re.compile(r"/(compare-planos|comparer-les-plans|pricing-new|compare-testlify-vs-)", re.I)

# A page whose URL reads like an article, not a product. The crawler files some of these as product
# pages because they carry a product CTA block.
ARTICLEY = re.compile(r"interview-questions|-to-ask-|how-to-|top-\d", re.I)


def build():
    work = config.WORK
    facts = json.load(open(os.path.join(work, "facts.json")))
    pages = {p["url"]: p for p in json.load(open(os.path.join(work, "source-pages.json")))}

    rows, dropped = [], []
    for f in facts:
        url, kind = f.get("url", ""), f.get("kind", "")
        why = None
        if kind not in KINDS:
            why = f"kind is {kind}"
        elif any(x in url for x in LEAF):
            why = "leaf page — one test for one role"
        elif SKIP.search(url):
            why = "localised or superseded duplicate"
        elif ARTICLEY.search(url):
            why = "reads as an article, not a product page"
        if why:
            dropped.append((url, why))
            continue
        p = pages.get(url, {})
        feats = [x for x in (f.get("features") or []) if x.strip()][:3]
        rows.append({"url": url, "title": (p.get("title") or "").strip(),
                     "traffic": int(p.get("traffic") or 0), "kind": kind, "features": feats})

    rows.sort(key=lambda r: (r["kind"] != "homepage", -r["traffic"]))

    out = [f"# {config.BRAND} — pages a call to action may link to", "",
           "Built by code from the site crawl. Every URL here was fetched and is live.",
           "The close of an article links to ONE of these and nothing else.", "",
           f"{len(rows)} pages. {len(dropped)} candidates were dropped; the reasons are at the foot.", ""]
    for r in rows:
        out.append(f"## {r['title'] or r['url']}")
        out.append(f"- Page: {r['url']}")
        out.append(f"- Kind: {r['kind']}  ·  {r['traffic']:,} visits a month")
        for x in r["features"]:
            out.append(f"- {x}")
        out.append("")
    out += ["---", "", "## Dropped, and why", ""]
    out += [f"- {u}  — {w}" for u, w in dropped[:60]]
    if len(dropped) > 60:
        out.append(f"- ... and {len(dropped)-60} more")

    dest = os.path.join(config.BRAND_CTX, "cta-pages.md")
    config.write_text(dest, "\n".join(out) + "\n")
    print(f"  -> {dest}  ({len(rows)} linkable page(s), {len(dropped)} dropped)")
    for r in rows:
        print(f"     {r['traffic']:>6,}  {r['url']}")
    return dest


if __name__ == "__main__":
    argparse.ArgumentParser(description="Build the CTA page list from the crawl.").parse_args()
    build()
