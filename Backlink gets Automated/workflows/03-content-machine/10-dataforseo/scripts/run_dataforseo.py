#!/usr/bin/env python3
"""DataForSEO research engine — one command, all steps, resumable. Pure sequencing: it calls each step's
script/run() in order and hands outputs forward. No business logic lives here.

  python3 run_dataforseo.py --slug recruiting-metrics-benchmark --asset "Recruiting Metrics Benchmark"

--asset is a substring that UNIQUELY matches the Asset column in clubbed-ideas.csv (Step 0 reads the row).
--slug names the output dir: config.OUT/<slug>/ (proof/ + research-doc-<slug>.md + research-notes.md).
Resumable: each step writes a named file; on re-run an existing one is reused. --redo forces a full rerun;
--from <step> reruns from that step onward (0,1,2,3,4,5,7 — 6/AEO was removed 2026-08-04: nothing consumed it).
"""
import os, sys, json, argparse, subprocess
import config, dfs, s0_seeds, s3_score, s4b_snapshot, s5b_winners, s7_assemble

ORDER = ["0", "1", "2", "3", "4", "5", "7"]   # "6" (AEO) removed — zero consumers


def _credit_preflight():
    """Before spending, stop cleanly if the DataForSEO balance is below config.MIN_CREDITS. Fail-open on a
    flaky balance check (the paid calls themselves error loudly). A non-zero exit leaves the topic queued."""
    try:
        bal = dfs.balance()
    except Exception as e:
        print(f"   · credit pre-flight skipped (balance check failed: {str(e)[:80]})")
        return
    if isinstance(bal, (int, float)) and bal < config.MIN_CREDITS:
        sys.exit(f"  !! Not enough DataForSEO credits: ${bal:.2f} < ${config.MIN_CREDITS:.2f} — "
                 f"top up and re-run. (Nothing spent; topic left in the queue.)")
    if isinstance(bal, (int, float)):
        print(f"   · DataForSEO balance ${bal:.2f} (>= ${config.MIN_CREDITS:.2f}) — proceeding")


def _sh(*cmd):
    """Run a fetch-step script as a subprocess (they're CLI tools), streaming failures loudly."""
    r = subprocess.run([sys.executable, os.path.join(config.HERE, cmd[0]), *cmd[1:]],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"  ! {cmd[0]} failed:\n{r.stdout[-600:]}\n{r.stderr[-600:]}")
    tail = r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else []
    if tail: print("   ", tail[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--hub", default="", help="hub slug — nest a spoke's output under its pillar: config.OUT/<hub>/<slug>/ (empty = flat, for hubs)")
    ap.add_argument("--asset", required=True, help="hub: substring matching the clubbed Asset · spoke: the full title")
    ap.add_argument("--angle", default=None, help="spoke/direct mode: pass the angle so Step 0 skips the clubbed lookup")
    ap.add_argument("--world-file", dest="world_file", default=None,
                    help="path to spine.json holding the world statement (about/not_about) — threaded into seeds, scorer, judge and the SERP snapshot")
    ap.add_argument("--redo", action="store_true", help="ignore cached outputs; rerun everything")
    ap.add_argument("--from", dest="frm", default=None, choices=ORDER,
                    help="force-rerun from this step onward (default: resume — reuse every cached output)")
    ap.add_argument("--provider", choices=["claude", "codex", "deepseek"], default=None,
                    help="headless LLM provider for the judgment steps (default: env LLM_PROVIDER, else claude)")
    ap.add_argument("--model", default=None, help="model for the chosen provider (blank = that CLI's default)")
    a = ap.parse_args()
    if a.provider:                    # None => inherit the env (e.g. the conductor's choice); else override
        os.environ["LLM_PROVIDER"] = a.provider; config.LLM_PROVIDER = a.provider
    if a.model:
        os.environ["LLM_MODEL"] = a.model; config.LLM_MODEL = a.model

    run_dir = os.path.join(config.OUT, a.hub, a.slug); proof = os.path.join(run_dir, "proof")   # a.hub="" → flat OUT/<slug>
    os.makedirs(proof, exist_ok=True)
    # THE WORLD STATEMENT (2026-08-04) — about/not_about from the conductor's Step 0b (spine.json). Optional:
    # a standalone run without it just fills the prompts' world slots with "(not available)".
    world = {}
    if a.world_file and os.path.exists(a.world_file):
        try:
            _w = json.load(open(a.world_file))
            world = {"about": (_w.get("about") or "").strip(), "not_about": (_w.get("not_about") or "").strip()}
        except Exception as e:
            print(f"   ! world file unreadable ({e}) — continuing without it")
    _credit_preflight()               # stop before spending if the balance is below the buffer
    start = ORDER.index(a.frm) if a.frm is not None else None

    def do(step):  # force-run this step? (--redo, or it's at/after --from). Otherwise resume drives it via have().
        return a.redo or (start is not None and ORDER.index(step) >= start)

    def have(fname):
        return os.path.exists(os.path.join(proof, fname))

    # ---- Step 0: anchors + seeds ------------------------------------------------
    print("== Step 0: anchors + seeds ==")
    if do("0") or not have("00-anchors.json"):
        anc = (s0_seeds.run(run_dir, asset=a.asset, angle=a.angle, world=world) if a.angle else s0_seeds.run(run_dir, asset_match=a.asset, world=world))
    else:
        anc = json.load(open(os.path.join(proof, "00-anchors.json"))); print("    · cached")
    asset, angle = anc["asset"], anc["angle"]
    seeds = anc["head_seeds"] + anc["sibling_seeds"]
    head_seed = anc["head_seeds"][0] if anc["head_seeds"] else seeds[0]

    # ---- Step 1: expand (tight net + ranked net) --------------------------------
    # Gate on 01b-ranked.json (written by the LAST sub-step, s1b_ranked). Gating on 01-pool.json was wrong:
    # s1_expand writes it after the tight net, so a crash before the ranked net left resume skipping Step 1
    # entirely — the run continued without its main relevance data (the ranked net), silently. [A#13]
    print("== Step 1: expand — tight + ranked nets ==")
    if do("1") or not have("01b-ranked.json"):
        _sh("s1_expand.py", run_dir, *seeds)
        _sh("s1b_ranked.py", run_dir, head_seed)
    else:
        print("    · cached")

    # ---- Step 2: filter on volume + KD ------------------------------------------
    print("== Step 2: filter (volume + KD) ==")
    if do("2") or not have("02-shortlist.json"):
        _sh("s2_filter.py", run_dir)
    else:
        print("    · cached")

    # ---- Step 3: metrics + intent, then score + judge ---------------------------
    print("== Step 3: metrics + score + judge ==")
    if do("3") or not have("03-final.json"):
        _sh("s3_metrics.py", run_dir)
        try:
            final = s3_score.run(run_dir, asset, angle, world=world, hygiene=anc.get("hygiene", ""))
        except s3_score.NoViableKeywords as e:
            # DEFINED no-keyword-demand outcome (editorial/niche topic). Exit 3 = a SPECIFIC signal the conductor
            # recognises and handles by skipping this topic gracefully (never a crash / retry). [fallback 2026-07-23]
            print(f"  ⚠ {e}\n  → nothing to research; signalling the conductor to SKIP this topic (exit 3).")
            sys.exit(3)
    else:
        final = json.load(open(os.path.join(proof, "03-final.json"))); print("    · cached")
    primary = (final.get("primary") or {}).get("keyword")
    if not primary:
        sys.exit("  ! no primary keyword from Step 3")

    # ---- Step 4: live SERP + snapshot + read-list -------------------------------
    # Gate on the read-list (04-pages-to-read.txt), the LAST file s4b_snapshot writes and the one Step 5 opens.
    # Gating on 04-serp-snapshot.md (written just before it) could resume into Step 5 with no read-list. [A#13]
    print(f"== Step 4: SERP on '{primary}' + snapshot ==")
    if do("4") or not have("04-pages-to-read.txt"):
        _sh("s4_serp.py", run_dir, primary)
        s4b_snapshot.run(run_dir, asset, angle, primary, world=world)
    else:
        print("    · cached")

    # ---- Step 5: read winning pages + winners write-up --------------------------
    print("== Step 5: read winners + gaps ==")
    if do("5") or not have("05-winners.md"):
        _sh("s5_pages.py", run_dir)
        s5b_winners.run(run_dir, angle, primary)
    else:
        print("    · cached")

    # ---- Step 7: assemble the brief + notes -------------------------------------
    # Gate on research-notes.md, the LAST file s7_assemble writes. The doc is written first, so gating on it
    # could resume as "done" with the notes missing. [A#13]
    print("== Step 7: assemble brief + notes ==")
    if do("7") or not have("../research-notes.md"):
        s7_assemble.run(run_dir, a.slug, asset, angle)
    else:
        print("    · cached")

    print(f"\nDONE -> {run_dir}/research-doc-{a.slug}.md")


if __name__ == "__main__":
    main()
