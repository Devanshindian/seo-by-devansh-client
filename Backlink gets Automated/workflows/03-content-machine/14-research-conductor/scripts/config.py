#!/usr/bin/env python3
"""Research conductor settings. Chains the 4 research engines (10-dataforseo, 11-storm, 12-gap-check,
13-research-structure) per topic. Brand-agnostic — set COMPANY per company; every path derives from one anchor.

Outside deps: the four engine runners, the STORM shim (headless-Claude server) + its venv, the `claude` CLI.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))          # .../14-research-conductor/scripts
ROOT = os.path.dirname(HERE)                                # .../14-research-conductor
CM = os.path.dirname(ROOT)                                  # .../03-content-machine
REPO_ROOT = os.path.dirname(os.path.dirname(CM))            # .../Backlink gets Automated

COMPANY = os.environ.get("COMPANY", "testlify")
_PROJ = os.path.join(REPO_ROOT, "projects", COMPANY)
PROJ_CM = os.path.join(_PROJ, "03-content-machine")
PROMPTS = os.path.join(ROOT, "prompts")           # the bundle's LLM prompt files (persona/author pick)

# THE COMPANY RECORD (tenant contract) — projects/<company>/company.json, single source of truth (F1).
# BRAND is the DISPLAY name for prompts ({{BRAND}} was previously filled with the lowercase COMPANY slug —
# one of the three drifted meanings of {{BRAND}} unified in revamp Phase 1.3).
import json as _tenant_json, sys as _tenant_sys
def _load_tenant():
    p = os.path.join(_PROJ, "company.json")
    try:
        with open(p) as f:
            return _tenant_json.load(f)
    except FileNotFoundError:
        if COMPANY != "testlify":
            _tenant_sys.exit(f"!! no company record at {p} — create it before running (revamp Phase 1.1)")
        return {}
TENANT = _load_tenant()
BRAND = TENANT.get("brand", COMPANY)

# LLM (headless Claude) — used by the bundle step's persona/author picker. Free, no API key.
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_TIMEOUT = 300
LLM_RETRIES = 1

# --- inputs -----------------------------------------------------------------
CLUBBED_CSV = os.path.join(_PROJ, "02-asset-engine", "clubbed", "output", "clubbed-ideas.csv")  # the idea cabinet
LOG_CSV = os.path.join(PROJ_CM, "research-log.csv")         # THE QUEUE/SHEET (single source of truth for status)
# Reuse-verdict handling (2026-07-22). We WRITE all three writable verdicts, but in priority order:
#   PRIMARY first (net-new value), then 'Improve existing' LAST (we rebuild those from the distinct angle for now;
#   the sanity-check confirmed all 769 point at a real existing page). 'Already have it' is never written.
REUSE_PRIMARY = {"Brand new", "Build from parts"}          # written first
REUSE_LAST = {"Improve existing"}                          # written last (pushed to the bottom of the pick order)
REUSE_OK = REUSE_PRIMARY | REUSE_LAST                      # all verdicts we research (i.e. everything except 'Already have it')

# Spoke policy (Step 6 enqueue). DataForSEO ranks a hub's spoke candidates best-first (0.5 relevance / 0.25 volume /
# 0.25 ease); the conductor enqueues only the top MAX_SPOKES of them. ONE-LEVEL-ONLY: a spoke never spawns its own
# spokes (else the queue grows 3 + 9 + 27… with no bound) — so each hub yields at most MAX_SPOKES, full stop.
# PARKED (revamp Phase 0.4): default 0 — spokes are a half-idea (bare keyword, no title/angle/competitors/RAG) and
# every spoke run crashes at research-structure Step 1 and blocks the queue. Real spoke generation moves to the
# asset engine after revamp Phase 3. Set MAX_SPOKES=N to re-enable once that lands. See revamp-phase-plan.md.
MAX_SPOKES = int(os.environ.get("MAX_SPOKES", "3"))        # spokes per hub. Re-enabled 2026-07-22: each bare keyword is
                                                           # now MINTED into a real idea (spoke_idea.accept) so it no longer starves.

# Retry cap (revamp Phase 0.4). An in_progress row is reclaimed and retried on the next run; without a cap a
# deterministically-failing topic is retried forever, blocking the queue and burning paid API calls each attempt.
# After MAX_ATTEMPTS the row is marked 'failed' (a terminal state, skipped by the picker) instead of reclaimed.
MAX_ATTEMPTS = int(os.environ.get("MAX_ATTEMPTS", "3"))

# Cannibalisation FLAG (2026-07-23). Before writing, check the article's primary keyword against OUR real ranking
# footprint (00-foundation's ranked_keywords pull). If we already rank for it, flag it in the bundle — never block.
# CANNIB_RANK_MAX=10: only a TOP-10 (page-1) ranking is real cannibalisation — that's where a second page actually
# splits our own traffic; a #40 nobody sees is not. The exact position is always shown in the flag. See cannibalization.py.
CANNIB_CHECK = os.environ.get("CANNIB_CHECK", "1") == "1"   # off-switch: CANNIB_CHECK=0
CANNIB_RANK_MAX = int(os.environ.get("CANNIB_RANK_MAX", "10"))   # flag only if we rank in the top N (page 1)

# --- the engine runners (what the conductor calls) --------------------------
DFS_RUN    = os.path.join(CM, "10-dataforseo", "scripts", "run_dataforseo.py")
STORM_RUN  = os.path.join(CM, "11-storm", "scripts", "run_storm.py")
STORM_PREVIEW = os.path.join(CM, "11-storm", "preview", "view-article.py")  # renders a dossier dir -> viewable article.html
STORM_SHIM = os.path.join(CM, "11-storm", "scripts", "shim.py")
STORM_PY   = os.path.join(CM, "11-storm", "venv", "bin", "python")   # STORM needs its own venv (knowledge_storm/dspy)
GAP_RUN    = os.path.join(CM, "12-gap-check", "scripts", "run_gapcheck.py")
STRUCT_RUN = os.path.join(CM, "13-research-structure", "scripts", "build_structure.py")

# --- where each engine writes (for resume checks + handoffs) ----------------
DFS_OUT    = os.path.join(PROJ_CM, "dataforseo", "out")     # /<slug>/research-doc-<slug>.md  + proof/03-final.json
STORM_OUT  = os.path.join(PROJ_CM, "storm", "out")          # /<TopicDir>/storm_gen_article_polished.txt
GAP_OUT    = os.path.join(PROJ_CM, "gap-check", "out")      # /<slug>/gap-check.md
STRUCT_OUT = os.path.join(PROJ_CM, "research-structure", "out")  # /<slug>/structure-<slug>.json (+ .html)

# --- STORM run knobs --------------------------------------------------------
SHIM_PORT = int(os.environ.get("SHIM_PORT", "8081"))       # the headless-Claude shim STORM talks to
SHIM_WAIT = 40                                              # seconds to wait for the shim to come up
STORM_ARGS = ["--article", "--polish"]                     # STORM must produce the polished dossier gap-check/structure read
STORM_MIN_WORDS = 1500     # GATE: a healthy STORM article is ~9k words; a failed/stub run is ~300. Below this = FAILED run.

# --- bundle (Step 5) paths: the constants the bundle POINTS to + where it writes ---
BRAND_CTX   = os.path.join(_PROJ, "01-brand-context")          # layer 01's output: brand-voice/style/features/examples/integrity/persona/voices
# stats.md · opinions.md · stories.md (cite-from SEED) live in BRAND_CTX since the
# brand-brain retirement (2026-07-19) — no separate path.
AVOID_AI    = os.path.join(CM, "reference", "avoid-ai-writing", "SKILL.md")   # mandatory final anti-AI pass
# The SEO/AEO/GEO checklist is a POINTER to the one workflow-tree original — never a per-company
# copy (a byte-identical copy is only a drift risk; decided 2026-07-19, revamp plan 3.0a).
SEO_CHECKLIST = os.path.join(CM, "reference", "seo-aeo-geo-guidelines", "seo-aeo-geo-checklist.md")
BUNDLE_OUT  = os.path.join(PROJ_CM, "research-bundle")         # the handoff: BUNDLE_OUT/<slug>/

# --- slug (the short folder nickname made from the unique title) ------------
SLUG_MAX_WORDS = 5      # first N meaningful words of the title
SLUG_MAX_LEN = 45       # hard cap on the slug length


def storm_dir(topic, hub=""):
    """The folder STORM creates for a topic — MUST match knowledge_storm's naming exactly
    (engine.py: topic.replace(' ','_').replace('/','_'), truncated to 125). A spoke nests under its pillar:
    STORM_OUT/<hub>/<TopicDir>/ (hub="" → flat STORM_OUT/<TopicDir>/)."""
    return os.path.join(STORM_OUT, hub, topic.replace(" ", "_").replace("/", "_")[:125])


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
