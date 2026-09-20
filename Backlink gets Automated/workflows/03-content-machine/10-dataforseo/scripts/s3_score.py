"""Step 3 (scoring/judge) — the agent step, now scripted. Reads the fetched metrics, runs a scorer PANEL
(parallel headless-Claude calls) + a JUDGE, and writes the Keywords section.

Reads:  <run_dir>/proof/03-metrics.json  (list of {kw, vol, kd, intent})  + the asset title + distinct angle.
Writes: <run_dir>/proof/03-verdict-1..N.json (panel audit trail) · 03-keywords.md (the section) · spoke-candidates.md.
"""
import os, sys, json, math, argparse
from concurrent.futures import ThreadPoolExecutor
import config, llm

SCORE = llm.load_prompt("score-keywords.md")
JUDGE = llm.load_prompt("judge-keywords.md")
BATCH = 60


def _table(rows):
    return "\n".join(f"{r['kw']} | {r.get('vol')} | {r.get('kd')} | {r.get('intent','')}" for r in rows)


def _score_batch(batch, asset, angle, world=None, hygiene=""):
    """Returns (ok, rows). ok=False marks a real failure (distinct from a legitimately empty result), so run()
    can tell 'the scorer crashed' from 'the scorer scored nothing' and refuse to pick a primary off no scores."""
    world = world or {}
    p = (SCORE.replace("{{BRAND}}", config.BRAND).replace("{{ASSET_TOPIC}}", asset)
         .replace("{{DISTINCT_ANGLE}}", angle).replace("{{BRAND_ONELINER}}", config.BRAND_ONELINER)
         .replace("{{ABOUT}}", world.get("about") or "(not available for this run)")
         .replace("{{NOT_ABOUT}}", world.get("not_about") or "(not available for this run)")
         .replace("{{HYGIENE}}", hygiene or "(none flagged)")
         .replace("{{CANDIDATE_TABLE}}", _table(batch)))
    try:
        return True, llm.call_json(p)
    except Exception as e:
        print(f"    ! scorer batch failed: {e}")
        return False, []


def _kw_table(items, extra=None):
    cols = ["keyword", "vol", "KD"] + ([extra] if extra else [])
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols)
    body = "\n".join("| " + " | ".join(
        [i.get("keyword", ""), str(i.get("volume", "")), str(i.get("kd", ""))]
        + ([str(i.get("why", ""))] if extra else [])) + " |" for i in items)
    return head + "\n" + body


def _num(x, d=0.0):
    try: return float(x)
    except (TypeError, ValueError): return d


def _rank_spokes(spokes):
    """Score each spoke candidate and return them sorted best-first (the conductor keeps its top MAX_SPOKES).
    score = W_REL*(relevance/10) + W_VOL*volume(log min-max across the set) + W_KD*((100-KD)/100).
    Volume is log-normalized because it's heavy-tailed — raw min-max would let one giant head dominate the 25%."""
    if not spokes:
        return spokes
    # HARD FLOOR first: drop off-cluster heads (relevance below the floor) whatever their volume. Missing → kept.
    spokes = [s for s in spokes if _num(s.get("relevance"), 5.0) >= config.SPOKE_MIN_RELEVANCE]
    if not spokes:
        return spokes
    logs = [math.log10(max(_num(s.get("volume")), 1.0)) for s in spokes]
    lo, hi = min(logs), max(logs)
    span = hi - lo
    for s, lv in zip(spokes, logs):
        rel = max(0.0, min(_num(s.get("relevance"), 5.0), 10.0)) / 10.0   # default 5 if the judge omitted it
        vol = 0.5 if span == 0 else (lv - lo) / span                       # all-equal volumes → neutral, don't inflate
        kd  = max(0.0, min((100.0 - _num(s.get("kd"), 50.0)) / 100.0, 1.0))
        s["spoke_score"] = round(config.SPOKE_W_RELEVANCE * rel
                                 + config.SPOKE_W_VOLUME * vol
                                 + config.SPOKE_W_KD * kd, 3)
    return sorted(spokes, key=lambda s: s.get("spoke_score", 0.0), reverse=True)


class NoViableKeywords(RuntimeError):
    """DEFINED, non-error outcome: not one keyword cleared the volume floor, so there is nothing to score — the
    topic simply has no keyword demand (an editorial/niche idea). Distinct from a scoring FAILURE. The conductor
    catches this and SKIPS the topic gracefully (marks it terminal + a remark) instead of crashing the queue."""


def run(run_dir, asset, angle, world=None, hygiene=""):
    world = world or {}
    proof = os.path.join(run_dir, "proof")
    metrics = json.load(open(os.path.join(proof, "03-metrics.json")))
    cands = [r for r in metrics if (r.get("intent") in ("informational", "commercial"))]
    if not cands:
        # No candidate ever reached the scorer — the volume filter emptied the pool. This is the no-keyword-demand
        # fallback path (a DEFINED outcome), not a failure: signal the conductor to skip, don't crash. [fallback 2026-07-23]
        raise NoViableKeywords(
            f"no informational/commercial keyword cleared the volume floor (>= {config.VOL_FLOOR}) — "
            f"this topic has no keyword demand")
    print(f"  scoring {len(cands)}/{len(metrics)} candidates (informational/commercial) in batches of {BATCH}")
    batches = [cands[i:i + BATCH] for i in range(0, len(cands), BATCH)]

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        results = list(ex.map(lambda b: _score_batch(b, asset, angle, world, hygiene), batches))
    verdicts = [rows for ok, rows in results]
    for n, v in enumerate(verdicts, 1):
        config.write_json(os.path.join(proof, f"03-verdict-{n}.json"), v)

    scored_rows = [row for ok, rows in results if ok for row in rows]
    failed_batches = sum(1 for ok, _ in results if not ok)
    # "No pick without a score": the judge must never choose a primary keyword off zero scorer input. If every
    # batch failed (or all returned empty), abort loudly instead of fabricating a primary from nothing. [A#18]
    if not scored_rows:
        raise RuntimeError(f"scorer produced 0 rows across {len(batches)} batch(es) "
                           f"({failed_batches} failed) — refusing to pick a primary keyword with no scores.")
    if failed_batches:
        print(f"    !! {failed_batches}/{len(batches)} scorer batches FAILED — judging on the survivors only")
    all_verdicts = json.dumps(scored_rows)
    jp = (JUDGE.replace("{{BRAND}}", config.BRAND).replace("{{ASSET_TOPIC}}", asset)
          .replace("{{DISTINCT_ANGLE}}", angle)
          .replace("{{ABOUT}}", world.get("about") or "(not available for this run)")
          .replace("{{NOT_ABOUT}}", world.get("not_about") or "(not available for this run)")
          .replace("{{VERDICTS}}", all_verdicts)
          .replace("{{METRICS_TABLE}}", _table(cands)))
    final = llm.call_json(jp)
    final["spoke_candidates"] = _rank_spokes(final.get("spoke_candidates", []))   # ranked; conductor caps to its top few

    # render the Keywords section (matches the SAMPLE shape)
    pr = final.get("primary") or {}
    md = [f"**Primary:** `{pr.get('keyword','')}`",
          f"- Volume: {pr.get('volume')}", f"- KD: {pr.get('kd')}", f"- Intent: {pr.get('intent','')}"]
    if pr.get("split_world"):
        md.append("- ⚠ Split-world phrase: part of this volume belongs to searchers in a different field "
                  "— the SERP will be mixed (see 'why').")
    md += [f"- Why: {pr.get('why','')}", ""]
    if final.get("variations"):
        md += ["**Variations** (rewords/synonyms of the primary — same intent; woven in-body, NO own section):", "",
               _kw_table(final["variations"]), ""]
    if final.get("secondary"):
        md += ["**Secondary** (no fixed cap — each anchors one section):", "",
               _kw_table(final["secondary"], extra="section it anchors"), ""]
    if final.get("in_body"):
        md += ["**In-body only** (core to the angle, no keyword clears the floor):"] + \
              [f"- {t}" for t in final["in_body"]] + [""]
    md += ["**Spokes** (own future articles → `spoke-candidates.md`):"] + \
          [f"- {s.get('keyword')} ({s.get('volume')})" for s in final.get("spoke_candidates", [])]
    config.write_text(os.path.join(proof, "03-keywords.md"), "\n".join(md) + "\n")

    spokes = final.get("spoke_candidates", [])
    sp = ["# Spoke candidates (own future articles) — ranked best-first", "",
          "> Score = `0.5·relevance + 0.25·volume(log) + 0.25·ease(100−KD)`. The research conductor enqueues only its "
          "top few (`config.MAX_SPOKES`); the rest stay here for the record.", "",
          "| # | keyword | vol | KD | intent | relevance | score | why |",
          "|---|---|---|---|---|---|---|---|"]
    sp += [f"| {i} | {s.get('keyword')} | {s.get('volume')} | {s.get('kd')} | {s.get('intent','')} | "
           f"{s.get('relevance','')} | {s.get('spoke_score','')} | {s.get('why','')} |" for i, s in enumerate(spokes, 1)]
    config.write_text(os.path.join(proof, "spoke-candidates.md"), "\n".join(sp) + "\n")
    config.write_json(os.path.join(proof, "03-final.json"), final)   # machine copy (primary for the runner/resume)

    print(f"  -> primary '{pr.get('keyword')}' · {len(final.get('variations',[]))} variations · "
          f"{len(final.get('secondary',[]))} secondaries · {len(spokes)} spokes -> 03-keywords.md")
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--asset", required=True); ap.add_argument("--angle", default="")
    a = ap.parse_args()
    run(a.run_dir, a.asset, a.angle)
