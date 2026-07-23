#!/usr/bin/env python3
"""2-model-other-niches settings. Adds only this engine's knobs; everything company-related
comes from _shared/config_base.py (COMPANY is one setting).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "_shared"))
from config_base import *            # noqa: F403 — shared anchor, brand facts, atomic writes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../2-model-other-niches
PROMPTS = os.path.join(ROOT, "prompts")
RECIPE_MD = os.path.join(ROOT, "model-other-niches.workflow.md")     # the recipe OWNS the swipe table (Source 1)

# --- where this engine writes -----------------------------------------------
OUT = os.path.join(ASSET_ENGINE, "model-other-niches", "output")     # noqa: F405
WORK = os.path.join(ASSET_ENGINE, "model-other-niches", "_work")     # noqa: F405

# --- inputs read from the layers before -------------------------------------
# The shared ownership anchor (Method 1 / G0). Method 2 judges CORE/TRANSPLANT/ADJACENT against THIS.
BRAND_SCOPE = os.path.join(ASSET_ENGINE, "competitor-study", "output", "brand-scope.md")  # noqa: F405
BRAND_VOICE = os.path.join(BRAND_CTX, "brand-voice.md")              # noqa: F405
FEATURES = os.path.join(BRAND_CTX, "features.md")                    # noqa: F405
STATS = os.path.join(BRAND_CTX, "stats.md")                          # noqa: F405

# --- knobs (every tunable named + commented, one place) ---------------------
EXTRA_FORMATS = int(os.environ.get("MN_EXTRA_FORMATS", "5"))   # A2: how many formats agent-knowledge adds (recipe: 3-5)
ADAPT_WORKERS = int(os.environ.get("MN_ADAPT_WORKERS", "6"))   # Step B: parallel adaptation calls
METHOD_TAG = "M2 — Other Niches"                               # the Method column value (shared merge schema)
IDEA_PREFIX = "M2"                                             # idea-number prefix so the merge never collides with M1
LINKABILITY_MIN = int(os.environ.get("MN_LINK_MIN", "3"))     # Step C Test B: needs >= 3 of 4 to pass
