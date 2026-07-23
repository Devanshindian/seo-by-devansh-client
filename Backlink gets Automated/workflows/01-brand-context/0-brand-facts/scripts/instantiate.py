#!/usr/bin/env python3
"""Step 1 — instantiate the three brand-facts templates for this company.

Reads:  templates/stats.md · opinions.md · stories.md ({{BRAND}}/{{NICHE}} slots) + the company record.
Writes: BRAND_CTX/stats.md · opinions.md · stories.md — ONLY IF MISSING. An existing file is SEED
        (human-confirmed answers) and is NEVER overwritten; the step reports it and moves on.
"""
import os
import config

FILES = ["stats.md", "opinions.md", "stories.md"]


def run():
    made, kept = [], []
    for name in FILES:
        target = os.path.join(config.BRAND_CTX, name)
        if os.path.exists(target):
            kept.append(name)                       # seed protection: never overwrite
            continue
        with open(os.path.join(config.TEMPLATES, name)) as f:
            body = f.read()
        body = body.replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE or "the niche")
        config.write_text(target, body)
        made.append(name)
    if made:
        print(f"   instantiated: {', '.join(made)}")
    if kept:
        print(f"   kept (already exist — SEED, never overwritten): {', '.join(kept)}")
    return made


if __name__ == "__main__":
    run()
