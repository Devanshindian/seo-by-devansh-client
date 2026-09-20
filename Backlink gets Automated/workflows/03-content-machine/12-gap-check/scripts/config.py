"""Gap-check config: paths, the LLM caller settings, and the coverage-target policy.
Self-contained — the only outside dependency is the `claude` CLI (headless Claude Code) for the three
LLM steps (judge, triage — the Step-0 checklist is pure code since 2026-08-04), and STORM's own runner for the (optional) gap-fill re-runs.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))          # .../12-gap-check/scripts
ROOT = os.path.dirname(HERE)                               # .../12-gap-check
PROMPTS = os.path.join(ROOT, "prompts")

# ALL output lives under projects/<company>/content-machine/ — never inside the workflow repo.
# COMPANY comes from the same env switch every engine uses (the split-brain fix, revamp Phase 1.2 —
# this file used to hardcode testlify, so COMPANY=acme runs tore across two companies' folders).
_BGA = os.path.normpath(os.path.join(ROOT, "..", "..", ".."))   # .../Backlink gets Automated
COMPANY = os.environ.get("COMPANY", "testlify")
# Uniform fail-closed guard: gap-check reads no tenant FACTS (only paths), but a missing company record for a
# non-default company still means "this tenant isn't onboarded" — stop at the boundary like every other engine.
if COMPANY != "testlify" and not os.path.exists(os.path.join(_BGA, "projects", COMPANY, "company.json")):
    import sys as _s
    _s.exit(f"!! no company record at projects/{COMPANY}/company.json — create it before running (revamp Phase 1.1)")
PROJ = os.path.join(_BGA, "projects", COMPANY, "03-content-machine")
RUNS = os.path.join(PROJ, "gap-check", "out")              # this workflow's output
STORM_OUT = os.path.join(PROJ, "storm", "out")            # where STORM writes (read by the re-run step)

# The LLM step runs on headless Claude Code (free on the subscription). No API key, no shim needed.
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
CLAUDE_TIMEOUT = 240          # seconds per call
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "claude").lower()
LLM_MODEL = os.environ.get("LLM_MODEL", "")
MAX_WORKERS = 4               # how many judge calls run at once
JUDGE_RETRIES = 1             # re-ask once if the model returns unparseable JSON

# STORM's runner, for the gap-fill re-runs (Step 3). This is the ONE real cross-folder dependency —
# you cannot re-run STORM without STORM. Everything else in gap-check is standalone.
STORM_DIR = os.path.normpath(os.path.join(ROOT, "..", "11-storm"))
STORM_RUNNER = os.path.join(STORM_DIR, "scripts", "run_storm.py")
STORM_PYTHON = os.path.join(STORM_DIR, "venv", "bin", "python")

# --- Coverage-target policy (cut to three types, 2026-08-04, decided with Devansh) ---
JUDGED_TYPES = [
    "gap_we_own",       # competitor-read -> gaps_to_own  (THE priority — the article's differentiator)
    "winner_h2",        # competitor-read -> winners_common_h2s (table stakes)
    "aio_subtopic",     # SERP extract -> AI Overview "what it covers" (the answer skeleton)
]
# DROPPED: secondary_kw + in_body (keyword strings — section keywords are the architect's job now),
# paa (the write phase's FAQ can only use facts already in the article, so it self-corrects),
# aeo_faq (the AEO step was deleted; nothing consumed it).


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
