# Testlify — Pillar &amp; Topic-Cluster Strategy (fine-grained)

**Prepared for:** Devansh Asawa · **Date:** 2026-07-07
**Scope:** 2,972 English blog posts + 1,047 pages from the live sitemap.
**Best way to explore this:** open **[pillar-cluster-map.html](pillar-cluster-map.html)** in a browser — it's the interactive version of everything below.

---

## What changed vs the first version

The first pass produced 8 giant buckets (400–800 posts each). That's useless in practice — **no real pillar article can link to 800 posts.** So this version follows your rule:

> *"Of all these posts, which ones are actually relevant enough to link together in ONE hub article?"*

Every post title was **read individually by an LLM** and grouped into a **tight cluster with a hard cap of 15 spokes.** Where a topic had more than 15 posts, it was split into named siblings (e.g. *Coding Tests — by Language* vs *Coding Tests — Hiring Strategy*). The number of pillars was left unlimited.

**Result: 373 tight pillars, grouped under 11 broad themes.** Average 7.9 posts per pillar. Every one of the 2,972 posts is placed exactly once; nothing invented or duplicated; only 25 true one-off "orphans" remain.

---

## The mental model (unchanged, just finer)

```
THEME            broad area (11 of these)          e.g. "Skills & Job Assessments"
  └─ PILLAR      one hub page, ≤15 linkable spokes  e.g. "Coding & Programming Tests"
        └─ SPOKE individual blog post               e.g. "coding-tests-for-tech-hiring"
```

A **pillar** = the group of posts you *could* link from a single hub article without it feeling random. That's the whole test.

---

## The 11 themes

| Theme | Pillars | Posts | Pillar page today? |
|---|---:|---:|---|
| Interview Questions by Role | 51 | 420 | 🟠 **Build** `/interview-questions/` |
| Skills & Job Assessments | 77 | 581 | 🟢 Exists — `/skills-assessment-platform/` + test-type pages |
| Personality & Aptitude Testing | 18 | 165 | 🟢 Exists — `/psychometric-tests/`, `/cognitive-ability-tests/` |
| Candidate Screening & Proctoring | 36 | 256 | 🟢 Exists — `/anti-cheating-and-proctoring/`, `/ai-resume-screener/` |
| Recruiting & Talent Acquisition | 60 | 483 | 🟠 **Build** `/recruitment-guide/` |
| Hiring by Role & Use-case | 31 | 277 | 🟢 Exists — `/hiring-guides/` + use-case pages |
| Employee Experience & Development | 27 | 194 | 🟠 **Build** `/employee-engagement-guide/` |
| HR Operations & Compliance | 33 | 239 | 🟢 Exists — `/hr-guide/` (12 chapters) |
| Workplace Culture & Future of Work | 16 | 128 | 🟠 **Build** `/future-of-work/` |
| Skills Management | 9 | 60 | 🟢 Exists — `/skills-management/` (your model) |
| Competitor Alternatives | 15 | 144 | 🟢 Exists — `/[competitor]-alternatives/` + `/hr-tools/` |
| **Total** | **373** | **2,972** | 4 themes need a new pillar page |

Full pillar list: **[data/all-pillars.md](data/all-pillars.md)**. Every pillar with its exact posts: **[data/final-clusters.json](data/final-clusters.json)**.

---

## What a real pillar now looks like (examples)

**Interview Questions by Role** → split by role family, each ≤15:
- *Web & Full-Stack Developer Interview Questions* (15) — angular / backend / frontend / app developer …
- *Sales Role Interview Questions* (15) — account executive / account manager / inside sales …
- *Finance & Investment Role Interview Questions* (15) — financial advisor / analyst / administrator …

**Skills & Job Assessments**:
- *Evaluating Marketing Skills in Candidates* (15) — content-marketing / brand-management / SEO skills …
- *Talent Assessment: Fundamentals, Benefits & Getting Started* (14)

**Employee Experience & Development**:
- *Succession Planning* (15) — a tight, high-value cluster that had no home before
- *Employee Engagement Strategies & Programs* (15)

Each of these is a realistic hub article: one page, ~15 contextual links, all genuinely on-topic.

---

## How this maps to action

**1. The 4 themes marked 🟠 Build are your highest-leverage work** — big clusters of posts with no hub page:
- `/interview-questions/` — 51 role pillars, 420 posts. Biggest single win.
- `/recruitment-guide/` — 60 pillars, 483 posts.
- `/employee-engagement-guide/` — 27 pillars, 194 posts.
- `/future-of-work/` — 16 pillars, 128 posts.

For each: build the theme hub page → it links to the ~15–60 *pillar* pages → each pillar links down to its ≤15 spokes. Classic three-tier structure.

**2. For the 🟢 Exists themes, the work is internal linking, not writing** — the hub pages already live; wire each pillar's spokes to the right existing page (e.g. the *Coding & Programming Tests* pillar's posts should all link to `/coding-tests/`).

**3. Thin but valuable pillars to feed** — clusters with only 3–5 posts but strong buyer intent: *Succession Planning*, *Skills Management* (9 pillars/60 posts — your model theme is under-fed), onboarding, workforce planning. Add spokes.

**4. 25 orphans** — one-off posts with no cluster. Either leave standalone or grow each into a real cluster over time. Listed in the HTML and `all-pillars.md`.

---

## How this was built (so it's reproducible &amp; auditable)

1. `build_workitems.py` → split 2,972 posts into 39 coherent slices.
2. **39 LLM subagents** each read a slice and grouped it into tight ≤15 pillars (`data/fine/`).
3. `assemble.py` → merged into 402 pillars, validated full coverage.
4. **10 LLM subagents** consolidated near-duplicate pillars per domain + rescued clusters from orphans (`data/consolidate/out/`).
5. `final_assemble.py` → 373 pillars / 11 themes, re-validated (0 missing, 0 invented, 0 duplicated, none over the 15 cap).
6. `build_html.py` → the interactive map.

Every step re-runnable. Rebuild after a re-crawl with `final_assemble.py &amp;&amp; build_html.py`.

---

## Files

```
pillar-cluster-strategy/
├── PILLAR-CLUSTER-STRATEGY.md   ← this report
├── pillar-cluster-map.html      ← interactive map (open this)
├── data/
│   ├── final-clusters.json      ← THE source of truth: 373 pillars → exact posts
│   ├── all-pillars.md           ← readable list of all 373 pillars
│   ├── url-clusters.csv         ← every URL, coarse cluster (input)
│   ├── fine/ · consolidate/     ← intermediate subagent outputs (audit trail)
│   └── work/                    ← the 39 slices + instructions
└── *.py                         ← the re-runnable pipeline
```

### Honest limitations
- Clusters were judged from **post titles (slugs)**, not full article bodies. A minority of posts may sit in a debatable pillar — open `final-clusters.json` and move any slug to correct it.
- **Internal links were not crawled** — the "wire spokes to the hub" actions say where links *should* go, not which already exist. A Search Console Links export would confirm the current graph before bulk edits.
- Programmatic sections (test library, glossaries, job descriptions — ~5,900 URLs) remain out of scope by your earlier decision.
