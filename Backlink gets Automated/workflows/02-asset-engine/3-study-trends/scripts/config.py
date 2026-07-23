#!/usr/bin/env python3
"""3-study-trends settings. Adds only this engine's knobs; everything company-related comes from
_shared/config_base.py (COMPANY is one setting). Phase A (the Reddit scrape) is the scripts/reddit/ tool;
this config drives Phase B (mining the scrape into tensions -> ideas).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "_shared"))
from config_base import *            # noqa: F403 — shared anchor, brand facts, atomic writes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../3-study-trends
PROMPTS = os.path.join(ROOT, "prompts")
RECIPE_MD = os.path.join(ROOT, "study-trends.workflow.md")
VERIFY = os.path.join(ROOT, "scripts", "study-trends-verify.py")     # Stage 5 fail-closed gate (already built)

# --- where this engine writes -----------------------------------------------
OUT = os.path.join(ASSET_ENGINE, "study-trends", "output")          # noqa: F405
WORK = os.path.join(ASSET_ENGINE, "study-trends", "_work")          # noqa: F405
RAW = os.path.join(ASSET_ENGINE, "study-trends", "_raw")            # noqa: F405
SCRAPE_XLSX = os.path.join(RAW, f"{COMPANY}-reddit-trends.xlsx")     # noqa: F405 — Phase A output (the input to Phase B)

# --- inputs read from the layers before -------------------------------------
BRAND_SCOPE = os.path.join(ASSET_ENGINE, "competitor-study", "output", "brand-scope.md")  # noqa: F405
BRAND_VOICE = os.path.join(BRAND_CTX, "brand-voice.md")             # noqa: F405
FEATURES = os.path.join(BRAND_CTX, "features.md")                   # noqa: F405
STATS = os.path.join(BRAND_CTX, "stats.md")                         # noqa: F405

# --- knobs (every tunable named + commented, one place) ---------------------
PHRASE_WORKERS = int(os.environ.get("ST_PHRASE_WORKERS", "8"))     # 2a: parallel phrase-extraction calls
PHRASE_SHARD = int(os.environ.get("ST_PHRASE_SHARD", "12"))        # 2a: posts per phrase-extraction call (a "content-card batch")
# 2b: phrases recur at the level of MEANING, not exact string (measured: 1224 phrases, only 18 exact-repeat), so
# we cluster by embedding (Voyage) then name each cluster. Agglomerative into a CONTROLLED number of clusters
# (threshold union-find made 4 mega-blobs on this dense space — no good). Tune the target count here.
TARGET_CLUSTERS = int(os.environ.get("ST_CLUSTERS", "45"))         # phrase clusters to name (each names 1+ candidate tensions)
# KEEP SPECIFIC — do NOT force a target count (that squishes distinct pains, the competitor-study 3.4-vs-4.6
# lesson). The naming over-produces candidate tensions; we merge ONLY genuine near-duplicates (the same pain
# named by two zones), keeping every distinct pain. The real cut is Stage 3's brand-scope filter, not here.
MERGE_SIM = float(os.environ.get("ST_MERGE_SIM", "0.85"))          # merge two tension SENTENCES only if at least this similar (true dupes)
TENSION_MIN_PHRASES = int(os.environ.get("ST_MIN_PHRASES", "2"))   # drop 1-phrase tensions (noise -> their posts go to misc)
ASSIGN_SHARD = int(os.environ.get("ST_ASSIGN_SHARD", "30"))        # 2c: posts per assignment call
RECORDS_SHARD = int(os.environ.get("ST_RECORDS_SHARD", "20"))      # 2d: tensions per record-building call (rich output -> keep small)
FILTER_SHARD = int(os.environ.get("ST_FILTER_SHARD", "30"))        # 3: tensions per filter call
TENSION_MAX_POSTS = int(os.environ.get("ST_MAX_POSTS", "8"))       # 2b size alarm: > this many posts => presumed merged-by-topic
TENSION_MAX_PHRASES = int(os.environ.get("ST_MAX_PHRASES", "15"))  # 2b size alarm: > this many phrases => presumed merged-by-topic
MISC_MAX_PCT = float(os.environ.get("ST_MISC_MAX_PCT", "15"))      # 2c: misc must stay <= this % of posts
LINKABILITY_MIN = int(os.environ.get("ST_LINK_MIN", "3"))         # Stage 3 Test A: needs >= 3 of 4
IDEA_CTX_CHARS = int(os.environ.get("ST_IDEA_CTX", "6000"))       # Stage 4: cap each brand doc per idea call (full 100KB x many ideas is slow + costly)
EMOTIONS = ("anger", "anxiety", "disbelief", "ridicule")           # 2d closed vocabulary (no free-text emotions)
