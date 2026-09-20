#!/usr/bin/env python3
"""7-writer-brief settings. Company-agnostic — set COMPANY per company; every path derives from one anchor.

The engine is the runnable twin of writer-brief.workflow.md: read the brand pack's rule-carrying files,
classify every section by three questions (whose job · universal or company · rule or fact), find the
places two files contradict each other, then assemble the one small file the body writer actually reads.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                  # .../7-writer-brief
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

BRAND_CTX = os.path.join(_PROJ, "01-brand-context")
WORK = os.path.join(BRAND_CTX, "_work", "writer-brief")
OUT_MD = os.path.join(BRAND_CTX, "writer-brief.md")   # THE deliverable — written in place; git diff is
# the review surface. (A separate _drafts copy meant a human had to remember to promote it, and that step
# was forgotten for 5 of 6 builders — Devansh, 2026-07-20.)

PROMPTS = os.path.join(ROOT, "prompts")
RECIPE_MD = os.path.join(ROOT, "writer-brief.workflow.md")     # the template lives here (lifted verbatim)

# --- which brand files carry WRITING RULES -----------------------------------------------------------
# Only these are read. Each exclusion below is a decision, not an oversight:
#   stats.md, stories.md  -> statistics and customer stories. Facts, not rules about writing.
#   features.md           -> a product catalogue. Not rules about writing.
#   persona.md            -> describes the reader, not the company's own voice.
#   writing-examples.md   -> five complete published articles. Whole finished pages, not rules.
#   opinions.md           -> an empty template with no opinions recorded in it.
SOURCE_FILES = ["brand-voice.md", "style-guide.md", "voices.md", "writing-integrity.md"]

# Decisions a human made that cannot be worked out from the source files. Optional, hand-written, short —
# where two files simply disagree, Step 2 resolves it on its own. It is COMPANY content, so it lives under
# projects/ with the rest of the brand context, never in this tool folder (Part A1: the tool is generic,
# the output is per-company, and the two never mix). templates/rulings.md is the blank to copy.
RULINGS_MD = os.environ.get("WB_RULINGS", os.path.join(BRAND_CTX, "writer-brief-rulings.md"))

MAX_WORKERS = int(os.environ.get("WB_WORKERS", "4"))        # one classify call per source file, in parallel
SECTION_CHAR_CAP = int(os.environ.get("WB_SECTION_CAP", "40000"))   # per source file into a classify prompt

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "claude")
LLM_MODEL = os.environ.get("LLM_MODEL", "")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "600"))
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
