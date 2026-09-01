#!/usr/bin/env python3
"""Writer Step 2 — BLEND: the editor that reads the whole article and cuts what did not earn its place.

Reads:  writer/_work/body.json (the sections' prose) + architect/structure.json (the spine, and each
        section's JOB) + gather/plan-inputs.json (group_a.keyword_set, group_a.word_band) + the queue row.
Writes: writer/_work/blend.json — the edited sections, the edit list, the measured diff, the measured
        keyword counts, the tag audit and the guard verdict.

REBUILT 2026-08-11, in coherence's shape, for one measured reason: the old design gave the editor five
tiny permitted moves and trusted its self-report. Across four articles it returned "edits: none" on TWO
of them, cut a repetition ZERO times, and reported 6 keywords woven out of a set of 5. Coherence had the
same failure and was fixed by handing the model a list instead of asking it to hunt. Same fix here.

  Step 1  COUNT in code — every sentence over BLEND_SENTENCE_WORDS, every paragraph over
          BLEND_PARA_SENTENCES, the body total against the article's word band. Exact, free, no AI.
  Step 2  EDIT (blend.md) — the article, each section's JOB (which blend never used to see), and that
          list. Eleven faults, most valuable first. Returns the whole article.
  Step 3  MEASURE in code — diff every block, and count the keywords in the finished text. We do not
          trust what it says it did; there is a diff.
  Step 4  GUARDS in code, ALL-OR-NOTHING. Headings, section survival, section count, catastrophic tag
          loss. Any failure and the ORIGINAL body publishes unchanged, loudly logged.

The safety design is unchanged: the editor sees ONLY the prose, never the cards, so it cannot invent a
fact. Code then audits the [c<id>] tags: a tag present after blending that never existed in the body is
an invention -> stripped and logged; tags that disappeared are logged as cut-content.
"""
import argparse
import difflib
import json
import os
import re

import config
import llm
import fmt_router

import tags

# A sentence ends at . ! or ? followed by whitespace. Good enough for counting, and the same shape
# coherence uses. Lines that are markdown table rows or headings are skipped before this ever runs:
# a table row has no full stop, so it counts as one enormous "sentence" and poisons the list.
_SENT = re.compile(r"(?<=[.!?])\s+")


def _prose_lines(text):
    """The lines a reader reads. Headings and table rows are not editable prose, so they never count."""
    out = []
    for ln in str(text or "").split("\n"):
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("|") or set(s) <= set("-| :"):
            continue
        out.append(s)
    return out


_LIST_ITEM = re.compile(r"^(?:[-*+]\s|\d+[.)]\s)")


def _paragraphs(text):
    """Blank-line separated blocks, headings and tables removed.

    Returns (text, is_list). A LIST IS NOT A PARAGRAPH: a four-item bulleted list is four separate
    thoughts a reader takes one at a time, so counting its sentences and calling it a fat paragraph
    is a false positive. Its items are still read for over-long sentences, because a rambling bullet
    is a rambling bullet."""
    out = []
    for block in str(text or "").split("\n\n"):
        lines = _prose_lines(block)
        if not lines:
            continue
        listy = sum(1 for ln in lines if _LIST_ITEM.match(ln)) >= max(2, len(lines) // 2)
        out.append((" ".join(lines), listy))
    return out


def _sentences(para):
    return [s for s in _SENT.split(para.strip()) if s.strip()]


def _count(secs):
    """Everything the counter finds, per section. Returns (long_sentences, fat_paragraphs, totals)."""
    longs, fats, n_sent = [], [], 0
    for s in secs:
        head = s.get("headline") or s.get("heading") or "?"
        for para, listy in _paragraphs(s.get("prose")):
            sents = _sentences(para)
            n_sent += len(sents)
            if not listy and len(sents) > config.BLEND_PARA_SENTENCES:
                fats.append({"section": head, "sentences": len(sents),
                             "opens": " ".join(sents[0].split()[:12])})
            for sent in sents:
                w = len(sent.split())
                if w > config.BLEND_SENTENCE_WORDS:
                    longs.append({"section": head, "words": w, "text": sent})
    return longs, fats, {"sentences": n_sent}


def _flags_block(longs, fats, totals):
    """The counter's list, as the editor reads it. Exact numbers, no judgement."""
    if not longs and not fats:
        return (f"Nothing to report. Every sentence is at or under {config.BLEND_SENTENCE_WORDS} words "
                f"and every paragraph at or under {config.BLEND_PARA_SENTENCES} sentences.\n"
                "Spend your effort on faults 1 to 8 and 11 instead.")
    L = []
    n = totals.get("sentences") or 0
    pct = f" ({round(100 * len(longs) / n)}% of all sentences)" if n else ""
    L.append(f"SENTENCES OVER {config.BLEND_SENTENCE_WORDS} WORDS — {len(longs)} of {n}{pct}")
    by_sec = {}
    for x in longs:
        by_sec.setdefault(x["section"], []).append(x)
    for head, items in by_sec.items():
        L.append(f"  [{head}] {len(items)} of them")
        for x in sorted(items, key=lambda y: -y["words"])[:config.BLEND_FLAG_SAMPLE]:
            L.append(f"    {x['words']}w  \"{x['text'][:150]}\"")
        if len(items) > config.BLEND_FLAG_SAMPLE:
            L.append(f"    ... and {len(items) - config.BLEND_FLAG_SAMPLE} more in this section")
    L.append("")
    L.append(f"PARAGRAPHS OVER {config.BLEND_PARA_SENTENCES} SENTENCES — {len(fats)}")
    for x in fats:
        L.append(f"  [{x['section']}] {x['sentences']} sentences, opens \"{x['opens']}...\"")
    return "\n".join(L)


def _length_facts(secs, band):
    """The length numbers, for the review page. Same arithmetic the prompt is told, kept once."""
    words = sum(len(str(s.get("prose") or "").split()) for s in secs)
    lo, hi = (band or {}).get("min"), (band or {}).get("max")
    if not (lo and hi):
        return {"words": words}
    reserve = config.BLEND_WRAPPER_WORDS
    aim_lo, aim_hi = max(0, lo - reserve), max(0, hi - reserve)
    return {"words": words, "band_min": lo, "band_max": hi, "wrapper_reserve": reserve,
            "aim_min": aim_lo, "aim_max": aim_hi,
            "over_by": max(0, words - aim_hi), "under_by": max(0, aim_lo - words)}


def _length_line(secs, band):
    """What the editor is told about length. A statement of fact, never a quota."""
    words = sum(len(str(s.get("prose") or "").split()) for s in secs)
    lo, hi = (band or {}).get("min"), (band or {}).get("max")
    if not (lo and hi):
        return f"the sections below total {words:,} words. No band was set for this article."
    reserve = config.BLEND_WRAPPER_WORDS
    aim_lo, aim_hi = max(0, lo - reserve), max(0, hi - reserve)
    verdict = ("over that aim by about {:,} words".format(words - aim_hi) if words > aim_hi
               else "under that aim by about {:,} words".format(aim_lo - words) if words < aim_lo
               else "inside that aim")
    return (f"the sections below total {words:,} words. The finished article should land between "
            f"{lo:,} and {hi:,}. An intro, five FAQ answers and a close are written AFTER you and add "
            f"roughly {reserve} words, so the sections need to come in around {aim_lo:,} to {aim_hi:,}. "
            f"Right now they are {verdict}.")


def _jobs_block(st, secs):
    """Each section's job — the brief its writer was given. Blend has never seen these before."""
    by_head = {str(s.get("headline") or ""): s for s in (st.get("sections") or [])}
    L = []
    for i, s in enumerate(secs, 1):
        head = s.get("headline") or "?"
        plan = by_head.get(head) or {}
        job = str(plan.get("job") or "(no job on file)").strip()
        target = plan.get("word_target")
        wrote = len(str(s.get("prose") or "").split())
        t = f"  [target {target}w, written {wrote}w]" if target else f"  [written {wrote}w]"
        L.append(f"{i}. {head}{t}\n   JOB: {job}")
    return "\n".join(L)


def _kw_counts(secs, phrases):
    """Count each phrase in the finished text ourselves. The editor's own report does not add up:
    one article claimed 6 keywords woven out of a set of 5, another 21 out of 13."""
    text = " ".join(str(s.get("prose") or "") for s in secs).lower()
    return {p: len(re.findall(r"\b" + re.escape(p.lower()) + r"\b", text)) for p in phrases if p}


def _diff(before, after):
    """MEASURE what changed, per section. Not what it claims — what it did."""
    out, bmap = [], {s["headline"]: str(s.get("prose") or "") for s in before}
    for b in after:
        old, new = bmap.get(b["heading"]), str(b.get("prose") or "")
        if old is None or old == new:
            continue
        sm = difflib.SequenceMatcher(None, old.split(), new.split())
        edits = [{"was": " ".join(old.split()[i1:i2]) or "(nothing)",
                  "now": " ".join(new.split()[j1:j2]) or "(cut)"}
                 for tag_, i1, i2, j1, j2 in sm.get_opcodes() if tag_ != "equal"]
        out.append({"section": b["heading"], "similarity": round(sm.ratio(), 3), "edits": edits})
    return out


def _guards(secs, result):
    """TIERED, the same shape coherence uses.

    BLOCKING — discard the whole edit and publish the body as written. Only faults a human cannot
    catch by reading the review page, or that no legitimate edit ever needs.
    WARN — surfaced loudly, but the edit still applies.
    """
    block, warn = [], []
    hb = [s.get("headline") for s in secs]
    ha = [s.get("heading") for s in result]
    if len(hb) != len(ha):
        block.append(f"section count changed ({len(hb)} -> {len(ha)})")
    elif hb != ha:
        block.append("headings changed; they belong to the architect")
    empty = [b.get("heading") for b in result if not str(b.get("prose") or "").strip()]
    if empty:
        block.append(f"{len(empty)} section(s) left empty: {', '.join(str(x)[:40] for x in empty[:3])}")

    tb = set()
    for s in secs:
        tb |= tags.id_set(s["prose"])
    ta = set()
    for b in result:
        ta |= tags.id_set(str(b.get("prose") or ""))
    lost = tb - ta
    if tb and len(lost) / len(tb) > config.BLEND_TAG_LOSS_BLOCK:
        block.append(f"stripped {len(lost)} of {len(tb)} source tags "
                     f"({round(100 * len(lost) / len(tb))}%) — that is not editing")
    elif lost:
        warn.append({"kind": "source tags lost", "detail": sorted(str(x) for x in lost),
                     "note": "correct if those claims were cut; a fault if the claim survived"})
    return block, warn


def run(slug, redo=False):
    outp = config.artifact(slug, "blend.json")
    if not redo and config.fresh(outp, config.artifact(slug, "body.json")):
        print(f"  reusing {outp}")
        return json.load(open(outp))

    body = json.load(open(config.artifact(slug, "body.json")))
    st = json.load(open(config.artifact(slug, "structure.json")))
    row = fmt_router._queue_row(slug)
    ga = json.load(open(config.artifact(slug, "plan-inputs.json")))["group_a"]
    # the keyword decision was made ONCE, by the architect's headings step; carry it forward.
    # (an older structure without the block falls back to the research-era set, so old runs still work)
    kw = st.get("keywords") or {}
    ks = ga.get("keyword_set") or {}
    primary = kw.get("primary") or ks.get("primary") or ""
    variations = kw.get("variations") if kw else (ks.get("variations") or [])

    secs = body["sections"]

    # ---- Step 1: COUNT, in code ---------------------------------------------------------------
    longs, fats, totals = _count(secs)
    print(f"  counter: {len(longs)} sentence(s) over {config.BLEND_SENTENCE_WORDS}w of "
          f"{totals['sentences']} · {len(fats)} paragraph(s) over {config.BLEND_PARA_SENTENCES} sentences")

    block = "\n\n".join(f"## {s['headline']}\n\n{s['prose'].split(chr(10), 1)[-1].strip() if s['prose'].startswith('##') else s['prose']}"
                        for s in secs)
    prompt = (llm.load_prompt("blend.md")
              .replace("{{BRAND}}", config.BRAND)
              .replace("{{ABOUT}}", config.ABOUT or "(no description on file)")
              .replace("{{TITLE}}", (row.get("asset") or "").strip() or "(none)")
              .replace("{{ANGLE}}", (row.get("angle") or "").strip() or "(none)")
              .replace("{{SPINE}}", body.get("spine") or st.get("spine") or "(none)")
              .replace("{{LENGTH}}", _length_line(secs, ga.get("word_band")))
              .replace("{{PRIMARY}}", primary or "(none)")
              .replace("{{VARIATIONS}}", ", ".join(variations or []) or "(none)")
              .replace("{{JOBS}}", _jobs_block(st, secs))
              .replace("{{FLAGS}}", _flags_block(longs, fats, totals))
              .replace("{{SECTIONS}}", block))

    # ---- Step 2: the edit ----------------------------------------------------------------------
    out = llm.call_json(prompt) or {}
    blended = [b for b in (out.get("sections") or []) if isinstance(b, dict)]

    def keep_original(reason):
        print(f"  !! {reason} — keeping the body as written")
        return [{"heading": s["headline"], "prose": s["prose"]} for s in secs], \
               [{"section": "(all)", "what": "none", "why": reason}]

    edits = [e for e in (out.get("edits") or []) if isinstance(e, dict)]
    guard_failures, warnings = ([], [])
    if not blended:
        blended, edits = keep_original("the editor returned no sections")
    else:
        guard_failures, warnings = _guards(secs, blended)
        if guard_failures:
            for f in guard_failures:
                print(f"    !! BLOCKED: {f}")
            blended, edits = keep_original("guards failed")
            warnings = []

    # --- the tag audit: nothing invented, every disappearance visible -------
    before = set()
    for s in secs:
        before |= tags.id_set(s["prose"])
    invented, result = 0, []
    for i, b in enumerate(blended):
        prose = str(b.get("prose") or "")
        bad = tags.id_set(prose) - before
        if bad:
            prose = tags.drop(prose, bad)                # keeps the good ids in a shared block
            invented += len(bad)
        result.append({"heading": secs[i]["headline"], "prose": prose})
    after = set()
    for b in result:
        after |= tags.id_set(b["prose"])
    gone = sorted(before - after)

    # ---- Step 3: MEASURE what changed, and count the keywords for real -------------------------
    diff = _diff(secs, result)
    n_passages = sum(len(d["edits"]) for d in diff)
    phrases = [p for p in ([primary] + list(variations or [])) if p]
    kw_before, kw_after = _kw_counts(secs, phrases), _kw_counts(result, phrases)
    kw_measured = [{"keyword": p, "before": kw_before.get(p, 0), "after": kw_after.get(p, 0)}
                   for p in phrases]
    woven = sum(1 for k in kw_measured if k["after"] > k["before"])
    present = sum(1 for k in kw_measured if k["after"] > 0)
    longs_after, fats_after, totals_after = _count(
        [{"headline": b["heading"], "prose": b["prose"]} for b in result])

    # the editor's OWN report is kept for the review page, but it is a note, never a measurement
    claimed_used = [k for k in (out.get("keywords_used") or []) if isinstance(k, dict) and k.get("keyword")]
    claimed_skipped = [k for k in (out.get("keywords_skipped") or []) if isinstance(k, dict) and k.get("keyword")]

    if not guard_failures and not n_passages:
        warnings.append({"kind": "no edit made", "detail": [f"{len(secs)} sections, zero text changed"],
                         "note": "twelve blind writers always leave something; this is a non-result"})

    final = {"slug": slug, "sections": result, "edits": edits,
             "keywords": {"primary": primary, "variations": variations},
             "keywords_measured": kw_measured,
             "keywords_used": claimed_used, "keywords_skipped": claimed_skipped,
             "length_before": _length_facts(secs, ga.get("word_band")),
             "length_after": _length_facts([{"prose": b["prose"]} for b in result], ga.get("word_band")),
             "counter_before": {"long_sentences": len(longs), "fat_paragraphs": len(fats),
                                "sentences": totals["sentences"], "flagged": longs, "fat": fats},
             "counter_after": {"long_sentences": len(longs_after), "fat_paragraphs": len(fats_after),
                               "sentences": totals_after["sentences"]},
             "diff": diff, "guard_failures": guard_failures, "warnings": warnings,
             "applied": not guard_failures,
             "tag_audit": {"tags_before": len(before), "tags_after": len(after),
                           "invented_stripped": invented, "cut_with_content": gone}}
    config.write_json(outp, final)
    print(f"  -> {outp} | {len(edits)} edit(s) claimed, {n_passages} passage(s) actually changed"
          f" | long sentences {len(longs)}->{len(longs_after)}, fat paragraphs {len(fats)}->{len(fats_after)}"
          f" | keywords present {present}/{len(phrases)} ({woven} newly woven)"
          f" | tags {len(before)}->{len(after)}"
          + (f" | STRIPPED {invented} invented" if invented else "")
          + (f" | cut with content: {gone[:8]}" if gone else ""))
    for e in edits[:10]:
        print(f"    [{e.get('what','?')}] {str(e.get('section',''))[:40]}: {str(e.get('why',''))[:70]}")
    for wn in warnings:
        print(f"    ~ {wn['kind']}: {', '.join(str(x) for x in wn['detail'][:8])}")
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Writer Step 2 — blend the sections into one piece.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Writer Step 2: blend — {a.slug} ==")
    run(a.slug, redo=a.redo)
