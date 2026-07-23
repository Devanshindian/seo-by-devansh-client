#!/usr/bin/env python3
"""4-merge settings. Clubs the three method idea-pools into ONE deduped sheet the research phase reads.
Everything company-related comes from _shared/config_base.py (COMPANY is one setting).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "_shared"))
from config_base import *            # noqa: F403 — shared anchor, brand facts, atomic writes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../4-merge
PROMPTS = os.path.join(ROOT, "prompts")

# --- the three inputs (each method's deliverable) ---------------------------
M1 = os.path.join(ASSET_ENGINE, "competitor-study", "output", "ideas.csv")            # noqa: F405
M2 = os.path.join(ASSET_ENGINE, "model-other-niches", "output", "model-other-niches-ideas.csv")  # noqa: F405
M3 = os.path.join(ASSET_ENGINE, "study-trends", "output", "study-trends-ideas.csv")   # noqa: F405

# Method 2 is INCLUDED (2026-07-22): it was corrected to the format-honesty rules — it still imports proven
# cross-niche formats, but the asset title carries no shape-words and anything needing a build is honestly
# flagged in `Tool escalation` (so the write phase can pick only the desk-doable ones). Disable with
# MG_INCLUDE_M2=0. See format-honesty-fix-plan.md.
INCLUDE_M2 = os.environ.get("MG_INCLUDE_M2", "1") == "1"

# --- where this engine writes -----------------------------------------------
OUT = os.path.join(ASSET_ENGINE, "clubbed", "output")               # noqa: F405 — the old 'clubbed' location
WORK = os.path.join(ASSET_ENGINE, "clubbed", "_work")               # noqa: F405
CLUBBED = os.path.join(OUT, "clubbed-ideas.csv")

# --- the ONE merged schema --------------------------------------------------
# First block = idea data filled by the merge. Last block = reuse-check placeholders (Method 5 fills them).
# The research phase reads only: Asset (key), Distinct angle, Proof URLs, RAG candidates, Topic pages we own,
# Reuse verdict — so those are the load-bearing ones; the rest are human/prioritisation context.
COLS = ["Sources", "Brand fit", "Asset", "Format", "Tool escalation", "Distinct angle", "What it'd be",
        "# pages", "# words", "Total domains", "# comps", "# posts", "Beatability", "Effort", "Proof URLs",
        "RAG candidates", "Topic pages we own", "Reference links", "Reuse verdict", "Chosen links", "Why"]
REUSE_COLS = ["RAG candidates", "Topic pages we own", "Reference links", "Reuse verdict", "Chosen links", "Why"]

# --- dedup knobs (the cross-method repeat check; same pattern as competitor-study dedup) --------------------
DEDUP_THRESHOLD = float(os.environ.get("MG_DEDUP_THR", "0.78"))  # cosine to NOMINATE a pair as a possible repeat (looser than within-method: cross-method dupes are worded more differently; the LLM still decides)
DEDUP_TOPK = int(os.environ.get("MG_DEDUP_TOPK", "6"))          # nearest neighbours considered per idea
DEDUP_MAX_CLUSTER = int(os.environ.get("MG_DEDUP_MAX", "10"))   # cap a cluster before the LLM pass
DEDUP_WORKERS = int(os.environ.get("MG_DEDUP_WORKERS", "6"))    # parallel adjudication calls

# --- Step 3: relevance recheck (E7) — remove obvious junk / off-brand ideas, conservatively -----------------
RELEVANCE_BATCH = int(os.environ.get("MG_REL_BATCH", "30"))      # ideas per judge call (title+angle only, so they fit)
RELEVANCE_WORKERS = int(os.environ.get("MG_REL_WORKERS", "6"))   # parallel judge calls
PROTECT_DOMAINS = int(os.environ.get("MG_PROTECT_DOMAINS", "50"))  # an idea with >= this many follow domains is NEVER dropped (J3 protect)
RELEVANCE_DROP_CAP = float(os.environ.get("MG_REL_CAP", "0.15"))   # if the model wants to drop > this fraction, refuse to apply without --force (start conservative)
