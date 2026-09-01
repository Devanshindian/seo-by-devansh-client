#!/usr/bin/env python3
"""Writer Step 1 — BODY: write each section of the article into neutral, sourced prose.

Reads:  architect/structure.json (the spine, every section's job/headline/H3s/word target) +
        gather/plan-inputs.json + architect/enriched-cards.json + architect/brand-cards-used.json
        (the card text) +
        the brand voice pack (config.VOICE_FILES) + the article's chosen persona.
Writes: writer/_work/body.json — per section: {headline, prose, provenance[]}.

Design:
  - ONE call per section, run in parallel. A call sees ONLY its own cards, so it cannot invent facts.
  - Every call also sees the article's SPINE and the FULL PLAN (every other section's headline, job
    and sub-topics) so 12 separately-written sections still pull in one direction and never overlap.
    They cannot see each other's TEXT — only the briefs — so nothing can reference prose that does
    not exist yet.
  - Facts carry a [c<id>] tag inline; CODE parses those into a provenance list (a tag pointing at a
    card not in this section is dropped and counted). assemble turns the tags into source links.
  - PRODUCT-FREE by default; the rule flips only for a section that IS about the brand.
  - Wrappers (intro/TL;DR/takeaways/CTA/FAQ) are NOT written here — they are later steps.
"""
import argparse
import json
import os
import re
import article_ctx
import config
import llm
import fmt_router
import shape          # for _groups(): the lead group lives outside h3s, and every reader must see it
from concurrent.futures import ThreadPoolExecutor, as_completed

import tags
_NUM = re.compile(r"\$?\d[\d,]*(?:\.\d+)?\s?%?")


def _nid(x):
    try:
        return int(str(x).lower().replace("id", "").strip())
    except (ValueError, AttributeError):
        return x


def _has_number(t):
    return any(len(re.sub(r"[^\d]", "", m)) >= 2 for m in _NUM.findall(t or ""))


def _card_index(slug):
    """Every card the writer may cite: the research cards + any enriched (9001+) cards."""
    idx = {}
    inp = json.load(open(config.artifact(slug, "plan-inputs.json")))
    for s in inp["group_b"]["sections_menu"]:
        for c in s.get("evidence", []):
            idx[_nid(c.get("card_id"))] = c
        for h in s.get("h3", []):
            for c in h.get("evidence", []):
                idx[_nid(c.get("card_id"))] = c
    for name in ("enriched-cards.json", "brand-cards-used.json"):
        ep = config.artifact(slug, name)
        if os.path.exists(ep):
            for cid, c in json.load(open(ep)).items():
                idx[_nid(cid)] = c
    return idx


def _brief():
    """The ONE brand file: writer-brief.md, built per company by 01-brand-context/7-writer-brief.

    Until 2026-08-10 this injected the whole brand pack — seven files, ~26,600 words — under a single
    line ("match these"). Most of it governed work this writer does not do (headings, links, meta,
    pricing), some of it was facts it could not cite, and several files contradicted each other. The
    brief is what survived: what the company believes, who speaks, its words, its bans."""
    p = config.brand_file(config.BRIEF_FILE)
    if not os.path.exists(p):
        return ("(no writer-brief.md for this company — build it with "
                "workflows/01-brand-context/7-writer-brief)")
    return open(p).read().strip()


def _field(slug):
    """The voices-from-the-field block, or "" when this article has no such file.

    NO PROMPT TEXT LIVES HERE. The words are in prompts/field-block.md, like every other prompt in this
    engine; this function only decides whether the block appears at all and drops the article's own file
    into it. (It briefly lived inline in this file, which meant nobody could read or edit it without
    opening Python. Fixed 2026-08-11.)"""
    p = config.artifact_optional(slug, "voices-from-the-field.md")
    if not p or not os.path.exists(p):
        return ""
    body = open(p).read().strip()
    if not body:
        return ""
    # A FILE THAT FOUND NOTHING MUST NOT APPEAR AT ALL. When fewer than two findings survived the
    # filter, field-write.md writes a two-line "nothing useful came back, ignore this file" instead of
    # a report. Wrapping that in the rules block would hand the writer a page of instructions about a
    # file with nothing in it, and invite it to lean on something that was never there. So the whole
    # block is dropped and the writer never learns the step ran.
    findings = [h for h in re.findall(r"^## (.+)$", body, re.M)
                if "did not show up" not in h.lower()]
    if len(findings) < 2:
        return ""
    block = open(os.path.join(config.PROMPTS, "field-block.md")).read().strip()
    return "\n\n" + block.replace("{{FIELD_FILE}}", body) + "\n"


def _plan_block(sections, cur):
    lines = []
    for i, s in enumerate(sections, 1):
        mark = "    <<<< YOU WRITE THIS ONE" if s is cur else ""
        lines.append(f"{i}. {s.get('headline', '')}{mark}")
        lines.append(f"   JOB: {s.get('job') or '(none given)'}")
        lines.append(f"   COVERS: {shape.covers(s)}")
    return "\n".join(lines)


def _facts(group, idx):
    lines = []
    for cid in group.get("card_ids", []):
        c = idx.get(_nid(cid)) or {}
        text = (c.get("verbatim") or c.get("gloss") or "").strip().replace("\n", " ")[:config.BODY_CARD_CHARS]
        if not text:
            continue
        # OUR OWN RESEARCH HAS NO URL, AND USED TO RENDER AS "(no source)" (2026-08-13). The company's
        # own study is the one fact in the article a competitor cannot use, and it was reaching the
        # writer looking like the least credible line on the page. The study name already sits on the
        # card as source_note, per company, so nothing here is hardcoded to one client.
        src = (c.get("source_urls") or [None])[0] or c.get("source_note") or "(no source)"
        ours = " [OUR OWN RESEARCH — name it in the prose]" if str(c.get("tag", "")).startswith("brand") else ""
        lines.append(f"  [c{_nid(cid)}] {text}  — source: {src}{ours}")
    return lines


def _render_shape(sec, idx):
    """The section's SHAPE and its facts, together (2026-08-09).

    The architect decides how a section is built: which facts open it under the H2, and which sit
    under each sub-heading it authored. Until now the writer was handed every fact in one flat pile
    and the shape was thrown away, so it wrote continuous prose and rendered no sub-headings at all —
    3 of the first 4 articles shipped with zero H3s on the page despite the architect writing them.

    Showing the facts UNDER their heading, rather than as a list of headings plus a separate list of
    facts, is the point: the writer cannot follow the shape it cannot see.
    """
    lead, h3s = (sec.get("lead") or {}), (sec.get("h3s") or [])
    lead_facts = _facts(lead, idx)
    out = []
    if h3s:
        out.append("THE OPENING — write this first, directly under the section heading, with no "
                   "sub-heading of its own:")
        out += lead_facts or ["  (no facts of its own — open with a short lead-in to the sub-headings below)"]
        for h in h3s:
            out.append("")
            out.append(f'SUB-HEADING (render it exactly, as "### {h.get("h3", "")}"):')
            out += _facts(h, idx) or ["  (no facts — do not invent any; if it cannot be written, leave it out)"]
    else:
        out.append("THIS SECTION HAS NO SUB-HEADINGS. Write it straight through as prose under its "
                   "heading. Do NOT invent sub-headings.")
        out += lead_facts
    body = "\n".join(out).strip()
    return body or ("(this section has NO research facts — write honestly and generally; do NOT "
                    "claim any testing, survey or interview you did not run, and invent nothing.)")


def _provenance(prose, sec, idx):
    """Parse the [c<id>] tags into a per-card provenance list. A tag naming a card that is NOT in this
    section is a hallucinated id — dropped and counted."""
    allowed = {_nid(c) for h in shape._groups(sec) for c in h.get("card_ids", [])}
    seen, prov, dropped = set(), [], 0
    for m in tags.BLOCK.finditer(prose):
        for cid in [int(d) for d in re.findall(r"\d+", m.group(0))]:
            if cid not in allowed:
                dropped += 1
                continue
            if cid in seen:
                continue
            seen.add(cid)
            c = idx.get(cid) or {}
            claim = re.split(r"(?<=[.!?])\s", prose[:m.start()])[-1].strip()[-160:]
            prov.append({"card_id": cid, "source_url": (c.get("source_urls") or [None])[0],
                         "is_number": _has_number(c.get("verbatim", "")), "claim": claim})
    return prov, dropped


def _table_instruction(sec):
    """The architect marks a section as a table when its content is parallel items on shared axes.
    Added 2026-08-05: an outside review found an article titled "Hackathon Judging Rubric" that
    described a rubric for 5,500 words and never rendered one. A rubric is a table; explaining it in
    paragraphs makes the reader hold six parallel things in their head at once."""
    cols = ((sec.get("table") or {}).get("columns")) or []
    if len(cols) < 2:
        return ""
    return ("\nRENDER THIS SECTION AS A MARKDOWN TABLE. Not a description of a table — the table itself.\n"
            "Columns, in this order: " + " | ".join(cols) + "\n"
            "  · Two or three sentences may set it up. The table is the section's payload, not an aside.\n"
            "  · Every row is built from the evidence below. A cell you cannot fill from the evidence is\n"
            "    an em-less dash \"-\", never a guess and never a placeholder like \"varies\" or \"TBD\".\n"
            "  · Keep cells short — a figure, a phrase, a band. A cell holding a paragraph means this\n"
            "    was not table-shaped after all; write the row shorter rather than widening the cell.\n"
            "  · Keep each fact's [c...] tag with it, inside the cell.\n"
            "  · Standard markdown pipes, with the header separator row. Nothing else renders.\n")


def _list_instruction(sec):
    """The architect marks a section as a list when its payload is three or more parallel items.
    Mirrors _table_instruction. Added 2026-08-09: the field existed and nothing read it."""
    kind = ((sec.get("list") or {}).get("kind") or "").strip().lower()
    if kind not in ("numbered", "bulleted"):
        return ""
    marker = "1. 2. 3." if kind == "numbered" else "- "
    why = ("the ORDER MATTERS — these are steps performed in sequence, or a ranking"
           if kind == "numbered" else "the items are PARALLEL and could be read in any order")
    of = ((sec.get("list") or {}).get("of") or "").strip()
    return (f"\nRENDER THIS SECTION'S PAYLOAD AS A {kind.upper()} LIST"
            + (f" — the items are: {of}\n" if of else "\n")
            + f"  · Use {marker} markers, one item per line. {why.capitalize()}.\n"
            + "  · Two or three sentences set it up first. The list is the payload, not an aside.\n"
            + "  · Each item is a line or two. An item needing four sentences is a paragraph in\n"
            + "    disguise — write it shorter, or this was not list-shaped after all.\n"
            + "  · Keep each fact's [c...] tag on whichever item carries it.\n"
            + "  · The section is NOT only a list. It still needs prose around it: the set-up before,\n"
            + "    and what it means for the reader after. A section that is nothing but bullets reads\n"
            + "    as a slide deck.\n")


def _thin_note(sec, failures):
    """Warn the writer when this section asked for research and it came back empty (2026-08-09).

    The architect records it; nobody told the writer. So the section still carries a full word target
    on material that was judged too thin, and the writer pads to reach it — which is exactly the
    fluff the review complained about."""
    mine = [f for f in failures if (f.get("section") or "") == (sec.get("headline") or "")]
    if not mine:
        return ""
    return ("\nA WARNING ABOUT THIS SECTION: it asked for extra research and the research came back "
            "EMPTY on " + ("this topic: " if len(mine) == 1 else "these topics: ")
            + "; ".join(f'"{f.get("h3", "")}"' for f in mine)
            + ".\nSo the facts below are all there is, and they are thinner than this section was "
              "designed for. Write what the material honestly supports and STOP. Do not stretch to "
              "reach the word target, and do not fill the gap with generalities — a short section "
              "that says only what it can prove is the correct outcome here.\n")


def run(slug, redo=False):
    outp = config.artifact(slug, "body.json")
    if os.path.exists(outp) and not redo:
        print(f"  reusing {outp}")
        return json.load(open(outp))

    st = json.load(open(config.artifact(slug, "structure.json")))
    sections = st["sections"]
    idx, brief, persona = _card_index(slug), _brief(), article_ctx.persona(slug)
    field = _field(slug)

    # the architect's per-item contract (listicles only; empty everywhere else)
    fields = [str(f).strip() for f in (st.get("item_fields") or []) if str(f).strip()]
    contract = ("\nTHIS ARTICLE'S PER-ITEM CONTRACT — your section IS one of the list's items, so it MUST end\n"
                "with exactly these labelled parts, in this order:\n"
                + "\n".join(f"  {i + 1}. **{f}**" for i, f in enumerate(fields))
                + "\nEvery other ITEM in this article ends with the same parts. That is the reason the article\n"
                  "exists: a reader comparing items across the page needs the same parts in the same place\n"
                  "every time. Write each as a real, usable answer for THIS item — never a placeholder, never\n"
                  "a note that it does not apply. A scoring line means ONE sentence that separates a top\n"
                  "answer from a middling one; a yes/no question is not a scoring line.\n") if fields else ""
    # SCOPED TO REAL ITEMS (2026-08-09). It used to go to every section. On the strategic article that
    # put "Strong Answer / Weak Answer / Scoring line" on all 27 sections, including "Build an
    # Interview Question Bank" and "3 Frameworks for Scoring Interview Answers" — sections with no
    # candidate answer to score. The architect marks which sections are items; this reads that mark.
    supporting = ("\nThis article is a list, and the item sections each end with a fixed set of labelled parts.\n"
                  "YOUR SECTION IS NOT ONE OF THE ITEMS — it is a supporting section. Do NOT add those parts,\n"
                  "and do not imitate the shape of an item section. Write it as ordinary prose.\n") if fields else ""
    research_failures = st.get("research_failures") or []
    brand, tmpl = config.BRAND, llm.load_prompt("write-body.md")
    spine = st.get("spine") or "(no spine stated)"
    row = fmt_router._queue_row(slug)
    title, angle = (row.get("asset") or "").strip(), (row.get("angle") or "").strip()

    def _write(sec):
        head = (sec.get("headline") or "").strip()
        is_brand = brand.lower() in head.lower()
        # RELAXED 2026-08-10 (Devansh). The old rule was an absolute ban outside a brand-named section,
        # which produced a product-free body plus a product paragraph bolted on later, and the seam
        # showed. The line that matters is not "never name it", it is "never make it the answer".
        rule = (f"This section IS about {brand}. Cover it factually and fairly from the facts above, name at "
                f"least one honest limitation, and never oversell or invent a capability."
                if is_brand else
                f"Name {brand} as little as you can. This article earns trust by being useful, not by "
                f"selling. If naming it is genuinely the clearest way to make a point the section is "
                f"already making, you may. Never make {brand} the answer to the reader's problem, and "
                f"never spend more than a line on it.")
        prompt = (tmpl.replace("{{BRAND}}", brand).replace("{{ABOUT}}", config.ABOUT or "(no description on file)")
                  .replace("{{TITLE}}", title or "(none)").replace("{{ANGLE}}", angle or "(none)")
                  .replace("{{SPINE}}", spine)
                  .replace("{{PERSONA}}", persona).replace("{{PLAN}}", _plan_block(sections, sec))
                  .replace("{{HEADING}}", head).replace("{{JOB}}", sec.get("job") or "(none given)")
                  .replace("{{WORD_TARGET}}", str(sec.get("word_target") or 300))
                  .replace("{{ITEM_CONTRACT}}", contract if sec.get("is_item") else supporting)
                  .replace("{{TABLE}}", _table_instruction(sec))
                  .replace("{{LIST}}", _list_instruction(sec))
                  .replace("{{THIN}}", _thin_note(sec, research_failures))
                  .replace("{{SHAPE}}", _render_shape(sec, idx))
                  .replace("{{PRODUCT_RULE}}", rule)
                  .replace("{{BRIEF}}", brief).replace("{{FIELD}}", field))
        prose = llm.call_text(prompt).strip()
        prov, dropped = _provenance(prose, sec, idx)
        return {"headline": head, "job": sec.get("job", ""), "word_target": sec.get("word_target"),
                "words": len(prose.split()), "prose": prose, "provenance": prov, "bad_tags_dropped": dropped}

    results = {}
    with ThreadPoolExecutor(max_workers=llm.max_workers()) as ex:
        futs = {ex.submit(_write, s): i for i, s in enumerate(sections)}
        for f in as_completed(futs):
            i = futs[f]
            results[i] = f.result()
            r = results[i]
            print(f"  [{len(results)}/{len(sections)}] {r['words']:>4}w (target ~{r['word_target']}) "
                  f"| {len(r['provenance'])} sourced claims | {r['headline'][:50]}")
    out = {"slug": slug, "format": st.get("format_archetype"), "spine": spine,
           "item_fields": fields,
           "sections": [results[i] for i in range(len(sections))]}

    # verify the contract in code — a promise kept on 6 of 21 items is a broken promise, and the
    # writers cannot see each other, so only this check can tell whether it held across the article.
    # Counted over ITEM sections only (2026-08-09): it used to count all of them, so a supporting
    # section correctly WITHOUT the contract was recorded as a miss, and a supporting section wrongly
    # carrying it was recorded as a success. The number was measuring the opposite of what it claimed.
    if fields:
        items = [(s, o) for s, o in zip(sections, out["sections"]) if s.get("is_item")]
        misses = []
        for _, sec_out in items:
            missing = [f for f in fields if f.lower() not in sec_out["prose"].lower()]
            if missing:
                misses.append((sec_out["headline"], missing))
        kept = len(items) - len(misses)
        print(f"  per-item contract {fields}: honoured in {kept}/{len(items)} ITEM section(s)")
        for head, missing in misses[:10]:
            print(f"    MISSING {missing} in: {head[:60]}")
        # the other half of the same check: a supporting section that copied the contract anyway
        leaked = [o["headline"] for s, o in zip(sections, out["sections"])
                  if not s.get("is_item") and all(f.lower() in o["prose"].lower() for f in fields)]
        if leaked:
            print(f"    !! {len(leaked)} SUPPORTING section(s) carry the item contract anyway:")
            for h in leaked[:5]:
                print(f"       {h[:64]}")
        out["contract_misses"] = [{"section": h, "missing": m} for h, m in misses]
        out["contract_leaked"] = leaked

    config.write_json(outp, out)
    tot = sum(s["words"] for s in out["sections"])
    print(f"  -> {outp} | {len(out['sections'])} sections | {tot} words | "
          f"{sum(len(s['provenance']) for s in out['sections'])} sourced claims")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Writer Step 1 — write every body section.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Writer Step 1: body — {a.slug} ==")
    run(a.slug, redo=a.redo)
