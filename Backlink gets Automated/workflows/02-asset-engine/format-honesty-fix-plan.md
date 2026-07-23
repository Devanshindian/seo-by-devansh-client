---
type: fix-plan + build checklist (the format-honesty / over-tooling fix)
principle: GENERALISED FIRST — every fix lands in the reusable engine (workflows/), never as a Testlify patch.
           Testlify is simply the first company we re-run the fixed engine for.
for: 02-asset-engine — Method 1 (competitor study), Method 3 (study trends), 4-merge, 5-reuse-check
status: design approved; awaiting Devansh's GO to start
last_updated: 2026-07-22
---

# The format-honesty fix — generalised-first plan

## The problem in one line
The engine picks a FORMAT first (a tool, because tools win links in OTHER niches) then finds a topic, so
~1,143 of 2,213 ideas became calculators/quizzes when the pages that actually rank are plain ARTICLES.
Root cause is upstream in idea generation, and the fix must live in the GENERIC engine so no future
company over-tools either.

## Proof (measured)
- 92% of Method 1 ideas have exactly ONE backing page (mean 1.10) → the honest format is already recorded
  in that page's Step D tag. Copying the tag is safe.
- 8 calculator pages in the whole 15-competitor set; quizzes pull 3.2 domains/page. Tools barely earn links
  here; articles do.
- The earlier session's idea-review/drop-list.csv (65 ideas) proves the page-filter leaks: off-domain topics
  + product/pricing/HOMEPAGE pages that G2 turned into "Testlify X Calculator" ideas.

## Decisions locked (Devansh)
1. Format ≠ differentiator. Format = copy the competitor page's shape (tool page → tool, flagged). The
   "no tool" rule applies ONLY to the differentiator.
2. Differentiator = a real content gap found by READING the page. Kept BROAD, never a granular menu.
3. Currency is valid: their 2022 stat → cite the current public figure.
4. The desk-research guardrail: the angle must be deliverable by a writer citing PUBLIC sources. It may NOT
   require (a) a tool build, (b) our own original data/survey/internal benchmark, (c) new primary research.
   When the FORMAT itself needs one of these, keep the format + record `tool_escalation`; never fake it as an article.
5. Titles carry NO shape-words (Calculator/Quiz/Interactive/Dashboard/Generator). Shape lives in `Format` only.
6. `tool_escalation` = a real column carried to clubbed-ideas.csv.
7. Method 2: FIXED + INCLUDED (revised 2026-07-22). It still imports cross-niche formats, but `b-adapt.md`
   now follows the same rules as M1's G2 — no shape-words in the `asset` title, and anything needing a real
   build (interactive tool / our own original data / new primary research) is flagged in `tool_escalation`.
   The write phase later picks only the desk-doable (tool_escalation-empty) ideas; genuine tool ideas are
   labelled for a human. `4-merge` config `INCLUDE_M2=True`. (Earlier plan had it on hold; Devansh chose to
   correct it properly instead.)
8. Method 3: unchanged (already tension-first, zero tool words).
9. Relevance recheck: drop ONLY nonsense + off-brand, never for low backlinks; protect high-proof; log drops.
10. Sort clubbed by Brand fit (CORE→TRANSPLANT→ADJACENT), then each idea's own strength (so M3 isn't buried).
11. Reuse-check: reuse the existing page-index (do NOT re-embed our site); redo only the idea-lookup + judge.
12. Self-check with JUDGE subagents at each key stage; Devansh reviews clean samples.

---

# PART A — THE GENERALISED ENGINE CHANGES (do these first, company-agnostic)

Every row is an edit to a reusable file under `workflows/02-asset-engine/`. Nothing here is Testlify-specific.

| # | Change | Generic file(s) to edit | What changes |
|---|---|---|---|
| **E1** | Format = the Step D tag; never upgrade an article into a tool | `1-competitor-study/prompts/g2-reason-rows.md` | rewrite step 4: `format` output = the tag passed in; explicit ban on article→tool |
| **E2** | Differentiator = desk-research content gap (broad) + currency; ban tool/own-data as the angle | `1-competitor-study/prompts/g2-reason-rows.md` | rewrite the gap/angle steps + add the desk-research guardrail; keep it principle-based |
| **E3** | Title carries no shape-words | `1-competitor-study/prompts/g2-reason-rows.md` | title rule + one clean/dirty example; delete the 2 over-tooling examples |
| **E4** | `tool_escalation` field end-to-end | `prompts/g2-reason-rows.md` (schema) · `scripts/step_g2_reason.py` · `step_g25_dedup.py` · `step_g3_ideas.py` · `step_h_deliver.py` · `4-merge/scripts/config.py` (COLS) · `4-merge/scripts/step_1_stack.py` | new column added + carried through dedup, rank, deliver, merge |
| **E5** | Data-quality gate BEFORE G2 (drop no-body + junk-flagged + commercial-format pages) | `1-competitor-study/scripts/step_g1_sheet.py` · `scripts/config.py` (new `DROP_FORMATS`, `REQUIRE_BODY`) | only clean, buildable pages enter G2; counts logged; assert in code |
| **E6** | Tagger separates commercial vs free-tool cleanly (ONLY if Phase-0 judge says it's needed) | `1-competitor-study/prompts/tag-format.md` | sharpen "Product/landing (commercial)" vs "Free product/library" |
| **E7** | NEW relevance-recheck step (per-idea KEEP/DROP gate) | NEW `4-merge/scripts/step_3_relevance.py` + `4-merge/prompts/relevance-recheck.md` + `config.py` knobs (`RELEVANCE_DROP_CAP`, model) | runs on the merged pool; audit file; protect high-proof |
| **E8** | Sort the clubbed file by Brand fit then own-strength | `4-merge/scripts/step_2_dedup.py` (final write) | replace pure-domains sort with fit-first sort |
| **E9** | Reuse the page-index; redo only idea-side + judge | `5-reuse-check` — run behavior (don't pass rebuild); confirm `step_1_retrieve.py` reuses cached index | no code change if index reuse already supported; else add a reuse flag |
| **E10** | Method 2 on hold | `2-model-other-niches/*.workflow.md` (note: on hold, format-first over-tools) · `SKILL.md` · `4-merge` inputs exclude M2 | doc note + merge input list |
| **E11** | Sync the recipe prose to the new rules (F5 shared vocabulary) | `1-competitor-study/competitor-study.workflow.md` (Step G text + G6 checklist) | recipe matches the prompt; no drift |

**Order to make the edits:** E5+E6 (clean inputs) → E1–E4 (the G2 rewrite + schema) → E7+E8 (merge gate + sort)
→ E10 (M2 hold) → E9 (reuse behavior) → E11 (docs). Then validate (Part C) before any Testlify run.

> ⚠️ **WHAT ACTUALLY SHIPPED — three deltas from the design above (2026-07-22):**
> - **E5 was REVERTED.** Using the format tagger to DELETE pages made the tagger do two jobs; wrong (Devansh).
>   Junk removal is now handled by three existing gates only: Step C's URL filter + G2's `brand_fit=SKIP` +
>   the E7 relevance recheck. `step_g1_sheet.py` / `config.py` / `step_g2_reason.py` are back to no gate.
> - **E6 KEPT but decoupled.** The tagger's commercial-vs-usable-asset split (`tag-format.md`) stayed as a pure
>   FORMAT-accuracy improvement; it is NOT used to drop anything. Testlify was NOT re-tagged (existing tags reused).
> - **E10 → M2 FIXED + INCLUDED** (not on hold). `b-adapt.md` got the format-honesty rules + a `tool_escalation`
>   field; `INCLUDE_M2=True`. See decision 7 and the M2 recipe banner.

---

# PART B — THE TESTLIFY RUN (only after Part A is done + validated)

Run the fixed generic engine for `--company testlify`. Reuses everything already on disk that the fix doesn't
invalidate (competitor pulls, page reads, format tags), regenerates everything downstream of G2.

| Phase | Run action | Cost |
|---|---|---|
| **T0** | Re-run Method 1 from the E5 gate → G2 → G2.5 dedup → G3 rank → Step H deliver | ~2,300 LLM calls, resumable |
| **T1** | Method 3: keep the 106 ideas as-is (no re-run) | free |
| **T2** | Merge M1(new)+M3 → dedup cross-method → sort (E8) → clubbed-ideas.csv | moderate |
| **T3** | Relevance recheck (E7) on the clubbed pool | light |
| **T4** | Reuse-check: reuse index (E9), redo idea-lookup + full judge | judge ~2,000 calls, resumable |
| **T5** | Verify vs idea-review/enriched-v2.csv (tool count fell) + final audit | quick |

---

# PART C — VALIDATION (the judge loop + ground-truth)  [🤖 JUDGE] / [👤 YOU]

- [ ] **Phase-0 tag check** [🤖 JUDGE][👤 YOU] — is the Step D tagger trustworthy enough to copy? Decides whether
      E6 is needed and how hard E5 drops "Product/landing". (Judge is running now.)
- [ ] **G2 prompt** [👤 YOU] — approve the rewritten `g2-reason-rows.md` before T0.
- [ ] **Regenerated ideas** [🤖 JUDGE][👤 YOU] — judge a big sample on every rule (format==tag? title
      shape-word-free? angle a readable desk-deliverable gap? tool_escalation only where real?), fix via the
      prompt, then Devansh reviews a clean sample.
- [ ] **Relevance recheck** [🤖 JUDGE][👤 YOU] — validate E7 against idea-review/drop-list.csv (must catch the
      same KINDS: off-domain + product/homepage); Devansh approves the drop list.
- [ ] **Final** [🤖 JUDGE][👤 YOU] — audit clubbed-ideas.csv; Devansh's final look before the write phase.

Devansh is pulled in at 5 points: Phase-0 tags · G2 prompt · idea quality · drop list · final file.
