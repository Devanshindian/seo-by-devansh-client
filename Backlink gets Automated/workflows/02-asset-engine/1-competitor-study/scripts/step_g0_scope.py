#!/usr/bin/env python3
"""Step G0 — distil the one-page brand scope every G2 agent reasons against. THEN STOP (human gate).

Reads:  brand-context/brand-voice.md + features.md (+ stats.md / opinions.md for extra signal)
        company.json (the one-liner + niche definition)
Writes: output/brand-scope.md

Company-agnostic: every input path comes from config (company is one setting). If a source file is
missing it is simply left out of the prompt — the scope still builds from whatever brand context exists,
so a half-onboarded company degrades gracefully instead of crashing.

⛔ GATE (recipe G0): brand-scope.md is the ONE place a human sets direction. After it is written, show
it to the user and get approval BEFORE running G2. This script writes the file and prints the gate
notice; it does not run anything downstream.
"""
import argparse, json, os, sys
import config as c
sys.path.insert(0, c.SHARED)
import llm


def _read(path):
    return open(path).read().strip() if path and os.path.exists(path) else ""


def run():
    record = _read(os.path.join(c.PROJ, "company.json"))
    voice = _read(os.path.join(c.BRAND_CTX, "brand-voice.md"))
    feats = _read(os.path.join(c.BRAND_CTX, "features.md"))
    extra = "\n\n".join(x for x in (_read(os.path.join(c.BRAND_CTX, "stats.md")),
                                    _read(os.path.join(c.BRAND_CTX, "opinions.md"))) if x)
    if not (voice or feats):
        sys.exit(f"!! no brand-voice.md or features.md under {c.rel(c.BRAND_CTX)} — build Layer 01 first")

    prompt = (llm.load_prompt("g0-brand-scope.md")
              .replace("{{BRAND}}", c.BRAND)
              .replace("{{COMPANY_RECORD}}", record or "(none)")
              .replace("{{BRAND_VOICE}}", voice or "(none)")
              .replace("{{FEATURES}}", feats or "(none)")
              .replace("{{EXTRA}}", extra or "(none)"))
    print(f"   distilling brand scope from voice+features+record ...")
    scope = llm.call_text(prompt).strip()
    # strip stray code fences if the model wrapped the whole doc
    if scope.startswith("```"):
        scope = scope.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    os.makedirs(c.OUT, exist_ok=True)
    path = os.path.join(c.OUT, "brand-scope.md")
    with open(path + ".tmp", "w") as f:
        f.write(scope + "\n")
    os.replace(path + ".tmp", path)
    print(f"\n   -> {c.rel(path)}  ({len(scope.split())} words)\n")
    print("   " + "=" * 68)
    print("   ⛔ GATE: brand-scope.md is the ONE place a human sets direction.")
    print("      READ it, and approve (or edit) it BEFORE running Step G2.")
    print("      G2 (the ~480 reasoning passes) reasons against this anchor — a bad")
    print("      scope wastes the whole run. Nothing downstream has run yet.")
    print("   " + "=" * 68)
    return scope


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    run()
