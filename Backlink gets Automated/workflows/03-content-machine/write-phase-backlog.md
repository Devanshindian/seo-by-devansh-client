---
type: backlog + design notes for the WRITE / research phase (Layer 03)
purpose: durable home for the changes Devansh wants, so they survive file cleanups. Capture first, implement in order.
status: captured 2026-07-22 — awaiting build
---

# Write-phase backlog (the things still to build)

Everything below is in Devansh's words, simplified to pointers, each with a proposed approach. Nothing here is
built yet unless marked DONE.

---

## 📌 QUICK REFERENCE — what's parked, and what the client must be told (both stored HERE, in this file)

### A. Parked for LATER (need the writer/publish step, which isn't built yet)
- **Content-database feedback loop** — after an article is published, add it back into `content-database.csv` +
  re-embed it, so future reuse/cannibalisation checks see it and we never rebuild it. (details in §4)
- **Format router** — connect each idea's `Format` to its matching playbook (the 9 `formats/*/ACTIONABLE-CHECKLIST.md`)
  so a listicle is written like a listicle. (details in §5)
- **Precise cannibalisation at PUBLISH time** — re-check the final keyword against the live SERP at publish (the
  pre-write SERP flag we built now is the early-warning version). (details in §1)
- **The "key decisions the company should know" doc** — emit `key-decisions-<slug>.md` per article at publish,
  listing every flag that fired. (details in §1b)

### B. KEY DECISIONS the CLIENT (Testlify) must be told — per article
1. **Cannibalisation:** "we already rank for keyword X (position N, URL) — we're rebuilding anyway because the new
   article should outperform." (flagged in the bundle now; the client-facing doc is parked to publish.)
2. **Rewrite of an existing page:** an "Improve existing" idea means we are REWRITING one of the company's own
   existing pages (not adding a new one) — tell them which page + why.

_Both lists live in THIS file: `workflows/03-content-machine/write-phase-backlog.md`. The end-to-end system map +
standing problems live in `workflows/BIG-PICTURE.md`._

---

## ALREADY DONE (2026-07-22) — the first pass
- Tool ideas are never written → enqueued as `tool-build` markers. DONE
- Word-count target shown in the bundle. DONE. UPDATED 2026-07-23: the AUTHORITATIVE target is now DataForSEO's
  live-SERP **Word band** (per-topic), NOT the clubbed `# words` median (a coarse cluster-wide estimate). The clubbed
  median is only a fallback when the brief carries no band. Devansh's call: DataForSEO wins — it read the real SERP.
- "Improve existing" ideas are written but sorted to the BOTTOM (rebuilt from the angle for now). DONE
- The queue sheet (research-log.csv) gained: format · target_words · reuse_verdict · chosen_links · tool_build · tool_reason. DONE

---

## 1. CANNIBALISATION FLAG — our real ranking footprint ✅ DONE + generalised (2026-07-22)
**Final approach (Devansh's call):** do we ALREADY rank for this keyword? Checked against our OWN ranking
footprint — the dedicated DataForSEO `ranked_keywords` pull that 00-foundation already paid for + cached
(`00-foundation/_work/traffic-raw.json`, ~18k keywords we rank for + position + URL). We build a slim
keyword→(rank,url) index once (`03-content-machine/_work/our-rankings.json`, cached, rebuilt only if the raw is
newer), then look the article's primary keyword up: if we rank in the top `CANNIB_RANK_MAX` (**default 10 = page 1**,
the only band where a second page actually splits our traffic) → flag it with the EXACT position + URL. EXACT (real
ranking data), FREE at check-time (the $2.50 pull already happened in the foundation layer), fires ONLY on a real
ranking (13,362 kw indexed; 568 in top-10, 876 more in 11-20 that we now correctly IGNORE).
- Built in `scripts/cannibalization.py` (`check(keyword)`), wired in `run_research.py` after Step 1, shown in the
  bundle, written to the queue (`cannibalization` / `cannibalization_url`). Settings in `config.py`: `CANNIB_CHECK`
  (off-switch), `CANNIB_RANK_MAX` (=10). Documented in `research-conductor-plan.md` as Step 1b.
- Superseded TWO earlier tries: (a) fuzzy top-pages keyword-match (~19% precision, over-flagged), (b) SERP-top-10
  of the researched keyword (free but only the top-10 of one keyword). The footprint lookup is exact AND complete.
- FUTURE (parked): the most precise version re-checks the FINAL keyword against the live SERP at PUBLISH — see PARKED.

## 1b. "KEY DECISIONS THE COMPANY SHOULD KNOW" doc (per article) — PARKED to the write phase
**What he wants (simple):**
- Some decisions the client (e.g. Testlify) must be told, per article. Put them in a small MD that ships with the
  write bundle (a folder, or a section inside the final write article — "things the team should know").
- Two known so far:
  1. **Cannibalisation:** "we already rank for X, but we're rebuilding because the new article is better."
  2. **Rewrite of an existing company article:** an "Improve existing" idea means we are REWRITING one of the
     company's existing pages — the company should know which page and why.
- The write/publish phase isn't built yet, so keep this as an ACTIONABLE CHECKLIST item for that phase.

**Proposed approach (parked):** when the writer/publish step exists, emit `key-decisions-<slug>.md` into the
bundle folder listing every flag that fired (cannibalisation URL, rewritten page URL, tool-escalation, etc.).

## 2. SPOKES — give a spoke the raw materials a real asset idea has (Devansh: "solve for spoke")
**What he wants (simple):**
- A spoke today is just a bare keyword. It has NO title, NO distinct angle, NO internal links — unlike a real asset idea.
- So first, turn the spoke keyword INTO a proper asset idea, using an LLM:
  - Tell the LLM: "this keyword has decent volume + low difficulty, and it's part of pillar X. Create the best
    title + angle for it."
- Then treat it like any idea: vectorise it → search it against our existing content (the reuse check) → get a
  verdict (Brand new / Improve / Build from parts / Already have it).
- The 2-3 ITERATIONS are for DUPLICATION: if the reuse-check says "Already have it", regenerate a sharper angle
  (up to 2-3 tries) until it's genuinely new; if it never gets there, drop it.
- Cannibalisation for a spoke is handled the SAME as #1 — FLAG it, don't block (build anyway).

**Proposed approach:**
- New `spoke_to_idea` step: LLM prompt (keyword + pillar title + pillar angle + brand-scope + volume/difficulty)
  → returns {title, distinct_angle}. This mints the asset idea a spoke was missing.
- Feed that idea through the SAME reuse-check machinery (embed → retrieve vs content-index → LLM verdict) the
  asset engine uses (5-reuse-check) — reused, not reinvented.
- Loop 2-3x on the reuse verdict: while verdict == "Already have it" and tries<3 → re-prompt for a fresher angle;
  else accept (Brand new / Build from parts / Improve existing all proceed, per #Change-3 priority).
- Run the cannibalisation FLAG (#1). Then it enters the write pipeline as a normal idea (format/word-target/etc.).

## 3. SPOKE FOLDER NESTING + CLEAN SLUGS (Devansh: "under that research bundle")
**What he wants (simple):**
- Everything lands under `projects/<company>/03-content-machine/research-bundle/`.
- A spoke that belongs to a pillar should be NESTED UNDER that pillar's bundle folder.
- e.g. `research-bundle/psychometric-tests-hiring/` holds the main article AND `spoke-1-<name>/`, `spoke-2-<name>/`…
- Make sure the slugs are clean and correct.

**Proposed approach:**
- For a spoke, the bundle (and each engine's out dir) writes under `research-bundle/<hub-slug>/spoke-N-<spoke-slug>/`
  instead of a flat top-level folder.
- Slug rule: hub = its clean title slug; spoke = `spoke-<n>-<clean-keyword-slug>` under the hub dir.
- Touch: config paths (BUNDLE_OUT/DFS_OUT/etc. per-spoke), topic_pick slug minting for spokes, bundle.run output path.

## 4. FEEDBACK LOOP — a built article joins the content-database (Devansh: "become a part of content database")
**What he wants (simple):**
- After an article is actually BUILT/published, it should be ADDED to the content-database.
- So the next reuse-check + cannibalisation check can see it (we never rebuild the same thing across runs).
- (The write/publish phase isn't built yet — keep this for the right place, later.)

**Proposed approach:**
- After publish (a step we haven't built), append the new page (URL, title, full content, target keyword) to
  `00-foundation/output/content-database.csv`, and re-embed just that page into the reuse-check index.
- PARKED until the write→publish step exists. Placed here so it's not forgotten.

## 5. FORMAT ROUTER (the earlier suggestion — parked, re-added on request)
- Connect each idea's `Format` column to its matching format playbook (the 9 `formats/*/ACTIONABLE-CHECKLIST.md`).
- So a listicle is written like a listicle, a report like a report — not one generic shape for all.
- Not wired today; the `Format` column is read by nothing in the write phase. Build when we wire the writer itself.

## 6. UPDATE ALL THE ARCHITECTURE-EXPLAINER HTML FILES
- We revamped a lot (asset engine + write phase). Every phase/workflow has an explainer HTML that's now stale.
- Go through each, edit it to match what the engine actually does now. (Convention: ~/.claude/conventions/architecture-explainer-html.md)

---

## THE PLAN FOR THIS SESSION (Devansh)
1. Capture all the above (this file). ✅
2. Decide the approach for each (done above — review).
3. Build #1 (cannibalisation) + #2 (spoke→idea + iterations) + #3 (spoke nesting).
4. Clean the stale research-log (3 done + 14 failed spokes + 1 in-progress) — keep one best bundle as the compare baseline.
5. Run ONE normal article end-to-end AND ONE spoke end-to-end, both with the new checks — on the **Haiku** model (save credits).
6. Compare both to the best earlier run.
7. If good: delete the earlier runs, keep the sheet + final idea file clean.
8. Update all the architecture-explainer HTML files.
9. Build the tickable checklists as we go.
