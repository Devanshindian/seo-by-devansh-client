---
type: live issues log for the first real end-to-end run (article + spoke) on the revamped pipeline
purpose: every problem hit during the run, and the generalized fix, so the NEXT article+spoke pair runs clean
started: 2026-07-23 — run on Sonnet 5 (`--provider claude --model sonnet`)
---

# First-run hardening log

Each issue: what broke → the generalized fix (in `workflows/`, never a per-company patch) → verified.

## Issue 1 — `--model` ignored on the Claude path (Sonnet 5 wouldn't apply) ✅ FIXED
- **Found before running.** All four engines (`10-dataforseo`, `12-gap-check`, `13-research-structure`,
  `14-research-conductor`) honored `config.LLM_MODEL` only on the **codex** branch. The **claude** path called
  `claude -p <prompt>` with NO `--model`, so `--provider claude --model sonnet` silently ran on the CLI's default
  model (Opus) for every step except STORM (which threads `--model` correctly via the shim).
- **Fix:** each engine's `llm.py` claude path now appends `--model <LLM_MODEL>` when set:
  `[CLAUDE_BIN, "-p", "--model", LLM_MODEL, prompt]`. One-line change per engine, same shape everywhere.
- **Verified:** the constructed command includes `--model sonnet` when `LLM_MODEL=sonnet`.

## Issue 2 — `NameError: parse_fails` crashed DataForSEO's first LLM call ✅ FIXED
- **Hit on the real run**, Step 0 seeds (`10-dataforseo/scripts/llm.py` `call_json`, line 102): `p = prompt if
  parse_fails == 0 ...` referenced `parse_fails`, which is never defined in that function → NameError on the very
  first call, before any paid DataForSEO spend. (The conductor's llm.py had the identical bug, fixed earlier; the
  engines are drifted copies, so this one survived.)
- **Fix:** rewrote `call_json` to the corrected shape used by the conductor — `attempt == 0` gate + `_sleep_backoff`
  between retries (this copy also had NO pause between retries, so a rate-limited CLI would burn its whole budget
  instantly). Scanned all four engines: gap-check + structure define `parse_fails` correctly; only DataForSEO was broken.
- **Verified:** all four `llm.py` compile; the run resumes cleanly from Step 1.

## Issue 3 — STORM crashed: `ModuleNotFoundError: knowledge_storm` (orphaned by the 02→03 rename) ✅ FIXED
- **Hit on the real run**, Step 2 STORM. DataForSEO (Step 1) completed fully — brief + primary keyword ("cost per
  hire") + 2 spokes. STORM then died on import. Root cause: STORM's venv finds `knowledge_storm` via a path file
  `venv/.../site-packages/_storm_local.pth` that held a **hardcoded absolute path** to
  `.../workflows/02-content-machine/11-storm/engine`. When the content-machine layer was renumbered 02→03, that
  `.pth` (git-ignored, so not caught by the rename sweep) kept the dead `02` path → the import failed even though the
  source sits right there at the `03` path. Classic "renamed a folder, broke a reference silently" (conventions D2).
  Confirmed it was the ONLY stale `02-content-machine` reference in the whole tree.
- **Fix (two parts):** (1) corrected the `.pth` to the real `03` path — immediate unblock; import verified.
  (2) DURABLE: `run_storm.py` now does `sys.path.insert(0, <_storm_dir>/engine)` resolved from `__file__` *before*
  importing knowledge_storm, so the import is rename-proof and no longer depends on the fragile absolute `.pth`.
- **Verified:** `venv/bin/python -c "import knowledge_storm"` → OK; run resumes from Step 2 (DataForSEO cached).
- **Note:** this is a machine-local venv issue (the venv isn't committed), so it won't recur on THIS machine now, and
  the `run_storm.py` insert protects any fresh checkout/rename going forward.

## Issue 4 — the word target: DataForSEO band now wins over the clubbed median ✅ DONE (Devansh's call)
- **Observed on the run:** three disagreeing word targets reached the writer — clubbed `# words` (1,133), DataForSEO
  build-spec band (3,000-4,000), and the structure blueprint's 16 H2s. Devansh's ruling: **DataForSEO wins** because
  it read THIS keyword's live SERP, whereas the clubbed median is a coarse, cluster-wide asset-engine estimate.
  (The 16-H2 blueprint is NOT a defect — the research phase stays exhaustive on purpose; the write phase trims it.)
- **Fix:** `bundle.py` now reads the authoritative band straight from the DataForSEO brief (`_dfs_word_band` parses
  the build-spec `**Word band**` bullet) and surfaces THAT as the target, falling back to the clubbed median only
  when the brief has no band. Single source of truth (F1): the target is now decided in one place, DataForSEO.
- **Verified:** `_dfs_word_band('the-real-cost-recruitment-2026')` → `'3,000-4,000'`; the regenerated bundle shows
  "Target length: 3,000-4,000 words — DataForSEO's live-SERP band" (was "~1133 words").

## Issue 5 — build_structure crashed on spokes: `asset not found` in clubbed ✅ FIXED
- **Hit on the spoke-1 run**, Step 4 (build_structure → harvest_ownpages). `harvest_ownpages._pull_urls` looks the
  asset up in clubbed-ideas.csv to pull its internal-link candidates, and `sys.exit`ed when not found. A MINTED
  spoke isn't in clubbed → crash. Same class as the DataForSEO spoke bug (a clubbed dependency the spoke can't
  satisfy), but in a different engine that hadn't been spoke-tested.
- **Fix:** clubbed own-pages are ENRICHMENT (internal links), not a hard input — the structure's real content is
  STORM cards. So `_pull_urls` now WARNS and returns `[]` when the asset isn't in clubbed, instead of exiting. Fixes
  spokes and makes real articles robust to any title mismatch (graceful degrade, not a dead build).
- **Verified:** the spoke asset → `[]` (no crash); real-article found-path unchanged; compiles; spoke run resumes
  from Step 4 (DataForSEO/STORM/gap-check all cached — no re-spend).

## Issue 6 — DataForSEO retry missed `socket.timeout` → a network blip killed a whole run ✅ FIXED
- **Hit on the spoke-2 run**, DataForSEO Step 4 (SERP): `socket.timeout: The read operation timed out` (a network
  blip — Devansh flagged the net dropping). `dfs.call()` DOES retry transient failures, but its except tuple caught
  `TimeoutError`, and on **Python 3.9** `socket.timeout` is NOT a subclass of `TimeoutError` (unified only in 3.10).
  So the read timeout escaped the retry and crashed the run — one bad network moment = dead run, despite the retry.
- **Fix:** `import socket` + added `socket.timeout` to the caught tuple in `dfs.call()`. Now a read timeout retries
  with backoff like every other transient failure. Harmless on 3.10+ (there it's just an alias).
- **Verified:** `issubclass(socket.timeout, TimeoutError)` is `False` on this 3.9 (the bug), dfs.py compiles, spoke-2
  resumes from Step 4 (steps 0-3 cached, no re-spend).

## Issue 7 — no-keyword-demand FALLBACK: a topic with no viable keyword now SKIPS gracefully ✅ BUILT
- **Surfaced on the "Why Candidates Abandon Applications" run.** DataForSEO's scorer correctly refused (guard:
  "no primary keyword with no scores") because the topic is editorial and had NO keyword ≥ VOL_FLOOR (proven
  deterministic across two independent pulls: 16 keywords, max vol 70; broader neighbours were off-angle). The
  guard was DEFINED but only as a hard crash — no graceful skip.
- **Fix (a real fallback cascade, minimal version):** `s3_score` now raises a typed `NoViableKeywords` when 0
  candidates reach the scorer (distinct from a scoring FAILURE). `run_dataforseo` catches it and exits **3** (a
  specific signal). The conductor's `_run(soft=True)` recognises code 3 → marks the topic terminal `skipped` +
  a **remarks** note (new sheet column) explaining why → returns cleanly (never crashes/retries the queue).
- **Verified:** `run_dataforseo … --from 3` on the editorial topic exits 3; the editorial row is now
  `skipped` with the remark. Devansh's call: skip (not seed-broaden — the broader terms were off-angle).

## Issue 8 — spokes now nest under their pillar in EVERY output dir (not just research-bundle) ✅ DONE
- **Devansh's request:** a spoke's output should sit under its hub everywhere — dataforseo/, gap-check/, storm/,
  research-structure/ — the way research-bundle/ already did.
- **Fix (one consistent pattern):** each engine (`run_dataforseo`, `run_gapcheck`, `build_structure`, `run_storm`)
  takes an optional `--hub`; its run dir becomes `os.path.join(OUT, hub, slug)` (hub="" → flat, so HUBS are
  unchanged). `config.storm_dir(topic, hub)` nests STORM. The conductor computes `hub` once from the spoke's
  `spoke-of:` source and passes `--hub` + nests every path it reads; `bundle.py` gained a shared `_hub(slug)` used
  by every DFS/STRUCT read. Existing Testlify spoke files were moved under the hub.
- **Verified:** all nested paths resolve for both spokes across all 5 locations; the main article (hub, flat) still
  resolves. All 9 changed files compile.

## GOOD — gap-check's STORM re-run path validated LIVE for the first time (spoke-1)
- The spoke dossier had real gaps (2 partial + 1 no). gap-check triaged them → 2 STORM queries → **ran 2 STORM
  re-run iterations successfully** (both rendered). First real exercise of the re-run path; the Issue-3 `.pth`/sys.path
  fix held under it. Confirms the mechanism the article run left unexercised (0-gaps that time).

## Non-issue verified — gap-check's "0 STORM re-runs" is GENUINE, not a masked failure
- Judge scored 21/21 items "covered", each with a real evidence quote from the dossier (not blank defaults) →
  triage produced 0 gap queries → the re-run step wrote `{"iterations": []}` and returned WITHOUT calling STORM.
- A failure could not have been hidden as "0": `rerun_storm.py` fires STORM with `subprocess.run(..., check=True)`,
  so a failed re-run raises and crashes gap-check loudly (like Issue 3 did) rather than recording 0 iterations.
- Caveat: with 0 gaps, the re-run PATH never executed STORM this run — validated by code-reading, not a live re-run.
  Its first real exercise is the first topic that actually has a gap (now protected by the Issue-3 fixes too).
