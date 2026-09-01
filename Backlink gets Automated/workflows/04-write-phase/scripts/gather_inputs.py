#!/usr/bin/env python3
"""Planner Step 1 — GATHER the raw material for one article into ONE file: gather/plan-inputs.json.

Reads:  the research bundle (structure-<slug>.json), the research-doc (research-doc-<slug>.md), two proof
        files (05-winners.md, 04-serp-extract.json), and the queue row (title + angle, via fmt_router).
Writes: gather/plan-inputs.json — group_a (article settings) + group_b (selection raw material). That is the
        step's ONLY output; every later planner step reads it.
        gather/_work/ — the intermediate AI extractions (winners, word band, vetting), kept for inspection.

Everything is a clean lift (JSON copied as-is) except three AI calls:
  1. extract-winners.md   — lifts the winners-study lists out of prose (the router reads the winners
                            study on its own, separately)
  2. extract-word-band.md — the word band from the research doc's prose (regex crash-net if the call fails)
  3. vet-lists.md         — keeps only on-angle PAA questions + related searches (judged by title + angle)
"""
import argparse
import json
import os
import re
import article_ctx
import config
import llm
import fmt_router


def _parse_word_band(doc):
    """CRASH NET only (used when the AI call fails): {min,max} from the '**Word band:** 2,400-3,200' line."""
    m = re.search(r"Word band:\**\s*([\d,]+)\s*[-\u2013\u2014]+\s*([\d,]+)", doc)
    if m:
        return {"min": int(m.group(1).replace(",", "")), "max": int(m.group(2).replace(",", ""))}
    m = re.search(r"Word band:\**\s*([\d,]+)", doc)
    if m:
        lo = int(m.group(1).replace(",", ""))
        return {"min": lo, "max": round(lo * 1.2)}
    return {"min": 0, "max": 0}


def _work_save(slug, name, data):
    config.write_json(os.path.join(config.gather_work_dir(slug), name), data)


def _extract_winners(slug, winners_md):
    """ONE AI call lifts the winners-study lists out of prose. Verbatim lifts, validated shapes."""
    out = llm.call_json(llm.load_prompt("extract-winners.md").replace("{{WINNERS}}", winners_md)) or {}
    got = {
        "gaps_to_own": [str(x) for x in (out.get("gaps_to_own") or [])],
        "winners_common_h2s": [str(x) for x in (out.get("winners_common_h2s") or [])],
        "winners_drift": [str(x) for x in (out.get("winners_drift") or [])],
    }
    _work_save(slug, "winners-extract.json", got)
    return got


def _word_band(slug, doc):
    """AI-first; the regex parse is only the crash net. Records which path produced the value."""
    try:
        got = llm.call_json(llm.load_prompt("extract-word-band.md").replace("{{DOC}}", doc))
        wb = got.get("word_band") or {}
        lo, hi = int(wb.get("min", 0)), int(wb.get("max", 0))
        if lo > 0 and hi >= lo:
            _work_save(slug, "word-band.json", {"word_band": {"min": lo, "max": hi}, "extracted_by": "llm"})
            return {"min": lo, "max": hi}
    except Exception as e:
        print(f"    - word-band AI extract failed ({str(e)[:50]}) -- using the regex crash net", flush=True)
    wb = _parse_word_band(doc)
    _work_save(slug, "word-band.json", {"word_band": wb, "extracted_by": "parse-fallback"})
    return wb


def _vet_kept(kept, originals):
    """Match a keep-list back against the originals (verbatim), dedupe, never wipe a list to zero."""
    if kept is None:
        return list(dict.fromkeys(originals))
    ks, seen = set(kept), set()
    out = [q for q in originals if q in ks and not (q in seen or seen.add(q))]
    return out or list(dict.fromkeys(originals))


_INTENT = re.compile(r"^\s*-\s*Intent:\s*(.+)$", re.M)
_AIO = re.compile(r"^\s*-\s*What it covers:\s*(.+)$", re.M)


def _search_signals(doc):
    """Two lines the research already wrote, lifted from the doc this step already opens.

    intent      — informational / commercial / etc. What kind of page Google is rewarding.
    ai_overview — Google's OWN answer to the query, in Google's own order. Not a competitor's
                  opinion of the topic shape; the search engine's. The single best ordering signal
                  in the research, and the architect has never seen it.

    Both are honest when they are useless: on one article the AI Overview recorded itself as an
    "entirely off-topic homonym collision", and that is passed through as-is rather than hidden.
    """
    i, a = _INTENT.search(doc), _AIO.search(doc)
    return (i.group(1).strip() if i else ""), (a.group(1).strip() if a else "")


def _vet_lists(slug, title, angle, paa, related, table_stakes=None):
    """ONE AI call vets all three Google lists against the article's title, angle and WORLD.

    The world matters most here: a PAA question that shares our words but belongs to a different field
    is exactly what this step exists to drop, and title + angle alone cannot always tell the two apart.

    TABLE STAKES joined this call on 2026-08-22 rather than getting a filter of their own. They need
    exactly the same world test, and the architect reads them to decide what an article covers early —
    so an off-angle topic every competitor happens to share would push our article toward being the
    tenth copy of a page that already ranks. Kept most-missed first; that order is used downstream.
    """
    table_stakes = table_stakes or []
    if not paa and not related and not table_stakes:
        return paa, related, table_stakes
    ctx = article_ctx.article_context(slug)
    try:
        r = llm.call_json(llm.load_prompt("vet-lists.md")
                          .replace("{{BRAND}}", config.BRAND)
                          .replace("{{ABOUT}}", config.ABOUT or "(no description on file)")
                          .replace("{{TITLE}}", title or "(none given)")
                          .replace("{{ANGLE}}", angle or "(none given)")
                          .replace("{{WORLD_ABOUT}}", article_ctx.or_na(ctx, "about"))
                          .replace("{{WORLD_NOT_ABOUT}}", article_ctx.or_na(ctx, "not_about"))
                          .replace("{{QUESTIONS}}", "\n".join(f"- {q}" for q in paa) or "(none)")
                          .replace("{{RELATED}}", "\n".join(f"- {q}" for q in related) or "(none)")
                          .replace("{{TABLE_STAKES}}",
                                   "\n".join(f"- {q}" for q in table_stakes) or "(none)")
                          .replace("{{MAX_TABLE_STAKES}}", str(config.MAX_TABLE_STAKES))) or {}
    except Exception as e:
        # SAY SO. This was a bare, silent `except` — and when a missing setting made the call raise
        # AttributeError, it returned every list UNVETTED with no sign anything had gone wrong.
        # Three articles shipped with unfiltered PAA, related searches and table stakes before the
        # article count on a review page gave it away (2026-08-26). A fallback that cannot be seen
        # is not a fallback, it is a silent downgrade.
        print(f"  !! VETTING FAILED ({type(e).__name__}: {str(e)[:90]}) — "
              f"the lists are UNFILTERED: {len(paa)} PAA, {len(related)} related, "
              f"{len(table_stakes)} table stakes go through as they came")
        return paa, related, table_stakes
    kept_q = _vet_kept(r.get("keep_questions"), paa)
    kept_r = _vet_kept(r.get("keep_related"), related)
    # NOT _vet_kept: that helper restores the ORIGINAL order, and here the order the model returned
    # IS the answer — most-missed first, which is what the architect uses to decide what comes early.
    ks = [str(x).strip() for x in (r.get("keep_table_stakes") or []) if str(x).strip()]
    kept_t = [x for x in ks if x in set(table_stakes)][:config.MAX_TABLE_STAKES] or table_stakes
    _work_save(slug, "vet.json", {"paa_raw": paa, "related_raw": related,
                                  "table_stakes_raw": table_stakes,
                                  "paa_kept": kept_q, "related_kept": kept_r,
                                  "table_stakes_kept": kept_t})
    return kept_q, kept_r, kept_t


def run(slug, redo=False):
    out_path = os.path.join(config.gather_dir(slug), "plan-inputs.json")
    if os.path.exists(out_path) and not redo:
        print(f"  reusing {out_path} (--redo to rebuild)")
        return json.load(open(out_path))

    # --- read the sources ---
    structure = json.load(open(config.structure_path(slug)))
    doc = open(config.research_doc_path(slug)).read()
    winners_md = open(os.path.join(config.proof_dir(slug), "05-winners.md")).read()
    serp = json.load(open(os.path.join(config.proof_dir(slug), "04-serp-extract.json")))
    row = fmt_router._queue_row(slug)
    title, angle = (row.get("asset") or "").strip(), (row.get("angle") or "").strip()

    # --- the AI steps: the router first (its own step; it reads the winners study itself) ---
    archetype = fmt_router.route_slug(slug)
    winners = _extract_winners(slug, winners_md)
    word_band = _word_band(slug, doc)
    paa, related, table_stakes = _vet_lists(
        slug, title, angle, serp.get("paa") or [], serp.get("related_searches") or [],
        winners.get("winners_common_h2s") or [])
    intent, ai_overview = _search_signals(doc)

    # --- group A: the article's settings ---
    keyword_set = dict(structure.get("keyword_set", {}))
    keyword_set.pop("in_body", None)                       # below the volume floor -- not carried
    # secondaries ARE carried: they are the merit-picked section keywords the architect's
    # headings step maps onto the article as built. h2_keywords (one keyword stapled to each
    # PLANNED section) stays only as context -- the outline it was matched to no longer exists.
    internal_pool = []
    for s in structure.get("sections") or []:
        internal_pool += s.get("internal_links") or []
    group_a = {
        "slug": slug,
        "h1": structure.get("h1", ""),
        "internal_link_pool": list(dict.fromkeys(internal_pool)),
        "format_archetype": archetype,
        "primary_keyword": keyword_set.get("primary", ""),
        "keyword_set": keyword_set,
        "persona": structure.get("persona", {}),
        "word_band": word_band,
        # WHAT SEARCHERS EXPECT (2026-08-22). The architect decided section ORDER with none of this:
        # it designed from the facts alone and never saw what people search for. All four ride here.
        "search_intent": intent,
        "ai_overview": ai_overview,
        "table_stakes": table_stakes,
    }

    # --- group B: the selection raw material ---
    group_b = {
        "sections_menu": structure.get("sections", []),
        "gaps_to_own": winners["gaps_to_own"],
        "winners_common_h2s": winners["winners_common_h2s"],
        "winners_drift": winners["winners_drift"],
        "paa_pool": paa,
        "related_searches": related,
    }

    result = {"slug": slug, "generated_by": "gather_inputs.py", "group_a": group_a, "group_b": group_b}
    config.write_json(out_path, result)
    print(f"  -> {out_path}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Gather group A + B into gather/plan-inputs.json (Planner Step 1).")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true", help="rebuild even if plan-inputs.json exists")
    a = ap.parse_args()
    print(f"== Planner Step 1: gather -- {a.slug} ==")
    run(a.slug, redo=a.redo)
