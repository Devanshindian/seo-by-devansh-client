#!/usr/bin/env python3
"""8-brand-cards settings. Company-agnostic — set COMPANY per company; every path derives from one anchor.

The engine is the runnable twin of brand-cards.workflow.md: turn the company's own material — its
research findings and its customer results — into cards in the same shape as any other card, so a use
of one carries its source the same way.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                  # .../8-brand-cards
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
WORK = os.path.join(BRAND_CTX, "_work", "brand-cards")
OUT_JSON = os.path.join(BRAND_CTX, "brand-cards.json")   # THE deliverable

PROMPTS = os.path.join(ROOT, "prompts")

# --- the two sources ---------------------------------------------------------------------------------
# RESEARCH = the company's own study: neutral data about its market, safe to cite widely.
# RESULTS  = what a named customer achieved using the product: the company's own proof about itself.
# They are kept apart all the way through, because downstream they are rationed differently.
RESEARCH_MD = os.path.join(BRAND_CTX, "stats.md")
RESULTS_MD = os.path.join(BRAND_CTX, "stories.md")

# Card ids live in reserved bands so a card's origin is readable from its number alone:
#   1..999   research cards from the article's own gathering
#   8001+    THIS engine (the company's own material)
#   9001+    the architect's enrichment step
ID_BASE = int(os.environ.get("BC_ID_BASE", "8001"))

# Where the research is published, if it is. Empty means the cards carry a written citation but no link,
# which is correct for an unpublished report — do NOT invent a URL to fill this.
RESEARCH_URL = os.environ.get("BC_RESEARCH_URL", "")

BATCH_SECTIONS = int(os.environ.get("BC_BATCH", "3"))   # research sections per extraction call

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


def write_json(path, data, indent=1):
    import json
    write_text(path, json.dumps(data, indent=indent, ensure_ascii=False))
