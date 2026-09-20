"""Run STORM through a headless Claude Code or Codex shim + DataForSEO deep-RAG retriever.
Usage: python run_storm.py "TOPIC" [--provider claude|codex|deepseek] [--model MODEL] [--article] [--polish]
                          [--perspectives N] [--turns N] [--topk N] [--hub HUB]
                          [--folder SLUG] [--spine-file PATH] [--title T] [--angle A]

The article BRIEF (2026-08-03): --spine-file points at the conductor's spine.json
({"title","angle","spine","about","not_about"}). Its fields — overridable by --title/--angle — are
registered in knowledge_storm.brief and reach the researcher picker, every question, the outline and
every section. --folder names the output folder (the pipeline slug), so the topic string no longer has
to double as a folder name. All new flags optional: a bare run behaves exactly as before.
"""
import os, sys, time, tempfile

# dspy's cross-run answer-cache is turned OFF — every run is genuinely fresh. DSP_CACHEBOOL=False makes
# caching a no-op; DSP_CACHEDIR sends the (unused, empty) joblib stub into the system temp dir so nothing
# lands in your home folder or this project. Must be set before knowledge_storm (→ dsp) is imported.
os.environ["DSP_CACHEBOOL"] = "False"
os.environ.setdefault("DSP_CACHEDIR", os.path.join(tempfile.gettempdir(), "dsp_cache_off"))

# Load DataForSEO creds (DFS_LOGIN / DFS_PW) — from THE canonical repo .env first ("Backlink gets
# Automated/.env", the ONE place to rotate), with the legacy storm/.env as back-compat fallback.
# Real env vars, if already set, win over both (load_dotenv never overrides existing).
from dotenv import load_dotenv
_storm_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.normpath(os.path.join(_storm_dir, "..", "..", "..", ".env")))   # canonical (wins of the two)
load_dotenv(os.path.join(_storm_dir, ".env"))                                       # legacy fallback

# Make knowledge_storm importable from the VISIBLE local source (./engine) resolved from THIS file's
# location — rename-proof. The venv's `_storm_local.pth` bakes in an ABSOLUTE path that silently breaks on
# any folder move: the 02->03 content-machine renumber orphaned it (ModuleNotFoundError: knowledge_storm).
# A __file__-relative insert never drifts, whatever the folder is renumbered to.
sys.path.insert(0, os.path.join(_storm_dir, "engine"))

from knowledge_storm.storm_wiki.engine import (
    STORMWikiRunner, STORMWikiLMConfigs, STORMWikiRunnerArguments)
from knowledge_storm.lm import LitellmModel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataforseo_rm import DataForSEORM

SHIM = os.environ.get("SHIM_URL", "http://127.0.0.1:8081/v1")
DEEPSEEK_BASE = "https://api.deepseek.com"

def arg(flag, default):
    return int(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default

def value(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default

def mk(max_tokens):
    if provider == "deepseek":
        # DEEPSEEK_API_KEY is already in os.environ — the load_dotenv() calls above pulled it in from
        # the canonical repo .env. Direct HTTPS to DeepSeek's real API; no local shim needed at all.
        key = os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise SystemExit("no DEEPSEEK_API_KEY — set it in the canonical 'Backlink gets Automated/.env'")
        ds_model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        return LitellmModel(model=f"openai/{ds_model}", api_key=key, api_base=DEEPSEEK_BASE,
                            max_tokens=max_tokens, temperature=1.0, top_p=0.9)
    return LitellmModel(model="openai/claude-code", api_key="sk-local", api_base=SHIM,
                        max_tokens=max_tokens, temperature=1.0, top_p=0.9)

topic = sys.argv[1]
provider = value("--provider", os.environ.get("LLM_PROVIDER", "claude")).lower()
model = value("--model", os.environ.get("LLM_MODEL", ""))
if provider not in {"claude", "codex", "deepseek"}:
    raise SystemExit("--provider must be 'claude', 'codex', or 'deepseek'")
persp = arg("--perspectives", 3)
turns = arg("--turns", 3)
topk = arg("--topk", 3)
do_article = "--article" in sys.argv
do_polish = "--polish" in sys.argv
hub = value("--hub", "")            # nest a spoke's STORM run under its pillar: storm/out/<hub>/<folder>/ (empty = flat)
folder = value("--folder", "")      # output folder name (the pipeline slug); empty = legacy (derived from topic)
spine_file = value("--spine-file", "")   # conductor's spine.json → the article brief for every prompt

cfg = STORMWikiLMConfigs()
cfg.set_conv_simulator_lm(mk(500))
cfg.set_question_asker_lm(mk(500))
cfg.set_outline_gen_lm(mk(800))
cfg.set_article_gen_lm(mk(4000))
cfg.set_article_polish_lm(mk(16000))

# Output lives under projects/<company>/content-machine/, never inside the workflow repo.
# __file__ = .../workflows/03-content-machine/11-storm/scripts/run_storm.py  → 5 dirnames up = Backlink gets Automated
_bga = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
COMPANY = os.environ.get("COMPANY", "testlify")   # the tenant switch (was hardcoded — split-brain, Phase 1.2)
out_dir = os.path.join(_bga, "projects", COMPANY, "03-content-machine", "storm", "out", hub)   # hub="" → flat .../out/

# THE COMPANY RECORD — market + research identity come from projects/<company>/company.json.
# Missing record for a NON-default company = hard stop (fail closed).
import json as _json
_tenant_p = os.path.join(_bga, "projects", COMPANY, "company.json")
try:
    with open(_tenant_p) as _f:
        TENANT = _json.load(_f)
except FileNotFoundError:
    if COMPANY != "testlify":
        raise SystemExit(f"!! no company record at {_tenant_p} — create it before running (revamp Phase 1.1)")
    TENANT = {}

args = STORMWikiRunnerArguments(output_dir=out_dir, max_conv_turn=turns, max_perspective=persp,
                                search_top_k=topk, retrieve_top_k=8,
                                # Concurrency default is PROVIDER-AWARE: DeepSeek is a real API with a huge
                                # concurrency ceiling (confirmed 500-2500 at once), so it gets a higher default.
                                # Claude/Codex are headless CLIs that stall under heavy parallel load (the
                                # freeze we hit earlier today) — they keep the proven-safe default of 3.
                                # Still env-overridable either way; a claude/codex run never silently
                                # inherits deepseek's higher number.
                                max_thread_num=int(os.environ.get("STORM_MAX_THREAD",
                                                                   "8" if provider == "deepseek" else "3")))
# Market from the record. These constructor defaults were previously unreachable (no caller passed them),
# so a non-US tenant could not run STORM correctly at all. [revamp Phase 1.5]
rm = DataForSEORM(k=topk, location=TENANT.get("location", "United States"),
                  language=TENANT.get("language", "en"))
# Research identity for the persona step's Wikipedia fetches (was a hardcoded TestlifyResearch UA —
# every tenant's research announced itself as Testlify). persona_generator reads this env. [Phase 1.6]
os.environ.setdefault("RESEARCH_UA",
    f"Mozilla/5.0 (compatible; {TENANT.get('brand', 'Testlify')}Research/1.0; +https://{TENANT.get('domain', 'testlify.com')})")
runner = STORMWikiRunner(args, cfg, rm)

# ---- THE ARTICLE BRIEF (2026-08-03) — title/angle/spine/about/not-about for every prompt ----------
# Loaded from the conductor's spine.json (--spine-file); --title/--angle override its fields for ad-hoc
# runs. Registered in knowledge_storm.brief; when nothing is passed, no brief is set and STORM behaves
# exactly as before (Wikipedia persona route, unchanged prompts).
from knowledge_storm import brief as _brief
_sp = {}
if spine_file:
    try:
        with open(spine_file) as _f:
            _sp = _json.load(_f)
    except Exception as _e:
        raise SystemExit(f"!! --spine-file {spine_file} unreadable ({_e}) — refusing to run half-briefed")
_title = value("--title", "") or _sp.get("title", "")
_angle = value("--angle", "") or _sp.get("angle", "")
if _title or _angle or _sp:
    _brief.set_brief(title=_title, angle=_angle,
                     spine=_sp.get("spine", ""), about=_sp.get("about", ""),
                     not_about=_sp.get("not_about", ""),
                     brand=TENANT.get("brand", ""), about_brand=TENANT.get("about", ""))

print(f">>> STORM provider={provider} model={model or 'CLI default'} topic={topic!r} perspectives={persp} turns={turns} topk={topk} "
      f"article={do_article} polish={do_polish} folder={folder or '(from topic)'} brief={'yes' if _brief.has_brief() else 'no'}", flush=True)
t0 = time.time()
runner.run(topic=topic, do_research=True, do_generate_outline=True,
           do_generate_article=do_article, do_polish_article=do_polish,
           folder_name=folder)
runner.post_run()
print(f">>> DONE in {int(time.time()-t0)}s -> {out_dir}", flush=True)
