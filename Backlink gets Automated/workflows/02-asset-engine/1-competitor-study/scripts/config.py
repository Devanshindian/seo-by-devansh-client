#!/usr/bin/env python3
"""1-competitor-study settings. Adds only this engine's knobs; everything company-related
comes from _shared/config_base.py (COMPANY is one setting).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "_shared"))
from config_base import *            # noqa: F403 — the shared anchor, brand facts, atomic writes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../1-competitor-study
PROMPTS = os.path.join(ROOT, "prompts")
RECIPE_MD = os.path.join(ROOT, "competitor-study.workflow.md")       # the recipe owns the criteria

# --- where this engine writes ----------------------------------------------
OUT = os.path.join(ASSET_ENGINE, "competitor-study", "output")       # noqa: F405
WORK = os.path.join(ASSET_ENGINE, "competitor-study", "_work")       # noqa: F405
RAW = os.path.join(ASSET_ENGINE, "competitor-study", "_raw")         # noqa: F405
COST_LOG = os.path.join(WORK, "dfs-cost-log.json")

# --- Step A: competitor discovery + shortlist -------------------------------
CANDIDATE_LIMIT = int(os.environ.get("CS_CANDIDATES", "200"))  # how many the API returns to judge from
SHORTLIST_N = int(os.environ.get("CS_SHORTLIST", "15"))        # the recipe says 15; the real run used 12

# --- Step B: pull each competitor's pages -----------------------------------
PAGES_PER_COMPETITOR = int(os.environ.get("CS_PAGES", "300"))  # recipe: top 300 by referring domains

# Fields we depend on — asserted on first use so a missing one is LOUD, never a silent empty column.
# (`page` not `url` — the 2026-07-20 lesson, recorded in _shared/dfs-fit-report.md.)
PAGE_FIELDS = ["page", "status_code", "page_summary.referring_domains", "page_summary.backlinks"]

# RANKING METRIC (Devansh, 2026-07-20): rank on FOLLOW referring domains, not the raw total.
# Measured on testgorilla.com: 17 of the top 100 pages are >40% nofollow and four are ~100% nofollow —
# including what looked like the #2 link magnet (343 domains, 340 nofollow). Nofollow passes no
# authority, and authority flow is the entire point of the reverse-silo. Both numbers are kept.
RANK_ON_FOLLOW = os.environ.get("CS_RANK_ON_FOLLOW", "1") == "1"

# --- Step C: the filter -----------------------------------------------------
# Every list here is GENERIC — no company or niche words. The recipe's scar (L247-250): matching
# against the full URL made "keep anything with 'test' in it" match every page on testgorilla.com,
# so step_c matches the PATH only, never the domain.
# BLACKLIST, not a whitelist. I first used a whitelist (www/blog/resources/learn/insights/guides) and
# it threw away research. and webinar. subdomains — which are exactly the content assets this study
# exists to find. The recipe's rule is "over-dropping is unrecoverable; over-keeping isn't", so we now
# name the subdomains that are definitely NOT editorial and keep everything else.
DENY_SUB = set(s for s in os.environ.get("CS_DENY_SUB",
    "help,docs,support,kb,knowledgebase,knowledge,faq,app,apps,api,status,portal,login,auth,account,"
    "dashboard,admin,my,secure,billing,pay,checkout,cdn,static,assets,img,images,media,files,download,"
    "downloads,mail,email,smtp,ftp,git,dev,test,staging,stage,qa,sandbox,demo,preview,beta,"
    "candidates,candidate,applicant,applicants,jobs,careers,recruit,hire,partners,partner,"
    "community,forum,forums,discuss,chat,shop,store,pay,invoice,track,link,go,click,email").split(",") if s)
LOCALES = {"fr","de","es","nl","ja","it","pt","ru","zh","ko","ar","pl","tr","sv","da","no","fi","cs",
           "hu","ro","el","he","hi","id","th","vi","uk","bg","hr","sk","sl","et","lv","lt","ms","fa",
           "pt-br","zh-cn","zh-tw","en-gb","en-au","en-ca","en-in"}
PAGINATION_SEGS = {"page","pages","p"}
JOB_SEGS = {"jobs","job","careers","career","vacancies","vacancy","hiring","openings","positions"}
# Generic commercial/utility paths — the kind of page every SaaS has and nobody links to as a resource.
DROP_PATH_SUBSTR = [s for s in os.environ.get("CS_DROP_PATHS",
    "/pricing,/login,/signin,/sign-in,/signup,/sign-up,/register,/checkout,/cart,/account,"
    "/dashboard,/admin,/legal,/privacy,/terms,/cookie,/gdpr,/dpa,/security-policy,/sitemap,"
    "/contact,/demo,/book-a-demo,/free-trial,/trial,/subscribe,/unsubscribe,/thank-you,"
    "/404,/search,/tag/,/tags/,/category/,/categories/,/author/,/feed,/rss,/amp/,"
    "/wp-content,/wp-admin,/wp-json,/cdn-cgi,/.well-known").split(",") if s]
# Link floor. Set to 1 — drop only pages with ZERO authority-passing links, nothing more.
# I first set this to 2 and it dropped 1,487 pages (22% of everything), taking the keep rate to 44%
# against the hand-run's 69%. The recipe has no such floor and warns "over-dropping is unrecoverable;
# over-keeping isn't" (L239-245). It also matters for Step F: the format summary SUMS referring
# domains across pages, so 200 pages carrying 1 domain each is 200 domains of real signal — dropping
# them silently understates that format. Focus effort at Step E (what to read in full), not here.
MIN_FOLLOW_DOMAINS = int(os.environ.get("CS_MIN_FOLLOW", "1"))
# Loud when a competitor collapses — the eSkill/TalentLyft scar (they fell to 38 and 22 pages).
LOW_KEEP_ALARM = int(os.environ.get("CS_LOW_KEEP_ALARM", "40"))

# --- Step D: format tagging (LLM judgment, was a regex) ----------------------
TAG_BATCH = int(os.environ.get("CS_TAG_BATCH", "25"))     # pages per call — headings only, so they fit
TAG_WORKERS = int(os.environ.get("CS_TAG_WORKERS", "4"))  # concurrent calls

# --- Step E: read every kept page (reuses Layer 00's fetcher + extractor) ----
READ_WORKERS = int(os.environ.get("CS_READ_WORKERS", "6"))
MIN_BODY_WORDS = int(os.environ.get("CS_MIN_BODY_WORDS", "80"))   # under this = FETCH FAILED, never "(from title)"
DUP_BODY_ALARM = int(os.environ.get("CS_DUP_BODY", "8"))          # N identical bodies = a template, not content
PER_DOMAIN_RPS = float(os.environ.get("CS_RPS_PER_DOMAIN", "1.0"))  # requests/sec to EACH site
COMPETITOR_PARALLEL = int(os.environ.get("CS_PARALLEL_COMPETITORS", "6"))  # sites read at once
# Step E patience — deliberately impatient vs Layer 00 (see step_e_read._layer00 for why)
BLOCK_COOLDOWN = int(os.environ.get("CS_BLOCK_COOLDOWN", "0"))   # Layer 00 uses 120s; we skip
FETCH_ATTEMPTS = int(os.environ.get("CS_FETCH_ATTEMPTS", "2"))   # Layer 00 uses 6
FETCH_TIMEOUT = int(os.environ.get("CS_FETCH_TIMEOUT", "12"))    # Layer 00 uses 30

# --- Step F: format aggregation ---------------------------------------------
# A format one competitor happens to own is not a proven format — the recipe wants shapes that earn
# links across the niche, not a single site's quirk.
FORMAT_MIN_COMPETITORS = int(os.environ.get("CS_FMT_MIN_COMPS", "3"))
FORMAT_MIN_PAGES = int(os.environ.get("CS_FMT_MIN_PAGES", "5"))
BLOCK_GIVE_UP = int(os.environ.get("CS_BLOCK_GIVE_UP", "5"))  # consecutive blocks before abandoning a host (D17)
GLOBAL_INFLIGHT = int(os.environ.get("CS_GLOBAL_INFLIGHT", "40"))  # Layer 00 caps at 6 GLOBALLY; per-host politeness is enforced separately

# --- Step G: rows -> ideas ---------------------------------------------------
# G1 dedup FLAG (not delete): rows whose body is byte-identical to another are redundant for idea-
# writing (the merge would collapse them anyway) — flag so G2 reasons over each unique text ONCE and
# never writes the same idea N times. Their backlink value is PROTECTED (kept in the master, counted
# in F). A whole GROUP that is nav/soft-404 is a different problem, handled by E's duplicate-body kill.
G_DEDUP_FLAG = os.environ.get("CS_G_DEDUP_FLAG", "1") == "1"

# G2 per-row reasoning: tiny batches keep the model reading EACH page instead of pattern-matching
# across a block (the recipe's rule — 5 rows, never a big block). Sharded by format so like pages
# travel together (cleaner G3 merge). Fast mid-tier model for the bulk; strong model reserved for G3.
G2_BATCH = int(os.environ.get("CS_G2_BATCH", "5"))            # rows per reasoning pass — NEVER raise past ~5
G2_WORKERS = int(os.environ.get("CS_G2_WORKERS", "6"))        # parallel reasoning passes
G2_MODEL = os.environ.get("CS_G2_MODEL", "claude-sonnet-5")   # mid-tier for the ~480 bulk passes
G2_BODY_CHARS = int(os.environ.get("CS_G2_BODY_CHARS", "6000"))  # page text handed per row (title+headings+body)

# G3 merge: one strong-model pass over compact lines (Row ID · Asset · Format · Competitor · Domains).
# If the asset list is huge, fall back to "decide the ideas, then place the rows" (recipe G3 step 2).
G3_MODEL = os.environ.get("CS_G3_MODEL", "claude-opus-4-8")   # strong model for the classification
G3_PLACE_FALLBACK = int(os.environ.get("CS_G3_FALLBACK", "1200"))  # assets above this -> two-pass place
G3_PLACE_BATCH = int(os.environ.get("CS_G3_PLACE_BATCH", "40"))    # rows per placement batch in the fallback
G3_DECIDE_CHUNK = int(os.environ.get("CS_G3_DECIDE_CHUNK", "250"))  # assets per Pass-A slice; each decided then reconciled (bounded calls)
G3_RECON_GROUP = int(os.environ.get("CS_G3_RECON_GROUP", "120"))  # ideas per reconcile-merge group; hierarchical, bounded calls

# --- Step G2.5: semantic de-dup (Voyage embed -> candidate clusters -> LLM decides merge/keep) --------
# The embedding only PROPOSES candidates; the LLM decides. Measured 2026-07-21 on real titles: true twins
# score ~0.83 (Voyage voyage-4-large), genuinely-different ideas ~0.5-0.66, and a danger band ~0.72-0.80
# where different builds (a glossary vs a test library) can look close. So the threshold is set to gather
# candidates generously and let the LLM separate them — never to auto-merge on cosine alone.
DEDUP_THRESHOLD = float(os.environ.get("CS_DEDUP_THR", "0.80"))   # cosine to become a merge CANDIDATE
DEDUP_TOPK = int(os.environ.get("CS_DEDUP_TOPK", "6"))            # nearest neighbours considered per idea
DEDUP_MAX_CLUSTER = int(os.environ.get("CS_DEDUP_MAXCL", "10"))   # cap a cluster so an LLM pass stays small
DEDUP_MODEL = os.environ.get("CS_DEDUP_LLM", "claude-sonnet-5")   # the adjudicator (pairwise, cheap task)
DEDUP_WORKERS = int(os.environ.get("CS_DEDUP_WORKERS", "6"))  # parallel cluster adjudications (CLI calls at once)
