#!/usr/bin/env python3
"""Architect Step 1 — SHAPE: design the article's final BODY structure, with full freedom, from numbered boxes.

Reads:  planner/article-plan.json (the frozen plan: H2s -> H3s -> card_ids + tags) + gather/plan-inputs.json
        (card text) + the queue row (title + angle) + the format's Structure (formats/<archetype>.md).
Writes: architect/_work/structure.shaped.json — the shaped structure (sections + expanded H3s/card_ids +
        any needs_research markers). enrich.py runs the research and owns the FINAL architect outputs
        (structure.json + structure.md + enriched-cards.json).
        architect/_work/ also holds h3-numbers.json and every AI reply along the way.

The design (Devansh, 2026-07-28):
- Every H3 in the plan is a numbered BOX (#1..#N, plan order). Cards live inside their box and follow it.
- The AI designs the body with FREEDOM (no iron rules): sections, order, merges — anything. It answers
  ONLY with headlines + box numbers. Guidance, not rules: keep original families together when it fits,
  one box belongs to one section, leave out what the article does not need. Wrappers (intro/TLDR/FAQ/CTA)
  are another step's job and are explicitly out of scope.
- Roads by archetype:
    simple    (answer-bait / how-to / common-spine / data-report / glossary): one structure call
    listicle  : detect-items -> structure call (items each get a section)
    comparison: detect-entities -> find-yardsticks -> filter (>= SHAPE_MIN_YARDSTICK_PCT% info) -> structure
    template  : structure call that also returns the artifact spec (what the download IS + which boxes go inside)
- Code validates every box number, warns on shared boxes (guidance breach, not rejection), audits unused
  boxes, and re-checks promise coverage (gaps / table-stakes / PAA) over the boxes actually used.
"""
import argparse
import json
import os
import article_ctx
import config
import llm
import fmt_router

SIMPLE_ROAD = {"answer-bait-definitional", "how-to-guide", "common-spine", "data-benchmark-report", "glossary"}


def _card_index(inp):
    idx = {}
    for s in inp["group_b"]["sections_menu"]:
        for c in s.get("evidence", []):
            idx[c.get("card_id")] = c
        for h in s.get("h3", []):
            for c in h.get("evidence", []):
                idx[c.get("card_id")] = c
    return idx


def _mint_boxes(plan):
    """Number every H3 across the plan: box #1..#N in plan order. Returns [{n, h2, h3, tags, card_ids}]."""
    boxes, n = [], 0
    for sec in plan["sections"]:
        for h in sec["h3s"]:
            n += 1
            boxes.append({"n": n, "h2": sec["h2"], "h3": h["h3"], "tags": h.get("tags", []),
                          "card_ids": h.get("card_ids", [])})
    return boxes


def _gloss(idx, cid):
    c = idx.get(cid) or {}
    return (c.get("gloss") or c.get("verbatim") or "").strip().replace("\n", " ")


def _boxes_block(boxes, idx, with_cards="gloss"):
    """The material block. with_cards: 'gloss' (structure calls) or 'full' (detector/filter calls).

    The "serves:" line (which research promise a box carries) was REMOVED 2026-08-08 (Devansh): the
    architect designs the article, and knowing a box was bought to fill a promise biases it into
    placing the box rather than judging it. Promise coverage is still COMPUTED and reported after the
    fact by compute_coverage(), which reads the plan file, not this block.
    """
    lines, cur_h2 = [], None
    for b in boxes:
        if b["h2"] != cur_h2:
            cur_h2 = b["h2"]
            lines.append(f'\nH2: "{cur_h2}"')
        lines.append(f'  [#{b["n"]}] {b["h3"]}   ({len(b["card_ids"])} cards)')
        for cid in b["card_ids"]:
            g = _gloss(idx, cid)
            if not g:
                continue
            if with_cards == "full":
                v = (idx.get(cid) or {}).get("verbatim", "")
                v = (v or "").strip().replace("\n", " ")[:200]
                lines.append(f"      - {g}" + (f" — {v}" if v and v != g else ""))
            else:
                lines.append(f"      - {g}")
    return "\n".join(lines).strip()


def _fill(name, **kw):
    p = llm.load_prompt(name)
    for k, v in kw.items():
        p = p.replace("{{" + k + "}}", str(v))
    return p


def _format_rules(arch):
    """The format rulebook, minus its developer header (2026-08-08).

    formats/<arch>.md opens with a title line and a note saying who consumes the file. Both were being
    pasted into the live prompt on every run, so the model read a build note as an instruction. Only
    the rules go in now: everything from the first '##' heading onward.
    """
    text = open(config.format_path(arch)).read()
    i = text.find("\n## ")
    return (text[i + 1:] if i >= 0 else text).strip()


def _work(slug, name, data):
    config.write_json(os.path.join(config.architect_work_dir(slug), name), data)


def run(slug, redo=False):
    outp = os.path.join(config.architect_work_dir(slug), "structure.shaped.json")
    if os.path.exists(outp) and not redo:
        print(f"  reusing {outp}")
        return json.load(open(outp))

    plan = json.load(open(config.artifact(slug, "article-plan.json")))
    inp = json.load(open(config.artifact(slug, "plan-inputs.json")))
    idx = _card_index(inp)
    row = fmt_router._queue_row(slug)
    title, angle = (row.get("asset") or "").strip(), (row.get("angle") or "").strip()
    arch = plan["format_archetype"]
    fmt_structure = _format_rules(arch)
    boxes = _mint_boxes(plan)
    bymap = {b["n"]: b for b in boxes}
    _work(slug, "h3-numbers.json", [{k: b[k] for k in ("n", "h2", "h3", "card_ids")} for b in boxes])
    print(f"  {len(boxes)} boxes minted | archetype: {arch}")

    # The WORLD (about / not_about) is decided once, in the research phase's Step −1, and only read here.
    # The structure step DESIGNS the article, so it is the last place a wrong-field box should slip through.
    # It still writes its OWN spine: the research spine is the plan made before any cards existed, this one
    # is that plan corrected by the material that actually came back. Two different jobs, both kept.
    ctx = article_ctx.article_context(slug)
    # HOW MANY SECTIONS THE BUDGET CAN CARRY (2026-08-06). Nothing used to connect the word band to the
    # section count, so the architect designed as many as it liked and allocate_words divided the band
    # across them. Type D came out at 24 sections on a 2,800-word budget = 117 words each, which is not
    # writable; the writers produced 155 and the article ran 57% over. The band and the count are one
    # decision, and it belongs here. config.WORDS_PER_SECTION holds the number.
    # 2026-08-08 (Devansh): the fallback dropped 3000 -> 1500, and sec_target is now a CEILING the
    # prompt is told never to exceed, not a "natural shape" it can drift past. Still not enforced in
    # code: the AI is asked to return fewer, and the count is reported below so an overrun is visible.
    band = plan.get("word_band") or {}
    # ONE BUDGET FOR BOTH STEPS (2026-08-13). shape used to size its ceiling from the middle of the
    # band while allocate_words divided a number cut by config.ARCH_BAND_SHRINK, so shape planned 11
    # sections expecting ~318 words each and allocate only had 286 to hand out. Same number now.
    budget = int(((band.get("min") or 0) + (band.get("max") or 0)) / 2) or 1500
    budget = max(1, round(budget * (1 - config.ARCH_BAND_SHRINK)))
    sec_target = max(4, round(budget / config.WORDS_PER_SECTION))
    print(f"  budget {budget} words -> ceiling of {sec_target} sections ({budget // sec_target} words each)")

    # THE PARAGRAPH MATHS, derived from config so the prompt can never drift from the code (2026-08-09).
    # A section "needs ~300 words" AND was "2 or 3 paragraphs, split it if more" — with nothing saying
    # what a paragraph was worth, so every normal section was over the line and got split (26 H3s on
    # one 3,300-word article). Now a paragraph is 4 sentences, which makes a 3-paragraph section
    # exactly the 300 words the ceiling already assumes. The two rules finally agree.
    w_para = config.WORDS_PER_SENTENCE * config.SENTENCES_PER_PARAGRAPH          # 25 x 4 = 100
    paras_per_section = max(1, round(config.WORDS_PER_SECTION / w_para))         # 300 / 100 = 3
    paras_per_subhead = max(1, round(config.MIN_WORDS_PER_SUBHEAD / w_para))     # 200 / 100 = 2

    common = {"WORD_BUDGET": f"{budget:,}", "SECTION_TARGET": sec_target,
              "WORDS_PER_SENTENCE": config.WORDS_PER_SENTENCE,
              "SENTENCES_PER_PARAGRAPH": config.SENTENCES_PER_PARAGRAPH,
              "WORDS_PER_PARAGRAPH": w_para,
              "WORDS_PER_SECTION": config.WORDS_PER_SECTION,
              "PARAGRAPHS_PER_SECTION": paras_per_section,
              "MIN_WORDS_PER_SUBHEAD": config.MIN_WORDS_PER_SUBHEAD,
              "PARAGRAPHS_PER_SUBHEAD": paras_per_subhead,
              "TITLE": title or "(none)", "ANGLE": angle or "(none)", "H1": plan.get("h1", ""),
              "FORMAT_STRUCTURE": fmt_structure,
              "WORLD_ABOUT": article_ctx.or_na(ctx, "about"),
              "WORLD_NOT_ABOUT": article_ctx.or_na(ctx, "not_about"),
              # WHO the article is for (2026-08-08). The persona sat in article-plan.json — the very
              # file this step reads — and no architect step had ever looked at it, so the step that
              # decides WHICH SECTIONS EXIST was blind to the reader. That is how an article for
              # hiring managers grew sections written for candidates.
              "PERSONA": article_ctx.persona(slug),
              # WHAT SEARCHERS EXPECT (2026-08-22). This step decides the section ORDER, and until
              # now it did so from the facts alone: no intent, no idea what Google rewards, no idea
              # what every ranking page covers. Three of the four already sat in article-plan.json,
              # the very file this step opens, and were read from disk and never shown to the model.
              # Deliberately NOT here: the per-box promise tags removed on 2026-08-08, which biased
              # placement. This is about the running order, not about which fact goes where.
              "INTENT": plan.get("search_intent") or "(not recorded for this article)",
              "AI_OVERVIEW": plan.get("ai_overview") or "(Google shows no AI Overview for this query)",
              "TABLE_STAKES": "\n".join(f"  {i}. {x}" for i, x in
                                        enumerate(plan.get("table_stakes") or [], 1)) or "  (none found)",
              "THE_GAP": "\n".join(f"  - {x}" for x in (plan.get("gaps_to_own") or [])) or "  (none found)",
              "BRAND": config.BRAND, "ABOUT": config.ABOUT or "(no description on file)"}
    entities, yardsticks, artifact = [], [], None
    # every pre-call gets the world + the article, same as the structure call (2026-08-08). Until now
    # they judged which options/items exist with no idea what the article is or is not about, so a
    # neighbouring field's option could survive three filters and become a section.
    pre = {k: common[k] for k in ("BRAND", "ABOUT", "TITLE", "ANGLE", "WORLD_ABOUT", "WORLD_NOT_ABOUT",
                                  "PERSONA")}

    if arch == "comparison-rankings":
        mat_full = _boxes_block(boxes, idx, "full")
        got = llm.call_json(_fill("detect-entities.md", **pre, MATERIAL=mat_full)) or {}
        cand = [e for e in got.get("entities", []) if isinstance(e, dict) and e.get("name")]
        _work(slug, "detected-entities.json", cand)
        print(f"  detected options: {[(e['name'], e.get('count')) for e in cand]}")

        ents = "\n".join(f"- {e['name']}" for e in cand) or "(none)"
        got = llm.call_json(_fill("find-yardsticks.md", **pre, ENTITIES=ents, MATERIAL=mat_full)) or {}
        yardsticks = [str(y) for y in got.get("yardsticks", [])][:6]
        _work(slug, "yardsticks.json", yardsticks)
        print(f"  yardsticks: {yardsticks}")

        got = llm.call_json(_fill("filter-tools.md", **pre, ENTITIES=ents,
                                  YARDSTICKS="\n".join(f"- {y}" for y in yardsticks), PAGES_NOTE="",
                                  MATERIAL=mat_full, MIN_PCT=config.SHAPE_MIN_YARDSTICK_PCT)) or {}
        _work(slug, "filtered-tools.json", got)
        entities = [e["name"] for e in got.get("keep", []) if isinstance(e, dict) and e.get("name")]
        dropped = [e.get("name") for e in got.get("dropped", []) if isinstance(e, dict) and e.get("name")]
        category = str(got.get("category") or "").strip() or "(not stated)"
        print(f"  category: {category}")
        print(f"  options kept: {entities} | dropped: {len(dropped)}")

        # THE HANDOFF (2026-08-08). filter-tools already works out, per option, which yardsticks the
        # material can speak to. Only the surviving NAMES used to travel; the coverage, the dropped
        # list and the category were computed, printed and thrown away. All three now reach the
        # structure call, so it can see which option is thin on what and decide for itself whether to
        # raise research. The missing list is the complement, computed here so the yardstick list
        # stays the single source of truth.
        ent_lines = []
        for e in got.get("keep", []):
            if not (isinstance(e, dict) and e.get("name")):
                continue
            cov = [str(y) for y in (e.get("yardsticks_covered") or [])]
            missing = [y for y in yardsticks if y not in cov]
            ent_lines.append(f"- {e['name']}" + (f"   MISSING INFORMATION ON: {', '.join(missing)}" if missing else ""))
            print(f"    keep {e.get('name')}: covers {cov}" + (f" | missing {missing}" if missing else ""))

        sp = _fill("structure-comparison.md", **common, BOXES=_boxes_block(boxes, idx),
                   CATEGORY=category,
                   ENTITIES="\n".join(ent_lines) or "(none)",
                   DROPPED="\n".join(f"- {d}" for d in dropped) or "(none were removed)",
                   YARDSTICKS="\n".join(f"- {y}" for y in yardsticks) or "(none)")
    elif arch == "listicle":
        # A FLAT CAP (2026-08-08, Devansh). Was max(12, min(30, band_max/250)), which let a 7,500-word
        # band ask for 30 items. The house is moving to shorter articles, so the ceiling is one number.
        max_items = config.LISTICLE_MAX_ITEMS
        got = llm.call_json(_fill("detect-items.md", **pre, MAX_ITEMS=max_items,
                                  MATERIAL=_boxes_block(boxes, idx, "full"))) or {}
        cand = [e for e in got.get("entities", []) if isinstance(e, dict) and e.get("name")]
        _work(slug, "detected-items.json", cand)
        entities = [e["name"] for e in cand]
        print(f"  detected items ({len(entities)}/{max_items} allowed): {entities}")
        # FIT THE LIST TO THE BUDGET (2026-08-08). The structure call is the only step that knows both
        # the item count and the word budget, so it does the arithmetic. It also needs each item's card
        # count, which the detector already returns and which used to be dropped on the floor here —
        # without it "drop the weakest item" is an instruction the model can only guess at.
        reserve = config.LISTICLE_SUPPORTING_SECTIONS * config.WORDS_PER_SECTION
        item_budget = max(0, budget - reserve)
        fits = item_budget // config.LISTICLE_MIN_ITEM_WORDS if config.LISTICLE_MIN_ITEM_WORDS else len(entities)
        print(f"  budget fit: {budget:,}w - {reserve:,}w reserved for {config.LISTICLE_SUPPORTING_SECTIONS} "
              f"supporting = {item_budget:,}w for items -> room for ~{fits} at "
              f"{config.LISTICLE_MIN_ITEM_WORDS}w each (floor {config.LISTICLE_MIN_ITEMS})")
        if entities and fits < len(entities):
            print(f"     the structure call is expected to drop about {len(entities) - max(fits, config.LISTICLE_MIN_ITEMS)} item(s)")
        sp = _fill("structure-listicle.md", **common, BOXES=_boxes_block(boxes, idx),
                   SUPPORTING_RESERVE=f"{reserve:,}", SUPPORTING_MAX=config.LISTICLE_SUPPORTING_SECTIONS,
                   MIN_ITEM_WORDS=config.LISTICLE_MIN_ITEM_WORDS, MIN_ITEMS=config.LISTICLE_MIN_ITEMS,
                   ENTITIES="\n".join(f"- {e['name']}   ({e.get('count') or 0} cards)" for e in cand) or "(none)")
    elif arch == "template-resource":
        sp = _fill("structure-template.md", **common, BOXES=_boxes_block(boxes, idx))
    else:                                   # the simple road (incl. data-report, glossary, common-spine)
        sp = _fill("structure-simple.md", **common, BOXES=_boxes_block(boxes, idx))

    out = llm.call_json(sp) or {}
    _work(slug, "structure-reply.json", out)

    # --- validate + assemble ------------------------------------------------
    # THE SHAPE CHANGED 2026-08-08 (Devansh). A section used to answer with one flat "boxes" list, and
    # its H3s were simply the box titles inherited from research — planning labels nobody wrote as
    # headings, which is why 3 of the first 4 articles shipped with zero H3s on the page. The architect
    # now AUTHORS the H3s: "lead_boxes" are the boxes above the first sub-heading, then each authored
    # H3 names its own boxes. Box titles are material labels from here on, never headings.
    #
    # Downstream (write_body, section_keywords, headings) reads sec["h3s"] as {h3, card_ids}, so that
    # key keeps exactly its old shape and nothing breaks. "lead" is an addition, and the readers were
    # patched to include it so no card goes invisible.
    used, shared, sections, bad_dest = set(), [], [], []

    def _claim(raw, seen_here):
        """Box numbers from one answer slot. Drops non-numbers, unknown boxes, and any box already
        claimed elsewhere in THIS section (a box belongs in exactly one place inside a section)."""
        nums = []
        for x in raw or []:
            try:
                n = int(x)
            except (TypeError, ValueError):
                continue
            if n not in bymap or n in seen_here:
                continue
            seen_here.add(n)
            nums.append(n)
            if n in used:
                shared.append(n)
            used.add(n)
        return nums

    def _group(title, nums, is_lead=False):
        # box_labels: the planning labels of the boxes in this group. NOT headings — they are what the
        # material is about. Carried because the writer and the word allocator used to describe a
        # section by listing its box titles, and now that the H3s are authored (and most sections have
        # none) they would otherwise be handed "(none)" and lose that description entirely.
        cards, tags, from_h2, labels = [], [], "", []
        for n in nums:
            cards += bymap[n]["card_ids"]
            tags += [t for t in bymap[n]["tags"] if t not in tags]
            labels.append(bymap[n]["h3"])
            from_h2 = from_h2 or bymap[n]["h2"]
        return {"h3": title, "boxes": nums, "box_labels": labels, "from_h2": from_h2, "tags": tags,
                "card_ids": cards, **({"is_lead": True} if is_lead else {})}

    for s in out.get("sections", []):
        head = str(s.get("headline") or "").strip() or "(headline missing)"
        seen_here = set()
        # The legacy flat "boxes" key is accepted ONLY when the reply carries neither of the new keys,
        # so a model answering in the old shape degrades to one lead group instead of losing its
        # section. It must NOT fire when the reply is new-shape but happens to leave lead_boxes empty
        # (every box is under an H3): claiming the flat list first would swallow them all into the
        # lead and leave every H3 empty.
        answered_new = ("lead_boxes" in s) or bool(s.get("h3s"))
        lead_nums = _claim(s.get("lead_boxes") if answered_new else s.get("boxes"), seen_here)
        h3s = []
        for h in (s.get("h3s") or []):
            if not isinstance(h, dict):
                continue
            title = str(h.get("h3") or "").strip()
            hn = _claim(h.get("boxes"), seen_here)
            if not title:                      # an H3 with no title is not a heading; fold its boxes up
                lead_nums += hn
                continue
            h3s.append(_group(title, hn))
        # RESEARCH REQUESTS now say WHERE the answer goes (2026-08-09). One string used to do two
        # jobs — a research brief AND the heading it became — and those want opposite writing. A real
        # one rendered as "### Exact SHRM report titles, publication years, sample sizes, and
        # methodology notes for the $4,700 (2022)...", 200 characters of search query as a heading.
        # Now: "topic" is the brief, "goes_to" names the opening or an existing sub-heading of THIS
        # section, and enrich never invents a heading. A plain string (the old shape) still parses.
        titles = {h["h3"] for h in h3s}
        nr = []
        for x in (s.get("needs_research") or []):
            if isinstance(x, str):
                topic, dest = x.strip(), "opening"
            elif isinstance(x, dict):
                topic, dest = str(x.get("topic") or "").strip(), str(x.get("goes_to") or "").strip()
            else:
                continue
            if not topic:
                continue
            if dest not in titles and dest.lower() != "opening":
                if dest:
                    bad_dest.append((head, dest))
                dest = "opening"
            nr.append({"topic": topic, "goes_to": dest})
        # a section may render as a table when its content is parallel items on shared axes. Carried
        # through to write_body, which turns it into real markdown. Kept only when columns are named —
        # "table": {} with no columns is a decision nobody can act on.
        tbl = s.get("table") if isinstance(s.get("table"), dict) else None
        cols = [str(c).strip() for c in ((tbl or {}).get("columns") or []) if str(c).strip()]
        # LISTS, added 2026-08-08 — the same guard as tables, one field the writer can act on. Kept
        # only when the kind is one we can render; "list": {} is a decision nobody can act on.
        lst = s.get("list") if isinstance(s.get("list"), dict) else None
        kind = str((lst or {}).get("kind") or "").strip().lower()
        kind = kind if kind in ("numbered", "bulleted") else ""
        sections.append({
            "headline": head,
            # WHICH EXPECTED TOPIC THIS SECTION COVERS (2026-08-26). The architect knows; it just
            # never said. Carrying it forward means the HEADINGS step — which writes the published
            # heading and used to see none of this — gets exactly one topic for its own section
            # rather than a list of seven it has to match itself. It is also countable: a run where
            # almost nothing maps is visible on the review page instead of needing a dig.
            "covers": str(s.get("covers") or "").strip() or None,
            "job": str(s.get("job") or "").strip(),
            "is_item": bool(s.get("is_item")),
            "boxes": lead_nums + [n for h in h3s for n in h["boxes"]],
            "table": {"columns": cols} if len(cols) >= 2 else None,
            "list": {"kind": kind, "of": str((lst or {}).get("of") or "").strip()} if kind else None,
            "needs_research": nr,
            "lead": _group("", lead_nums, is_lead=True),
            "h3s": h3s,
        })
    bench_why = {}
    for b in out.get("benched") or []:
        try:
            bench_why[int(b.get("box"))] = str(b.get("why") or "").strip()
        except (TypeError, ValueError):
            continue
    if not sections:
        raise SystemExit("!! the structure call returned no sections — see architect/_work/structure-reply.json")
    unused = [b for b in boxes if b["n"] not in used]

    # the per-item contract (listicles only): what EVERY item section must end with, in order
    item_fields = [str(x).strip() for x in (out.get("item_fields") or []) if str(x).strip()][:4]
    # items the structure call left out because the word budget could not carry them. Recorded like a
    # benched box, so a dropped item is visible rather than silently gone.
    dropped_items = [{"item": str(d.get("item") or "").strip(), "why": str(d.get("why") or "").strip()}
                     for d in (out.get("dropped_items") or []) if isinstance(d, dict) and str(d.get("item") or "").strip()]
    result = {"slug": slug, "format_archetype": arch, "spine": str(out.get("spine") or "").strip(),
              # WHAT IT CHOSE TO LEAVE OUT (2026-08-22). The point of showing the architect what
              # readers expect is that it can still say no. This line is how we tell judging from
              # complying: a note saying "left nothing out" on every article means it stopped
              # designing and started ticking boxes, which is the failure this must not become.
              "coverage_note": str(out.get("coverage_note") or "").strip(),
              "item_fields": item_fields,
              "dropped_items": dropped_items,
              "sections": sections,
              "entities": entities, "yardsticks": yardsticks, "artifact": out.get("artifact"),
              "unused_boxes": [{"n": b["n"], "h3": b["h3"], "from_h2": b["h2"], "cards": len(b["card_ids"]),
                                "serves": b["tags"], "why_benched": bench_why.get(b["n"], "")} for b in unused],
              "shared_box_warnings": sorted(set(shared))}
    config.write_json(outp, result)
    n_items = sum(1 for s in sections if s.get("is_item"))
    if item_fields:
        print(f"  per-item contract: every ITEM section ends with {item_fields} "
              f"({n_items} item / {len(sections) - n_items} supporting sections)")
        # a contract that lands on nothing is a silent no-op: the model named the fields and then
        # flagged no section as an item, so nothing downstream can ever apply them.
        if not n_items:
            print("  !! item_fields were named but NO section is flagged is_item — the contract "
                  "applies to nothing. Check architect/_work/structure-reply.json")
    if n_items and not item_fields:
        print(f"  note: {n_items} item section(s) and no per-item contract (the angle promised nothing repeating)")
    coverage, reopened = compute_coverage(sections, plan)
    markers = sum(len(s["needs_research"]) for s in sections)
    tabled = [s for s in sections if s.get("table")]
    if tabled:                       # reported, not enforced — the cap lives in the prompt
        print(f"  tables: {len(tabled)}" + ("  !! more than 2 — check this is deliberate" if len(tabled) > 2 else ""))
        for s in tabled:
            print(f"    · {s['headline'][:52]}  [{', '.join(s['table']['columns'])}]")
    listed = [s for s in sections if s.get("list")]
    for s in listed:                 # reported, not enforced — the rule lives in the prompt
        print(f"  list ({s['list']['kind']}): {s['headline'][:48]}  — {s['list']['of'][:44]}")
    n_h3 = sum(len(s["h3s"]) for s in sections)
    if bad_dest:
        print(f"  !! {len(bad_dest)} research request(s) named a destination that is not a sub-heading "
              f"of their section — sent to the opening instead:")
        for h, d in bad_dest[:5]:
            print(f"       {h[:40]} -> {d[:52]!r}")
    if dropped_items:
        print(f"  items dropped to fit the budget: {len(dropped_items)}")
        for d in dropped_items:
            print(f"    - {d['item'][:56]} — {d['why'][:60]}")
    # The ceiling is prompt guidance; code only makes an overrun visible. A listicle is governed by
    # its item budget rather than a section count, so there its supporting sections are what gets
    # checked. A comparison's option sections are exempt for the same reason: every kept option earns
    # one, so counting them against the ceiling would flag every run and train everyone to ignore it.
    if arch == "listicle":
        n_supporting = len(sections) - n_items
        if n_supporting > config.LISTICLE_SUPPORTING_SECTIONS:
            print(f"  !! {n_supporting} supporting section(s), {config.LISTICLE_SUPPORTING_SECTIONS} reserved for")
    else:
        exempt = len(entities) if arch == "comparison-rankings" else 0
        counted = len(sections) - min(exempt, len(sections))
        room = max(0, sec_target - exempt)
        if counted > room:
            print(f"  !! {counted} section(s) against room for {room} "
                  f"(ceiling {sec_target}, {exempt} exempt option section(s))")

    print(f"  -> {outp} | {len(sections)} sections | {n_h3} authored H3s | {len(used)}/{len(boxes)} boxes used | "
          f"unused {len(unused)} | shared-box warnings {len(set(shared))} | research markers: {markers}"
          + (f" | REOPENED holes: {len(reopened)}" if reopened else ""))
    return result


def _groups(sec):
    """Every card-carrying group in a section: the lead (the prose above the first H3) then each H3.
    One helper so nothing has to remember that the lead lives outside h3s."""
    lead = sec.get("lead")
    return ([lead] if lead else []) + list(sec.get("h3s") or [])


def covers(sec):
    """One line describing what a section covers, for prompts that need to summarise it.

    Prefers the AUTHORED H3s, because those are the real shape of the section. Falls back to the box
    labels when a section has no sub-headings, which is most of them — without the fallback every
    such section would be described as "(none)" and the reader of that prompt (the word allocator,
    the body writer's plan block) would be judging a section it cannot see the contents of.
    """
    h3s = [h.get("h3", "") for h in (sec.get("h3s") or []) if h.get("h3")]
    if h3s:
        return " · ".join(h3s)
    labels = [l for g in _groups(sec) for l in (g.get("box_labels") or []) if l]
    return " · ".join(labels) or "(no sub-topics)"


def compute_coverage(sections, plan):
    """Promise coverage over the boxes actually placed. Returns (coverage dict, reopened list).

    Reads the tags carried on the placed boxes. The architect no longer SEES those tags (2026-08-08),
    so this is a report on what happened, not something the design was steered by.
    """
    served = {t for s in sections for h in _groups(s) for t in h.get("tags", [])}
    coverage, reopened = {}, []
    for kind, key, label in [("gap", "gaps_to_own", "Gaps"), ("common-h2", "winners_common_h2s", "Table-stakes"),
                             ("paa", "paa_pool", "PAA questions")]:
        items = plan.get(key) or []
        holes = [x for x in items if f"{kind}: {x}" not in served]
        coverage[label] = f"{len(items) - len(holes)}/{len(items)}"
        for h in holes:
            reopened.append(f"{label}: {h[:70]}")
    return coverage, reopened


def render_md(slug, result, plan):
    """The human view (architect/structure.md), rendered from the FINAL structure. Called by enrich.py."""
    sections = result["sections"]
    coverage, reopened = compute_coverage(sections, plan)
    n_boxes_used = len({n for s in sections for n in s.get("boxes", [])})   # DISTINCT boxes, not slots
    n_h3 = sum(len(s.get("h3s") or []) for s in sections)
    L = [f"# STRUCTURE — {plan.get('h1', '')}", "",
         f"**Format:** {result['format_archetype']} · **Sections:** {len(sections)} · "
         f"**Authored H3s:** {n_h3} · **Boxes used:** {n_boxes_used}", ""]
    if result.get("entities"):
        kind = "Options" if result["format_archetype"] == "comparison-rankings" else "Items"
        L.append(f"**{kind}:** " + " · ".join(result["entities"]))
    if result.get("yardsticks"):
        L.append("**Yardsticks:** " + " · ".join(result["yardsticks"]))
    if result.get("artifact"):
        a = result["artifact"]
        L.append(f"**The artifact:** {a.get('type', '?')} — {a.get('note', '')}")
    L.append("")
    if result.get("spine"):
        L.append("**The article's spine:** " + result["spine"])
    if result.get("coverage_note"):
        L.append("")
        L.append("**What it left out, and why:** " + result["coverage_note"])
        L.append("")
    for i, s in enumerate(sections, 1):
        tag = "  `[item]`" if s.get("is_item") else ("  `[supporting]`" if result.get("item_fields") else "")
        L.append(f"## {i}. {s['headline']}{tag}")
        if s.get("job"):
            L.append(f"*Job: {s['job']}*")
        if s.get("word_target"):
            L.append(f"*Word target: ~{s['word_target']}*")
        if s.get("table"):
            L.append(f"*Renders a TABLE: {' | '.join(s['table']['columns'])}*")
        if s.get("list"):
            L.append(f"*Renders a {s['list']['kind'].upper()} LIST: {s['list'].get('of', '')}*")
        lead = s.get("lead") or {}
        if lead.get("card_ids"):
            enr = "  [enriched from web research]" if any(_nid_ge_9000(c) for c in lead["card_ids"]) else ""
            L.append(f"- (opening, no sub-heading)  ({len(lead['card_ids'])} cards){enr}")
        for h in s.get("h3s", []):
            enr = "  [enriched from web research]" if any(_nid_ge_9000(c) for c in h.get("card_ids", [])) else ""
            L.append(f"- ### {h['h3']}  ({len(h.get('card_ids', []))} cards){enr}")
        for nr in s.get("needs_research", []):
            topic = nr.get("topic", "") if isinstance(nr, dict) else str(nr)
            dest = nr.get("goes_to", "opening") if isinstance(nr, dict) else "opening"
            L.append(f"- *research requested -> {dest}:* {topic[:110]}")
        L.append("")
    L.append("## Coverage after shaping")
    L.append("- " + " · ".join(f"**{k}:** {v}" for k, v in coverage.items()))
    for r in reopened:
        L.append(f"- REOPENED {r}")
    if result.get("empty_subheadings_removed"):
        L.append("")
        L.append("## Sub-headings removed because the research never filled them")
        for x in result["empty_subheadings_removed"]:
            L.append(f"- **{x.get('section', '?')}** -> \"{x.get('h3', '?')}\"")
    if result.get("research_failures"):
        L.append("")
        L.append("## Research that came back EMPTY — these sections are thinner than designed")
        for x in result["research_failures"]:
            L.append(f"- **{x.get('section', '?')}** → {x.get('h3', '?')}  ({x.get('status', '?')})")
    if result.get("dropped_items"):
        L.append("")
        L.append("## List items dropped to fit the word budget")
        for d in result["dropped_items"]:
            L.append(f"- {d['item']} — {d['why']}")
    if result.get("unused_boxes"):
        L.append("")
        L.append("## Material NOT used")
        explained = [b for b in result["unused_boxes"] if b.get("why_benched")]
        silent = [b for b in result["unused_boxes"] if not b.get("why_benched")]
        for b in explained:
            L.append(f"- [#{b['n']}] {b['h3']}  ({b.get('cards', 0)} cards) — {b['why_benched']}")
        # every benched box now needs a reason (2026-08-08). The old rule only demanded one when the
        # box carried a research promise, and promises no longer reach the architect at all.
        for b in silent:
            L.append(f"- [#{b['n']}] {b['h3']}  ({b.get('cards', 0)} cards)  <-- NO REASON GIVEN")
    if result.get("shared_box_warnings"):
        L.append("")
        L.append(f"## WARNING: boxes used in more than one section: {result['shared_box_warnings']}")
    config.write_text(config.artifact(slug, "structure.md"), "\n".join(L) + "\n")


def _nid_ge_9000(cid):
    try:
        return int(cid) >= 9001
    except (TypeError, ValueError):
        return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Architect Step 1 — SHAPE (free structure design over numbered boxes).")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Architect Step 1: shape — {a.slug} ==")
    run(a.slug, redo=a.redo)
