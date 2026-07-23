"""Step 9 — render the blueprint: structure-<slug>.json (machine source of truth) + a clean, interactive
structure-<slug>.html (TOC sidebar; hover an evidence point -> its source links; inline clickable [n]
citations -> a numbered References list; H2 keyword chip).
"""
import os, sys, json, html, datetime, re
import config
from urllib.parse import urlparse

WRITE_GUIDANCE = {
    "note": "This is a RESEARCH menu, not the final article. The writer selects sections and does the wording.",
    "seo_spec (from seo-aeo-geo-guidelines.md 3.2)": [
        "H1 = the asset title, primary keyword near the start, <=60 chars, benefit-focused.",
        "4-7 H2s in the final article (select from this menu); only 2-3 carry a keyword variation.",
        ">=50% of H2s phrased as questions; 40-60 word answer-first under question H2s.",
        "Primary keyword in: H1, first 100 words, 2-3 H2s, conclusion.",
        "Intro (answer-first), TL;DR block, FAQ (5), forward-looking close are written at the write phase.",
    ],
}


def build_json(slug, h1, sections, faq, orphans, keyword_set=None, angle_filter=None, persona=None):
    doc = {"slug": slug, "h1": h1, "generated": datetime.date.today().isoformat(),
           "keyword_set": keyword_set or {}, "sections": sections, "faq": faq,
           "orphan_keywords": orphans, "write_guidance": WRITE_GUIDANCE}
    if persona:
        doc["persona"] = persona                  # the ONE reader persona (picked in Step 1a); the bundle REUSES this
    if angle_filter:
        doc["angle_filter"] = angle_filter        # {kept, dropped, dropped_pct} — off-angle cards removed pre-cluster; see dropped-cards.json
    return doc


# ---------- html ----------
def _domain(u):
    try:
        return urlparse(u).netloc.replace("www.", "")
    except Exception:
        return u


def _label(u):
    p = [x for x in urlparse(u).path.split("/") if x]
    return (p[-1].replace("-", " ") if p else _domain(u))[:60]


def _refs(sections):
    """Global unique external URLs -> {url: n} in first-seen order."""
    order, seen = [], set()
    for s in sections:
        pools = [s.get("evidence", [])] + [h.get("evidence", []) for h in s.get("h3", [])]
        for ev in pools:
            for e in ev:
                for u in e.get("source_urls", []):
                    if u not in seen:
                        seen.add(u)
                        order.append(u)
    return {u: i + 1 for i, u in enumerate(order)}


def _kw_chip(tk):
    if not tk:
        return '<span class="kw none" title="no target keyword picked for this H2">no keyword</span>'
    t = f"KD {tk.get('kd')} · vol {tk.get('volume')}"
    return f'<span class="kw" title="{html.escape(t)}">{html.escape(str(tk.get("keyword")))} <em>{html.escape(t)}</em></span>'


def _evi_list(ev, refmap):
    out = ['<ul class="ev">']
    for e in ev:
        nums = [refmap[u] for u in e.get("source_urls", []) if u in refmap]
        cites = "".join(f'<a class="cn" href="#r{n}">{n}</a>' for n in nums)
        tip = "".join(
            f'<a href="{html.escape(u)}" target="_blank">{html.escape(_domain(u))}</a>'
            for u in e.get("source_urls", [])) or '<span class="own">our own page</span>'
        out.append(f'<li class="e">{html.escape(e["verbatim"])}'
                   f'<sup class="cites">{cites}</sup>'
                   f'<span class="tip">{tip}</span></li>')
    out.append("</ul>")
    return "\n".join(out)


def _links_row(internal):
    if not internal:
        return ""
    chips = "".join(f'<a class="pill" href="{html.escape(u)}" target="_blank">{html.escape(_label(u))}</a>'
                    for u in internal)
    return f'<div class="own-links"><span class="lbl">Pages we own:</span> {chips}</div>'


CSS = """
:root{--fg:#1c1e21;--mut:#6b7280;--line:#e6e8eb;--acc:#2563eb;--diff:#c0392b}
*{box-sizing:border-box}
body{font:15px/1.6 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;color:var(--fg);margin:0;background:#fafbfc}
.wrap{display:grid;grid-template-columns:230px minmax(0,1fr);gap:2.5rem;max-width:1080px;margin:0 auto;padding:2rem 1.4rem}
header{max-width:1080px;margin:0 auto;padding:1.6rem 1.4rem .2rem}
h1{font-size:1.5rem;line-height:1.3;margin:0 0 .3rem}
.note{color:var(--mut);font-size:.82rem;margin:0}
.orphan{background:#fff8e1;border:1px solid #ffe082;border-radius:8px;padding:.55rem .8rem;margin:.8rem 0 0;font-size:.82rem}
nav.toc{align-self:start;position:sticky;top:1.2rem;font-size:.8rem;border-right:1px solid var(--line);padding-right:1rem}
nav.toc a{display:block;color:var(--mut);text-decoration:none;padding:.18rem 0;border-radius:4px}
nav.toc a:hover{color:var(--acc)}
nav.toc a.diff::after{content:" \\25C6";color:var(--diff);font-size:.6rem}
main{min-width:0}
section{margin:0 0 1.8rem;scroll-margin-top:1rem}
h2{font-size:1.18rem;margin:.2rem 0 .5rem;padding-bottom:.25rem;border-bottom:2px solid var(--line)}
h2 .badge{font-size:.62rem;color:#fff;background:var(--diff);border-radius:3px;padding:1px 5px;vertical-align:middle;margin-left:.4rem}
h3{font-size:1rem;margin:1rem 0 .2rem;color:#333}
.kw{display:inline-block;font-size:.72rem;background:#eef2ff;color:#3730a3;border-radius:5px;padding:1px 7px;margin-left:.5rem;vertical-align:middle;font-weight:500}
.kw em{opacity:.7;font-style:normal}
.kw.none{background:#f3f4f6;color:#9ca3af}
ul.ev{list-style:none;margin:.2rem 0 .5rem;padding:0}
li.e{position:relative;padding:.28rem 0;border-bottom:1px solid #f1f3f5}
li.e:hover{background:#f6f9ff}
sup.cites{margin-left:3px;white-space:nowrap}
a.cn{color:var(--acc);text-decoration:none;font-size:.7rem;background:#eef2ff;border-radius:3px;padding:0 4px;margin:0 1px}
a.cn:hover{background:var(--acc);color:#fff}
.tip{visibility:hidden;opacity:0;position:absolute;left:0;top:1.7em;z-index:30;background:#1b1b1b;color:#eee;padding:7px 10px;border-radius:8px;font-size:.74rem;line-height:1.7;box-shadow:0 6px 20px rgba(0,0,0,.28);max-width:560px;transition:opacity .12s}
li.e:hover .tip{visibility:visible;opacity:1}
.tip a{color:#8ab4ff;text-decoration:none;display:block;max-width:540px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tip a:hover{text-decoration:underline}
.tip .own{color:#aaa}
.own-links{font-size:.78rem;margin:.3rem 0 .2rem}
.own-links .lbl{color:var(--mut)}
.pill{display:inline-block;background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;border-radius:12px;padding:1px 9px;margin:2px 3px 2px 0;text-decoration:none;font-size:.74rem}
.pill:hover{background:#dcfce7}
ol.refs{font-size:.78rem;color:var(--mut);padding-left:1.4rem}
ol.refs li{margin:.15rem 0;scroll-margin-top:1rem;word-break:break-all}
ol.refs a{color:var(--acc);text-decoration:none}
.faq li{margin:.25rem 0}
"""


def build_html(doc):
    refmap = _refs(doc["sections"])
    S = [f'<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         f'<title>Structure — {html.escape(doc["h1"][:50])}</title><style>{CSS}</style>']
    S.append("<header>")
    S.append(f"<h1>{html.escape(doc['h1'])}</h1>")
    S.append(f"<p class='note'>Research blueprint (a menu — the writer selects sections & does the wording). "
             f"{len(doc['sections'])} candidate sections · generated {doc['generated']}. Hover a line for its sources.</p>")
    per = doc.get("persona")
    if per and (per.get("name") or per.get("lens")):
        S.append(f"<p class='note'>Reader persona (steers research + write depth; never named in the article): "
                 f"<b>{html.escape(per.get('name') or 'generic')}</b>"
                 + (f" — {html.escape(per.get('lens'))}" if per.get('lens') else "") + "</p>")
    af = doc.get("angle_filter")
    if af:
        S.append(f"<p class='note'>Angle-relevance filter: {af.get('kept')} cards kept, "
                 f"{af.get('dropped')} off-angle cards dropped ({af.get('dropped_pct')}%) before clustering — "
                 f"see <code>dropped-cards.json</code>.</p>")
    ks = doc.get("keyword_set") or {}
    if ks.get("primary"):
        def _kw(lst): return " · ".join(html.escape(str(k.get("keyword", k)) if isinstance(k, dict) else str(k)) for k in (lst or []))
        S.append("<div class='orphan'><b>Keyword set</b> (for the write-phase coverage check) — "
                 f"<b>primary:</b> {html.escape(ks['primary'])}"
                 + (f" · <b>variations:</b> {_kw(ks.get('variations'))}" if ks.get('variations') else "")
                 + (f" · <b>secondaries (brief):</b> {_kw(ks.get('secondaries'))}" if ks.get('secondaries') else "")
                 + (f" · <b>per-H2 keywords:</b> {_kw(ks.get('h2_keywords'))}" if ks.get('h2_keywords') else "")
                 + (f" · <b>in-body:</b> {_kw(ks.get('in_body'))}" if ks.get('in_body') else "") + "</div>")
    if doc["orphan_keywords"]:
        oks = " · ".join(f"{html.escape(o.get('keyword',''))} ({o.get('volume')})" for o in doc["orphan_keywords"])
        S.append(f"<div class='orphan'><b>Orphan keywords</b> (high-demand, not yet covered): {oks}</div>")
    S.append("</header>")

    # TOC + main
    S.append('<div class="wrap"><nav class="toc">')
    for i, s in enumerate(doc["sections"]):
        cls = " class='diff'" if s.get("is_differentiator") else ""
        S.append(f"<a href='#s{i}'{cls}>{html.escape(s['h2'])}</a>")
    S.append("<a href='#faq'>FAQ candidates</a><a href='#refs'>References</a></nav><main>")

    for i, s in enumerate(doc["sections"]):
        badge = "<span class='badge'>differentiator</span>" if s.get("is_differentiator") else ""
        S.append(f"<section id='s{i}'><h2>{html.escape(s['h2'])}{badge}{_kw_chip(s.get('target_keyword'))}</h2>")
        if s.get("evidence"):
            S.append(_evi_list(s["evidence"], refmap))
        for h in s.get("h3", []):
            S.append(f"<h3>{html.escape(h['h3'])}</h3>")
            if h.get("evidence"):
                S.append(_evi_list(h["evidence"], refmap))
        S.append(_links_row(s.get("internal_links", [])))
        S.append("</section>")

    if doc["faq"]:
        S.append("<section id='faq'><h2>FAQ candidates</h2><ul class='faq'>")
        S += [f"<li>{html.escape(q)}</li>" for q in doc["faq"]]
        S.append("</ul></section>")

    # references
    S.append("<section id='refs'><h2>References</h2><ol class='refs'>")
    for u, n in sorted(refmap.items(), key=lambda kv: kv[1]):
        S.append(f"<li id='r{n}'><a href='{html.escape(u)}' target='_blank'>{html.escape(u)}</a></li>")
    S.append("</ol></section></main></div>")
    return "\n".join(S)


def run(slug, h1, sections, faq, orphans, keyword_set, run_dir):
    af = None
    dp = os.path.join(run_dir, "dropped-cards.json")
    if os.path.exists(dp):
        r = json.load(open(dp))
        af = {"kept": r.get("kept_count"), "dropped": r.get("dropped_count"), "dropped_pct": r.get("dropped_pct_of_cards")}
    persona = None
    pp = os.path.join(run_dir, "persona.json")
    if os.path.exists(pp):
        persona = json.load(open(pp))
    doc = build_json(slug, h1, sections, faq, orphans, keyword_set, angle_filter=af, persona=persona)
    jp = os.path.join(run_dir, f"structure-{slug}.json")
    hp = os.path.join(run_dir, f"structure-{slug}.html")
    config.write_json(jp, doc)
    config.write_text(hp, build_html(doc))
    print(f"  -> {jp}\n  -> {hp}")
    return jp, hp


if __name__ == "__main__":
    d = json.load(open(sys.argv[1]))
    run(d["slug"], d["h1"], d["sections"], d["faq"], d["orphan_keywords"], d.get("keyword_set", {}), os.path.dirname(sys.argv[1]))
