"""Research-structure config: paths, LLM caller settings, keyword constraints.
Self-contained. Outside deps: the `claude` CLI (headless, free) for the LLM steps, a live web fetch for
our own pages, and DataForSEO for the per-H2 keyword step. Brand-agnostic — paths/creds set per company.
"""
import os, json, tempfile


# ---- atomic output writes (crash-safe) -------------------------------------------------------------
# Write to a temp file in the SAME dir, then os.replace() over the target. os.replace is atomic on one
# filesystem, so a step's real output file only ever exists COMPLETE — a crash mid-write leaves a stray
# .tmp (ignored), never a half-written output that resume would wrongly trust. Use these everywhere a
# step saves its output.
def write_json(path, data, indent=2):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=indent)
        os.chmod(tmp, 0o644)   # match normal umask perms (mkstemp defaults to 0600)
        os.replace(tmp, path)
    except BaseException:
        try: os.remove(tmp)
        except OSError: pass
        raise


def write_text(path, text):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.chmod(tmp, 0o644)   # match normal umask perms (mkstemp defaults to 0600)
        os.replace(tmp, path)
    except BaseException:
        try: os.remove(tmp)
        except OSError: pass
        raise

HERE = os.path.dirname(os.path.abspath(__file__))        # .../13-research-structure/scripts
ROOT = os.path.dirname(HERE)                             # .../13-research-structure
PROMPTS = os.path.join(ROOT, "prompts")
CM = os.path.normpath(os.path.join(ROOT, ".."))          # .../03-content-machine  (dfs.py lives here)

# ALL output lives under projects/<company>/content-machine/ — never inside the workflow repo.
# COMPANY comes from the same env switch every engine uses. THIS file was the sharpest half of the
# split-brain [A#2]: it hardcoded testlify while the conductor respected COMPANY, so a COMPANY=acme run
# wrote steps 1-3 under projects/acme/ and step 4 under projects/testlify/. Fixed: revamp Phase 1.2.
_BGA = os.path.normpath(os.path.join(CM, "..", ".."))    # .../Backlink gets Automated
COMPANY = os.environ.get("COMPANY", "testlify")
PROJ = os.path.join(_BGA, "projects", COMPANY, "03-content-machine")
OUT = os.path.join(PROJ, "research-structure", "out")

# THE COMPANY RECORD (tenant contract) — projects/<company>/company.json, single source of truth (F1).
# Missing record for a NON-default company = hard stop (fail closed). See 10-dataforseo/scripts/config.py.
import json as _tenant_json, sys as _tenant_sys
def _load_tenant():
    p = os.path.join(_BGA, "projects", COMPANY, "company.json")
    try:
        with open(p) as f:
            return _tenant_json.load(f)
    except FileNotFoundError:
        if COMPANY != "testlify":
            _tenant_sys.exit(f"!! no company record at {p} — create it before running (see revamp Phase 1.1)")
        return {}
TENANT = _load_tenant()

# Sibling workflow OUTPUTS we read from (also under projects/)
STORM_OUT = os.path.join(PROJ, "storm", "out")           # projects/<company>/content-machine/storm/out/<Topic>/ (+ iteration-<n>/)
DFS_RUNS = os.path.join(PROJ, "dataforseo", "out")       # out/<slug>/research-doc-<slug>.md

# Per-company inputs
CLUBBED_CSV = os.environ.get("CLUBBED_CSV",
    os.path.join(_BGA, "projects", COMPANY, "02-asset-engine", "clubbed", "output", "clubbed-ideas.csv"))

# The site catalogue (built by 00-foundation/1-site-catalogue). harvest_ownpages reads page bodies
# from HERE instead of re-fetching the live site — the bodies carry #/##/### heading markers.
CONTENT_DB = os.path.join(_BGA, "projects", COMPANY, "00-foundation", "output", "content-database.csv")


# Market for the paid per-H2 keyword step (Step 6) — from the company record. Used to live hardcoded
# inside keywords.py (a C1 violation: a tunable buried in a step script).
LOCATION = TENANT.get("location", "United States")
LANGUAGE = TENANT.get("language", "en")

# The LLM steps run on headless Claude Code (free). No API key, no shim.
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_TIMEOUT = 300      # seconds per call
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "claude").lower()
LLM_MODEL = os.environ.get("LLM_MODEL", "")
# Concurrency default is PROVIDER-AWARE (not a flat number): DeepSeek is a real API with a huge concurrency
# ceiling (500-2500 requests at once, confirmed), so it gets a higher default. Claude/Codex are headless CLIs
# that stall under heavy parallel load (the freeze we hit earlier today) — they keep the proven-safe default.
# Still env-overridable either way, but a run on claude/codex NEVER silently inherits deepseek's higher number.
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "8" if LLM_PROVIDER == "deepseek" else "4"))
LLM_RETRIES = 1           # re-ask once on unparseable JSON
HARVEST_RETRIES = 2       # Step 1: re-run a section/page that yields 0 cards this many extra times

# Reader persona (Step 1a) — the ONE persona this asset serves, picked from the brand's persona library and
# carried forward (blueprint + persona.json) so the bundle reuses it (single source of truth). Brand-agnostic.
BRAND_CTX = os.path.join(os.path.dirname(PROJ), "01-brand-context")   # layer 01's output: brand-voice/style/features/persona/voices/…
PERSONA_MD = os.path.join(BRAND_CTX, "persona.md")       # the persona library (has a "How to pick" section)

# Angle-relevance filter (Step 1b) — drop off-angle cards BEFORE clustering (the biggest anti-bloat lever).
# BRAND_ONELINER comes from the company record (it used to be a SECOND hand-typed copy here, already
# drifted from 10-dataforseo's — the exact F1 violation the record exists to kill). Env still overrides.
BRAND_ONELINER = os.environ.get("BRAND_ONELINER",
    TENANT.get("brand_oneliner", "Testlify — a talent-assessment platform that sells pre-employment tests"))
SCORE_BATCH = int(os.environ.get("SCORE_BATCH", "30"))    # cards per scoring call — env-overridable
SCORE_KEEP_THRESH = 1     # DROP a card if relevance <= this AND not protected (0=conservative, 1=default)
SCORE_FLAG_PCT = 60       # flag loudly if >this% of cards get dropped (something's likely wrong)

# Clustering (Step 2)
CLUSTER_SINGLE_MAX = 200  # <= this many cards -> one clustering call; more -> batched two-level
CLUSTER_BATCH = 120       # cards per batch in the two-level path

# Per-H2 keyword pick (Step 6). Engine method knobs — NOT company facts (the record holds brand identity
# only). ONE constant pair everywhere (Devansh 2026-07-18): KD <= 40 / volume >= 100, same as 10-dataforseo.
# (This engine previously used KD 30; unified to 40 — accepted behavior change.)
KD_CEIL = 40              # keep target keyword only if difficulty < this
VOL_FLOOR = 100           # ...and volume >= this

# Orphan check (Step 7): a section whose keyword clears this volume is "high-volume" for the audit.
# Used to live hardcoded inside orphan.py (C1 violation).
HIGH_VOL = 300
