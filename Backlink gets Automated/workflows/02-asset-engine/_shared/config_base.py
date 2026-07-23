#!/usr/bin/env python3
"""THE shared settings base for every 02-asset-engine engine.

Company-agnostic by construction: COMPANY is one setting, every company fact comes from
projects/<company>/company.json, every path derives from one anchor. An engine's own config.py
imports this and adds only its own knobs.

Layer anchors (the output tree mirrors the workflow tree — renamed 2026-07-20):
  00-foundation/      the site catalogue      (this layer READS it)
  01-brand-context/   voice/features/stats    (this layer READS it)
  02-asset-engine/    THIS layer's output
"""
import json, os, sys, tempfile

# --- the one anchor ---------------------------------------------------------
SHARED = os.path.dirname(os.path.abspath(__file__))            # .../02-asset-engine/_shared
LAYER = os.path.dirname(SHARED)                                 # .../02-asset-engine
WORKFLOWS = os.path.dirname(LAYER)                              # .../workflows
REPO_ROOT = os.path.dirname(WORKFLOWS)                          # .../Backlink gets Automated

COMPANY = os.environ.get("COMPANY", "")
if not COMPANY:
    raise SystemExit("!! COMPANY is not set. Run as: COMPANY=<slug> ... — this layer has no default company.")

PROJ = os.path.join(REPO_ROOT, "projects", COMPANY)

# --- the company record: fail closed ----------------------------------------
_rec = os.path.join(PROJ, "company.json")
try:
    with open(_rec) as f:
        TENANT = json.load(f)
except FileNotFoundError:
    sys.exit(f"!! no company record at {_rec} — create it first (see workflows/company-record.md)")

BRAND = TENANT.get("brand") or sys.exit("!! company record has no 'brand'")
DOMAIN = TENANT.get("domain") or sys.exit("!! company record has no 'domain'")
NICHE = TENANT.get("niche_definition", "")
ONELINER = TENANT.get("brand_oneliner", "")
LOCATION = TENANT.get("location", "United States")
LANGUAGE = (TENANT.get("language") or "en")[:2]

# --- what this layer reads from the layers before ---------------------------
FOUNDATION = os.path.join(PROJ, "00-foundation", "output")
CATALOGUE_CSV = os.path.join(FOUNDATION, "content-database.csv")
TOP_PAGES_CSV = os.path.join(FOUNDATION, "top-pages.csv")
BRAND_CTX = os.path.join(PROJ, "01-brand-context")

# --- where this layer writes ------------------------------------------------
ASSET_ENGINE = os.path.join(PROJ, "02-asset-engine")

# --- LLM (headless CLI — free, no API key) ----------------------------------
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "claude")
LLM_MODEL = os.environ.get("LLM_MODEL", "")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "420"))
LLM_RETRIES = 1
SHARED_PROMPTS = os.path.join(SHARED, "prompts")


# --- atomic writes: a file's existence must GUARANTEE it is complete ---------
def _atomic(path, write_fn):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")     # SAME dir -> the rename is atomic
    try:
        with os.fdopen(fd, "w") as f:
            write_fn(f)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try: os.remove(tmp)
        except OSError: pass
        raise


def write_text(path, text):
    _atomic(path, lambda f: f.write(text))


def write_json(path, data, indent=2):
    _atomic(path, lambda f: json.dump(data, f, indent=indent))


def rel(path):
    """Repo-relative — stable and readable in any printed output."""
    return os.path.relpath(path, REPO_ROOT)
