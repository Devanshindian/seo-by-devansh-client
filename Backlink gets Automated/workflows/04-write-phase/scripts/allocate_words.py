#!/usr/bin/env python3
"""Architect Step 3 — ALLOCATE: give every section a word target, judged by importance (not card count).

Reads:  architect/structure.json (FINAL — after enrichment, so researched H3s are counted) +
        planner/article-plan.json (the word band) + gather/plan-inputs.json and
        architect/enriched-cards.json (the card text).
Writes: architect/structure.json — each section gains "word_target"; the file also gains "word_budget".
        architect/structure.md — re-rendered with the targets.
        architect/_work/word-allocation.json — the AI's shares + reasons.

How the number is built (Devansh, 2026-07-30):
  base   = the MIDPOINT of the word band, then cut by config.ARCH_BAND_SHRINK (2026-08-11) because
           every section of the previous run overshot and the articles landed 14-44% over their band.
           The band itself is never rewritten; only the number we divide up moves.
  share  = an AI decides each section's PERCENTAGE of the article in two passes. Pass 1: IMPORTANCE
           to the argument sets the number. Pass 2: the section's actual FACTS are a ceiling — can it
           be written to that length without padding? — so evidence can only ever take words away,
           never earn them. Code does the arithmetic so shares always total 100 and the words add up.
           (Before 2026-08-08 it was shown only a card COUNT, while its prompt forbade judging by
           card count: the one number it had was the one it was not allowed to use.)
  target = base * share, then +WRITE_OVERWRITE_PCT (20%) because blending trims the draft: writers
           overwrite, editors cut.
A failed or malformed call falls back to an even split — the pipeline never stalls on this step.
"""
import argparse
import json
import os
import article_ctx
import config
import llm
import section_keywords
import shape
import fmt_router

OVER_PCT = int(os.environ.get("WRITE_OVERWRITE_PCT", "0"))    # buffer per section
# Was 20, on the theory that blending trims the draft back. Measured 2026-08-02: blending trims nothing,
# so the buffer became permanent overshoot. Both articles were planned ABOVE their own ceiling before a
# word was written (band max 3,800 -> planned 3,961 -> written 4,866; max 7,500 -> 7,800 -> 8,594).
# Default 0: plan to the band. Raise it only if a measured trim step ever exists to absorb it.


def run(slug, redo=False):
    outp = config.artifact(slug, "structure.json")
    st = json.load(open(outp))
    plan = json.load(open(config.artifact(slug, "article-plan.json")))
    # section_keywords' index, not shape's: it is keyed by string and it INCLUDES the enriched cards
    # (ids 9001+). shape's reads plan-inputs only, so every fact enrich.py went and bought would have
    # been invisible here.
    idx = section_keywords._card_index(slug)
    wb = plan.get("word_band") or {}
    lo, hi = int(wb.get("min") or 0), int(wb.get("max") or 0)
    true_base = (lo + hi) // 2 if lo and hi else (hi or lo or 2500)
    # AIM LOW. See config.ARCH_BAND_SHRINK: every section of the last run overshot, so the target the
    # architect divides up is deliberately below the middle of the real band. The band itself is not
    # rewritten anywhere; only this base moves.
    base = max(1, round(true_base * (1 - config.ARCH_BAND_SHRINK)))
    if base != true_base:
        print(f"  aiming low: band {lo}-{hi} (middle {true_base}) -> allocating {base} "
              f"({round(config.ARCH_BAND_SHRINK * 100)}% under)")
    secs = st["sections"]

    block = []
    for i, s in enumerate(secs):
        # THE FACTS, not a count (2026-08-08). It used to be handed "evidence available: 14 cards"
        # while the prompt told it not to judge by card count — the one number it had was the one it
        # was forbidden to use. It now sees the glosses (one line per fact) and treats them as a
        # ceiling: can this section be written to that length from this material?
        facts = []
        for h in shape._groups(s):
            for cid in h.get("card_ids", []):
                c = idx.get(str(cid)) or {}
                g = (c.get("gloss") or c.get("verbatim") or "").strip().replace("\n", " ")
                if g:
                    facts.append(g[:config.ALLOC_GLOSS_CHARS])
        shown, more = facts[:config.ALLOC_CARDS_PER_SECTION], max(0, len(facts) - config.ALLOC_CARDS_PER_SECTION)
        ev = "\n".join(f"       - {g}" for g in shown) or "       (this section holds no research facts)"
        if more:
            ev += f"\n       ... and {more} more fact(s) not shown"
        # the sub-heading count is a real signal of how much ground the section covers, and it comes
        # with a floor: every stretch (the opening plus each sub-heading) needs MIN_WORDS_PER_SUBHEAD
        n_h3 = len(s.get("h3s") or [])
        # the [LIST ITEM] marker (2026-08-09). Without it the allocator judges list entries the way it
        # judges argument sections, by importance — and the strategic article came out with items
        # ranging 260w to 910w, a 3.5x spread across twelve things a reader compares side by side.
        tag = "  [LIST ITEM]" if s.get("is_item") else ""
        block.append(f"[{i}] {s['headline']}{tag}\n     JOB: {s.get('job') or '(none given)'}\n"
                     f"     COVERS: {shape.covers(s)}\n"
                     f"     SUB-HEADINGS: {n_h3}"
                     + (f"  (so {n_h3 + 1} stretches, needing at least "
                        f"{(n_h3 + 1) * config.MIN_WORDS_PER_SUBHEAD} words in total)" if n_h3 else "")
                     + f"\n     THE FACTS IT HOLDS ({len(facts)}):\n{ev}")
    got = {}
    try:
        row = fmt_router._queue_row(slug)
        got = llm.call_json(llm.load_prompt("allocate-words.md")
                            .replace("{{BRAND}}", config.BRAND)
                            .replace("{{ABOUT}}", config.ABOUT or "(no description on file)")
                            .replace("{{TITLE}}", (row.get("asset") or "").strip() or "(none)")
                            .replace("{{ANGLE}}", (row.get("angle") or "").strip() or "(none)")
                            .replace("{{SPINE}}", st.get("spine") or "(none given)")
                            .replace("{{PERSONA}}", article_ctx.persona(slug))
                            .replace("{{MIN_WORDS_PER_SUBHEAD}}", str(config.MIN_WORDS_PER_SUBHEAD))
                            .replace("{{TARGET}}", str(base))
                            .replace("{{CARD_CAP}}", str(config.ALLOC_CARDS_PER_SECTION))
                            .replace("{{SECTIONS}}", "\n".join(block))) or {}
    except Exception as e:
        print(f"    - allocation call failed ({str(e)[:60]}) — falling back to an even split")

    shares = {}
    for a in got.get("allocation") or []:
        try:
            i, sh = int(a.get("section")), float(a.get("share"))
        except (TypeError, ValueError):
            continue
        if 0 <= i < len(secs) and sh > 0:
            shares[i] = sh
    if not shares:                                    # crash net: even split
        shares = {i: 100.0 / len(secs) for i in range(len(secs))}
    total = sum(shares.values())
    for i, s in enumerate(secs):                      # normalise, apply, add the overwrite buffer
        sh = shares.get(i, 0.0) / total
        s["word_target"] = int(round(base * sh * (1 + OVER_PCT / 100.0)))

    st["word_budget"] = {"band": {"min": lo, "max": hi},
                         "band_middle": true_base, "aim_low_pct": round(config.ARCH_BAND_SHRINK * 100),
                         "base": base, "overwrite_pct": OVER_PCT,
                         "sum_of_targets": sum(s["word_target"] for s in secs)}
    config.write_json(outp, st)
    config.write_json(os.path.join(config.architect_work_dir(slug), "word-allocation.json"),
                      {"base": base, "raw": got, "applied": {s["headline"][:60]: s["word_target"] for s in secs}})
    shape.render_md(slug, st, plan)
    # DID THE H3 RULE ACTUALLY HOLD? (2026-08-09) This is the only step that knows BOTH the
    # sub-heading count and the real word target, so it is the only place the question can be asked.
    # It REPORTS and does not delete: measure first, decide whether to enforce once we have seen a
    # few runs. Before the rule was fixed, one section came out at 165 words across 4 sub-headings.
    thin, n_h3_total = [], 0
    for s in secs:
        n = len(s.get("h3s") or [])
        n_h3_total += n
        # NO `if n` (2026-08-13). It used to skip sections with no sub-heading, so the two THINNEST
        # sections on the last run — 158 words each, no sub-heading — were invisible to the only check
        # that exists for thin sections. It reported 4; the real answer was 7.
        if s["word_target"] // (n + 1) < config.MIN_WORDS_PER_SUBHEAD:
            thin.append((s["headline"], s["word_target"], n, s["word_target"] // (n + 1)))
    heads = len(secs) + n_h3_total
    print(f"  -> word targets set | band {lo}-{hi} · base {base} · +{OVER_PCT}% "
          f"→ {st['word_budget']['sum_of_targets']} words across {len(secs)} sections")
    for s in secs:
        n = len(s.get("h3s") or [])
        print(f"    ~{s['word_target']:>5} w  {('+' + str(n) + ' sub') if n else '       '}  {s['headline'][:56]}")
    print(f"  headings: {len(secs)} section(s) + {n_h3_total} sub-heading(s) = {heads} | "
          f"{base // max(1, heads)} words each")
    if thin:
        print(f"  !! {len(thin)} section(s) have more sub-headings than their words support "
              f"(floor {config.MIN_WORDS_PER_SUBHEAD}w per stretch):")
        for h, w, n, per in thin:
            print(f"       {w:>5}w across {n + 1} stretches = {per}w each — {h[:48]}")
    st["word_budget"]["headings"] = {"sections": len(secs), "sub_headings": n_h3_total, "total": heads,
                                     "words_per_heading": base // max(1, heads),
                                     "under_floor": [{"section": h, "words": w, "sub_headings": n,
                                                      "words_per_stretch": per} for h, w, n, per in thin]}
    config.write_json(outp, st)
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Architect Step 3 — allocate a word target per section.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Architect Step 3: allocate words — {a.slug} ==")
    run(a.slug, redo=a.redo)
