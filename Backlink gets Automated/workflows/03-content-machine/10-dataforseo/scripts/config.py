#!/usr/bin/env python3
"""Run defaults for the research pipeline. Override per run by editing here or via CLI flags."""
import json as _tenant_json
import os
import sys as _tenant_sys

HERE = os.path.dirname(os.path.abspath(__file__))   # .../10-dataforseo/scripts
ROOT = os.path.dirname(HERE)                          # .../10-dataforseo
PROMPTS = os.path.join(ROOT, "prompts")              # the thinking-step prompt files
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(ROOT)))   # .../Backlink gets Automated

# Company (one setting — everything company-specific derives from it). Outputs live under projects/<company>/.
COMPANY = os.environ.get("COMPANY", "testlify")
_PROJ = os.path.join(REPO_ROOT, "projects", COMPANY)
OUT = os.path.join(_PROJ, "03-content-machine", "dataforseo", "out")   # runs go to OUT/<slug>/
CLUBBED_CSV = os.path.join(_PROJ, "02-asset-engine", "clubbed", "output", "clubbed-ideas.csv")  # Step 0 input
CHECKLIST = os.path.join(_PROJ, "01-brand-context", "seo-aeo-geo-checklist.md")  # Step 7 build-spec source

# ---- THE COMPANY RECORD (tenant contract) ---------------------------------------------------------
# All class-(a) company facts live in ONE file: projects/<company>/company.json (single source of truth, F1).
# A missing record for a NON-default company is a hard stop (fail closed — running with another tenant's
# defaults would silently research the wrong market/niche). The testlify default keeps legacy runs working.
def _load_tenant():
    p = os.path.join(_PROJ, "company.json")
    try:
        with open(p) as f:
            return _tenant_json.load(f)
    except FileNotFoundError:
        if COMPANY != "testlify":
            _tenant_sys.exit(f"!! no company record at {p} — create it before running (see revamp Phase 1.1)")
        return {}
TENANT = _load_tenant()

LOCATION = TENANT.get("location", "United States")   # DataForSEO location_name (the audience market)
LANGUAGE = TENANT.get("language", "en")

# LLM (headless Claude Code) — the THINKING steps (0 seeds, 3 scoring, 4-6 write-ups, 7 assembly) run through
# llm.py. Free, no API key. The API/fetch steps (s1_expand … s5_pages fetch) route through dfs.py, not this.
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_TIMEOUT = 300     # seconds per headless-Claude call
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "claude").lower()
LLM_MODEL = os.environ.get("LLM_MODEL", "")
MAX_WORKERS = 4          # parallel scorer calls (the Step-3 "panel")
LLM_RETRIES = 1          # re-ask once on unparseable JSON

# Credit guard (pre-flight): before the paid run, stop cleanly if the DataForSEO balance is below this ($).
# Leaves the topic in the queue (not marked done) so it resumes after top-up. Tunable via env.
MIN_CREDITS = float(os.environ.get("DFS_MIN_CREDITS", "1.0"))

# Brand identity — from the company record. BRAND is the display name fed to every judgment prompt;
# DOMAIN is the company's own site (NOT assumed to be <brand>.com — see revamp Phase 1.4);
# BRAND_ONELINER is the one-line "what we sell" the scorer/judge uses to judge brand-fit.
BRAND = TENANT.get("brand", "testlify")
DOMAIN = TENANT.get("domain", "testlify.com")
BRAND_ONELINER = TENANT.get("brand_oneliner", "skills assessments + conversational AI interviews (chat/voice/video)")
# One-sentence definition of the company's niche — fills {{NICHE_DEFINITION}} in the seed/vetting prompts,
# replacing the hardcoded "recruiting / hiring / HR metrics" rule (revamp Phase 1.3).
NICHE_DEFINITION = TENANT.get("niche_definition", "recruiting / hiring / HR metrics — talent assessment, analytics, funnels, scorecards, benchmarks")

# Engine method knobs — NOT company facts (Devansh 2026-07-18: the record holds brand identity only).
# One constant pair everywhere: volume >= 100, KD <= 40 (13-research-structure uses the same pair).
VOL_FLOOR = 100              # Step 2: keep keywords with monthly volume >= this
KD_CEIL   = 40              # Step 2: keep keywords with keyword_difficulty <= this

# Spoke ranking (Step 3 judge): score each spoke candidate so the conductor can keep only its best few.
# score = W_REL*(relevance/10) + W_VOL*volume(log-normalized across candidates) + W_KD*((100-KD)/100).
# The CAP (how many actually enqueue) lives in the conductor (config.MAX_SPOKES) — this only ranks them.
SPOKE_W_RELEVANCE = 0.5     # same-cluster relevance from the judge (0-10) — dominates, so big-but-generic heads lose
SPOKE_W_VOLUME    = 0.25    # search volume, log-normalized (heavy-tailed, so raw min-max would over-reward one giant)
SPOKE_W_KD        = 0.25    # ease = (100-KD)/100 (lower difficulty = higher score)
# HARD FLOOR: drop any spoke whose same-cluster relevance is BELOW this, whatever its volume — so a huge but
# off-cluster head (e.g. "benchmarking" @110k) can never make the top 3 on volume alone. A missing relevance is kept.
SPOKE_MIN_RELEVANCE = 3     # keep only spokes with relevance >= this (0-2 = off-cluster → dropped)

# Step 1 — TIGHT net (keyword_suggestions, one call per seed)
TIGHT_LIMIT = 200          # phrases per seed

# Step 1 — RANKED net (ranked_keywords on winning pages; replaces the dropped wide net)
RANKED_SERP_LINKS = 6      # SPOKES only: how many top organic pages to pull from the SERP-of-seed
RANKED_URL_CAP    = 5      # HUBS: max vetted competitor URLs the ranked net pulls (2026-08-04 — cost cap;
                           # the seed-SERP source was dropped for hubs, competitor pages are the better net)
RANKED_PER_URL    = 120    # max keywords to pull per winning page (ordered by volume)

# Step 4 — SERP on the primary
SERP_DEPTH = 20
PAA_CLICK_DEPTH = 3
PAGES_TO_READ = 3          # Step 5: how many top URLs to free-fetch


# ---- atomic output writes (crash-safe): temp file in same dir -> os.replace over target -----------
import os as _os, json as _json, tempfile as _tempfile
def write_json(path, data, indent=2):
    d = _os.path.dirname(path) or "."
    fd, tmp = _tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with _os.fdopen(fd, "w") as f:
            _json.dump(data, f, indent=indent)
        _os.chmod(tmp, 0o644)   # match normal umask perms (mkstemp defaults to 0600)
        _os.replace(tmp, path)
    except BaseException:
        try: _os.remove(tmp)
        except OSError: pass
        raise
def write_text(path, text):
    d = _os.path.dirname(path) or "."
    fd, tmp = _tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with _os.fdopen(fd, "w") as f:
            f.write(text)
        _os.chmod(tmp, 0o644)   # match normal umask perms (mkstemp defaults to 0600)
        _os.replace(tmp, path)
    except BaseException:
        try: _os.remove(tmp)
        except OSError: pass
        raise
