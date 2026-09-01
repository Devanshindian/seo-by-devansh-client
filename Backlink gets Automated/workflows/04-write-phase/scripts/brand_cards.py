#!/usr/bin/env python3
"""ARCHITECT STEP 3 — place the company's OWN material, if any of it earns a place.

Reads:  architect/structure.json          (enrich's output — sections, their sub-headings, their cards)
        <brand-context>/brand-cards.json  (the pool, built once per company by 01-brand-context/8-brand-cards)
Writes: architect/structure.json          — placed ids joined onto the destination, in place
        architect/brand-cards-used.json   — the placed cards, full text + source, keyed by id (8001+)
        architect/_work/brand-placement.json — every placement with its reason, and every rejection

The pool holds two kinds and they are rationed differently. RESEARCH is the company's own study: neutral
data about its market, so it reads as evidence. RESULTS are what a named customer achieved using the
product, so every one is the company arguing for itself. Caps live in config, are asked for in the
prompt, and are ENFORCED here — the prompt states a limit, this file is what makes it true.

Placement copies enrich exactly: a card joins an existing section's opening or one of its existing
sub-headings, by name. Nothing here ever creates a heading.
"""
import argparse, json, os
import config, llm, article_ctx, fmt_router, shape, section_keywords


def _fill(name, **kw):
    t = open(os.path.join(config.PROMPTS, name)).read()
    for k, v in kw.items():
        t = t.replace("{{%s}}" % k, str(v))
    return t


def _sections_block(sections, idx):
    """Every section with its heading, its job, its sub-headings, and the facts it ALREADY has.

    The existing facts are the whole point: without them the judge cannot tell "this section needs
    evidence" from "this section already has better evidence than ours" (J2)."""
    out = []
    for i, sec in enumerate(sections, 1):
        out.append(f"--- SECTION {i}: {sec.get('headline', '')}")
        out.append(f"    JOB: {sec.get('job') or '(none given)'}")
        for grp in shape._groups(sec):
            name = grp.get("h3") or "opening"
            label = "OPENING (no sub-heading)" if not grp.get("h3") else f'SUB-HEADING: "{grp["h3"]}"'
            facts = []
            for cid in (grp.get("card_ids") or [])[:config.BRAND_FACTS_SHOWN]:
                c = idx.get(str(cid)) or {}
                g = (c.get("gloss") or c.get("verbatim") or "").strip().replace("\n", " ")
                if g:
                    facts.append(f"        · {g[:config.ALLOC_GLOSS_CHARS]}")
            out.append(f"    {label}")
            out += facts or ["        · (no facts yet)"]
        out.append("")
    return "\n".join(out)


def _pool_block(cards, kind):
    lines = []
    for c in cards:
        extra = ""
        if kind == "result" and c.get("number"):
            extra = f" | number: {c['number']}"
        topics = c.get("topics") or []
        if topics:
            extra += f" | about: {', '.join(topics)}"
        lines.append(f"  [{c['card_id']}] {(c.get('gloss') or '').strip()}{extra}")
    return "\n".join(lines) or "  (none)"


def _load_pool():
    p = config.BRAND_CARDS_POOL
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    return {"research": d.get("cards", {}).get("research", []),
            "results": d.get("cards", {}).get("results", [])}


def run(slug, redo=False):
    outp = config.artifact(slug, "structure.json")
    used_p = config.artifact(slug, "brand-cards-used.json")
    work_p = os.path.join(config.architect_work_dir(slug), "brand-placement.json")
    if os.path.exists(work_p) and not redo:
        print(f"  reusing {work_p}")
        return json.load(open(outp))

    st = json.load(open(outp))
    # A RERUN MUST NOT STACK. This step joins ids onto groups inside structure.json, and structure.json
    # is written in place — so without this, --redo would append the same cards a second time and the
    # writer would be handed each one twice.
    if st.get("brand_cards"):
        old = {int(k["card_id"]) for k in st["brand_cards"]}
        for sec in st["sections"]:
            for grp in shape._groups(sec):
                grp["card_ids"] = [c for c in (grp.get("card_ids") or []) if int(c) not in old]
        st.pop("brand_cards", None)
        print(f"  cleared {len(old)} previously-placed card(s) before re-placing")

    pool = _load_pool()
    if not pool or not (pool["research"] or pool["results"]):
        print(f"  no brand-cards.json for this company — nothing to place (build it with "
              f"01-brand-context/8-brand-cards)")
        config.write_json(work_p, {"placements": [], "rejected": [], "notes": "no pool"})
        return st

    row = fmt_router._queue_row(slug)
    actx = article_ctx.article_context(slug)
    idx = section_keywords._card_index(slug)
    sections = st["sections"]

    reply = llm.call_json(_fill(
        "place-brand-cards.md",
        TITLE=(row.get("asset") or "").strip() or "(none)",
        ANGLE=(row.get("angle") or "").strip() or "(none)",
        SPINE=article_ctx.or_na(actx, "spine"),
        PERSONA=article_ctx.persona(slug),
        SECTIONS=_sections_block(sections, idx),
        RESEARCH_CARDS=_pool_block(pool["research"], "research"),
        RESULT_CARDS=_pool_block(pool["results"], "result"),
        RESEARCH_CAP=config.BRAND_RESEARCH_CAP,
        RESEARCH_PER_SECTION=config.BRAND_RESEARCH_PER_SECTION,
        RESULT_CAP=config.BRAND_RESULT_CAP)) or {}

    by_id = {c["card_id"]: ("research", c) for c in pool["research"]}
    by_id.update({c["card_id"]: ("result", c) for c in pool["results"]})

    # VALIDATE, THEN CAP. Every rejection is recorded with its reason: a cap that silently trims reads
    # as "nothing else qualified", which is the opposite of what happened.
    kept, rejected, per_section, n_res, n_out = [], [], {}, 0, 0
    for p in (reply.get("placements") or []):
        cid = p.get("card_id")
        try:
            cid = int(cid)
        except (TypeError, ValueError):
            rejected.append(dict(p, reason="card_id is not a number")); continue
        if cid not in by_id:
            rejected.append(dict(p, reason=f"card {cid} is not in the pool")); continue
        kind, card = by_id[cid]
        si = p.get("section")
        if not isinstance(si, int) or not (1 <= si <= len(sections)):
            rejected.append(dict(p, reason=f"section {si} does not exist")); continue
        sec = sections[si - 1]
        dest = str(p.get("goes_to") or "opening").strip()
        target = None
        if dest.lower() != "opening":
            target = next((h for h in sec.get("h3s") or [] if h.get("h3") == dest), None)
            if target is None:
                rejected.append(dict(p, reason=f'no sub-heading named "{dest[:50]}" in that section'))
                continue
        if any(k["card_id"] == cid for k in kept):
            rejected.append(dict(p, reason="already placed")); continue
        if kind == "result":
            if n_out >= config.BRAND_RESULT_CAP:
                rejected.append(dict(p, reason=f"over the customer-result cap of {config.BRAND_RESULT_CAP}"))
                continue
            n_out += 1
        else:
            if n_res >= config.BRAND_RESEARCH_CAP:
                rejected.append(dict(p, reason=f"over the research cap of {config.BRAND_RESEARCH_CAP}"))
                continue
            if per_section.get(si, 0) >= config.BRAND_RESEARCH_PER_SECTION:
                rejected.append(dict(p, reason=f"section {si} already has "
                                               f"{config.BRAND_RESEARCH_PER_SECTION} research card(s)"))
                continue
            per_section[si] = per_section.get(si, 0) + 1
            n_res += 1
        kept.append({"card_id": cid, "kind": kind, "section": si, "headline": sec.get("headline", ""),
                     "goes_to": "opening" if target is None else dest,
                     "why": str(p.get("why") or "").strip(), "gloss": card.get("gloss", "")})
        grp = target if target is not None else sec.setdefault(
            "lead", {"h3": "", "boxes": [], "card_ids": [], "is_lead": True})
        grp.setdefault("card_ids", []).append(cid)

    if kept:
        config.write_json(used_p, {str(k["card_id"]): by_id[k["card_id"]][1] for k in kept})
        st["brand_cards"] = kept
        config.write_json(outp, st)
    config.write_json(work_p, {"placements": kept, "rejected": rejected,
                               "notes": str(reply.get("notes") or "").strip()})

    print(f"  pool: {len(pool['research'])} research + {len(pool['results'])} customer results")
    print(f"  placed {len(kept)}: research {n_res}/{config.BRAND_RESEARCH_CAP} · "
          f"customer results {n_out}/{config.BRAND_RESULT_CAP}")
    for k in kept:
        print(f"    [{k['card_id']}] {k['kind']:8} -> S{k['section']} {k['headline'][:34]} / "
              f"{k['goes_to'][:26]}")
        print(f"        {k['why'][:96]}")
    if rejected:
        print(f"  !! {len(rejected)} placement(s) rejected:")
        for r in rejected:
            print(f"       card {r.get('card_id')} -> {r['reason']}")
    if not kept:
        print(f"  nothing placed — which is the expected answer for most articles. "
              f"{reply.get('notes') or ''}")
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Architect Step 3 — place the company's own material.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Architect Step 3: brand-cards — {a.slug} ==")
    run(a.slug, redo=a.redo)
