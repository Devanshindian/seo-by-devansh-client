#!/usr/bin/env python3
"""Step 0 (thinking) — anchors + seeds + competitor URLs, from the clubbed-ideas row. No free brainstorm.

Reads:  config.CLUBBED_CSV, matching the row whose Asset contains <asset_match>.
Writes: <run_dir>/proof/00-seeds.md · 00-competitor-urls.txt
Returns: {asset, angle, head_seeds[], sibling_seeds[], competitor_urls[]} for the runner to hand downstream.
"""
import os, sys, csv, json, argparse
import config, llm

SEEDS = llm.load_prompt("seeds.md")


def _find_row(asset_match):
    with open(config.CLUBBED_CSV, newline="") as f:
        hits = [r for r in csv.DictReader(f) if asset_match.lower() in (r.get("Asset") or "").lower()]
    if not hits:
        sys.exit(f"no clubbed row Asset contains {asset_match!r}")
    if len(hits) > 1:
        sys.exit(f"{len(hits)} clubbed rows match {asset_match!r} — narrow the --asset match string")
    return hits[0]


def run(run_dir, asset_match=None, asset=None, angle=None, world=None):
    """Hub mode: pass asset_match → looks the row up in clubbed (asset+angle+proof URLs from there).
    Direct mode (spoke — not in clubbed): pass asset + angle directly; no proof URLs (ranked-net uses SERP links)."""
    if asset:   # direct / spoke mode
        asset, angle, raw_urls = asset.strip(), (angle or "").strip(), []
    else:       # hub mode — look it up in the clubbed CSV by title
        row = _find_row(asset_match)
        asset = (row.get("Asset") or "").strip()
        angle = (row.get("Distinct angle") or "").strip()
        raw_urls = [u.strip() for u in (row.get("Proof URLs") or "").split(";") if u.strip()]

    world = world or {}
    p = (SEEDS.replace("{{BRAND}}", config.BRAND).replace("{{NICHE_DEFINITION}}", config.NICHE_DEFINITION)
         .replace("{{ASSET_TOPIC}}", asset)
         .replace("{{DISTINCT_ANGLE}}", angle)
         .replace("{{ABOUT}}", world.get("about") or "(not available for this run)")
         .replace("{{NOT_ABOUT}}", world.get("not_about") or "(not available for this run)")
         .replace("{{PROOF_URLS}}", "\n".join(raw_urls)))
    seeds = llm.call_json(p)
    head = seeds.get("head_seeds", []); sib = seeds.get("sibling_seeds", []); hyg = seeds.get("hygiene", "")
    # keep only the on-angle URLs the LLM returned; guard against hallucinated URLs (must be in the raw list)
    comp_urls = [u for u in seeds.get("competitor_urls", []) if u in raw_urls] or raw_urls

    proof = os.path.join(run_dir, "proof"); os.makedirs(proof, exist_ok=True)
    md = ["# Step 0 — anchors + seeds", "",
          "## Asset title (verbatim → {asset_topic})", asset, "",
          "## Distinct angle (verbatim → {distinct_angle})", angle, "",
          "## Head seeds (from title)", "; ".join(head), "",
          "## Sibling seeds (from distinct angle)", "; ".join(sib), "",
          "## Seed hygiene", hyg, ""]
    config.write_text(os.path.join(proof, "00-seeds.md"), "\n".join(md))
    config.write_text(os.path.join(proof, "00-competitor-urls.txt"), "\n".join(comp_urls) + "\n")
    out = {"asset": asset, "angle": angle, "head_seeds": head, "sibling_seeds": sib,
           "hygiene": hyg, "competitor_urls": comp_urls}
    config.write_json(os.path.join(proof, "00-anchors.json"), out)   # machine copy for the runner/resume

    print(f"  asset: {asset[:70]}")
    print(f"  seeds: {len(head)} head + {len(sib)} sibling · {len(comp_urls)} competitor URLs")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--asset", required=True, help="hub: substring matching the clubbed Asset · spoke: the full title")
    ap.add_argument("--angle", default=None, help="spoke/direct mode: the angle (skips the clubbed lookup)")
    a = ap.parse_args()
    out = run(a.run_dir, asset=a.asset, angle=a.angle) if a.angle else run(a.run_dir, asset_match=a.asset)
    print(json.dumps(out, indent=2))
