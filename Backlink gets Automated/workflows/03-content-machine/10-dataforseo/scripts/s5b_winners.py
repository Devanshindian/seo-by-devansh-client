#!/usr/bin/env python3
"""Step 5 (thinking) — turn the parsed competitor pages into the "What the winners cover" section.

Reads:  <run_dir>/proof/05-pages.json (from s5_pages.py) + distinct angle + primary keyword.
Writes: <run_dir>/proof/05-winners.md
"""
import os, sys, json, argparse
import config, llm

WIN = llm.load_prompt("winners.md")


def run(run_dir, angle, primary):
    proof = os.path.join(run_dir, "proof")
    pages = json.load(open(os.path.join(proof, "05-pages.json")))
    p = (WIN.replace("{{BRAND}}", config.BRAND).replace("{{DISTINCT_ANGLE}}", angle)
         .replace("{{PRIMARY_KEYWORD}}", primary).replace("{{PARSED_PAGES}}", json.dumps(pages, indent=2)))
    md = llm.call_text(p)
    config.write_text(os.path.join(proof, "05-winners.md"), md.rstrip() + "\n")
    print("  -> 05-winners.md")
    return md


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--angle", default=""); ap.add_argument("--primary", required=True)
    a = ap.parse_args()
    run(a.run_dir, a.angle, a.primary)
