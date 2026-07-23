#!/usr/bin/env python3
"""6-voices instantiate — drops the voices questionnaire/skeleton into the company's brand-context
IF MISSING (an existing voices.md is the team's answered SEED — never overwritten). Runs at its
SKILL.md stage. The filling is HUMAN (steps 1-4 of the recipe are questions to the team)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(ROOT)))
COMPANY = os.environ.get("COMPANY", "") or sys.exit("!! COMPANY is not set")
import json
try:
    TENANT = json.load(open(os.path.join(REPO_ROOT, "projects", COMPANY, "company.json")))
except FileNotFoundError:
    sys.exit(f"!! no company record for '{COMPANY}'")
target = os.path.join(REPO_ROOT, "projects", COMPANY, "01-brand-context", "voices.md")
if os.path.exists(target):
    print(f"   voices.md exists — SEED, never overwritten: {target}"); sys.exit(0)
body = open(os.path.join(ROOT, "templates", "voices.md")).read().replace("{{BRAND}}", TENANT.get("brand", COMPANY))
os.makedirs(os.path.dirname(target), exist_ok=True)
open(target, "w").write(body)
print(f"   instantiated -> {target}  (now ask the team steps 1-4 and fill it)")
