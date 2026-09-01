#!/usr/bin/env python3
"""Architect Step 5 — HEADINGS: write the final heading for every section, then the H1.

Built 2026-08-04, replacing place_keywords.py. That step solved a matching puzzle — "research picked 8
keywords against a planned outline, the real article has 12 different sections, which goes where?" —
in ONE call over the whole article, with no evidence in front of it. Step 4 (section_keywords.py) now
researches a keyword per REAL section from that section's own cards, so the puzzle is gone. What is
left is wording, and wording is done best with the evidence in view.

So this runs ONE CALL PER SECTION, in parallel. Each call sees that section's full cards, its own
researched keyword, the leftover pool, and the primary + variations — and is free to use none of them.
Then one final call writes the H1, having seen every finished heading.

Then 5b reads all the finished headings AS A SET and edits them — the cross-section pass. Added
2026-08-06 after a real run showed exactly what the per-section writers cannot see: numbering that ran
1-5 then jumped to 16, one instrument called "BARS" in one heading and its full name in another, and
Title Case and sentence case mixed inside one article. The coherence step found two of these in the
finished draft and could not fix them, because headings belong to the architect. This is where they
belong. It runs BEFORE a word of the body exists, so an edit here costs nothing downstream.

DELIBERATELY NOT HERE:
  · Replacing the primary. Research picked it from real search data with a world-check; second-guessing
    that from inside the architect is a weaker decision overriding a better-informed one.

Reads:  architect/structure.json · architect/_work/section-keywords.json · gather/plan-inputs.json.
Writes: architect/structure.json (headings, h1, keywords block) · _work/structure.pre-headings.json
        (the baseline, written once) · _work/heading-map.json (the full decision record).
"""
import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

import article_ctx
import config
import llm
import section_keywords as sk
import shape

MAX_HEADING_CHARS = 60          # a soft target: over-length is RECORDED, never rejected (see run())


def _fill(name, **kw):
    p = llm.load_prompt(name)
    for k, v in kw.items():
        p = p.replace("{{" + k + "}}", str(v))
    return p


def _write_one(n, sec, ctx, ks, found, pool, idx):
    """One section's heading. Returns the decision record; never raises (a failure keeps the draft)."""
    head, job = sec.get("headline") or "", sec.get("job") or "(none)"
    rec = {"n": n, "was": head, "heading": head, "keyword_used": None, "changed": False, "why": ""}
    kw = (found or {}).get("keyword")
    try:
        out = llm.call_json(_fill("write-heading.md",
                                  TITLE=ctx["title"] or "(untitled)",
                                  ANGLE=ctx["angle"] or "(none recorded)",
                                  SPINE=ctx["spine"] or "(not available)",
                                  PRIMARY=ks.get("primary") or "(none)",
                                  PERSONA=ctx["persona"],
                                  VARIATIONS=", ".join(ks.get("variations") or []) or "(none)",
                                  HEADING=head, JOB=job,
                                  SECTION_KEYWORD=(f"{kw} (vol {found.get('volume')}, KD {found.get('kd')})"
                                                   if kw else "(none found for this section)"),
                                  # The block is BUILT here, not toggled in the prompt: a section
                                  # that maps to nothing gets no block at all, so there is no list
                                  # to ignore and no match for it to invent.
                                  COVERS_BLOCK=_covers_block(sec.get("covers")),
                                  POOL="\n".join(f"  - {p}" for p in pool) or "  (none left)",
                                  CARDS=sk.render_cards(sec, idx))) or {}
    except Exception as e:
        rec["why"] = f"heading call failed ({str(e)[:80]}) — draft kept"
        return rec

    new = str(out.get("heading") or "").strip()
    if not new:
        rec["why"] = "empty heading returned — draft kept"
        return rec

    used = str(out.get("keyword_used") or "").strip() or None
    # GUARD (corruption, not quality): it may only claim a keyword it was actually shown.
    offered = {p.lower() for p in pool}
    offered |= {(ks.get("primary") or "").lower()} | {v.lower() for v in (ks.get("variations") or [])}
    if kw:
        offered.add(kw.lower())
    if used and used.lower() not in offered:
        rec.update(heading=head, why=f"claimed keyword {used!r} was never offered — draft kept")
        return rec

    rec.update(heading=new, keyword_used=used, changed=(new != head),
               why=str(out.get("why") or "").strip(), chars=len(new))
    return rec


def _flat(s):
    """Lowercased, punctuation stripped, single-spaced — the form a locked keyword is checked in."""
    return " ".join(re.findall(r"[a-z0-9]+", str(s or "").lower()))


def _holds(heading, keyword):
    """True when `heading` still carries the keyword's words, in order, next to each other.

    Deliberately blind to case and punctuation: the pass is allowed to recase a heading to match the
    rest of the list, and to hyphenate ("Type-D" for "type d"), and neither loses the phrase. It is
    also blind to a trailing plural — a heading reading "Rating Scales" still carries "rating scale",
    and search treats them as one phrase. What it will NOT allow is a changed or reordered word:
    "Cost of a Hire" does not carry "cost per hire".
    """
    k = _flat(keyword)
    return (not k) or k in _flat(heading)


# A FIGURE IN A HEADING (2026-08-27, Devansh). A digit that a reader reads as a statistic: a
# percentage, a count, a year, a money figure, a range. Deliberately NOT an ordinal ("Step 2") or a
# number inside a name ("Fortune 500", "Type D", "ISO 27001"), which are part of the thing's name and
# carry none of the spreadsheet feeling this rule exists to stop.
_NAMED_NUMBER = re.compile(
    r"(?:fortune|iso|type|tier|level|section|step|part|chapter|covid|gpt|g)[\s-]*\d+", re.I)
_FIGURE = re.compile(r"\d")


def _has_figure(heading):
    """True when the heading carries a figure a reader reads as a statistic."""
    return bool(_FIGURE.search(_NAMED_NUMBER.sub("", str(heading or ""))))


def _pass_all(ctx, ks, secs, recs):
    """5b — read every heading as a SET and edit them. Returns (applied_count, notes, per-heading log).

    Guarded PER HEADING, not per reply: one heading that drops its locked keyword is reverted on its
    own and the rest of the pass still lands. A malformed or failed call leaves all 20 alone.
    """
    # WHICH PHRASES ARE OVER-USED (2026-08-09). Only this step can know: 5a writes every heading in
    # parallel and blind, so each writer is offered the primary, each honestly says "yes it fits", and
    # nobody counts. Code counts here; the AI decides WHICH copies to keep, because it is the only
    # thing that can see all the headings at once and judge where the phrase genuinely earns its place.
    cap = config.MAX_HEADINGS_PER_KEYWORD
    counts = {}
    for r in recs:
        if r.get("keyword_used"):
            counts[r["keyword_used"]] = counts.get(r["keyword_used"], 0) + 1
    overused = {k: n for k, n in counts.items() if n > cap}

    lines = []
    for sec, r in zip(secs, recs):
        lines.append(f"  {r['n']}. {r['heading']}")
        # the job in FULL (2026-08-09). It used to be cut at 150 characters, which sliced most jobs
        # mid-sentence — and the job is the only thing stopping this pass writing a heading the
        # section cannot pay off, so handing it half a sentence undercut the one guard it has.
        lines.append(f"       job: {sec.get('job') or '(none)'}")
        kw = r.get("keyword_used")
        if kw and kw in overused:
            lines.append(f'       OVER-USED — "{kw}" is in {overused[kw]} of these headings. '
                         f"You may take it out of this one.")
        elif kw:
            lines.append(f'       LOCKED — this phrase must survive: "{kw}"')

    if overused:
        block = "\n".join(f'  · "{k}" is in {n} headings — keep it in at most {cap}, strip it from the other {n - cap}'
                          for k, n in sorted(overused.items(), key=lambda x: -x[1]))
        print(f"    over-used phrase(s): {', '.join(f'{k!r} x{n}' for k, n in overused.items())}")
    else:
        block = "  (none — no phrase is in more than %d headings, so every LOCKED phrase is untouchable)" % cap

    # HOW MANY HEADINGS CARRY A FIGURE. Same shape as the over-used-keyword count above, and for the
    # same reason: 5a writes them blind and in parallel, so only this step can see the total.
    fig_cap = max(1, int(len(recs) * config.FIGURE_HEADING_SHARE))
    numbered = [r["n"] for r in recs if _has_figure(r["heading"])]
    if len(numbered) > fig_cap:
        fig_block = (f"  · {len(numbered)} of these {len(recs)} headings carry a figure "
                     f"(headings {', '.join(str(n) for n in numbered)}).\n"
                     f"  · At most {fig_cap} may keep one. Take the figure out of at least "
                     f"{len(numbered) - fig_cap} of them.")
        print(f"    figure-heavy: {len(numbered)}/{len(recs)} headings carry a number (cap {fig_cap})")
    else:
        fig_block = (f"  · {len(numbered)} of these {len(recs)} headings carry a figure, which is within "
                     f"the limit of {fig_cap}. Nothing to strip — do not add one either.")
    try:
        out = llm.call_json(_fill("heading-pass.md",
                                  TITLE=ctx["title"] or "(untitled)",
                                  ANGLE=ctx["angle"] or "(none recorded)",
                                  SPINE=ctx["spine"] or "(not available)",
                                  PRIMARY=ks.get("primary") or "(none)",
                                  PERSONA=ctx["persona"],
                                  KEYWORD_CAP=cap, OVERUSED=block,
                                  FIGURE_CAP=fig_cap, FIGURE_HEAVY=fig_block,
                                  HEADINGS="\n".join(lines))) or {}
    except Exception as e:
        print(f"    ! heading pass failed ({str(e)[:70]}) — every heading kept as written")
        return 0, "", []

    by_n = {}
    for h in (out.get("headings") or []):
        if isinstance(h, dict) and str(h.get("heading") or "").strip():
            try:
                by_n[int(h["n"])] = h
            except (KeyError, TypeError, ValueError):
                pass
    if not by_n:
        print("    ! heading pass returned nothing usable — every heading kept as written")
        return 0, "", []

    # THE FLOOR, checked before anything is applied (2026-08-09). An over-used phrase may be stripped
    # from individual headings, so the per-heading guard cannot protect it any more. This does: for
    # each over-used phrase, count how many headings would STILL carry it after the pass. If that
    # falls below the cap, the pass has thrown away a keyword we paid for, and the whole thing is
    # refused. At most `cap` is what we ASK for; at least `cap` is what code ENFORCES.
    starved = {}
    for kw in overused:
        survives = sum(1 for r in recs
                       if r.get("keyword_used") == kw
                       and _holds(str((by_n.get(r["n"]) or {}).get("heading") or r["heading"]).strip(), kw))
        if survives < cap:
            starved[kw] = survives
    if starved:
        for kw, n in starved.items():
            print(f"    !! the pass left {kw!r} in only {n} heading(s), below the floor of {cap} — "
                  f"every heading kept as written")
        return 0, "", [{"n": 0, "kept": True,
                        "why": f"pass refused: {starved} fell below the floor of {cap} heading(s)"}]

    applied, log = 0, []
    for r in recs:
        h = by_n.get(r["n"])
        if not h:
            continue
        new, was = str(h["heading"]).strip(), r["heading"]
        if new == was:
            continue
        # A HEADING MAY LOSE A FIGURE HERE. IT MAY NEVER GAIN ONE. Reverted per heading, not as a
        # whole pass: refusing the pass would put back the number-heavy originals, which is the very
        # thing this rule exists to remove. So a bad edit costs one heading and the rest still land.
        if _has_figure(new) and not _has_figure(was):
            log.append({"n": r["n"], "was": was, "proposed": new, "kept": True,
                        "why": "added a figure to a heading that had none — original put back"})
            print(f"    !! {r['n']:2}. reverted (added a figure)")
            continue
        kw = r.get("keyword_used")
        # an over-used phrase is NOT guarded per heading — the whole point is that this pass may take
        # it out of the surplus. The floor above is what protects it instead.
        if kw and kw not in overused and not _holds(new, kw):
            log.append({"n": r["n"], "was": was, "proposed": new, "kept": True,
                        "why": f"dropped its locked keyword {kw!r} — original put back"})
            print(f"    !! {r['n']:2}. reverted (lost the keyword {kw!r})")
            continue
        if kw and kw in overused and not _holds(new, kw):
            r["keyword_used"] = None          # it genuinely no longer carries it; keep the record honest
            print(f"    {r['n']:2}. dropped the over-used {kw!r}")
        log.append({"n": r["n"], "was": was, "heading": new, "kept": False,
                    "why": str(h.get("why") or "").strip()})
        r["heading"], r["changed"], applied = new, True, applied + 1
        print(f"    {r['n']:2}. {was[:52]}\n        -> {new[:52]}  ({str(h.get('why') or '')[:56]})")

    # Did it actually get under the cap? Reported, never enforced by refusal — see the revert note
    # above. A line in the log is what a reviewer needs; throwing the pass away would make it worse.
    left = [r["n"] for r in recs if _has_figure(r["heading"])]
    if len(left) > fig_cap:
        print(f"    !! {len(left)}/{len(recs)} headings still carry a figure, over the cap of {fig_cap} "
              f"(headings {', '.join(str(n) for n in left)})")
        log.append({"n": 0, "kept": True,
                    "why": f"figure-heavy: {len(left)} of {len(recs)} headings still carry a number, "
                           f"cap is {fig_cap}"})
    return applied, str(out.get("notes") or "").strip(), log


_COVERS = """
════════════════════════════════════════════════════════════════════════
THE WORDS PEOPLE ARE SEARCHING FOR

This section covers a topic almost every ranking page covers:  {topic}

Its heading must carry that topic's own words. Not instead of your angle — as well.

   Topic:      Formula / how to calculate it
   Angle only: "The SHRM Formula, and Where It Stops Counting"
   Words only: "How to Calculate Cost Per Hire"
   Both:       "How to Calculate Cost Per Hire, and Where It Stops"

A reader scanning is hunting the words already in their head. Clever without them means they
never find the section that answers their question, and neither does a search engine.

THE ANGLE IS NOT COMPULSORY. Where the plain words say it best, use the plain words and stop.
"How to Calculate Cost Per Hire" is a good heading. A heading forced to carry an angle it does
not need reads worse than a plain one, and an article whose every heading is built the same way
is exhausting to scan.
"""


def _covers_block(topic):
    """The searchable-words rule, or nothing at all.

    Until 2026-08-26 the headings step — which writes the PUBLISHED heading — saw no research at
    all, so it renamed "Formula / how to calculate it" into "The SHRM Formula, and Where It Stops
    Counting" with no idea it had just dropped the phrase every ranking page uses. Zero of nine
    headings on that article carried a searchable phrase.
    """
    topic = (topic or "").strip()
    return _COVERS.format(topic=topic) if topic else ""


def _write_h1(ctx, ks, planned_h1, headings):
    try:
        out = llm.call_json(_fill("write-h1.md",
                                  H1=planned_h1 or "(none)",
                                  ANGLE=ctx["angle"] or "(none recorded)",
                                  SPINE=ctx["spine"] or "(not available)",
                                  PRIMARY=ks.get("primary") or "(none)",
                                  VARIATIONS=", ".join(ks.get("variations") or []) or "(none)",
                                  HEADINGS="\n".join(f"  {i + 1}. {h}" for i, h in enumerate(headings)))) or {}
    except Exception as e:
        print(f"    ! H1 call failed ({str(e)[:70]}) — keeping the planned H1")
        return planned_h1, "H1 call failed"
    h1 = str(out.get("h1") or "").strip()
    return (h1 or planned_h1), str(out.get("why") or "").strip()


def run(slug, redo=False):
    outp = config.artifact(slug, "structure.json")
    st = json.load(open(outp))
    if st.get("keywords") and not redo:
        print("  reusing the written headings (--redo to rewrite)")
        return st

    # A redo must start from the ORIGINAL shaped headings, not the previous run's rewritten ones —
    # otherwise each rerun reads its own edits back and compounds. The snapshot is only valid for THIS
    # run: a stale one (older than the shaped structure) is discarded, never restored.
    work = config.architect_work_dir(slug)
    pre_p = os.path.join(work, "structure.pre-headings.json")
    shaped_p = os.path.join(work, "structure.shaped.json")
    if os.path.exists(pre_p):
        if (not os.path.exists(shaped_p)) or os.path.getmtime(pre_p) >= os.path.getmtime(shaped_p):
            st = json.load(open(pre_p))
        else:
            print("  (ignoring a pre-headings snapshot from an earlier run — using this run's structure)")

    secs = st.get("sections") or []
    ctx = article_ctx.article_context(slug, st)
    ks = sk._keyword_set(slug)
    idx = sk._card_index(slug)

    skp = os.path.join(work, "section-keywords.json")
    found_by_n = {}
    if os.path.exists(skp):
        for r in json.load(open(skp)).get("sections") or []:
            if r.get("pick"):
                found_by_n[int(r["n"])] = r["pick"]
    else:
        print("  ! no section-keywords.json — writing headings without researched section keywords")

    pool = [p for p in (ks.get("secondaries") or []) if p]

    print(f"  == 5a headings == ({len(secs)} sections, {len(found_by_n)} with a researched keyword)")
    with ThreadPoolExecutor(max_workers=llm.max_workers()) as ex:
        recs = list(ex.map(lambda t: _write_one(t[0] + 1, t[1], ctx, ks, found_by_n.get(t[0] + 1), pool, idx),
                           list(enumerate(secs))))

    for r in recs:
        mark = f"[{r['keyword_used']}]" if r["keyword_used"] else "[—]"
        print(f"    {r['n']:2}. {mark:34} {r['heading'][:60]}  ({len(r['heading'])}c)")

    # 5b — the only step that sees all the headings at once. Runs before the H1, so the H1 is written
    # against the final list, and before the body, so an edit here costs nothing downstream.
    print(f"  == 5b heading pass == (all {len(recs)} read together)")
    n_pass, pass_notes, pass_log = _pass_all(ctx, ks, secs, recs)
    print(f"    {n_pass} heading(s) edited across the set" + (f" | {pass_notes[:90]}" if pass_notes else ""))

    long_ones = []
    for sec, r in zip(secs, recs):
        sec["headline"] = r["heading"]
        if len(r["heading"]) > MAX_HEADING_CHARS:
            long_ones.append((r["n"], len(r["heading"]), r["heading"]))

    if not os.path.exists(pre_p):                    # the baseline is written ONCE, never overwritten
        config.write_json(pre_p, json.loads(json.dumps(st)))

    print("  == 5c H1 ==")
    plan_p = config.artifact(slug, "article-plan.json")
    planned_h1 = (json.load(open(plan_p)).get("h1") or "") if os.path.exists(plan_p) else (st.get("h1") or "")
    h1, why_h1 = _write_h1(ctx, ks, planned_h1, [r["heading"] for r in recs])
    st["h1"] = h1
    print(f"    {h1}  ({len(h1)}c)" + ("" if h1 != planned_h1 else "  (unchanged)"))

    # --- the keywords block, computed in CODE (no AI decides these) -----------
    # section_keywords = ONLY phrases that actually landed in a final heading. Nothing from the research
    # phase gets in for merely existing. `relevant` was REMOVED 2026-08-04 (with its blend.md slot).
    used = []
    for r in recs:
        k = r.get("keyword_used")
        if k and k not in used:
            used.append(k)
    st["keywords"] = {"primary": ks.get("primary") or "",
                      "primary_changed": False,          # kept for downstream shape; the primary is research's
                      "why_primary": "",
                      "variations": ks.get("variations") or [],
                      "section_keywords": used,
                      "unplaced": [{"keyword": p, "why": "no section's heading took it"}
                                   for p in pool if p not in used]}

    config.write_json(outp, st)
    config.write_json(os.path.join(work, "heading-map.json"),
                      {"context": ctx, "researched_set": ks, "found_per_section": found_by_n,
                       "headings": recs, "h1_planned": planned_h1, "h1_final": h1, "why_h1": why_h1,
                       "cross_section_pass": {"edited": n_pass, "notes": pass_notes, "changes": pass_log},
                       "over_length": [{"n": n, "chars": c, "heading": h} for n, c, h in long_ones],
                       "decision": st["keywords"]})
    try:
        shape.render_md(slug, st, json.load(open(plan_p)) if os.path.exists(plan_p) else {})
    except Exception as e:
        print(f"    (structure.md re-render skipped: {str(e)[:70]})")

    changed = sum(1 for r in recs if r["changed"])
    print(f"  headings rewritten: {changed}/{len(recs)} ({n_pass} of them by the cross-section pass) | "
          f"keywords in headings: {len(used)} | pool unused: {len(st['keywords']['unplaced'])}")
    if long_ones:
        print(f"  !! {len(long_ones)} heading(s) over {MAX_HEADING_CHARS} chars (kept, recorded in heading-map.json):")
        for n, c, h in long_ones[:5]:
            print(f"       #{n} ({c}c) {h[:70]}")
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Architect Step 5 — write the final headings + H1.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    run(a.slug, redo=a.redo)
