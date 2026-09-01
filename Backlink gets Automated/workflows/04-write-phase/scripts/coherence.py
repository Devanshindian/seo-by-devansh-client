#!/usr/bin/env python3
"""Writer Step 4 — COHERENCE: the first and only step that reads the finished article WHOLE.

Every section is written by a different call, in parallel, none able to see the others. So faults
that live BETWEEN sections cannot be caught by any earlier step: the article states a rule in
section 7 and breaks it in section 5, or scores one thing on 1-5 here and 0-2-4 there. Every
section reads perfectly well alone. Nobody ever held both.

REBUILT 2026-08-05, second design. The first one asked ONE call to read a 5,000-word article and
"find anywhere it contradicts itself", then return before/after sentence pairs for code to apply.
It failed twice over, and both failures are worth recording:

  1. IT COULD NOT SEE. One finding across four articles, three "internally consistent" verdicts on
     articles that provably contain five scoring scales, a 5-6-vs-3-6 rule clash, a counselling
     recommendation that contradicts the article's own legal warning, and a 19% drop described as
     "essentially flat". The one thing it DID find was a broken promise in the intro — the only
     fault that needed no searching. Asking a model to work out what to look for AND find it, in
     one pass, is a needle hunt with no needle specified.
  2. IT COULD NOT FIX. Sentence pairs can only express a one-place edit. The hackathon article uses
     0-2-4 in ten places with worked examples attached; that fix is not expressible as a pair, so
     the design could not make it even in principle.

So: give it the list first, and let it return the whole article.

  Step 1  INVENTORY (coherence-inventory.md) — pure transcription, no judgement: every rule,
          scale and quantity, with where each appears and HOW OFTEN. Four scales in one column is
          the finding; nobody has to be clever.
  Step 2  EDIT (coherence-edit.md) — the article plus that list, returns the WHOLE article edited.
          Free to reach across sections, which is the only way scale drift gets fixed.
  Step 3  DIFF in code — we MEASURE what changed rather than trusting it to report. It cannot
          under-report, because there is no report; there is a diff.
  Step 4  GUARDS in code, ALL-OR-NOTHING. Numbers, source tags, headings, section count, length.
          Any failure and the ORIGINAL publishes unchanged, loudly logged. No partial application:
          either the whole edit is trustworthy or none of it is used.

The per-edit AI verifier from the first design is gone — it judged one pair at a time, which no
longer exists. Its job is now done by the aggregate guards, which are stronger: they check the
finished article rather than one proposed change.

TWO CHANGES ON 2026-08-11 (Devansh):
  · PROMISE-NOT-KEPT was dropped as a fault, and "promises" with it from the inventory. Four faults
    now, not five. It cost the step its strongest single result: three of the strategic article's
    four fixes were broken promises, one of them inserting an interview question missing entirely
    from an article about interview questions.
  · A WORD BUDGET went into the prompt, {{WORD_TOLERANCE}}%, which was a placeholder the code had
    been filling and the prompt had never used. WORD_TOLERANCE dropped 10 -> 5 so the flag matches
    what the editor is told. It stays a WARNING: a version that discarded the edit for going over
    was written and deliberately left out, because an editor afraid of the ceiling skips the fix
    that needed room.

WHERE IT SITS — after the wrapper, before the slop pass:
  · after the wrapper, the first moment the intro, FAQ and close exist
  · before links, whose anchors are matched against exact sentences and would break
  · before slop, so anything clumsy it writes still gets style-cleaned

Reads:  writer/_work/wrapper.json + gather/plan-inputs.json (persona) + the article context.
Writes: writer/_work/coherent.json         — wrapper.json's shape, edited (slop reads this)
        writer/_work/coherence-report.json — the inventory, the measured diff, the guard verdict
"""
import argparse
import difflib
import json
import os
import re

import article_ctx
import config
import llm
import tags

# % the length may move. Dropped 10 -> 5 on 2026-08-11 when the prompt gained a word budget: the
# prompt now tells the editor {{WORD_TOLERANCE}}%, so the flag has to be the same number or the
# review page shrugs at an article that ignored the instruction. Still a WARNING, never a block.
WORD_TOLERANCE = int(os.environ.get("COHERENCE_WORD_TOLERANCE", "5"))
# This step sends the WHOLE article twice and the second call writes the whole article back — 5,600
# words in, 5,600 out. The repo-wide 300s LLM timeout is sized for one section and kills that mid-
# thought, so a run burns three attempts producing nothing and silently falls back to a lesser model.
TIMEOUT = int(os.environ.get("COHERENCE_TIMEOUT", "1200"))
# Digits, optional thousand separators, optional decimal part — but NEVER a trailing . or ,
# The greedy version captured "5." and "4," as distinct numbers, so a sentence rewritten to end
# on a figure looked like fabrication and blocked the whole edit. Third guard bug of the day.
_NUMS = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def _fill(name, **kw):
    p = llm.load_prompt(name)
    for k, v in kw.items():
        p = p.replace("{{" + k + "}}", str(v))
    return p


def _render(w):
    """The whole article as the editor sees it — the order the reader gets."""
    L = [f"# {w.get('h1') or ''}", "", w.get("intro") or ""]
    if w.get("quick_answer"):
        L += ["", "## Quick answer", "", w["quick_answer"]]
    for s in w.get("sections") or []:
        L += ["", f"## {s['heading']}", "", s.get("prose") or ""]
    if w.get("faq"):
        L += ["", "## Frequently asked questions"]
        for f in w["faq"]:
            L += ["", f"**{f.get('question','')}**", "", f.get("answer") or ""]
    if w.get("close_heading"):
        L += ["", f'(the close sits under the heading "{w["close_heading"]}")']
    L += ["", w.get("close") or ""]
    return "\n".join(L)


def _prose_blocks(w):
    """(label, text) for every block a reader sees. Headings excluded — they are not editable."""
    out = [("intro", w.get("intro") or ""), ("quick answer", w.get("quick_answer") or "")]
    out += [(s.get("heading", "?"), s.get("prose") or "") for s in w.get("sections") or []]
    out += [(f"FAQ: {f.get('question','')[:50]}", f.get("answer") or "") for f in w.get("faq") or []]
    out.append(("close", w.get("close") or ""))
    return out


def _all_prose(w):
    return "\n\n".join(t for _, t in _prose_blocks(w))


def _guards(before, after):
    """TIERED, decided with Devansh 2026-08-05.

    BLOCKING — discard the whole edit. Only faults a human CANNOT catch by reading the review page,
    or that no legitimate fix ever needs:
      · a heading or the H1 changed  (the architect researched those against real search data)
      · a section vanished or was emptied
      · a number INVENTED that appears nowhere in the original  (fabrication)
      · a catastrophic tag strip (>25% gone) — that is not editing, that is the model dropping brackets

    NOT BLOCKING, but surfaced loudly on the review page:
      · a few source tags lost — losing one or two while rewriting is acceptable; blocking the whole
        article over it costs more than it saves
      · numbers that CHANGED — because that is the repair. Converting a 0-2-4 rating band to 1-5
        necessarily removes 0,2,4 and adds 1,3,5. The first design blocked exactly this and threw
        away 10 good fixes over it. Changed figures go to the top of the review page instead.

    Returns (blocking_reasons, warnings).
    """
    block, warn = [], []
    ob, oa = _all_prose(before), _all_prose(after)

    # --- BLOCKING: headings, the H1, and section survival are not negotiable -------------------
    hb = [s.get("heading") for s in before.get("sections") or []]
    ha = [s.get("heading") for s in after.get("sections") or []]
    if hb != ha:
        block.append(f"headings changed ({len(hb)} -> {len(ha)}); they belong to the architect")
    if (before.get("h1") or "") != (after.get("h1") or ""):
        block.append("the H1 was changed")
    empty = [s.get("heading") for s in after.get("sections") or [] if not (s.get("prose") or "").strip()]
    if empty:
        block.append(f"{len(empty)} section(s) left empty: {', '.join(str(x)[:40] for x in empty[:3])}")

    # --- BLOCKING: a number that exists NOWHERE in the original is fabrication -----------------
    nb, na = set(_NUMS.findall(ob)), set(_NUMS.findall(oa))
    invented = na - nb
    if invented:
        block.append(f"INVENTED {len(invented)} number(s) absent from the original: "
                     f"{', '.join(sorted(invented)[:6])}")

    # --- BLOCKING only if catastrophic: the tags were stripped rather than edited --------------
    tb, ta = set(tags.ids(ob)), set(tags.ids(oa))
    lost_tags = tb - ta
    if tb and len(lost_tags) / len(tb) > 0.25:
        block.append(f"stripped {len(lost_tags)} of {len(tb)} source tags "
                     f"({round(100 * len(lost_tags) / len(tb))}%) — that is not editing")
    elif lost_tags:
        warn.append({"kind": "source tags lost", "detail": sorted(str(x) for x in lost_tags),
                     "note": "acceptable if those claims were cut; a problem if the claim survived"})

    # --- WARN: every figure whose count moved, so a human sees it ------------------------------
    fb, fa = _NUMS.findall(ob), _NUMS.findall(oa)
    moved = sorted({n for n in set(fb) | set(fa) if fb.count(n) != fa.count(n)})
    if moved:
        warn.append({"kind": "numbers changed", "detail": moved,
                     "note": "a rating band changing is the repair; a statistic changing is a fact change"})

    # --- WARN: length ---------------------------------------------------------------------------
    wb, wa = len(ob.split()), len(oa.split())
    if wb and abs(wa - wb) * 100 / wb > WORD_TOLERANCE:
        warn.append({"kind": "length moved", "detail": [f"{wb} -> {wa} words",
                     f"{round((wa - wb) * 100 / wb):+d}%"], "note": "over the usual tolerance"})
    return block, warn


def _diff(before, after):
    """MEASURE what changed, per block. Not what it claims — what it did."""
    out, bmap = [], dict(_prose_blocks(before))
    for label, new in _prose_blocks(after):
        old = bmap.get(label)
        if old is None or old == new:
            continue
        sm = difflib.SequenceMatcher(None, old.split(), new.split())
        edits = [{"was": " ".join(old.split()[i1:i2]) or "(nothing)",
                  "now": " ".join(new.split()[j1:j2]) or "(cut)"}
                 for tag_, i1, i2, j1, j2 in sm.get_opcodes() if tag_ != "equal"]
        out.append({"block": label, "similarity": round(sm.ratio(), 3), "edits": edits})
    return out


def run(slug, redo=False):
    outp = config.artifact(slug, "coherent.json")
    if not redo and config.fresh(outp, config.artifact(slug, "wrapper.json")):
        print(f"  reusing {os.path.basename(outp)}")
        return json.load(open(outp))

    w = json.load(open(config.artifact(slug, "wrapper.json")))
    ctx = article_ctx.article_context(slug)
    inp = json.load(open(config.artifact(slug, "plan-inputs.json")))
    p = (inp.get("group_a") or {}).get("persona") or {}
    persona = (f"{p.get('name','')} — {p.get('lens','')}".strip(" —") if isinstance(p, dict) else str(p)) \
        or "(no persona on file)"
    article = _render(w)
    report = {"slug": slug}

    def bail(msg, **extra):
        print(f"  ! {msg} — the article passes through unchanged")
        config.write_json(outp, w)
        config.write_json(config.artifact(slug, "coherence-report.json"),
                          {**report, "applied": False, "reason": msg, **extra})
        return w

    # ---- Step 1: the inventory (transcription, not judgement) ----------------------------------
    _prev = os.environ.get("WRITE_LLM_TIMEOUT")
    os.environ["WRITE_LLM_TIMEOUT"] = str(TIMEOUT)
    config.CLAUDE_TIMEOUT = TIMEOUT
    try:
        inv = llm.call_json(_fill("coherence-inventory.md", ARTICLE=article)) or {}
    except Exception as e:
        return bail(f"inventory call failed ({type(e).__name__})")
    report["inventory"] = inv
    counts = {k: len(inv.get(k) or []) for k in ("rules", "scales", "quantities")}
    scale_kinds = {str(s.get("scale", "")).strip().lower() for s in (inv.get("scales") or [])}
    print(f"  inventory: {counts['rules']} rules · {counts['scales']} scale mentions "
          f"({len(scale_kinds)} distinct) · {counts['quantities']} quantities")

    # ---- Step 2: the edit (the whole article back) ---------------------------------------------
    try:
        out = llm.call_json(_fill("coherence-edit.md",
                                  BRAND=config.BRAND, ABOUT=config.ABOUT or "(no description on file)",
                                  H1=w.get("h1") or "", ANGLE=article_ctx.or_na(ctx, "angle"),
                                  SPINE=article_ctx.or_na(ctx, "spine"),
                                  WORLD_ABOUT=article_ctx.or_na(ctx, "about"),
                                  WORLD_NOT_ABOUT=article_ctx.or_na(ctx, "not_about"),
                                  PERSONA=persona, WORD_TOLERANCE=WORD_TOLERANCE,
                                  INVENTORY=json.dumps(inv, indent=2), ARTICLE=article)) or {}
    except Exception as e:
        return bail(f"edit call failed ({type(e).__name__})")

    changes = [c for c in (out.get("changes") or []) if isinstance(c, dict)]
    could_not = [c for c in (out.get("could_not_fix") or []) if isinstance(c, dict)]
    report.update(verdict=str(out.get("verdict") or "").strip(),
                  changes_claimed=changes, could_not_fix=could_not)

    def apply_reply(reply):
        """The reply, folded back into wrapper.json's shape, keeping every field it does not own."""
        n = json.loads(json.dumps(w))
        import readable as _r                     # one definition of "strip a stray heading"
        n["intro"] = _r._strip_heading(str(reply.get("intro") or w.get("intro") or ""))
        if reply.get("quick_answer"):
            n["quick_answer"] = _r._strip_heading(str(reply["quick_answer"]))
        n["close"] = _r._strip_heading(str(reply.get("close") or w.get("close") or ""))
        by_head = {str(s.get("heading", "")): str(s.get("prose") or "")
                   for s in reply.get("sections") or [] if isinstance(s, dict)}
        for s in n.get("sections") or []:
            if s["heading"] in by_head and by_head[s["heading"]].strip():
                s["prose"] = by_head[s["heading"]]
        ans = {str(f.get("question", "")): str(f.get("answer") or "")
               for f in (reply.get("faq") or []) if isinstance(f, dict)}
        for f in n.get("faq") or []:
            if f.get("question") in ans and ans[f["question"]].strip():
                f["answer"] = ans[f["question"]]
        return n

    if not out.get("sections"):
        return bail("the edit returned no sections", verdict=report.get("verdict"))
    new = apply_reply(out)

    # ---- Step 3: MEASURE what changed ----------------------------------------------------------
    diff = _diff(w, new)
    report["diff"] = diff
    n_edits = sum(len(d["edits"]) for d in diff)

    # ---- Step 4: the guards, all or nothing ----------------------------------------------------
    failures, warnings = _guards(w, new)
    report["guard_failures"] = failures
    report["warnings"] = warnings
    report["numbers_changed_claimed"] = [c for c in (out.get("numbers_changed") or []) if isinstance(c, dict)]
    print(f"  edit: {len(diff)} block(s) touched, {n_edits} passage(s) changed | "
          f"claimed {len(changes)} fix(es), {len(could_not)} it could not fix")
    for c in changes:
        print(f"    · {c.get('kind')} in {str(c.get('section'))[:44]}: {str(c.get('what_you_did'))[:70]}")
    for c in could_not:
        print(f"    ! COULD NOT FIX: {str(c.get('what'))[:60]} — {str(c.get('why_not'))[:60]}")

    for wn in warnings:
        print(f"    ~ {wn['kind']}: {', '.join(str(x) for x in wn['detail'][:8])}"
              + (" …" if len(wn["detail"]) > 8 else ""))
    # ---- Step 5: ONE RETRY, added 2026-08-13 ---------------------------------------------------
    # The first time a guard ever fired, it cost 9 good fixes to catch 1 invented number ("32,000",
    # absent from the article). Reverting only the offending SECTION was considered and rejected:
    # this step's best work is cross-section (one scale corrected in ten places), so a partial revert
    # leaves the article MORE inconsistent than doing nothing. A retry has no partial state — either
    # a whole clean article or the original, untouched.
    # It costs one call, and only on a run that was about to be discarded anyway.
    if failures:
        for f in failures:
            print(f"    !! BLOCKED: {f}")
        print("  retrying once, naming exactly what failed")
        try:
            retry = llm.call_json(_fill("coherence-retry.md",
                                        FAILURES="\n".join(f"- {f}" for f in failures),
                                        EDITED=_render(new))) or {}
        except Exception as e:
            retry = {}
            print(f"    ! retry call failed ({type(e).__name__})")
        report["retry_attempted"] = True
        if retry.get("sections"):
            new2 = apply_reply(retry)
            f2, w2 = _guards(w, new2)
            report["retry_failures"] = f2
            if f2:
                for f in f2:
                    print(f"    !! STILL BLOCKED after retry: {f}")
            else:
                print("    retry passed the guards — using it")
                new, failures, warnings, out = new2, [], w2, retry
                diff = _diff(w, new)
                report.update(diff=diff, guard_failures=[], warnings=warnings, retry_worked=True,
                              changes_claimed=[c for c in (retry.get("changes") or []) if isinstance(c, dict)],
                              could_not_fix=[c for c in (retry.get("could_not_fix") or []) if isinstance(c, dict)],
                              verdict=str(retry.get("verdict") or "").strip())
        else:
            print("    ! the retry returned nothing usable")
    if failures:
        return bail("guards failed twice — keeping the original", verdict=report.get("verdict"))

    report["applied"] = True
    config.write_json(outp, new)
    config.write_json(config.artifact(slug, "coherence-report.json"), report)
    print(f"  -> {os.path.basename(outp)} | APPLIED | verdict: {report.get('verdict','')[:80]}")
    return new


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Writer Step 4 — read the whole article, fix what only that reveals.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    run(a.slug, redo=a.redo)
