#!/usr/bin/env python3
"""Step 1b — THE TOPIC GATE: is this topic ours, and what is the real angle?

Reads:  <dfs run_dir>/proof/04-serp-snapshot.md   (who ranks + Google's own answer)
        <dfs run_dir>/proof/07-competitor-read.json (the winners lists — same extraction Step 2a uses)
        the brand scope (config.BRAND_SCOPE)
        the topic's current angle, from the queue row
Writes: <dfs run_dir>/proof/08-topic-gate.json — the verdict, both calls, and the angle it replaced

WHY IT SITS HERE. DataForSEO has just finished, so the real search results exist; STORM has not
started, so nothing expensive has been spent. Both questions need the same material and this is the
first moment it is all on disk.

TWO CALLS, NOT ONE, AND THE ORDER MATTERS.
  1. IS THIS OURS?  Sees the brand scope, who ranks, Google's answer, and what every page covers.
     It deliberately does NOT see the gaps. Hand a judge a list of openings nobody has taken and it
     will talk itself into "worth doing" — that is material belonging to the other question, and it
     can only push the verdict one way.
  2. WHAT IS THE ANGLE?  Only runs when the first says yes. Sees the gaps, and replaces the angle
     written months ago, before anyone had seen this search.

A "no" is terminal and cheap: the row is marked in the sheet with the reason, and STORM never runs.
"""
import argparse
import json
import os
import re

import config
import llm
import spine
import topic_pick


def _section(md, heading):
    """One **bold-headed** block out of the SERP snapshot, without its heading."""
    m = re.search(rf"^\*\*{re.escape(heading)}\*\*[^\n]*\n(.*?)(?=^\*\*|\Z)", md, re.M | re.S)
    return m.group(1).strip() if m else ""


def _who_ranks(md):
    """The 'who ranks' block, with any gap line taken OUT.

    The snapshot's own who-ranks block ends with an 'Open gap:' line. That is gap material, and the
    relevance call must not see it — see the two-calls note at the top.
    """
    body = _section(md, "Who ranks:")
    kept = [ln for ln in body.splitlines() if not re.match(r"\s*-\s*Open gap\b", ln, re.I)]
    return "\n".join(kept).strip()


def _ai_overview(md):
    return _section(md, "AI Overview") or "(no AI Overview captured for this search)"


def _render(items):
    return "\n".join(f"  - {i}" for i in items) if items else "  (none listed)"


def run(slug, asset, angle, hub="", redo=False):
    """Returns {relevant, why, angle, angle_changed, why_changed}. Never writes to the queue —
    the conductor owns that, so this stays a judgement and nothing else."""
    proof = os.path.join(config.DFS_OUT, hub, slug, "proof")
    outp = os.path.join(proof, "08-topic-gate.json")
    if os.path.exists(outp) and not redo:
        v = json.load(open(outp))
        print(f"   · topic gate cached — relevant={v.get('relevant')}")
        return v

    snap_p = os.path.join(proof, "04-serp-snapshot.md")
    if not os.path.exists(snap_p):
        raise SystemExit(f"   ! topic gate needs {snap_p} — DataForSEO must run first")
    snap = open(snap_p).read()
    scope = open(config.BRAND_SCOPE).read() if os.path.exists(config.BRAND_SCOPE) else ""
    if not scope:
        print("   !! no brand-scope.md — the relevance call would be judging blind. Passing the topic.")
        return {"relevant": True, "why": "not judged — no brand scope on file",
                "angle": angle, "angle_changed": False, "why_changed": ""}

    # The winners lists. spine.py caches these to 07-competitor-read.json, and Step 2a reads the same
    # file straight after, so running it here costs one call for both of us rather than two.
    lists = spine._competitor_read(proof, redo=redo)
    common = _render(lists["winners_common_h2s"])

    # ---- call 1: is this ours? -------------------------------------------------
    p1 = (llm.load_prompt("topic-relevance.md")
          .replace("{{BRAND}}", config.BRAND)
          .replace("{{BRAND_SCOPE}}", scope)
          .replace("{{WHO_RANKS}}", _who_ranks(snap) or "(no ranking summary captured)")
          .replace("{{AI_OVERVIEW}}", _ai_overview(snap))
          .replace("{{COMMON_TOPICS}}", common))
    got = llm.call_json(p1) or {}
    relevant = bool(got.get("relevant"))
    why = str(got.get("why") or "").strip()
    if "relevant" not in got:
        # Fail OPEN. A gate that silently drops topics because a call came back malformed is worse
        # than a gate that lets one through: the article is reviewed, a dropped topic is not.
        print("   !! relevance call returned no verdict — passing the topic through")
        relevant, why = True, "not judged — the relevance call returned no verdict"

    verdict = {"relevant": relevant, "why": why, "angle": angle,
               "angle_changed": False, "why_changed": "", "angle_before": angle}
    if not relevant:
        config.write_json(outp, verdict)
        print(f"   NOT OURS — {why}")
        return verdict
    print(f"   ours to write — {why}")

    # ---- call 2: what is the real angle? ---------------------------------------
    p2 = (llm.load_prompt("topic-angle.md")
          .replace("{{BRAND}}", config.BRAND)
          .replace("{{OLD_ANGLE}}", angle or "(none recorded)")
          .replace("{{GAPS}}", _render(lists["gaps_to_own"]))
          .replace("{{COMMON_TOPICS}}", common)
          .replace("{{AI_OVERVIEW}}", _ai_overview(snap)))
    new = ""
    for _ in range(2):                      # a parse-clean reply with an empty field still slips through
        got2 = llm.call_json(p2) or {}
        new = str(got2.get("angle") or "").strip()
        if new:
            break
    if new:
        verdict.update(angle=new, angle_changed=new != (angle or ""),
                       why_changed=str(got2.get("why_changed") or "").strip())
        print(f"   angle: {new[:120]}")
        if verdict["why_changed"]:
            print(f"     (was missing: {verdict['why_changed'][:100]})")
    else:
        print("   !! the angle call came back empty twice — keeping the angle it had")

    config.write_json(outp, verdict)
    return verdict


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Step 1b — is this topic ours, and what is the real angle?")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--hub", default="")
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    row = topic_pick.read_queue()
    r = next((x for x in row if x["slug"] == a.slug), {})
    v = run(a.slug, r.get("asset", ""), r.get("angle", ""), a.hub, a.redo)
    print(json.dumps(v, indent=2))
