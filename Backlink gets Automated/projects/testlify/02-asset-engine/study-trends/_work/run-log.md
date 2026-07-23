# Study-Trends RUN LOG — Testlify (re-run 2026-06-29)

Re-run with the client-supplied subreddit list (replacing the prior study-trends pool, which was deleted).

## Phase A
- Subreddits: client-supplied list (19 unique) — treated as approved; sanity-checked each is alive.
- Scrape: 17 subs × 25 top/year posts = 425 posts, 46,011 comments. Dropped 2 dead/blocked subs:
  r/TalentAcquisition (1 post on hot; the documented dead-sub case) and r/recruiters (top/year 403; hot feed
  avg score 2 = promo junk). FetchLayer fully removed from the toolchain per client instruction.

## Phase B
- 2a: phrases extracted by 9 parallel Sonnet sub-agents → 1,092 phrases, validated 425/425 (0 missing/extra/dup).
  ~7% of phrases ran 5-8 words (kept; specific and meaningful) — logged, not faked.
- 2b: consolidation done by me (not delegated); merge-check.md written BEFORE tensions.csv. First pass via a
  shared-pain taxonomy after reading all phrases; per-phrase validation + bleed removal on the kept tensions.
- 2c/2d: 425 posts mapped to 29 tensions + misc (59, 13.9% ≤ 15%). tensions.csv built.
- Stage 3: scored against brand-scope.md. **6 KEEP (all CORE), 23 DROP** (off-brand/off-buyer; off-brand
  buckets >8 posts examined by name in merge-check.md). Client delegated the KEEP/DROP sign-off ("only a few
  relevant, decide accordingly").
- Stage 4: 6 kept tensions → 6 asset ideas → study-trends-ideas.csv.

## Stage 5 — verify gate
VERIFY: PASS — all gates satisfied.
(posts=425  tensions=30  kept=6  ideas=6  misc=59)
