#!/usr/bin/env python3
"""2-style-guide settings. Company-agnostic — set COMPANY per company; every path derives from one anchor.

The engine is the runnable twin of style-guide.workflow.md: pick the top editorial blogs (script, via the
classified editorial types), analyze them in batches (LLM per batch — the recipe's 3 sub-agents), fill the
recipe's template (LLM; the template is lifted VERBATIM from the recipe MD). Draft only — promotion is human.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                  # .../2-style-guide
LAYER = os.path.dirname(ROOT)                                 # .../01-brand-context
REPO_ROOT = os.path.dirname(os.path.dirname(LAYER))

COMPANY = os.environ.get("COMPANY", "")
if not COMPANY:
    raise SystemExit("!! COMPANY is not set. Run as: COMPANY=<slug> ...")
_PROJ = os.path.join(REPO_ROOT, "projects", COMPANY)

import json as _json, sys as _sys
try:
    with open(os.path.join(_PROJ, "company.json")) as _f:
        TENANT = _json.load(_f)
except FileNotFoundError:
    _sys.exit(f"!! no company record for '{COMPANY}' — create projects/{COMPANY}/company.json first")
BRAND = TENANT.get("brand") or _sys.exit("!! company record has no 'brand'")
NICHE = TENANT.get("niche_definition", "")
LANGUAGE = (TENANT.get("language") or "en")[:2]

CATALOGUE_CSV = os.path.join(_PROJ, "00-foundation", "output", "content-database.csv")
BRAND_CTX = os.path.join(_PROJ, "01-brand-context")
TYPE_ROLES = os.path.join(BRAND_CTX, "_work", "type-roles.json")   # from 0-brand-facts step 0
WORK = os.path.join(BRAND_CTX, "_work", "style-guide")
DRAFT_MD = os.path.join(BRAND_CTX, "style-guide.md")   # THE deliverable — written in place;
# git diff is the review surface. (A separate _drafts copy meant a human had to remember to
# promote it, and that step was forgotten for 5 of 6 builders — Devansh, 2026-07-20.)

PROMPTS = os.path.join(ROOT, "prompts")
RECIPE_MD = os.path.join(ROOT, "style-guide.workflow.md")          # the template lives here (lifted verbatim)

TOP_BLOGS = int(os.environ.get("SG_TOP_BLOGS", "30"))
BATCHES = int(os.environ.get("SG_BATCHES", "3"))
BODY_CHAR_CAP = int(os.environ.get("SG_BODY_CAP", "9000"))         # per blog inside a batch prompt

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "claude")
LLM_MODEL = os.environ.get("LLM_MODEL", "")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "420"))
LLM_RETRIES = 1

import tempfile as _tempfile
def write_text(path, text):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = _tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try: os.remove(tmp)
        except OSError: pass
        raise
