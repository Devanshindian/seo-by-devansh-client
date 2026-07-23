#!/usr/bin/env python3
"""0-brand-facts settings. Company-agnostic — set COMPANY per company; every path derives from one anchor.

The builder instantiates the three brand-facts templates (stats/opinions/stories) into the company's
brand-context folder, then machine-DRAFTS stats + stories candidates from the site catalogue for a human
to confirm. opinions.md is human-only (the template's question list is the interview).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))            # .../0-brand-facts/scripts
ROOT = os.path.dirname(HERE)                                  # .../0-brand-facts
LAYER = os.path.dirname(ROOT)                                 # .../01-brand-context
REPO_ROOT = os.path.dirname(os.path.dirname(LAYER))           # .../Backlink gets Automated

COMPANY = os.environ.get("COMPANY", "")
if not COMPANY:
    raise SystemExit("!! COMPANY is not set. Run as: COMPANY=<slug> ... — this tool has no default company.")
_PROJ = os.path.join(REPO_ROOT, "projects", COMPANY)

# THE COMPANY RECORD — fail closed: no record, no run (revamp Phase 1.1).
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

# --- inputs ------------------------------------------------------------------
CATALOGUE_CSV = os.path.join(_PROJ, "00-foundation", "output", "content-database.csv")  # layer 00's output

# --- outputs -----------------------------------------------------------------
BRAND_CTX = os.path.join(_PROJ, "01-brand-context")   # the three REAL files live here (SEED once confirmed)
DRAFTS = os.path.join(BRAND_CTX, "_drafts")                           # machine drafts land here — the engine NEVER writes the real files after instantiation
TEMPLATES = os.path.join(ROOT, "templates")
PROMPTS = os.path.join(ROOT, "prompts")

# --- candidate selection (which catalogue pages the LLM reads) --------------
# Defaults chosen on Testlify's page-type mix; env-tunable per company. A Type absent from a company's
# CMS simply yields zero candidates — the step reports that and moves on, never crashes.
STAT_PAGE_TYPES = os.environ.get("BF_STAT_TYPES", "page,certifications").split(",")   # where companies publish their own numbers
STAT_TOP_PAGES = int(os.environ.get("BF_STAT_TOP", "25"))    # cap on `page`-type candidates, by Traffic desc (the homepage is always added)
STORY_PAGE_TYPES = os.environ.get("BF_STORY_TYPES", "successstory,press-release,podcast").split(",")
BODY_CHAR_CAP = int(os.environ.get("BF_BODY_CAP", "12000"))  # chars of page body per prompt (median page ~1.8k words fits whole)

# --- LLM (headless CLI — Claude Code or Codex; free, no API key) ------------
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "claude")      # claude | codex
LLM_MODEL = os.environ.get("LLM_MODEL", "")                  # blank = the CLI's default
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "300"))
LLM_RETRIES = 1                                              # parse-failure nudges (transient-CLI retries live in llm.py)


# ---- atomic output writes (crash-safe): temp file in same dir -> os.replace over target -----------
import tempfile as _tempfile
def write_text(path, text):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = _tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.chmod(tmp, 0o644)   # match normal umask perms (mkstemp defaults to 0600)
        os.replace(tmp, path)
    except BaseException:
        try: os.remove(tmp)
        except OSError: pass
        raise
