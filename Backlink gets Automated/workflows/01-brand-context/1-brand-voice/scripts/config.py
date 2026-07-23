#!/usr/bin/env python3
"""1-brand-voice settings. Company-agnostic — set COMPANY per company; every path derives from one anchor.

The engine is the runnable twin of brand-voice.workflow.md: shortlist the voice pages (LLM picks, script
fetches bodies from the catalogue), read each page into an evidence row (LLM per page), assemble the
brand-voice document from the evidence (LLM, pure assembly per the recipe's mapping), then a quality gate
vs Appendix A's completeness/depth bar (LLM judge, looped). The draft NEVER overwrites brand-voice.md —
promotion is the human gate.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))            # .../1-brand-voice/scripts
ROOT = os.path.dirname(HERE)                                  # .../1-brand-voice
LAYER = os.path.dirname(ROOT)                                 # .../01-brand-context
REPO_ROOT = os.path.dirname(os.path.dirname(LAYER))           # .../Backlink gets Automated

COMPANY = os.environ.get("COMPANY", "")
if not COMPANY:
    raise SystemExit("!! COMPANY is not set. Run as: COMPANY=<slug> ... — this tool has no default company.")
_PROJ = os.path.join(REPO_ROOT, "projects", COMPANY)

import json as _json, sys as _sys
_record_path = os.path.join(_PROJ, "company.json")
try:
    with open(_record_path) as _f:
        TENANT = _json.load(_f)
except FileNotFoundError:
    _sys.exit(f"!! no company record at {_record_path} — create it before running (see workflows/company-record.md)")
BRAND = TENANT.get("brand") or _sys.exit("!! company record has no 'brand'")
NICHE = TENANT.get("niche_definition", "")
DOMAIN = TENANT.get("domain") or _sys.exit("!! company record has no 'domain'")

# --- inputs (Layer 00) -------------------------------------------------------
CATALOGUE_CSV = os.path.join(_PROJ, "00-foundation", "output", "content-database.csv")
TOP_PAGES_CSV = os.path.join(_PROJ, "00-foundation", "output", "top-pages.csv")

# --- outputs -----------------------------------------------------------------
BRAND_CTX = os.path.join(_PROJ, "01-brand-context")
SHORTLIST_MD = os.path.join(BRAND_CTX, "page-shortlist.md")   # the picked pages (reused if it exists)
PAGES_DIR = os.path.join(BRAND_CTX, "_pages")                 # saved page bodies (from the catalogue — no refetch)
WORK = os.path.join(BRAND_CTX, "_work", "brand-voice")        # evidence.json · gate verdicts · oneliner draft
DRAFT_MD = os.path.join(BRAND_CTX, "brand-voice.md")   # THE deliverable — written in place;
# git diff is the review surface. (A separate _drafts copy meant a human had to remember to
# promote it, and that step was forgotten for 5 of 6 builders — Devansh, 2026-07-20.)

PROMPTS = os.path.join(ROOT, "prompts")
RECIPE_MD = os.path.join(ROOT, "brand-voice.workflow.md")     # Appendix A (schema) + Step-2 mapping live here

# --- shortlist knobs ---------------------------------------------------------
SHORTLIST_MIN, SHORTLIST_MAX = 20, 40      # the recipe's page-count band
CAND_TOP_TRAFFIC = int(os.environ.get("BV_CAND_TOP", "80"))   # top-traffic candidates shown to the picker
CAND_COMMERCIAL = int(os.environ.get("BV_CAND_COMM", "300"))  # commercial candidates shown; ALL shallow ones always make it (the ones raw traffic misses)
THIN_WORDS = 150                            # a saved page under this = thin; fall back to the catalogue body

# --- read/assemble knobs -----------------------------------------------------
BODY_CHAR_CAP = int(os.environ.get("BV_BODY_CAP", "14000"))   # chars of one page body per evidence prompt
GATE_MAX_ROUNDS = int(os.environ.get("BV_GATE_ROUNDS", "3"))  # assemble->gate loop cap (the recipe loops until pass)
WORKERS = int(os.environ.get("BV_WORKERS", "4"))              # concurrent CLI calls in the read step

# --- LLM (headless CLI — Claude Code or Codex) -------------------------------
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "claude")
LLM_MODEL = os.environ.get("LLM_MODEL", "")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "420"))    # assemble reads ~30 evidence rows — give it room
LLM_RETRIES = 1


# ---- atomic output writes (crash-safe) --------------------------------------
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
def write_json(path, data, indent=2):
    _json_mod = _json
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = _tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            _json_mod.dump(data, f, indent=indent)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try: os.remove(tmp)
        except OSError: pass
        raise
