#!/usr/bin/env python3
"""9-field-sources settings. Company-agnostic — set COMPANY per company; every path derives from one anchor.

Reddit cannot be searched without naming subreddits, so somebody has to decide which ones. This engine
decides once per company, and VERIFIES each one is real and alive — because a wrong subreddit name
returns zero results silently, which is indistinguishable from "nobody discusses this".
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                  # .../9-field-sources
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
WORK = os.path.join(BRAND_CTX, "_work", "field-sources")
OUT_MD = os.path.join(BRAND_CTX, "field-sources.md")     # THE deliverable, written in place

PROMPTS = os.path.join(ROOT, "prompts")
SOURCES_MD = os.path.join(ROOT, "sources.md")            # the capability list, hand-written, generic

# --- how a subreddit qualifies -----------------------------------------------------------------------
# Vetted by ACTIVITY, never by subscriber count: old.reddit stopped exposing subscriber counts in 2026,
# and a big dormant community is worth less than a small busy one anyway.
MIN_POSTS = int(os.environ.get("FS_MIN_POSTS", "5"))       # top posts found in the last year
MIN_COMMENTS = int(os.environ.get("FS_MIN_COMMENTS", "40"))  # summed across those posts
MAX_KEEP = int(os.environ.get("FS_MAX_KEEP", "10"))        # subreddits kept in the final list.
# A longer list is nearly free: the per-article planner names which subreddits a given query
# goes to, so the list is a menu, not a workload. Too short is the expensive mistake.
PER_ANGLE = int(os.environ.get("FS_PER_ANGLE", "3"))        # kept from EACH `covers` angle first
CANDIDATES = int(os.environ.get("FS_CANDIDATES", "18"))    # discovered before verification

THROTTLE = float(os.environ.get("FS_THROTTLE", "2.0"))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# The paid fallback. old.reddit is free but rate-limits an IP that scrapes hard, and then serves a login
# page instead of results — which parses as "no results" unless you look. When that happens this takes
# over. The key is NOT in the repo: it lives in the user's own config, outside the tree.
SC_ENV = os.path.expanduser(os.environ.get("SC_ENV", "~/.config/last30days/.env"))
SC_BASE = "https://api.scrapecreators.com/v1/reddit"


def sc_key():
    k = os.environ.get("SCRAPECREATORS_API_KEY", "")
    if k:
        return k
    try:
        for line in open(SC_ENV):
            if line.startswith("SCRAPECREATORS_API_KEY="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


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
