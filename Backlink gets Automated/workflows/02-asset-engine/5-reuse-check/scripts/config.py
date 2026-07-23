#!/usr/bin/env python3
"""5-reuse-check settings. The reuse check: for every clubbed idea, find the closest existing pages
(RAG) and let an LLM decide build-vs-reuse. Adds only this engine's knobs; everything company-related
comes from _shared/config_base.py (COMPANY is one setting). RAG knobs are the PROVEN values ported
verbatim from projects/.../clubbed/_work/rag.py — do NOT retune (see reuse-check.workflow.md).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "_shared"))
from config_base import *            # noqa: F403 — the shared anchor, brand facts, atomic writes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../5-reuse-check
PROMPTS = os.path.join(ROOT, "prompts")
RECIPE_MD = os.path.join(ROOT, "reuse-check.workflow.md")            # the recipe owns the criteria

# --- inputs ------------------------------------------------------------------
# The merged pool (from 4-merge). We fill its 6 reuse columns IN PLACE — same file in and out.
OUT = os.path.join(ASSET_ENGINE, "clubbed", "output")               # noqa: F405
WORK = os.path.join(ASSET_ENGINE, "clubbed", "_work")               # noqa: F405
CLUBBED = os.path.join(OUT, "clubbed-ideas.csv")
# CATALOGUE_CSV (content-database.csv, WITH the `Full content` column) comes from config_base.

# --- where the two-vector content index lives (built once, refreshed on content change) -------
INDEX_DIR = os.path.join(WORK, "content-index")                     # title/ + body/ subdirs

# --- which step owns which column (single source of truth) -------------------
# Stage 2 (step_1_retrieve) fills these three; Stage 3 (step_2_judge) fills the last three.
STAGE2_COLS = ["RAG candidates", "Topic pages we own", "Reference links"]
STAGE3_COLS = ["Reuse verdict", "Chosen links", "Why"]
REUSE_COLS = STAGE2_COLS + STAGE3_COLS

# --- RAG retrieval knobs (PROVEN — ported from rag.py; do NOT retune) ---------
# rag.py L21-28. The embed + rerank MODELS themselves live in _shared/voyage.py
# (voyage-4-large + rerank-2.5) — reused, never re-declared here.
ALPHA = float(os.environ.get("RC_ALPHA", "0.5"))          # title weight in blended dense score (rag.py L21)
N_RETRIEVE = int(os.environ.get("RC_N_RETRIEVE", "40"))   # dense candidates before reranking (rag.py L22)
TOPK = int(os.environ.get("RC_TOPK", "15"))               # RAG candidate LINKS kept per idea (rag.py L23)
CHUNK_CHARS = int(os.environ.get("RC_CHUNK_CHARS", "4800"))   # body chunk size (rag.py L24)
OVERLAP = int(os.environ.get("RC_OVERLAP", "600"))            # chunk overlap (rag.py L25)
RERANK_DOC_CHARS = int(os.environ.get("RC_RERANK_DOC_CHARS", "4000"))  # per-candidate truncation for rerank (rag.py L28)
INDEX_BATCH_CHUNKS = int(os.environ.get("RC_INDEX_BATCH", "64"))       # body chunks per embed flush (rag.py MAX_ITEMS)
RETRIEVE_PACE = float(os.environ.get("RC_RETRIEVE_PACE", "0.0"))       # optional sleep between ideas (rate courtesy)
RETRIEVE_WORKERS = int(os.environ.get("RC_RETRIEVE_WORKERS", "8"))     # parallel per-idea retrieve+rerank (I/O-bound; Voyage has headroom)

# --- foreign-language exclusion (validated add-on, ported from retrieve_top15.py) -------------
# Drop translation duplicates: URLs whose FIRST path segment is an ISO language code (/de/, /fr/, ...).
# Company-agnostic — matched on the path segment, never on a hardcoded domain.
LOCALES = set(s for s in os.environ.get("RC_LOCALES",
    "ar,pl,it,pt-br,no,ja,da,es,de,el,sv,nl,fr,pt,zh,ko,ru,tr,hi,id,th,vi,fi,cs,hu,ro,he,uk,bg,hr,sk,"
    "sl,et,lv,lt,ms,fa,zh-cn,zh-tw,en-gb,en-au,en-ca,en-in").split(",") if s)

# --- Topic catalogue knobs (deterministic keyword catalogue; smart label + dumb match) --------
TOPIC_KW_BATCH = int(os.environ.get("RC_TOPIC_KW_BATCH", "25"))    # asset titles per keyword-labelling call
TOPIC_KW_WORKERS = int(os.environ.get("RC_TOPIC_KW_WORKERS", "4")) # parallel labelling calls
CATALOGUE_MAX_MATCH = int(os.environ.get("RC_CAT_MAX_MATCH", "80"))  # a keyword matching > this = too generic, skip it
CATALOGUE_CAP = int(os.environ.get("RC_CAT_CAP", "30"))             # displayed catalogue capped; true count still shown

# --- Stage 3 judge knobs -----------------------------------------------------
JUDGE_WORKERS = int(os.environ.get("RC_JUDGE_WORKERS", "6"))       # concurrent judge calls (stage3_judge.py WORKERS=6)
JUDGE_READ_WINDOW = int(os.environ.get("RC_JUDGE_READ", "7"))      # top-N RAG candidates read per idea (workflow Stage 3)
JUDGE_PARSE_RETRIES = int(os.environ.get("RC_JUDGE_PARSE_RETRIES", "2"))  # re-call on an unparseable verdict
JUDGE_DOC_CHARS = int(os.environ.get("RC_JUDGE_DOC_CHARS", "12000"))      # per-candidate page text handed to the judge
VERDICTS = ["Already have it", "Improve existing", "Build from parts", "Brand new"]

# --- orchestrator resume markers (the clubbed CSV is edited in place, so it can't be the marker) ---
STAGE2_MARKER = os.path.join("_work", ".stage2-retrieved.done")   # relative to clubbed/
STAGE3_MARKER = os.path.join("_work", ".stage3-judged.done")
STAGE2_DONE = os.path.join(WORK, ".stage2-retrieved.done")        # absolute (steps write these)
STAGE3_DONE = os.path.join(WORK, ".stage3-judged.done")
