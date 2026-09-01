#!/usr/bin/env python3
"""Build the SHARE SITE — the clean, public pages a reviewer reads.

Reads:  writer/draft.md for every finished slug (the single source of truth for the article).
Writes: projects/<company>/04-write-phase/share/  — index.html + per article:
          <slug>.html   the article as it would publish: no keyword highlights, no scoring panel,
                        no hover tooltips. Citations are small superscript links to the source.
          <slug>.md     the raw draft, offered as a download from the article page.

There was briefly a second "draft" PAGE alongside each article. It was dropped: a properly previewed
markdown draft IS the article, so the two pages differed only in whether "[2]" was a link. Two links
that look different but are not is worse than one link.

Why not reuse writer/article.html: that page is the REVIEW artifact. It carries 44 keyword
highlights, 158 hover tooltips and a scoring panel above the article. A reviewer opening it reads
our SEO machinery instead of the article, which biases exactly the judgement we are asking for.

Markdown -> HTML goes through review_page._md_to_html, so lists, tables and headings render the same
way here as in the published article and there is only one converter to keep correct.

One exception to "no SEO machinery on this page": a single Keywords panel sits above the article,
read straight from writer/_work/keyword-coverage.json. It is a summary, not inline highlighting, so
the article below it still reads clean. Every figure in it is lifted from that file; nothing here
recounts or re-decides anything.
"""
import argparse
import html
import json
import os
import re

import config
import review_page

CSS = """
:root{--bg:#fffdf8;--ink:#1c1a17;--mut:#6b6459;--line:#efe7d8;--card:#fff;--wash:#fff8ec;
--acc:#b25a00;--pink:#c2185b;--pinkwash:#fdf1f5;--pinkline:#f4d3e0;
--shadow:0 1px 2px rgba(28,26,23,.04),0 8px 24px rgba(28,26,23,.05)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:17px/1.75 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:760px;margin:0 auto;padding:40px 24px 120px}
/* The FAQ collapses. Colours come from the variables above so it follows the dark theme; the first
   version hardcoded near-black text and vanished for anyone whose device is set to dark. */
details.faq{border-bottom:1px solid var(--line)}
details.faq summary{list-style:none;cursor:pointer;padding:15px 30px 15px 0;position:relative;
 font-weight:600;font-size:17px;line-height:1.45;color:var(--ink)}
details.faq summary::-webkit-details-marker{display:none}
details.faq summary:hover{color:var(--acc)}
details.faq summary::after{content:"+";position:absolute;right:4px;top:13px;font-size:22px;
 font-weight:400;color:var(--mut);transition:.15s}
details.faq[open] summary{color:var(--acc)}
details.faq[open] summary::after{content:"\2013";color:var(--acc)}
details.faq .a{padding:0 30px 18px 0;color:var(--ink)}
details.faq .a p{margin:0 0 10px}
details.faq .a p:last-child{margin-bottom:0}
h1{font-size:clamp(28px,4.5vw,38px);line-height:1.22;margin:.2em 0 .5em;letter-spacing:-.02em}
/* every subheading in the article is pink; the H1 and the index cards stay ink */
h2{font-size:clamp(21px,2.8vw,25px);line-height:1.3;margin:2.2em 0 .5em;letter-spacing:-.01em;
color:var(--pink)}
h3{font-size:18px;margin:1.7em 0 .4em;color:var(--pink)}
.card h3{color:var(--ink)}
p{margin:0 0 1.1em}
ul,ol{margin:0 0 1.2em;padding-left:1.5em}
li{margin:0 0 .55em}
li>p{margin:.4em 0 .2em}
a{color:var(--acc)}
sup a,a.cite{font-size:.72em;text-decoration:none;padding:0 .12em;vertical-align:super;font-weight:600}
.scroll{overflow-x:auto;margin:0 0 1.4em;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:15px;background:var(--card);
box-shadow:var(--shadow);border-radius:8px;overflow:hidden}
th,td{padding:10px 13px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--wash);font-weight:650;font-size:13.5px;letter-spacing:.02em}
tr:last-child td{border-bottom:none}
.bar{border-bottom:1px solid var(--line);background:var(--card);position:sticky;top:0;z-index:5}
.bar .in{max-width:760px;margin:0 auto;padding:13px 24px;display:flex;gap:18px;align-items:baseline;
flex-wrap:wrap;font-size:14px}
.bar a{text-decoration:none;color:var(--mut)}
.bar a:hover{color:var(--acc)}
.bar .now{color:var(--ink);font-weight:650}
.meta{color:var(--mut);font-size:14.5px;margin:0 0 2.4em;padding-bottom:1.4em;
border-bottom:1px solid var(--line)}
.srcs{margin-top:3.5em;padding-top:1.6em;border-top:1px solid var(--line)}
.srcs h2{margin-top:0;font-size:19px}
.srcs ol{font-size:14px;line-height:1.6;color:var(--mut);word-break:break-word}
.srcs li{margin-bottom:.45em}
.cards{display:grid;gap:16px;margin:2em 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:20px 22px;
box-shadow:var(--shadow)}
.card h3{margin:0 0 .3em;font-size:19px;letter-spacing:-.01em}
.card .n{color:var(--mut);font-size:13.5px;margin:0 0 .9em}
.card .go{display:flex;gap:10px;flex-wrap:wrap}
.card .go a{display:inline-block;text-decoration:none;font-size:14px;font-weight:600;
padding:7px 14px;border-radius:7px;border:1px solid var(--line)}
.card .go a.p{background:var(--acc);color:#fff;border-color:var(--acc)}
.lead{font-size:18px;color:var(--mut);margin:0 0 2em;max-width:60ch}
/* the draft view: same content, shown as the writer handed it over */
.draft{font-size:16px}
.draft .mk{color:#b0a08a;font-weight:400}
/* the Keywords panel — a summary above the article, never inline in the prose */
.kw{background:var(--pinkwash);border:1px solid var(--pinkline);border-radius:11px;
padding:20px 22px 6px;margin:0 0 2.6em}
.kw .t{margin:0 0 .15em;font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
color:var(--pink)}
.kw .n{margin:0 0 1.1em;font-size:14px;color:var(--mut)}
.kw .p{margin:0 0 1em;font-size:17px}
.kw .p b{color:var(--pink)}
.kw table{background:transparent;box-shadow:none;font-size:14.5px}
.kw th{background:transparent;color:var(--pink);border-bottom:1px solid var(--pinkline)}
.kw td{border-bottom:1px solid var(--pinkline)}
.kw .k{font-weight:650}
.kw .no{color:var(--mut)}
.kw .chk{list-style:none;padding:0;margin:0 0 1.2em;font-size:14.5px;color:var(--mut)}
.kw .chk li{margin:0 0 .3em}
.kw .chk .y{color:var(--pink);font-weight:700}
@media (prefers-color-scheme: dark){
:root{--bg:#171512;--ink:#efe9e0;--mut:#a49b8d;--line:#2e2a24;--card:#1e1b17;--wash:#241f19;--acc:#e08a2e;
--pink:#ff8fb1;--pinkwash:#26191f;--pinkline:#3d2731}
}
"""


def _page(title, body, nav=""):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><style>{CSS}</style></head><body>'
            f'{nav}<div class="wrap">{body}</div></body></html>')


_Q = re.compile(r"<p><strong>(.+?)</strong></p>", re.S)


def _faq_details(page_html):
    """Collapse the FAQ into click-to-open rows.

    The FAQ renders as a run of alternating "<p><strong>question</strong></p>" and answer
    paragraphs. Five open answers push everything after them a screen and a half down, and a reader
    scrolling for the end reads none of them. Collapsed, the whole set is scannable in one look.

    Only the FAQ block is touched: everything before the heading, and everything from the next <h2>
    onward, comes through untouched.
    """
    m = re.search(r"<h2>Frequently asked questions</h2>", page_html, re.I)
    if not m:
        return page_html
    head, rest = page_html[:m.end()], page_html[m.end():]
    nxt = re.search(r"<h2>", rest)
    block, tail = (rest[:nxt.start()], rest[nxt.start():]) if nxt else (rest, "")
    parts = _Q.split(block)                       # [before, q1, a1, q2, a2, ...]
    if len(parts) < 3:
        return page_html
    out = [parts[0]]
    for i in range(1, len(parts) - 1, 2):
        out.append(f'<details class="faq"><summary>{parts[i]}</summary>'
                   f'<div class="a">{parts[i + 1].strip()}</div></details>')
    return head + "".join(out) + tail


def _split(md):
    """(h1, body_markdown, [source urls]) — the Sources block is rendered separately, not as prose."""
    lines = md.split("\n")
    h1 = lines[0].lstrip("# ").strip() if lines and lines[0].startswith("# ") else ""
    rest = "\n".join(lines[1:]) if h1 else md
    parts = re.split(r"\n##\s+Sources\s*\n", rest)
    body = parts[0].strip()
    srcs = []
    if len(parts) > 1:
        for ln in parts[1].split("\n"):
            m = re.match(r"^\s*\d+\.\s*(\S+)", ln)
            if m:
                srcs.append(m.group(1))
    return h1, body, srcs


def _cite_links(html_text, srcs):
    """Turn the plain [12] markers into superscript links to source 12."""
    def one(m):
        n = int(m.group(1))
        if not (1 <= n <= len(srcs)):
            return m.group(0)
        return f'<sup><a href="{html.escape(srcs[n-1])}" target="_blank" rel="noopener">{n}</a></sup>'
    return re.sub(r"\[(\d{1,3})\]", one, html_text)


def _srcs_block(srcs):
    if not srcs:
        return ""
    items = "".join(f'<li><a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(u)}</a></li>'
                    for u in srcs)
    return f'<div class="srcs"><h2>Sources</h2><ol>{items}</ol></div>'


def _where(e):
    """Plain-English 'where it lands' for one keyword row. Pure assembly of the coverage fields."""
    bits = []
    if e.get("in_h1"):
        bits.append("the title")
    if e.get("in_first_100_words"):
        bits.append("the first 100 words")
    n_h = e.get("in_headings") or 0
    if n_h:
        bits.append(f"{n_h} subheading{'s' if n_h > 1 else ''}")
    n_s = len(e.get("sections") or [])
    if n_s:
        bits.append(f"{n_s} section{'s' if n_s > 1 else ''}")
    if e.get("in_close"):
        bits.append("the closing line")
    return ", ".join(bits) if bits else '<span class="no">not used in the draft</span>'


def _kw_block(slug):
    """The Keywords panel: primary, its variations, and the per-section keywords the architect picked.

    Reads writer/_work/keyword-coverage.json — the one file that already measured all of this against
    the finished draft. Returns "" when a run predates that file, so older articles still build.
    """
    p = config.artifact(slug, "keyword-coverage.json")
    if not os.path.exists(p):
        return ""
    cov = json.load(open(p))
    prim = cov.get("primary") or {}
    if not prim.get("phrase"):
        return ""

    rows = [(prim, "Primary")]
    seen = {prim["phrase"].lower()}
    for v in cov.get("variations") or []:
        if v.get("phrase") and v["phrase"].lower() not in seen:
            seen.add(v["phrase"].lower())
            rows.append((v, "Variation"))
    for k in cov.get("h2_keywords") or []:          # the architect's per-section picks
        if k.get("phrase") and k["phrase"].lower() not in seen:
            seen.add(k["phrase"].lower())
            rows.append((k, "Section keyword"))

    body = "".join(
        f'<tr><td class="k">{html.escape(e["phrase"])}</td><td>{role}</td>'
        f'<td>{e.get("total", 0)}</td><td>{_where(e)}</td></tr>'
        for e, role in rows)

    total = cov.get("primary_plus_variations_total", prim.get("total", 0))
    words = (cov.get("length") or {}).get("words") or 0
    dens = f" — {total / words * 100:.2f}% of the {words:,} words" if words else ""

    chk = "".join(f'<li><span class="y">{"Yes" if ok else "No"}</span> &middot; {html.escape(q)}</li>'
                  for q, ok in (cov.get("checklist") or {}).items())
    chk = f'<ul class="chk">{chk}</ul>' if chk else ""

    return (
        '<div class="kw"><p class="t">Keywords</p>'
        '<p class="n">What this article is written to rank for, counted against the finished draft.</p>'
        f'<p class="p"><b>{html.escape(prim["phrase"])}</b> is the primary keyword. '
        f'It and its variations appear {total} times{dens}.</p>'
        f'{chk}'
        '<div class="scroll"><table><thead><tr><th>Keyword</th><th>Role</th><th>Uses</th>'
        f'<th>Where it lands</th></tr></thead><tbody>{body}</tbody></table></div></div>')


def _extra_h2s(slug, body_md):
    """The H2s that are not sections: the FAQ, and the close's own heading."""
    extra = re.findall(r"^##\s+(?:Frequently asked questions|Quick answer)\s*$",
                       body_md, re.M | re.I)
    p = config.artifact(slug, "wrapper.json")
    if os.path.exists(p):
        ch = (json.load(open(p)).get("close_heading") or "").strip()
        if ch and re.search(r"^##\s+" + re.escape(ch) + r"\s*$", body_md, re.M):
            extra.append(ch)
    return extra


def _nav(slug):
    return (f'<div class="bar"><div class="in"><a href="index.html">&larr; All articles</a>'
            f'<a href="{slug}.md" download>Download the markdown</a></div></div>')


def build_one(slug, out_dir):
    """Both pages for one article. Returns its card data for the index, or None if not finished."""
    p = config.artifact(slug, "draft.md")
    if not os.path.exists(p):
        print(f"  (skipping {slug} — no draft yet)")
        return None
    md = open(p).read()
    h1, body_md, srcs = _split(md)
    words = len(body_md.split())
    # "N sections" must mean what the architect planned, not every H2 on the page. The FAQ has
    # always had a heading, and from 2026-08-21 the close has one too, so a raw H2 count reports two
    # more sections than the article has and disagrees with what assemble prints.
    n_sec = len(re.findall(r"^##\s+", body_md, re.M)) - len(_extra_h2s(slug, body_md))

    body_html = _faq_details(review_page._md_to_html(body_md))
    meta = (f'<p class="meta">{words:,} words &middot; {n_sec} sections &middot; '
            f'{len(srcs)} sources</p>')

    art = (f"<h1>{html.escape(h1)}</h1>{meta}{_kw_block(slug)}"
           + _cite_links(body_html, srcs) + _srcs_block(srcs))
    open(os.path.join(out_dir, f"{slug}.html"), "w").write(_page(h1, art, _nav(slug)))
    open(os.path.join(out_dir, f"{slug}.md"), "w").write(md)      # the raw draft, for the download

    print(f"  {slug}: {words:,}w, {n_sec} sections, {len(srcs)} sources")
    return {"slug": slug, "h1": h1, "words": words, "secs": n_sec, "srcs": len(srcs)}


def build(slugs, out_dir=None, title="Testlify articles for review"):
    # sibling of out/, never inside it — out/ is per-run and gets deleted on a clean rerun
    out_dir = os.path.abspath(out_dir or os.path.join(config.WRITE_OUT, "..", "share"))
    os.makedirs(out_dir, exist_ok=True)
    cards = [c for c in (build_one(s, out_dir) for s in slugs) if c]

    body = [f'<h1>{html.escape(title)}</h1>',
            '<p class="lead">Each one is shown as it would look published. Every source marker in '
            'the text is a link, and the full source list sits at the bottom of each article.</p>',
            '<div class="cards">']
    for c in cards:
        body.append(
            f'<div class="card"><h3>{html.escape(c["h1"])}</h3>'
            f'<p class="n">{c["words"]:,} words &middot; {c["secs"]} sections &middot; '
            f'{c["srcs"]} sources</p>'
            f'<div class="go"><a class="p" href="{c["slug"]}.html">Read the article</a>'
            f'<a href="{c["slug"]}.md" download>Markdown</a></div></div>')
    body.append("</div>")
    open(os.path.join(out_dir, "index.html"), "w").write(_page(title, "".join(body)))
    print(f"  -> {out_dir}/index.html  ({len(cards)} article(s))")
    return out_dir


def run(slug, redo=False):
    """THE PER-ARTICLE PAGE. Every finished article gets its own clean, shareable copy at
    out/<slug>/share/index.html — no keyword highlights, no scoring panel, no tooltips.

    Called by run_writer as its last step, so a reader-ready link exists for every run without
    anyone remembering to build one. `redo` is accepted for the standard step signature; the page is
    cheap and rebuilt every time, so it is ignored.
    """
    return build([slug], out_dir=os.path.join(config.out_dir(slug), "share"),
                 title="Ready to read")


def build_all(out_dir=None):
    """The batch page — every slug under out/ that has a finished draft, newest first."""
    root = config.WRITE_OUT
    slugs = [s for s in sorted(os.listdir(root))
             if os.path.isdir(os.path.join(root, s))
             and os.path.exists(os.path.join(root, s, "writer", "draft.md"))]
    slugs.sort(key=lambda s: os.path.getmtime(os.path.join(root, s, "writer", "draft.md")), reverse=True)
    return build(slugs, out_dir=out_dir)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build the public share site for finished articles.")
    ap.add_argument("--slugs", nargs="*", help="omit to build every finished article")
    ap.add_argument("--out")
    a = ap.parse_args()
    build(a.slugs, a.out) if a.slugs else build_all(a.out)
