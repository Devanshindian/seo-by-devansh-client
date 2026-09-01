#!/usr/bin/env python3
"""The review page — one self-contained HTML file per article, for reading and vetting the output.

Called by assemble.py; writes writer/article.html.

What you can do on it:
  - read the finished article exactly as it will publish
  - hover any statistic to see the claim and the source link it carries
  - hover any highlighted phrase to see what it is: the primary keyword, a variation of it, or a
    researched section keyword
  - read the keyword panel at the top: every target phrase, how many times it landed, and whether
    the placement rules (H1, first 100 words, headings, close) were met
"""
import html
import json
import re

import assemble
import config

import tags

CSS = """
:root{--bg:#fffdf8;--ink:#1c1a17;--mut:#6b6459;--line:#efe7d8;--card:#fff;--wash:#fff8ec;
      --pri:#b25a00;--pri-bg:#ffe9ad;--var:#2f6fb0;--var-bg:#eef4fb;--h2k:#fb7a00;--h2k-bg:#ffd9b0;
      --ok:#2e7d43;--no:#c2603a;
      --shadow:0 1px 2px rgba(28,26,23,.04),0 8px 24px rgba(28,26,23,.05)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:16.5px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:780px;margin:0 auto;padding:44px 24px 120px}
h1{font-size:clamp(28px,4.5vw,38px);line-height:1.18;margin:.2em 0 .5em;letter-spacing:-.02em}
h2{font-size:1.32em;margin:2em 0 .6em;padding-top:.5em;border-top:1px solid var(--line);letter-spacing:-.01em}
h3{font-size:1.05em;margin:1.5em 0 .4em}
p{margin:0 0 1.1em}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;
       margin:0 0 32px;box-shadow:var(--shadow)}
.panel h4{margin:0 0 12px;font-size:.72em;letter-spacing:.12em;text-transform:uppercase;color:var(--h2k);font-weight:700}
.kwrow{display:flex;gap:10px;align-items:baseline;padding:5px 0;border-top:1px dashed var(--line);flex-wrap:wrap}
.kwrow:first-of-type{border-top:0}
.kwrow .n{margin-left:auto;color:var(--mut);font-size:.85em;white-space:nowrap}
.kwrow .kind{font-size:.7em;letter-spacing:.08em;text-transform:uppercase;font-weight:700;opacity:.75}
.kwrow .kind.p{color:#b4530f}.kwrow .kind.v{color:#8a6d00}.kwrow .kind.k{color:#4a6a2f}
.why{color:var(--mut);font-size:.85em;margin:2px 0 10px;line-height:1.5}
.chk{display:flex;gap:8px;padding:4px 0;font-size:.92em}
.yes{color:var(--ok)}.no{color:var(--no)}
.tk{background:var(--wash);border:1px solid var(--h2k-bg);border-left:4px solid var(--h2k);
    border-radius:10px;padding:14px 18px;margin:0 0 32px}
.tk li{margin:.35em 0}
mark{padding:1px 3px;border-radius:3px;cursor:help;background:transparent}
mark.p{background:var(--pri-bg);color:var(--pri);font-weight:650}
mark.v{background:var(--var-bg);color:var(--var)}
mark.k{background:var(--h2k-bg);color:#8a4400}
.cite{display:inline-block;min-width:17px;height:17px;line-height:17px;text-align:center;font-size:.66em;
      vertical-align:super;background:var(--wash);border:1px solid var(--line);color:var(--ink);border-radius:4px;
      cursor:help;text-decoration:none;margin-left:1px;padding:0 3px}
.cite:hover{background:var(--h2k);color:#fff;border-color:var(--h2k)}
.ilink{color:var(--h2k);text-decoration:underline;text-decoration-style:dotted;text-underline-offset:3px}
.faq b{display:block;margin:1.4em 0 .3em}
.close{border-top:1px solid var(--line);margin-top:2.5em;padding-top:1.5em}
.src{font-size:.86em;color:var(--mut)}
.src li{margin:.5em 0;overflow-wrap:anywhere}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:.8em;color:var(--mut);margin-top:12px}
.strip{display:flex;gap:26px;flex-wrap:wrap;background:linear-gradient(180deg,var(--wash),var(--card));
       border:1px solid var(--line);border-radius:12px;padding:14px 20px;margin:0 0 20px;box-shadow:var(--shadow)}
.strip b{font-size:1.35em;display:block}
.strip span{color:var(--mut);font-size:.76em}
.trail h2{border-top:0}
.chip{display:inline-block;background:var(--wash);border:1px solid var(--line);border-radius:100px;
      padding:1px 8px;font-size:.7em;color:var(--mut);margin-left:6px;vertical-align:middle}
.chip.warn{color:#9a6700;border-color:var(--pri-bg)}
ins{background:#e8f5ec;color:#2e7d43;text-decoration:none;border-radius:2px;padding:0 1px}
del{background:#fdf3f0;color:#c2603a;border-radius:2px;padding:0 1px}
details.diff{border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin:8px 0;background:var(--card)}
details.diff summary{font-weight:600;cursor:pointer}
.dbody{margin-top:8px;font-size:.93em;line-height:1.7}
.kwlist{margin:.3em 0;padding-left:1.3em}
a{color:var(--h2k)}
table{width:100%;border-collapse:collapse}
.scroll{overflow-x:auto}
[data-tip]{position:relative}
[data-tip]:hover::after{content:attr(data-tip);position:absolute;left:50%;bottom:calc(100% + 8px);
  transform:translateX(-50%);background:#1c1a17;color:#fff;font:400 13px/1.5 -apple-system,BlinkMacSystemFont,
  "Segoe UI",Inter,sans-serif;padding:9px 12px;border-radius:8px;width:max-content;max-width:min(380px,86vw);
  white-space:normal;text-align:left;z-index:60;box-shadow:0 6px 24px rgba(0,0,0,.22);pointer-events:none}
[data-tip]:hover::before{content:"";position:absolute;left:50%;bottom:calc(100% + 2px);transform:translateX(-50%);
  border:6px solid transparent;border-top-color:#1c1a17;z-index:61;pointer-events:none}
.kwrow mark{cursor:help}
"""

JS = ""


def _mark_keywords(text, phrases):
    """Highlight each target phrase, longest first so 'cost per hire' wins over 'hire'."""
    out, spans = text, []
    for phrase, cls, label in sorted(phrases, key=lambda x: -len(x[0])):
        if not phrase:
            continue
        rx = assemble._phrase_re(phrase)
        if rx is None:
            continue
        for m in rx.finditer(out):
            if any(m.start() < e and s < m.end() for s, e, *_ in spans):
                continue                                   # already inside a longer highlight
            spans.append((m.start(), m.end(), cls, label))
    for s, e, cls, label in sorted(spans, reverse=True):
        out = f'{out[:s]}<mark class="{cls}" data-tip="{html.escape(label)}">{out[s:e]}</mark>{out[e:]}'
    return out


_MDLINK = re.compile(r"\[([^\]\[]+)\]\((https?://[^)\s]+)\)")


def _render(text, idx, phrases, numbering, kept=None):
    """Markdown links out first (as placeholders, so keyword marks never land inside a url), then
    escape, keywords, citations, and finally the links back in as real anchors.

    `kept`: url -> number for the curated external sources. When set, a citation renders only if
    its card's url is kept (numbered against the short Sources list); everything else is stripped
    from display — provenance stays in the _work files."""
    links = []

    def stash(m):
        links.append((m.group(1), m.group(2)))
        return f"\x02{len(links) - 1}\x02"

    t = _MDLINK.sub(stash, text)
    t = _mark_keywords(html.escape(t), phrases)

    def cite(found):
        # De-dupe on the REFERENCE NUMBER, not on the rendered anchor: two different cards can share one
        # source url and so one number, and their anchors differ (different tooltip) — that rendered as
        # the same number twice ("[9][9]").
        out, seen_n = [], set()
        for cid in found:
            c = idx.get(cid) or {}
            u = c.get("url")
            if kept is not None:
                if u not in kept:
                    continue
                n = kept[u]
            else:
                n = numbering.setdefault(cid, len(numbering) + 1)
            if n in seen_n:
                continue
            seen_n.add(n)
            tip = (c.get("gloss") or f"card {cid}")[:300] + " — " + (u or "(no link on file)")
            out.append(f'<a class="cite" href="{html.escape(u or "#")}" target="_blank" '
                       f'data-tip="{html.escape(tip)}">{n}</a>')
        return "".join(out)

    t = tags.sub(t, cite)
    t = re.sub(r" +([.,;:])", r"\1", t)
    for i, (anchor, url) in enumerate(links):
        t = t.replace(f"\x02{i}\x02",
                      f'<a class="ilink" href="{html.escape(url)}" target="_blank">{html.escape(anchor)}</a>')
    return _md_to_html(t)


def _md_to_html(t):
    """Turn the writer's markdown into real HTML.

    Until 2026-08-05 this was one line — every block wrapped in <p> — so "### Heading" published as a
    paragraph reading "### Heading" and "**Strong answer.**" published with the asterisks showing. An
    outside review counted 61 such defects across five articles and called it a publication blocker.
    The writers were producing correct markdown the whole time; nothing was converting it.
    """
    out, bullets, rows = [], [], []
    # A NUMBERED list used to publish as plain bullets, throwing the numbers away — and in a numbered
    # list the order IS the meaning ("first do this, then that"). So the list kind is tracked, and a
    # list that does not start at 1 keeps its starting number.
    #
    # `bullets` holds [lead_html, [continuation_html, ...]] per item. Writers habitually put the point
    # on the marker line and its explanation on the NEXT line, unindented:
    #     1. **Executive cost per hire is climbing.**
    #     The 2026 median stands at $15,000 ...
    # That explanation belongs INSIDE the item. Treating it as a fresh paragraph closed the list after
    # one entry, so a five-point list published as five one-item lists each trailed by an orphan
    # paragraph — visibly broken, and the first thing a reader noticed.
    kind = {"tag": "ul", "start": None, "next": None}

    def flush():
        if bullets:
            attr = f' start="{kind["start"]}"' if kind["tag"] == "ol" and kind["start"] not in (None, 1) else ""
            out.append(f"<{kind['tag']}{attr}>"
                       + "".join("<li>" + lead + "".join(f"<p>{x}</p>" for x in extra) + "</li>"
                                 for lead, extra in bullets)
                       + f"</{kind['tag']}>")
            bullets.clear()
            kind.update(tag="ul", start=None, next=None)
        if rows:
            # first row is the header; the |---|---| separator was dropped on the way in
            head, body = rows[0], rows[1:]
            out.append('<div class="scroll"><table><thead><tr>'
                       + "".join(f"<th>{c}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in body)
                       + "</tbody></table></div>")
            rows.clear()

    _MARKER = re.compile(r"^(?:\d+[.)]|[-*•])\s+")
    for block in t.split("\n\n"):
        if not block.strip():
            continue
        lines = [x.strip() for x in block.split("\n") if x.strip()]
        # A blank line does not end a list — the next numbered item usually sits in its own block. But
        # a block that does NOT open with a marker is ordinary prose, and the list ends before it.
        if bullets and lines and not _MARKER.match(lines[0]):
            flush()
        for line in lines:
            # inline: [text](url) -> a real link. FIRST, so the emphasis rules below cannot chew a
            # URL. The writer emits internal links in markdown; nothing here converted them, so they
            # published as literal "[work sample test](https://...)" in the middle of a sentence.
            # The digit-only form "[12]" is a citation marker and has no "(" after it, so it is safe.
            line = re.sub(r"\[([^\]\n]+)\]\((https?://[^)\s]+)\)",
                          r'<a href="\2" target="_blank" rel="noopener">\1</a>', line)
            # inline: **bold** -> <strong>, *italic* -> <em> (never inside an existing tag)
            line = re.sub(r"\*\*(?!\s)([^*]+?)(?<!\s)\*\*", r"<strong>\1</strong>", line)
            line = re.sub(r"(?<![*\w])\*(?!\s)([^*]+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", line)
            h = re.match(r"^(#{2,6})\s+(.*)$", line)
            if h:                                   # a markdown heading becomes a real one
                flush()
                lvl = min(len(h.group(1)), 4)       # never emit h5/h6 inside an article body
                out.append(f"<h{lvl}>{h.group(2)}</h{lvl}>")
                continue
            if line.startswith("|") and line.endswith("|"):     # a markdown table row
                cells = [c.strip() for c in line.strip("|").split("|")]
                if all(set(c) <= set("-: ") for c in cells):       # the |---|---| separator
                    continue
                if bullets:
                    flush()
                rows.append(cells)
                continue
            if rows:                                               # the table just ended
                flush()
            num = re.match(r"^(\d+)[.)]\s+(.*)$", line)
            b = re.match(r"^[-*\u2022]\s+(.*)$", line)
            if num or b:                            # collect consecutive items into one list
                if bullets and ((kind["tag"] == "ol") != bool(num)):
                    flush()                         # a dash list and a numbered list are two lists
                if not bullets:                     # the FIRST item decides the kind, and the start
                    kind.update(tag="ol" if num else "ul",
                                start=int(num.group(1)) if num else None)
                if num:
                    kind["next"] = int(num.group(1)) + 1
                bullets.append([num.group(2) if num else b.group(1), []])
                continue
            if bullets:                             # an unindented line under an item explains it
                bullets[-1][1].append(line)
                continue
            flush()
            out.append(f"<p>{line}</p>")
        if not bullets:            # tables and prose still close at the block boundary
            flush()
    flush()                        # anything still open at the end of the document
    return "".join(out)


def _word_diff(a, b):
    """Word-level before/after: deletions struck red, insertions green."""
    import difflib
    aw, bw = a.split(), b.split()
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, aw, bw).get_opcodes():
        if op == "equal":
            out.append(html.escape(" ".join(aw[i1:i2])))
        else:
            if op in ("delete", "replace"):
                out.append(f"<del>{html.escape(' '.join(aw[i1:i2]))}</del>")
            if op in ("insert", "replace"):
                out.append(f"<ins>{html.escape(' '.join(bw[j1:j2]))}</ins>")
    return " ".join(out)


def _norm(t):
    return " ".join((t or "").split())


def _trail(slug, w):
    """The article page's foot: a link out to the page for every step that touched this article.

    It used to hold the whole audit — the editor's diffs, the wrapper's touch-ups, the scrub receipt —
    which meant one page carried five steps' work while COHERENCE was shown nowhere at all. Each step
    now owns exactly one page (eval_pages.build_body / _editor / _wrapper_page / _coherence / _clean),
    so this is a signpost, not a second copy of what those pages say.
    """
    import json as _json
    import os as _os
    bp, lp = config.artifact(slug, "body.json"), config.artifact(slug, "blend.json")
    if not (_os.path.exists(bp) and _os.path.exists(lp)):
        return "", []
    body, bl = _json.load(open(bp)), _json.load(open(lp))
    orig = {}
    for x in body["sections"]:
        p = x["prose"]
        orig[x["headline"]] = p.split(chr(10), 1)[-1].strip() if p.startswith("##") else p
    edited = {x["heading"]: x["prose"] for x in bl["sections"]}
    changed = sum(1 for h, a in edited.items() if _norm(orig.get(h, "")) != _norm(a))

    STEPS = [("body-review.html", "1 · The first draft",
              "every section as its own writer produced it, against its word budget"),
             ("editor-review.html", "2 · The editor",
              "what it joined, what it cut, the keywords woven in, and the source-tag audit"),
             ("wrapper-review.html", "3 · The wrapper",
              "the intro, the FAQ and the close, and the two seams they create"),
             ("coherence-review.html", "4 · Coherence",
              "the only pass that reads the whole article at once, and what it rewrote"),
             ("slop-review.html", "5 · The slop pass",
              "every AI writing tell removed, with the before and after"),
             ("links-review.html", "6 · The links",
              "every internal, read-more and external link, and why it was chosen"),
             ("clean-review.html", "7 · The scrub",
              "the mechanical character clean-up. Pure code, no judgment")]
    here = _os.path.dirname(config.artifact(slug, "article.html"))
    rows = "".join(
        (f'<li><a href="{f}"><b>{html.escape(t)}</b></a> — <span class="q">{html.escape(d)}</span></li>'
         if _os.path.exists(_os.path.join(here, f)) else
         f'<li><b>{html.escape(t)}</b> — <span class="q">{html.escape(d)}</span> '
         '<span class="chip warn">page not built for this run</span></li>')
        for f, t, d in STEPS)

    trail = ('<div class="trail"><h2>How this article was built</h2>'
             '<p class="why">Sections are written independently, so they arrive reading like strangers. Seven '
             'steps then repair them. Each step has its own page showing exactly what it changed and why, and '
             'every change it made had to be declared. This page is only the finished article.</p>'
             f'<ul class="kwlist">{rows}</ul>'
             '<p class="why">Start at <a href="../index.html">the front door</a> to see the whole pipeline, '
             'including the research and planning that ran before any of this.</p></div>')

    body_words = sum(len(p.split()) for p in orig.values())
    stats = [("words the section writers produced, before editing", body_words),
             (f"edits the editor declared — {changed} section(s) actually changed",
              len(bl.get("edits") or [])),
             (f"keywords placed into the text — {len(bl.get('keywords_skipped') or [])} skipped",
              len(bl.get("keywords_used") or [])),
             # BOTH steps, not just the wrapper. This tile read only the wrapper's count, so an invented
             # tag caught at the blend step never reached the page.
             ("made-up source tags caught, editor + wrapper (0 is good)",
              (bl.get("tag_audit") or {}).get("invented_stripped", 0) + w.get("invented_tags_stripped", 0))]
    return trail, stats


def _render_leaks(page):
    """Every markdown construct that survived into the rendered page. Returns [(kind, sample)].

    Only the article BODY is checked — the review panels legitimately contain markdown-looking text
    when they quote the writer's own before/after, and flagging those would cry wolf every run.
    """
    body = page.split('<div class="trail">')[0]          # panels and diffs live after the article
    found = []
    for kind, rx in (("heading (###)", r"<(?:p|li)[^>]*>\s*#{2,6}\s"),
                     ("bold (**)", r"\*\*[^*<]{1,80}\*\*"),
                     ("table row (|--)", r"\|\s*-{2,}"),
                     ("bare pipe row", r"<(?:p|li)[^>]*>\s*\|.*\|\s*</(?:p|li)>"),
                     # an unconverted link publishes as "[work sample test](https://...)" mid-sentence
                     ("link ([text](url))", r"\[[^\]\n]{1,90}\]\(\s*https?://")):
        for m in re.finditer(rx, body):
            lo = max(0, m.start() - 40)
            found.append((kind, re.sub(r"\s+", " ", body[lo:m.end() + 60])))
    return found


def _reads_banner():
    """Point at the clean read. This page is for tracing a statistic, not for reading the article."""
    return ('<div class="panel"><p><b>This is the marked-up copy.</b> Every keyword is highlighted '
            'and every statistic carries a hover tooltip, which is useful for checking our working '
            'and distracting if you just want to read. '
            '<a href="reads/assemble.html">Open the clean article</a>, or '
            '<a href="reads/index.html">read it after every step</a>.</p></div>')


def build(slug, w, ks, idx, cov, sources=None):
    primary = ks.get("primary") or ""
    variations = [v for v in (ks.get("variations") or []) if v]
    h2kw = [k.get("keyword") for k in (ks.get("h2_keywords") or []) if k.get("keyword")]
    phrases = ([(primary, "p", f"PRIMARY keyword — {primary}")]
               + [(v, "v", f"variation of the primary — {v}") for v in variations]
               + [(k, "k", f"researched section keyword — {k}") for k in h2kw])
    numbering = {}
    # ONE SOURCE LIST, DECIDED ONCE. `sources` is the list assemble.py just published, in its order,
    # so this page shows the same numbers against the same urls as draft.md — curated or not. It used
    # to rebuild its own list here and could therefore disagree with the article it was reviewing.
    # (Passing kept=None makes _render number per CARD, which double-numbers two cards sharing one
    # url, so the map is always built complete before it is handed over.)
    if sources is not None:
        kept = {u: i for i, u in enumerate(sources, 1)}
    else:
        kept, seen = {}, set()
        for _h, txt in ([("intro", w.get("intro") or "")]
                        + [(s_["heading"], s_.get("prose") or "") for s_ in w.get("sections") or []]
                        + [("faq", f.get("answer") or "") for f in w.get("faq") or []]
                        + [("close", w.get("close") or "")]):
            for cid in tags.ids(txt):
                u = (idx.get(cid) or {}).get("url")
                if u and u not in seen:
                    seen.add(u)
                    kept[u] = len(kept) + 1
    trail, tstats = _trail(slug, w)

    KIND = {"p": "PRIMARY KEYWORD", "v": "variation of the primary", "k": "section keyword (researched)"}

    def row(c, cls):
        bits = []
        if c["in_h1"]: bits.append("H1")
        if c["in_first_100_words"]: bits.append("first 100w")
        if c["in_headings"]: bits.append(f"{c['in_headings']} heading(s)")
        if c["in_close"]: bits.append("close")
        return (f'<div class="kwrow"><mark class="{cls}" data-tip="{html.escape(KIND[cls])}: {html.escape(c["phrase"])} — appears {c["total"]}x in the article">{html.escape(c["phrase"])}</mark>'
                f'<span class="kind {cls}">{KIND[cls]}</span>'
                f'<span class="n">appears {c["total"]}x'
                + (" · in " + " · ".join(bits) if bits else " · not in any key position") + "</span></div>")

    final_words = len(" ".join([w.get("intro") or ""]
                               + [x["prose"] for x in w["sections"]]
                               + [f'{f["question"]} {f["answer"]}' for f in (w.get("faq") or [])]
                               + [w.get("close") or ""]).split())
    strip = ('<div class="strip">'
             + "".join(f'<div><b>{html.escape(str(v))}</b><span>{html.escape(str(k))}</span></div>'
                       for k, v in [("final words", final_words)] + tstats)
             + "</div>")
    panel = [strip,
             '<p class="why">The article is written in sections by separate calls, then an editor stitches '
             'them together and weaves the keywords in. The numbers above are the receipts for that: how much '
             'text was produced, how much the editor touched, and whether it tried to fake a source.</p>',
             '<div class="panel"><h4>Keywords this article targets</h4>',
             '<p class="why">Three kinds. The <b>primary keyword</b> is the one phrase this article is meant to '
             'rank for. A <b>variation</b> is another way people phrase the same search. A <b>section keyword</b> '
             'is a related phrase researched for one specific H2. Each row shows how often it landed and whether '
             'it reached the places that matter.</p>',
             row(cov["primary"], "p")]
    panel += [row(v, "v") for v in cov["variations"]]
    panel += [row(k, "k") for k in cov["h2_keywords"]]
    panel.append('<h4 style="margin-top:16px">Placement checks</h4>')
    for k, v in cov["checklist"].items():
        panel.append(f'<div class="chk"><span class="{"yes" if v else "no"}">{"✓" if v else "✗"}</span>'
                     f'<span>{html.escape(k)}</span></div>')
    panel.append('<div class="legend"><span><mark class="p">primary</mark></span>'
                 '<span><mark class="v">variation</mark></span>'
                 '<span><mark class="k">researched keyword</mark></span>'
                 '<span>hover a number for its source</span></div></div>')

    # THIS PAGE IS THE MARKED-UP ONE (2026-08-13). Keyword highlights, hover tooltips, a scoring
    # panel. Anyone who just wants to read the article should be sent one door earlier, so say so.
    body = [_reads_banner(),
            f'<h1>{_mark_keywords(html.escape(w.get("h1") or ""), phrases)}</h1>',
            _render(w.get("intro") or "", idx, phrases, numbering, kept)]
    for s in w["sections"]:
        body.append(f'<h2>{_mark_keywords(html.escape(s["heading"]), phrases)}</h2>')
        body.append(_render(s["prose"], idx, phrases, numbering, kept))
    if w.get("faq"):
        body.append('<h2>Frequently asked questions</h2><div class="faq">')
        for f in w["faq"]:
            origin = '<span class="chip">from real searches</span>' if (f.get("origin") or "").startswith("resear") \
                     else '<span class="chip">added by the editor</span>'
            # LENGTH, not draws_on (2026-08-11). An FAQ answer is what a search engine lifts and shows
            # on its own, so an over-long one fails at the only job it has.
            n = f.get("words") or len((f.get("answer") or "").split())
            drew = ('<span class="chip no">%d words</span>' % n if f.get("over_target") else
                    '<span class="chip">%d words</span>' % n)
            body.append(f'<b>{html.escape(f["question"])} {origin}{drew}</b>'
                        f'{_render(f["answer"], idx, phrases, numbering, kept)}')
        body.append("</div>")
    body.append(f'<div class="close">{_render(w.get("close") or "", idx, phrases, numbering, kept)}</div>')

    if kept:
        srcs = "".join(f'<li>{n}. <a href="{html.escape(u)}" target="_blank">{html.escape(u[:90])}</a></li>'
                       for u, n in sorted(kept.items(), key=lambda kv: kv[1]))
    else:
        srcs = "".join(
            f'<li>{n}. {html.escape((idx.get(cid) or {}).get("gloss") or f"card {cid}")} — '
            f'<a href="{html.escape((idx.get(cid) or {}).get("url") or "#")}" target="_blank">'
            f'{html.escape(((idx.get(cid) or {}).get("url") or "(no link on file)")[:80])}</a></li>'
            for cid, n in sorted(numbering.items(), key=lambda kv: kv[1]))

    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(w.get("h1") or slug)}</title><style>{CSS}</style></head><body>'
            f'<div class="wrap">'
            + "".join(panel) + "".join(body)
            + f'<h2>Sources</h2><ol class="src">{srcs}</ol>'
            + trail
            + f'</div><script>{JS}</script></body></html>')

    # THE RENDER GATE (2026-08-05). An outside review counted 61 markdown defects across five published
    # articles and called it a publication blocker: "### Heading" and "**bold**" reaching the page as
    # literal text. _md_to_html now converts them, but a converter only handles the patterns it knows.
    # This is the backstop: anything markdown-shaped that survives into the BODY is reported loudly with
    # the offending line, so it is caught here rather than by a reviewer reading the live page.
    leaks = _render_leaks(page)
    if leaks:
        print(f"  !! RENDER GATE: {len(leaks)} markdown leak(s) reached the page — fix before publishing")
        for kind, sample in leaks[:8]:
            print(f"       {kind}: {sample[:96]}")
    else:
        print("  render gate: clean — no markdown reached the page")

    out = config.artifact(slug, "article.html")
    config.write_text(out, page)
    return out
