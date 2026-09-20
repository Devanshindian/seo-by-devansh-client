#!/usr/bin/env python3
"""Steps −1 and 2a — the WORLD STATEMENT and the WORKING SPINE. Both live in spine.json, filled in two
stages, because they are decided at two different moments:

  Step −1  WORLD  (before DataForSEO): about + not_about, from title + angle + brand alone. This is the
           boundary the keyword research itself checks against — the seeds step, the scorer, the judge and
           the SERP relevance pass all receive it, so a wrong-world keyword (a phrase whose searchers live
           in a different field) is caught BEFORE it aims the whole run at the wrong SERP.
           world() → writes {"title","angle","about","not_about"} to <storm dir>/spine.json.

  Step 2a  SPINE  (after DataForSEO): what the article argues, built from the world + the winners study.
           Also extracts the competitor read (three lists, verbatim) that the spine builds from:
             <dfs run_dir>/proof/07-competitor-read.json
           (Same extraction the write phase runs for itself from the same file — the write phase is left
           untouched and keeps its own copy; edit both prompts together.)
           run() → adds {"spine"} to the same spine.json.

spine.json lives WITH the dossier (storm/out/<hub>/<slug>/spine.json) so STORM, gap-check iterations and
the later spine-vs-final-spine comparison all find everything in one place.
"""
import os
import json
import config
import llm


def _render(items):
    return "\n".join(f"  - {i}" for i in items) if items else "  (none listed)"


def _spine_path(slug, hub=""):
    return os.path.join(config.storm_dir(slug, hub), "spine.json")


def _load(path):
    try:
        return json.load(open(path))
    except Exception:
        return {}


def world(slug, asset, angle, hub="", redo=False):
    """Step −1: the world statement. Cheap (one AI call), no dependencies. Returns the spine.json path."""
    outp = _spine_path(slug, hub)
    cur = _load(outp)
    if cur.get("about") and cur.get("not_about") and not redo:
        print(f"   · world cached ({outp})")
        return outp
    # THE ANGLE IS DELIBERATELY NOT PASSED (2026-08-26, Devansh). It used to be, and it leaked: measured
    # across three real runs, two world statements had the angle wearing the world's clothes. One said the
    # subject was "interview questions each paired with a strong and a weak answer plus a line on how to
    # score" — that is how we planned to WRITE it, not what the topic IS. The other narrowed the subject to
    # "the current public benchmark figure ... by role and volume". That matters because this world then
    # decides which keywords survive inside DataForSEO, so a world narrowed by a months-old angle drops
    # keywords for being off-ANGLE while reporting them as off-WORLD.
    # The prompt's own job is homonyms and neighbouring subjects (hiring hackathon vs prize hackathon), and
    # the title plus the brand answer that. `angle` stays in the signature: callers pass it, and it is still
    # recorded below so a run can be traced back to what it was told.
    prompt = (llm.load_prompt("world.md")
              .replace("{{TITLE}}", asset)
              .replace("{{BRAND}}", config.BRAND)
              .replace("{{ABOUT_BRAND}}", config.ABOUT or "(no description on file)"))
    # llm.call_json retries a PARSE failure, but a reply that parses with a missing field slips through —
    # seen live on the first smoke test. One field-level retry before failing closed.
    w = {}
    for _ in range(2):
        got = llm.call_json(prompt) or {}
        w = {k: str(got.get(k) or "").strip() for k in ("about", "not_about")}
        if all(w.values()):
            break
    missing = [k for k, v in w.items() if not v]
    if missing:
        raise SystemExit(f"   ! world step returned empty field(s) twice: {', '.join(missing)} — not writing a half world")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    config.write_json(outp, {**cur, "title": asset, "angle": angle or "", **w})
    print(f"   world — NOT about: {w['not_about'][:100]}...")
    return outp


def _competitor_read(proof_dir, redo=False):
    """The three winners lists, extracted once and saved next to the study they came from."""
    outp = os.path.join(proof_dir, "07-competitor-read.json")
    winners_p = os.path.join(proof_dir, "05-winners.md")
    if os.path.exists(outp) and not redo:
        print(f"   · competitor-read cached ({os.path.basename(outp)})")
        return json.load(open(outp))
    winners_md = open(winners_p).read()
    got = llm.call_json(llm.load_prompt("extract-winners.md").replace("{{WINNERS}}", winners_md)) or {}
    lists = {k: [str(x).strip() for x in (got.get(k) or []) if str(x).strip()]
             for k in ("gaps_to_own", "winners_common_h2s", "winners_drift")}
    config.write_json(outp, lists)
    print(f"   competitor-read: {len(lists['gaps_to_own'])} gaps · "
          f"{len(lists['winners_common_h2s'])} table-stakes · {len(lists['winners_drift'])} drift warnings")
    return lists


def run(slug, asset, angle, hub="", redo=False):
    """Step 2a: build (or reuse) the working spine. Needs the world (Step −1) + the winners study.
    Returns the spine.json path."""
    proof_dir = os.path.join(config.DFS_OUT, hub, slug, "proof")
    if not os.path.exists(os.path.join(proof_dir, "05-winners.md")):
        raise SystemExit(f"   ! spine step needs {proof_dir}/05-winners.md — DataForSEO must run first")

    outp = _spine_path(slug, hub)
    cur = _load(outp)
    if not (cur.get("about") and cur.get("not_about")):     # world missing (legacy resume) — build it now
        world(slug, asset, angle, hub, redo=False)
        cur = _load(outp)
    if cur.get("spine") and not redo:
        print(f"   · spine cached ({outp})")
        return outp

    lists = _competitor_read(proof_dir, redo=redo)
    prompt = (llm.load_prompt("build-spine.md")
              .replace("{{TITLE}}", asset)
              .replace("{{ANGLE}}", angle or "(no distinct angle recorded)")
              .replace("{{ABOUT}}", cur["about"])
              .replace("{{NOT_ABOUT}}", cur["not_about"])
              .replace("{{BRAND}}", config.BRAND)
              .replace("{{ABOUT_BRAND}}", config.ABOUT or "(no description on file)")
              .replace("{{GAPS}}", _render(lists["gaps_to_own"]))
              .replace("{{COMMON_H2S}}", _render(lists["winners_common_h2s"]))
              .replace("{{DRIFT}}", _render(lists["winners_drift"])))
    sp = ""
    for _ in range(2):                       # same field-level retry as the world step
        got = llm.call_json(prompt) or {}
        sp = str(got.get("spine") or "").strip()
        if sp:
            break
    if not sp:
        raise SystemExit("   ! build-spine returned an empty spine twice — not writing a half spine")

    config.write_json(outp, {**cur, "title": asset, "angle": angle or "", "spine": sp})
    print(f"   spine: {sp[:100]}...")
    return outp


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Build the world and/or spine for one topic (standalone/testing).")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--asset", required=True)
    ap.add_argument("--angle", default="")
    ap.add_argument("--hub", default="")
    ap.add_argument("--world-only", action="store_true", help="run Step −1 only (no winners study needed)")
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    if a.world_only:
        world(a.slug, a.asset, a.angle, a.hub, redo=a.redo)
    else:
        run(a.slug, a.asset, a.angle, a.hub, redo=a.redo)
