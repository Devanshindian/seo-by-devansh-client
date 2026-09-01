#!/usr/bin/env python3
"""ONE front page across every article in a run: projects/<co>/04-write-phase/index.html

  COMPANY=<slug> python3 build_run_index.py

eval_pages.build_index writes a front door PER ARTICLE. There was no page above those, so reviewing a
run meant knowing four file paths. This is that missing page: one row per article, the headline
numbers, and a link into each article's own front door.

Read-only. It opens finished output and writes one file; it never runs a step and never edits a draft.
"""
import argparse
import json
import os

import config

E = __import__("html").escape
SLUGS = ["the-real-cost-recruitment-2026", "running-hiring-hackathon-that-screens",
         "strategic-interview-questions-paired-strong", "the-type-d-personality-label"]


def _load(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


def _row(slug):
    """Everything this article can tell us, tolerating a run that stopped early."""
    d = config.out_dir(slug)
    st = _load(os.path.join(d, "architect", "structure.json"))
    body = _load(os.path.join(d, "writer", "_work", "body.json"))
    bl = _load(os.path.join(d, "writer", "_work", "blend.json"))
    wr = _load(os.path.join(d, "writer", "_work", "wrapper.json"))
    co = _load(os.path.join(d, "writer", "_work", "coherence-report.json"))
    r = {"slug": slug, "title": slug.replace("-", " "), "has_index": os.path.exists(os.path.join(d, "index.html"))}

    if st:
        wb = st.get("word_budget") or {}
        r["title"] = st.get("h1") or r["title"]
        r["sections"] = len(st.get("sections") or [])
        r["band"] = (wb.get("band") or {})
        r["aim"] = wb.get("base")
        r["aim_low_pct"] = wb.get("aim_low_pct")
        r["under_floor"] = len((wb.get("headings") or {}).get("under_floor") or [])
    if body:
        secs = body.get("sections") or []
        tgt = sum(s.get("word_target") or 0 for s in secs)
        got = sum(s.get("words") or len(str(s.get("prose") or "").split()) for s in secs)
        r["written"] = got
        r["target"] = tgt
        r["drift"] = round((got - tgt) * 100 / tgt) if tgt else None
        off = [s for s in secs
               if (s.get("word_target") or 0) and
               abs((s.get("words") or len(str(s.get("prose") or "").split())) - s["word_target"]) * 100
               / s["word_target"] > 20]
        r["sections_off"] = len(off)
    if bl:
        cb, ca = bl.get("counter_before") or {}, bl.get("counter_after") or {}
        r["long_before"], r["long_after"] = cb.get("long_sentences"), ca.get("long_sentences")
        r["passages"] = sum(len(x.get("edits") or []) for x in bl.get("diff") or [])
        r["blend_flags"] = len(bl.get("warnings") or []) + len(bl.get("guard_failures") or [])
        la = bl.get("length_after") or {}
        r["over_by"] = la.get("over_by")
    if wr:
        faq = wr.get("faq") or []
        r["faq"] = len(faq)
        r["faq_over"] = sum(1 for f in faq if f.get("over_target"))
        r["intro_words"] = len((wr.get("intro") or "").split())
    if co:
        r["coh_applied"] = co.get("applied")
        r["coh_fixes"] = len(co.get("changes_claimed") or [])
        r["coh_flags"] = len(co.get("warnings") or []) + len(co.get("guard_failures") or [])
    return r


CSS = """<style>
*{box-sizing:border-box}
body{margin:0;background:#fff;color:#1c1a17;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:0 24px}
header{background:linear-gradient(180deg,#fff8ec,#fff);border-bottom:1px solid #efe7d8;padding:46px 0 26px}
h1{font-size:34px;line-height:1.1;margin:0 0 10px;letter-spacing:-.02em}
.lede{color:#6b6459;max-width:720px;margin:0}
h2{font-size:20px;margin:38px 0 12px}
.card{border:1px solid #efe7d8;border-radius:14px;padding:18px 20px;margin:0 0 14px;
 box-shadow:0 1px 2px rgba(28,26,23,.04),0 8px 24px rgba(28,26,23,.05)}
.card h3{margin:0 0 4px;font-size:18px}
.card h3 a{color:#1c1a17;text-decoration:none;border-bottom:2px solid #ffe9ad}
.card h3 a:hover{border-bottom-color:#fb7a00}
.slug{font:12px ui-monospace,Menlo,Consolas,monospace;color:#6b6459;margin:0 0 12px}
.nums{display:flex;flex-wrap:wrap;gap:8px}
.n{border:1px solid #efe7d8;border-radius:10px;padding:7px 12px;background:#fffdf8;min-width:104px}
.n b{display:block;font-size:17px}
.n span{font-size:11.5px;color:#6b6459;letter-spacing:.02em}
.n.good b{color:#1a7f4b} .n.bad b{color:#c0392b}
.note{background:#fffdf8;border:1px solid #efe7d8;border-left:4px solid #ffb703;border-radius:12px;
 padding:14px 17px;margin:0 0 22px;font-size:15px}
.miss{color:#6b6459;font-size:14px}
footer{padding:26px 0 60px;color:#6b6459;font-size:13.5px;border-top:1px solid #efe7d8;margin-top:34px}
</style>"""


def _n(val, label, good=None):
    if val is None:
        return ""
    cls = "" if good is None else (" good" if good else " bad")
    return f'<div class="n{cls}"><b>{E(str(val))}</b><span>{E(label)}</span></div>'


def build():
    rows = [_row(s) for s in SLUGS if os.path.isdir(config.out_dir(s))]
    cards = []
    for r in rows:
        nums = "".join([
            _n(r.get("sections"), "sections"),
            _n(f'{r["written"]:,}' if r.get("written") else None, "words written"),
            _n(f'{r["drift"]:+d}%' if r.get("drift") is not None else None, "off target",
               good=(abs(r["drift"]) <= 10) if r.get("drift") is not None else None),
            _n(r.get("sections_off"), "sections >20% off",
               good=(r.get("sections_off") == 0) if r.get("sections_off") is not None else None),
            _n(f'{r["long_before"]} to {r["long_after"]}'
               if r.get("long_before") is not None else None, "long sentences",
               good=(r.get("long_after", 1) < r.get("long_before", 0)) if r.get("long_before") is not None else None),
            _n(r.get("passages"), "passages blend changed",
               good=(r.get("passages", 0) > 0) if r.get("passages") is not None else None),
            _n(r.get("faq"), "FAQ questions"),
            _n(r.get("faq_over"), "answers over 40w",
               good=(r.get("faq_over") == 0) if r.get("faq_over") is not None else None),
            _n(r.get("coh_fixes"), "contradictions fixed"),
            _n(r.get("under_floor"), "sections under the sub-heading floor"),
        ])
        link = (f'<a href="{E(r["slug"])}/index.html">{E(r["title"])}</a>'
                if r["has_index"] else E(r["title"]))
        missing = "" if r.get("coh_applied") is not None else \
            '<p class="miss">This article has not reached coherence yet.</p>'
        cards.append(f'<div class="card"><h3>{link}</h3><p class="slug">{E(r["slug"])}</p>'
                     f'<div class="nums">{nums}</div>{missing}</div>')

    body = f"""<header><div class="wrap">
<h1>The write phase, four articles</h1>
<p class="lede">One row per article. Click a title to open that article's own front door, which links
every step in order. These runs stop after coherence, so there is no finished draft yet.</p>
</div></header>
<div class="wrap">
<div class="note"><b>What the numbers mean.</b> <b>Off target</b> is how far the sections came in
against the length the architect planned; green is within 10%. <b>Long sentences</b> is how many ran
over 25 words before and after the editor. <b>Passages blend changed</b> being zero is a failure, not
a clean bill. <b>Answers over 40w</b> counts FAQ answers longer than a search engine will show.</div>
{''.join(cards) or '<p>No articles found.</p>'}
</div>
<footer><div class="wrap">Built from the saved run files. Read-only.</div></footer>"""

    out = os.path.join(os.path.dirname(config.WRITE_OUT), "index.html")
    config.write_text(out, f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
                           f'<meta name="viewport" content="width=device-width,initial-scale=1">'
                           f'<title>The write phase — {config.BRAND}</title>{CSS}</head><body>{body}</body></html>')
    print(f"  -> {out}  ({len(rows)} article(s))")
    return out


if __name__ == "__main__":
    argparse.ArgumentParser(description="One index across every article in the run.").parse_args()
    build()
