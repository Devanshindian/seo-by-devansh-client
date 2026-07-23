#!/usr/bin/env python3
"""Step 4 (thinking) — turn the raw SERP extract into the SERP-snapshot section + the Step-5 read-list.

Reads:  <run_dir>/proof/04-serp-extract.json (from s4_serp.py) + asset title + distinct angle + primary keyword.
Writes: <run_dir>/proof/04-serp-snapshot.md · 04-pages-to-read.txt (the 3 vetted URLs Step 5 opens).
"""
import os, sys, json, argparse
import config, llm

SNAP = llm.load_prompt("serp-snapshot.md")


def _readlist(text):
    """Pull the fenced ```readlist block the prompt appends; fall back to any http lines."""
    urls = []
    if "```readlist" in text:
        block = text.split("```readlist", 1)[1].split("```", 1)[0]
        urls = [l.strip() for l in block.splitlines() if l.strip().startswith("http")]
    return urls[:config.PAGES_TO_READ]


def run(run_dir, asset, angle, primary):
    proof = os.path.join(run_dir, "proof")
    extract = json.load(open(os.path.join(proof, "04-serp-extract.json")))
    p = (SNAP.replace("{{BRAND}}", config.BRAND).replace("{{DOMAIN}}", config.DOMAIN)
         .replace("{{ASSET_TOPIC}}", asset)
         .replace("{{DISTINCT_ANGLE}}", angle).replace("{{PRIMARY_KEYWORD}}", primary)
         .replace("{{SERP_EXTRACT}}", json.dumps(extract, indent=2)))
    text = llm.call_text(p)

    urls = _readlist(text)
    if not urls:  # fallback: raw top-3 organic
        urls = [r["url"] for r in extract.get("top_organic", []) if r.get("url")][:config.PAGES_TO_READ]
    md = text.split("```readlist")[0].rstrip()   # strip the machine block from the human doc
    config.write_text(os.path.join(proof, "04-serp-snapshot.md"), md + "\n")
    config.write_text(os.path.join(proof, "04-pages-to-read.txt"), 
        "# Step 4 read-list — top relevant, readable articles (exact extract URLs)\n" + "\n".join(urls) + "\n")
    print(f"  -> 04-serp-snapshot.md · read-list: {len(urls)} URLs")
    return urls


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--asset", required=True)
    ap.add_argument("--angle", default=""); ap.add_argument("--primary", required=True)
    a = ap.parse_args()
    run(a.run_dir, a.asset, a.angle, a.primary)
