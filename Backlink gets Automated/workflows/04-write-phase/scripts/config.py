#!/usr/bin/env python3
"""Write-phase settings — the ONE place paths + tunables live (convention C1).

Engine location: workflows/04-write-phase/ (a top-level stage; NOT nested under content-machine).
Turns ONE research bundle into ONE article. Brand-agnostic: set COMPANY; every path derives from one anchor.

LEAN ON PURPOSE: lists ONLY what the currently-built code reads. SEO/AEO thresholds (meta lengths, readability
floors, etc.) are deliberately NOT here — no built station reads them yet. Recipe + design record: ../write-phase-architecture.md.
"""
import os
import sys
import json

# --- the one anchor: everything derives from here ---------------------------
HERE = os.path.dirname(os.path.abspath(__file__))      # .../04-write-phase/scripts
ROOT = os.path.dirname(HERE)                            # .../04-write-phase
WORKFLOWS = os.path.dirname(ROOT)                       # .../workflows
REPO_ROOT = os.path.dirname(WORKFLOWS)                  # .../Backlink gets Automated

COMPANY = os.environ.get("COMPANY", "testlify")        # the one company switch
_PROJ = os.path.join(REPO_ROOT, "projects", COMPANY)
_PROJ_CM = os.path.join(_PROJ, "03-content-machine")   # research outputs (bundle / dataforseo / queue) live per company here
PROMPTS = os.path.join(ROOT, "prompts")                # one .md per LLM call
FORMATS = os.path.join(ROOT, "formats")                # one .md per archetype (the format rulebooks)

# --- the company record (tenant contract) -----------------------------------
def _load_tenant():
    p = os.path.join(_PROJ, "company.json")
    try:
        with open(p) as f:
            return json.load(f)
    except FileNotFoundError:
        if COMPANY != "testlify":
            sys.exit(f"!! no company record at {p} — create it before running")
        return {}
TENANT = _load_tenant()
BRAND = TENANT.get("brand", COMPANY)
ABOUT = TENANT.get("about", "")          # one line on what the company does — injected into judgment prompts

# --- LLM (headless Claude by default; DeepSeek/Codex via LLM_PROVIDER) -------
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
# 300s was too short for the WHOLE-ARTICLE calls (2026-08-13). Blend hands the model the entire piece
# and asks for the entire piece back, so a 6,500-word article is a ~13,000-word round trip. On a
# 15-section article the Claude CLI hit the 5-minute wall, fell through to Codex, and Codex returned a
# reply with no `sections` key — so blend silently kept the body as written: 80 long sentences
# untouched, 0 of 24 keywords woven. A timeout should catch a HUNG process, not a big one.
# 900 WAS STILL TOO SHORT, AND THE SAFETY NET IS GONE (2026-08-27). Same failure again on the glossary
# article: blend on 4,234 words with 151 sourced claims ran past 15 minutes, timed out, and fell to
# Codex — which is now out of quota until late September, so the fallback returned nothing and the step
# looped. The note above assumed a dead Claude call would land on a working Codex. It will not. With one
# provider left, the timeout has to be long enough for the biggest real call rather than short enough to
# fail over quickly.
CLAUDE_TIMEOUT = int(os.environ.get("WRITE_LLM_TIMEOUT", "2400"))

# NO_CLAUDE=1 forbids the two web-search fallbacks that shell out to the Claude CLI directly (enrich and
# verify_sources). Those sit OUTSIDE llm.py, so LLM_PROVIDER / LLM_PROVIDER_CHAIN do not reach them: a
# run pinned to DeepSeek would still spend Claude quota the moment the DataForSEO balance check errored.
# With this set, that path returns nothing and the step records an honest "search unavailable" instead.
NO_CLAUDE = os.environ.get("NO_CLAUDE", "") == "1"
LLM_RETRIES = 1

# --- INPUTS the built code reads (grows per station) ------------------------
LOG_CSV = os.path.join(_PROJ_CM, "research-log.csv")       # the queue — fmt_router reads `format` by slug
BUNDLE = os.path.join(_PROJ_CM, "research-bundle")         # per-topic: <slug>/structure-<slug>.json
DFS_OUT = os.path.join(_PROJ_CM, "dataforseo", "out")      # per-topic: <slug>/research-doc-<slug>.md + proof/
GAPCHECK_OUT = os.path.join(_PROJ_CM, "gap-check", "out")   # per-topic: <slug>/coverage-verdicts.json (research coverage vs the winners)
STORM_OUT = os.path.join(_PROJ_CM, "storm", "out")          # per-topic: <slug>/spine.json (the world + working spine)
BRAND_CTX = os.path.join(_PROJ, "01-brand-context")        # per-company voice pack: brand-voice/style-guide/writing-examples/writing-integrity/features
# (more inputs are added here per station as they are built)

# --- OUTPUT (per company, under this stage — convention A1) ------------------
WRITE_OUT = os.path.join(_PROJ, "04-write-phase", "out")   # <slug>/plan-inputs.json, article-plan.draft.json, coverage.json, ...

# --- selection (Station 1b) tunables ----------------------------------------
# The four size caps are set effectively UNLIMITED (Devansh, 2026-07-27): show the judge and the writer
# everything, never truncate. If a model's context window overflows, dial one down via its env var.
SELECT_CARDS_PER_H2 = int(os.environ.get("SELECT_CARDS_PER_H2", "10000000"))      # cards SHOWN to the judge per H2 (uncapped)
SELECT_VERBATIM_CHARS = int(os.environ.get("SELECT_VERBATIM_CHARS", "10000000"))  # per-card text shown to the judge (uncapped)
SELECT_CONCURRENCY = int(os.environ.get("SELECT_CONCURRENCY", "8"))   # the ONE concurrency owner (llm.max_workers reads this)
SELECT_H3_COVERAGE = float(os.environ.get("SELECT_H3_COVERAGE", "0.45"))  # an H2 survives at >= this fraction of tagged H3s
# How many internal links an article should carry, expressed as one link per N words. Was a flat
# "3 to 5 across the whole article" in the prompt, which gave a 5,000-word piece the same allowance as
# a 900-word one — the AI hit the ceiling and turned down links it had already judged good ("sits
# between two stronger links"). 400 words per link is ~2.5 per 1,000, the normal range.
WORDS_PER_INTERNAL_LINK = int(os.environ.get("WORDS_PER_INTERNAL_LINK", "400"))
MIN_INTERNAL_LINKS = int(os.environ.get("MIN_INTERNAL_LINKS", "3"))    # the floor for a short article

# --- how an internal-link candidate is FOUND (the retrieval proven by 02's reuse-check) ---
# Until 2026-08-06 a section was matched against page TITLES only: a heading compared to a headline,
# neither side carrying a word of real content. That is how "work sample test" landed on the job-
# simulation page. Same recipe as 5-reuse-check now: blend the title and best body chunk, then rerank.
LINK_ALPHA = float(os.environ.get("LINK_ALPHA", "0.5"))            # title weight in the blend; 1-ALPHA is body
LINK_N_RETRIEVE = int(os.environ.get("LINK_N_RETRIEVE", "40"))     # dense candidates handed to the reranker
LINK_PER_SECTION = int(os.environ.get("LINK_PER_SECTION", "8"))    # shortlist size shown to the judge
LINK_RERANK_DOC_CHARS = int(os.environ.get("LINK_RERANK_DOC_CHARS", "4000"))  # per-page text sent to rerank
LINK_EXCERPT_CHARS = int(os.environ.get("LINK_EXCERPT_CHARS", "800"))  # per-page opening shown to the judge
# The floor. 0.0 = OFF, which is deliberate: pick it from the measured spread of real scores, never
# from a guess. Below it a section is offered nothing, because no link beats a wrong link.
LINK_MIN_SCORE = float(os.environ.get("LINK_MIN_SCORE", "0.0"))
# Display only: a placed link scoring under this is flagged "weak" on the review page, so a human can
# see the shaky picks without the floor silently deleting them first.
LINK_WEAK_SCORE = float(os.environ.get("LINK_WEAK_SCORE", "0.45"))

# THE PARAGRAPH MATHS (2026-08-09, Devansh). The architect had two rules that could not both hold: a
# section "needs roughly 300 words", and a section is "2 or 3 paragraphs, split it with H3s if more".
# Nothing said what a paragraph was worth, so every normal section landed on the wrong side of the
# line and got split. Measured on the first rerun: 26 sub-headings on a 3,300-word article, 36
# headings in total, 91 words each — one section was 165 words across 4 sub-headings.
# The fix is to make the two agree: a paragraph is 4 sentences, so a 3-paragraph section IS 300 words.
# WORDS_PER_SECTION stays at 300 and sections stay H2s only; only the paragraph maths is new.
WORDS_PER_SENTENCE = int(os.environ.get("WORDS_PER_SENTENCE", "25"))            # the house sentence cap
SENTENCES_PER_PARAGRAPH = int(os.environ.get("SENTENCES_PER_PARAGRAPH", "5"))   # -> a paragraph is ~110w
# 4 -> 5 (2026-08-29). The human articles run 3-5 sentences a paragraph. A 4-sentence ceiling
# was being read as a target and pushed the rewrite toward 2-sentence paragraphs, which is a
# fact with its explanation missing.
PARAGRAPHS_PER_SECTION  = int(os.environ.get("PARAGRAPHS_PER_SECTION", "4"))    # -> a section is ~400w
# The third rung of the same ladder (2026-08-27, Devansh). 25 words -> 4 sentences -> 4 paragraphs is
# the shape write-body has always been designed on; readable rebuilds the article and had only the
# first two, so it merged sections into walls of prose. It is also the BUDGET the fat-paragraph fixer
# spends: a paragraph may be split in two only while its section stays under this.
# ^ 4 sentences is also the writer's own pending paragraph rule, so one number now serves both engines
#   instead of each inventing its own. See PENDING-WRITER-CHANGES.md section B.
MIN_WORDS_PER_SUBHEAD = int(os.environ.get("MIN_WORDS_PER_SUBHEAD", "200"))     # 2 paragraphs
# ^ the floor under a sub-heading. Below it, an H3 is a label on a paragraph. allocate_words REPORTS
#   sections that fall under it; it does not yet delete anything (measure before enforcing).
WORDS_PER_SECTION = int(os.environ.get("WORDS_PER_SECTION", "300"))  # the architect is TOLD this, never held to it:
# a section reads well at ~300 words, so budget/300 is the natural section count. SEO consensus is one H2 per
# 250-500 words. Guidance only — no code counts or trims sections, the prompt says "a sense of scale, not a rule".
SHAPE_MIN_YARDSTICK_PCT = int(os.environ.get("SHAPE_MIN_YARDSTICK_PCT", "60"))  # a comparison option needs info for >= this % of yardsticks to keep its section
# The hard ceiling on how many items a listicle may carry (2026-08-08). Replaced a sliding formula
# — max(12, min(30, band_max/250)) — that let a 7,500-word band ask for 30. One number, because the
# house is moving to shorter articles. The AI is told it, and it is not re-checked in code.
LISTICLE_MAX_ITEMS = int(os.environ.get("LISTICLE_MAX_ITEMS", "12"))
# FITTING THE LIST TO THE BUDGET (2026-08-08, Devansh). A listicle used to take every item the
# detector found and let the article run as long as that needed, so a short budget produced a long
# list of stubs. The structure step now does the arithmetic, because it is the only step that knows
# BOTH the item count and the word budget. Three numbers, all guidance in the prompt (no code trims):
LISTICLE_SUPPORTING_SECTIONS = int(os.environ.get("LISTICLE_SUPPORTING_SECTIONS", "3"))
# ^ how many supporting sections (how the list was chosen, how to use it, what next) to RESERVE
#   words for BEFORE dividing the rest among the items. Supporting sections always exist, so they
#   come out first rather than living on the leftovers. Reserve = this x WORDS_PER_SECTION.
#   NOTE: this is the one number tied to article length. It is a flat word count, so if the house
#   word band ever drops a lot (say to 1,500), 900 reserved words eat more than half the article and
#   this should become a PERCENTAGE of the budget instead. Revisit it then, not before.
LISTICLE_MIN_ITEM_WORDS = int(os.environ.get("LISTICLE_MIN_ITEM_WORDS", "200"))
# ^ below this an item is a stub. A shorter list fully written beats a longer list of stubs.
LISTICLE_MIN_ITEMS = int(os.environ.get("LISTICLE_MIN_ITEMS", "5"))
# ^ the floor. Fewer than this and it has stopped being a list, so it keeps the strongest and says so
#   rather than quietly turning into a different format.
ENRICH_QUERIES_PER_H3 = int(os.environ.get("ENRICH_QUERIES_PER_H3", "3"))   # web queries planned per researched H3
ENRICH_PAGES_PER_H3 = int(os.environ.get("ENRICH_PAGES_PER_H3", "15"))      # best-loading pages downloaded per H3
ENRICH_PAGE_CHARS = int(os.environ.get("ENRICH_PAGE_CHARS", "8000"))        # top slice of each page fed to the card builder
DFS_MIN_CREDITS = float(os.environ.get("DFS_MIN_CREDITS", "1.0"))           # below this DataForSEO balance, research falls back to Claude web

# --- word allocation (architect Step 3) -------------------------------------
# The allocator used to be shown only a CARD COUNT per section, while its prompt told it not to judge
# by card count — it was handed the one number it was forbidden to use and nothing it could use
# instead. It now sees the facts themselves (glosses), and the prompt treats them as a CEILING (can
# this section be written to that length?) rather than a claim on words. These two are display caps,
# not tuning knobs: one real section held 110 cards, and an unbounded block next to a 2-card section
# reads as "give me more words", which is the bias the whole rule exists to prevent.
ALLOC_CARDS_PER_SECTION = int(os.environ.get("ALLOC_CARDS_PER_SECTION", "60"))  # facts shown per section
# AIM LOW ON PURPOSE (2026-08-11). Measured across the last run: every section overshot its target and
# the finished articles ran 14% to 44% over their band. Rather than add a rule the writer ignores, the
# architect now allocates against a band shrunk by this much, so an overshoot lands back inside the
# real band instead of outside it. The TRUE band is untouched in plan-inputs.json and article-plan.json,
# and blend still measures the finished article against that truth — this only moves the aim.
ARCH_BAND_SHRINK = float(os.environ.get("ARCH_BAND_SHRINK", "0.10"))
ALLOC_GLOSS_CHARS = int(os.environ.get("ALLOC_GLOSS_CHARS", "200"))             # per fact, one line

# --- field sources: what practitioners actually say (2026-08-11) -------------
# Reddit, Teamblind and LinkedIn. Three adapters, one contract: search() and fetch(). All three are
# searched every time; the article's own probe decides what was worth reading. The subreddit list comes
# from 01-brand-context/9-field-sources, because Reddit cannot be searched without naming communities.
FIELD_SOURCES_MD = os.path.join(BRAND_CTX, "field-sources.md")   # per company: the checked subreddits
FIELD_CATALOGUE = os.path.join(WORKFLOWS, "01-brand-context", "9-field-sources", "sources.md")
FIELD_THROTTLE = float(os.environ.get("FIELD_THROTTLE", "2.0"))   # seconds between requests
FIELD_PROBE_ROUNDS = int(os.environ.get("FIELD_PROBE_ROUNDS", "3"))  # search rounds before giving up
FIELD_MAX_READ = int(os.environ.get("FIELD_MAX_READ", "12"))      # threads whose comments we download
FIELD_COMMENTS_PER = int(os.environ.get("FIELD_COMMENTS_PER", "12"))  # top comments kept per thread
FIELD_COMMENT_CHARS = int(os.environ.get("FIELD_COMMENT_CHARS", "700"))

# The paid Reddit path. old.reddit is free but rate-limits an IP that scrapes hard, and then serves a
# LOGIN PAGE with HTTP 200 — which parses as "no results" unless you look for it. The key lives in the
# user's own config OUTSIDE this repo, so it never travels with the code.
SC_REDDIT = "https://api.scrapecreators.com/v1/reddit"
SC_ENV = os.path.expanduser(os.environ.get("SC_ENV", "~/.config/last30days/.env"))


def sc_key():
    k = os.environ.get("SCRAPECREATORS_API_KEY", "")
    if k:
        return k
    try:
        for line in open(SC_ENV):
            if line.startswith("SCRAPECREATORS_API_KEY="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


# --- the company's own material (architect Step 3, 2026-08-10) ---------------
# The pool is built once per company by workflows/01-brand-context/8-brand-cards. Two kinds, rationed
# differently on purpose: RESEARCH is the company's own study — neutral data about its market, so it
# reads as evidence. RESULTS are what a named customer achieved with the product, so every one is the
# company arguing for itself. The prompt ASKS for these limits; brand_cards.py ENFORCES them.
BRAND_CARDS_POOL = os.path.join(BRAND_CTX, "brand-cards.json")
BRAND_RESEARCH_CAP = int(os.environ.get("BRAND_RESEARCH_CAP", "4"))          # per article
BRAND_RESEARCH_PER_SECTION = int(os.environ.get("BRAND_RESEARCH_PER_SECTION", "1"))
BRAND_RESULT_CAP = int(os.environ.get("BRAND_RESULT_CAP", "1"))              # per article; usually 0
BRAND_FACTS_SHOWN = int(os.environ.get("BRAND_FACTS_SHOWN", "12"))           # existing facts per group

# --- write (Station 2) tunables ---------------------------------------------
BODY_VOICE_CHARS = int(os.environ.get("BODY_VOICE_CHARS", "10000000"))    # per voice-file text injected into each section prompt (uncapped)
BODY_CARD_CHARS = int(os.environ.get("BODY_CARD_CHARS", "10000000"))      # per-card verbatim shown to the writer (uncapped)

# --- section-keyword research (architect Step 4, 2026-08-04) ----------------
# The paid DataForSEO client + its keyword floors, used ONLY by section_keywords.py. These mirror the
# research engine's own thresholds so a section keyword clears the same bar the article's primary did.
DFS_SCRIPTS = os.path.join(WORKFLOWS, "03-content-machine", "10-dataforseo", "scripts")
LOCATION = TENANT.get("location", "United States")   # DataForSEO market — from the company record
LANGUAGE = TENANT.get("language", "en")
VOL_FLOOR = int(os.environ.get("KW_VOL_FLOOR", "100"))   # a section keyword needs >= this monthly volume
# How many HEADINGS may carry the same phrase (2026-08-09, Devansh). Step 5a writes each heading in
# parallel and blind, so every writer is offered the primary and every writer honestly answers "yes it
# fits" — the cost-per-hire article came out with "cost per hire" frozen into 7 of 12 headings plus the
# H1. Step 5b is the only step that sees the set, so it is told to keep the phrase in at most this many
# and strip it from the rest. Two-sided: at most N is asked for, AT LEAST N is enforced in code, so a
# keyword we paid for can never vanish from the page entirely.
MAX_HEADINGS_PER_KEYWORD = int(os.environ.get("MAX_HEADINGS_PER_KEYWORD", "2"))

# THE SAME PROBLEM, WITH FIGURES (2026-08-27, Devansh). Step 5a writes every heading alone, holding a
# pile of evidence, and each writer reaches for its best statistic — on the resume-statistics article
# 10 of 12 headings led with a number, and the article read like a spreadsheet. Expressed as a
# FRACTION of the article's sections, not a flat count, so a 6-section piece and a 20-section piece
# are held to the same shape. 1 in 3 is the agreed line; the floor is 1, so a single section whose
# whole job is to demolish a number never has to give it up.
FIGURE_HEADING_SHARE = float(os.environ.get("FIGURE_HEADING_SHARE", "0.34"))
KD_CEIL   = int(os.environ.get("KW_KD_CEIL", "40"))      # ... and difficulty below this

# THE brand file the body writer reads. ONE file, built per company by 01-brand-context/7-writer-brief.
# Until 2026-08-10 seven files went in whole (~26,600 words) under a single line, "match these". Most of
# it governed other steps' work, some was facts the writer could not cite, and several contradicted each
# other. VOICE_FILES is kept only for the wrapper, which still injects the old pack.
BRIEF_FILE = os.environ.get("BRIEF_FILE", "writer-brief.md")
VOICE_FILES = ["brand-voice.md", "style-guide.md", "writing-integrity.md", "opinions.md",
               "stats.md", "stories.md", "writing-examples.md"]
# The WRAPPER writes the first thing a reader sees and the last, and until 2026-08-06 it was the only
# writing step with NO brand voice at all — the sections under it get ~171KB of guidance, the opening
# got none. It gets the three files that govern how a sentence SOUNDS; stories/stats are source
# material for the body, not for a three-sentence intro. Trimmed, because this prompt already carries
# the whole article.
WRAP_VOICE_FILES = ["brand-voice.md", "style-guide.md", "writing-examples.md"]
WRAP_VOICE_CHARS = int(os.environ.get("WRAP_VOICE_CHARS", "6000"))   # per file, into the wrapper prompt
# features.md went in UNCAPPED at 69KB, four times the whole voice payload, for a job that produces
# three to five sentences of close. Capped 2026-08-11.
WRAP_FEATURES_CHARS = int(os.environ.get("WRAP_FEATURES_CHARS", "8000"))
# The CTA page list is short by design (8 pages for testlify), so this ceiling only ever bites for a
# company with a very wide product surface. It is here so one file cannot crowd out the features.
WRAP_CTA_CHARS = int(os.environ.get("WRAP_CTA_CHARS", "6000"))

# --- Writer Step 9, the readability rewrite ---------------------------------
# Flesch Reading Ease, now a BAND, not a floor (2026-08-29, Devansh).
# MEASURED, not guessed: the human-written Testlify articles Devansh holds up as the target score
# 28 and 35 on this formula. The old floor of 60 would have failed both of them. Chasing 60 is what
# produced the telegraphic register he rejected: the step hit 71 by deleting every explanation and
# keeping only the dense factual clause, which is the opposite of readable.
# So the floor drops to 45 (about where the raw writer draft already lands) and a CEILING goes on,
# because a score above the ceiling now means the prose went clipped, not clear.
READABLE_EASE = float(os.environ.get("READABLE_EASE", "45"))
READABLE_EASE_MAX = float(os.environ.get("READABLE_EASE_MAX", "72"))

# HOW MUCH ROOM EACH FACT GETS (2026-08-29, Devansh). The real disease behind "it reads badly".
# Measured across all six articles at the coherence step: one sourced fact every 30 to 56 words.
# The human articles carry one every ~250. At that density every sentence is a citation, so no
# sentence sets up, explains, or gives an example, and the page reads as a list of true things.
# This is the number the readable step is now steered by: it must cut FACTS to buy room, not
# compress facts into clauses. 110 is a deliberate first step toward the human figure, not the
# destination. Raise it toward 200 once the shape is right.
READABLE_WORDS_PER_FACT = int(os.environ.get("READABLE_WORDS_PER_FACT", "110"))
# HOW LONG THE REWRITE MAY HAND BACK (2026-08-26). One flat number, not a percentage. It began as
# "never go above the length you were handed", which is a ceiling a one-word cut satisfies, and it
# cut 3%. It then became "a quarter off, capped here", which let a 6,000-word article settle at
# 4,500 and pass. So the cap IS the target: at most this, and never longer than it came in.
# The prompt states the same number in words (readable.md, line 7) — change both together.
# KEEP THIS EQUAL TO THE NUMBER WRITTEN INTO prompts/readable.md (2026-08-27, Devansh). They drifted
# once: the prompt said 1,600 while this said 2,500, so the model aimed at the lower number and the
# check measured against the higher one and passed it. Three articles came out near 1,400 words
# against architect plans of 3,500-5,500, and the sections squeezed hardest were the ones that lost
# their visible citations. Change one, change the other, in the same commit.
READABLE_CEILING = int(os.environ.get("READABLE_CEILING", "2100"))

# --- how much of the research a READER meets (2026-08-22, the SEO reviewer's notes) ---------
# The pipeline gathers and verifies everything; that is its job and it stays. These three caps
# govern how much of it reaches the page, which is a different question. Measured before changing
# them: one article carried 151 numbers, one section was handed 92 facts, and a single source was
# marked 20 times. None of that is more trustworthy than three well-placed figures. It is louder.
# How many of the topics every ranking page covers reach the architect. A long list reads as a
# checklist and pushes the article toward being the tenth copy of a page that already ranks.
MAX_TABLE_STAKES = int(os.environ.get("MAX_TABLE_STAKES", "7"))
BODY_MAX_STATS = int(os.environ.get("BODY_MAX_STATS", "3"))          # statistics per SECTION (prompt + flag)
EXTERNAL_LINKS_MAX = int(os.environ.get("EXTERNAL_LINKS_MAX", "4"))  # visible outbound links per article
CITATION_MAX_REPEATS = int(os.environ.get("CITATION_MAX_REPEATS", "3"))  # times ONE source may be marked


# THE FAQ (reviewer, 2026-08-11). An FAQ answer is what a search engine lifts and shows on its own,
# so it has to be complete in one breath. Every answer written before this rule ran 47-146 words.
WRAP_FAQ_WORDS = int(os.environ.get("WRAP_FAQ_WORDS", "40"))
# Code MEASURES the FAQ and never edits it. A length ceiling that deleted answers, and a check that
# deleted an answer carrying a figure the body lacked, were both built and both removed on 2026-08-11:
# the FAQ is deliberately allowed to answer past the article, so an outside figure is expected, and a
# long answer is a thing to see on the review page rather than something code silently removes.
WRAP_FAQ_COUNT = int(os.environ.get("WRAP_FAQ_COUNT", "5"))
# The TL;DR block (was "Quick answer"). Under 60 words it says nothing; over 110 it is a second intro.
QUICK_MIN = int(os.environ.get("QUICK_MIN", "60"))
QUICK_MAX = int(os.environ.get("QUICK_MAX", "110"))   # a ceiling. Three real questions beat five padded.

# BLEND (rebuilt 2026-08-11). Code counts what a model counts badly, and hands the editor an exact
# list; the editor then judges. Same shape as coherence, which is why coherence went from 1 finding
# to 27. These are the counting thresholds and the guard that can discard a whole edit.
BLEND_SENTENCE_WORDS = int(os.environ.get("BLEND_SENTENCE_WORDS", "25"))   # flag a sentence longer
BLEND_PARA_SENTENCES = int(os.environ.get("BLEND_PARA_SENTENCES", "4"))    # flag a paragraph longer
BLEND_FLAG_SAMPLE    = int(os.environ.get("BLEND_FLAG_SAMPLE", "6"))       # flagged lines shown per section
# The intro, five FAQ answers and the close are written AFTER blend by the wrapper. Blend sees only
# the sections, so it must aim below the band or the finished article lands over it. Measured across
# the four Testlify articles: the wrapper adds 550-750 words.
BLEND_WRAPPER_WORDS  = int(os.environ.get("BLEND_WRAPPER_WORDS", "600"))
# Losing one or two source tags while rewriting is acceptable; losing a quarter of them is not
# editing, it is the model dropping brackets. Same threshold coherence uses.
BLEND_TAG_LOSS_BLOCK = float(os.environ.get("BLEND_TAG_LOSS_BLOCK", "0.25"))

def brand_file(name):        return os.path.join(BRAND_CTX, name)


def artifact_optional(slug, name):
    """Path for a per-article file that MAY not exist and is not in ARTIFACT_ENGINE.

    NOT bundle_dir(): that is the research bundle under 03-content-machine. These files sit beside the
    article's own engines, in out/<slug>/, which is where the step that writes them puts them."""
    return os.path.normpath(os.path.join(
        os.path.dirname(artifact(slug, "structure.json")), "..", name))

# --- per-topic path helpers -------------------------------------------------
def bundle_dir(slug):        return os.path.join(BUNDLE, slug)
def structure_path(slug):    return os.path.join(bundle_dir(slug), f"structure-{slug}.json")
def dfs_dir(slug):           return os.path.join(DFS_OUT, slug)
def research_doc_path(slug): return os.path.join(dfs_dir(slug), f"research-doc-{slug}.md")
def proof_dir(slug):         return os.path.join(dfs_dir(slug), "proof")
def gapcheck_dir(slug):      return os.path.join(GAPCHECK_OUT, slug)
def coverage_path(slug):     return os.path.join(gapcheck_dir(slug), "coverage-verdicts.json")
def out_dir(slug):           return os.path.join(WRITE_OUT, slug)
def format_path(archetype):  return os.path.join(FORMATS, f"{archetype}.md")

# The 3 STRUCTURED formats (a repeating unit measured on the same yardsticks) — the architect regroups their cards
# and builds a matrix. Everything else is LINEAR (reorder/merge/create only). See write-phase-architecture.md.
STRUCTURED_ARCHETYPES = {"comparison-rankings", "listicle", "data-benchmark-report"}
def is_structured(archetype): return archetype in STRUCTURED_ARCHETYPES

# --- engine output folders (one per engine; _work holds intermediates) -------
def _engine_dir(slug, *parts):
    d = os.path.join(out_dir(slug), *parts)
    os.makedirs(d, exist_ok=True)
    return d
def gather_dir(slug):      return _engine_dir(slug, "gather")
def gather_work_dir(slug): return _engine_dir(slug, "gather", "_work")
def planner_dir(slug):     return _engine_dir(slug, "planner")
def planner_work_dir(slug): return _engine_dir(slug, "planner", "_work")
def architect_dir(slug):   return _engine_dir(slug, "architect")
def architect_work_dir(slug): return _engine_dir(slug, "architect", "_work")
def writer_dir(slug):      return _engine_dir(slug, "writer")
def writer_work_dir(slug):  return _engine_dir(slug, "writer", "_work")

# The ONE resolver: artifact filename -> its engine folder. Every script asks this instead of joining paths.
ARTIFACT_ENGINE = {
    "plan-inputs.json": "gather", "gather-review.html": "gather",
    "selection-review.html": "planner", "sources-review.html": "planner",
    "blueprint-review.html": "architect",
    "article-plan.json": "planner", "article-plan.md": "planner",
    "coverage.json": "planner", "source-cuts.json": "planner", "source-fix.json": "planner",
    "_NEEDS-REVIEW.md": "planner",
    "structure.json": "architect", "structure.md": "architect",
    "enriched-cards.json": "architect", "brand-cards-used.json": "architect",
    "blueprint.json": "architect", "blueprint-filled.json": "architect", "blueprint-fills.json": "architect",
    "blueprint-drops.json": "architect", "blueprint-check.json": "architect", "article-blueprint.json": "architect",
    # writer DELIVERABLES (what a human opens) stay on top; every intermediate lives in _work
    "draft.md": "writer", "draft-v1.md": "writer", "article.html": "writer", "slop-review.html": "writer",
    "readable.json": "writer/_work", "readable-report.json": "writer/_work",
    "readable-brief.json": "writer/_work",
    "readable-review.html": "writer",
    # one review page per writer step, so each step's work is shown in exactly one place
    "body-review.html": "writer", "editor-review.html": "writer", "wrapper-review.html": "writer",
    "coherence-review.html": "writer", "clean-review.html": "writer",
    "body.json": "writer/_work", "blend.json": "writer/_work", "wrapper.json": "writer/_work",
    "coherent.json": "writer/_work", "coherence-report.json": "writer/_work",
    "sentences.json": "writer/_work", "sentence-report.json": "writer/_work",
    "sentence-review.html": "writer",
    "polish.json": "writer/_work", "slop-report.json": "writer/_work",
    "scrubbed.json": "writer/_work", "clean-report.json": "writer/_work",
    "linked.json": "writer/_work", "links-report.json": "writer/_work", "links-review.html": "writer",
    "keyword-coverage.json": "writer/_work", "coverage-patch.json": "writer/_work",
    "wrappers.json": "writer/_work", "faq.json": "writer/_work", "product-fit.json": "writer/_work",
    "meta.json": "writer/_work",
}
def artifact(slug, name):  return os.path.join(_engine_dir(slug, *ARTIFACT_ENGINE[name].split("/")), name)

# --- atomic saves (owner: write_atomic.py) ----------------------------------
from write_atomic import write_json, write_text   # noqa: E402,F401


def fresh(outp, *inputs):
    """True when `outp` exists AND is newer than every input that feeds it.

    Added 2026-08-05. Every step used to resume on "does the output file exist", which is not the
    same question as "is it current". It cost three full runs in one day: a draft from 16:30 was
    served after a 22:42 run that had rebuilt the wrapper, the coherence pass and the links. Reuse is
    only safe when nothing upstream has moved since.
    """
    import os as _os
    if not _os.path.exists(outp):
        return False
    t = _os.path.getmtime(outp)
    for p in inputs:
        if p and _os.path.exists(p) and _os.path.getmtime(p) > t:
            return False
    return True
