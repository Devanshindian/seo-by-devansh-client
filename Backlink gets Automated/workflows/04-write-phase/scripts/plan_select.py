#!/usr/bin/env python3
"""Planner Step 2 — SELECT: judge every H3, keep sections by arithmetic, place orphans, write the lean plan.

Reads:  gather/plan-inputs.json (+ the queue row for title/angle, via fmt_router._queue_row).
Writes: planner/_work/article-plan.tagged.json — the lean tagged plan (verify_sources.py turns it into
        planner/article-plan.draft.json after checking every citable number's source).
        planner/_work/ — tags.json / drops.json / placements.json / selection-stats.json (the full audit).

Design (Devansh, 2026-07-28):
  0. NORMALISE — cards sitting directly on an H2 become one pseudo-H3 titled after the H2, so every card
                 lives under exactly one H3 and every H3 under exactly one H2.
  1. TAG       — one AI call per H2 (parallel): each H3 tagged asset-angle / gap / common-h2 / paa /
                 related (target text verbatim from the lists), or untagged. winners_drift = the avoid list.
                 2026-08-04: the tagger now also gets the SPINE + the world (about / not_about) and each
                 card's SOURCE, and applies a WORLD TEST first — an H3 from a neighbouring field gets no
                 tag even when it genuinely matches a table-stake or a PAA question. Measured before this:
                 152 of 478 H3s untagged (32%), and 71 survived on the loosest tag ("related") alone.
  2. SCORE     — pure arithmetic: an H2 survives at >= SELECT_H3_COVERAGE tagged H3s and keeps ONLY its
                 tagged H3s; below the bar the H2 dies and its tagged H3s become orphans.
  3. PLACE     — one AI call force-fits every orphan into the best surviving H2 (code fallback: the
                 survivor sharing the most tag targets).
  4. ASSEMBLE  — the lean plan. No slots, no format checklist, no is_differentiator, no seatbelt:
                 the tags are the only authority. Everything dropped is recorded in _work.
"""
import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import article_ctx
import config
import llm
import fmt_router


def _nid(x):
    """Normalise a card id — 'id1', ' 1 ', 1 all become the int 1."""
    if isinstance(x, int):
        return x
    s = str(x).strip()
    if s.lower().startswith("id"):
        s = s[2:]
    try:
        return int(s)
    except ValueError:
        return x


def _norm_txt(s):
    return " ".join((s or "").strip().lower().split())


def _normalise_sections(menu):
    """Step 0: section-level cards -> one pseudo-H3; every H3 carries its cards."""
    out = []
    for sec in menu:
        h3s = []
        sec_cards = list(sec.get("evidence", []))
        if sec_cards:
            h3s.append({"h3": sec.get("h2", ""), "cards": sec_cards})
        for h in sec.get("h3", []):
            h3s.append({"h3": h.get("h3", ""), "cards": list(h.get("evidence", []))})
        tk = sec.get("target_keyword")
        tko = ({"keyword": tk["keyword"], "volume": tk.get("volume")}
               if isinstance(tk, dict) and tk.get("keyword") else None)
        out.append({"h2": sec.get("h2", ""), "target_keyword": tko, "h3s": h3s})
    return out


def _render_h3_block(h3s):
    lines = []
    for i, h in enumerate(h3s):
        lines.append(f"[index {i}] H3: {h['h3']}")
        for c in h["cards"]:
            g = (c.get("gloss") or "").strip()
            v = (c.get("verbatim") or "").strip().replace("\n", " ")
            src = (c.get("source_urls") or [None])[0] or "-"       # the world test reads this (2026-08-04)
            lines.append(f"  - id{c.get('card_id')} [{c.get('tag', '')}] {src}: {g}" + (f" — {v}" if v else ""))
        if not h["cards"]:
            lines.append("  (no cards)")
    return "\n".join(lines)


TAG_KINDS = ("gap", "common-h2", "paa", "related")
_ID_PREFIX = {"gap": "G", "common-h2": "T", "paa": "Q", "related": "R"}


def _tag_maps(b):
    """Mint per-article IDs: kind -> {id: original text} (G1.., T1.., Q1.., R1..). Saved to _work/ids.json."""
    lists = {"gap": b.get("gaps_to_own", []), "common-h2": b.get("winners_common_h2s", []),
             "paa": b.get("paa_pool", []), "related": b.get("related_searches", [])}
    return {kind: {f"{_ID_PREFIX[kind]}{i + 1}": x for i, x in enumerate(items)}
            for kind, items in lists.items()}


def _id_block(maps, kind):
    return "\n".join(f"- {i}: {x}" for i, x in maps[kind].items()) or "(none)"


def _clean_tags(raw, maps, h3_card_ids=None):
    """Validate one H3's tags. Each entry is {"tag": "kind: ID", "cards": [ids]} (a bare string is still
    accepted). A tag is kept only when it cites at least one card that really belongs to THIS H3 — the
    receipt rule. 'asset-angle' passes on its kind; 'kind: <ID>' decodes via the minted map; a tag carrying
    the item's full text (old style) still matches verbatim. Anything else -> bad."""
    text_maps = {k: {_norm_txt(x): x for x in m.values()} for k, m in maps.items()}
    allowed = {_nid(c) for c in (h3_card_ids or [])}
    good, bad, receipts = [], [], {}
    for entry in raw or []:
        if isinstance(entry, dict):
            t = str(entry.get("tag") or "").strip()
            cited = [_nid(c) for c in (entry.get("cards") or [])]
            cited = [c for c in cited if c in allowed] if allowed else cited
            if allowed and not cited:                      # no valid receipt -> the tag does not exist
                bad.append(f"{t} (no valid card cited)")
                continue
        else:
            t, cited = str(entry).strip(), []
        if _norm_txt(t) == "asset-angle":
            if "asset-angle" not in good:
                good.append("asset-angle")
                receipts["asset-angle"] = cited
            continue
        matched = False
        for kind in TAG_KINDS:
            if t.lower().startswith(kind + ":"):
                val = t.split(":", 1)[1].strip()
                hit = maps[kind].get(val.upper()) or text_maps[kind].get(_norm_txt(val))
                if hit:
                    canon = f"{kind}: {hit}"
                    if canon not in good:
                        good.append(canon)
                        receipts[canon] = cited
                    matched = True
                break
        if not matched:
            bad.append(t)
    return good, bad, receipts


def run(slug, redo=False):
    out_path = os.path.join(config.planner_work_dir(slug), "article-plan.tagged.json")
    if os.path.exists(out_path) and not redo:
        print(f"  reusing {out_path} (--redo to rebuild)")
        return json.load(open(out_path))

    inp = json.load(open(config.artifact(slug, "plan-inputs.json")))
    a, b = inp["group_a"], inp["group_b"]
    row = fmt_router._queue_row(slug)
    title, angle = (row.get("asset") or "").strip(), (row.get("angle") or "").strip()
    # The spine + world (about / not_about) — the same statement the research phase judged cards against.
    # Without them the tagger could pass an H3 on a common-h2 or related match from a NEIGHBOURING world.
    ctx = article_ctx.article_context(slug)
    sections = _normalise_sections(b["sections_menu"])
    maps = _tag_maps(b)

    base = (llm.load_prompt("tag-h3s.md")
            .replace("{{BRAND}}", config.BRAND)
            .replace("{{ABOUT}}", config.ABOUT or "(no description on file)")
            .replace("{{TITLE}}", title or "(none)")
            .replace("{{ANGLE}}", angle or "(none)")
            .replace("{{H1}}", a.get("h1", ""))
            .replace("{{PRIMARY_KEYWORD}}", a.get("primary_keyword", ""))
            .replace("{{SPINE}}", article_ctx.or_na(ctx, "spine"))
            .replace("{{WORLD_ABOUT}}", article_ctx.or_na(ctx, "about"))
            .replace("{{WORLD_NOT_ABOUT}}", article_ctx.or_na(ctx, "not_about"))
            .replace("{{GAPS}}", _id_block(maps, "gap"))
            .replace("{{COMMON_H2S}}", _id_block(maps, "common-h2"))
            .replace("{{PAA}}", _id_block(maps, "paa"))
            .replace("{{RELATED}}", _id_block(maps, "related"))
            .replace("{{DRIFT}}", "\n".join(f"- {x}" for x in b.get("winners_drift", [])) or "(none)"))

    # --- Step 1: TAG (one call per H2, parallel) -----------------------------
    def _tag(i):
        sec = sections[i]
        p = base.replace("{{H2}}", sec["h2"]).replace("{{H3S}}", _render_h3_block(sec["h3s"]))
        r = llm.call_json(p) or {}
        return i, r.get("h3s") or []

    tag_log, invalid_log = {}, {}
    with ThreadPoolExecutor(max_workers=llm.max_workers()) as ex:
        for fut in as_completed([ex.submit(_tag, i) for i in range(len(sections))]):
            i, entries = fut.result()
            got = {}
            for e in entries:
                try:
                    idx = int(e.get("index"))
                except (TypeError, ValueError):
                    continue
                if 0 <= idx < len(sections[i]["h3s"]):
                    h3_cards = [c.get("card_id") for c in sections[i]["h3s"][idx]["cards"]]
                    good, bad, rcp = _clean_tags(e.get("tags"), maps, h3_cards)
                    got[idx] = good
                    sections[i]["h3s"][idx]["tag_receipts"] = rcp
                    why = (e.get("why_untagged") or "").strip()
                    if why and not good:
                        sections[i]["h3s"][idx]["why_untagged"] = why
                    if bad:
                        invalid_log.setdefault(sections[i]["h2"], []).extend(bad)
            for j, h in enumerate(sections[i]["h3s"]):
                h["tags"] = got.get(j, [])
                if j not in got:
                    h["ai_missed"] = True
            tagged = sum(1 for h in sections[i]["h3s"] if h["tags"])
            print(f"  [{i + 1}/{len(sections)}] tagged {tagged}/{len(sections[i]['h3s'])} H3s | {sections[i]['h2'][:56]}")
            tag_log[sections[i]["h2"]] = [{"h3": h["h3"], "tags": h["tags"]} for h in sections[i]["h3s"]]

    # --- Step 2: SCORE + SPLIT (pure arithmetic) -----------------------------
    thr = config.SELECT_H3_COVERAGE
    survivors, dead, drops, stats_rows = [], [], [], []
    for sec in sections:
        total = len(sec["h3s"])
        tagged = [h for h in sec["h3s"] if h["tags"]]
        cov = (len(tagged) / total) if total else 0.0
        verdict = "keep" if cov >= thr and tagged else "cut"
        stats_rows.append({"h2": sec["h2"], "h3s": total, "tagged": len(tagged),
                           "coverage": round(cov, 2), "verdict": verdict})
        for h in sec["h3s"]:
            if not h["tags"]:
                drops.append({"h3": h["h3"], "from_h2": sec["h2"],
                              "why": f"untagged in {'surviving' if verdict == 'keep' else 'dead'} section",
                              "ai_reason": h.get("why_untagged", "")})
        if verdict == "keep":
            survivors.append({"h2": sec["h2"], "target_keyword": sec["target_keyword"], "h3s": tagged})
        else:
            dead.append(sec)
    orphans = [{"h3": h, "from_h2": sec["h2"]} for sec in dead for h in sec["h3s"] if h["tags"]]
    if not survivors:
        raise SystemExit("!! every section died — refusing to emit an empty plan (see planner/_work)")

    # --- Step 3: PLACE the orphans -------------------------------------------
    placements = []
    if orphans:
        surv_block = "\n".join(
            f"[index {i}] {s['h2']} — kept H3s: " + ("; ".join(h["h3"] for h in s["h3s"]) or "(none)")
            for i, s in enumerate(survivors))
        orph_block = "\n".join(
            f"[index {j}] {o['h3']['h3']} | tags: {', '.join(o['h3']['tags'])} | from cut section: {o['from_h2']}"
            f" | evidence: " + "; ".join((c.get("gloss") or "")[:80] for c in o["h3"]["cards"][:3])
            for j, o in enumerate(orphans))
        r = llm.call_json(llm.load_prompt("place-orphans.md")
                          .replace("{{TITLE}}", title).replace("{{ANGLE}}", angle)
                          .replace("{{SPINE}}", article_ctx.or_na(ctx, "spine"))
                          .replace("{{WORLD_NOT_ABOUT}}", article_ctx.or_na(ctx, "not_about"))
                          .replace("{{SURVIVORS}}", surv_block).replace("{{ORPHANS}}", orph_block)) or {}
        chosen = {}
        for p in r.get("placements") or []:
            try:
                chosen[int(p["orphan"])] = int(p["into"])
            except (TypeError, ValueError, KeyError):
                continue
        for j, o in enumerate(orphans):
            k = chosen.get(j)
            fb = not (isinstance(k, int) and 0 <= k < len(survivors))
            if fb:                                          # fallback: the survivor sharing the most tag targets
                tags = set(o["h3"]["tags"])
                k = max(range(len(survivors)),
                        key=lambda i2: len({t for h in survivors[i2]["h3s"] for t in h["tags"]} & tags))
            h = dict(o["h3"])
            h["placed_from"] = o["from_h2"]
            survivors[k]["h3s"].append(h)
            placements.append({"h3": o["h3"]["h3"], "from": o["from_h2"], "into": survivors[k]["h2"],
                               "fallback": fb})

    # --- Step 4: ASSEMBLE + SAVE ---------------------------------------------
    def _out_h3(h):
        o = {"h3": h["h3"], "tags": h["tags"], "tag_receipts": h.get("tag_receipts", {}), "card_ids": []}
        for c in h["cards"]:
            cid = _nid(c.get("card_id"))
            if cid not in o["card_ids"]:
                o["card_ids"].append(cid)
        if h.get("placed_from"):
            o["placed_from"] = h["placed_from"]
        return o

    plan = {
        "slug": slug, "h1": a.get("h1", ""), "format_archetype": a.get("format_archetype", ""),
        "primary_keyword": a.get("primary_keyword", ""), "word_band": a.get("word_band", {}),
        "persona": a.get("persona", {}),
        "gaps_to_own": b.get("gaps_to_own", []), "winners_common_h2s": b.get("winners_common_h2s", []),
        "winners_drift": b.get("winners_drift", []), "paa_pool": b.get("paa_pool", []),
        "related_searches": b.get("related_searches", []),
        # WHAT SEARCHERS EXPECT — carried through untouched so the architect can read it (2026-08-22).
        # Nothing in this step judges them; they are lifted here only so they survive the freeze.
        "search_intent": a.get("search_intent", ""),
        "ai_overview": a.get("ai_overview", ""),
        "table_stakes": a.get("table_stakes", []),
        "sections": [{"h2": s["h2"], "target_keyword": s["target_keyword"],
                      "h3s": [_out_h3(h) for h in s["h3s"]]} for s in survivors],
    }
    wd = config.planner_work_dir(slug)
    config.write_json(os.path.join(wd, "ids.json"), maps)
    config.write_json(os.path.join(wd, "tags.json"), {"by_h2": tag_log, "invalid_tags": invalid_log})
    config.write_json(os.path.join(wd, "drops.json"),
                      {"dead_h2s": [s["h2"] for s in dead], "dropped_h3s": drops})
    config.write_json(os.path.join(wd, "placements.json"), placements)
    config.write_json(os.path.join(wd, "selection-stats.json"), {
        "threshold": thr, "candidates": len(sections), "survivors": len(survivors), "dead": len(dead),
        "orphans_placed": len(placements), "h3s_dropped": len(drops), "per_h2": stats_rows})
    config.write_json(out_path, plan)
    print(f"  -> {out_path} | {len(survivors)} sections | {len(placements)} orphans placed | "
          f"{len(drops)} H3s dropped")
    return plan


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Planner Step 2 — SELECT (tag H3s, keep by arithmetic, place orphans).")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()
    print(f"== Planner Step 2: select — {args.slug} ==")
    run(args.slug, redo=args.redo)
