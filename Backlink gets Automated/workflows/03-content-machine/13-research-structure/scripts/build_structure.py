"""Research-structure — one asset, end to end. Turns all research into the article blueprint.

  python3 build_structure.py --slug <slug> --asset "<exact Asset title>" --storm-topic <projects/<company>/content-machine/storm/out/<slug>> \
      [--angle "<distinct angle>"]

Steps: 1 harvest (STORM + own pages -> cards) · 1a pick persona · 1b spine-relevance filter (drop
       off-spine cards) · 2-3 cluster (MECE, article-aware) · 4 name+split · 5 attach · 7 orphan ·
       8 FAQ+order · 8b keyword-set (pure code, from 03-final.json) · 9 render.
       (Step 6 — a paid DataForSEO keyword per H2 — was REMOVED 2026-08-04: it bought keywords for the
       research blueprint's headings, which the architect redesigns away; live proof — resume-stats bought
       5 keywords for 17 sections, 3 of them for sections the spine filter now deletes. Real per-section
       keywords are the architect's job, after the real sections exist.)

2026-08-03 revamp: the filter + clusterer read the conductor's spine.json (<storm-topic>/spine.json —
spine/about/not_about) and the brand's four personas. REMOVED: brief-card harvesting (duplicated data the
write phase reads directly from the DataForSEO files, with no evidence behind it); Step 4c differentiator
re-decide (fed a review-page badge the write phase ignores); Step 4b competitor-source filter (never fired
once in six runs — parser mismatch — and deleting competitor-sourced research was the wrong behaviour anyway;
the write phase's "never cite a competitor as the authority" rule is the real guard).
Outputs land under out/<slug>/.
"""
import os, sys, argparse, json
import config, harvest_storm, harvest_ownpages, pick_persona, score_cards, cluster, name_clusters, attach, orphan, faq_order, keyword_set, render


import time as _time, sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))))
try:
    import usage_meter as _meter
except Exception:
    _meter = None
_PHASE_T0 = _time.time()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--hub", default="", help="hub slug — nest a spoke's output under its pillar: config.OUT/<hub>/<slug>/ (empty = flat)")
    ap.add_argument("--asset", required=True)
    ap.add_argument("--angle", default="", help="the asset's distinct angle (steers the Step 1b relevance filter); defaults to the asset title")
    ap.add_argument("--storm-topic", dest="storm_topic", required=True, help="projects/<company>/content-machine/storm/out/<Topic> dir (hub)")
    ap.add_argument("--reharvest", action="store_true", help="re-run Step 1 even if cards.json exists")
    ap.add_argument("--refilter", action="store_true", help="re-run Step 1b even if dropped-cards.json exists")
    ap.add_argument("--redo", action="store_true", help="ignore ALL cached stage snapshots (steps 2-9); recompute everything")
    ap.add_argument("--provider", choices=["claude", "codex", "deepseek"], default=None,
                    help="headless LLM provider for the judgment steps (default: env LLM_PROVIDER, else claude)")
    ap.add_argument("--model", default=None, help="model for the chosen provider (blank = that CLI's default)")
    a = ap.parse_args()
    if a.provider:                    # None => inherit the env (e.g. the conductor's choice); else override
        os.environ["LLM_PROVIDER"] = a.provider; config.LLM_PROVIDER = a.provider
    if a.model:
        os.environ["LLM_MODEL"] = a.model; config.LLM_MODEL = a.model

    run_dir = os.path.join(config.OUT, a.hub, a.slug)   # a.hub="" → flat OUT/<slug>
    os.makedirs(run_dir, exist_ok=True)
    cards_path = os.path.join(run_dir, "cards.json")
    drops_path = os.path.join(run_dir, "dropped-cards.json")
    persona_path = os.path.join(run_dir, "persona.json")

    # THE ARTICLE CONTEXT — the conductor's spine.json lives with the dossier. Missing (a legacy run) is
    # tolerated: the filter/clusterer prompts fall back to "(not available for this run)".
    spine_path = os.path.join(a.storm_topic, "spine.json")
    spine_ctx = json.load(open(spine_path)) if os.path.exists(spine_path) else {}
    print(f"  spine context: {'loaded' if spine_ctx else 'NOT FOUND (legacy run — prompts fall back)'}"
          f" ({spine_path})")

    print("== structure · Step 1: harvest cards ==")
    if os.path.exists(cards_path) and not a.reharvest:
        cards = json.load(open(cards_path))
        print(f"  reusing {len(cards)} cards from cards.json (--reharvest to redo)")
    else:
        cards = harvest_storm.harvest(a.storm_topic) + harvest_ownpages.harvest(a.asset)
        for i, c in enumerate(cards, 1):                   # continuous ids across all sources
            c["id"] = i
        config.write_json(cards_path, cards)
        print(f"  total {len(cards)} cards")

    print("== structure · Step 1a: pick reader persona ==")
    if os.path.exists(persona_path) and not (a.refilter or a.reharvest):
        persona = json.load(open(persona_path))
        print(f"  reusing persona: {persona.get('name') or '(generic)'} (--refilter to redo)")
    else:
        persona = pick_persona.run(a.asset, a.angle, run_dir)
        print(f"  persona: {persona.get('name') or '(generic)'} — {persona.get('why','')[:70]}")

    print("== structure · Step 1b: spine-relevance filter ==")
    if os.path.exists(drops_path) and not (a.refilter or a.reharvest):
        dropped_ids = {d["id"] for d in json.load(open(drops_path)).get("dropped", [])}
        cards = [c for c in cards if c["id"] not in dropped_ids]
        print(f"  reusing dropped-cards.json: {len(dropped_ids)} dropped, {len(cards)} kept (--refilter to redo)")
    else:
        cards, rep = score_cards.run(cards, a.asset, a.angle, persona, spine_ctx, run_dir)
        print(f"  dropped {rep['dropped_count']}/{rep['total_cards']} off-spine cards "
              f"({rep['dropped_pct_of_cards']}%, keep_threshold<= {rep['keep_threshold']}); "
              f"{rep['kept_count']} kept -> dropped-cards.json"
              + ("   !! DROP-HEAVY — review" if rep["FLAG"] else ""))

    # ---- Stage-cache for steps 2-9 -------------------------------------------------------------------
    # These steps thread Python objects (sections, cards, …) between each other, so resuming means snapshotting
    # the forward STATE after each stage, not just eyeballing an output file. Without this, a crash at Step 8
    # threw away Steps 2-8 — including Step 6, the PAID DataForSEO keyword step. Each stage reuses its snapshot
    # unless --redo is set. [A#18]
    stage_dir = os.path.join(run_dir, "_stage")
    os.makedirs(stage_dir, exist_ok=True)
    state = {"cards": cards}

    def stage(tag, produce):
        """Reuse _stage/<tag>.json if present (and not --redo); else run produce() -> dict, snapshot, return it.
        produce() gets the current `state` and returns the keys it updates."""
        p = os.path.join(stage_dir, f"{tag}.json")
        if os.path.exists(p) and not a.redo:
            print(f"  · cached ({tag})")
            return json.load(open(p))
        out = produce()
        config.write_json(p, out)
        return out

    print("== structure · Step 2-3: cluster (MECE, article-aware) ==")
    state.update(stage("02-cluster", lambda: {
        "clusters": cluster.run(state["cards"], os.path.join(run_dir, "clusters.json"),
                                a.asset, a.angle, spine_ctx, persona)}))

    print("== structure · Step 4: name + split ==")
    state.update(stage("04-name", lambda: {
        "sections": name_clusters.run(state["clusters"], state["cards"], os.path.join(run_dir, "sections.json"),
                                      a.asset, a.angle, spine_ctx)}))

    print("== structure · Step 5: attach evidence + links ==")
    state.update(stage("05-attach", lambda: {"sections": attach.run(state["sections"], state["cards"])}))

    print("== structure · Step 7: orphan check ==")
    state.update(stage("07-orphan", lambda: {"orphans": orphan.run(state["sections"], a.slug, hub=a.hub)}))

    print("== structure · Step 8: FAQ + order ==")
    def _faq():
        sections2, faq = faq_order.run(state["sections"], a.slug, a.hub)
        return {"sections": sections2, "faq": faq}
    state.update(stage("08-faq", _faq))

    print("== structure · Step 8b: keyword-set (brief primary/variations/secondaries + per-H2 keywords + in-body) ==")
    state.update(stage("08b-kset", lambda: {"kset": keyword_set.run(a.slug, run_dir, hub=a.hub)}))

    print("== structure · Step 9: render ==")
    render.run(a.slug, a.asset, state["sections"], state["faq"], state["orphans"], state["kset"], run_dir)
    if _meter:
        _meter.record_step("build_structure", _time.time() - _PHASE_T0, "research", a.slug)
    print(f"\nDONE -> {run_dir}")


if __name__ == "__main__":
    main()
