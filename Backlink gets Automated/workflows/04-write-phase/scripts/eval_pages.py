#!/usr/bin/env python3
"""The eval pages — one self-contained HTML file per engine, per article, for judging a run by eye.

Pure read-and-render: these pages are built ONLY from files the pipeline already writes. Nothing
here decides anything, so a page can be rebuilt at any time for any past run.

  gather/gather-review.html      "What we started with"  — settings · kept-vs-dropped vetting · card depth
  planner/selection-review.html  "Selection"             — drops first · weak keeps · close calls · orphans
  planner/sources-review.html    "Sources"               — one row per checked card, filterable by verdict
  architect/blueprint-review.html "The blueprint"        — spine · bench · sections with jobs+words · research

The writer's page (writer/article.html) is built by assemble.py/review_page.py, not here.
"""
import argparse
import html
import json
import os
import re

import article_ctx
import config

E = html.escape


# ---------------------------------------------------------------- shared skin
MAP_CSS = """.map{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:0 0 30px;align-items:start}
.mcol{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:9px 9px 11px;
      box-shadow:var(--shadow);min-width:0}
.mh{font-size:10.5px;letter-spacing:.11em;text-transform:uppercase;color:var(--acc);font-weight:700;
    padding:2px 5px 7px}
.mnote{font-size:11.5px;color:var(--warn);background:var(--wash);border:1px dashed var(--acc-soft);
       border-radius:7px;padding:5px 8px;margin:0 3px 6px;line-height:1.45}
.lead{color:var(--mut);font-size:.93em;margin:0 0 22px;line-height:1.6}
.mstep{display:block;text-decoration:none;color:var(--ink);border-radius:8px;padding:5px 8px;
       border:1px solid transparent}
.mstep b{display:block;font-size:13.5px;font-weight:700;line-height:1.35}
.mstep span{display:block;font-size:12.5px;color:var(--mut);line-height:1.45}
.mstep i{display:block;font-style:normal;font-size:11px;color:var(--mut);opacity:.7;margin-top:1px}
a.mstep:hover{background:var(--wash);border-color:var(--acc-soft)}
a.mstep:hover b{color:var(--acc)}
.mstep.on{background:var(--acc);border-color:var(--acc)}
.mstep.on b,.mstep.on span{color:#fff}
.mstep.on span{opacity:.9}
.mstep.none{opacity:.5}
@media(max-width:820px){.map{grid-template-columns:1fr}}"""

CSS = """
:root{--ink:#1c1a17;--mut:#6b6459;--line:#efe7d8;--bg:#fffdf8;--card:#fff;--wash:#fff8ec;
      --acc:#fb7a00;--acc-soft:#ffd9b0;--yellow:#ffb703;--yellow-soft:#ffe9ad;
      --ok:#2e7d43;--ok-bg:#e8f5ec;--no:#c2603a;--no-bg:#fdf3f0;--warn:#9a6700;--chip:#fff8ec;
      --shadow:0 1px 2px rgba(28,26,23,.04),0 8px 24px rgba(28,26,23,.05)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:920px;margin:0 auto;padding:40px 24px 120px}
h1{font-size:clamp(26px,4vw,34px);margin:0 0 4px;letter-spacing:-.02em}
h1 .hl,h1{background:linear-gradient(180deg,transparent 68%,var(--yellow-soft) 68%);display:inline}
.sub{color:var(--mut);margin:10px 0 28px;display:block}
h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--acc);
   margin:36px 0 10px;border-bottom:1px solid var(--line);padding-bottom:7px;font-weight:700}
/* A failed check has to be findable at a glance in a table of green ticks. */
tr.bad td{background:var(--pinkwash)}
tr.bad td:first-child{color:var(--pink);font-weight:700}
.panel.bad{border-color:var(--pinkline);background:var(--pinkwash)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;
       margin:0 0 14px;box-shadow:var(--shadow)}
.nums{display:flex;gap:28px;flex-wrap:wrap;background:linear-gradient(180deg,var(--wash),var(--card));
      border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin:0 0 10px;box-shadow:var(--shadow)}
.nums b{font-size:1.55em;display:block;color:var(--ink)}
ins{background:var(--ok-bg);color:var(--ok);text-decoration:none;border-radius:2px;padding:0 2px}
del{background:var(--no-bg);color:var(--no);border-radius:2px;padding:0 2px}
details.diff{border:1px solid var(--line);border-radius:10px;padding:9px 13px;margin:8px 0;background:var(--card)}
details.diff summary{font-weight:600;cursor:pointer;line-height:1.9}
details.diff[open] summary{margin-bottom:6px;border-bottom:1px solid var(--line);padding-bottom:6px}
.dbody{margin-top:6px;font-size:.94em;line-height:1.75}
.subh{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--acc);
      font-weight:700;margin:14px 0 4px}
code{background:var(--wash);border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:.86em}
.kwlist{margin:.3em 0;padding-left:1.3em}
.kwlist li{margin:.35em 0}
""" + MAP_CSS + """
.nums span{color:var(--mut);font-size:.8em}
.row{padding:10px 2px;border-top:1px dashed var(--line)}
.row:first-of-type{border-top:0}
.row .t{font-weight:650}
.row .m{color:var(--mut);font-size:.88em}
.reason{margin-top:2px;font-size:.92em}
.chip{display:inline-block;background:var(--chip);border:1px solid var(--line);border-radius:100px;
      padding:1px 9px;font-size:.76em;color:var(--mut);margin-left:6px;vertical-align:middle}
.tag{display:inline-block;background:var(--yellow-soft);border-radius:100px;padding:1px 9px;font-size:.8em;
     margin:2px 4px 2px 0;cursor:help;color:var(--ink)}
.ok{color:var(--ok)}.no{color:var(--no)}.warn{color:var(--warn)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:700px){.grid2{grid-template-columns:1fr}}
.bar{height:9px;background:var(--wash);border:1px solid var(--line);border-radius:5px;overflow:hidden;margin-top:3px}
.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--yellow),var(--acc))}
ul{margin:.3em 0;padding-left:1.3em}
li{margin:.18em 0}
a{color:var(--acc);overflow-wrap:anywhere}
details{margin:6px 0}
summary{cursor:pointer}
.spine{font-size:1.12em;line-height:1.65;background:var(--wash);border:1px solid var(--acc-soft);
       border-left:4px solid var(--acc);border-radius:12px;padding:18px 20px;margin:0 0 20px}
.job{font-style:italic;color:var(--mut);margin:2px 0 6px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}
.filters button{background:var(--card);border:1px solid var(--line);color:var(--ink);border-radius:100px;
                padding:5px 13px;cursor:pointer;font-size:.85em;font-weight:600}
.filters button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
.q{color:var(--mut);font-size:.85em}
.where{background:var(--wash);border:1px solid var(--acc-soft);border-radius:12px;padding:14px 18px;margin:0 0 22px}
.where ol{margin:6px 0 0;padding-left:20px}
.where li{margin:.2em 0;color:var(--mut)}
.where li.now{color:var(--ink);font-weight:650}
.where .lead{font-size:.9em;color:var(--mut)}
.note{color:var(--mut);font-size:.88em;margin:-4px 0 10px}
.from{color:var(--mut);font-size:.88em}
.from b{color:var(--ink);font-weight:650}
.nav{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 24px}
.nav a{background:var(--card);border:1px solid var(--line);border-radius:100px;padding:5px 13px;
       font-size:.85em;font-weight:600;text-decoration:none;color:var(--ink)}
.nav a.on{background:var(--acc);color:#fff;border-color:var(--acc)}
.lede{font-size:1.06em;line-height:1.66;margin:0 0 22px;color:var(--ink)}
.oneline{background:var(--wash);border:1px solid var(--acc-soft);border-left:4px solid var(--acc);
         border-radius:12px;padding:16px 20px;margin:0 0 26px;line-height:1.7}
.oneline b{white-space:nowrap}
.stn{display:flex;align-items:baseline;gap:10px;margin:26px 0 8px}
.stn .name{font-size:1.06em;font-weight:700}
.stn .does{color:var(--mut);font-size:.9em}
.step{display:grid;grid-template-columns:30px 1fr;gap:2px 10px;padding:9px 2px;
      border-top:1px dashed var(--line)}
.step:first-child{border-top:0}
.step .no{color:var(--acc);font-weight:700;font-variant-numeric:tabular-nums;font-size:.92em}
.step .nm{font-weight:650}
.step .dsc{grid-column:2;color:var(--mut);font-size:.9em}
.step .see{grid-column:2;font-size:.84em;margin-top:2px}
.b{display:inline-block;border-radius:100px;padding:0 8px;font-size:.7em;font-weight:700;
   letter-spacing:.03em;vertical-align:middle;margin-left:6px;border:1px solid var(--line);
   background:var(--chip);color:var(--mut);text-transform:uppercase}
.b.ai{background:var(--yellow-soft);border-color:#f2d98d;color:#6a4a00}
.b.paid{background:var(--no-bg);border-color:#f0d3c8;color:var(--no)}
.b.code{background:var(--ok-bg);border-color:#cfe6d6;color:var(--ok)}
.pg{padding:14px 2px;border-top:1px dashed var(--line)}
.pg:first-child{border-top:0}
.pg .t{font-weight:700;font-size:1.02em}
.pg .ask{color:var(--mut);font-size:.9em;margin-top:1px}
.pg .cov{font-size:.84em;margin-top:5px;color:var(--mut)}
.pg .look{font-size:.88em;margin-top:4px}
.key{display:flex;gap:16px;flex-wrap:wrap;font-size:.84em;color:var(--mut);margin:0 0 14px}
"""

# The whole write phase, in order. Every page prints this and bolds where you are, so a page is never
# read out of context. (label, one-line plain-English description)


def _where(_now, lead=""):
    """The page's opening paragraph: what this step is, in four to six plain sentences.

    It used to also print the five-stage list with "← you are here", which the map at the top of the
    page now shows properly. The stage argument is kept only so every caller need not change.
    """
    return f'<p class="lead">{E(lead)}</p>' if lead else ""


STEP_ANCHOR = {"shape": "sections", "allocate": "sections", "enrich": "research",
               "section-keywords": "keywords", "headings": "headings"}


def _nav(now, base="../"):
    """THE MAP — the same three stations and every step, at the top of every single page.

    This is the one navigation the whole review has. It is not a menu: it is the pipeline itself, one
    short line per step, so a reader who lands on any page still sees where that step sits and what
    ran before and after it. Built from STATIONS, the map the orchestrators are asserted against, so
    it can never describe a pipeline that no longer runs.

    A step with a page is a link and opens in a NEW TAB, so the map is never lost. A step with no page
    of its own says so plainly rather than being hidden or pointed at some other step's page.

    `base` is how far up the run root sits from the page being written: "../" for a page inside an
    engine folder, "" for one at the run root (time-and-usage.html, index.html).
    """
    href_of = {p[0]: p[1] for p in PAGES}
    href_of.update({p[0]: p[1] for p in EXTRA_PAGES})
    cols = []
    for i, (station, _engine, _does, steps) in enumerate(STATIONS, 1):
        rows = []
        for sname, one, _dsc, _run, page in steps:
            if page and page in href_of:
                cls = "mstep on" if page == now else "mstep"
                anc = STEP_ANCHOR.get(sname)
                rows.append(f'<a class="{cls}" href="{base}{href_of[page]}'
                            f'{"#" + anc if anc else ""}" target="_blank">'
                            f'<b>{E(sname)}</b><span>{E(one)}</span></a>')
            else:
                rows.append(f'<span class="mstep none"><b>{E(sname)}</b><span>{E(one)}</span>'
                            '<i>no page — nothing here to overrule</i></span>')
        pages = [st[4] for st in steps if st[4]]
        shared = {pg for pg in pages if pages.count(pg) > 1}
        note = (f'<div class="mnote">All {len(pages)} open the one <b>{E(sorted(shared)[0])}</b> page, '
                'each at its own section.</div>') if len(shared) == 1 and len(set(pages)) == 1 else ""
        cols.append(f'<div class="mcol"><div class="mh">{i} · {E(station)}</div>{note}{"".join(rows)}</div>')
    return '<div class="map">' + "".join(cols) + "</div>"


JS_THEME = ""


def _page(title, sub, body, extra_js=""):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(title)}</title><style>{CSS}</style></head><body>'
            f'<div class="wrap">'
            f'<h1>{E(title)}</h1><p class="sub">{E(sub)}</p>{body}</div>'
            f'<script>{JS_THEME}{extra_js}</script></body></html>')


def reads_link(stage, label=None):
    """The 'read it as it stands' banner every writer step page carries (2026-08-13).

    Each step page shows what CHANGED: diffs, counts, flags. None of them showed the article itself,
    so you could see that blend cut a repetition and still have no idea how the piece read afterwards.
    build_stage_reads.py writes one clean page per step; this is the link to it.

    Every writer page lives in writer/, so the relative path is the same from all of them.
    """
    what = label or f"after {stage}"
    return (f'<div class="panel"><p><b>Want to just read it?</b> '
            f'<a href="reads/{E(stage)}.html">Open the article as it stands {E(what)}</a> — '
            f'no highlights, no panels, the way a reader would see it. '
            f'<a href="reads/index.html">Every step</a>.</p></div>')


def _nums(pairs):
    return ('<div class="nums">' +
            "".join(f'<div><b>{E(str(v))}</b><span>{E(k)}</span></div>' for k, v in pairs) + '</div>')


def _card_glosses(slug):
    """card_id -> gloss (+ url), for hover receipts and source rows."""
    idx = {}
    inp = json.load(open(config.artifact(slug, "plan-inputs.json")))
    for s in inp["group_b"]["sections_menu"]:
        for c in list(s.get("evidence", [])) + [e for h in s.get("h3", []) for e in h.get("evidence", [])]:
            try:
                cid = int(str(c.get("card_id")).lower().replace("id", "").strip())
            except ValueError:
                continue
            idx[cid] = {"gloss": (c.get("gloss") or "").strip(),
                        "url": (c.get("source_urls") or [None])[0]}
    return idx


def _work(slug, engine, name):
    p = os.path.join(getattr(config, f"{engine}_work_dir")(slug), name)
    return json.load(open(p)) if os.path.exists(p) else None


def _world_panel(slug, why):
    """The world (about / not_about) — the boundary several steps on this page judged against.

    A reviewer cannot check a keep/drop/bench decision without seeing the rule it was made against, so
    every page that shows one of those decisions shows this too. Reads the research phase's spine.json
    through the same shared reader the pipeline uses, so the page can never show a different world than
    the one the run actually applied.
    """
    ctx = article_ctx.article_context(slug)
    if not (ctx.get("about") or ctx.get("not_about")):
        return ('<h2>The world — what this article is and is not about</h2>'
                '<div class="panel"><p class="q">No world statement on file for this run. Decisions below '
                'were made without a boundary, so judge them on the angle alone.</p></div>')
    return ('<h2>The world — what this article is and is not about</h2>'
            f'<p class="note">{E(why)}</p><div class="panel">'
            f'<div class="row"><span class="t">IS about</span><div>{E(ctx["about"] or "—")}</div></div>'
            f'<div class="row"><span class="t">is NOT about</span><div>{E(ctx["not_about"] or "—")}</div></div>'
            "</div>")


# ---------------------------------------------------------------- 1. GATHER
def build_gather(slug):
    inp = json.load(open(config.artifact(slug, "plan-inputs.json")))
    ga, gb = inp["group_a"], inp["group_b"]
    vet = _work(slug, "gather", "vet.json") or {}
    win = _work(slug, "gather", "winners-extract.json") or {}

    ks = ga.get("keyword_set") or {}
    persona = ga.get("persona")
    persona = persona.get("name") if isinstance(persona, dict) and persona.get("name") else str(persona or "—")
    wb = ga.get("word_band") or {}
    settings = "".join(
        f'<div class="row"><span class="t">{E(k)}</span><div>{E(str(v))}</div></div>' for k, v in [
            ("H1", ga.get("h1") or "—"),
            ("Format", ga.get("format_archetype") or "—"),
            ("Primary keyword", ga.get("primary_keyword") or "—"),
            ("Variations", ", ".join(ks.get("variations") or []) or "—"),
            # The pool the architect's headings step draws from. This row used to read h2_keywords —
            # one keyword stapled to each PLANNED heading — which the keyword set stopped carrying when
            # per-section keywords moved to the architect. It could only ever render as "—".
            ("Secondary pool (for section headings)", ", ".join(ks.get("secondaries") or []) or "—"),
            ("Persona", persona),
            ("Word band", f"{wb.get('min', '?')}–{wb.get('max', '?')} words"),
        ])

    def vet_cols(raw, kept, label):
        seen, raw_d = set(), []
        for x in raw or []:
            if x not in seen:
                seen.add(x)
                raw_d.append(x)
        kept_set = set(kept or [])
        dropped = [x for x in raw_d if x not in kept_set]
        left = "".join(f"<li>{E(x)}</li>" for x in kept or []) or "<li class='q'>none</li>"
        right = "".join(f"<li>{E(x)}</li>" for x in dropped) or "<li class='q'>none dropped</li>"
        return (f'<h2>{E(label)} — kept {len(kept or [])} of {len(raw_d)}</h2><div class="grid2">'
                f'<div class="panel"><b class="ok">Kept</b><ul>{left}</ul></div>'
                f'<div class="panel"><b class="no">Dropped</b><ul>{right}</ul>'
                f'<p class="q">The vet call returns only the keeps, so no per-drop reason is on record. '
                f'A drop means one of two things: off-topic for this article, or belonging to the world in '
                f'the NOT ABOUT line above.</p></div></div>')

    rows, mx = [], 1
    for s in gb["sections_menu"]:
        n = len(s.get("evidence", [])) + sum(len(h.get("evidence", [])) for h in s.get("h3", []))
        rows.append((n, s.get("h2") or s.get("title") or "?"))
        mx = max(mx, n)
    depth = "".join(
        f'<div class="row"><div class="t">{E(t)} <span class="chip">{n} cards</span></div>'
        f'<div class="bar"><i style="width:{max(2, round(100 * n / mx))}%"></i></div></div>'
        for n, t in rows)

    winners = "".join(
        f'<details><summary>{E(lbl)} ({len(win.get(k) or [])})</summary><ul>'
        + "".join(f"<li>{E(str(x))}</li>" for x in win.get(k) or []) + "</ul></details>"
        for k, lbl in [("gaps_to_own", "Gaps we chose to own"),
                       ("winners_common_h2s", "What every winning article covers"),
                       ("winners_drift", "Where winners drift off-topic")])

    body = (_nav("Gather")
            + _where("Gather", "Nothing has been decided yet. This is the raw material the article will be "
                               "built from, and the settings it will be built to.")
            + '<h2>The settings this run used</h2><div class="panel">' + settings + "</div>"
            + _world_panel(slug, "Google returns questions and searches for the WORDS in a query, not for the "
                                 "audience behind them, so some of what comes back belongs to a different field "
                                 "that happens to share our vocabulary. The two lines below are the boundary the "
                                 "vetting used. Read them before judging the keeps and drops.")
            + vet_cols(vet.get("paa_raw"), vet.get("paa_kept"), "People-Also-Ask questions")
            + vet_cols(vet.get("related_raw"), vet.get("related_kept"), "Related searches")
            + '<h2>Research depth per section (cards available)</h2><div class="panel">' + depth + "</div>"
            + '<h2>The winners study</h2><div class="panel">' + winners + "</div>")
    out = config.artifact(slug, "gather-review.html")
    config.write_text(out, _page("What we started with", f"{slug} — gather review", body))
    return out


# ---------------------------------------------------------------- 2. SELECTION
def build_selection(slug):
    stats = _work(slug, "planner", "selection-stats.json") or {}
    drops = _work(slug, "planner", "drops.json") or {}
    placements = _work(slug, "planner", "placements.json") or []
    tagged = _work(slug, "planner", "article-plan.tagged.json") or {"sections": []}
    glosses = _card_glosses(slug)

    nums = _nums([("sections in", stats.get("candidates", "?")),
                  ("sections kept", stats.get("survivors", "?")),
                  ("sections dead", stats.get("dead", "?")),
                  ("subsections dropped", stats.get("h3s_dropped", "?")),
                  ("orphans re-homed", stats.get("orphans_placed", "?")),
                  ("survival rule", f"≥{round((stats.get('threshold') or 0.45) * 100)}% tagged")])

    dead_h2s = drops.get("dead_h2s") or []
    # A wrong-world refusal is the drop most worth reading, so it gets its own chip. The tagger writes an
    # exact `WRONG WORLD:` prefix for it (tag-h3s.md); this page only looks for that token.
    # Deliberately NOT guessed from the prose: matching phrases like "not about" caught ordinary English
    # ("this H3 is about X, not about Y") and mislabelled plain off-angle drops as world refusals.
    # Runs from before that token existed simply show none, which is the honest answer for them.
    def _is_world(reason):
        return (reason or "").lstrip().upper().startswith("WRONG WORLD:")

    dropped = drops.get("dropped_h3s") or []
    n_world = sum(1 for d in dropped if _is_world(d.get("ai_reason") or d.get("why")))
    dr = "".join(
        f'<div class="row"><div class="t">{E(d.get("h3") or "?")}'
        + ('<span class="chip no">wrong world</span>'
           if _is_world(d.get("ai_reason") or d.get("why")) else "")
        + "</div>"
        f'<div class="from">was under: <b>{E(d.get("from_h2") or "?")}</b>'
        + ('  <span class="chip no">this H2 was cut too</span>' if d.get("from_h2") in dead_h2s else "")
        + f'</div><div class="reason">{E(d.get("ai_reason") or d.get("why") or "(no reason recorded)")}</div></div>'
        for d in dropped) or '<p class="q">nothing dropped</p>'
    if n_world:
        dr = (f'<p class="note"><b>{n_world}</b> of these {len(dropped)} were refused for belonging to a '
              f'different subject, not for being weak. Those are the ones worth reading closely — they are '
              f'material that looked perfectly good and was aimed at someone else.</p>') + dr

    # the survival rule, in one plain sentence
    thr_pct = round((stats.get("threshold") or 0.45) * 100)
    rule = (f'<p class="note">Every H2 had to have at least <b>{thr_pct}%</b> of its sub-sections tagged as '
            f'useful. <b>{stats.get("survivors", "?")}</b> H2 section(s) cleared that bar and stayed; '
            f'<b>{stats.get("dead", "?")}</b> fell short and were cut. A cut H2 does not take its good '
            f'sub-sections with it — <b>{stats.get("orphans_placed", "?")}</b> of them were moved into a '
            f'surviving section instead. Only untagged sub-sections are actually lost '
            f'({stats.get("h3s_dropped", "?")} of them).</p>')

    keeps = []
    for sec in tagged.get("sections") or []:
        for h in sec.get("h3s") or []:
            rec = h.get("tag_receipts") or {}
            cards = {c for v in rec.values() for c in (v if isinstance(v, list) else [])}
            keeps.append((len(h.get("tags") or []), len(cards), sec.get("h2") or "?", h))
    keeps.sort(key=lambda x: (x[0], x[1]))
    weak = []
    for ntags, ncards, h2, h in keeps:
        tags_html = ""
        for t in h.get("tags") or []:
            rec = (h.get("tag_receipts") or {}).get(t) or []
            tip = "; ".join((glosses.get(int(c), {}).get("gloss") or f"card {c}")[:90]
                            for c in rec[:4] if str(c).isdigit()) or "no receipt cards"
            tags_html += f'<span class="tag" title="{E(tip)}">{E(t.split(":")[0])}</span>'
        cls = ' class="warn"' if ntags <= 1 or ncards <= 1 else ""
        weak.append(f'<div class="row"><div class="t"><span{cls}>{E(h.get("h3") or "?")}</span>'
                    f'<span class="chip">{ntags} tag(s) · {ncards} proof card(s)</span></div>'
                    f'<div class="m">in: {E(h2)}</div><div>{tags_html}</div></div>')

    per = sorted(stats.get("per_h2") or [], key=lambda x: x.get("coverage") or 0)
    close = "".join(
        f'<div class="row"><div class="t">'
        f'<span class="{ "no" if p.get("verdict") != "keep" else ("warn" if (p.get("coverage") or 0) < .7 else "ok")}">'
        f'{E(p.get("verdict") or "?").upper()}</span> {E(p.get("h2") or "?")}'
        f'<span class="chip">{p.get("tagged", "?")}/{p.get("h3s", "?")} tagged · '
        f'{round((p.get("coverage") or 0) * 100)}%</span></div></div>' for p in per)

    orph = "".join(
        f'<div class="row"><div class="t">{E(p.get("h3") or "?")}</div>'
        f'<div class="m">from dead: {E(p.get("from") or "?")} → placed into: {E(p.get("into") or "?")}'
        f'{" (code fallback, not AI)" if p.get("fallback") else ""}</div></div>'
        for p in placements) or '<p class="q">no orphans</p>'

    body = (_nav("Select")
            + _where("Select", "The planner has all the research. This page shows what it chose to keep, "
                               "what it threw away, and why.")
            + nums + rule
            + _world_panel(slug, "The tagger judged every sub-topic against these two lines before anything "
                                 "else. Where it refused one for belonging to a different subject, it says so "
                                 "in the reason below, so read the boundary first.")
            + '<h2>Everything we dropped — read this panel first</h2>'
            + '<p class="note">One row per sub-section (H3) that did not make it, and the H2 it used to sit under.</p>'
            + '<div class="panel">' + dr + "</div>"
            + '<h2>What we kept, thinnest evidence first</h2>'
            + '<p class="note">Weakest first. Anything on 1 tag or 1 proof card is highlighted — ask yourself '
              'whether there is enough here to write a paragraph. Nothing downstream acts on this list; it is for you.</p>'
            + '<div class="panel">' + "".join(weak) + "</div>"
            + '<h2>Close calls per section (lowest coverage first)</h2>'
            + f'<p class="note">Each H2 and how much of it was tagged useful. Anything under {thr_pct}% was CUT. '
              'The ones just above the line are the ones worth a second look.</p>'
            + '<div class="panel">' + close + "</div>"
            + '<h2>Orphans and where they went</h2>'
            + '<p class="note">Good sub-sections rescued from a cut H2 and re-homed into a surviving one.</p>'
            + '<div class="panel">' + orph + "</div>")
    out = config.artifact(slug, "selection-review.html")
    config.write_text(out, _page("Selection", f"{slug} — did we throw away something good?", body))
    return out


# ---------------------------------------------------------------- 3. SOURCES
def build_sources(slug):
    sp = _work(slug, "planner", "source-police.json") or {}
    glosses = _card_glosses(slug)

    def g(cid):
        return glosses.get(int(cid), {}) if str(cid).isdigit() else {}

    rows = []
    for cid in sp.get("kept_ok") or []:
        c = g(cid)
        rows.append(("ok", cid, c.get("gloss") or f"card {cid}", c.get("url"), None, None, None))
    for f in sp.get("fixed") or []:
        rows.append(("fixed", f.get("card_id"), f.get("claim"), f.get("old"), f.get("new"),
                     f.get("quote"), f.get("how")))
    for c in sp.get("cut") or []:
        rows.append(("cut", c.get("card_id"), c.get("claim"), c.get("old"), None, None,
                     c.get("why") or "hunted the web; no page supports this claim"))
    for cid in sp.get("unverifiable_kept") or []:
        c = g(cid)
        rows.append(("unloadable", cid, c.get("gloss") or f"card {cid}", c.get("url"), None, None,
                     "page would not load (paywall/block) — kept, but unverified"))
    for f in sp.get("search_failed") or []:
        if f.get("card_id") is None:
            continue
        c = g(f["card_id"])
        rows.append(("unchecked", f["card_id"], c.get("gloss") or f"card {f['card_id']}", c.get("url"),
                     None, None, f.get("reason")))

    counts = {}
    for r in rows:
        counts[r[0]] = counts.get(r[0], 0) + 1
    nums = _nums([("verified as-is", counts.get("ok", 0)), ("repaired", counts.get("fixed", 0)),
                  ("cut", counts.get("cut", 0)), ("unloadable, kept", counts.get("unloadable", 0)),
                  ("never checked", counts.get("unchecked", 0)),
                  ("proven-bad urls", len(sp.get("bad_urls") or []))])

    lab = {"ok": ("ok", "VERIFIED"), "fixed": ("warn", "REPAIRED"), "cut": ("no", "CUT"),
           "unloadable": ("q", "UNLOADABLE"), "unchecked": ("q", "UNCHECKED")}
    rws = []
    for verdict, cid, claim, old, new, quote, note in rows:
        cls, name = lab[verdict]
        h = (f'<div class="row" data-v="{verdict}"><div class="t"><span class="{cls}">{name}</span> '
             f'{E(str(claim or "")[:160])} <span class="chip">c{cid}</span></div>')
        if old:
            h += f'<div class="m">was: <a href="{E(old)}" target="_blank">{E(old[:90])}</a></div>'
        if new:
            h += f'<div class="m">now: <a href="{E(new)}" target="_blank">{E(new[:90])}</a></div>'
        if quote:
            h += f'<div class="reason">proof on the page: “{E(quote[:220])}”</div>'
        if note:
            h += f'<div class="reason">{E(str(note))}</div>'
        rws.append(h + "</div>")

    filters = ('<div class="filters"><button class="on" data-f="all">all</button>'
               + "".join(f'<button data-f="{v}">{lab[v][1].lower()} ({n})</button>'
                         for v, n in counts.items()) + "</div>")
    js = """
document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');
  document.querySelectorAll('[data-v]').forEach(r=>{
    r.style.display=(b.dataset.f==='all'||r.dataset.v===b.dataset.f)?'':'none';});});
"""
    # Did losing cards kill anything? A card is the smallest unit; an H3 with no cards left dies, and an
    # H2 that loses every H3 dies with it. Empty here is the healthy case, and it must SAY so.
    d_h3, d_sec = sp.get("dropped_h3s") or [], sp.get("dropped_sections") or []
    if d_h3 or d_sec:
        collapse = "".join(
            f'<div class="row"><div class="t"><span class="no">SECTION LOST</span> {E(str(s))}</div>'
            f'<div class="from">every sub-section under it lost all its evidence</div></div>' for s in d_sec)
        collapse += "".join(
            f'<div class="row"><div class="t"><span class="no">SUB-SECTION LOST</span> {E(h.get("h3") or "?")}</div>'
            f'<div class="from">was under: <b>{E(h.get("from_h2") or "?")}</b></div>'
            f'<div class="reason">{E(h.get("why") or "all its cards were cut")}</div></div>' for h in d_h3)
    elif counts.get("cut"):
        collapse = ('<p class="q">Nothing collapsed. Cards were cut, but every sub-section kept at least one '
                    'piece of evidence, so no sub-section or section was lost.</p>')
    else:
        collapse = ('<p class="q">Nothing collapsed, because nothing was cut. Every claim held up against '
                    'the page it credits.</p>')

    # Did the check actually run? Zeros mean "clean" only if it completed. Say which, loudly, at the top.
    cov = sp.get("coverage") or {}
    if cov and not cov.get("trustworthy", True):
        banner = (f'<div class="panel" style="border-color:var(--no);background:var(--no-bg)">'
                  f'<div class="t no">⚠ THIS SOURCE CHECK DID NOT COMPLETE</div>'
                  f'<div class="reason">Only <b>{cov.get("actually_judged")}</b> of '
                  f'<b>{cov.get("claims_to_check")}</b> claims were judged '
                  f'({cov.get("percent_judged")}%) — the web search failed or hit its cap, so '
                  f'<b>{cov.get("never_checked")}</b> were never checked. A low CUT count below means '
                  f'<b>not checked</b>, not clean. Re-run the planner before publishing.</div></div>')
    elif cov:
        banner = (f'<p class="note ok">✓ Check complete — {cov.get("actually_judged")} of '
                  f'{cov.get("claims_to_check")} claims judged ({cov.get("percent_judged")}%).</p>')
    else:
        banner = ""

    # THE FUNNEL. A reader seeing "14 verified" reasonably asks "14 out of what?" — the article has
    # hundreds of cards. Only a slice of them carry a citable statistic, and only a slice of THOSE need
    # a published source (a step number or a duration does not). Without this the page looks like it
    # checked almost nothing. Read straight from the two files the step already writes.
    vc = _work(slug, "planner", "verify-cards.json") or {}
    plan = _work(slug, "planner", "article-plan.tagged.json") or {}
    used = {str(c) for s in plan.get("sections", []) for h in s.get("h3s", []) for c in h.get("card_ids", [])}
    n_numeric, n_worthy = len(vc.get("numeric") or []), len(vc.get("worthy") or [])
    funnel = ""
    if n_numeric:
        funnel = (f'<h2>{n_worthy} out of what? — how this narrowed</h2>'
                  + '<div class="panel"><div class="row"><div class="t">'
                  + f'{len(used)} cards used in the plan → <b>{n_numeric}</b> carry a number → '
                    f'<b>{n_worthy}</b> needed a published source and were checked'
                  + '</div><div class="reason">Not every number needs a citation. Step numbers, years, list '
                    'counts and plain durations ("a 30-day notice period") are skipped on purpose. What gets '
                    'checked is a statistic, benchmark, study result, price, or a claim naming a specific '
                    'study, law or company. So a small number here is normal; a small number next to a '
                    'large card count is not a sign the check was skipped.</div></div>'
                  + (f'<div class="row"><div class="t no">⚠ {vc.get("failed_batches")} filter batch(es) '
                     'failed</div><div class="reason">Those cards were kept unverified rather than deleted '
                     'unjudged. Re-run the planner to close the gap.</div></div>'
                     if vc.get("failed_batches") else "")
                  + "</div>")

    kept_un = sp.get("kept_unsourced") or []
    unsourced_panel = ""
    if kept_un:
        unsourced_panel = (
            '<h2>Kept, but the source was stripped</h2>'
            '<p class="note">These cited a URL proven wrong elsewhere, but carry no number, so there is '
            'nothing specific to search for and no way to judge them. Deleting them would let a '
            'neighbour\'s bad link silently remove a fact that was never examined. So the claim stays and '
            'the false source goes. Treat them as unsourced.</p>'
            + '<div class="panel">' + "".join(
                f'<div class="row"><div class="t">{E(str(u.get("claim") or "?"))[:150]}'
                f'<span class="chip">c{u.get("card_id")}</span></div></div>' for u in kept_un[:60])
            + (f'<p class="q">…and {len(kept_un) - 60} more</p>' if len(kept_un) > 60 else "") + "</div>")

    body = (_nav("Sources")
            + _where("Sources", "Every claim carrying a citable statistic is opened against the page it "
                                "credits. This page is the verdict on each one.")
            + banner + nums + funnel
            + '<p class="note"><b>VERIFIED</b> = the page it credits really does back the claim. '
              '<b>REPAIRED</b> = the original page did not, so we searched and found one that does. '
              '<b>CUT</b> = we searched and found nothing, so the claim was removed. '
              '<b>UNLOADABLE</b> = the page would not open (paywall or block), so we kept the card unchecked '
              'rather than punish it. <b>UNCHECKED</b> = we ran out of search budget.</p>'
            + filters + '<div class="panel">' + "".join(rws) + "</div>"
            + unsourced_panel
            + '<h2>Did anything collapse?</h2>'
            + '<p class="note">Cutting a claim only removes a fact. But a sub-section that loses <i>every</i> '
              'fact has nothing left to write about, so it dies — and an H2 that loses every sub-section dies too. '
              'This is where that shows up.</p>'
            + '<div class="panel">' + collapse + "</div>")
    out = config.artifact(slug, "sources-review.html")
    config.write_text(out, _page("Sources", f"{slug} — every checked claim and its verdict", body, js))
    return out


# ---------------------------------------------------------------- 4. BLUEPRINT
def build_blueprint(slug):
    st = json.load(open(config.artifact(slug, "structure.json")))
    # the expected-topics list lives on the frozen plan, not on the structure
    _pp = config.artifact(slug, "article-plan.json")
    plan_stakes = (json.load(open(_pp)).get("table_stakes") or []) if os.path.exists(_pp) else []
    alloc = _work(slug, "architect", "word-allocation.json") or {}
    enrich = _work(slug, "architect", "enrichment.json")
    shares = {a.get("section"): a for a in (alloc.get("raw") or {}).get("allocation") or []}

    spine = ('<h2 id="spine">The spine — the one argument this article makes</h2>'
             '<p class="note">Every section below exists to move this sentence forward. If a section does not '
             'serve it, it should not be here.</p>'
             f'<div class="spine">{E(st.get("spine") or "(no spine recorded)")}</div>'
             # WHAT IT LEFT OUT (2026-08-22). The architect is now shown what people searching for
             # this expect. This line is the check on that: it is allowed to drop an expected topic,
             # and has to say which. "Left nothing out" on every article would mean it is ticking
             # boxes rather than designing, and this is where that shows.
             # HOW MANY EXPECTED TOPICS GOT A SECTION (2026-08-26). The architect now names, per
             # section, which topic every ranking page covers it is serving. Counting them is the
             # honest check on the whole change: an article where almost nothing maps is one that
             # renamed the expected ground past recognition, which is exactly what shipped before.
             + (lambda covered, total: (
                 f'<h2>Topics people expect</h2>'
                 f'<p class="note">Almost every page ranking for this subject covers a handful of '
                 f'topics. The architect names which of its sections serves each one. Too few mapped '
                 f'means the article renamed the expected ground past recognition and a reader '
                 f'scanning it will not find what they came for.</p>'
                 f'<div class="panel">'
                 + "".join(f'<div class="row"><span class="t">{E(c)}</span>'
                           f'<div>{E(h)}</div></div>' for c, h in covered)
                 + (f'<div class="row"><span class="t">not covered</span><div class="m">'
                    f'{total - len(covered)} expected topic(s) have no section</div></div>'
                    if total > len(covered) else "")
                 + '</div>') if total else "")(
                 [(s["covers"], s.get("headline") or s.get("heading", ""))
                  for s in st.get("sections", []) if s.get("covers")],
                 len(st.get("table_stakes") or plan_stakes or []))
             + (f'<h2>What it chose to leave out</h2>'
                f'<p class="note">The architect is shown the topics every ranking page covers. It is '
                f'allowed to drop any that do not serve this article. Watch for the opposite of a '
                f'problem here: if it never drops anything, it has stopped judging.</p>'
                f'<div class="panel">{E(st["coverage_note"])}</div>'
                if st.get("coverage_note") else ""))

    comp = ""
    if st.get("entities") or st.get("yardsticks"):
        comp = ('<h2>The comparison frame</h2><div class="panel">'
                f'<div class="row"><span class="t">Options compared</span><div>'
                f'{E(", ".join(st.get("entities") or []) or "—")}</div></div>'
                f'<div class="row"><span class="t">Yardsticks (what they are judged on)</span><div>'
                f'{E(", ".join(st.get("yardsticks") or []) or "—")}</div></div></div>')

    bench = "".join(
        f'<div class="row"><div class="t">{E(b.get("h3") or "?")}'
        f'<span class="chip">{b.get("cards", "?")} cards</span></div>'
        f'<div class="m">from: {E(b.get("from_h2") or "?")}</div>'
        + (f'<div class="reason">{E(b["why_benched"])}</div>' if b.get("why_benched")
           else '<div class="reason no">NO REASON RECORDED — the architect must justify every bench</div>')
        + "</div>"
        for b in st.get("unused_boxes") or []) or '<p class="q">nothing benched</p>'

    total_w = sum(s.get("word_target") or 0 for s in st.get("sections") or []) or 1
    secs = []
    for i, s in enumerate(st.get("sections") or []):
        sh = shares.get(i) or {}
        wt = s.get("word_target") or 0
        # the lead group (the prose above the first H3) carries cards too and lives outside h3s
        h3s = "".join(f"<li>{E(h.get('h3') or '(opening, no sub-heading)')} "
                      f"<span class='q'>({len(h.get('card_ids') or [])} cards)</span></li>"
                      for h in ([s['lead']] if (s.get('lead') or {}).get('card_ids') else [])
                      + list(s.get("h3s") or []))
        secs.append(
            f'<div class="row"><div class="t">{i + 1}. {E(s.get("headline") or "?")}'
            f'<span class="chip">{wt}w · {sh.get("share", "?")}% share</span></div>'
            f'<div class="job">Job: {E(s.get("job") or "(none)")}</div>'
            f'<div class="bar"><i style="width:{max(2, round(100 * wt / total_w))}%"></i></div>'
            + (f'<div class="reason q">why this share: {E(sh.get("why") or "")}</div>' if sh.get("why") else "")
            + f"<ul>{h3s}</ul></div>")

    if enrich is None:
        research = '<p class="q">no enrichment log on file for this run</p>'
    elif not enrich:
        research = '<p class="q">Nothing flagged — the architect judged the plan complete without new research.</p>'
    else:
        research = "".join(
            f'<div class="row"><div class="t">{E(e.get("h3") or "?")}'
            f'<span class="chip">{E(e.get("status") or "?")}</span></div>'
            f'<div class="m">in: {E(e.get("section") or "?")} · queries: '
            f'{E("; ".join(e.get("queries") or []) or "—")} · pages read: {len(e.get("pages") or [])} · '
            f'cards produced: {e.get("cards_kept", 0)}</div></div>' for e in enrich)

    # ---- Step 4: the gate + the hunt. The ONLY place the architect spends money, so it gets its own panel:
    # what was judged worth a lookup, what was searched, and every section that honestly found nothing.
    # A MISSING file gets an explicit note, never a silent gap. This page is judged by what it shows, so a
    # step that did not run has to look different from a step that ran and found nothing.
    MISSING = ('<h2>{title}</h2><div class="panel"><p class="q">No <b>{f}</b> on file for this run. Either this '
               'article predates the step, or the step did not complete — check the run log before reading the '
               'rest of this page as complete.</p></div>')
    sk = _work(slug, "architect", "section-keywords.json")
    gatep = MISSING.format(title="Section keywords — what we paid to look up", f="section-keywords.json")
    if sk:
        rows, n_hunt, n_found = [], 0, 0
        for r in sk.get("sections") or []:
            g = r.get("gate") or {}
            hunted = bool(g.get("hunt"))
            n_hunt += hunted
            head = f'{r.get("n")}. {E(r.get("heading") or "?")}'
            if not hunted:
                rows.append(f'<div class="row"><div class="t">{head}<span class="chip">no lookup</span></div>'
                            f'<div class="reason q">{E(g.get("why") or "gate gave no reason")}</div></div>')
                continue
            pick, seeds = r.get("pick") or {}, r.get("seeds") or []
            detail = (f'<div class="m">seeds: {E("; ".join(seeds) or "—")} · '
                      f'{r.get("candidates", 0)} candidate(s) cleared vol/KD</div>')
            if pick:
                n_found += 1
                rows.append(f'<div class="row"><div class="t">{head}'
                            f'<span class="chip ok">{E(pick.get("keyword") or "")}</span>'
                            f'<span class="chip">vol {pick.get("volume", "?")} · KD {pick.get("kd", "?")}</span></div>'
                            + detail + f'<div class="reason">{E(pick.get("why") or "")}</div></div>')
            else:
                why = r.get("why_none") or r.get("error") or "no pick recorded"
                rows.append(f'<div class="row"><div class="t">{head}<span class="chip warn">none taken</span></div>'
                            + detail + f'<div class="reason">{E(why)}</div></div>')
        gatep = ('<h2 id="keywords">Section keywords — what we paid to look up</h2>'
                 '<p class="note">A free gate first decides which sections a stranger would actually search for; '
                 'only those get a paid lookup. Most sections should say <b>no lookup</b> — they carry the argument '
                 'rather than a search. <b>None taken</b> is a good answer too: a big number for a phrase the section '
                 'does not answer just means the page ranks and the reader bounces. What to check here is whether '
                 'each reason is honest.</p>'
                 + _nums([("sections", len(sk.get("sections") or [])), ("gated for lookup", n_hunt),
                          ("keyword found", n_found), ("found nothing", n_hunt - n_found)])
                 + '<div class="panel">' + "".join(rows) + "</div>")

    # ---- Step 5: every heading, and the H1 written last.
    hm = _work(slug, "architect", "heading-map.json")
    kwp = MISSING.format(title="The headings, and the H1", f="heading-map.json")
    if hm:
        d = hm.get("decision") or {}
        rows = [f'<div class="row"><span class="t">Primary</span><div><b>{E(d.get("primary") or "?")}</b>'
                ' <span class="chip">research picked this; the architect never overrides it</span></div></div>']
        h1p, h1f = hm.get("h1_planned") or "", hm.get("h1_final") or ""
        rows.append('<div class="row"><span class="t">H1</span><div>'
                    + (f'<b>{E(h1f)}</b> <span class="chip">{len(h1f)} chars</span>'
                       + (f'<div class="reason">was: “{E(h1p)}”<br>{E(hm.get("why_h1") or "")}</div>'
                          if h1f != h1p else ' <span class="chip">unchanged from the plan</span>'))
                    + "</div></div>")
        # Two different steps can rewrite a heading, and they must not be shown as one. 5a writes each
        # heading from its own section alone; 5b then reads the whole set and fixes what only the set
        # reveals. Without this split the page printed 5a's reason next to 5b's heading — an explanation
        # of wording that is no longer on the page.
        xs = hm.get("cross_section_pass") or {}
        by_pass = {c.get("n"): c for c in (xs.get("changes") or []) if not c.get("kept")}
        reverted = [c for c in (xs.get("changes") or []) if c.get("kept")]
        changed = [h for h in hm.get("headings") or [] if h.get("changed")]
        if changed:
            out_rows = []
            for h in changed:
                p = by_pass.get(h.get("n"))
                kw = (f' <span class="chip ok">{E(h["keyword_used"])}</span>' if h.get("keyword_used")
                      else ' <span class="chip">no keyword</span>')
                if p:                       # the set-wide pass had the last word on this heading
                    out_rows.append(
                        f'<div class="reason">#{h.get("n")} “{E(h.get("was") or "")}” → '
                        f'<b>{E(h.get("heading") or "")}</b>{kw}'
                        f'<br><span class="chip">read as a set</span> {E(p.get("why") or "")}</div>')
                else:
                    out_rows.append(
                        f'<div class="reason">#{h.get("n")} “{E(h.get("was") or "")}” → '
                        f'<b>{E(h.get("heading") or "")}</b>{kw}<br>{E(h.get("why") or "")}</div>')
            rows.append('<div class="row"><span class="t">Headings rewritten</span>' + "".join(out_rows) + "</div>")
        else:
            rows.append('<div class="row"><span class="q">No heading was rewritten — the shaped drafts all '
                        'survived as written.</span></div>')
        if xs.get("notes"):
            rows.append('<div class="row"><span class="t">Read as a set</span><div>'
                        '<div class="m">Every heading above was written by a different call that saw only its '
                        'own section. One more pass then read them all together — the only step that can catch '
                        'numbering that does not run, one thing called two names, or mixed capitalisation.</div>'
                        f'<div class="reason">{E(xs["notes"])}</div>'
                        f'<span class="chip">{xs.get("edited", 0)} heading(s) edited by that pass</span>'
                        '</div></div>')
        if reverted:
            rows.append('<div class="row"><span class="t warn">Put back</span>'
                        '<div class="m">The set-wide pass proposed these, and code refused them: a heading may '
                        'not lose the keyword research bought for it. The original stands.</div>'
                        + "".join(f'<div class="reason">#{c.get("n")} proposed “{E(c.get("proposed") or "")}”'
                                  f'<br>{E(c.get("why") or "")}</div>' for c in reverted) + "</div>")
        # over-length is RECORDED, never rejected — so the page has to surface it or nobody ever sees it
        long_ones = hm.get("over_length") or []
        if long_ones:
            rows.append('<div class="row"><span class="t warn">Over 60 characters</span>'
                        '<div class="m">Kept on purpose. 60 is a target, not a wall: a longer heading is right '
                        'when the shorter one would say less. Worth an eye anyway — these get cut off in search '
                        'results.</div>'
                        + "".join(f'<div class="reason">#{o.get("n")} ({o.get("chars")} chars) {E(o.get("heading") or "")}</div>'
                                  for o in long_ones) + "</div>")
        unp = d.get("unplaced") or []
        if unp:
            rows.append('<div class="row"><span class="t">Keywords no heading took</span>'
                        + "".join(f'<div class="reason">“{E(u.get("keyword") or "")}” — {E(u.get("why") or "")}</div>'
                                  for u in unp) + "</div>")
        kwp = '<h2 id="headings">The headings, and the H1</h2><div class="panel">' + "".join(rows) + "</div>"

    # the word budget, stated once and in plain terms
    band = st.get("word_budget") or {}
    n_sec = len(st.get("sections") or [])
    total_line = (f'<p class="note"><b>{total_w:,} words</b> planned in total across <b>{n_sec}</b> sections'
                  + (f' (target band {band.get("min"):,}–{band.get("max"):,} words)'
                     if band.get("min") and band.get("max") else "")
                  + f'. Average <b>{round(total_w / max(n_sec, 1)):,}</b> words per section. The bar shows each '
                    'section\'s share of the article.</p>')

    # ---- the coherence pass: what reading the whole article revealed --------------------------
    cr = _work(slug, "writer", "coherence-report.json")
    cohp = ""
    if cr:
        inv = cr.get("inventory") or {}
        scales = inv.get("scales") or []
        kinds = {}
        for x in scales:
            k = str(x.get("scale", "")).strip()
            kinds.setdefault(k, []).append(str(x.get("section", "?")))
        inv_rows = ""
        if kinds:
            inv_rows += ('<div class="row"><div class="t">Scales this article uses'
                         + (f'<span class="chip no">{len(kinds)} different ones</span>' if len(kinds) > 1
                            else '<span class="chip ok">just one</span>') + "</div>"
                         + "".join(f'<div class="reason">{E(k)} <span class="q">&times;{len(v)} — '
                                   f'{E(", ".join(dict.fromkeys(v))[:110])}</span></div>'
                                   for k, v in kinds.items()) + "</div>")
        # "promises" was dropped from the inventory on 2026-08-11 with the promise-not-kept fault
        for label, key, fld in (("Rules and warnings it states", "rules", "text"),
                                ("Quantities it names", "quantities", "amount")):
            items = inv.get(key) or []
            if not items:
                continue
            inv_rows += (f'<div class="row"><div class="t">{E(label)}<span class="chip">{len(items)}</span></div>'
                         + "".join(f'<div class="reason q">{E(str(x.get(fld, ""))[:170])}</div>'
                                   for x in items[:12]) + "</div>")

        applied = cr.get("applied")
        diff = cr.get("diff") or []
        n_edits = sum(len(d.get("edits") or []) for d in diff)
        fails = cr.get("guard_failures") or []
        chg = cr.get("changes_claimed") or []
        cant = cr.get("could_not_fix") or []

        warns = cr.get("warnings") or []
        declared = cr.get("numbers_changed_claimed") or []
        wrows = ""
        for wn in warns:
            cls = "no" if wn.get("kind") == "numbers changed" else "warn"
            wrows += (f'<div class="row"><div class="t {cls}">{E(wn.get("kind","?"))}'
                      f'<span class="chip">{len(wn.get("detail") or [])}</span></div>'
                      f'<div class="reason q">{E(wn.get("note") or "")}</div>'
                      f'<div class="reason">{E(", ".join(str(x) for x in (wn.get("detail") or []))[:400])}</div></div>')
        for d in declared:
            wrows += (f'<div class="row"><div class="t">declared: {E(str(d.get("was"))[:40])} &rarr; '
                      f'{E(str(d.get("now"))[:40])}</div>'
                      f'<div class="reason q">{E(d.get("why") or "")}</div></div>')
        warnp = ('<h2>Read this first — what changed that nobody blocked</h2>'
                 '<p class="note">These are allowed on purpose, because blocking them would throw away the '
                 'repair. A rating band changing from 0-2-4 to 1-5 is the fix. A statistic changing is a '
                 'fact change. Both look identical to code, so they are shown to you instead.</p>'
                 '<div class="panel">' + wrows + "</div>") if wrows else ""

        state = ('<p class="note ok"><b>Edits applied.</b> Every safety check passed.</p>' if applied
                 else '<p class="note no"><b>Edits REJECTED — the original was published unchanged.</b> '
                      + E("; ".join(fails) or cr.get("reason") or "no reason recorded") + "</p>")

        chg_rows = "".join(
            f'<div class="row"><div class="t">{E(c.get("kind","?"))}'
            f'<span class="chip">{E(str(c.get("section","?"))[:44])}</span></div>'
            f'<div class="reason">{E(c.get("what_you_did") or "")}</div>'
            f'<div class="reason q">{E(c.get("why") or "")}</div></div>' for c in chg)
        cant_rows = "".join(
            f'<div class="row"><div class="t">could not fix<span class="chip warn">needs you</span></div>'
            f'<div class="reason">{E(c.get("what") or "")} — <i>{E(str(c.get("where") or ""))}</i></div>'
            f'<div class="reason q">{E(c.get("why_not") or "")}</div></div>' for c in cant)
        diff_rows = "".join(
            f'<div class="row"><div class="t">{E(d.get("block","?")[:60])}'
            f'<span class="chip">{len(d.get("edits") or [])} change(s)</span></div>'
            + "".join(f'<div class="reason q">was: {E(str(e.get("was"))[:190])}</div>'
                      f'<div class="reason">now: {E(str(e.get("now"))[:190])}</div>'
                      for e in (d.get("edits") or [])[:4]) + "</div>" for d in diff)

        cohp = ('<h2>Reading the article whole</h2>'
                '<p class="note">Every section was written by a different writer at the same time, so faults '
                'BETWEEN sections are invisible to every other step. This is the one pass that reads the '
                'finished article end to end. It first LISTS every rule, scale and number (below), then edits '
                'with that list in front of it. The changes shown are <b>measured</b> by comparing the before '
                'and after, not taken from what it claims. If any safety check fails, the whole edit is thrown '
                'away and the original publishes.</p>'
                + (f'<p class="note"><b>Verdict:</b> {E(cr.get("verdict") or "-")}</p>' if cr.get("verdict") else "")
                + state
                + warnp
                + _nums([("passages changed", n_edits), ("blocks touched", len(diff)),
                         ("fixes claimed", len(chg)), ("left for you", len(cant))])
                + ('<h2>What it found in the article</h2><div class="panel">' + inv_rows + "</div>" if inv_rows else "")
                + ('<h2>What it changed</h2><div class="panel">' + chg_rows + "</div>" if chg_rows else "")
                + ('<h2>What it could not fix</h2><div class="panel">' + cant_rows + "</div>" if cant_rows else "")
                + ('<h2>Every change, measured</h2><div class="panel">' + diff_rows + "</div>" if diff_rows else ""))

    body = (_nav("Blueprint")
            + _where("Blueprint", "The facts are settled. This page is the plan for the article itself: "
                                  "what it argues, which sections carry it, and how long each one gets.")
            + spine
            + _world_panel(slug, "Written in the research phase, before any searching started, and never changed "
                                 "since. It is one of the stated reasons the architect benches material below, so "
                                 "read it before judging whether a bench was right.")
            + cohp + gatep + kwp + comp
            + '<h2 id="bench">The bench — what the architect chose NOT to use</h2>'
            + '<p class="note">Material that survived selection but the architect still left out. Every bench '
              'needs a stated reason; a missing one is flagged in red. A bench for belonging to the NOT ABOUT '
              'world above is the one to check hardest, because it is the one that saves the article.</p>'
            + '<div class="panel">' + bench + "</div>"
            + '<h2 id="sections">The sections, in reading order</h2>' + total_line
            + '<div class="panel">' + "".join(secs) + "</div>"
            + '<h2 id="research">Research: asked for vs delivered</h2>'
            + '<p class="note">If a section was too thin, the architect could ask for fresh web research. '
              'This is what it asked for and what came back.</p>'
            + '<div class="panel">' + research + "</div>")
    out = config.artifact(slug, "blueprint-review.html")
    config.write_text(out, _page("The blueprint", f"{slug} — architect review", body))
    return out


# ------------------------------------------------- 5-9. THE WRITER, STEP BY STEP
#
# Until now the writer's five prose steps had no page of their own: body, blend, wrapper, coherence
# and clean were all squashed into one "What was done to it" block at the foot of article.html, and
# COHERENCE was not shown anywhere at all — a whole AI pass that rewrites the article, invisible.
# Slop and links already had their own pages (slop_pass.py / links_pass.py build them), so these five
# finish a pattern the repo had already started rather than inventing a new one.


def _norm(t):
    return " ".join((t or "").split())


def _wdiff(a, b):
    """Word-level before/after, reusing the writer page's renderer so one diff style exists."""
    import review_page
    return review_page._word_diff(a, b)


def _diff_rows(pairs, badge_of=None, note_of=None):
    """pairs: [(heading, before, after)]. Only genuinely-changed blocks become rows."""
    rows = []
    for h, before, after in pairs:
        if _norm(before) == _norm(after):
            continue
        badge = badge_of(h) if badge_of else ""
        note = note_of(h) if note_of else ""
        rows.append(f'<details class="diff"><summary>{E(h[:95])} {badge}</summary>'
                    f'{note}<div class="dbody">{_wdiff(before, after)}</div></details>')
    return rows


def _strip_h2(prose):
    """The body writer repeats its own "## Heading" line; the later stages do not. Drop it so a
    diff between the two stages does not report the heading as a deletion."""
    p = prose or ""
    return p.split(chr(10), 1)[-1].strip() if p.startswith("##") else p


_BULLET = re.compile(r"^(?:[-*\u2022]|\d+[.)])\s")
_PARA_SPLIT = re.compile(r"\n\s*\n")


def _prose_html(text):
    """A writer's raw prose as readable paragraphs, with its [c123] source tags left visible."""
    out = []
    for para in _PARA_SPLIT.split((text or "").strip()):
        para = para.strip()
        if not para or para.startswith("##"):
            continue                                  # the writer repeats its own heading; the row has it
        lines = [ln.strip() for ln in para.split(chr(10)) if ln.strip()]
        if all(_BULLET.match(ln) for ln in lines):
            items = "".join("<li>" + E(_BULLET.sub("", ln)) + "</li>" for ln in lines)
            out.append(f'<ul class="kwlist">{items}</ul>')
        else:
            out.append("<p>" + E(" ".join(lines)) + "</p>")
    return "".join(out) or '<p class="q">(empty)</p>'


def build_body(slug):
    """writer/body-review.html — the first draft, exactly as the section writers produced it."""
    body_j = _work(slug, "writer", "body.json")
    if body_j is None:
        raise FileNotFoundError(config.artifact(slug, "body.json"))
    secs = body_j["sections"]
    tot_target = sum(s.get("word_target") or 0 for s in secs)
    tot_words = sum(s.get("words") or 0 for s in secs)
    dropped = sum(s.get("bad_tags_dropped") or 0 for s in secs)
    sourced = sum(1 for s in secs if s.get("provenance"))

    rows = []
    for s in secs:
        tgt, got = s.get("word_target") or 0, s.get("words") or 0
        off = (got - tgt) / tgt * 100 if tgt else 0
        cls = "no" if abs(off) >= 25 else "ok"
        prov = s.get("provenance") or []
        nums = sum(1 for p in prov if p.get("is_number"))
        srcs = sorted({p.get("source_url") for p in prov if p.get("source_url")})
        ev = "".join(
            f'<li>{E((p.get("claim") or "").strip()[:220])}'
            + (' <span class="chip no">a number</span>' if p.get("is_number") else "")
            + (f' <a href="{E(p["source_url"])}" target="_blank" class="q">source</a>'
               if p.get("source_url") else ' <span class="q">no link on file</span>')
            + "</li>" for p in prov[:60])
        rows.append(
            f'<details class="diff"><summary>{E(s["headline"][:95])} '
            f'<span class="chip">wrote {got} words, was asked for {tgt}</span> '
            f'<span class="chip {cls}">{off:+.0f}%</span> '
            + ('<span class="chip warn">used no research at all</span>' if not prov else
               f'<span class="chip">used {len(prov)} facts · {nums} of them numbers · '
               f'{len(srcs)} sources</span>')
            + "</summary>"
            + f'<div class="q"><b>What this section was asked to do:</b> {E(s.get("job") or "—")}</div>'
            + '<div class="subh">What the writer actually wrote</div>'
            + f'<div class="dbody">{_prose_html(s.get("prose"))}</div>'
            + (f'<div class="subh">The research it used — {len(prov)} fact(s)</div>'
               f'<ul class="kwlist">{ev}</ul>' if ev else
               '<div class="subh">The research it used</div>'
               '<p class="q">None recorded. Everything above is the model\'s own words.</p>')
            + "</details>")

    body = (_nav("Body")
            + reads_link("write-body")
            + _where("", "This is the article before anyone repaired it. Every section was written by its own "
                         "separate AI call, and all of them ran at the same time, so no writer could see what any "
                         "other one wrote. Each was handed only its own heading, the job that heading has to do, a "
                         "word budget, and the fact cards for it. That is why the sections arrive reading like "
                         "strangers, repeating each other and referring to things that are not there — every later "
                         "step exists to fix that. What you are judging here is the raw material: did each writer "
                         "use the evidence it was given, and did it write to the length the plan asked for.")
            + _where("", f"Each writer is shown far more facts than it may use, and told to keep at most "
                         f"{config.BODY_MAX_STATS} SOLID statistics — a figure the argument leans on. Years, "
                         f"numbers inside names, and small numbers in passing do not count against that, and "
                         f"zero is an acceptable answer. So a section listing eight facts below and using two "
                         f"of them is the rule working, not evidence being wasted. Whether a figure is solid "
                         f"is a judgment, so nothing here counts it for you; the fact list under each section "
                         f"is where you check what was offered against what was taken.")
            + _nums([("sections written", len(secs)), ("words written", f"{tot_words:,}"),
                     ("words the plan asked for", f"{tot_target:,}"),
                     ("sections backed by research", f"{sourced}/{len(secs)}"),
                     ("made-up source tags code removed", dropped)])
            + "<h2>How to read the rows below</h2>"
            + '<p class="note">Click any heading to open that section. Inside you get three things: <b>the job</b> '
              'the plan gave it, <b>the words the writer actually produced</b>, and <b>every fact it was handed</b> '
              'with a link to the source. The tags in the prose, like <code>[c412]</code>, mark which fact each '
              'sentence came from.</p>'
            + '<p class="note"><b>What to watch for.</b> A section more than 25% off its word budget is marked in '
              'red: far under means the writer ran out of material and the section will read thin, far over means '
              'it wandered. A section that used no research is opinion, not evidence.</p>'
            + "<h2>Every section, exactly as it was first written</h2>"
            + "".join(rows))
    out = config.artifact(slug, "body-review.html")
    config.write_text(out, _page("The first draft", f"{slug} — what the section writers produced", body))
    return out


def build_editor(slug):
    """writer/editor-review.html — the blend step: what the editor cut, wove and left alone."""
    bl = _work(slug, "writer", "blend.json")
    body_j = _work(slug, "writer", "body.json")
    if bl is None or body_j is None:
        raise FileNotFoundError(config.artifact(slug, "blend.json"))
    orig = {s["headline"]: _strip_h2(s["prose"]) for s in body_j["sections"]}
    edited = {s["heading"]: s["prose"] for s in bl["sections"]}

    declared = {str(e.get("section")) for e in bl.get("edits") or []} - {"(all)"}
    why = {}
    for e in bl.get("edits") or []:
        why.setdefault(str(e.get("section")), []).append(f"{e.get('what')}: {e.get('why')}")

    def badge(h):
        return ('<span class="chip ok">declared</span>' if h in declared
                else '<span class="chip warn">NOT declared by the editor</span>')

    def note(h):
        r = why.get(h) or []
        return ((f'<div class="q">{len(r)} edits declared here:</div>' if len(r) > 1 else "")
                + "".join(f'<div class="q">• {E(x)}</div>' for x in r))

    pairs = [(h, orig.get(h, ""), after) for h, after in edited.items()]
    rows = _diff_rows(pairs, badge, note)
    changed = {h for h, b, a in pairs if _norm(b) != _norm(a)}
    phantom = sorted(declared - changed)

    ta = bl.get("tag_audit") or {}
    cut = ta.get("cut_with_content") or []
    inv = ta.get("invented_stripped", 0)
    tag_panel = (
        '<h2>The source-tag audit</h2>'
        '<p class="note">Every fact carries a tag like [c412] naming where it came from. Code counted the '
        'tags before and after this step, so this is <b>measured, not the editor reporting on itself</b>. A '
        'tag that exists only afterwards is a source the editor invented: it is deleted and counted here. A '
        'tag that disappears left with a sentence the editor cut, which is allowed, but never silent.</p>'
        '<div class="panel">'
        f'<div class="row"><span class="t">tags</span><div><b>{ta.get("tags_before", 0)}</b> before → '
        f'<b>{ta.get("tags_after", 0)}</b> after</div></div>'
        f'<div class="row"><span class="t">invented</span><div class="{"no" if inv else "ok"}">'
        f'<b>{inv}</b>{"" if inv else " — nothing was faked"}</div></div>'
        f'<div class="row"><span class="t">disappeared</span><div>'
        + (f'<b>{len(cut)}</b> left with the content they supported: {E(", ".join("c%s" % c for c in cut))}'
           if cut else "none") + "</div></div></div>") if ta else ""

    # THE COUNTER. Code counts long sentences and fat paragraphs before the editor runs, hands it the
    # exact list, and counts again afterwards. Both numbers are measured, neither is reported.
    cb, ca = bl.get("counter_before") or {}, bl.get("counter_after") or {}
    counter = (f'<div class="panel">'
               f'<div class="row"><span class="t">sentences over 25 words</span><div>'
               f'<b>{cb.get("long_sentences", 0)}</b> before → <b>{ca.get("long_sentences", 0)}</b> after</div></div>'
               f'<div class="row"><span class="t">paragraphs over 4 sentences</span><div>'
               f'<b>{cb.get("fat_paragraphs", 0)}</b> before → <b>{ca.get("fat_paragraphs", 0)}</b> after</div></div>'
               f'</div>') if cb else ""

    # THE FLAGS. Anything in guard_failures threw the whole edit away; anything in warnings did not.
    flags = "".join(f'<p class="no"><b>BLOCKED:</b> {E(f)}</p>' for f in bl.get("guard_failures") or [])
    flags += "".join(f'<p class="q"><b>{E(w.get("kind"))}:</b> '
                     f'{E(", ".join(str(x) for x in (w.get("detail") or [])[:8]))}</p>'
                     for w in bl.get("warnings") or [])
    flags = (f'<div class="panel">{flags}</div>' if flags
             else '<div class="panel"><p class="ok">No flags. Nothing was blocked.</p></div>')

    # LENGTH. Blend is the last step that measures it before the article is judged, so the verdict
    # lives here. The wrapper reserve matters: blend sees only the sections, and an intro, five FAQ
    # answers and a close are written after it.
    la = bl.get("length_after") or {}
    if la.get("band_max"):
        over, under = la.get("over_by", 0), la.get("under_by", 0)
        verdict = (f'<span class="no"><b>{over:,} words over</b></span>' if over else
                   f'<span class="q">{under:,} words under</span>' if under else
                   '<span class="ok"><b>inside the aim</b></span>')
        length_panel = (
            '<h2>Length</h2>'
            '<p class="note">The finished article should land inside the band the research phase set. '
            'Blend only sees the sections: an intro, five FAQ answers and a close are written after it '
            f'and add about {la["wrapper_reserve"]} words, so the sections have to come in below the '
            'band, not inside it.</p>'
            f'<div class="panel">'
            f'<div class="row"><span class="t">sections now</span><div><b>{la["words"]:,}</b> words</div></div>'
            f'<div class="row"><span class="t">they needed to be</span><div>'
            f'{la["aim_min"]:,} to {la["aim_max"]:,}</div></div>'
            f'<div class="row"><span class="t">verdict</span><div>{verdict}</div></div>'
            f'<div class="row"><span class="t">the real band</span><div class="q">'
            f'{la["band_min"]:,} to {la["band_max"]:,} for the finished article</div></div></div>')
    else:
        length_panel = ""

    kw = "".join(f'<li><b>{E(k.get("keyword"))}</b> — appears <b>{k.get("after", 0)}</b> time(s)'
                 + (f' <span class="q">(was {k.get("before", 0)}, so the editor added {k.get("after",0)-k.get("before",0)})</span>'
                    if k.get("after", 0) > k.get("before", 0) else
                    ' <span class="q">(unchanged)</span>' if k.get("after") else
                    ' <span class="q">(never used)</span>')
                 + "</li>" for k in bl.get("keywords_measured") or [])
    kw = kw or '<li class="q">no keywords on file</li>'

    body = (_nav("Editor")
            + reads_link("blend")
            + _where("", 'Twelve writers wrote twelve sections and none of them could see any other. '
                         'This step is the first to read them all, joins them into one piece, and cuts what did '
                         'not earn its place: a point made twice, a term explained twice, fluff, a section that '
                         'never lands its point. Code counts the over-long sentences and paragraphs first and '
                         'hands it the exact list, so it judges rather than hunts. It is never shown the source '
                         'cards, so it has no facts to add even if it wanted to.')
            + _nums([("sections it changed", len(rows)),
                     ("passages changed", sum(len(d.get("edits") or []) for d in bl.get("diff") or [])),
                     ("edits it declared", len(bl.get("edits") or []))]
                    # only when the counter actually ran; an older run has no such numbers and
                    # printing "0 long sentences left" would be a measurement nobody took
                    + ([("long sentences left", ca.get("long_sentences", 0))] if cb else [])
                    + [("invented source tags removed", inv)])
            + '<p class="note"><b>How to read this.</b> One row per section that actually changed, worked out '
              'by comparing the text, not by asking. Click a row: <del>deleted</del> words are red, '
              '<ins>added</ins> words are green. <b>Declared</b> means the editor owned up to that section; '
              '<b>NOT declared</b> means it changed the words and did not say so. Read those first.</p>'
            + (f'<div class="panel"><p class="no"><b>Declared but unchanged:</b> {E(", ".join(phantom))}. '
               'It claimed an edit here and the text is identical.</p></div>' if phantom else "")
            + "<h2>Flags</h2>" + flags
            + length_panel
            + (f"<h2>Did the long sentences come down?</h2>{counter}" if counter else "")
            + f"<h2>Every change it made — {len(rows)} section(s)</h2>"
            + ("".join(rows) or '<div class="panel"><p class="no">No section changed. On an article written '
                                'by writers who could not see each other, that is a non-result, not a clean '
                                'bill.</p></div>')
            + tag_panel
            + "<h2>Keywords</h2>"
            + '<p class="note">Counted in the finished text by code. The editor also reports its own count and '
              'that report has been wrong, once claiming six woven out of a set of five, so only these numbers '
              'are shown.</p>'
            + f'<div class="panel"><ul class="kwlist">{kw}</ul></div>')
    out = config.artifact(slug, "editor-review.html")
    config.write_text(out, _page("The editor", f"{slug} — joining the sections, then cutting what did not earn its place", body))
    return out


def build_wrapper_page(slug):
    """writer/wrapper-review.html — the intro, FAQ and close, plus the two seams they create."""
    wr = _work(slug, "writer", "wrapper.json")
    bl = _work(slug, "writer", "blend.json")
    if wr is None or bl is None:
        raise FileNotFoundError(config.artifact(slug, "wrapper.json"))
    before = {s["heading"]: s["prose"] for s in bl["sections"]}
    after = {s["heading"]: s["prose"] for s in wr["sections"]}
    tu = {str(t.get("heading")): f'{t.get("what")}: {t.get("why")}' for t in wr.get("touch_ups_applied") or []}
    rows = _diff_rows([(h, before.get(h, ""), a) for h, a in after.items()],
                      lambda h: '<span class="chip">touch-up</span>',
                      lambda h: f'<div class="q">• {E(tu[h])}</div>' if h in tu else
                                '<div class="q">• <b>not declared</b> as a touch-up</div>')

    # draws_on was removed on 2026-08-11 with the rule it enforced. An answer is now judged on its
    # LENGTH, because an FAQ answer is what a search engine lifts and shows on its own.
    faq = []
    for f in wr.get("faq") or []:
        n = f.get("words") or len((f.get("answer") or "").split())
        origin = ('<span class="chip">from real searches</span>'
                  if (f.get("origin") or "").startswith("resear") else
                  '<span class="chip">the editor found this one</span>')
        length = (f'<span class="chip warn">{n} words, over {config.WRAP_FAQ_WORDS}</span>'
                  if f.get("over_target") else f'<span class="chip ok">{n} words</span>')
        # Figures the article does not contain. NOT a fault: the FAQ is allowed to answer past the
        # article. Shown so a human can spot-check the ones that came from outside it.
        outs = f.get("outside_numbers") or []
        num = (f'<span class="chip warn">check {len(outs)} figure(s) from outside the article</span>'
               if outs else "")
        faq.append(f'<details class="diff"><summary>{E(f.get("question") or "")[:110]} {origin}{length}{num}</summary>'
                   f'<div class="dbody">{E(f.get("answer") or "")}</div>'
                   + (f'<div class="q">not in the article: {E(", ".join(outs))}</div>' if outs else "")
                   + "</details>")

    dropped = "".join(f'<li>{E(d.get("question") or "")} — <span class="q">{E(d.get("why") or "")}</span></li>'
                      for d in wr.get("dropped_questions") or [])
    # touch_ups_ignored is a list of HEADING STRINGS — wrapper.py appends the heading it could not
    # match, not a record. This read it as dicts and crashed the whole page build with
    # "'str' object has no attribute 'get'", which is why one article shipped with four review pages
    # missing (2026-08-26). Handles both shapes, because an older run may hold either.
    ig = wr.get("touch_ups_ignored") or []
    def _ig(x):
        if isinstance(x, dict):
            return (str(x.get("heading") or ""), str(x.get("why") or x.get("what") or ""))
        return (str(x), "the wrapper named a heading that is not in the article, so it was skipped")
    ignored = "".join(f'<li>{E(h)} — <span class="q">{E(why)}</span></li>'
                      for h, why in (_ig(x) for x in ig))

    body = (_nav("Wrapper")
            + reads_link("wrapper")
            + _where("", 'The article has a middle but no beginning and no end. This step writes the four '
                         'things around it: the opening, the Quick answer, the FAQ, and the closing. The '
                         'Quick answer is the whole piece in 60 to 110 words, for the reader who reads nothing '
                         'else — it has to ANSWER, not list takeaways. The opening follows problem, '
                         'agitate, solution, and the solution is the article\'s own answer, never the product. '
                         'The FAQ takes real searched questions first, and it is allowed to answer things the '
                         'article does not cover, because a question the article already answers under a heading '
                         'is a wasted slot. Adding an opening and a closing creates two new seams, so it may also '
                         'repair those two joins and nothing else.')
            + _nums([("intro words", len((wr.get("intro") or "").split())),
                     ("quick answer words", len((wr.get("quick_answer") or "").split())),
                     ("FAQ questions", len(wr.get("faq") or [])),
                     ("answers over %d words" % config.WRAP_FAQ_WORDS,
                      sum(1 for f in wr.get("faq") or [] if f.get("over_target"))),
                     ("close words", len((wr.get("close") or "").split())),
                     ("touch-ups applied", len(wr.get("touch_ups_applied") or [])),
                     ("invented source tags removed", wr.get("invented_tags_stripped", 0))])
            + '<p class="note"><b>How to read this.</b> The H1 and opening, then every FAQ question (click one '
              'for its answer), then the closing, then any seam it repaired. In a seam repair, <del>red</del> is '
              'what it removed and <ins>green</ins> is what it added.</p>'
            + '<p class="note"><b>The FAQ badges.</b> <b>From real searches</b> means the question came from what '
              'people type into Google; <b>the editor found this one</b> means it wrote the question itself. The '
              f'word count is the one to watch: an FAQ answer is what a search engine lifts and shows on its own, '
              f'so it should be under {config.WRAP_FAQ_WORDS} words. <b>Check N figures from outside the '
              'article</b> is not a fault, it is a spot-check: the FAQ may answer past the article, so those '
              'figures came from the model rather than a sourced card.</p>'
            + "<h2>The H1 and the intro</h2>"
            + f'<div class="panel"><div class="row"><span class="t">H1</span><div><b>{E(wr.get("h1") or "—")}</b>'
              '</div></div>'
              f'<div class="row"><span class="t">intro</span><div>{E(wr.get("intro") or "—")}</div></div>'
              + (f'<div class="row"><span class="t">quick answer</span><div>'
                 f'{E(wr.get("quick_answer"))}</div></div>' if wr.get("quick_answer") else "")
              + '</div>'
            + f"<h2>The FAQ — {len(wr.get('faq') or [])} question(s)</h2>" + ("".join(faq) or
              '<div class="panel"><p class="q">No FAQ.</p></div>')
            + (f'<h2>Questions it dropped</h2><div class="panel"><ul class="kwlist">{dropped}</ul></div>'
               if dropped else "")
            + "<h2>The close</h2>"
            + (f'<p class="note">It sits under its own heading, written in the same call so the two '
               f'cannot drift: <b>{E(wr.get("close_heading"))}</b>. The one product link in the whole '
               f'article lives here.</p>' if wr.get("close_heading") else "")
            + f'<div class="panel"><p>{E(wr.get("close") or "—")}</p>'
            + (f'<div class="row"><span class="t">links to</span><div>{E(wr.get("cta_link"))}</div></div>'
               if wr.get("cta_link") else "")
            + "".join(f'<div class="row bad"><span class="t">flagged</span><div>{E(x)}</div></div>'
                      for x in (wr.get("cta_problems") or []))
            + '</div>'
            + f"<h2>Seam repairs it made — {len(rows)} section(s)</h2>"
            + ("".join(rows) or '<div class="panel"><p class="q">Nothing needed repairing.</p></div>')
            + (f'<h2>Touch-ups code refused</h2><p class="note">The wrapper asked for these and code '
               f'rejected them, usually for reaching outside the two seams it is allowed to touch.</p>'
               f'<div class="panel"><ul class="kwlist">{ignored}</ul></div>' if ignored else ""))
    out = config.artifact(slug, "wrapper-review.html")
    config.write_text(out, _page("The wrapper", f"{slug} — the intro, the FAQ and the close", body))
    return out


def build_coherence(slug):
    """writer/coherence-review.html — the only step that reads the whole article at once.

    This step was invisible: nothing in the repo rendered coherence-report.json, so an AI pass that
    rewrites sourced prose left no trace a reviewer could read.
    """
    cr = _work(slug, "writer", "coherence-report.json")
    if cr is None:
        raise FileNotFoundError(config.artifact(slug, "coherence-report.json"))
    import coherence as _coh          # for the word budget, so the page and the prompt agree
    inv = cr.get("inventory") or {}
    changes = cr.get("changes_claimed") or []
    warn = cr.get("warnings") or []

    ch = "".join(
        f'<details class="diff"><summary>{E(str(c.get("section"))[:95])} '
        f'<span class="chip no">{E(str(c.get("kind")))}</span></summary>'
        f'<div class="q"><b>What it did:</b> {E(str(c.get("what_you_did") or ""))}</div>'
        f'<div class="q"><b>Why:</b> {E(str(c.get("why") or ""))}</div></details>' for c in changes)

    dif = ""
    for d in cr.get("diff") or []:
        sim = d.get("similarity")
        edits = "".join(f'<li><del>{E(str(e.get("was") or ""))}</del> → <ins>{E(str(e.get("now") or ""))}</ins></li>'
                        for e in d.get("edits") or [])
        dif += (f'<details class="diff"><summary>{E(str(d.get("block"))[:95])} '
                f'<span class="chip">{(1 - (sim or 0)) * 100:.1f}% of the block rewritten</span></summary>'
                f'<ul class="kwlist">{edits}</ul></details>')

    wrows = "".join(
        f'<div class="row"><span class="t">{E(str(w.get("kind")))}</span><div>'
        f'{E(", ".join(str(x) for x in (w.get("detail") or [])))}'
        f'<div class="q">{E(str(w.get("note") or ""))}</div></div></div>' for w in warn)

    cnf = "".join(f'<li>{E(str(c))}</li>' for c in cr.get("could_not_fix") or [])
    gf = cr.get("guard_failures") or []
    applied = cr.get("applied")

    body = (_nav("Coherence")
            + reads_link("coherence")
            + _where("", 'Every earlier step looked at one section at a time. This one holds the whole '
                         'article at once, so it is the only step that can catch a fault living between '
                         'sections: a rule stated in section seven and broken in section five, or the same '
                         'thing scored out of five here and out of four there. It works in two passes. First '
                         'it lists every rule, scale and number in the article, without judging any of them. '
                         'Then a second pass gets that list and fixes four things: the article breaking its own '
                         'rule, advice its own warning covers, one thing scored on two different scales, and '
                         'two numbers that cannot both be true. It is the only step allowed to rewrite sourced '
                         'prose, which makes it the riskiest one here.')
            + _nums([("rules the article states", len(inv.get("rules") or [])),
                     ("scoring scales", len(inv.get("scales") or [])),
                     ("quantities", len(inv.get("quantities") or [])),
                     ("contradictions it fixed", len(changes)),
                     ("it could not fix", len(cr.get("could_not_fix") or [])),
                     ("code guard failures", len(gf)),
                     ("warnings raised", len(warn))])
            + '<p class="note"><b>How to read this.</b> The first three counts are what the article contained '
              'before anything changed. Below: its own verdict, then the flags, then every contradiction it '
              'fixed with its reason, then the exact words it rewrote, <del>red</del> removed and '
              '<ins>green</ins> added.</p>'
            + '<p class="note"><b>Read the flags first.</b> <b>Numbers changed</b> is normal when a rating '
              'scale was the fix, and a fact change when a statistic moved: check which. <b>Source tags lost</b> '
              'means a claim lost the citation behind it. <b>Length moved</b> means the article grew or shrank '
              f'more than {_coh.WORD_TOLERANCE}%, which is the budget the prompt gives it.</p>'
            # WHEN IT IS BLOCKED, SAY SO FIRST. A blocked run means the article you are reading is the
            # ORIGINAL and every fix below was thrown away — that is the single most important fact on
            # the page, and it used to sit at the bottom under "code guard failures".
            + ('<div class="panel"><p class="no"><b>NOTHING ON THIS PAGE WAS APPLIED.</b></p>'
               '<p>Code checked the rewrite and rejected it, so the article kept its original wording. '
               'Every fix listed below is one it <b>wanted</b> to make and did not.</p>'
               + "".join(f'<p class="no"><b>Why it was rejected:</b> {E(g)}</p>' for g in gf)
               + '<p class="q">This step has no sources and cannot look anything up, so a number in its '
                 'rewrite that appears nowhere in the original is one it invented. That is all-or-nothing '
                 'on purpose: one made-up figure throws away the whole edit, because there is no safe way '
                 'to keep the rest of a rewrite that contains a fabricated number.</p></div>'
               if not applied else "")
            + f'<div class="panel"><div class="row"><span class="t">changes applied</span>'
              f'<div class="{"ok" if applied else "no"}"><b>{"yes" if applied else "NO — the original published instead"}'
              f'</b></div></div>'
              f'<div class="row"><span class="t">its verdict</span><div>{E(str(cr.get("verdict") or "—"))}'
              "</div></div></div>"
            + (f'<h2>Warnings — {len(warn)}</h2><div class="panel">{wrows}</div>' if warn else "")
            + (f"<h2>The {len(changes)} fixes it wanted to make, and did not</h2>" if not applied
               else f"<h2>The contradictions it found — {len(changes)}</h2>")
            + (ch or '<div class="panel"><p class="q">It found no contradiction. On a long article that is '
                     'worth a second look: the first version of this step reported "internally consistent" on '
                     'articles that provably contradicted themselves.</p></div>')
            + (f"<h2>Exactly what it rewrote</h2>{dif}" if dif else "")
            + (f'<h2>Faults it could not fix</h2><div class="panel"><ul class="kwlist">{cnf}</ul></div>'
               if cnf else "")
            + (f'<h2>Why code rejected the whole rewrite</h2>'
               '<p class="note">These are the faults that discard an entire edit rather than being '
               'flagged: a heading or the H1 changed, a section deleted or emptied, a number invented, '
               'or more than a quarter of the source tags stripped. Any one of them and the original '
               'article publishes untouched.</p>'
               f'<div class="panel"><ul class="kwlist">'
               + "".join(f"<li>{E(str(g))}</li>" for g in gf) + "</ul></div>" if gf else ""))
    out = config.artifact(slug, "coherence-review.html")
    config.write_text(out, _page("Coherence", f"{slug} — does the article contradict itself?", body))
    return out


def build_readable(slug):
    """writer/readable-review.html — the rewrite, and every check code ran against it.

    This is the ONE step allowed to touch every sentence, so it is the one that could quietly undo
    the eighteen before it. The table is therefore the point of the page: each row names an earlier
    step and says whether its work survived. Nothing here blocks a run — it flags.
    """
    r = _work(slug, "writer", "readable-report.json")
    if r is None:
        raise FileNotFoundError(config.artifact(slug, "readable-report.json"))
    checks = r.get("checks") or []
    failed = [c for c in checks if not c.get("ok")]

    rows = "".join(
        f'<tr class="{"bad" if not c.get("ok") else ""}">'
        f'<td>{"&#10007;" if not c.get("ok") else "&#10003;"}</td>'
        f'<td><b>{E(c.get("check",""))}</b></td>'
        f'<td>{E(c.get("detail",""))}</td>'
        f'<td class="m">{E(c.get("protects",""))}</td></tr>' for c in checks)

    banner = ""
    if failed:
        banner = ('<div class="panel bad"><p class="q"><b>'
                  f'{len(failed)} check(s) failed.</b> The rewrite is still saved and still published '
                  'beside the original — nothing here stops a run. Read the failing rows first: each '
                  'one names the earlier step whose work did not survive.</p></div>')

    # MEASURED, NOT REPORTED (2026-08-26). This used to print the model's own list of edits, which
    # asked it to describe sentence swaps — and so nudged it into making sentence swaps instead of
    # deleting anything. The field is gone from the prompt. What replaces it is arithmetic over the
    # two files: a section that lost paragraphs did the job, one that kept them all only tightened
    # wording, and no self-report can fudge either number.
    def _blocks(w):
        return {(s.get("heading") or f"section {i}"): str(s.get("prose") or "")
                for i, s in enumerate(w.get("sections") or [], 1)}

    _A = _work(slug, "writer", "coherent.json") or {}
    _B = _work(slug, "writer", "readable.json") or {}
    _ba, _bb = _blocks(_A), _blocks(_B)
    _rows = []
    for _h, _before in _ba.items():
        _after = _bb.get(_h, "")
        _pa = len([x for x in re.split(r"\n\s*\n", _before) if x.strip()])
        _pb = len([x for x in re.split(r"\n\s*\n", _after) if x.strip()])
        _wa, _wb = len(_before.split()), len(_after.split())
        _pct = (_wb - _wa) / _wa * 100 if _wa else 0
        _cls = "bad" if (_pb >= _pa and _pct > -5) else ""
        _rows.append(f'<tr class="{_cls}"><td><b>{E(_h[:58])}</b></td>'
                     f'<td>{_wa:,} &rarr; {_wb:,}</td><td>{_pct:+.0f}%</td>'
                     f'<td>{_pa} &rarr; {_pb}</td></tr>')
    changes = (f'<table><thead><tr><th>Section</th><th>Words</th><th>Change</th>'
               f'<th>Paragraphs</th></tr></thead><tbody>{"".join(_rows)}</tbody></table>'
               if _rows else '<p class="q">Nothing to compare — the step has not run.</p>')
    body = (_nav("Readable")
            + reads_link("readable")
            + _where("", 'Every earlier step is either writing one section in isolation or guarding one property. '
                         'None of them can fix how the article READS, because none of them sees the finished piece '
                         'as a reader meets it. This step does, and changes only the wording: no fact, no link, no '
                         'source, no section. It is also the step that makes the article SHORTER — it is asked for '
                         'about a quarter off, because length is what makes a busy reader stop. Because it may touch every sentence, it is also the step most able to '
                         'undo the rest, so code checks the result against the original rather than trusting it. '
                         'The original draft is kept, so you can read both.')
            + _nums([("reading ease before", r.get("ease_before", 0)),
                     ("reading ease after", r.get("ease_after", 0)),
                     ("words before", f'{r.get("words_before", 0):,}'),
                     ("words after", f'{r.get("words_after", 0):,}'),
                     ("cut", (f'{(r["words_after"] - r["words_before"]) / r["words_before"] * 100:+.0f}%'
                              if r.get("words_before") else "—")),
                     ("checks clean", f'{len(checks) - len(failed)}/{len(checks)}')])
            + banner
            + "<h2>What to watch for</h2>"
            + '<p class="note">Reading ease is the standard plain-English score: 60 or more reads easily, '
              'under 50 is heavy going. A rewrite that raises it while every check stays green is the step '
              'working. A rewrite that raises it by <i>losing</i> a link, a figure or a source has cheated, '
              'and the table below is where that shows.</p>'
            + f"<h2>Every check</h2><table><thead><tr><th></th><th>Check</th><th>Result</th>"
              f"<th>What it protects</th></tr></thead><tbody>{rows}</tbody></table>"
            + '<h2>Where the cut actually happened</h2>'
              '<p class="note">Measured from the two files, not reported by the model. A section that '
              'came back with fewer paragraphs genuinely removed something. One that kept every '
              'paragraph and barely moved on words only tightened sentences, and is marked in pink — '
              'that is the failure this step kept having.</p>'
              + f'<div class="panel">{changes}</div>')
    out = config.artifact(slug, "readable-review.html")
    config.write_text(out, _page("Readable", f"{slug} — the readability rewrite, and what it kept", body))
    return out


def build_clean(slug):
    """writer/clean-review.html — the mechanical scrub. Pure code, so this is a count, not a judgment."""
    r = _work(slug, "writer", "clean-report.json")
    if r is None:
        raise FileNotFoundError(config.artifact(slug, "clean-report.json"))
    rules = "".join(f'<li><b>{v}x</b> {E(k)}</li>' for k, v in (r.get("by_rule") or {}).items())
    where = "".join(f'<div class="row"><span class="t">{E(f)[:44]}</span><div>'
                    + ", ".join(f"{v}x {E(k)}" for k, v in t.items()) + "</div></div>"
                    for f, t in (r.get("by_field") or {}).items())
    total = r.get("total_fixes", 0)
    body = (_nav("Clean")
            + reads_link("clean")
            + _where("", 'This is the last pass before the article is assembled, and it is pure code. It never reads meaning and never touches a word — it only fixes characters and spacing. Its real job is catching the characters that look like ordinary ones but are not, such as a non-breaking hyphen that looks exactly like a hyphen, which makes find-and-replace and exact matching fail silently later. Curly quotes and genuine maths symbols are left alone on purpose. There is no judgment here to overrule, so a high count is the step working rather than a problem.')
            + _nums([("characters fixed", total),
                     ("kinds of fix", len(r.get("by_rule") or {})),
                     ("places touched", len(r.get("by_field") or {}))])
            + "<h2>What to watch for</h2>"
            + '<p class="note">This step only ever touches characters and spacing, never a word, so nothing '
              'here can change meaning. It catches what the eye cannot: characters that <i>look</i> like normal '
              'ASCII but are not, so find-and-replace and exact-match quietly fail on them. Curly quotes and '
              'real maths symbols (≥, ≈, ×) are deliberately left alone. A high count is not a problem; it is '
              'the step doing its job.</p>'
            + (f'<h2>What it fixed</h2><div class="panel"><ul class="kwlist">{rules}</ul></div>'
               f'<h2>Where they were</h2><div class="panel">{where}</div>' if total else
               '<div class="panel"><p class="q">Nothing to fix — the text was already mechanically clean.</p>'
               "</div>"))
    out = config.artifact(slug, "clean-review.html")
    config.write_text(out, _page("The scrub", f"{slug} — the mechanical character clean-up", body))
    return out


# ---------------------------------------------------------------- 5. INDEX
#
# THE STEP MAP. Every step the write phase actually runs, in run order, mirroring the three
# orchestrators exactly: run_planner.STEPS, run_architect.STEPS, run_writer.STEPS. Kept here (not
# imported) so the front door renders even when a step module will not import, but it must be updated
# whenever a STEPS list changes — the build asserts the two agree, so a drift fails loudly.
#
#   (step name, what it does in one plain line, what it runs on, which review page shows its output)
#
# "runs on":  ai = an AI call decides something · paid = also spends DataForSEO credits · code = pure
# code, no AI, no cost. A reviewer reads this to know where a bad call could have come from.
#   (step name, ONE plain line, the longer description, what it runs on, its review page or None)
#
# The one-line version is what the map on every page shows. It must stay one short sentence: the map
# is the whole pipeline on one screen, and a second clause on any step breaks that.
STATIONS = [
    ("Planner", "planner",
     "Decides what is worth writing about, and refuses to carry a number it cannot prove.",
     [("gather", "Collects everything the research phase produced.",
       "Pulls everything the research phase produced into one file: the fact cards, the keywords, "
       "the questions real searchers ask, and what the top-ranking pages covered.", "ai", "Gather"),
      ("select", "Keeps the sub-topics that earn a place, and drops the rest.",
       "Judges every sub-topic against this article's angle. Keeps the ones that earn a place, "
       "drops the rest, and records a reason for every drop.", "ai", "Select"),
      ("verify-sources", "Opens the page behind every statistic to check the number is really there.",
       "Takes each claim carrying a citable statistic and opens the page it credits. If the "
       "page does not back it, searches for one that does. If nothing does, the claim is cut.",
       "paid", "Sources"),
      ("freeze", "Locks the plan so no later step can quietly change it.",
       "Checks the plan's shape and stamps it. After this the plan cannot change, so every later "
       "step is building on one fixed thing.", "code", None),
      ("plan-view", "Writes the locked plan out in plain English.",
       "Writes the frozen plan out as plain English, so you can read it without opening JSON.",
       "code", None)]),
    ("Architect", "architect",
     "Designs the article: what the sections are, what each one is for, and how long each gets.",
     [("shape", "Designs the sections and the order they come in.",
       "Designs the real section structure from the approved material, following the chosen format "
       "(how-to, comparison, listicle).", "ai", "Blueprint"),
      ("enrich", "Runs the extra research the structure asked for.",
       "Runs the extra research the structure asked for, and turns what comes back into new "
       "sourced cards.", "paid", "Blueprint"),
      ("brand-cards", "Turns the company's own research and results into facts the article can cite.",
       "Turns the company's own survey research and customer results into cards in the same shape as "
       "every other fact, each with its own source. They then compete for a place on merit, so the "
       "company's material lands where it genuinely belongs instead of being bolted on at the end.",
       "ai", "Blueprint"),
      ("allocate", "Gives every section a word budget.",
       "Gives every section a word target, judged by how much the section matters rather than by "
       "how many cards it happens to hold.", "ai", "Blueprint"),
      ("section-keywords", "Buys a real search keyword for the sections that deserve one.",
       "Decides which sections deserve a real search keyword, and buys the lookup only "
       "for those.", "paid", "Blueprint"),
      ("headings", "Writes the final wording of every heading, and the H1.",
       "Writes the final wording of every heading, then the H1.", "ai", "Blueprint")]),
    ("Writer", "writer",
     "Writes it, then repairs everything that only shows up once the words exist.",
     [("write-body", "Writes every section at once, none able to see the others.",
       "Writes each section into sourced prose. Every section is a separate AI call, run at "
       "the same time, so none of them can see the others.", "ai", "Body"),
      ("blend", "Reads the whole article and cuts what did not earn its place.",
       "Joins the separately-written sections into one piece, then edits it: repetition between "
       "sections, fluff, a section that never lands its job, over-long sentences and paragraphs. "
       "Code counts the countable faults first and hands it an exact list, so it judges rather "
       "than hunts. It also weaves the target keywords into sentences that already say the thing.",
       "ai", "Editor"),
      ("wrapper", "Writes the intro on PAS, the FAQ, and the close.",
       "Writes what sits around the article. The intro follows problem, agitate, solution, with the "
       "article's own answer as the third beat rather than the product. The FAQ takes real searched "
       "questions first and may go beyond what the article covers, since a question the article "
       "already answers is a wasted slot, but it may never use a number the article does not have. "
       "The close is the one place the company is named, and the only place a product link appears. "
       "It also writes the Quick answer: the whole article in 60 to 110 words, for the reader who reads nothing else.", "ai", "Wrapper"),
      ("coherence", "Reads the whole article at once and fixes what contradicts itself.",
       "The first step that reads the whole article at once. Catches the faults that live "
       "between sections, such as the same point made twice or a rule stated then contradicted.",
       "ai", "Coherence"),
      ("readable", "Rewrites the whole article so a person wants to read it.",
       "The article is accurate by here, and stiff: step 1 wrote each section on its own from a "
       "pile of facts, with no room to breathe. This one reads the whole piece and changes only "
       "the wording. Same facts, same source tags, same sections, checked in code rather than "
       "trusted. It runs before the three finishing steps so they polish this wording, and so the "
       "links land on the sentences a reader actually gets.",
       "ai", "Readable"),
      ("sentences", "Re-shapes the sentences so a reader gets through them.",
       "The article is readable by here and still hard work: its sentences carry two or three ideas each, joined by commas and \"and\". This step splits them, un-inverts them, and swaps the formal word for the one a person says out loud. It changes nothing else. The word count, every number, every source tag, every link, every heading and every table row are checked in code against the block it was given, and a block that fails twice keeps its original text.",
       "ai", "Sentences"),
      ("slop", "Strips the AI writing tells.",
       "Strips the AI writing tells, one block at a time, then checks in code that every number and "
       "every source tag survived the edit.", "ai", "Slop pass"),
      ("links", "Lays in the internal and external links.",
       "Lays in the internal links, the read-more pointers and the external links.", "ai", "Links"),
      ("clean", "Fixes odd characters and spacing. No AI.",
       "A mechanical scrub of characters and spacing. No AI, no judgment, no cost.", "code", "Clean"),
      ("assemble", "Builds the finished draft and the page you review it on.",
       "Stitches the parts into the finished draft, and into the page you can review.",
       "code", "Article")]),
]

# The review pages, in reading order. (label, path, the question it answers, what to watch for)
PAGES = [
    ("Gather", "gather/gather-review.html",
     "What did the research hand over, and what did we throw away before we started?",
     "A card that was dropped in vetting but that you would have wanted. The drop reasons are all listed."),
    ("Select", "planner/selection-review.html",
     "Which sub-topics earned a place in the article, and why did the rest die?",
     "A sub-topic dropped for being off-angle that actually belonged. Check the close calls first."),
    ("Sources", "planner/sources-review.html",
     "Does every citable statistic really appear on the page it credits?",
     "Whether the check completed. A low CUT count means nothing if the run ran out of search budget."),
    ("Blueprint", "architect/blueprint-review.html",
     "What is the article's one argument, and which sections carry it?",
     "A section with no clear job, or a word budget that does not match how much the section matters."),
    ("Body", "writer/body-review.html",
     "What did each section writer produce, before anyone repaired it?",
     "A section far under its word budget — it ran out of material and will read thin. And any section "
     "with no sourced cards, which is opinion rather than evidence."),
    ("Editor", "writer/editor-review.html",
     "What did the editor join, cut and leave alone, and did it own up to all of it?",
     "A section badged NOT DECLARED: the text changed and the editor never said so. An article with "
     "NO edits at all, which is a non-result, not a clean bill. Also check the skipped keywords, "
     "where it argues why a phrase had no honest home."),
    ("Wrapper", "writer/wrapper-review.html",
     "What surrounds the article — the intro, the FAQ and the close?",
     "An FAQ answer that draws on only one section: it restates that section rather than answering "
     "anything new. And any question invented by the editor rather than taken from real searches."),
    ("Coherence", "writer/coherence-review.html",
     "Does the article contradict itself, and what did the only whole-article pass rewrite?",
     "The warnings. 'Numbers changed' means a statistic was altered, which is only acceptable if the "
     "sentence carrying it was cut. Zero contradictions on a long article is itself suspicious."),
    ("Slop pass", "writer/slop-review.html",
     "Which AI writing tells were stripped out, and did every number survive it?",
     "A rewrite that lost a source tag or bent a sentence's meaning while removing a tell."),
    ("Links", "writer/links-review.html",
     "Which internal, read-more and external links were laid in, and why?",
     "A link that does not go where its sentence promises, and any section left with no way out."),
    ("Clean", "writer/clean-review.html",
     "What did the mechanical character scrub fix?",
     "Nothing, really. This step is pure code and cannot change meaning. A high count is it working."),
    # THE ARTICLE, CLEAN, FIRST (2026-08-13). writer/article.html is the REVIEW artifact: keyword
    # highlights, hover tooltips, a scoring panel. Anyone sent that link reads our SEO machinery
    # instead of the article. The clean read comes first now; the marked-up one stays underneath it
    # for when you actually want the machinery.
    ("The finished article", "writer/reads/assemble.html",
     "What would a reader actually get?",
     "Read it as a reader, start to finish. If it does not hold up here, no number on any other "
     "page matters."),
    ("The article at every step", "writer/reads/index.html",
     "How did it read after each step of the writer?",
     "The same piece at nine moments. Useful when a page tells you a step changed something and "
     "you want to see whether the change helped."),
    ("Article, marked up", "writer/article.html",
     "Where did each statistic come from, and where did the keywords land?",
     "Any statistic you cannot trace back to a source, and any section that reads thinner than its budget."),
    # THE STEP MAP LOOKS PAGES UP BY LABEL (2026-08-21). Two steps named a page the registry did not
    # carry — assemble pointed at "Article" and readable at "Readable" — so both rendered as plain
    # grey text with no link, and the finished article was unreachable from the front door for weeks.
    # These two rows are what make those steps clickable; the label must match STATIONS exactly.
    ("Readable", "writer/readable-review.html",
     "Did the rewrite make it readable without breaking anything?",
     "The check table. A rising reading-ease score with every check green is the step working; a "
     "rising score next to a lost link or a dropped figure is the step cheating."),
    ("Sentences", "writer/sentence-review.html",
     "Did the sentences get shorter without anything going missing?",
     "The before-and-after, block by block. A falling average sentence length with the word count held is the step working; any block marked REJECTED is one it could not do safely, so it kept the original."),
    ("Article", "writer/article.html",
     "Where did each statistic come from, and where did the keywords land?",
     "The same marked-up page as above — assemble is the step that builds it."),
]

EXTRA_PAGES = [
    ("Time and API usage", "time-and-usage.html",
     "how long each step took and what it cost, in tokens and DataForSEO credits"),
    ("How the whole write phase works", "../../review/write-phase-review.html",
     "the walkthrough of every step and every prompt, written for someone outside the team. Not about this "
     "article specifically — it explains the machine that built it."),
]

# THE SENT VERSION. The article with all the review machinery stripped out: no keyword highlights, no
# hover tooltips, no scoring panel. This is the file that actually goes to the client, and it was the
# one thing a run produced that the front door never linked. {SLUG} is filled in per article.
SENT_FILES = [
    ("The article, exactly as we sent it", "share/{SLUG}.html",
     "The clean reading version. Same words as the draft, laid out as it would publish, with citations as "
     "small numbered links. This is the page the client opens."),
    # ADDED 2026-08-13. Every step page shows what CHANGED. None of them showed the article, so you
    # could read that blend cut a repetition and still not know how the piece read afterwards.
    ("The article after every single step", "writer/reads/index.html",
     "The same piece read at nine moments: after the sections are written, after they are joined and cut, "
     "after the intro, close and FAQ are added, after the whole thing is rewritten to be read, and so on "
     "to the finished draft. Laid out exactly like the page above, so you can watch it change without "
     "reading a single diff."),
    ("The same article as markdown", "share/{SLUG}.md",
     "The plain-text version of that page, for pasting into a CMS or a doc."),
    ("The index of every sent article", "share/index.html",
     "The contents page that sits in front of them when several articles go over together."),
]

# The raw output. Each line says what the file IS and, more importantly, WHY you would open it — a name
# alone ("the frozen plan") tells a newcomer nothing.
RAW_FILES = [
    ("The draft", "writer/draft.md",
     "The finished article as plain markdown, straight out of the writer. Open it to read the words with "
     "nothing else on the page."),
    ("The blueprint, in plain text", "architect/structure.md",
     "Every section with its job, its sub-topics and its word target. Open it to check the article was "
     "designed sensibly before worrying about how it was written."),
    ("The frozen plan", "planner/article-plan.md",
     "The list of sub-topics the Planner approved, with the evidence attached to each, frozen before the "
     "Architect was allowed to touch it. \"Frozen\" means no later step can add to it or change it. Open it "
     "to settle one question: did a fact go missing because it was never approved, or because a later step "
     "lost it?"),
]


def _published_url():
    """The public base URL of the share site, or "" if it was never published.

    Derived from the push clone's git remote (share/_pages-repo) rather than hardcoded, so a repo
    renamed or re-created keeps the front door honest. Reads .git/config directly: this is a view
    builder and must never shell out or touch the network.
    """
    cfg = os.path.join(config.WRITE_OUT, "..", "share", "_pages-repo", ".git", "config")
    try:
        with open(os.path.abspath(cfg)) as f:
            m = re.search(r"url\s*=\s*https://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?\s*$",
                          f.read(), re.M)
    except OSError:
        return ""
    return f"https://{m.group(1).lower()}.github.io/{m.group(2)}/" if m else ""


def _assert_steps_match():
    """The STATIONS map above must name the same steps, in the same order, as the orchestrators run.
    Drift here would make the front door describe a pipeline that no longer exists, so it is an error,
    not a warning. Skipped silently if an orchestrator cannot be imported (a step module may be mid-edit)."""
    try:
        import run_planner, run_architect, run_writer
    except Exception:
        return
    real = {"Planner": [n for n, _ in run_planner.STEPS],
            "Architect": [n for n, _ in run_architect.STEPS],
            "Writer": [n for n, _ in run_writer.STEPS]}
    for name, _engine, _does, steps in STATIONS:
        mine = [s[0] for s in steps]
        if mine != real[name]:
            raise AssertionError(f"eval_pages.STATIONS['{name}'] = {mine} but the orchestrator runs "
                                 f"{real[name]} — update STATIONS to match")


def build_index(slug):
    """The front door: out/<slug>/index.html.

    Deliberately thin. The MAP at the top of this (and every other) page already lists all three
    stations, every step in run order, one line each, linked to the page that shows it — so the front
    door does not repeat that as a second list. It had two lists saying the same thing in different
    words, which is what made it hard to read. What is left here is only what the map cannot carry:
    the finished article the client received, and the raw files behind it.
    """
    _assert_steps_match()
    root = config.out_dir(slug)
    live = lambda h: os.path.exists(os.path.join(root, h))
    ctx = article_ctx.article_context(slug)
    title = (ctx.get("title") or "").strip()
    total = sum(len(st[3]) for st in STATIONS)

    def file_rows(items):
        return "".join(
            f'<div class="row"><div class="t">'
            + (f'<a href="{h}" target="_blank">{E(nm)}</a>' if live(h)
               else f'{E(nm)} <span class="chip">not built yet</span>')
            + f'</div><div class="m">{E(d)}</div></div>'
            for nm, h, d in ((n, p_.replace("{SLUG}", slug), t) for n, p_, t in items))

    pub = _published_url()
    pub_row = (f'<div class="row"><div class="t"><a href="{pub}{slug}.html" target="_blank">'
               f'The live link the client actually opened</a></div>'
               f'<div class="m">The same page, published on the web: {E(pub)}{E(slug)}.html</div></div>'
               if pub else "")

    key = ('<div class="key"><span><span class="b ai">AI decides</span> a model made the call</span>'
           '<span><span class="b paid">AI + paid data</span> also spends DataForSEO credits</span>'
           '<span><span class="b code">code only</span> no AI, no cost, no judgment</span></div>')

    body = (
        _nav("", base="")
        + (f'<p class="lede">{E(title)}</p>' if title else "")
        + '<p class="lead">The research phase handed this article a pile of facts. The write phase turns '
          f'that pile into a finished article in <b>{total} steps</b>, across the three stations above. '
          'Click any step to see exactly what it did — each opens in a new tab, so this map stays put.</p>'
        + key
        + '<h2>What the client actually receives</h2>'
        + '<p class="lead">Every step page shows our working. These are the finished thing with all of it '
          'stripped out: no keyword highlights, no hover tooltips, no scoring panel.</p>'
        + '<div class="panel">' + file_rows(SENT_FILES) + pub_row + "</div>"
        + '<h2>Also on file</h2><div class="panel">' + file_rows(EXTRA_PAGES) + "</div>"
        + '<h2>The raw output, if you would rather read it plain</h2>'
        + '<div class="panel">' + file_rows(RAW_FILES) + "</div>")
    out = os.path.join(root, "index.html")
    config.write_text(out, _page("This article, end to end", f"{slug} — start here", body))
    return out


def _build_reads(slug):
    """The clean read of the article at every writer step. Imported here rather than at the top so
    build_stage_reads can import eval_pages for its own helpers without a circular import."""
    import build_stage_reads
    return build_stage_reads.build(slug)


BUILDERS = [("gather", build_gather), ("selection", build_selection),
            ("sources", build_sources), ("blueprint", build_blueprint),
            ("body", build_body), ("editor", build_editor), ("wrapper", build_wrapper_page),
            ("coherence", build_coherence), ("clean", build_clean),
            ("readable", build_readable),
            ("reads", _build_reads),
            ("index", build_index)]


def build_all(slug):
    outs = []
    for name, fn in BUILDERS:
        try:
            outs.append(fn(slug))
            print(f"  {name:<10} -> {outs[-1]}")
        except FileNotFoundError as e:
            print(f"  {name:<10} skipped — missing input: {e.filename}")
    return outs


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build the per-engine eval pages from a run's saved files.")
    ap.add_argument("--slug")
    ap.add_argument("--all", action="store_true", help="every article that has outputs")
    a = ap.parse_args()
    if a.all:
        root = config.WRITE_OUT
        for slug in sorted(os.listdir(root)):
            if os.path.isfile(os.path.join(root, slug, "gather", "plan-inputs.json")):
                print(f"== {slug} ==")
                build_all(slug)
    elif a.slug:
        build_all(a.slug)
    else:
        ap.error("pass --slug <slug> or --all")
