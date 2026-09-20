#!/usr/bin/env python3
"""The research conductor — ONE command, one topic, all four engines, autonomous + resumable.
Pure sequencing: it picks a topic, then calls each engine's runner in order and hands outputs forward.
No business logic here (that lives in the engines).

  python3 run_research.py                       # auto-pick the next topic (queue, else clubbed CSV)
  python3 run_research.py --asset "Recruiting Metrics Benchmark"   # force a specific clubbed topic (testing)

Chain: 0 pick → 1 DataForSEO → 2 STORM → 3 gap-check → 4 build_structure → 5 bundle → 6 log + enqueue spokes.
Resumable: a step is skipped if its output already exists; --redo reruns all, --from N forces from step N.
"""
import os, sys, json, re, time, socket, argparse, subprocess, urllib.request
import config, topic_pick, bundle, cannibalization, spine, topic_gate

ORDER = ["0", "1", "2", "3", "4", "5", "6"]


def _run(cmd, py=None, cwd=None, soft=False):
    """Run an engine runner as a subprocess, streaming its output live so long steps (STORM) are legible.
    soft=True returns the exit code instead of sys.exit-ing, so the caller can handle DEFINED non-zero outcomes
    (e.g. DataForSEO's exit 3 = 'no keyword demand, skip this topic')."""
    full = [py or sys.executable] + cmd
    print(f"   $ {os.path.basename(full[1])} " + " ".join(str(c) for c in cmd[1:]))
    r = subprocess.run(full, cwd=cwd)
    if r.returncode != 0 and not soft:
        sys.exit(f"   ! {os.path.basename(full[1])} exited {r.returncode} — stopping (fix + re-run to resume).")
    return r.returncode


def _port_up(port):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _shim_provider():
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{config.SHIM_PORT}/health", timeout=1) as r:
            return json.load(r).get("provider")
    except Exception:
        return None


def ensure_shim(model=None, log_dir=None):
    """Start the local shim for the requested CLI provider and model when needed.
    log_dir (per revamp Phase 0.5): where the shim writes its logs — kept under projects/<company>/ so run
    artefacts stay out of the tool folder (convention A1). Falls back to the shim's own default if None."""
    provider = os.environ.get("SHIM_PROVIDER", "claude")
    if model or (_port_up(config.SHIM_PORT) and _shim_provider() != provider):
        subprocess.run(["pkill", "-f", "shim.py"], capture_output=True); time.sleep(2)
    if _port_up(config.SHIM_PORT):
        return
    env = dict(os.environ)
    env["SHIM_PROVIDER"] = provider
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        env["SHIM_LOG_DIR"] = log_dir
    if model:
        env["SHIM_MODEL"] = model
    print(f"   starting STORM shim on :{config.SHIM_PORT}{' (model=' + model + ')' if model else ''} ...")
    subprocess.Popen([config.STORM_PY, config.STORM_SHIM], env=env,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(config.SHIM_WAIT):
        if _port_up(config.SHIM_PORT):
            print("   shim up."); return
        time.sleep(1)
    sys.exit(f"   ! shim did not come up on :{config.SHIM_PORT} within {config.SHIM_WAIT}s")


def _render_article(dossier_dir):
    """Render a STORM dossier dir -> a viewable article.html (clickable citations + references). Non-fatal."""
    if not os.path.exists(os.path.join(dossier_dir, "storm_gen_article_polished.txt")):
        return
    r = subprocess.run([sys.executable, config.STORM_PREVIEW, dossier_dir], capture_output=True, text=True)
    if r.returncode == 0:
        print(f"   rendered article.html for {os.path.basename(dossier_dir)}")
    else:
        print(f"   (article.html render skipped for {os.path.basename(dossier_dir)}: {r.stderr[:80]})")


def _primary_kw(slug, hub=""):
    """The DataForSEO primary keyword (Step 1 output) — used for SEO targeting downstream."""
    p = os.path.join(config.DFS_OUT, hub, slug, "proof", "03-final.json")
    return ((json.load(open(p)).get("primary") or {}).get("keyword") or "").strip()


def _research_subject(asset):
    """STORM's short research subject = the asset title with the brand word stripped. The folder no longer
    comes from this string (run_storm.py gets --folder <slug>), so it stays a clean, human topic label; the
    rich context (angle + spine + about/not-about) travels separately via --spine-file."""
    return " ".join(re.sub(r'(?i)\b' + re.escape(config.COMPANY) + r'\b\s*:?\s*', '', asset).split()).strip(" :–—|,&")


def _migrate_legacy_storm_dir(sdir, asset, angle, hub=""):
    """Self-heal (2026-08-03): a pre-slug run left this topic's dossier in a title-mangled folder. If the
    slug folder is missing but the legacy one exists, RENAME it — one folder name per topic, forever."""
    if os.path.isdir(sdir):
        return
    legacy = config.legacy_storm_dir(asset, angle, hub)
    if os.path.isdir(legacy) and legacy != sdir:
        os.rename(legacy, sdir)
        print(f"   migrated legacy STORM folder -> {os.path.basename(sdir)}")


def _spokes(slug, hub=""):
    """The hub's spoke candidates, already ranked best-first by DataForSEO — capped to the top config.MAX_SPOKES."""
    p = os.path.join(config.DFS_OUT, hub, slug, "proof", "03-final.json")
    if not os.path.exists(p):
        return []
    ranked = [{"keyword": s.get("keyword", "").strip(), "why": (s.get("why") or "").strip()}
              for s in (json.load(open(p)).get("spoke_candidates") or []) if s.get("keyword")]
    return ranked[:config.MAX_SPOKES]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", default=None, help="force a specific clubbed topic (substring match); else auto-pick")
    ap.add_argument("--redo", action="store_true", help="ignore cached outputs; rerun every step")
    ap.add_argument("--from", dest="frm", default=None, choices=ORDER, help="force-rerun from this step onward")
    # DeepSeek by default — see the note in run_topic.py. Claude is nearly out, Codex is quota-locked.
    ap.add_argument("--provider", choices=["claude", "codex", "deepseek"], default="deepseek",
                    help="LLM provider for every LLM step. Default: claude.")
    ap.add_argument("--model", default=None,
                    help="model for the selected provider (for example sonnet or gpt-5.4). Uses that CLI's default when omitted.")
    # WHO GOT PICKED (2026-08-26). The topic is chosen inside this run, so a caller that wants to WRITE
    # what was just researched has no way to learn the slug — and it must not call pick_next() itself,
    # because that marks in_progress and increments the attempt counter. One line to a file settles it.
    ap.add_argument("--slug-out", default=None,
                    help="write the picked slug to this file, so a caller can act on it afterwards")
    ap.add_argument("--until", default=None, choices=ORDER,
                    help="stop after this step (e.g. --until 2 = stop after STORM). Default: run all steps.")
    a = ap.parse_args()
    os.environ["LLM_PROVIDER"] = a.provider
    os.environ["SHIM_PROVIDER"] = a.provider
    if a.model:
        os.environ["LLM_MODEL"] = a.model
    else:
        os.environ.pop("LLM_MODEL", None)
    start = ORDER.index(a.frm) if a.frm is not None else None

    def force(step):  # force this step? else resume decides via have()
        return a.redo or (start is not None and ORDER.index(step) >= start)

    def have(path):
        return os.path.exists(path)

    def stop_after(step):  # honor --until: exit once we've finished the requested step
        if a.until and ORDER.index(step) >= ORDER.index(a.until):
            print(f"\n== STOPPED after step {step} (--until {a.until}), as requested. =="); sys.exit(0)

    # ---- Step 0: pick the topic (bookkeeping only) -----------------------------
    print("== research · Step 0: pick topic ==")
    topic = topic_pick.pick_next(a.asset)
    if topic is None:
        print("   nothing pending in the queue and no eligible clubbed idea left. Done."); return
    slug, asset, angle, source = topic["slug"], topic["asset"], topic["angle"], topic["source"]
    is_spoke = source.startswith("spoke-of:")
    hub = source.split("spoke-of:", 1)[1].strip() if is_spoke else ""   # spoke → nest ALL its engine outputs under the pillar
    if a.slug_out:
        with open(a.slug_out, "w") as _f:
            _f.write(slug)
    print(f"   slug={slug} · source={source}")
    print(f"   asset: {asset[:72]}")

    # ---- Step 0b: the WORLD STATEMENT (about + not_about) — BEFORE any keyword research -----------
    # One cheap AI call from title + angle + brand. The seeds step, the keyword scorer, the judge and the
    # SERP relevance pass all receive it, so a phrase whose searchers live in a different field is caught
    # BEFORE it aims the SERP, the winners study and the spine at the wrong world. [2026-08-04]
    print("== research · Step 0b: world statement ==")
    world_path = spine.world(slug, asset, angle, hub, redo=force("1"))

    # ---- Step 1: DataForSEO (keyword + competitor research) --------------------
    print("== research · Step 1: DataForSEO ==")
    brief = os.path.join(config.DFS_OUT, hub, slug, f"research-doc-{slug}.md")
    dfs_fresh = force("1") or not have(brief)
    if dfs_fresh:
        dfs_cmd = [config.DFS_RUN, "--slug", slug, "--asset", asset, "--world-file", world_path]
        if hub:       # spoke → nest under the pillar (and hand DataForSEO the title + angle directly, since a
            dfs_cmd += ["--hub", hub, "--angle", angle]   # minted spoke isn't in clubbed; competitors come from the SERP)
        code = _run(dfs_cmd, soft=True)
        if code == 3:   # DEFINED no-keyword-demand outcome (s3_score.NoViableKeywords) — SKIP this topic gracefully,
                        # never crash or retry the queue. Terminal 'skipped' status + a remark so the sheet explains it.
            topic_pick.set_meta(slug, research_status="skipped",
                                remarks="no keyword demand — no keyword cleared the volume floor (editorial/niche topic, not researched)")
            print(f"\n⏭  '{slug}' has no keyword demand → marked SKIPPED (terminal) with a remark. Moving on; the next run picks the next topic.")
            return
        if code != 0:
            sys.exit(f"   ! run_dataforseo.py exited {code} — stopping (fix + re-run to resume).")
    else:
        print("   · cached")

    stop_after("1")   # --until 1 → stop after DataForSEO
    primary = _primary_kw(slug, hub)
    if not primary:
        sys.exit("   ! no primary keyword from DataForSEO — something went wrong in Step 1.")
    storm_topic = _research_subject(asset)
    sdir = config.storm_dir(slug, hub)                      # slug-named, same as every other engine
    _migrate_legacy_storm_dir(sdir, asset, angle, hub)      # adopt a pre-slug folder if one exists
    print(f"   primary keyword (SEO target): {primary!r}")
    print(f"   STORM research subject:       {storm_topic!r}  (folder: {slug})")

    # ---- Cannibalisation FLAG (free) — do we already RANK for this keyword? Looks the primary keyword up in our
    #      real ranking footprint (00-foundation's ranked_keywords pull). If we rank (top N) → flag it. Never blocks. ----
    hit = cannibalization.check(primary)
    if hit:
        print(f"   ⚠️  cannibalisation: we already rank #{hit.get('rank')} for {hit['keyword']!r} via {hit['url']} "
              f"— building anyway (flagged for the team).")
        topic_pick.set_meta(slug, cannibalization=f"#{hit.get('rank')} · {hit['keyword']}", cannibalization_url=hit["url"])

    # ---- Step 1b: THE TOPIC GATE — is this ours, and what is the real angle? ---
    # Here because DataForSEO has just produced the real search results and STORM has not started, so a
    # topic that cannot serve us is dropped before the expensive step rather than after it. The angle it
    # returns REPLACES the one written months ago against a single competitor page, and is written back to
    # the queue — the single source all 19 downstream consumers read.
    print("== research · Step 1b: topic gate ==")
    gate = topic_gate.run(slug, asset, angle, hub, redo=force("1"))
    if not gate.get("relevant"):
        topic_pick.set_meta(slug, research_status="not-relevant",
                            remarks=f"not relevant — {gate.get('why') or 'no reason given'}")
        print(f"\n⏭  '{slug}' is not our topic → marked NOT-RELEVANT (terminal) with the reason. "
              f"Nothing further ran; the next run picks the next topic.")
        return
    if gate.get("angle_changed") and gate.get("angle"):
        topic_pick.set_meta(slug, angle=gate["angle"])
        angle = gate["angle"]              # everything below this line uses the researched angle
        print("   queue: angle replaced with the researched one")

    # ---- Step 2a: the working spine (the research target STORM is pointed at) --
    print("== research · Step 2a: working spine ==")
    spine_path = spine.run(slug, asset, angle, hub, redo=force("2"))

    # ---- Step 2: STORM (deep background dossier) -------------------------------
    print("== research · Step 2: STORM ==")
    dossier = os.path.join(sdir, "storm_gen_article_polished.txt")
    raw_art = os.path.join(sdir, "storm_gen_article.txt")

    def _storm_ok():
        # GATE: STORM can exit 0 yet produce an empty/stub article (research ran, write-article call came back empty).
        # A healthy run has a non-empty raw article + a polished article of real length. Below the floor = FAILED run.
        if not have(dossier):
            return False
        words = len(open(dossier).read().split())
        raw_ok = os.path.exists(raw_art) and os.path.getsize(raw_art) > 0
        return raw_ok and words >= config.STORM_MIN_WORDS

    if force("2") or not _storm_ok():
        for attempt in (1, 2):   # one retry — the article-generation step can transiently return empty
            if a.provider != "deepseek":     # deepseek talks straight to its own real API — no local shim needed
                ensure_shim(a.model, log_dir=os.path.join(config.STORM_OUT, "_shim-logs", slug))
            storm_cmd = [config.STORM_RUN, storm_topic, "--provider", a.provider,
                         "--folder", slug,                       # folder = the slug, same as every other engine
                         "--spine-file", spine_path,             # title/angle/spine/about/not-about for every prompt
                         "--perspectives", "4",                  # the 4-role research team (builder/sceptic/evidence/practitioner)
                         *config.STORM_ARGS]
            if a.model:
                storm_cmd += ["--model", a.model]
            if hub:                             # spoke → STORM writes under storm/out/<hub>/<slug>/
                storm_cmd += ["--hub", hub]
            _run(storm_cmd, py=config.STORM_PY)
            if _storm_ok():
                break
            print(f"   ! STORM attempt {attempt} produced an empty/stub article (< {config.STORM_MIN_WORDS} words) — "
                  f"{'retrying once' if attempt == 1 else 'giving up'}")
        if not _storm_ok():
            sys.exit("   ! STORM FAILED — empty/stub article after a retry. NOT proceeding: a dud STORM run poisons "
                     "everything downstream (few cards -> own-pages dominate -> citations become ~all our own site). "
                     "Re-run to try again once STORM is healthy.")
    else:
        print("   · cached")

    _render_article(sdir)   # viewable article.html for the main dossier
    stop_after("2")   # --until 2 → stop after STORM
    # ---- Step 3: gap-check (fill what the brief covers but STORM missed) -------
    print("== research · Step 3: gap-check ==")
    gap = os.path.join(config.GAP_OUT, hub, slug, "gap-check.md")
    if force("3") or not have(gap):
        gap_cmd = [config.GAP_RUN, "--slug", slug, "--brief", brief, "--dossier", dossier]
        if hub:               # spoke → nest gap-check output under the pillar
            gap_cmd += ["--hub", hub]
        if force("3"):        # forcing the conductor step forces a full gap-check rerun (else it resumes)
            gap_cmd.append("--redo")
        _run(gap_cmd)
    else:
        print("   · cached")

    for _name in sorted(os.listdir(sdir)):   # render article.html for each gap-fill iteration too
        if _name.startswith("iteration-"):
            _render_article(os.path.join(sdir, _name))
    stop_after("3")
    # ---- Step 4: build the article blueprint ----------------------------------
    print("== research · Step 4: build structure (blueprint) ==")
    blueprint = os.path.join(config.STRUCT_OUT, hub, slug, f"structure-{slug}.json")
    if force("4") or not have(blueprint):
        struct_cmd = [config.STRUCT_RUN, "--slug", slug, "--asset", asset, "--storm-topic", sdir]
        if hub:               # spoke → nest structure output under the pillar
            struct_cmd += ["--hub", hub]
        if angle:  # steer build_structure's OWN relevance filter (its step 1b, not this file's)
            struct_cmd += ["--angle", angle]
        if force("4"):        # CASCADE (2026-08-04): forcing this step must also bust build_structure's OWN
            struct_cmd += ["--reharvest", "--redo"]   # caches (cards.json + _stage), or a "rerun" silently
                              # rebuilds the old blueprint from the old dossier's cards.
        _run(struct_cmd)
    else:
        print("   · cached")

    stop_after("4")
    # ---- Step 5: write-ready bundle -------------------------------------------
    print("== research · Step 5: write-ready bundle ==")
    bundle_md = os.path.join(bundle._bundle_dir(slug), f"bundle-{slug}.md")   # nested for spokes; MUST match bundle.run's path
    if force("5") or not have(bundle_md):
        bundle.run(slug, asset, angle)
    else:
        print("   · cached")

    stop_after("5")
    # ---- Step 6: log done + enqueue this hub's spokes --------------------------
    print("== research · Step 6: log + enqueue spokes ==")
    topic_pick.mark_done(slug)
    if is_spoke:   # ONE-LEVEL-ONLY: a spoke never spawns its own spokes (else the queue grows unbounded)
        print(f"   marked '{slug}' research=done · (this is a spoke — not enqueuing spokes-of-spokes)")
    else:
        # spoke minting costs money (Voyage + LLM) and runs AFTER mark_done — wrap it so a mint/Voyage
        # failure can't abort an already-successful hub research run (the hub stays done; spokes just skipped).
        try:
            added = topic_pick.insert_spokes(slug, asset, angle, _spokes(slug, hub))   # each spoke keyword minted into a real idea (hub="" here — hubs are flat)
            print(f"   marked '{slug}' research=done · recorded {len(added)} spoke(s) (top {config.MAX_SPOKES}) "
                  f"in spokes.csv against this hub — they do NOT enter the queue and are run by hand")
        except Exception as e:
            print(f"   marked '{slug}' research=done · ⚠ spoke enqueue failed ({str(e)[:60]}) — spokes skipped (not fatal)")

    print(f"\nDONE (research) → write-ready bundle: {bundle_md}")
    print("   research only — nothing is written yet. Next:  /writer " + slug)


if __name__ == "__main__":
    main()
