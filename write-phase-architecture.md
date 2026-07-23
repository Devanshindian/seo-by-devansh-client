---
type: the single source of truth for the WRITE phase — architecture (how it's built) + design record (why every decision was made)
scope: content-machine WRITE phase — asset idea → writability gate → research bundle → one published, checklist-passing article
supersedes: write-phase-plan.md (the old W1-W9 list, Appendix B) and write-phase-plan-2.md (the SEO Machine per-file verdicts, Appendix C)
reads: clubbed-ideas.csv (the asset queue) · the research bundle per topic · the embedded per-archetype format playbooks (Appendix D)
verified_against: full read of the research phase (layers 10-14, one complete bundle, all 10 brand-context files, the full seo-aeo-geo-guidelines standard) + a writability classification of all 2,213 live asset ideas (2026-07-22)
last_updated: 2026-07-22
---

# The Write Phase — complete architecture and design record

This is the only file for the write phase. How to read it:

- **Parts 0-6: the build.** Follow the run order: what enters (the gate + the bundle) → how the format layer shapes it → the 8-station assembly line → the loops → the build plan. Detailed enough to build one piece at a time.
- **Part 7: the open decisions** still sitting with Devansh.
- **Appendices A-C: the history.** Where every SEO Machine idea landed, the old W1-W9 list, and the full per-file design record ("why we kept/killed each thing"). Read only when you want the argument behind a decision.
- **Appendix D: the embedded format playbooks.** The full hand-to-a-writer version of all nine archetype playbooks (section skeleton, writing rules, checkable rules). Part 3.3 is the distilled overlay for the pipeline; Appendix D is the complete reference the format router loads. This doc stands alone — no external format folder is needed.

---
---

# PART 0 — The one idea, and the whole machine in one picture

## The one idea (seven lines)

1. **Not every asset idea is an article.** A writability gate classifies every idea BEFORE research spends money on it: write it, build it, collect data first, or route it to another system.
2. Research already did the finding. The write phase **selects, words, places, and proves** — it never re-researches.
3. **The format decides the shape.** A listicle is built differently from a report. The first act of planning is routing the asset to its format playbook; the format's rules overlay the common spine.
4. Nothing is invented. Every fact traces to the bundle's evidence cards (each has a `card_id`, a verbatim quote, source URLs) or to `features.md`.
5. **Code counts. The AI judges.** If you can count it, a script does it. If you can be wrong about it, the AI does it — and code runs first, feeding the AI the facts.
6. Every station writes a **named file**, atomically, so a crash resumes from the last finished station.
7. Nothing ships until **one checklist** passes; whatever fails three times goes to a human.

## The whole machine

```text
   ASSET IDEA  (clubbed-ideas.csv — 2,213 ideas today)
        |
        v
  [GATE 0]  WRITABILITY — runs in the RESEARCH phase, before any research money is spent
        |
        |-- WRITE / WRITE+ARTIFACT (70%) --> research runs --> bundle --> the pipeline below
        |-- WRITE+BUILD (9%)  ----------> tool-build queue (wrapper article follows once the tool exists)
        |-- DATA-GATED (4%)  -----------> data / sign-off collection queue (article follows once inputs are real)
        |-- NOT-ARTICLE (12%) ----------> other systems (landing pages, courses, webinars) — not this pipeline
        v
   RESEARCH BUNDLE  (2 files: the copied blueprint JSON + a cover sheet of pointers)
        |
        v
  [1] PLAN     FORMAT ROUTER first (asset format → archetype → load its playbook)
               then: select sections + cards + FAQ + orphans → freeze article-plan.json   (AI selects · code asserts)
        |
        v
  [2] WRITE    one section at a time, typed prompts + the format overlay
               (+ internal linker · + meta 5×5)                                           (AI writes from packets)
        |
        v
  [3] CLEAN    invisible chars · whitespace · em-dashes · atomic save                     (pure code)
        |
        v
  [4] MEASURE  facts.json — every countable check, incl. the format's checks              (pure code)
        |
        v
  [5] REVIEW   AI judges, fed facts.json → findings sorted Critical/High/Quick-win        (AI judges)
        |                                                        ^
        v                                                        |  LOOP B (max 3 passes)
  [6] EDIT     6a editor (add craft) → 6b avoid-ai-writing (remove tells)                 (AI improves)
        |                                                        |
        v                                                        |
  [7] GATE     seo-aeo-geo-checklist — code pre-ticks, AI ticks rest                      (code + AI)
        |----- fails 3 passes → review-required/ + _REVIEW_NOTES.md (= "ship as draft + report")
        v
  [8] PUBLISH  WordPress draft (parked) + Bing indexing + update research-log write_status
```

## The split from research (why write is a separate phase)

Research decided *what to say + the structure + the sources + the keywords*. Write decides *the exact wording, the citations chosen, the internal links, the meta, the slug* — and then **proves the draft matches the brief**. The write phase assembles and verifies; it does not re-research.

---
---

# PART 1 — The five governing rules (the common spine — apply to every article, every format)

## Rule 1 — Code counts, the AI judges

- Count it → code. (word count, "did this stat land", "did every link appear", "is the meta title ≤60 chars", "was every gap used once")
- Be-wrong-about-it → AI. (the angle of a section, whether a story belongs, whether the writing is good)
- **Test:** can two sensible people disagree about the answer? Then it's judgment, not code.

Every SEO Machine file that failed did so by breaking this rule — using arithmetic to make editorial decisions, which is why their automatic rules read as arbitrary.

## Rule 2 — Python feeds the MD checklist (one direction)

- Python runs first and writes a small factual report: `meta title 71 chars [FAIL] · keyword in H1 [OK] · 2 stats with no source link at lines 34, 88`.
- That report is poured into the AI's checking prompt alongside the draft.
- The AI never counts; it uses Python's facts and spends its attention on judgment.
- If you ask the AI "is the meta title 50-60 chars?" it eyeballs it and often gets it wrong. `len(title)` does not guess.

Where each check lands:

| Python (fact) | AI (judgment) |
|---|---|
| keyword in H1 / first 100 words | is the anchor text descriptive, not "click here" |
| meta title 50-60, description 140-160 | does this section deliver on its heading |
| one H1, H2s in order, no skipped levels | is a product mention forced or natural |
| count of internal / external links | is this a real featured-snippet opportunity |
| do links resolve (return 200) | does this section read as fair, not a pitch |
| a number with no source link nearby (Python *finds* it) | does this claim actually need a source (AI *decides*) |

## Rule 3 — Three kinds of instruction (sort every rule before building it)

- **Kind 1 — writing prompt:** handed to the AI *before* writing. Shapes what gets written.
- **Kind 2 — checking prompt:** handed to the AI *after* writing, with the draft. Judgment.
- **Kind 3 — code check:** a script, after writing. Counting.

Three things follow:
1. **Kind 1 and Kind 2 are the same rule at two moments.** "40-60 words" in the instruction becomes "is it 40-60 words" in the check. Write the rule once, reference it twice.
2. **Kind 3 quietly eats most of Kind 2's workload.** Once code handles the counting, the AI review spends all its attention on what only judgment can catch.
3. **Kind 3 is the only one that catches a broken promise** — a stat the plan required that never made it into the draft. The most common silent failure in AI writing; no prompting reliably prevents it; code catches it every time.

### Worked example — one FAQ section, all three kinds

The plan hands over:
```
heading: "Common questions about psychometric testing"
type: faq
gaps_addressed: ["nobody explains how long results stay valid"]
unique_data: ["Testlify tests average 18 minutes", "shelf life of results: 12-24 months"]
internal_links: ["/features/psychometric-tests"]
```

**Kind 1 (writing prompt, before):**
```
Write the FAQ section: "Common questions about psychometric testing"
Requirements: 4-6 questions · each answer ≤40 words (the AEO cap) · answer first, then context · questions from real research
Do: use questions people actually asked · answer the gap nobody covers (how long results stay valid)
Don't: generic questions · repeat anything answered earlier
Must include: "Testlify tests average 18 minutes" · "shelf life of results: 12-24 months"
Link to: /features/psychometric-tests
```

**Kind 2 (checking prompt, after):**
```
Review this FAQ section.
- Do the questions read as real, or as manufactured filler?
- Is any of them already answered elsewhere in the article?
- Does each answer lead with the answer?
- Does the section close its assigned gap?
Quote the exact line for each failure.
```

**Kind 3 (code check, after):**
```
FAQ section: "Common questions about psychometric testing"
  question count ........ 5          [pass, 4-6]
  answer word counts .... 38, 40, 33, 41, 36    answer 4 is 41 [fail, need ≤40 — the AEO cap]
  required data present:
     "18 minutes" ....... found
     "12-24 months" ..... NOT FOUND  [fail]
  internal links: /features/psychometric-tests ... found
```
Note what Kind 3 caught: a stat the plan promised that never made it into the draft. Invisible to Kind 1 and Kind 2. Caught every time by Kind 3.

## Rule 4 — The fabrication rule (governs every word written)

The line is **disguised vs signposted**, not fake vs real.

| Allowed | Not allowed |
|---|---|
| Signposted hypotheticals ("imagine a recruiter screening 300 applicants") | Named people/companies written to read as real events |
| Generic personas clearly framed as illustrative | Any invented **Testlify customer**, result, or metric — even signposted |
| Real examples from the bundle's cards or `features.md` | Fabricated outcomes attributed to any real or implied company |

- **Type A — fabrication written to read as true:** "Sarah launched her SaaS in 2023 and got stuck at 200 signups." The specific detail exists to make the reader believe it happened. A fake anecdote posing as testimony. **Banned.**
- **Type B — a hypothetical the reader knows is hypothetical:** "Say a recruiter, call her Maya, is screening 300 applicants." Signposted. Nobody is deceived. **Allowed.**
- **The one hard exception:** a made-up story about a **Testlify customer and their results** is a fabricated testimonial — false-advertising territory (FTC endorsement rules) and the opposite of the real first-hand experience Google's E-E-A-T rewards. Banned even when signposted.
- **Priority order for show-don't-tell:** (1) a real example from the bundle/brand files — always first; (2) if none, a signposted hypothetical with no Testlify-outcome claim; (3) never a disguised fabrication.
- This matches `writing-integrity.md` rule 5 verbatim: "no named or implied real customer · no fake quote · no fabricated first-party metric."

**The quote rule (blogs) — one named-source quote per blog, with a narrow internal exception.** Every standard blog / how-to carries at least one quotation from a named source (a GEO lever: quotations ~+41% AI-citation lift, Princeton). Two allowed kinds:
- **A real external industry leader or recognised body** — quote them only from a real, verifiable, cited source (e.g. a published SHRM/WEF/WHO statement, a named study author). **Never fabricate, paraphrase-as-quotation, or attribute an invented line to a real external person.** No source you have actually read = no quote.
- **A Testlify leader — Abhishek or Namrata** (leadership house voices; see the author-box route). For these two ONLY, a relevant quote **may be composed to fit the topic** (ghostwritten exec voice, the way a byline op-ed is written for an executive) — it must sound like them, stay on-message, and make no unverifiable first-party metric claim. This is the single carve-out to "no fake quote"; it never extends to any other named person, real customer, or external expert.

**The stats-recency rule (governs every statistic).** Prefer stats from **2024 or newer**; treat ~3 years as the hard floor (nothing older than ~2023 as of this writing) unless the figure is historical by nature. Never cite a number superseded by a newer one. AI engines cite recent content far more often (content refreshed in the last 30 days earns ~3.2x more AI citations), so freshness is a real GEO lever, not a nicety. Every stat still needs a real, named source URL that returns 200 and whose on-page year matches.

**Two more hard integrity lines (from the guidelines §10):**
- **No invented frameworks** — never coin a proprietary-sounding "Testlify [Something] Matrix / Model / Framework" unless it genuinely exists on our own site. (This has slipped into drafts before.)
- **No vague attributions** — "studies show" and "experts agree" are not sources. Name the study or the expert, or cut the claim.

## Rule 5 — One owner per rule (no duplicate lists)

- The banned-AI-phrase list existed in FOUR SEO Machine files. All dead. **`avoid-ai-writing` owns prose cleanup.**
- The gate existed as FIVE competing scores. All dead. **`seo-aeo-geo-checklist.md` owns the gate.**
- Voice is owned by `brand-voice.md` + `avoid-ai-writing`. The editor defers to them on overlap.
- Format rules are owned by the embedded per-archetype playbooks (Appendix D) — Part 3 encodes only the non-duplicate keepers for the pipeline, Appendix D carries the full hand-to-a-writer version.

---
---

# PART 2 — Intake: what enters the write phase

## 2.1 Intake filter — read the writability column (the asset engine owns the gate)

- The **asset engine** classifies every idea (WRITE / WRITE+ARTIFACT / WRITE+BUILD / DATA-GATED / NOT-ARTICLE) and stamps a `writability` column on `clubbed-ideas.csv`. It also fixed the over-tooling bug (a tool is only WRITE+BUILD when a competitor genuinely ranks a tool).
- **The write phase does not classify.** It reads the column and accepts only **WRITE + WRITE+ARTIFACT**. WRITE+BUILD → tool-build queue · DATA-GATED → waits for its data/sign-off · NOT-ARTICLE → out.
- One nuance the column encodes: a *statistics roundup* (curates already-public stats) = WRITE; a *data report / original research* (needs data nobody has yet) = DATA-GATED. Same playbook, different class.
- Full detail (the five classes, the corrected counts, the SERP-format-match fix) lives with the asset engine: `FIX-over-tooling-HANDOFF.md` + `idea-review/enriched-v2.csv`. Not repeated here.

## 2.2 The research bundle (what a WRITE-class idea arrives with — verified)

The bundle is exactly **two files**: `structure-<slug>.json` (the ONLY copied file) and `bundle-<slug>.md` (a cover sheet whose 10 divisions are pointers, never copies).

| Input | What it really carries (verified) | Used at |
|---|---|---|
| **Structure JSON** | slug · h1 · keyword_set · **18 candidate H2 sections** (a MENU) · faq (question strings — **empty for this topic**) · orphan_keywords · write_guidance · persona {name, lens, why} | 1, then all |
| — keyword_set | primary (str) · variations[6] · secondaries[14] · in_body[8] · h2_keywords[12] each {keyword, volume, kd} | 1, 2, 4 |
| — per section | h2 · is_differentiator (14/18 true) · target_keyword ({keyword, volume, kd, why} **or null** — null on 6, legit for differentiator sections) · internal_links · external_links · **h3[]** | 1, 2 |
| — per H3 | h3 title · **evidence[]** · internal_links · external_links. In the ONE sample bundle inspected, evidence sat on the H3s (1,188 items across 135 H3s; section-level arrays empty) — **observed, not guaranteed. Station 1 reads evidence wherever it lives (section OR H3) and verifies the layout per bundle** | 1, 2, 4 |
| — per evidence item | `{card_id, gloss, verbatim, source_urls, tag: ownpage\|storm}` — the traceability unit | 2, 4 |
| **research-doc Build spec** ⭐ | **word band (2,500-3,500 here** — *input:* the ideas' `# words` competitor-length column; research reasons it into a band from the confirmed content type + the ranking winners' lengths, so it is NOT in the structure JSON) · featured-snippet target (a spec'd 40-60w definition) · **2-4 named primary sources to cite** (APA/AERA/NCME, SIOP, Schmidt & Hunter, EEOC) · **exact close/CTA spec** | 1 — a REQUIRED input, not optional depth |
| **proof/04-serp-snapshot.md · proof/05-winners.md** | who ranks · snippet open-to-win · AI-Overview GEO gap · PAA on/off-angle · winners' format/depth · "5 gaps we can own" | 1 |
| **STORM dossier** (pointed) | the cited evidence dossier + `url_to_info.json` + raw search pool — "/write treats it as an evidence pool… can mine" for depth the cards don't carry | 2 (drill-down only) |
| **brand context** | brand-voice · style-guide · features · writing-integrity · writing-examples · persona · voices | 2, 5, 6, 7 |
| **seo-aeo-geo-checklist.md** | THE gate (pointer, never copied) | 7 |
| **avoid-ai-writing SKILL** | modes rewrite/detect/edit · P0/P1/P2 tiers · voice profiles · iterate cap 2 | 6b |

**Three facts that shape the whole build:**

1. **The JSON is a menu, not the article.** Its own write_guidance says "The writer selects sections and does the wording." ~18 candidate H2s; the final article uses **however many the FORMAT + the WORD BAND + the earn-its-place filter justify** — there is no fixed number (see Station 1). The first job is *selection*.
2. **Evidence may sit on the H3s (sub-sections), not the main sections** — that is what the ONE sample bundle showed (all section-level lists empty; the 1,188 cards hung off the 135 H3s). **Observed, not guaranteed.** Station 1 reads evidence wherever it lives and verifies the layout per bundle. Don't hard-code "evidence is always on H3s."
3. **The FAQ may arrive empty** — it did in the sample (zero on-angle PAA existed). **Observed, not guaranteed.** So Station 1 checks: if research supplied FAQ questions, use them; if not, author them. Don't assume either way.

## 2.3 What is NOT usable, and what research does not produce (verified)

- `stats.md` is machine-drafted, EVERY row unconfirmed and self-contradicting (3,500+ vs 3000+ vs 1500+ tests).
- `stories.md` is 34 unapproved drafts naming real customers — colliding with writing-integrity's hard ban until signed off.
- `opinions.md` is empty.
- **Until a human confirms them, approved evidence = the bundle's cards + `features.md` only.** The write prompts must carry an explicit "unconfirmed = unusable" rule.
- Research produces **no meta title and no meta description** (verified, zero hits). **The write phase owns meta entirely.**

---
---

# PART 3 — The format layer (common spine + format overlay)

Every article gets two layers of rules:

- **The common spine** — the five governing rules (Part 1) + the stations (Part 4) + the `seo-aeo-geo-checklist`. Applies to every article identically: answer-first 40-60w blocks, one-idea-per-section, cite-every-stat, length-is-an-output, question headings, the fabrication rule.
- **The format overlay** — what makes a listicle a listicle and a report a report. Owned by the embedded per-archetype playbook (Appendix D); the non-duplicate keepers are encoded below, tagged with the station that consumes each.

## 3.1 The format router (Station 1, job 0)

- Reads the asset's `Format` field (from `clubbed-ideas.csv`, carried through the research queue).
- Maps it to one of the **9 archetypes** and loads that archetype's embedded playbook (Appendix D). That playbook's skeleton drives the section plan; its writing rules inject into Station 2's prompts; its checkable rules become Station 4/7 checks.
- Like Gate 0, the mapping is a **lookup table** (format name → archetype), with an LLM fallback for unseen names. Assign the type by the table, never by keyword-matching the title (the article_planner failure mode).

**The mapping (current vocabulary → archetype; counts from the 2,213-idea snapshot):**

| Format names (count) | Archetype playbook | Gate 0 class |
|---|---|---|
| Definitional explainer (582) · FAQ page (2) | answer-bait-definitional | WRITE |
| How-to guide (228) · Pillar guide (139) · Role skills guide (46) | how-to-guide | WRITE |
| Listicle (134) · Interview-questions listicle (76) · Tips listicle (18) · Myths/facts/complete-list (few) · Curated resource directory (1) | listicle | WRITE |
| Rankings / comparison (117) | comparison-rankings | WRITE |
| Glossary (63+) | glossary | WRITE |
| Statistics roundup (30) | data-benchmark-report | WRITE (curates public stats) |
| Data report / original research (50) · State-of survey · Salary benchmark | data-benchmark-report | DATA-GATED |
| Templates / examples pack (31) · Toolkit (2) · Whitepaper/ebook (8) · Checklist/cheat sheet (3+) | template-resource | WRITE+ARTIFACT |
| Quiz / assessment (162) · Calculator/tool (6+) · Generator · Grader · Free product/library (15) | interactive-tool (wrapper only) | WRITE+BUILD |
| Case study (32+) · Testimonials (2) · Expert roundup (2) | case-study | DATA-GATED |
| News article (27) · Opinion / editorial (19+22) · Trends (3) · Framework/methodology (2) | **common spine only** — no overlay | WRITE |
| Product/landing/pricing/integrations pages · courses · webinars · podcasts | — | NOT-ARTICLE (other systems) |

## 3.2 Cross-format corrections (apply to every format — fold into the checklist / Station 8, not per-format)

- **Downgrade FAQ/HowTo schema:** deprecated for rich results (FAQ restricted to gov/health since Sept 2023, HowTo removed — confirmed on Google's own docs). Keep FAQ *sections* for readers + AI lift; use the markup for parseability only; never promise a rich result.
- **Bing indexing at Station 8:** ChatGPT search runs on Bing's index — a Google-only page is invisible to ChatGPT. "Indexed in Bing + Bing sitemap submitted" becomes a publish-phase requirement.
- **Gating kills visibility:** a gated (email-walled) asset is invisible to Google AND to ChatGPT/Perplexity/Gemini. Anything whose job is links or AI citation defaults ungated; gate only an "enhanced" companion.

## 3.3 The nine format profiles (the non-duplicate keepers, by archetype)

**Every profile below uses the SAME five heads, and each head plugs straight into a downstream station** — so "when to use it" and "how to use it" map onto the pipeline instead of floating free:

- **When to use / when not** → the router (3.1) + Gate 0
- **The shape (skeleton)** → Station 1 (PLAN)
- **The per-unit craft** → Station 2 (WRITE)
- **The format checks** → Station 4 (MEASURE) + Station 7 (GATE)
- **The one hard rule + pitfalls** → the gate's blockers

Only the non-duplicate keepers sit here; the full hand-to-a-writer version is each format's embedded playbook in Appendix D. Points already carried by the common spine are listed as *Parked* at the end of each.

### how-to-guide / pillar (also the standard-blog default)
- **When to use:** how-to guide · pillar guide · role skills guide · standard informational blog. A task to complete (how-to) OR a broad topic to map (pillar). NOT "what is X" (→ answer-bait) or "best X" (→ comparison).
- **The shape (Station 1):** the **fixed house order** — Intro (hook + direct answer) → TL;DR → body (H2 & H3 as per the keyword; the "what is X" definition is its own section, never mixed into the steps) → Key takeaways/Conclusion → one primary CTA → FAQ (last). Pick the mode — **how-to** (steps) vs **pillar** (orient + route), never blur them · pillar mode stays broad-not-deep (depth lives in the cluster articles); headers let a visitor self-qualify and jump.
- **The per-unit craft (Station 2):** each step = imperative verb first · one action only · state the goal before the action · state the location before the action · state the result immediately after · be prescriptive — recommend ONE way, the shortest path, never a menu of methods. **Every blog also carries: one named-source quote** (real cited industry leader/body, OR a composed Abhishek/Namrata leadership quote) · **one evergreen authoritative external link** (WHO / SHRM / WEF) · one original example/data point · stats 2024+.
- **The format checks (Station 4/7):** the house-order + required-blocks check (TL;DR, Key takeaways, one CTA after takeaways, FAQ last); otherwise the common structure checks; no format-specific schema.
- **Hard rule + pitfalls:** don't blur how-to and pillar; don't bury the task under theory; never reorder the wrapper (FAQ is always last).
- *Parked (not write-phase):* pillar↔cluster interlinking + cannibalization (site-level) · topic selection / "maps to what you sell" (research) · promotion (backlink machine).

### listicle
- **When to use:** "N best X" · interview-questions · tips · facts / statistics roundup · complete-list · expert roundup. A set of discrete items. NOT a single-topic explainer.
- **The shape (Station 1):** **jump straight into the list — ONE crisp intro (2-4 sentences: who the list is for + how you chose/ordered), then the items. NO long educative/informational preamble before the list.** Skeleton by search intent — info-heavy = plain list · imagery-heavy = image per item · **product/buying-intent = specs/comparison table ABOVE the list**, then per-item detail · supporting blocks (pros/cons, buying guide, definitions, data) go BELOW the items, never as a front-loaded preamble · item count matched to the SERP; 8+ items earns the "More items…" snippet but only if the topic honestly holds them — no padding.
- **The per-unit craft (Station 2):** per-item template = short descriptive heading → one-line self-contained summary (the sentence AI quotes) → 2-3 short paras → one concrete proof (number/example/screenshot) · held in **strict parallel** across all items (same heading shape, depth, register) · describe the THING, not your article — no marketing blurb, no "in this list we…" · ordering: strongest first; ranked = best-first with disclosed criteria; expert roundup = by fame.
- **The format checks (Station 4/7):** `ItemList` schema honestly reflecting the page · list kept flat, not nested (nesting blocks snippet extraction) · running numbers on the item H2s.
- **Hard rule + pitfalls:** every item must earn its number — cut filler even over the 8+ target.
- *Parked:* self-#1 → omission = authority-honesty · refresh cadence = content-refresh.

### comparison-rankings ("best X" · "X vs Y" · "alternatives to X")
- **When to use:** rankings · best-tools · comparison · alternatives · branded index. Choosing between named options. NOT a single concept (→ answer-bait).
- **The shape (Station 1):** lean fixed table (~5 columns: what-it-does · name · one-line description · one proof metric · a few capability tags), a real HTML `<table>`, shown up top after a ≤200-word BLUF intro — no feature-matrix sprawl · company background pushed to the bottom (one-line positioner up top only) · "A vs B" fixed sequence: what is A → what is B → differences → similarities → head-to-head → pros/cons each → verdict by use case → FAQ.
- **The per-unit craft (Station 2):** identical per-option block — name → overview → 4-5 features → pricing (seat/usage model explicit) → one strength → one honest weakness → verdict + who it suits · **fairness mechanics (the spine):** replace every adjective with a fact ("$12/mo for 5 users", not "affordable"); name ≥1 honest weakness for EVERY option incl. the favoured one; concede ≥1 place a rival genuinely wins and route the reader there · intro ≤200-word BLUF with the winner in paragraph 1; a "vs" answer in ≤60 words · constraint-based verdicts ("For a 5-person team…", "For B2B SaaS…").
- **The format checks (Station 4/7):** real HTML table not an image · unknown cell BLANK, not guessed · every metric dated + sourced (no hand-typed number without a date) · stale option flagged with a date, never silently deleted · `Review`/`Rating` + `Pros-and-Cons` schema only where real on the page.
- **Hard rule + pitfalls:** never cite/rank a direct assessment competitor; an "alternative to X" anchor points at a neutral job/category, never a named rival · no self-#1 without basis.
- *Parked:* author bio/last-updated = E-E-A-T + author box · "is it worth writing"/persona/keyword-difficulty = research · visuals/affiliate-disclosure/outreach = assets + off-page · cluster interlinking = linker.

### answer-bait-definitional ("what is X" / "how does X work")
- **When to use:** definitional explainer · "what is X" · "how does X work" · FAQ page · interactive explainer. A concept to define. NOT a task (→ how-to) or a set (→ listicle).
- **The shape (Station 1):** the 40-60w answer block sits at the VERY TOP of the body — nothing above it (no intro, no image) · then inverted pyramid: definition → how it works → types/components → why it matters → how-to/examples → related questions · match snippet format to query (paragraph = what-is/how · list = steps/types · table = comparison/specs).
- **The per-unit craft (Station 2):** four-part answer shape — direct answer (term restated + defined) → defining context → qualifier → outcome (~45 words the bullseye; over ~70 truncates) · **self-containment (the standout rule):** every section opener parses with its heading removed — no "this" / "as mentioned above"; restate the full claim inside each section, because engines extract one chunk alone · add a named quote alongside the required stat (Princeton levers: stats ~+41%, quotes ~+28%; stuffing LOWERS citation).
- **The format checks (Station 4/7):** `DefinedTerm` + `Article` schema · `DefinedTerm.description` byte-identical to the on-page one-sentence definition.
- **Hard rule + pitfalls:** answer-first in a self-contained chunk; no keyword stuffing (measurably lowers citation).
- *Parked:* answer-first / one-idea / cite-stats / question-headings / FAQ / no-stuffing = checklist · FAQ-HowTo-deprecation + Bing-index + crawler-access = cross-format corrections · off-site entity signals = off-page · refresh = content-refresh.

### data-benchmark-report (data study · benchmark · statistics roundup)
- **When to use:** data report / original research · survey · salary benchmark · statistics roundup · grader-results. Numbers to present for citation + links. (Gate 0: statistics roundup = WRITE; original research = DATA-GATED.)
- **The shape (Station 1):** big-number headline → intro states N immediately → a **numbered key-findings menu up top** (the citation menu) → 8-15 findings, one section each, each a distinct new number → methodology short-block in-page + full appendix at the bottom · **never gated** — a form kills the citation · **novelty gate:** kill a finding that only confirms the obvious ("information gain").
- **The per-unit craft (Station 2):** heading states the finding IN WORDS with the exact number one line below (heading = the conclusion, not the topic) · a boxed "key takeaway" per finding · the liftable one-sentence stat = number + subject + scope, no dangling pronoun, lifts cleanly with zero context · front-load the crunchy stat (it becomes the citing site's anchor text) · **chart rules** (content decisions here; rendering = later UI layer): name the relationship before the chart · "vs the average" = a diverging bar, NOT a plain column · one chart = one idea · chart title = a full takeaway sentence.
- **The format checks (Station 4/7):** **[RIGOR] methodology disclosure** — N · data source · dates/window · exactly what was measured · limitations. No method = dismissed as marketing; non-negotiable, the practitioner tactics never override it · `Article` + `BreadcrumbList` baseline, `Dataset` on proprietary research.
- **Hard rule + pitfalls:** no methodology = it reads as marketing; never gate it.
- *Parked:* promotion (reverse outreach, ping-cited-firms, PR syndication) = off-page · data gathering = upstream asset-building · journalist-keyword targeting = research · refresh = content-refresh.

### glossary (hub + term entries)
- **When to use:** glossary / dictionary — many short term-definition entries under one hub. Shares its definition-writing rules with answer-bait; the NEW part is the hub-and-spoke structure.
- **The shape (Station 1):** one A-Z hub page linking to EVERY entry (the crawl backbone); numbers/symbols first then A-Z; optional category filters · entry skeleton: H1 = the exact term → "[Term] is [definition]" first line → "why it matters" (the how/why, not a restated definition) → ≥1 real example → flag era/status on dated terms · sideways interlinking: 3-5 related-term links per entry + hub→entry and entry→hub reciprocity.
- **The per-unit craft (Station 2):** split multiple meanings in one entry — name each sense (apple = fruit/company), never define one and blend the rest · expand the acronym on first use, then define.
- **The format checks (Station 4/7):** `DefinedTerm` per entry + `DefinedTermSet` on the hub — inverses, one direction per page.
- **Hard rule + pitfalls:** no thin / near-duplicate entries (the glossary failure mode).
- *Parked:* 40-60w definition / plain-text / question-H2s / one-idea = answer-bait + checklist · term-as-entity sourcing = research · programmatic bulk generation = a separate pipeline · tooltip auto-linking plugin = site/UI layer · refresh = content-refresh.

### interactive-tool (calculator · quiz · assessment · grader · generator) — WRITE+BUILD
- **When to use:** ONLY when a competitor genuinely ranks a tool (post over-tooling fix); otherwise route the idea to an article. The write phase owns only the WORDS around the tool — the tool itself is a separate build.
- **The shape (Station 1):** the SEO wrapper sections below the tool — 150-200w intro (what/who) → "How to use" → "Why [topic] matters" (with data) → **Methodology** (how the numbers are calculated — this is what makes the tool citable) → FAQ → related links · one tool = one page = one keyword · link-magnet vs lead-gen decides gating.
- **The per-unit craft (Station 2):** result-interpretation copy — tell the user what their score MEANS and the next step.
- **The format checks (Station 4/7):** `WebApplication` schema.
- **Hard rule + pitfalls:** don't gate a link-magnet · the tool's build (input flow / scoring / embed) is NOT write-phase.
- *Parked (tool-build pipeline):* input flow (one-ask-per-screen, validation, progress bar) · score computation · gate placement · embed/distribution loop · launch. Recorded in the interactive-tool playbook (Appendix D, the parked-functionality note) for when we build the tool generator.

### template-resource (downloadable template · checklist · cheat sheet) — WRITE+ARTIFACT
- **When to use:** templates · asset library · checklist / cheat sheet · toolkit · whitepaper/ebook. An article + a downloadable the write phase can produce as text.
- **The shape (Station 1):** wrapper page — H1 = the "[thing] template/checklist" query + states the outcome → **real preview of the asset above the fold, before any ask** → a "what you get" stat block ("385 items across 11 categories") → a numbered "how to use it" → the shortest wrapper that fully explains the asset and covers the query.
- **The per-unit craft (Station 2):** checklist-item format (when the asset IS a checklist) — each item = checkbox + imperative action title ("Declare UTF-8 encoding", never a topic noun) + priority badge (Critical/High/Medium/Low) + one-sentence why · concrete/quantified ("load time under 3s") · define the priority scale ONCE up top · group by workflow with an item count per group · show ≥1 filled example.
- **The format checks (Station 4/7):** the asset preview must be above the fold; otherwise the common structure checks.
- **Hard rule + pitfalls:** default ungated · the download file itself = build/publish, not write-phase.
- *Parked:* delivery (Make-a-copy / download / multi-format) = build/publish · resource-page outreach + dead-link replacement = off-page · maintenance = content-refresh · topic/query selection = research.

### case-study (customer results story) — DATA-GATED
- **When to use:** customer results story · testimonials — ONLY when a real named customer, real numbers, and a verbatim quote are collected AND approved in writing. (Currently blocked pipeline-wide: `stories.md` is unapproved.)
- **The shape (Station 1) — Testlify's real customer-story template (supersedes any generic structure):** eyebrow label "Customer story" → **H1 = "How <Company> <achieved result> with Testlify"** (result-first) → metadata block (Company size · Headquarters · Industries · Use-case) → three 2-3 sentence blocks **Challenge / Solution / Outcome** → three big headline **stat cards** (number + one-line label, e.g. "67% faster time-to-hire") → a **Details** section of narrative H2s (situation/problem → solution rollout → measured results) with a cited stat woven in. Result-first for organic visitors.
- **The per-unit craft (Station 2):** every metric paired with baseline + timeframe + why it mattered ("from X to Y in 6 months") · lead with the business number a buyer cares about; vanity metrics only as SUPPORT · show the workings (screenshots, timeline, quotes) so it doesn't read as coincidence · **narrative:** borrow fiction's shape (setup → tension → resolution) but only real facts; include the real obstacle hit (the pratfall effect); editorialize to the 2-3 most interesting moments; a verbatim named-decision-maker quote every 2-3 paragraphs; business-journalism voice, not brochure; don't erase yourself.
- **The format checks (Station 4/7):** `Article` with the `author` property emphasised (credentials).
- **Hard rule + pitfalls:** the fabrication rule bites hardest — the per-claim test is *"would the named customer recognise this and nod?"*; no invented customer, quote, rounded-up metric, or composite client.
- *Parked:* customer sign-off collection = the Gate 0 data-collection queue (upstream input) · SEO keyword targeting = research · length ~800-1,000w = length-is-an-output.

### (no overlay) News · Opinion · Editorial · Trends · Frameworks
- **When to use:** news · opinion / editorial · trends / predictions · framework / methodology · other/editorial. No dedicated playbook — runs on the common spine alone.
- **Note:** for news, freshness matters more than depth — flag timeliness at Station 1.

## 3.4 Deferred functionality — a downloadable report/result (decide later, then build)

- **Not built yet — this is a build-layer feature to decide on later.** The open question: do we want to hand the reader a downloadable report/result file at all?
- **If yes, it fits only three formats:** data-benchmark-report (download the full report/dataset) · interactive-tool (download your personalized result) · template-resource (the download IS the asset). The other six get nothing — a download there is friction, not value.
- **Ownership split when we do build it:** the WRITE phase writes the *offer copy* only (the "download the report / your result" CTA + the "what you get" block + the methodology note that makes it trustworthy); the BUILD/publish layer generates the actual file (PDF/CSV). The write phase never pretends to make the file.
- **Decide before building:** which of the three, and gated or ungated — gating a link-magnet kills citations (see 3.2), so a report download defaults ungated.

---
---

# PART 4 — The assembly line: the 8 stations (build-ready)

Each station: purpose · inputs/outputs · the SEO Machine files it draws from with exact kept/dropped items · a build checklist. The full reasoning for any kept/dropped item is in Appendix C. Format-overlay hooks are marked where the router's playbook plugs in.

---

## STATION 1 — PLAN: route the format, freeze the section plan

**Purpose:** turn the 18-section menu + the Build spec + the proof files into ONE frozen `article-plan.json` — the single source of truth every later station checks against. It never changes after this station.

**Inputs:** the asset's Format field · structure JSON · research-doc Build spec · proof 04/05 · persona · the routed archetype's embedded playbook (Appendix D).
**Output:** `article-plan.json` (+ a human-readable `article-plan.md` mirror).

### The finished article's shape (what the plan is arranging)

The article is a fixed WRAPPER around a format-shaped BODY — this is the "two layers" of Part 3 made concrete:

```
├─ Intro (answer-first)        ← wrapper piece (common spine) — write phase adds
├─ TL;DR box                   ← wrapper piece (common spine) — write phase adds
├─ THE BODY                    ← the H2/H3 sections SELECTED FROM THE MENU
│     (H2 & H3 headings driven by the keyword set)
│     arranged into the loaded FORMAT SKELETON (Part 3.3):
│       listicle → N parallel items · report → 8-15 findings ·
│       comparison → table + per-option blocks · how-to → numbered steps ·
│       definitional → inverted-pyramid sections
│     each body section written in its style (explanation / how-to / comparison / list)
├─ Key takeaways / Conclusion  ← wrapper piece (common spine) — write phase adds
├─ CTA (one primary, forward)  ← wrapper piece (common spine) — write phase adds
└─ FAQ (5 Q&As, answers ≤40w)  ← wrapper piece (common spine) — write phase adds, LAST
```

**⭐ THE FIXED HOUSE ORDER (do not reorder — this is the single canonical article structure):**
**Intro → TL;DR → the body (H2 & H3 as per the keyword) → Key takeaways / Conclusion → one CTA → FAQ (last).**
Key takeaways come first, then the single primary CTA, then the FAQ closes the page. This matches the guidelines' house order (§4.6, §5.8-9, §11): "Key Takeaways, then the CTA, then the FAQ at the very end." The FAQ is always the last block on the page; the CTA sits between the takeaways and the FAQ.

So the menu's H2/H3s ARE the body; the wrapper pieces bookend them (Intro + TL;DR lead; Key takeaways/Conclusion, then one CTA, then the FAQ close). **The format skeleton (3.3) governs the body's arrangement; the common spine governs the wrapper.** The old planner's "seven types" map onto this: the wrapper pieces (intro · TL;DR · key-takeaways/conclusion · CTA · FAQ) + 4 body styles (how-to · comparison · explanation · list).

### What Station 1 actually does

0. **Route the format** (job 0, the format router — Part 3.1): Format field → archetype → load the playbook. The playbook's skeleton constrains everything below (a listicle plans per-item slots; a report plans findings; a comparison plans the table + per-option blocks).
1. **Select the sections — driven by FORMAT + WORD BAND, filtered by "earn its place." There is NO universal section count.**
   - **The format decides the *kind* and rough *count* of sections:** a how-to / definitional guide is ~4-7 H2s · a listicle is its N items (matched to the SERP, often 8-20) · a data report is its 8-15 findings · a comparison is its options + the table. The playbook's skeleton owns this.
   - **The word band is the *target* the count serves** — roughly, how many sections of honest depth add up to the band. It is a target to report against, never a floor to pad to.
   - **The earn-its-place filter is the final say:** every section must carry real, distinct value. Never add a section just to reach the word band. If a section would be filler, cut it — the article lands shorter, and that is the correct outcome (length is an output, not a quota).
   - **How it decides (an LLM judgment over the menu):** the dossier is a MENU of body H2s (each with H3s + fact-cards) and nothing else. The judgment reads the H2/H3 headings + their cards and keeps, merges, or cuts each section — a section survives only if it (a) fits the loaded format skeleton, (b) carries real value (closes one of the "5 gaps we can own", or is the differentiator angle `is_differentiator`, or holds strong unique evidence), and (c) is on-topic. Off-topic or thin sections are cut. For question-led formats, ≥50% of the surviving H2s phrased as questions.
2. **De-duplicate the headings** — research over-assigns: one real bundle had THREE H2s all targeting "cost per hire". Merge or cut sections that target the SAME keyword so we don't cannibalise, and tighten over-long H2s. Confirm the primary keyword is in the H1 (match hyphen/case-insensitively — "Skills-Based Hiring" satisfies "skills based hiring").
3. **Select H3s + evidence cards** within each chosen section — reference each card by `card_id` so Station 4 can trace it. **Read evidence wherever the bundle put it — H3 OR section** (verified: one bundle carried 12 cards directly on sections; reading H3-only would silently lose them).
4. **Reserve the wrapper pieces — do NOT write them yet.** The dossier's write_guidance says the **intro, TL;DR, key takeaways/conclusion, CTA, and FAQ are written at the write phase** — they are NOT in the menu. Because they all *summarise or frame the body*, Station 1 does not pre-write or pre-plan their content; it only reserves their slots in the fixed house order (**Intro → TL;DR → body → Key takeaways/Conclusion → CTA → FAQ**) and carries their RULES for Station 2: **intro = answer-first, primary keyword in the first 100 words and the main-topic answer inside the first 150 words · TL;DR present, directly under the intro · Key takeaways = 3-5 screenshot-ready bullets near the end · one primary CTA after the takeaways, matched to intent, forward-looking not a recap · FAQ = 5 Q&As placed LAST, each answer ≤40 words, answer-first.** Their actual wording is written at Station 2 AFTER the body exists (see Station 2's write order). For each SURVIVING body section, make a soft judgment on its writing STYLE (explanation / how-to / comparison / list) so Station 2 knows which template to use — not a rigid label, never keyword-matched from the heading.
5. **Gather the FAQ questions (finalised later).** If research supplied FAQ questions, carry them; if not (as in the sample), draft candidates from the material. Station 2 finalises + answers them AFTER the body, checking none duplicate a body section.
6. **Place loose keywords WITHOUT overfitting.** An orphan keyword (one research left unattached) stays ONLY if a relevant surviving section naturally carries it; otherwise drop it with a reason. Relevance + the word band + the format structure decide which sections live — never keep, add, or distort a section just to house a keyword.
7. **Carry the Build-spec numbers** — word band (reported, not a quota), snippet target, named primary sources, close/CTA spec.
8. **Fix the slug** (from the bundle).

### Source file → article_planner.py

**KEEP:** the section object (a section is an object with named fields, not a heading) · `gaps_addressed` (which gap this section closes) · `unique_data` → our `evidence_card_ids` (the exact evidence that must land here) · the seven section types · one-gap-one-section (every gap and card assigned to exactly one section) · the plan output layout.

**DROP:** default word counts · "beat competitors by 10%" · guessing type from the heading · mini-story/CTA placement by arithmetic · `_generate_angle`/`_generate_hook_idea` (canned templates) · `EngagementMap` (duplicates facts) · `create_default_structure`.

### The section object (corrected for the real schema)

```json
{
  "section_number": 3,
  "type": "explanation",
  "heading": "…",
  "strategic_angle": "…",
  "gaps_addressed": ["…"],
  "target_keyword": "… or null",
  "h3_plan": [
    { "h3": "…", "evidence_card_ids": [409, 411], "internal_link_candidates": ["…"], "external_links": ["…"] }
  ],
  "featured_snippet": false,
  "cta": "none | soft | product-mention"
}
```
Article-level fields: `slug`, `h1`, `format_archetype`, `word_band` {min,max}, `snippet_target`, `primary_sources` [], `close_spec`, `faq_questions` [5], `orphan_decisions` [].

### Code asserts before freeze (Kind 3)

- Every chosen evidence `card_id` appears in exactly ONE section.
- Primary keyword mapped to H1 + first-100 + 2-3 H2s + conclusion; every variation/secondary/in_body term assigned; **null target_keyword allowed** on differentiator sections.
- Section count matches the loaded FORMAT skeleton (NOT a fixed number) and every section passes the earn-its-place filter (no section is padding to hit the word band) · for question-led formats, ≥50% of H2s are questions · the FAQ has its 5 Q&As (research's questions if supplied, else authored) · every orphan keyword has a decision.
- The wrapper slots are reserved in the fixed house order: **Intro → TL;DR → body → Key takeaways/Conclusion → CTA → FAQ (last).** Key takeaways precede the single CTA, which precedes the FAQ; the FAQ is the final block. Close/CTA = one forward-looking primary CTA per Build spec, not a recap.
- The plan satisfies the loaded format skeleton (e.g. listicle has per-item slots; comparison has the table + vs-sequence; report has the findings menu).

### Build checklist — Station 1
- [ ] `fmt_router.py` — format-name → archetype lookup (+ the Gate 0 class map lives beside it); LLM fallback for unseen names
- [ ] `article-plan.json` schema + JSON-schema validator (incl. `format_archetype`)
- [ ] `prompts/plan-select.md` (select sections/H3s/cards using gaps + angle + the format skeleton)
- [ ] `prompts/plan-faq.md` (author the 5 FAQ questions)
- [ ] `prompts/plan-type.md` (assign each section its type)
- [ ] `plan_assert.py` (the Kind-3 assertions incl. the format-skeleton check; fails loudly)
- [ ] `article-plan.md` renderer (article_planner's output layout)

---

## STATION 2 — WRITE: one section at a time, typed prompts + the format overlay

**Purpose:** write each planned section, place internal links, write the meta.
**Inputs:** `article-plan.json` · brand-context · the bundle's evidence cards · the STORM dossier (drill-down) · the routed format playbook.
**Output:** `draft.md` + `links.json` + `meta-options.json`.

### What every section's write-prompt is handed (and the rule for using each)

Every section is written with the FULL brand context in front of it — but the files split into two kinds by HOW they're used:

- **Always applied (mandatory, never optional):** `brand-voice.md` (the 5 voice pillars + terminology table), `style-guide.md` (mechanics + banned words), `writing-integrity.md` (the 10 honesty rules), and the persona lens. The article is ALWAYS in our voice and ALWAYS honest — no section opts out.
- **Used only when genuinely relevant (never forced):** `features.md` (the product facts). A Testlify/product mention goes in ONLY where it's natural and earns its place — never cram features, never try to "use them all", never bend a sentence to fit one in. Most sections mention no product at all.
- **The material for THIS section:** its own evidence cards (full text) + the Build spec's named sources.

The rule in one line: **always voice + integrity; features only where relevant.** Voice and honesty are non-negotiable; product mentions are relevance-gated.

**The write ORDER matters — body first, wrappers last (this is the order of AUTHORING, not the order on the page; the finished page always follows the fixed house order Intro → TL;DR → body → Key takeaways/Conclusion → CTA → FAQ).** The intro, TL;DR, takeaways, CTA, and FAQ all *summarise or frame the body*, so they cannot be written well until the body exists. So Station 2 authors in this order:
1. **The body sections** (in the format skeleton), one at a time.
2. **The FAQ** — finalise the questions (drop any the body already answers) and write the answers, each **≤40 words** (the AEO cap — longer answers do not get lifted cleanly), answer-first. On the page the FAQ sits LAST.
3. **THEN the intro, TL;DR, key takeaways, and CTA** — written from the finished body + FAQ. The intro leads with the answer (primary keyword in the first 100 words; the main-topic answer inside the first 150 words). The TL;DR sits directly under the intro. Key takeaways = 3-5 screenshot-ready bullets. The CTA is one primary, forward-looking action matched to the reader's stage, not a recap. Assemble everything into the fixed house order.
4. **THEN the meta** (title + description) — written last of all, because it describes the whole finished article.

Each body/wrapper section is written by fusing FOUR layers into ONE prompt, then the AI writes that section:
- **Layer 1** — the type template (from section_writer.py's structure).
- **Layer 2** — the section packet: the plan object verbatim + the FULL text of its chosen evidence cards (gloss + verbatim + source_urls). Never truncated.
- **Layer 3** — the standing rules: persona lens, the fabrication rule, the evidence rule.
- **Layer 4** — the format overlay: the routed archetype's writing rules (Part 3.3 — e.g. the listicle per-item template, the comparison fairness mechanics, the report per-finding craft).

### Source file (section prompts) → section_writer.py

**KEEP:** seven types / seven instruction sets · the FAQ set nearly whole (4-6 questions, **answers ≤40 words** — the AEO cap per the guidelines, tighter than the 40-60w direct-answer block — answer-first, from real research) · "questions aren't answered elsewhere in the article" · the how-to set (numbered steps, action verbs, real tools, common mistakes, state the outcome) · the comparison set (be fair, real numbers, "best for X", table if 3+, cite competitor claims, grant real advantages) · the intro don'ts (no "[Topic] is…" / "When it comes to…" / "In today's world…" / dictionary-definition openings) · **the intro formulas (from the guidelines §4.2): PAS (Problem, Agitate, Solve) · APP (Agree, Promise, Preview) · AIDA — hook PLUS a direct answer, primary keyword in the first 100 words, the main-topic answer inside the first 150 words** · the explanation test ("a beginner could understand this, an expert wouldn't be bored") · the vague-word table (17 words → the specific to fetch from the bundle) · **the direct-answer templates (guidelines Appendix C): Definition, How-to (short), Comparison (short verdict) shapes to drop under any question heading — 40-60w, start with the key phrase, plain paragraph, no callout box** · the prompt-builder idea.

**DROP:** the mini-story "use a name" block (invents fake people) · "add contractions" · "add parenthetical asides/questions" · the AI-phrase blocklist · all the word ranges (except FAQ ≤40 and the 40-60w direct-answer block) · **silent truncation** (it passed only the first 3 insights/links — we pass ALL) · "strong CTA with risk reversal" as a hard requirement (soften to conditional) · the duplicated section-type list.

**REWRITE, don't import:** the *contents* of each type template come from `brand-voice.md` (5 pillars: Skills-Beat-Resumes, Show-the-Number, Fair-by-Design, Simple-Fair-Risk-free, the Hiring Coach; the terminology table; tone-by-content-type), `style-guide.md` (mechanics + banned-word list), `writing-integrity.md` (all 10 rules). Keep section_writer's *structure*, not its Castos advice.

**The evidence rule (Layer 3):** cite only from the packet's cards, `features.md`, or the Build spec's named primary sources. `stats.md`/`stories.md`/`opinions.md` are unconfirmed = **unusable** until signed off.

### Source file (link placement) → internal-linker.md

The linker is a **SELECTOR, not a discoverer** — research already attached 8-16 candidate links per section; the linker picks and places the best few.

**KEEP:** the six-field suggestion format (which page · which section · after which exact sentence · anchor text · full sentence · why · priority) · placement-by-location (body primary, 1 in intro max, 1-2 in conclusion, list items natural) · anchor-text guidance + good/bad examples (descriptive, varied, 2-5 words, <30% exact-match, never "click here") · "opportunities not pursued" (rejected links, with reasons — load-bearing, the pool is oversized) · "have I already linked this page?" (load-bearing, URLs repeat across sections) · the evaluation questions ("would I click this? too sales-y?") · links-to-avoid guardrails (≤1-2/paragraph, not only product pages, no repeats).

**DROP / PARK:** SEO-impact prediction (invention, cut) · cross-linking from other pages (needs whole-site knowledge, PARK) · user-journey map (decoration, optional) · Castos pages (replaced by the bundle's URLs).

**⭐ PILLAR PAGES — the deliberate current state (per Devansh):** pillars are being built in a separate effort and **do not exist in the candidate pool yet**. So:
- The linker runs NOW using the blog + feature-page links research already supplies.
- The "1-2 pillar links" line is **dormant** — the linker simply has no pillar candidates to pick, and that is fine.
- When pillars land, they enter the same pool the same way. **No change to how the linker works** — just more, higher-value candidates. The linker gets better automatically.
- Minor open item: research gives URLs but not page *type* (pillar/blog/product). Either add type in research later, or infer from the URL. Not a blocker.

### Source file (meta) → meta-creator.md

Runs LAST in the station, after the body + intro/TL;DR + key takeaways/CTA + FAQ exist (it describes the whole finished article). **The write phase owns meta fully.** One caveat: Stations 5-6 still edit the prose, so if editing changes the article materially, the meta is re-confirmed against the final version before the gate (Station 7) checks it — a cheap regen, not a full rewrite.

**KEEP:** 5 title options from 5 angles + 5 descriptions, recommend one with reasoning (the guidelines' **"write ten, keep one"** discipline — never ship the first headline) · **the headline swipe shapes (guidelines Appendix B): How-to · Number-list · Guide · Comparison · Question** — every option 50-60 chars, keyword near the front, one specific benefit/outcome, numbers/years for listicles and guides, matched to the format the SERP rewards, and still true to the article · the power-word/trigger-word lists (**meta-only exception** to the hype ban — SERP click-copy, not body prose) · the description formulas (Problem-Solution-CTA etc.) · character count per option · the SERP preview (mock up how it looks in Google) · the red-flags list (no clickbait, no ALL CAPS, no "click here", never misrepresent, no generic description; a title that over-promises and under-delivers hurts rankings when people bounce).

**DROP:** A/B testing recommendations (parked) · Castos / "| Castos" branding.

**Meta lengths:** style-guide says title ≤60, description ~150-160; the checklist says description **140-160**. Station 4 checks against the checklist's 140-160.

### Build checklist — Station 2
- [ ] `prompts/write-intro.md` … `write-conclusion.md` — the seven type templates (contents from brand-voice + style-guide + writing-integrity, structure from section_writer)
- [ ] `prompts/fmt-<archetype>.md` — the format-overlay blocks (Layer 4), one per archetype, distilled from Part 3.3
- [ ] `write_section.py` — the prompt-builder; fuses plan object + type template + format overlay + full evidence cards; NEVER truncates
- [ ] `prompts/place-links.md` — the internal linker; reads each section's candidate pool; writes `links.json`
- [ ] `prompts/write-meta.md` — the meta-creator; writes `meta-options.json`
- [ ] the standing-rules block (persona · fabrication · evidence-only-from-approved-sources) injected into every write prompt
- [ ] `assemble.py` — stitches sections + placed links into `draft.md`

---

## STATION 3 — CLEAN: mechanical scrub

**Purpose:** remove genuine noise. Pure code, zero judgment.
**Inputs:** `draft.md`. **Output:** `draft.clean.md` (atomic).

### Source files → scrub.md + content_scrubber.py

**KEEP:** invisible-character removal (15 named characters **plus a catch-all that strips every Unicode format-control character** — the smart bit, catches junk nobody listed) · whitespace normalisation (double spaces, punctuation spacing, cap blank lines at 2) · **em-dash AND en-dash replacement** (comma/semicolon/period; the guidelines ban BOTH em and en dashes — kept per Devansh's call, in practice mostly "→ comma", the editor pass is the backstop) · idempotency (running twice changes nothing) · atomic save (temp file + rename).

**DROP:** the AI-phrase regex rewriter (blind `leverage`→`use` on visible prose — breaks correct sentences, fourth copy of the list, and the part that actually **crashes**; cutting it fixes the file for free) · the "beat AI detectors" premise (wrong goal) · in-place overwrite (replaced by atomic save).

### Build checklist — Station 3
- [ ] `clean.py` — invisible-char removal (15 + Cf catch-all), whitespace normalise, em-dash AND en-dash replace; NO prose rewriting
- [ ] `write_atomic.py` helper — temp-file-then-rename (reused everywhere that saves)

---

## STATION 4 — MEASURE: the facts report

**Purpose:** answer every countable question → `facts.json`. The Python half of "Python feeds the MD checklist". **No score. No density. No word-count floor.**
**Inputs:** `draft.clean.md` · `article-plan.json` · `links.json` · `meta-options.json` · the routed archetype (for format checks).
**Output:** `facts.json` + a readable `facts-report.md`.

### Source file → content_scorer.py (the measurements, never the score)

**KEEP:** paragraph over 4 sentences → flag · sentence-rhythm check (5-sentence window finds flat stretches — the most reliable machine-writing tell) · prose-vs-bullets ratio (reported, no target) · meta title 50-60 / description 140-160 · H1 exists and contains the primary keyword · Flesch (reported; **and, per the guidelines §11 QA line, checked against a 60 floor at the gate** — the one readability metric that IS a pass/fail, alongside the >30-word-sentence and <10%-passive flags) · the report layout + "fix this first" ranking.

**DROP:** the 0-100 composite score + pass-70 · the whole humanity category (counting contractions/questions/brackets) · rewarding contractions/casual-openers · penalising a lack of contractions · counting numbers as proof of specificity (rewards fabrication) · the 2,000-word minimum · the AI-phrase blocklist · the 50-75% prose target · the unused SEO module.

**REPLACES:** specificity-by-counting-numbers → "does every stat trace back to the bundle?" · humanity-by-counting → `avoid-ai-writing` (6b) · the composite score → the checklist (7).

### Source file → readability_scorer.py (the engine, once)

**KEEP:** the engine that measures sentence length, paragraph length, passive voice, reading grade. **Called exactly ONCE** here (SEO Machine had three callers — that duplication is cut). Mostly signal — with the one exception the guidelines make binding: a **Flesch ≥60 floor** at the gate (§11), plus flags for sentences >30 words and passive >10%. The grade/length/passive breakdowns stay diagnostic.

### Source file → seo_quality_rater.py (plain yes/no checks)

**KEEP:** one H1 · meta lengths · has internal + external links. **DROP:** its 0-100 score (pass-80) and its density.

### Source files → keyword_analyzer.py + keyword-mapper.md

**KEEP:** keyword placement check (primary in H1/first-100/2-3 H2s/conclusion; **variations** + secondaries + in_body where mapped) · the section heat map ⭐ **reinterpreted as a topical-drift detector** — a section with zero mentions may have wandered off-topic, a flag for a human at Station 5, never "stuff more keywords in".

**DROP:** the entire density engine ("+28 instances to hit 1.5%" — the single most harmful instruction in the repo) · density targets/projections · LSI · the /100 integration score.

### Source file → seo-optimizer.md (the fact half)

**KEEP:** heading hierarchy (one H1, no skipped levels) · "every statistic needs a source link" (code flags un-cited numbers with line numbers) · featured-snippet formatting (a 40-60w liftable answer under the snippet-target H2).

### The full check list facts.json writes
- every planned evidence `card_id` appears in its assigned section (the broken-promise catch)
- keyword placement (primary + **variations** + secondaries + in_body where mapped) — the DataForSEO variations saved in the bundle's `keyword_set.variations` (6 in the sample) are checked too, not just the primary. Primary-keyword density is reported ONLY as an over-optimization ceiling (**>2% = stuffing flag**, guidelines §3.2) — never a floor or a target to pad toward
- **word count vs the Build-spec band** — reported WITH the band, not a standalone gate
- section heat map (zero-sections flagged)
- **required blocks present AND in the fixed house order** (guidelines §5.8-9, §11): intro answer-first (main answer in the first 150 words) → TL;DR directly under the intro → body → Key takeaways/Conclusion (3-5 bullets) → exactly ONE primary CTA (placed after the takeaways, before the FAQ) → FAQ LAST. Flag a missing block, a second CTA, or any block out of order.
- heading hierarchy · meta title 50-60 · description 140-160 · slug rules (short, keyword, no dates/stopword chains)
- links: ≥3 internal · ≤2/paragraph · every URL fetched returns 200 · ≥2 external · ≤2 cites/domain · ≥3 distinct domains · **no competitor domain** (style-guide's named list + `competitors.md`) · **≥1 evergreen authoritative external link** (a durable institutional source — WHO / SHRM / WEF-class, not a dated news item)
- numbers with no source link nearby → flagged with line numbers
- **stat recency**: each cited stat's year parsed and flagged if older than ~3 years (i.e. pre-2023 as of this writing) — 2024+ preferred; historical figures exempt (a human confirms at Station 5)
- **≥1 named-source quote present** (GEO lever); **≥1 evergreen authoritative external link** (WHO/SHRM/WEF-class institutional domain) present in a standard blog
- FAQ: 5 Q&As · answers ≤40 words (the AEO cap) · answer-first · FAQ is the LAST block on the page (after Key takeaways/Conclusion and the CTA)
- readability engine (once): Flesch, grade, sentence/paragraph lengths, passive %. Per the guidelines (§4.4) this is now checked against thresholds, not just reported: **Flesch ≥60** (the gate's floor per §11), **every sentence flagged if >30 words** (with the three longest surfaced for a rewrite), **passive voice <10%**, average sentence 15-20 words, paragraphs 2-4 sentences
- prose-vs-structure ratio per section · flat-rhythm windows · paragraphs >4 sentences
- self-consistency: all numbers listed, contradictions flagged (writing-integrity rule 6, PASS/FAIL)
- **format checks per the routed archetype** (from Part 3.3): listicle = ItemList schema + flat list + running numbers + parallel per-item template; comparison = real HTML table + blank-not-guessed + dated metrics + valid schema; answer-bait/glossary = DefinedTerm description byte-identical (+ DefinedTermSet on a hub); report = methodology fields present + Dataset schema + ungated; tool = WebApplication schema + wrapper sections present; case-study = the customer-story template blocks present + in order (eyebrow "Customer story", result-first H1, 4-field metadata, Challenge/Solution/Outcome, 3 stat cards, Details section) + every metric has baseline+timeframe; template = preview-above-fold present.

### Build checklist — Station 4 (BUILD THIS FIRST)
- [ ] `measure.py` orchestrator → `facts.json` + `facts-report.md`
- [ ] `check_evidence_landed.py` (trace each card_id into its section)
- [ ] `check_keywords.py` (placement + heat map)
- [ ] `check_structure.py` (H1, hierarchy, headings, **required blocks present + in the fixed house order: Intro → TL;DR → body → Key takeaways → one CTA → FAQ last**)
- [ ] `check_meta.py` (title/description lengths, slug)
- [ ] `check_links.py` (counts, ≤2/para, fetch-200, competitor-domain block, per-domain cap, **≥1 evergreen authoritative external link present**)
- [ ] `check_sources.py` (numbers with no nearby citation; **stat-recency flag: <2024 warned, ~3yr floor unless historical**; **≥1 named-source quote present**; no vague "studies show" attribution)
- [ ] `check_faq.py` (count = 5, answer lengths ≤40w, answer-first, FAQ placed last)
- [ ] `readability.py` (the single engine caller)
- [ ] `check_prose_rhythm.py` (prose ratio, rhythm windows, long paragraphs)
- [ ] `check_consistency.py` (numbers reconcile)
- [ ] `check_format.py` (the per-archetype checks, switched by `format_archetype`)
- [ ] `facts-report.md` renderer (content_scorer's report layout + fix-first ranking)

---

## STATION 5 — REVIEW: the AI judges, fed the facts

**Purpose:** the AI reads `draft.clean.md` + `facts.json` (so it NEVER counts) and judges only what needs judgment.
**Inputs:** `draft.clean.md` · `facts.json` · brand-context (persona, writing-integrity) · the routed format playbook. **Output:** `review.json`.

One checking prompt (Kind 2) per section type + one whole-article pass. What it judges:
- does each section deliver on its heading and close its assigned gap?
- **earn-its-place (whole-article):** does any section read as padding added to reach the word band? If a section carries no real, distinct value, flag it to cut — a shorter honest article beats a padded one. (This is the judgment mirror of Station 1's earn-its-place filter; the count is only ever what the topic honestly holds within the format skeleton.) **Routing note:** cutting or merging a WHOLE section is a PLAN-level defect, not a Station-6 prose edit — dropping a section would orphan its evidence cards and fail Station 4's broken-promise check. So this finding loops back to **Station 1** to regenerate + re-freeze the plan (drop the section, reassign or drop its cards), then re-write. It's rare, because Station 1's own earn-its-place filter should catch it first.
- FAQ: authentic questions? none answered elsewhere?
- comparison: fair, or a pitch in comparison's clothes? (format overlay: the fairness mechanics honoured?)
- listicle: per-item template held in strict parallel? every item earns its spot?
- report: is every finding genuinely liftable in one sentence?
- anchors: descriptive and natural, or forced?
- product mentions: natural, or promotional? (authority honesty: Testlify IS / IS NOT)
- flagged no-source numbers: does this claim need a citation? (find real or soften — NEVER invent proof)
- **quotes:** is there ≥1 named-source quote? If attributed to a **real external leader/body**, is it a genuine verifiable quote (never fabricated or paraphrase-as-quote)? If attributed to **Abhishek or Namrata**, does the composed quote sound like them, stay on-message, and make no unverifiable first-party metric claim?
- **stat recency:** is every cited stat recent (2024+ preferred; nothing older than ~3 years unless historical) and not superseded by a newer figure?
- **integrity sweep:** any invented "Testlify [X] Matrix/Framework"? any vague "studies show"/"experts agree" that must be named or cut?
- heat-map zero-sections: drift, or fine here?
- flat-rhythm stretches: which actually read flat?
- snippet target: genuinely liftable?
- persona check: any section tripping the persona's `not_this` → re-pitch or re-tag.

### Source files

**→ content-analyzer.md — KEEP:** Critical / High / Quick-wins sorting (three buckets, not a flat list of 30) · the behaviour rules (be specific with locations · prioritise · be honest · **"do not create work unnecessarily"** — stops an AI reviewer inventing problems to look useful).

**→ seo-optimizer.md (judgment half) — KEEP:** the AI-judgment version of "does this claim need a source", "is this anchor natural", "is this a real snippet opportunity".

**→ keyword-mapper.md (judgment half) — KEEP:** naturalness judgement — for each keyword use, forced or natural? The opposite of counting density.

**→ meta-creator.md red-flags — KEEP:** the AI applies the red-flags list to the chosen meta.

### Build checklist — Station 5
- [ ] `prompts/review-<type>.md` — one checking prompt per section type (the Kind-2 twin of each write prompt)
- [ ] `prompts/review-whole.md` — the whole-article pass (drift, authority honesty, persona, meta red-flags, format-overlay judgment items)
- [ ] `review.py` — feeds draft + facts.json into the prompts; sorts findings Critical/High/Quick-win; writes `review.json`

---

## STATION 6 — EDIT: add craft, then remove tells

**Purpose:** make the writing good, then strip AI tells. **Facts never change here** — any edit altering a number, claim, or citation is out of scope by rule.
**Inputs:** `draft.clean.md` · `review.json` · brand-context · the bundle's cards. **Output:** `draft.edited.md`.

### Station 6a — the editor (ADDITION) → editor.md + copy-editing/SKILL.md

**→ editor.md — KEEP the craft:** show-don't-tell (using OUR real data, never an invented Sarah) · kill corporate speak (leverage→use, delete "it should be noted") · add specific details ("recently"→"March 2024", "many"→"73%" — fetch the real number from the bundle) · vary sentence structure (pairs with Station 4's rhythm detector) · make lists actionable · the before/after report format (current → why it fails → rewrite → why it works) · the red lines (don't change facts, don't invent examples, no fluff for word count) · self-check questions.

**→ editor.md — DROP:** the composite-score JSON block · the mini-story *quota* (2-3 required — the forced count manufactures fabrication) · the CTA distribution quota · "add conversational devices" as a hard rule.

**→ editor.md — conversational devices, toned down not banned:** contractions and the occasional rhetorical question are part of Testlify voice; only the *checklist that forces* them is the problem. Allowed when earned, governed by `brand-voice.md`, never a quota.

**→ copy-editing/SKILL.md — KEEP the method (it structures 6a):** one focused pass per dimension · loop back after each pass (Loop C — a later fix can break an earlier one) · the "So What" test (every claim answers "why should I care?") · specificity sweep + "if it can't be made specific, it's filler — cut it" · clarity sweep · word-level cut/replace list · common problems & fixes.

**→ copy-editing/SKILL.md — the four changes:** "Prove It" → flag only, never add (its "add testimonials/case studies" invites fabrication) · Heightened Emotion → tone right down (FOMO is conversion manipulation) · Zero Risk → park (landing-page CTA work) · Voice sweep → defer (brand-voice + avoid-ai-writing own voice).

**Sweep order for 6a:** clarity → So-What → prove-it(flag-only) → specificity → toned-down-emotion, **looping back after each**. Every edit shown before/after.

### Station 6b — avoid-ai-writing (REMOVAL) → the skill (ours, sole prose owner)

**How to run it (verified):** edit mode on the draft file (minimal targeted edits; preserves passages already human; doesn't touch quotes/code/attributed text; re-reads to verify) · a **voice profile** chosen per `brand-voice.md` (casual/professional/technical/warm/blunt) · **iterate to convergence, cap 2 passes** · sole owner of every banned-phrase judgment (style-guide's list feeds the write prompts as guidance; this pass enforces at the end) · its P0 tier (chatbot artifacts, cutoff disclaimers, vague attributions, significance inflation) are hard credibility-killers to strip.

### Ownership settled
- **`avoid-ai-writing` = removal** (AI tells, hype, robotic transitions, forced casualness).
- **Editor = addition** (specificity, show-don't-tell, actionable lists, strong openings, before/after).
- Editor runs first (6a), avoid-ai-writing last (6b). On overlap, avoid-ai-writing is the single source and the editor defers.

### Build checklist — Station 6
- [ ] `prompts/edit-craft.md` — the editor sweeps, before/after format, red lines, fabrication rule, loop-back discipline
- [ ] `edit.py` — runs 6a sweeps, then invokes `avoid-ai-writing` in edit mode (voice from brand-voice, iterate cap 2); writes `draft.edited.md`
- [ ] guard: reject any 6a/6b edit that changes a number, claim, or citation (diff the facts before/after)

---

## STATION 7 — GATE: the checklist, then ship or route

**Purpose:** the single pass/fail gate. `seo-aeo-geo-checklist.md` is THE gate (it replaced SEO Machine's FIVE competing scores).
**Inputs:** `draft.edited.md` · `facts.json` · `review.json` · `meta-options.json` · `voices.md`. **Output:** a shippable article, or a routed `review-required/` package.

### Source file → seo-guidelines.md — DROPPED WHOLE
We take **nothing** from it. Our checklist is the superior replacement: its good half (answer-first, TL;DR, one-idea-per-section, FAQ) we already have phrased better; its bad half (density, word floors, LSI) is dead.

### The checklist's journey across the stations (so it's not invisible)
The one `seo-aeo-geo-checklist.md` isn't only a Station-7 thing — it threads through the whole back half:
- **Station 4 (MEASURE)** pre-computes every *countable* box of the checklist into `facts.json`.
- **Station 5 (REVIEW)** judges every *judgment* box of the checklist.
- **Station 7 (GATE)** runs the checklist itself: code ticks the countable boxes from facts.json, the AI ticks the judgment boxes from the review, and the verdict is pass/route.
So the checklist is authored once and *consumed* at 4, 5, and 7 — the single source of truth for "is this shippable".

### How the gate runs
- Code **pre-ticks every countable box** from `facts.json` (including the format checks).
- The AI **ticks the judgment boxes** citing Station 5/6 results.
- **Nothing is ticked from memory.**
- The author box renders from `voices.md` via the theme (auto-route: leadership/vision/CEO/strategy/future-of OR press-release/white-paper/PR → Abhishek Shah; everything else → Testlify Team; named individuals only on explicit request). Never in the body. Dates visible.
- The chosen meta option locks in.

### The checklist's contents (verified, the boxes grouped)
Content · Structure (one H1, **section count per the FORMAT skeleton — the checklist file's "4-7 H2s" is only the guide-family default; a listicle/report/comparison sets its own count, and the gate reads the count from the loaded format, not a fixed number** · ≥50% question H2s for question-led formats · hierarchy · **the fixed house order: answer-first intro → TL;DR → body → Key takeaways/Conclusion → one CTA → FAQ LAST** · 40-60w liftable direct-answer blocks under headings · **FAQ = 5 Q&As, each answer ≤40w** · one primary CTA placed after the takeaways and before the FAQ, forward not recap · no dividers) · Keywords (placement; **no density floor/target — a >2% ceiling only flags stuffing per the guidelines**) · Links (≥3 internal <30% exact, ≥2 external primaries incl. **≥1 evergreen authoritative source e.g. WHO / SHRM / WEF**, rel policy, no competitor, all 200) · AEO/GEO (question H2s, 4+ inline citations, **≥1 named-source quote**, quotable sentences, one idea per section, ≥1 embedded video) · Sources & claims integrity (every stat → exact source URL, 200, **year matches and is recent — 2024+ preferred, ~3-year floor unless historical**, verified on page; 2-3+ domains; ≤2/domain; self-consistency; **no invented framework, no vague "studies show" attribution**) · E-E-A-T (author box, dates, first-hand markers, Who/How/Why test, **citation integrity = P0**) · Meta · Readability/images (**Flesch ≥60, no sentence >30 words, passive <10%, no em OR en dashes**) · Voice & authority (brand voice, persona lens, authority honesty, no fake customer/quote/metric) · Ship.

### ⭐ Build reminder — turn the reference files into vettable checklists

`seo-aeo-geo-checklist.md` already IS a checklist, which is exactly why the gate can vet against it. The other reference files are still **prose**, which is hard to vet. Before this station is built, distil each into a **checklist form** (concrete, checkable rows) so the final article can be vetted against them the same way:
- `writing-integrity.md` → an integrity checklist (the 10 rules as pass/fail rows — no fake customer/quote/metric, every stat sourced, self-consistent numbers, etc.).
- `brand-voice.md` → a voice checklist (the 5 pillars + terminology table as checkable rows).
- `features.md` → a product-honesty checklist (every product claim true + "IS / IS NOT" honesty, mentions relevance-gated not crammed).

**Keep single-ownership (Rule 5):** these do NOT become competing gates. They plug in as the **Voice / Integrity / Authority sections of the one `seo-aeo-geo-checklist`**, so there's still exactly one gate — it just now vets voice, integrity, and product-honesty as explicit checkable rows instead of vague prose. (Ties to the §7-score open decision below: the boxes are the verdict.)

### Loop B — the retry loop (aligned to the standard, and TARGETED)
- Gate fails → **each failing box becomes a specific, actionable line in the revision brief** — the box that failed + the exact `facts.json`/`review.json` evidence for why (which line, which section, which number) → **Station 6 fixes ONLY those flagged issues, not a blind rewrite** → re-clean (3) → re-measure (4) → **re-confirm the meta if the prose changed** (the meta describes the article; a changed body can make it stale — the gate checks it) → re-gate (7). The loop acts on the precise failures and touches nothing else.
- **The one structural exception:** a finding that needs a WHOLE section cut or merged (e.g. Station 5's earn-its-place) is a PLAN defect, so it loops further back — to **Station 1** to regenerate + re-freeze the plan — not to Station 6. See Station 5's routing note.
- **Cap 3 passes** (the standard's §3.5/§7 number).
- Still failing after 3 → ships as a **draft** into `review-required/` with `_REVIEW_NOTES.md` stating which boxes failed and why. This IS the standard's "ship as a draft and report it."
- A **P0 failure (citation integrity)** blocks regardless.

### ⚠️ Open decision — the §7 score (verified, needs Devansh)
The checklist's Ship line says "Overall score ≥ 80 (§7)". §7 is, verbatim: `Overall = SEO ×0.25 + Structure ×0.15 + Content ×0.25 + EEAT ×0.15 + AEO/GEO ×0.20`, publish ≥ 80, **no rubric for how to score any dimension.** That is the same gameable vibe-scoring rejected five times across SEO Machine — five judgment numbers with fixed weights.
- **Recommendation:** replace §7 with the checklist itself — every box ticked + no P0 = ship; any unticked box = the revision brief. The boxes ARE the score. A two-line edit to the standard + checklist Ship lines, once approved.

### Build checklist — Station 7
- [ ] `gate.py` — pre-ticks countable boxes from facts.json, collects AI-ticked judgment boxes, applies P0 rule, decides ship vs route
- [ ] `prompts/gate-judgment.md` — the judgment-box tick prompt (cites Station 5/6, never memory)
- [ ] `route_review_required.py` — writes the `review-required/<slug>/` package + `_REVIEW_NOTES.md` on 3rd failure
- [ ] author-box render hook (from voices.md auto-route)
- [ ] distil `writing-integrity.md` + `brand-voice.md` + `features.md` into checklist rows, folded into the one checklist's Voice/Integrity/Authority sections (the build reminder above)
- [ ] DECISION GATE: resolve §7 before this station is final

---

## STATION 8 — PUBLISH (parked) + close the loop

**Purpose:** push to WordPress (built later), get the page reachable by every engine, and close the research queue.

### Source files (mapped, parked) → publish-draft.md + wordpress_publisher.py + the Yoast MU-plugin
Maps Markdown + frontmatter → a WordPress draft with Yoast fields via the REST API. Outside this build until the upstream pipeline is proven.

### NOT parked
- The orchestrator **updates `research-log.csv`'s `write_status` column** for the topic (research built the queue expecting this).
- **Bing indexing** (cross-format correction): confirm the page is indexed in Bing + the sitemap is submitted to Bing Webmaster Tools — ChatGPT search runs on Bing. Also confirm crawlers (GPTBot, Bingbot, Googlebot) are allowed and the answer text is server-rendered HTML, not JS-hidden or in an image.

### Build checklist — Station 8
- [ ] (later) `publish.py` wrapping WordPress REST + Yoast fields
- [ ] `update_queue.py` — sets `write_status` in research-log.csv (build with the orchestrator, not later)
- [ ] Bing/crawlability checklist item wired into the publish flow

---
---

# PART 5 — The loops

- **Loop A — per-section (inside Station 2):** write a section → its type's Kind-2 mini-check runs immediately → one rewrite if needed → move on. Catches problems while the section is one screen of text. (Applies to the body sections AND the wrapper pieces, which are written after the body.)
- **Loop B — whole-draft (7 → 5/6 → 3 → 4 → 7):** gate fails → each failing box becomes a **targeted** fix (not a blind rewrite) → fix at 5/6 → re-clean → re-measure → **re-confirm the meta if the prose changed** → re-gate. **Cap 3 passes**, then `review-required/` + notes.
- **Loop B's structural exception (7 → 1):** a finding that needs a WHOLE section cut or merged (e.g. Station 5's earn-its-place) is a PLAN defect — it would orphan the plan's evidence cards — so it loops all the way back to **Station 1** to regenerate + re-freeze the plan, then re-write. Rare, since Station 1 should catch it first.
- **Loop C — inside 6a:** after each editing sweep, re-check the earlier sweeps (a voice fix can break clarity).

Why loops can't corrupt anything: every station writes a named file atomically; a crash resumes from the last completed station; the `article-plan.json` never changes *within* a pass — an ordinary revision changes the draft, never the contract. The one time the plan itself must change (the structural exception above) is not an in-place edit — it's a full **regenerate + re-freeze** at Station 1, so the contract stays immutable-within-a-pass.

---
---

# PART 6 — The build plan

## 6.1 What lives where (file shapes, per the conventions)

| Piece | Format | Why |
|---|---|---|
| Gate 0 class map + format-router map | **code lookup tables** (beside `fmt_router.py`) | pure mappings, no LLM; one owner |
| article-plan | **JSON** | the machine-checkable contract every station verifies against |
| the 7 write + 7 review prompts · plan-select/faq/type · fmt-<archetype> overlays · place-links · write-meta · edit-craft · gate-judgment | **MD, one file per prompt** in `prompts/` | diffable, single-sourced, never inline in code |
| plan-assert · clean · measure (+ check_*.py incl. check_format) · assemble · edit · gate · route · update_queue | **Python step scripts**, each "Reads: X, Writes: Y" | countable work, resumable named outputs |
| facts | **JSON + facts-report.md** | Python's half of feeding the MD checklist |
| the gate | the existing **seo-aeo-geo-checklist.md** (pointer, never copied) | one owner |
| the format playbooks | **embedded in this doc — Appendix D** (the full per-archetype playbooks) | one owner; Part 3.3 encodes the keepers for the pipeline, Appendix D the full version |
| the orchestrator | **run_write.py** — pure sequencing, `== Step N ==`, resumable, `--redo` flags | the conventions' twin-file rule (this doc is its readable twin) |

Directory shape (per project-structure conventions):
```
workflows/03-content-machine/15-write/            (or wherever the write engine sits)
  write-phase-architecture.md    # THIS FILE — the recipe + design record
  README.md                      # how to run + file map
  scripts/
    config.py                    # all paths + settings from one anchor; company = one setting
    llm.py                       # the shared AI caller (claude -p / codex exec)
    run_write.py                 # the orchestrator (pure sequencing)
    fmt_router.py                # Gate 0 class map + format→archetype map
    plan_assert.py · clean.py · measure.py · check_*.py · assemble.py · edit.py · gate.py · route_review_required.py · update_queue.py · write_atomic.py
  prompts/
    plan-select.md · plan-faq.md · plan-type.md
    write-intro.md … write-conclusion.md
    fmt-listicle.md · fmt-comparison.md · … (the 9 archetype overlays)
    review-<type>.md · review-whole.md
    place-links.md · write-meta.md · edit-craft.md · gate-judgment.md
# output → projects/<company>/03-content-machine/write/out/<slug>/
```

## 6.2 Build order (one piece at a time)

0. **Gate 0 + the router maps** — pure lookup tables (`fmt_router.py`), buildable in an hour, and they immediately clean the queue: the conductor stops burning research runs on quizzes/landing pages. (Needs the one-line `writability` column + pick-logic edit in research layer 14.)
1. **Station 4 (MEASURE)** — pure code, testable TODAY against any existing draft; Stations 5 and 7 depend on its `facts.json`. Start with `check_evidence_landed.py` and `check_links.py` — the two highest-value catches.
2. **Station 1 (PLAN)** — the plan schema + assertions freeze the contract everything reads (router already exists from step 0).
3. **Station 2 (WRITE)** — the seven type prompts + the 9 format overlays + the linker + the meta. The judgment layer.
4. **Station 3 (CLEAN)** — small, pure code; slot in once there's a draft to clean.
5. **Station 5 (REVIEW) + Station 6 (EDIT)** — the judgment + craft passes, once facts.json exists to feed them.
6. **Station 7 (GATE) + Loop B routing** — after resolving the §7 decision.
7. **The orchestrator (`run_write.py`)** — pure sequencing over proven steps. Add `update_queue.py` here.
8. **Station 8 (PUBLISH)** — whenever the upstream pipeline is proven.

---
---

# PART 7 — Open decisions (for Devansh)

1. **§7 score** — replace the weighted 0-100 vibe-score with the checklist itself (recommended), or keep it? Blocks Station 7 being final.
2. **stats.md / stories.md / opinions.md** — unconfirmed/empty, so unusable. Someone has to confirm the real numbers and sign off the real customer stories (they currently violate writing-integrity's named-customer ban until approved), or articles stay thin on Testlify's own proof — and **all 32 case-study ideas stay blocked**. Not urgent this second; real gap.
3. **The 100 no-format ideas** — need a format assigned before Gate 0 can class them.
4. **Page-type label for links** (pillar/blog/product) — add in research, or infer from URL. Minor; not a blocker.
5. **Pillar pages** — being built separately; the linker is dormant on pillar links until they exist, then picks them automatically. No rework.
6. **The tool-build pipeline** (195 WRITE+BUILD ideas, mostly quizzes/assessments) and the **landing-page system** (227 NOT-ARTICLE ideas) — the two biggest non-article buckets; separate machines to plan after the write phase ships.

---
---

# APPENDIX A — Master traceability (every kept SEO Machine idea → its station)

| SEO Machine file | Exact items kept | Station |
|---|---|---|
| **article_planner.py** | section object as JSON · gaps_addressed · unique_data (→ evidence_card_ids) · seven types · one-gap-one-section assertion · plan output layout | 1 |
| **section_writer.py** | seven typed prompts · FAQ set (answers ≤40w, answer-first, not-elsewhere) · how-to set · comparison set · intro don'ts + PAS/APP/AIDA formulas · explanation test · vague-word table · prompt-builder | 2 + 6a |
| **internal-linker.md** | six-field format · placement-by-location · anchor rules · opportunities-not-pursued · already-linked check · evaluation questions · links-to-avoid | 2 |
| **meta-creator.md** | 5×5 options + recommend · power-words (meta-only) · description formulas · char counts · SERP preview · red-flags | 2 + 5 |
| **scrub.md + content_scrubber.py** | invisible-char removal (15 + Cf catch-all) · whitespace · em-dash replace · idempotency · atomic save | 3 |
| **content_scorer.py** | paragraph>4 flag · rhythm check · prose ratio (reported) · meta length checks · H1+keyword check · Flesch (reported) · report layout + fix-first ranking | 4 |
| **readability_scorer.py** | the measuring engine, called once, reported not gated | 4 |
| **seo_quality_rater.py** | plain yes/no checks (H1, meta lengths, links present) | 4 |
| **keyword_analyzer.py** | keyword placement check | 4 |
| **keyword-mapper.md** | section heat map as drift detector · naturalness judgement · placement checklist | 4 + 5 |
| **seo-optimizer.md** | every-stat-needs-a-source · heading hierarchy · quick-wins bucket · keyword distribution map · snippet formatting · anchor-text check | 4 + 5 |
| **content-analyzer.md** | Critical/High/Quick-wins sorting · behaviour rules ("don't create work") · placement check · readability engine (once) · plain SEO checks | 5 + 4 |
| **editor.md** | show-don't-tell · kill corporate speak · add specifics · vary structure · actionable lists · before/after format · red lines · self-check · fabrication rule | 6a |
| **copy-editing/SKILL.md** | one-pass-per-dimension · loop-back · So-What · specificity+filter-filler · clarity · word-level list · common-problems | 6a |
| **avoid-ai-writing (ours)** | edit mode · voice profile · iterate cap 2 · sole prose owner | 6b |
| **seo-guidelines.md** | nothing — our checklist replaces it | 7 (dropped) |

**Parked (real, but not write-phase):** cross-linking from other pages · cannibalisation · A/B meta testing · WordPress publishing · the §7 score decision · the tool-build pipeline · the landing-page system · off-site entity signals (Wikidata/directories) · content-refresh cadences.

---
---

# APPENDIX B — The old W1-W9 build list, mapped to stations (plan 1 absorbed)

The July 2026 plan framed the build as W1-W9. Every W-task now lives in a station; nothing was lost.

| Old task | What it was | Now lives in |
|---|---|---|
| **W1 — the write checklist** | assemble the per-article checklist from the guidelines' 📝 items | Station 7 (the gate = seo-aeo-geo-checklist) |
| **W2 — keyword-coverage check** | verify primary + variations + secondaries appear; primary in H1/first-100/2-3 H2s/conclusion | Station 4 (`check_keywords.py`) |
| **W3 — cite-with-credibility** | prefer the most credible + freshest source; no whitelist; never a competitor; ≤2/domain, 3+ domains | Station 2 (evidence rule) + Station 4 (`check_links.py`, `check_sources.py`) |
| **W4 — link integrity (200)** | every external link + every stat's source URL returns 200 | Station 4 (`check_links.py`) |
| **W5 — internal anchors** | varied, descriptive, keyword-aware anchors; <30% exact; ≤2/para; ≥3 internal; one product page | Station 2 (`place-links.md`) + Station 4 (`check_links.py`) |
| **W6 — URL slug decision** | include primary keyword, lowercase, hyphens, short, drop stop-words | Station 1 (slug fixed from bundle) + Station 4 (`check_meta.py`) |
| **W7 — meta + author box + self-consistency** | meta lengths; author box from voices.md via theme, never in body; every number reconciles | Station 2 (meta) + Station 7 (author box) + Station 4 (`check_consistency.py`) |
| **W8 — the checklist-verification workflow (the gate)** | check the article against W1's checklist, then the mandatory avoid-ai-writing pass | Station 7 (gate) + Station 6b (avoid-ai-writing) |
| **W9 — the /write orchestrator** | one entry script: bundle in → draft → checks → gate → publish; resumable | Part 6 / `run_write.py` |

**Decisions locked in plan 1 (still hold):** write verifies against the research checklist, does not re-research · cite-with-credibility, model-decided, no whitelist · link-200, freshness, self-consistency, anchor-wording, slug-choice, meta all live in write (they need the live page / final prose) · author box rendered by the theme from voices.md, never in body · we only write NEW articles (no re-slug / refresh governance).

---
---

# APPENDIX C — The SEO Machine design record (the full "why", per file — plan 2 absorbed)

This is the reasoning behind every kept/dropped decision above. One entry per file we studied. Read this when you want the argument, not just the placement. The governing rule under all of it: **code counts, the AI judges** — and every file below broke it in the same way, using arithmetic to make editorial decisions.

---

## article_planner.py

**What it is:** not a program — a **form** that defines the named boxes a section plan must fill. Nothing in the SEO Machine repo imports it. The form is the good part; the auto-fill is the bad part.

**Verdict:** do not port the file; take its field list as JSON. Strip the auto-fill and what remains is one JSON shape — 469 lines of Python to describe that is not worth maintaining.

**Kept:** the section object (a section is an object with named fields, so a script can check the draft against it) · `gaps_addressed` (forces every section to have a stated reason to exist) · `unique_data` (says which evidence goes where — most outlines never do) · the seven section types (each gets its own prompt downstream) · one-gap-one-section (nothing forgotten, nothing said twice) · the plan output layout.

**Dropped:** default word counts (invented, no source) · "beat competitors by 10%" (length-chasing) · guessing type from the heading ("Best practices" matches two types; our own voice matches none and silently becomes "explanation") · mini-story placement by arithmetic (a quota → invented filler) · CTA placement by arithmetic (never asks if the reader is ready to buy) · `_generate_angle` (pastes "Comprehensive coverage of <heading>" — restates the heading) · `_generate_hook_idea` (five canned sentences) · `EngagementMap` (duplicates facts already on each section, so the copies disagree) · `create_default_structure` (the shape of every forgettable SEO article).

**Noted, no action:** its meta-elements list — sensible, but our bundle + checklist already produce all of it.

---

## section_writer.py

**What it is:** a **prompt library** — a different instruction set per section type, so an FAQ and a how-to aren't written the same way. Seven types, each with requirements/dos/donts/quality-checks. The shape is right; the contents range from good to actively harmful. This is the file that produced the "three kinds of instruction" insight (Part 1, Rule 3).

**Verdict:** keep the shape (seven types, each with its own write + check prompt), rewrite the contents from our brand files. Prompts live in their own `.md` files, one per prompt, never inline in a `.py`.

**Kept:** seven types / seven instruction sets · the FAQ set nearly whole (4-6 questions, **answers ≤40 words** — the guidelines' AEO cap, tighter than the 40-60w direct-answer block so the FAQ answer lifts cleanly — answer-first, from real research) · "questions aren't answered elsewhere in the article" (the best single line in the file; stops the FAQ becoming padding) · the how-to set (numbered steps, action verbs, real tools, common mistakes at the step, state the outcome) · the comparison set (fair, real numbers, "best for X", table if 3+, cite competitor claims, grant real advantages) · the intro don'ts (the four most common bad openings on the internet, named exactly) · the explanation test ("a beginner could understand this, an expert wouldn't be bored") · the vague-word table (17 words → the specific to fetch; it says go find the real number, not delete the word) · the prompt-builder idea.

**Dropped:** the mini-story "use a name" block ⚠️ (combined with the planner's mini_story quota it orders the AI to invent three fictional named people per article — directly breaks writing-integrity; non-negotiable) · "add contractions for natural voice" (forced contractions are what AI writing sounds like) · "add parenthetical asides/questions" (a countable proxy for a quality it can't measure) · the AI-phrase blocklist (avoid-ai-writing covers far more) · all the word ranges (made-up; exceptions: FAQ ≤40 and the 40-60w direct-answer block) · silent truncation (passed only the first 3 insights/links — the exact silent loss "one gap, one section" exists to prevent) · "strong CTA with risk reversal" as a hard requirement (pushes a pitch onto informational articles) · the duplicated section-type list.

---

## content_scorer.py

**What it is:** a **grading machine** — reads a draft, gives one number out of 100 across five weighted categories (Humanity 30%, Specificity 25%, Structure 20%, SEO 15%, Readability 10%), passes at 70. It actually runs. The whole mechanism is counting patterns.

**The core problem:** it cannot measure what it claims, so it measures things that correlate, and those can be faked. A good factual paragraph scores badly on "humanity" (no contractions/questions); rewriting it with padding, a rhetorical question with no answer, and a manufactured accusation scores much higher and is worse writing. And the same AI writing the article is told the scoring rules, so it aims for the scoreboard. This is the disease repeated across the repo: **a countable proxy standing in for a quality it can't measure.**

**What it does NOT do (though `/write` claims it):** it does not revise, re-run, move a failed draft, or write a review note. It prints and exits.

**Verdict:** reject the score, keep the report and a handful of checks.

**Kept:** the report layout (one screen, worst first) · "fix this first" ranking (by damage, not order found) · paragraph >4 sentences → flag · sentence-rhythm check ⭐ (5-sentence window finds flat stretches — the most reliable machine-writing tell) · meta title 50-60 / description 150-160 · H1 exists + contains the primary keyword · prose-vs-bullets ratio (reported, no target) · Flesch (reported, not gated).

**Dropped:** the 0-100 score + pass-70 · the whole humanity category (counting contractions/questions/brackets/"Trust me") · rewarding contractions/casual-openers · penalising a lack of contractions (a formality tax) · counting numbers as proof of specificity (never checks if they're true or sourced — an incentive to fabricate) · the 2,000-word minimum · the AI-phrase blocklist (third copy) · the 50-75% prose target · the unused SEO module (dead weight that looks live).

**Replaces:** specificity-by-counting → "does every stat trace back to the bundle?" · humanity-by-counting → `avoid-ai-writing` · the composite score → the checklist.

---

## content-analyzer.md + its five modules

**What it is:** an agent (a checking prompt) that asks the AI to run five Python tools and merge them into one report. The code block is real (all five functions exist, arguments match) — what's missing is the *glue*: no single script runs all five and merges them, so the AI is asked to be the glue each time, which is neither reliable nor repeatable.

**The five modules, verdicts:** search_intent (word-matching; drop — intent after the draft is too late) · keyword_analyzer (keep placement only; drop density % and LSI) · content_length_comparator (drop — chasing competitor length is the wrong goal) · readability_scorer (keep, once — the one genuinely useful engine) · seo_quality_rater (keep the plain yes/no checks; drop the score and density).

**Two corrections about our own research (verified):** we do NOT formally label search intent (it's implied by keyword choice), and we DO get a word band from research (the earlier "no length target" claim was wrong — see Part 2.2).

**The readability relationship (verified):** not duplicates — one engine (`readability_scorer.py`) called by two places (`content_scorer.py` folds it in; `content-analyzer.md` calls it again). Fix: one engine, one caller.

**Kept:** Critical / High / Optimization sorting · the behaviour rules ("be specific, prioritise, be honest, **do not create work unnecessarily**") · keyword placement check · the readability engine (once) · the plain SEO checks.

**Dropped:** "run these five modules" as the AI's job (no glue; numbers get estimated and shown as measured) · keyword density 1-2% · LSI · search_intent at write time · content_length_comparator · the second/third scores (rater at 80, analyzer's own) · the duplicated readability reporting.

**Tell:** its last line says "help podcast creators succeed" — Castos's agent, a reminder that every agent file here is one company's prompt, not a neutral standard.

---

## seo-optimizer.md

**What it is:** the second reviewer — one long SEO checklist plus a report shape. Mostly a duplicate (fifth file to check keyword placement, fourth to check meta lengths, third to demand 2,000 words), but it forced the **"Python feeds the MD checklist"** decision (Part 1, Rule 2) and adds three genuinely new things.

**Kept:** "every statistic needs a source link" (our writing-integrity discipline as a concrete step — Python finds the un-sourced number, the AI decides if it needs one) · heading hierarchy check (one H1, no skipped levels — a real fault no other file checked) · the Quick-Wins bucket (sort by effort, not just importance) · the keyword distribution map (a 6-line at-a-glance panel) · featured-snippet formatting · descriptive anchor-text check.

**Dropped:** keyword density 1-2% (fifth appearance) · LSI · 2,000+ words (third appearance) · the score out of 100 + /25 sub-scores (fourth scoring system) · the readability block (third copy) · the Castos/podcast-relevance section · building our checklist from this file.

---

## meta-creator.md

**What it is:** the narrowest reviewer — one job, write the meta title and description. The best-structured agent file in the set. A generating prompt (kind 1).

**Verdict:** keep most of it. The one exception to a standing rule: the AI-hype-word ban does NOT apply here — meta is SERP click-copy, not body prose; a power word earning a click in a ~55-char title is a different job from the same word bloating a paragraph.

**Kept:** 5 options from 5 angles + recommend one with reasoning · the power-word/trigger-word lists (meta-only exception) · the description formulas · character count per option · the SERP preview (judge a title in the result, not in isolation) · the red-flags list (no clickbait, no ALL CAPS, no "click here", never misrepresent, no generic description).

**Dropped:** A/B testing recommendations (needs traffic + a tool + weeks) · Castos / "| Castos" branding.

**Resolved (was flagged):** who owns the meta title → the write phase, fully (research produces no meta — verified).

---

## internal-linker.md

**What it is:** the fourth reviewer — decides which of our pages this article links to, and where. The best agent to carry over.

**The key correction:** it is NOT blocked on a page list we don't have. Research already supplies candidate links per section (8-16 per section; verified). So the linker is a **selector, not a discoverer** — research did discovery, the linker does pick/place/phrase/reject. It can only place links that exist in the bundle, so it can't invent URLs.

**Kept:** the six-field suggestion format (which page · which section · after which exact sentence · anchor · full sentence · why · priority) · placement-by-location · anchor-text guidance + good/bad examples · "opportunities not pursued" (load-bearing — the pool is oversized, so rejecting is the main job) · "have I already linked this page?" (load-bearing — URLs repeat across sections) · the evaluation questions · links-to-avoid guardrails.

**Dropped / parked:** SEO-impact prediction (confident invention, cut) · cross-linking from other pages (needs whole-site knowledge, park) · user-journey map (decoration, optional) · Castos pages.

**Pillar pages:** being built separately; the "1-2 pillar links" line is dormant until they exist, then the linker picks them automatically — no rework. (See Station 2 for the full note.)

---

## keyword-mapper.md

**What it is:** the fifth reviewer — where the keyword appears and where it's missing. A fork in the road: one genuinely good idea, and the single worst idea in the repo.

**The worst idea, in full view:** it builds its whole engine around hitting a density number — "Current 0.42% (11 instances) · Target 1.5% (39) · Need +28 instances" — literally instructing someone to insert the exact phrase 28 more times. Density has been a dead ranking factor for a decade, and deliberately repeating a phrase to a number is exactly what Google's spam systems catch. Handed to the writing AI it makes the page worse and riskier.

**The one good idea — the section heat map** ⭐: read correctly it is not about *how many* times the keyword appears, but *whether a whole section forgot the topic exists*. A section at zero is a **topical-drift detector**, a flag for a human — not "add keywords to a quota." Same display, opposite conclusion: keep the map, throw away the interpretation.

**Kept:** the section heat map (as a drift detector) · naturalness judgement (forced or natural? — the opposite of counting density) · the placement checklist.

**Dropped:** the entire density engine ⚠️ · density targets/projections · LSI (sixth appearance) · the /100 integration score (fifth scoring system) · Castos framing.

**Parked — cannibalisation:** two of our own articles fighting over one keyword. Real and important, but needs whole-site knowledge, not one article. A later, site-level job.

---

## The three code modules (readability_scorer.py · seo_quality_rater.py · keyword_analyzer.py)

Same story three times: keep the parts that count facts, drop the parts that score or chase density.

- **readability_scorer.py** — the measuring engine (sentence/paragraph length, passive voice, Flesch). Keep, exactly once. Two other files call it; that duplication is cut. Signal, never a gate.
- **seo_quality_rater.py** — keep the plain yes/no checks (one H1, meta lengths, has internal + external links); drop the score out of 100 (pass-80 disagrees with content_scorer's 70) and the density.
- **keyword_analyzer.py** — keep the placement check (feeds the heat map); drop density % and LSI.

Net: only two things survive as real tools — the readability engine (once), and a set of plain yes/no SEO + placement checks (the Python half of "Python feeds the MD checklist").

---

## editor.md

**What it is:** the first file about *making the prose good*, not checking it. The best writing craft in the repo, wrapped around every bad idea we've killed, gathered in one place. The most important file in its round and the most contaminated.

**The self-contradiction at its heart:** it demands 2-3 named mini-stories ("When Sarah launched her SaaS in 2023…") AND bans made-up examples ("Don't add false claims or made-up examples") — in the same document. We resolve it with the fabrication rule (Part 1, Rule 4): the line is disguised vs signposted, not fake vs real, with a hard ban on fake Testlify customers/results.

**Kept — the craft:** show-don't-tell (using our real data) · kill corporate speak · add specific details (fetch the real number from the bundle) · vary sentence structure (pairs with the rhythm detector) · make lists actionable · the before/after report format (current → why it fails → rewrite → why it works) · the red lines (don't change facts, don't invent examples, no fluff for word count) · self-check questions.

**Dropped:** the composite-score JSON block (wires the editor into the rejected loop) · the mini-story *quota* (the forced count manufactures fabrication) · the CTA distribution quota · "add conversational devices" as a hard rule (toned down, not banned — allowed when earned, governed by brand-voice).

**Ownership settled:** avoid-ai-writing = removal; editor = addition; editor runs first, defers to avoid-ai-writing on overlap.

---

## copy-editing/SKILL.md

**What it is:** a skill — a systematic editing method: one focused pass per dimension, seven passes, loop back after each. Built for marketing/conversion copy, so we take the method and trim the conversion apparatus. It's not a separate desk from editor.md — it's the discipline that structures the editor's craft (editor = *what* to fix; copy-editing = *how to sequence* the fixing).

**Kept:** one focused pass per dimension · loop back after each pass (a later edit can silently break an earlier one — the most valuable idea in the file) · the "So What" test (every claim answers "why should I care?" — catches the #1 B2B failure) · specificity sweep + "if it can't be made specific, it's filler — cut it" · clarity sweep · the word-level cut/replace list · common problems & fixes.

**The four changes:** "Prove It" → flag only, never add (its "add testimonials/case studies" invites fabrication) · Heightened Emotion → tone right down (FOMO is conversion manipulation, wrong for calm informational authority) · Zero Risk → park (landing-page CTA work) · Voice sweep → defer (brand-voice + avoid-ai-writing own voice).

---

## scrub.md

**What it is:** a command — the "clean the raw text after it's written" desk. Two jobs; one is pure mechanical cleanup, and the framing around it is off.

**Verdict:** keep the cleanup, drop the "beat the detector" premise.

**Kept:** invisible-character removal (the one clearly-real job) · em-dash replacement (kept per Devansh's call — our global rule is no em-dashes, so an automatic sweep is a useful safety net; a wrong comma-vs-semicolon is a small cost next to a dash slipping through; the editor pass is the backstop) · whitespace normalisation · idempotency.

**Dropped:** the "make it appear human / beat AI detectors" premise (wrong goal — we make writing genuinely good, not disguised) · in-place file overwrite (violates atomic-save).

---

## content_scrubber.py

**What it is:** the Python behind `/scrub`. Verified by running it — it crashes (`KeyError: 'ai_phrases_replaced'`).

**The big finding:** it secretly rewrites prose the doc never admits — blind regex `leverage`→`use`, `utilize`→`use`, `delve into`→`explore`, deleting "In today's digital landscape" etc. across the visible text. The doc swore it "never modifies visible content or meaning" — false. Blind swapping breaks things ("leverage" can be a real noun). It's the FOURTH copy of the AI-phrase list, and the hidden third job is the buggy one — cutting it fixes the crash for free.

**The good part is better than the doc said:** invisible-character removal is 15 named characters PLUS a catch-all that strips every Unicode format-control character (removes junk nobody listed).

**Em-dash code:** ~65 lines of heuristics, but almost every ambiguous case falls through to the comma default. In practice mostly "→ comma". Fine for the no-em-dash rule; not as clever as it looks.

**Kept:** invisible-character removal (15 + Cf catch-all) · whitespace normalisation · em-dash replacement.

**Dropped:** the AI-phrase regex rewriter (breaks prose, fourth copy, and the crash lives here) · the KeyError bug (goes with the feature) · in-place overwrite (route through temp-file-then-rename).

---

## context/seo-guidelines.md

**What it is:** Castos's master SEO rules — really two documents stitched: an old-school top half (density, word floors, LSI, transition quotas) and a genuinely modern bottom half (answer-first, TL;DR, one-idea-per-section, FAQ).

**Verdict:** drop the whole file. Our own `seo-aeo-geo-checklist.md` is the superior replacement — its good half we already have phrased better, its bad half is dead. Nothing to carry. Use our checklist as THE gate.

**The scoring contradiction (now resolved into an open decision):** our own checklist ends with "Overall score ≥ 80 (§7)". Reading §7 (verified) showed it's the gameable kind — five judgment dimensions with fixed weights and no rubric. See Part 7 / Station 7 for the recommendation to replace it with the checklist itself.

---
---

# APPENDIX D — The embedded format playbooks (full hand-to-a-writer versions)

This is the complete per-archetype playbook the format router (Station 1, job 0) loads. Part 3.3 is the distilled overlay that plugs into the pipeline; this appendix is the full reference behind it — the section skeleton, the writing rules, and the checkable rules for each of the nine archetypes. Everything here is grounded in the format research; the numbers are real (peer-reviewed figures outrank single-vendor claims, and practitioner-only magnitudes are directional, not fact). Read the one archetype the router picked; the common spine (Part 1) applies on top of it regardless.

Each archetype below uses the same five heads, mapped to the station that consumes it:
- **When to use / not** → the router (3.1) + Gate 0
- **Section skeleton** → Station 1 (PLAN)
- **Per-unit writing craft** → Station 2 (WRITE)
- **Checkable rules + schema** → Station 4 (MEASURE) + Station 7 (GATE)
- **Hard rule + pitfalls** → the gate's blockers · **Parked** → carried by the common spine or another lane

---

## answer-bait-definitional ("what is X" / "how does X work")

**When to use:** definitional explainer · "what is X" · "how does X work" · FAQ page · interactive explainer. A concept to define, where the job is not to keep the reader but to *be the source that gets quoted* — in Google's featured snippet, an AI Overview, and inside a ChatGPT / Perplexity / Claude answer. NOT a task (→ how-to) or a set (→ listicle). The two names for this modern job: **AEO** (structuring content so an engine can use it as a direct answer) and **GEO** (optimizing so your content appears as a *cited source* inside AI answers).

**Section skeleton (Station 1), top to bottom:**
1. **H1** = the exact user question, under ~70 characters, mirroring the query. No brand spin, no cleverness (`What is a skills assessment?`).
2. **The liftable answer block** — a 40-60 word self-contained definition immediately under the H1 (or a TL;DR box under ~100 words), and in any case the main-topic answer sits **inside the first 150 words of the page** (a majority of AI-Overview citations come from that opening window). Write it as a **plain paragraph, never a coloured callout box or blockquote** — engines pull plain paragraphs more reliably. Nothing goes above it — no intro, no image, no "in today's landscape." This is the snippet-and-citation target.
3. **Question-based H2/H3 sections in depth order**, following the inverted pyramid: definition → how it works → types/components → why it matters → how-to/examples → related questions. Each heading is phrased as the user asks it and each section opens answer-first.
4. **Real lists/tables** where the content is a set or a comparison — native `<ol>/<ul>/<table>`, never styled `<div>`s.
5. **A closing summary / key-takeaways block** that repeats the key numbers + one bolded key-takeaway line, plus a short conclusion, then the single CTA.
6. **A related-questions / FAQ block (LAST)** — 3-6 real "People Also Ask"-style questions, each answered ≤40 words (the AEO cap), answer-first.
- Add a new descriptive subhead roughly every 200-300 words. Headings must be descriptive, carry the key terms, and stand alone (`CRM Pricing Overview: What to Expect`, not `Overview`; `Step 1: Create your HubSpot account`, not `The first step`).

**Per-unit writing craft (Station 2):**
- Write the answer block as a self-contained **40-60 words (~45 the bullseye)**. Under 30 reads skeletal; over 70-80 gets truncated. Build it in the four-part shape: **direct answer** (term restated + defined) → **defining context** (category + scope) → **qualifier** (the precision detail) → **outcome** (what it is for). Open with the term and a decisive verb (is / helps / improves / reduces / measures); kill wind-ups and hedges.
- **Self-containment (the standout rule):** every section opener must fully parse with its heading and surrounding text removed. No "this" / "as mentioned above" — engines lift one chunk alone, so restate the full claim inside each section.
- Add at least one **original statistic** (the biggest citation lever, up to ~+41%, Princeton) formatted as number + claim + source in one sentence, AND at least one **direct quote from a named source** (~+28%, Princeton). Cite credible sources on the page. Keyword stuffing and meta-tag manipulation measurably *lower* AI citation — do neither.
- Keep prose plain, fluent, declarative, authoritative; body paragraphs 2-4 sentences, one idea each; FAQ answers ≤40 words (the AEO cap). Prefer specific, only-you-can-source detail over generic phrasing. Whole-page length is not fixed — the discipline is density and structure, not total length.

**Checkable rules + schema (Station 4/7):**
- Match snippet format to the query: **paragraph** (~70% of snippets; the default for "what is / how"), **list** for steps/types, **table** for comparisons/specs. The page must realistically rank top 10 — Google pulls featured snippets from the top 10 **99.58%** of the time; snippet work is not a shortcut past ranking.
- Real semantic HTML with clean `H2 > H3 > H4` nesting (a reported ~2.8x citation lift over unstructured). Answer in raw, server-rendered HTML — not behind JavaScript, not in an image.
- Schema: `DefinedTerm` + `Article` (+ `Organization` + `Person/Author` for E-E-A-T). `DefinedTerm` fields: `name`, `description`, `termCode` (= URL slug), `inDefinedTermSet`, `url`. Keep `description` **byte-identical** to the on-page one-sentence definition. `FAQPage` JSON-LD is optional and machine-readability only — FAQ + HowTo rich results are deprecated (FAQ stopped rendering entirely May 7 2026; HowTo dropped Sept 2023). Never build the page around, or promise, a rich result. Every schema value mirrors visible content exactly.
- Visible author bio/credentials + a visible publish/updated date; set a refresh cadence (quarterly for competitive terms). Crawlability: `robots.txt` must not block GPTBot/Bingbot/Google; index in Bing + submit a Bing sitemap (ChatGPT search runs on Bing's index).

**Hard rule + pitfalls:** answer-first in a self-contained chunk; no keyword stuffing (measurably lowers citation). Pitfalls: burying the answer · too generic to cite (no number/source/specific) · non-self-contained sentences · fake structure · chasing FAQ rich results · answers over ~70-80 words · stale pages · answer hidden behind JS or in an image · skipping Bing · reprioritizing on vendor hype (follow the Princeton levers: stats > quotes > cited sources).

*Parked (common spine / other lanes):* answer-first / one-idea / cite-stats / question-headings / FAQ / no-stuffing = the checklist · FAQ-HowTo-deprecation + Bing-index + crawler-access = the cross-format corrections (3.2) · off-site entity signals (Wikidata, directories, roundup mentions) = off-page · refresh cadence = content-refresh.

---

## case-study (customer results story) — DATA-GATED

**When to use:** customer results story · testimonials — ONLY when a real named customer, real numbers, and a verbatim quote are collected AND approved in writing. (Currently blocked pipeline-wide: `stories.md` is unapproved.) A case study is a *proof asset, not a search asset*: the reader is a prospect mid-evaluation asking "will this work for someone like me?", so the whole job is to be believable, not just impressive.

**⛔ The hard constraint (read before anything else):** use ONLY real, approved customer data. No invented customer, no invented quote, no invented or rounded-up metric, no composite "typical client." Every number, name, logo, and quote traces to an actual Testlify customer and is cleared for publication. If the real inputs don't exist, go collect and get them approved — never fabricate. The governing gate for every claim: **"Would the named customer recognise this and nod?"** If no, cut it. This matches writing-integrity's hard ban.

**Section skeleton (Station 1) — Testlify's real customer-story template (verified from testlify.com/customer-success-stories/; this template SUPERSEDES any generic case-study structure).** Follow it exactly, top to bottom:
1. **Eyebrow label** — the literal words **"Customer story"** above the headline.
2. **H1 — a result-first headline** in the fixed shape: **"How <Company> <achieved result> with Testlify"**, where `<achieved result>` is the single most impressive verified outcome stated as a delta (e.g. "cut time-to-hire by 67%", "increased L&D participation by 82%"). Not the customer's name as the H1 — the result.
3. **A metadata block** — four labelled fields: **Company size · Headquarters · Industries · Use-case.**
4. **Three short blocks (2-3 sentences each):**
   - **Challenge** — the specific "before" pain.
   - **Solution** — what Testlify did / how it was rolled out (not a feature list).
   - **Outcome** — the measured "after" state.
5. **Three big headline stat cards** — each a single number + a one-line label (e.g. "67% faster time-to-hire", "82% increase in L&D participation", "4x recruiter efficiency"). These are the scannable proof.
6. **A "Details" section** — narrative H2s that tell the full story in order: **the situation/problem → the solution rollout → the measured results**, with at least one **cited stat woven into the narrative**.
- **The spine is still Challenge → Solution → Outcome**, and it is **result-first for organic visitors** (the chronological sales order is wrong for someone who doesn't trust you yet). The three cards + the headline let a reader get the whole story in under a minute; the Details section is the believable long form underneath.

**Per-unit writing craft (Station 2):**
- Pair every metric with **baseline + timeframe + why it mattered** ("from X to Y in 6 months") — without that quantitative context, claims "appear hollow." Lead with the business number a buyer cares about (pipeline/revenue); use any flashy secondary/vanity metric only as SUPPORT. Prefer a legible, well-explained figure over a lonely giant percentage (avoid "data deference").
- **Show the workings** (attribution): document how you caused the result — screenshots, timeline, quotes explaining why it mattered — so it doesn't read as coincidence.
- **Narrative:** borrow fiction's shape (setup → tension → resolution) but populate it only with real facts. Make the customer the hero (named and faced, never "a leading enterprise"); don't erase yourself (position as a peer). Include the real obstacle you hit (the pratfall effect makes a competent party more trusted). Reflect the actual decisions taken, never a tidy post-hoc rationale. Editorialize to the 2-3 most interesting moments — don't transcribe chronologically. A verbatim named-decision-maker quote roughly every 2-3 paragraphs. Voice: business journalism, not brochure; plain and jargon-light. Studies with all five core elements (measurable title, customer context, solution path, concrete metrics, verbatim decision-maker quote) converted 37% higher.

**Length + tone:** ~800-1,000 words (B2B average ~965); let the story set length within that band, don't pad, don't bury the hero number. The scannable summary (hero number + before/after) must read in under a minute.

**Checkable rules + schema (Station 4/7):** the template blocks are all present and in order — eyebrow "Customer story" · result-first H1 in the "How <Company> <result> with Testlify" shape · the 4-field metadata block (Company size · Headquarters · Industries · Use-case) · the three Challenge/Solution/Outcome blocks · exactly three headline stat cards (number + label) · a Details section with ≥1 cited stat. Every metric has a baseline + timeframe; who-you-are is established in the first two paragraphs. `Article` schema with the `author` property emphasised (credentials). Know the limit: schema is not a direct ranking factor and FAQ/AEO schema is a supporting layer, not a lever (an Ahrefs study of 1,885 pages found no significant AI-citation lift from schema alone). If you also want search traffic, target the buyer's research query ("Industry + Challenge + Outcome"), not the client's name, and place it in H1, first 100 words, ≥1 H2, slug, meta.

**Hard rule + pitfalls:** the fabrication rule bites hardest — the per-claim test is *"would the named customer recognise this and nod?"*; no invented customer, quote, rounded-up metric, or composite client. Pitfalls: vague results / no real numbers · data deference (context-free percentages) · all brag no story · unverifiable claims · result with no attribution · erasing yourself · post-hoc narrative · sales-asset structure when you wanted search · skipping the approval bottleneck.

*Parked:* customer sign-off collection = the Gate 0 data-collection queue (upstream input) · SEO keyword targeting = research · length ~800-1,000w = length-is-an-output.

---

## comparison-rankings ("best X" · "X vs Y" · "alternatives to X")

**When to use:** rankings · best-tools · comparison · alternatives · branded index. A reader in decision mode (commercial-investigation / BOFU intent) choosing between named options. NOT a single concept (→ answer-bait).

**House rule (never break):** we NEVER cite or link a direct assessment-platform competitor as a source, and never rank a competitor's page as a reference. We DO still name and fairly assess alternative tools inside our own pages when the page's job needs it — "who we cite" ≠ "what the page covers." Any "alternative to [X]" anchor points at a neutral job-to-be-done or category, never a named direct rival.

**The one rule that governs everything:** every claim must point to proof, and the page must be fair enough that a skeptic could not call it rigged. If you can't point to a page (pricing, docs, a test result) that proves a claim, don't write it as a fact.

**Section skeleton (Station 1)** — order so the verdict comes fast, then drill down:
1. **Intro / BLUF verdict (≤200 words)** — state the winner / "best for most" pick in the first paragraph, plus who the page is for; target keyword in the opening line. For a "which is better" comparison, give the top-level answer in **≤60 words** (the snippet play).
2. **Table of contents.**
3. **Criteria / methodology** — dimensions scored, whether you tested hands-on, how many options considered, last-updated; publish the **inclusion criteria** (what qualifies for the list).
4. **The at-a-glance comparison/specs table, shown immediately** — a lean fixed set of ~5 columns: **Category/Job · Name · one-line Description · a proof Metric · (optional) a few capability Tags.** A real HTML `<table>`, not a feature-matrix sprawl. Serves the two intents at once (which options exist + the specs that drive the decision).
5. **Per-option deep dives** — one identical block per tool (below).
6. **"Best for X" constraint-based verdicts** ("For a 5-person team…", "For B2B SaaS…").
7. **End-of-list extras below the items** — buying guide, definitions, research data — then FAQ.
8. **Close / how to choose** ("pick A if…, pick B if…").
- Push company/product background FAR down; keep only a one-line positioner up top. Number the item headings; carry ≥8 items where the category honestly supports it (list rich result), never padding. **"A vs B" fixed sequence:** what is A → what is B → how different → how similar → head-to-head → pros/cons A → pros/cons B → verdict split by use case → FAQ.

**Per-option block (identical for every entry):** name + one-line tagline → overview (what it is, who for) → 4-5 key features → pricing (seat/usage model explicit) → standout strength → one honest weakness → bottom-line verdict + who it suits (+ "why we selected it" + a link to the in-depth review). Write it foundation-first: work out strengths/weaknesses/fit before the tagline.

**Per-unit writing craft — the fairness mechanics (the spine that separates a review from an ad):**
- Replace every adjective with a fact: "$12/mo for 5 users", not "affordable"; "24-48h email", not "great support"; "OAuth, 3 steps, no code", not "easy setup."
- Name at least one honest weakness for EVERY option, including the favoured pick.
- Concede at least one place a rival genuinely wins, and route that reader to them. Never pigeonhole a competitor into a niche it wasn't built for.
- Show evidence of real use (screenshots / original media, aim 7+ visuals); state how many you tested and how you scored them. Visible author bio + "last updated" date.
- Voice: a practitioner reporting test results, not a salesperson; state the verdict, then the evidence; use "you"; vary sentence length.

**Checkable rules + schema (Station 4/7):**
- Real HTML table, not an image · unknown cell left BLANK, not guessed · every metric live or dated-and-sourced (no hand-typed number without a date) · a one-line "not fully complete/up to date" disclaimer · stale/retired option flagged with a date, never silently deleted · any featured/paid placement visibly marked, never smuggled into the ranking.
- Group by the buyer's real decision axis (job/use-case/role/team size), not alphabetical-only; rank only where the order is defensible, else group + sort neutrally.
- Schema: `Review`/`Rating` (Product · SoftwareApplication · Course, etc.) + `Pros-and-Cons` markup **only where real on the page**. Do NOT add `FAQPage` markup expecting a rich result — deprecated for typical SaaS/marketing sites; keep the FAQ section for readers + AI lift only.
- Every major claim points to a proof page (pricing, docs, changelog, status, compliance). Length driven by completeness (~2,000-2,500 words as a centre of gravity, not a target); cut padding.

**Hard rule + pitfalls:** never cite/rank a direct assessment competitor; an "alternative to X" anchor points at a neutral job/category, never a named rival; no self-#1 without a stated, provable basis. Pitfalls: no methodology / no real testing · unfair bias / pigeonholing · self-ranking with no basis · adjective cells · carbon-copy list · no author / no date · padding to a word count · guessed/stale cells · faked global ranking.

*Parked:* author bio/last-updated = E-E-A-T + author box · "is it worth writing"/persona/keyword-difficulty = research · visuals/affiliate-disclosure/outreach = assets + off-page · cluster interlinking (listicle ↔ single-product reviews ↔ A-vs-B posts) = linker.

---

## data-benchmark-report (data study · benchmark · statistics roundup)

**When to use:** data report / original research · survey · salary benchmark · statistics roundup · grader-results. Numbers to present for citation + links. (Gate 0: statistics roundup = WRITE, curates public stats; original research = DATA-GATED.) Two sub-types share one spine: *original research* (you collected/analysed the data — highest link value) and *statistics roundup* (you curate and freshen others' stats — lower novelty, wins on being current).

**The one rule that governs everything:** every finding must be liftable in one sentence (number + subject + source) AND traceable to a disclosed method. Quotability and credibility are the two non-negotiables. The mechanism is **information gain** — a number nobody had; if it only confirms the obvious, kill it.

**Section skeleton (Station 1):**
1. **Headline** — leads with the single biggest number or the dataset scale ("We Analyzed 912 Million Blog Posts").
2. **Intro (2-4 sentences)** — states N / dataset size immediately: what you studied, how big, why it matters.
3. **A numbered key-findings menu up top, before any detail** — the citation menu (Backlinko uses 11); the most-linked part of the page. A journalist or AI should never scroll to lift a stat.
4. **[RIGOR] Methodology** — findable, never buried: a short 2-4 sentence in-page block plus a full appendix/PDF at the bottom.
5. **8-15 distinct findings, one section each** — no two overlap; each carries a novel number. Ten strong beats twenty overlapping.
6. **Takeaways / conclusion** and **citation aids** (embeddable chart, "cite this study" line).
- **Publish as a free web page, never a gated PDF** — a gate kills the citation. Front-load the crunchiest bite-sized stats (industry size, revenue, headcount, % growth) toward the top — the crunchy stat becomes the citing site's anchor text.

**Per-unit writing craft (Station 2), per finding:**
- **Heading states the finding IN WORDS; the exact number lands one line below** (heading = the conclusion, not the topic — Pew: *"A majority of Americans say they use YouTube and Facebook…"* → *"roughly seven-in-ten Americans…"*).
- **One chart owns one idea** (no combined mega-charts); default to bar/line/scatter.
- **Name the relationship BEFORE picking the chart** (FT Visual Vocabulary): ranking (→ ordered bar/lollipop, never a pie) · magnitude (→ column/paired bar) · change-over-time (→ line/slope) · deviation, i.e. "vs the average / last year / a competitor" (→ **diverging bar**, not a plain column — the one most reports get wrong) · distribution (→ histogram/boxplot) · correlation (→ scatter).
- **Chart title = a full takeaway sentence**, not a neutral label ("Age gaps in Snapchat, Instagram use are particularly wide", not "Platform usage by age"). Declutter: strip gridlines, borders, extra labels, legends; use colour to point at the one number.
- **~200-400 words of context** per finding, then a boxed, quotable "key takeaway" callout. Write the liftable one-sentence stat deliberately: number + subject + scope, no dangling pronoun, lifts cleanly with zero context. Make every chart/table embeddable AND mobile-legible. Interpret, don't dump — but never bend the number. Tone: neutral, rigorous; the data carries the emphasis, not adjectives.

**Checkable rules + schema (Station 4/7):**
- **[RIGOR] methodology disclosure** — N · data source · collection dates/window · exactly what was measured and how (metric definition, filters, exclusions) · limitations. No method = dismissed as marketing; non-negotiable, the practitioner tactics never override it.
- Schema: `Article` (+ `BreadcrumbList`) baseline, `Dataset` on the proprietary research (populate `author`, `datePublished`, `dateModified`, `description`, `sameAs`). Honest caveat: schema *enables* extraction but does not manufacture authority.
- Target "[topic] statistics/stats/facts/figures" keywords (the passive-citation intent). Adding statistics is one of the highest-lift GEO moves (Princeton ~+30-40% AI visibility; "statistics addition" ~+32%) — a data report is GEO-native.

**Hard rule + pitfalls:** no methodology = it reads as marketing; never gate it. Pitfalls: thin data (a 40-person survey dressed as a study) · hidden/missing method · no novel finding · unquotable presentation (stat buried, needs prior context, chart with a neutral title) · gating · cluttered charts · a stats-page left to rot (being current is its entire moat).

*Parked:* promotion (reverse outreach, ping-cited-firms, "tweet this", PR/newsroom syndication, national-data-map visuals) = off-page · data gathering = upstream asset-building · journalist-keyword targeting = research · refresh cadence = content-refresh.

---

## glossary (hub + term entries)

**When to use:** glossary / dictionary — many short term-definition entries under one hub. Shares its definition-writing rules with answer-bait; the NEW part is the hub-and-spoke structure. Each term is treated as an **entity** (a singular, well-defined thing), not just a keyword — so terms are sourced from Wikipedia + Google's knowledge graph, not only keyword tools.

**Section skeleton (Station 1):**
- **The hub** — one A-Z index page linking to EVERY entry (the crawl backbone); numbers/symbols first (301 redirect, 404, 500…) then A-Z; optional category filters.
- **The entry (spoke), in fixed order:** H1 = the exact term (the only H1) → the concise definition FIRST (before any heading) → "Why it matters" (the how/why, not a restated definition) → ≥1 concrete real-world example (ideally with a number) → related-terms + internal links. Flag era/status on dated terms.
- **Interlinking:** 3-5 sideways links to related entries per entry; hub→entry and entry→hub reciprocity; feed the glossary from the rest of the site (link every in-content mention of a defined term to its entry). Point interlinks at the knowledge-panel related-entity set.

**Per-unit writing craft (Station 2):**
- **First line is the definition**, in the extractable **"[Term] is [definition]"** form. Keep it **40-60 words**, self-contained, readable as plain text (not buried in a styled callout/table). Over 60 gets truncated; if it needs the next sentence, rewrite it. Write the opening for a total newbie in 1-3 plain sentences.
- **Expand any acronym** on first use (title AND first line), then define ("CPA — cost per action").
- **Split multiple meanings explicitly** inside the one entry — name each sense (apple = fruit/company; "citations" = local-directory listing vs academic reference), never define one and blend the rest.
- Every H2 a self-describing question phrase ("Why does a pillar page matter?"), never bare labels ("Overview", "Benefits"). Target **600-1,000 words** where the term warrants depth; break long entries into **200-400 word** independently citable sections. Don't pad. Tone: precise, neutral, dictionary register — no promotional language in the definition (it kills the snippet). Keep terminology consistent, preserve real product/tool capitalization, attribute hard claims (standard, study, dataset).

**Checkable rules + schema (Station 4/7):**
- `DefinedTerm` JSON-LD per entry (`name`, `description`, `termCode` = the URL slug, `inDefinedTermSet`, `url`) + `DefinedTermSet` on the hub (`hasDefinedTerm`). `inDefinedTermSet` and `hasDefinedTerm` are **inverses** — one direction per page, never both. Keep the JSON-LD `description` byte-identical to the on-page one-sentence definition. Pair with `Article` (still supported); do NOT use `FAQPage`/`HowTo` for a rich result (deprecated). The 40-60w answer-first block is what triggers a paragraph featured snippet. Verify each self-contained section stands alone as a citable chunk; a statistic every 150-200 words with source attribution supports GEO.

**Hard rule + pitfalls:** no thin / near-duplicate entries (the glossary failure mode). Pitfalls: thin/duplicate entries (template pages differing only by the swapped term) · doorway pages (many keyword-variant pages funnelling to one product page) · generic templated output (if generated, a rich prompt + RAG knowledge base must do real work) · buried answer · definition over-length · isolated (no internal links — interlinking IS the topical-authority strategy) · promotional definition · set-and-forget.

*Parked:* 40-60w definition / plain-text / question-H2s / one-idea = answer-bait + checklist · term-as-entity sourcing = research · programmatic bulk generation (variables + outline + prompt + RAG) = a separate pipeline · tooltip auto-linking plugin = site/UI layer · refresh = content-refresh.

---

## how-to-guide / pillar

**When to use:** how-to guide · pillar guide · role skills guide. Two jobs under one label: a **how-to** (the reader knows the goal, needs the steps) OR a **pillar** (orient + route to cluster sub-articles). Don't blur the two modes. NOT "what is X" (→ answer-bait) or "best X" (→ comparison).

**The one rule that governs everything:** practical usability beats completeness — cover exactly what the reader needs to finish the task or orient on the topic, then stop. Length is an output of that, never a target.

**Section skeleton (Station 1) — the FIXED HOUSE ORDER, top to bottom (Intro → TL;DR → body → Key takeaways/Conclusion → CTA → FAQ):**
1. **H1 / Title** = the exact task/topic, target keyword front-loaded, one clear specific promise.
2. **Intro** using APP (Agree, Promise, Preview) or PAS (Problem, Agitate, Solve) — hook PLUS a direct answer to the core question, no warm-up, no "in today's…". Primary keyword in the first 100 words; the main-topic answer inside the first 150 words.
3. **TL;DR block** — 2-3 lines that answer the core question up front (AEO win), placed directly under the intro.
4. **Table of contents** (sticky/persistent for long pillars).
5. **A separate "what is X / why it matters" definition section** — one concept, never mixed into the steps; opened with a 40-60 word direct answer (its own snippet/AI-Overview bait).
6. **The steps / body, in order (H2 & H3 as per the keyword)** — procedural order for a sequence, importance/comprehension order for concept sections. (Pillar only: sub-topic sections that link out to cluster articles.)
7. **Key takeaways / Conclusion** — 3-5 screenshot-ready bullets a busy reader can walk away with (this also feeds AEO), then a one-line takeaway + next resources, not a long motivational summary.
8. **One primary CTA** — exactly one, matched to the reader's stage (an awareness-stage guide gets a soft next-read or free resource, not a hard "book a demo"). Placed AFTER the key takeaways and BEFORE the FAQ.
9. **FAQ** — the LAST block on the page. Real People Also Ask questions; each answer **≤40 words**, answer-first, marked up with FAQPage schema (visible Q&A only).
- Derive the actual headings from the SERP + PAA (sub-topics appearing across 3-4 competitors), never from memory. On a pillar, headers + bullets let a visitor self-qualify and jump to the right cluster; keep the pillar **broad-with-clarity** — depth lives in the cluster articles, not crammed into the hub.

**Per-unit writing craft (Station 2) — each step:**
- Start with an **imperative verb**; **one action only**; **state the goal before the action**; **state the location before the action**; **state the result right after** (same paragraph). Flag optional steps with "Optional:"; combine only tiny sequential UI actions (`File > New > Document`). Be **prescriptive** — recommend one way, the shortest path, never a menu of five methods. Complete sentences, second person, active voice; no "please"; no "above/below" directional language.
- Prose paragraphs 2-4 sentences; subheadings generously; a handful of bucket brigades across a long post. Include original data or a usable artifact (template/checklist/tool) — the thing that makes it link-worthy.

**Blog-level craft that every standard blog / how-to must carry (Station 2):**
- **One named-source quote (required).** Add at least one quotation from a named source. Either a **real, verifiable, cited industry leader or body** (SHRM, WEF, a named study author — never fabricated), OR a quote attributed to **Abhishek or Namrata** (Testlify leadership house voices), which MAY be composed to fit the topic (ghostwritten exec voice; on-message; no unverifiable first-party metric). See Part 1 Rule 4's quote rule.
- **One evergreen authoritative external link (required).** Link out to at least one durable institutional source — e.g. **WHO, SHRM, WEF (World Economic Forum)** — a reference that stays valid, not a dated news item. This sits inside the ≥2-external-links budget and never points at a direct assessment competitor.
- **One original example or data point** the top three results don't have (the differentiator / information-gain move); prefer a real Testlify number, put it up front and attribute it. **Stats 2024 or newer** (Part 1's recency rule).

**Length + tone:** no single correct number. Pillar ~2,500-3,500 words (HubSpot) up to a practitioner 3,000-5,000+; cluster/supporting articles ~400-600 words each. Length is an *output* of covering the topic for the searcher, never a target.

**Checkable rules + schema (Station 4/7):**
- **Answer-first per section:** frame each H2/H3 as the reader's/AI's question, open with a direct 40-60 word answer, inverted-pyramid. Each section a standalone citable unit, ~200-400 words, one concept only (never mix a definition with how-to steps). Numbered lists for processes, bulleted for features, tables for side-by-side. Citation density: a statistic roughly every 150-200 words with an inline authoritative link.
- Schema — only currently-valid types: `Article`/`BlogPosting` for the page, `BreadcrumbList` for hierarchy, `FAQPage` for the FAQ block. Treat `HowTo` schema as machine-readability/AEO support, NOT a guaranteed visual rich result (Google scaled back visible HowTo + FAQ rich results 2023-2024). Validate every schema in the Rich Results Test.
- **Pillar-cluster interlinking, both ways:** pillar → every cluster from the relevant section; every cluster → back to the pillar (mandatory); sideways cluster↔cluster only where relevant. Descriptive keyword anchors. Broad head term on the pillar, long-tail on the clusters (cannibalization check). Keep the pillar evergreen; put dated/refreshable content in the clusters.

**Hard rule + pitfalls:** don't blur how-to and pillar; don't bury the task under theory. Pitfalls: turning a how-to into an essay · offering a menu instead of a recommendation · chasing a word count · wall-of-text sections AI can't chunk · definition + steps mashed together · a pillar that doesn't link out (or clusters that don't link back) · going deep on every sub-area in the hub · topical incoherence · headings written from memory · unvalidated schema · justifying the cluster by dwell-time/bounce folk-metrics.

*Parked (not write-phase):* pillar↔cluster interlinking + cannibalization (site-level) · topic selection / "maps to what you sell" (research) · promotion / earn-links (backlink machine).

---

## interactive-tool (calculator · quiz · assessment · grader · generator) — WRITE+BUILD

**When to use:** ONLY when a competitor genuinely ranks a tool (post over-tooling fix); otherwise route the idea to an article. The write phase owns only the WORDS around the tool — the tool build itself is a separate pipeline. Decide the ONE primary job first: **link-magnet (ungated)** vs **lead-gen (gated detailed result)** — the gating choice cascades through the whole build. Sub-types are not interchangeable: calculator/converter (wins on accuracy + specificity), assessment/grader (wins on the emotional pull of a score), quiz/personality test (wins on a shareable, nameable identity).

**The one rule that governs everything:** the tool must do a real job at the lowest possible friction AND be wrapped in enough crawlable text to rank — both halves.

**The SEO wrapper skeleton the write phase owns (Station 1), below the tool:**
- Tool visible above the fold, in crawlable HTML (never an un-crawlable iframe or orphaned subdomain).
- **150-200w intro** (what it does, who for) → H2 **"How to use"** (200-300w, each input) → H2 **"Why [topic] matters"** (400-500w, with data) → H2 **"Methodology"** (how the numbers are calculated — this is what makes the tool citable) → H2 **FAQ** (6-8 semantic/long-tail questions) → related resources with internal links.
- Primary keyword in the H1, first paragraph, title tag, and meta description; **one tool = one page = one keyword.**

**Per-unit writing craft (Station 2) — the words, not the mechanics:**
- **Result-interpretation copy** — tell the user what their score MEANS and the next step ("scores 62/100 — biggest gap is page speed, here's why"), jargon-light and actionable. This is where a calculator becomes advice. Button copy states the outcome ("Get your score", "Calculate take-home pay"), never a bare "Submit." The promise (above the tool) leads with the payoff in the visitor's language.

**Checkable rules + schema (Station 4/7):** `WebApplication` schema (`name`, `description`, `url`, `applicationCategory`, `operatingSystem`); FAQ schema on the FAQ block; HowTo schema if the tool takes sequential inputs. The wrapper text (not the tool) is the surface that matches the query, so it must actually be written. Validate a winnable niche keyword before building (KD ≤ 30 at a low DR, a SERP of thin single-purpose tool pages). Why tool pages rank despite thin text: a working tool fulfils "do" intent directly and is far harder for AI Overviews to summarise out of existence — the format's durable moat.

**Hard rule + pitfalls:** don't gate a link-magnet (a gate is the single thing that stops a blogger linking); the tool's build (input flow / scoring / embed) is NOT write-phase. Pitfalls: too much friction · gating too early · no SEO wrapper · no shareable result · head-term greed · un-crawlable delivery · placeholder-as-label · a gimmick with no search demand.

*Parked (tool-build pipeline — recorded here for when we build the tool generator, not write-phase):* input flow (one-small-ask-per-screen, single-choice auto-advance, single-column top-aligned labels, validate-late-then-live, keep-the-typed-value-on-error, stepped wizard + visible progress bar — 65% of quiz-starters finish once they begin; forms that follow the rules hit ~78% one-try success vs 42%) · score computation (compute the tier ONCE via a named expression, then pipe answers into personalised result text) · make the output personal + nameable + visual + show-the-working + share triggers · gate placement (questions → lead form → result; gate the *detailed* result, disqualify by fit, route to a pixel-tracked landing page you own, "useful but incomplete" result) · embed/distribution loop (ship embed code before launch, keyword-rich attribution anchor, paste embed in outreach email, target competitor-tool linkers) · launch like a product (rankings stabilise 60-120 days) · data-freshness re-pitch.

---

## listicle

**When to use:** "N best X" · interview-questions · tips · facts / statistics roundup · complete-list · expert roundup. A set of discrete items, each expanded enough to stand on its own. NOT a single-topic explainer. Listicles are the most-cited format in AI search (~21.9% of AI-Overview sources — the single largest format share).

**The one rule over everything:** every item must earn its number. If an item has no distinct value and exists only to hit a round/odd total, cut it. This beats every other rule, including the 8+ items target.

**Section skeleton (Station 1)** — the five-part shape: **Title** (count + payoff + keyword) → **one crisp intro** (2-4 sentences ONLY; if ranked/curated, state HOW you chose/tested — the trust line) → **(optional) jump-to/TOC** for lists over ~10 items → **the list body** (80%+ of the article) → **short close** (one takeaway, no re-listing). **Jump straight into the list: NO long educative/informational preamble before the items.** Every supporting block (definitions, buying guide, pros/cons, data) goes BELOW the list, never in front of it. The one exception is a product/buying-intent specs-comparison table, which sits directly above the items (still not prose preamble).
- **Pick the body skeleton by query intent:** *info-heavy* = plain list (H2/item, 2-3 paras) → justifying block after the list → FAQ · *imagery-heavy* = image + short text per item; serve the secondary intent · *product/buying-intent* = **specs/comparison table ABOVE the list**, then per-item detail, buying guide/data BELOW → FAQ. Whichever skeleton: **all supporting blocks go BELOW the list items, never as a preamble.**
- **Item count:** roughly match the top-ranking SERP (10-20 the common sweet spot); prefer fewer-but-deeper for B2B (7 well-researched beat 15 shallow; a tight 1,500-word 5-item post beats a padded 3,000-word 15-item one). 8+ items earns the expandable "More items…" snippet — but only if the topic honestly holds them. Odd numbers are a soft tie-breaker at most.

**Per-unit writing craft (Station 2) — the load-bearing part, one fixed template per item, never changing item to item:**
- **Descriptive heading (substance-first, short — the "master/apprentice" rule: "Mix in the butter", not the full step) → a one-sentence self-contained micro-summary (the first line, the sentence AI quotes verbatim) → 2-3 short paras of substance → one concrete proof** (number/example/screenshot/mini-list).
- **Strict parallel structure** across all items (same heading shape, depth, register, person) — the single biggest tell of a great listicle. For named tools/products, fix the line shape: `Name — one-line description.` (same separator + terminal period; description starts uppercase; describe the THING, not your article — never a marketing blurb or "in this list we…"). Canonical naming identically everywhere (`Node.js`, not `NodeJS`).
- **Scan each item's real source FIRST, then write** (gather facts before drafting, so nothing is invented). Curate, don't collect — only picks you'd personally recommend. **Ordering:** front-load the strongest; ranked = best-first with disclosed criteria; process = basic→advanced; facts = most surprising/citable first; complete-list = alphabetical/chronological; expert roundup = by FAME. Any AI-assisted draft gets a genuine human editing pass.

**Length + tone:** no universal word count — *basic/simple* (1-2 sentences/item, long simple lists) vs *detailed/expanded* (a few paras + a visual, short complex lists). Consistent register across every item. Specific over generic — don't rewrite the other page-1 listicles.

**Checkable rules + schema (Station 4/7):** `ItemList` schema honestly reflecting the page (use `HowTo` only for genuine step-by-step procedures) · list kept **flat, not nested** (nesting blocks snippet extraction) · **running numbers on the item H2s** (signals "this is a list" to Google) · short self-explanatory item headings so Google can lift them · FAQ section + FAQ schema placed after the list, sourced from People Also Ask.

**Hard rule + pitfalls:** every item must earn its number — cut filler even over the 8+ target. Pitfalls: padding to a number (the cardinal sin) · bare-name items (no why/how) · format drift · covert self-#1 in a "best" list (brands lost 29-49% organic visibility in 2026 for this; and in AI Overviews a self-listicle omits the brand from the recommendation 69% of the time — earning a spot in a *third-party* trusted list beats publishing a self-serving one) · artificial freshening (year-swap with no real update) · programmatic/AI-spun lists at scale · deep-nested list snippets · long intro burying the list · dead/deprecated picks in a live tools list · describing your article instead of the item.

*Parked:* self-#1 → omission = authority-honesty · refresh cadence + third-party-list outreach = content-refresh / off-page.

---

## template-resource (downloadable template · checklist · cheat sheet) — WRITE+ARTIFACT

**When to use:** templates · asset library · checklist / cheat sheet · toolkit · whitepaper/ebook. An article + a downloadable the write phase can produce as text. The value is the **artifact itself**; the prose exists only to make it findable (rank it) and usable (explain it).

**The one rule that governs everything:** the artifact must be genuinely reusable on its own (a real, ready-to-use thing a stranger can pick up and use in five minutes) AND visible before anyone commits.

**Section skeleton (Station 1) — the wrapper page, top to bottom:**
1. **The promise (H1 + one line)** — matches the "[thing] template/checklist" query verbatim and states the outcome.
2. **A real preview of the artifact ABOVE THE FOLD, before any ask** (annotated screenshot, scrollable embed, or public read-only view). No preview = no trust = no link.
3. **Get-it CTA** (download / copy / format buttons), right after the preview and repeated later.
4. **A "what you get" stat block** with hard numbers ("385 items across 11 categories") — the shareable completeness signal.
5. **A short, numbered "how to use it"** (Backlinko's 6-step model: download → open a draft → pick one keyword → apply → publish → submit to GSC) — turns the file into a result.
6. **The explainer wrapper** — explains every field/section in the artifact's own order, states why it exists, shows ≥1 filled example; sized to complexity. Bridge internally to the deep guide + related product.

**Per-unit writing craft (Station 2) — the artifact itself, when it's a checklist:**
- Each item = **checkbox + imperative action title + priority badge + one-sentence why/how** on ONE line. The title is an imperative verb phrase naming one testable action ("Declare UTF-8 encoding", never a topic noun like "Encoding"); the rationale/how sits in the colon-clause after the badge. Concrete/quantified ("load time under 3s", "CLS below 0.1"), never vague.
- Tag EVERY item with a priority (Critical / High / Medium / Low); **define the priority scale ONCE up top** (Critical = site-breaking/security; High = major UX/SEO impact; Medium = best practice; Low = situational). Group items into named categories by the reader's workflow, print an item count per group; add a clickable TOC + back-to-top. Keep the tickable line shallow, layer the deep how-to/fix behind a link. Show ≥1 filled example row. State the artifact TYPE explicitly (tick-through checklist vs guide/cheat-sheet vs fill-in template). Tone: practical, imperative, second person, active voice, no throat-clearing.

**Length + tone:** the wrapper scales with complexity — ~800 words simple ungated · ~2,000-2,500 gated single · 3k-10k template hub. Write the *least* wrapper that fully explains the artifact and covers the query.

**Checkable rules + schema (Station 4/7):** the asset preview must be above the fold; the file/preview stays crawlable (ungated or hybrid) so the artifact itself can rank and be AI-cited. Delivery chosen by type: "Make a copy" (Google Doc/Sheet), direct download (Word/PDF/XLSX, multi-format), or on-page interactive embed — offer multiple formats, no lock-in. HowTo/step JSON-LD on procedural checklists (the only format Google recommends) + FAQ schema — **caveat: the HowTo visual rich result was deprecated in 2023**, the markup still aids AEO/GEO comprehension; don't add schema for a rich result that no longer exists. Visible "last updated" / maintenance signal.

**Hard rule + pitfalls:** default ungated (gated content is invisible to Google AND to ChatGPT/Perplexity/Gemini/Claude); gate ONLY a heavier "enhanced" version and always keep an ungated crawlable companion (hybrid). The download file itself = build/publish, not write-phase. Pitfalls: no preview · gating too hard · no instructions · thin wrapper (item titles only) · vague items · no triage (untagged wall) · format lock-in · no maintenance · over-writing.

*Parked:* delivery (Make-a-copy / download / multi-format) = build/publish · resource-page outreach + dead-link replacement = off-page · maintenance = content-refresh · topic/query selection = research.

---

## (no overlay) News · Opinion · Editorial · Trends · Frameworks

**When to use:** news · opinion / editorial · trends / predictions · framework / methodology · other/editorial. No dedicated playbook — runs on the common spine (Part 1) alone. **Note:** for news, freshness matters more than depth — flag timeliness at Station 1.

---
---

**One line to remember:** the gate sorts every idea before money is spent (write it, build it, collect data first, or route it elsewhere); research hands the writable ones over as a menu, a rulebook, and a build spec; the write phase routes the format, freezes a plan (sections, cards by id, FAQ, orphans, band), writes to it section by section under the format's overlay, lets code prove every promise was kept, lets the AI judge only what code can't, edits for craft then strips AI tells, and ships nothing until the one checklist passes — with a human catching whatever fails three times, and stats/stories staying out of bounds until confirmed.
