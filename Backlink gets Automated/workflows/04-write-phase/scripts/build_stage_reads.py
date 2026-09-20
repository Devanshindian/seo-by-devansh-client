#!/usr/bin/env python3
"""READ THE ARTICLE AS IT STANDS AFTER EACH WRITER STEP.

  COMPANY=<slug> python3 build_stage_reads.py --slug <slug>

Every step already has a review page showing WHAT IT CHANGED: diffs, counts, flags. None of them
showed the thing a human actually wants to check, which is whether the article reads well now. So a
reviewer could see that blend cut a repetition and still have no idea what the article looked like
afterwards.

This builds one clean page per step, in the SAME style as the published article: no highlights, no
tooltips, no scoring panel. Just the piece as it stands at that moment.

  write-body -> the sections, as written, blind to each other
  blend      -> the same sections, joined and cut
  wrapper    -> now with the H1, the intro, the FAQ and the close
  coherence  -> after the contradictions were fixed
  slop       -> after the AI writing tells were stripped
  links      -> now with internal links, and only the sources that survived the cut
  clean      -> after the character and spacing scrub
  assemble   -> the finished article, exactly as it would publish

Reads:  whichever writer/_work file that step wrote (draft.md for assemble).
Writes: writer/reads/<step>.html, plus writer/reads/index.html listing them.

Read-only: it opens finished output and writes pages. It never runs a step and never edits a draft.
"""
import argparse
import html
import json
import os
import re

import config
import build_share_site as share
import review_page
import assemble
import tags

# (step, the file it wrote, does that file hold the whole article or only the sections)
STAGES = [
    ("write-body", "body.json", "sections", "Every section as its own writer produced it. None of them could see another, so the joins are rough on purpose."),
    ("blend", "blend.json", "sections", "The same sections, joined into one piece and cut back: repetition, fluff, a point that never landed."),
    ("wrapper", "wrapper.json", "full", "Now it is a whole article. The title, the opening, the FAQ and the close have been written around the body."),
    ("coherence", "coherent.json", "full", "After the only step that reads the whole thing at once and fixes what contradicts itself."),
    ("readable", "readable.json", "full", "After the whole article was rewritten to be read. Every fact, source tag and section is unchanged; only the wording moved."),
    ("sentences", "sentences.json", "full", "After the sentences were re-shaped. Nothing was added or deleted: same length, same facts, same sections. The three-clause sentences were split, and the formal word swapped for the one a person says out loud."),
    ("slop", "polish.json", "full", "After the AI writing tells were stripped: em dashes, hollow words, bold scattered about."),
    ("links", "linked.json", "full", "Now carrying internal links, and only the sources that survived the cut. Everything else stays as internal provenance."),
    ("clean", "scrubbed.json", "full", "After the mechanical scrub. Invisible characters, lookalike hyphens, spacing. No word was rewritten."),
    ("assemble", "draft.md", "markdown", "The finished article, exactly as it would publish."),
]

STAGE_ORDER = [s[0] for s in STAGES]


def _sections_md(secs):
    """body.json calls it 'headline', every later file calls it 'heading'. Both land here."""
    out = []
    for s in secs or []:
        head = s.get("heading") or s.get("headline") or ""
        prose = str(s.get("prose") or "").strip()
        # the body writer repeats its own "## Heading" line; later steps do not
        if prose.startswith("##"):
            prose = prose.split("\n", 1)[-1].strip()
        out.append(f"## {head}\n\n{prose}")
    return "\n\n".join(out)


def _kept_urls(slug):
    """The source list the finished article actually published, or None if it has none yet.

    From the links step onward the article credits ONLY these, numbered 1..N — so the reads for
    links and clean must do the same, or they show a reader thirty sources the finished page does
    not. Everything before links still shows all of them: nothing has been curated at that moment,
    and hiding sources there would misrepresent the file.

    Read from draft.md, NOT from linked.json's external_kept, because assemble owns this decision:
    when curating would leave too many sections looking unsourced it credits everything instead, and
    a read built off the curated list would then contradict the very article it is showing. Whatever
    assemble published is the answer. linked.json is only the fallback for a run that stopped before
    assemble.
    """
    draft = config.artifact(slug, "draft.md")
    if os.path.exists(draft):
        parts = open(draft).read().split("## Sources")
        if len(parts) > 1:
            urls = re.findall(r"^\s*\d+\.\s*(\S+)", parts[-1], re.M)
            return urls or None
    p = config.artifact(slug, "linked.json")
    if not os.path.exists(p):
        return None
    urls = [k["url"] for k in ((json.load(open(p)).get("links") or {}).get("external_kept") or [])]
    return urls or None


def _number_refs(md, idx, only=None):
    """[c412] -> [7], plus the source list those numbers point at.

    Until 2026-08-13 these pages printed the raw tag: a reader met "[c39][c94]" mid-sentence with no
    way to reach the source behind it. The published article has never done that — assemble numbers
    every tag against a Sources list and share renders each number as a link. So do exactly that
    here, with the SAME numbering rule (per URL, not per card, so two cards on one source share one
    number) and the same renderer, and every stage reads like the finished page.

    A card with no url cannot be credited, so its tag is dropped from display — same as assemble.
    Provenance for those still lives in the _work files.
    """
    order, num_of = [], {}

    def one(found):
        out = []
        for cid in found:
            u = (idx.get(cid) or {}).get("url")
            if not u:
                continue
            if only is not None and u not in only:
                continue
            if u not in num_of:
                order.append(u)
                num_of[u] = len(order)
            out.append(str(num_of[u]))
        return ("[" + "][".join(dict.fromkeys(out)) + "]") if out else ""

    return re.sub(r" +([.,;:])", r"\1", tags.sub(md, one)), order


def _stage_md(slug, fname, kind):
    """The article as markdown, at one stage. None when that step has not run."""
    p = config.artifact(slug, fname)
    if not os.path.exists(p):
        return None
    if kind == "markdown":
        return open(p).read()
    d = json.load(open(p))
    if kind == "sections":
        return _sections_md(d.get("sections"))
    parts = []
    if d.get("h1"):
        parts.append(f"# {d['h1']}")
    if d.get("intro"):
        parts.append(str(d["intro"]).strip())
    if d.get("quick_answer"):
        parts += ["## TL;DR", str(d["quick_answer"]).strip()]
    parts.append(_sections_md(d.get("sections")))
    # Close, then FAQ — the order assemble publishes in (2026-08-20). These reads exist to show the
    # article as it stands, so they follow the finished page rather than the order of the JSON keys.
    if d.get("close"):
        if d.get("close_heading"):
            parts.append(f"## {d['close_heading']}")
        parts.append(str(d["close"]).strip())
    if d.get("faq"):
        parts.append("## Frequently asked questions")
        for f in d["faq"]:
            parts.append(f"**{f.get('question','')}**\n\n{str(f.get('answer') or '').strip()}")
    return "\n\n".join(x for x in parts if x)


def _nav(slug, now, built):
    """One row of step links, so you can walk the article forward without going back to the index."""
    bits = []
    for name, _, _, _ in STAGES:
        if name == now:
            bits.append(f'<b>{html.escape(name)}</b>')
        elif name in built:
            bits.append(f'<a href="{html.escape(name)}.html">{html.escape(name)}</a>')
        else:
            bits.append(f'<span class="off">{html.escape(name)}</span>')
    return ('<div class="stagenav"><span class="k">the article after</span>'
            + " → ".join(bits)
            + f'<a class="back" href="../../index.html">back to the steps</a></div>')


EXTRA_CSS = """
.stagenav{max-width:760px;margin:0 auto;padding:14px 24px;font-size:13.5px;
 border-bottom:1px solid #efe7d8;background:#fffdf8;line-height:2.1}
.stagenav .k{display:block;font-size:11px;font-weight:700;letter-spacing:.1em;
 text-transform:uppercase;color:#6b6459;margin-bottom:2px}
.stagenav a{color:#6b6459;text-decoration:none;border-bottom:1px solid #ffe9ad}
.stagenav a:hover{color:#1c1a17;border-bottom-color:#fb7a00}
.stagenav b{color:#1c1a17}
.stagenav .off{color:#c9c2b6}
.stagenav .back{float:right;border:none;color:#fb7a00}
.whatis{max-width:760px;margin:0 auto 8px;padding:14px 0 0;color:#6b6459;font-size:15px}
"""


def build(slug):
    built, made = [], []
    # first pass: which stages exist, so the nav can grey out the ones that never ran
    have = [(n, f, k, blurb) for n, f, k, blurb in STAGES
            if os.path.exists(config.artifact(slug, f))]
    names = [n for n, _, _, _ in have]

    outdir = os.path.join(os.path.dirname(config.artifact(slug, "body.json")), "..", "reads")
    outdir = os.path.normpath(outdir)
    os.makedirs(outdir, exist_ok=True)      # write_text is atomic, so the folder has to exist first

    idx = assemble._card_index(slug)
    kept = _kept_urls(slug)

    for name, fname, kind, blurb in have:
        md = _stage_md(slug, fname, kind)
        if not md or not md.strip():
            continue
        if kind == "markdown":                      # assemble already numbered its own tags
            h1, body_md, srcs = share._split(md)
        else:                                       # every earlier stage still carries raw [c] tags
            h1 = ""
            after_links = STAGE_ORDER.index(name) >= STAGE_ORDER.index("links")
            body_md, srcs = _number_refs(md, idx, only=kept if after_links else None)
        body_html = review_page._md_to_html(body_md)
        if srcs:
            body_html = share._cite_links(body_html, srcs)
        title = h1 or (json.load(open(config.artifact(slug, "wrapper.json"))).get("h1")
                       if os.path.exists(config.artifact(slug, "wrapper.json")) else "") or slug
        head = f"<h1>{html.escape(title)}</h1>" if kind != "markdown" or not h1 else f"<h1>{html.escape(h1)}</h1>"
        page = share._page(
            f"{title} — after {name}",
            f'<p class="whatis">{html.escape(blurb)}</p>{head}{body_html}'
            + (share._srcs_block(srcs) if srcs else ""),
            nav=_nav(slug, name, names))
        page = page.replace("</style>", EXTRA_CSS + "</style>")
        out = os.path.join(outdir, f"{name}.html")
        config.write_text(out, page)
        built.append(name)
        made.append((name, out, len(body_md.split())))

    if made:
        rows = "".join(
            f'<div class="card"><h3><a href="{html.escape(n)}.html">after {html.escape(n)}</a></h3>'
            f'<p class="slug">{w:,} words</p></div>' for n, _, w in made)
        idx = share._page(f"{slug} — the article at every step",
                          f"<h1>The article at every step</h1>"
                          f'<p class="whatis">The same piece, read at each stage of the writer. '
                          f'Nothing here is a diff or a report; it is what a reader would see if we '
                          f'stopped there.</p>{rows}', nav="")
        config.write_text(os.path.join(outdir, "index.html"), idx)

    print(f"  reads: {len(made)} stage page(s) -> {outdir}")
    for n, _, w in made:
        print(f"    {n:<11} {w:,} words")
    return outdir


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build one clean read of the article per writer step.")
    ap.add_argument("--slug", required=True)
    build(ap.parse_args().slug)
