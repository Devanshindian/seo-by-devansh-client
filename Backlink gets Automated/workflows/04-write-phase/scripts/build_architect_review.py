#!/usr/bin/env python3
"""Build the ARCHITECT REVIEW SITE — a public, plain-English walkthrough of the architect for a
non-technical marketing reader: what it does, every prompt it runs (verbatim, with its fill-ins
explained), and the finished blueprint of every article, down to the individual fact cards.

Reads:  workflows/04-write-phase/prompts/*.md            (the prompt text, verbatim, never copied)
        scripts/architect_review_copy.py                 (the plain-English copy)
        projects/<company>/04-write-phase/out/<slug>/architect/structure.json
                                                         + enriched-cards.json + _work/*.json
        projects/<company>/04-write-phase/out/<slug>/gather/plan-inputs.json   (the card text)
Writes: projects/<company>/04-write-phase/architect-review/
          index.html            the explainer: what the architect is, the five steps, the fill-ins
          prompts.html          all 18 prompts, each with what it asks for + its fill-ins + full text
          article-<slug>.html   one per finished article: the blueprint, every section, every card

  python3 build_architect_review.py            # build everything
"""
import argparse
import glob
import html
import json
import os
import re
from urllib.parse import urlparse

import config
import architect_review_copy as copy

CSS = """
:root{
  --ink:#1c1a17; --muted:#6b6459; --line:#efe7d8;
  --paper:#ffffff; --cream:#fffdf8; --wash:#fff8ec;
  --yellow:#ffb703; --yellow-soft:#ffe9ad; --orange:#fb7a00; --orange-soft:#ffd9b0;
  --green:#e8f5ec; --green-line:#cfe8d5; --green-ink:#2e7d43;
  --red:#fdf3f0; --red-line:#f6d9cf; --red-ink:#c2603a;
  --blue:#eef4fb; --blue-line:#d3e2f2; --blue-ink:#2f6fb0;
  --shadow:0 1px 2px rgba(28,26,23,.04), 0 8px 24px rgba(28,26,23,.05);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;
  line-height:1.62;font-size:16.5px;-webkit-font-smoothing:antialiased}
a{color:#b25a00}
.wrap{max-width:1000px;margin:0 auto;padding:0 24px}

header{background:linear-gradient(180deg,var(--wash),var(--paper));border-bottom:1px solid var(--line);padding:56px 0 40px}
.kicker{display:inline-block;font-size:12.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:#b25a00;background:var(--paper);border:1px solid var(--orange-soft);padding:5px 12px;border-radius:100px;margin-bottom:18px}
h1{font-size:clamp(28px,5vw,44px);line-height:1.12;margin:0 0 14px;letter-spacing:-.02em}
h1 .hl{background:linear-gradient(180deg,transparent 62%,var(--yellow-soft) 62%);padding:0 2px}
.lede{font-size:19px;color:var(--muted);max-width:760px;margin:0}
.back{display:inline-block;font-size:13.5px;font-weight:600;margin-bottom:14px;text-decoration:none}

nav{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.93);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
nav .wrap{display:flex;gap:4px;flex-wrap:wrap;padding-top:11px;padding-bottom:11px}
nav a{font-size:13px;font-weight:600;color:var(--muted);text-decoration:none;padding:6px 11px;border-radius:100px}
nav a:hover{color:var(--ink);background:var(--wash)}

section{padding:50px 0;border-bottom:1px solid var(--line)}
section:last-of-type{border-bottom:none}
h2{font-size:27px;letter-spacing:-.01em;margin:0 0 6px}
h2 .num{color:#b25a00;font-variant-numeric:tabular-nums;margin-right:10px}
.sub{color:var(--muted);margin:0 0 24px;font-size:17px;max-width:760px}
h3{font-size:18px;margin:22px 0 8px}
p{margin:0 0 14px}
.muted{color:var(--muted)}
ul,ol{margin:0 0 14px;padding-left:20px}li{margin:4px 0}

.note{background:var(--cream);border:1px solid var(--line);border-left:4px solid var(--yellow);border-radius:12px;
  padding:16px 18px;margin:20px 0;font-size:15.5px}
.note.orange{border-left-color:var(--orange);background:var(--wash)}
.note.red{border-left-color:var(--red-ink);background:var(--red)}
.tag{font-size:11.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#b25a00;display:block;margin-bottom:4px}
.tag.r{color:var(--red-ink)}

.grid{display:grid;gap:14px;margin:18px 0}
.grid.two{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.grid.three{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.card{background:var(--cream);border:1px solid var(--line);border-radius:14px;padding:18px 18px 14px;box-shadow:var(--shadow)}
.card h4{margin:0 0 6px;font-size:16.5px}
.card p{margin:0;font-size:15px;color:var(--muted)}
.ic{font-size:22px;display:block;margin-bottom:6px}

.define{border:1px dashed var(--orange-soft);border-radius:12px;padding:12px 16px;margin:10px 0;background:var(--cream);font-size:15.5px}
.define b{color:#b25a00}

.flow{display:flex;flex-direction:column;margin-top:10px}
.step{display:flex;gap:18px;align-items:flex-start;position:relative;padding:14px 0}
.step:not(:last-child)::after{content:"";position:absolute;left:23px;top:56px;bottom:-14px;width:2px;
  background:linear-gradient(var(--yellow),var(--orange-soft))}
.dot{flex:none;width:48px;height:48px;border-radius:14px;display:grid;place-items:center;font-weight:800;font-size:18px;
  background:var(--yellow-soft);border:2px solid var(--yellow);box-shadow:var(--shadow);line-height:1}
.step-body{min-width:0}
.step-body h3{margin:4px 0 6px}
.step-body p{margin:0 0 8px;color:var(--muted);font-size:15.5px}

.pill{display:inline-block;font-size:12px;font-weight:600;color:#b25a00;background:var(--wash);
  border:1px solid var(--orange-soft);padding:2px 9px;border-radius:100px;margin:0 6px 4px 0}
.pill.g{color:var(--green-ink);background:var(--green);border-color:var(--green-line)}
.pill.b{color:var(--blue-ink);background:var(--blue);border-color:var(--blue-line)}
.pill.r{color:var(--red-ink);background:var(--red);border-color:var(--red-line)}
.pill.n{color:var(--muted);background:#faf7f1;border-color:var(--line)}

table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14.5px}
th,td{text-align:left;padding:9px 11px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);background:var(--cream)}
td code,.tok{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;color:#b25a00;
  background:var(--wash);border:1px solid var(--orange-soft);border-radius:5px;padding:1px 5px;white-space:nowrap}
.tablewrap{overflow-x:auto}

pre.prompt{background:#fffdf8;border:1px solid var(--line);border-radius:12px;padding:18px 20px;overflow-x:auto;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13.2px;line-height:1.62;white-space:pre-wrap;
  word-wrap:break-word;margin:12px 0 0}
pre.prompt .tok{white-space:normal}
details{border:1px solid var(--line);border-radius:12px;background:var(--paper);margin:14px 0;padding:0}
details[open]{background:var(--cream)}
summary{cursor:pointer;padding:12px 16px;font-weight:600;font-size:15px;list-style:none;color:#b25a00}
summary::-webkit-details-marker{display:none}
summary::before{content:"+ ";font-weight:700}
details[open] summary::before{content:"\2013 ";font-weight:700}
details .inner{padding:0 16px 16px}

.pcard{border:1px solid var(--line);border-radius:16px;padding:22px 22px 18px;margin:20px 0;background:var(--paper);
  box-shadow:var(--shadow)}
.pcard>h3{margin-top:0;font-size:20px}
.pfile{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;color:var(--muted);
  background:#faf7f1;border:1px solid var(--line);border-radius:6px;padding:2px 7px}

.sec{border:1px solid var(--line);border-radius:16px;margin:18px 0;background:var(--paper);box-shadow:var(--shadow);overflow:hidden}
.sec-head{padding:20px 22px 16px;background:var(--cream);border-bottom:1px solid var(--line)}
.sec-head h3{margin:0 0 8px;font-size:21px;line-height:1.3}
.sec-n{color:#b25a00;font-variant-numeric:tabular-nums;margin-right:8px}
.job{font-size:15px;color:var(--muted);margin:8px 0 0}
.job b{color:var(--ink);font-weight:600}
.sec-body{padding:6px 22px 18px}
.grp{margin:16px 0 0}
.grp-h{font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#b25a00;margin:18px 0 8px}
.grp-h.sub3{text-transform:none;letter-spacing:0;font-size:16.5px;color:var(--ink)}
.crd{border-left:3px solid var(--yellow-soft);padding:4px 0 4px 14px;margin:12px 0}
.crd-n{font-size:11.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.crd-g{margin:2px 0 5px;font-size:15.5px}
.crd-src{font-size:13px;color:var(--muted)}
.crd details{margin:8px 0 0;border-radius:10px}
.crd summary{padding:8px 12px;font-size:13.5px}
.crd .inner{padding:0 12px 12px;font-size:14.5px;color:var(--muted);white-space:pre-wrap}

footer{padding:36px 0 60px;color:var(--muted);font-size:14px}
@media(max-width:640px){.sec-head,.sec-body{padding-left:16px;padding-right:16px}}
"""


def _page(title, body, description=""):
    return (f"<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{html.escape(title)}</title>"
            f"<meta name=\"description\" content=\"{html.escape(description)}\">"
            f"<style>{CSS}</style></head><body>\n{body}\n</body></html>\n")


def _e(s):
    return html.escape(str(s or ""))


def _tokens(text):
    """Escape prompt text, then wrap every {{FILL_IN}} in a chip so the reader can see them at a glance."""
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", r'<span class="tok">{{\1}}</span>', html.escape(text))


def _domain(url):
    try:
        return (urlparse(url).netloc or url).replace("www.", "")
    except Exception:
        return url


# --------------------------------------------------------------------------- data
def _slugs():
    out = []
    for p in sorted(glob.glob(os.path.join(config.WRITE_OUT, "*", "architect", "structure.json"))):
        out.append(os.path.basename(os.path.dirname(os.path.dirname(p))))
    return out


def _load(slug):
    d = os.path.join(config.WRITE_OUT, slug)
    st = json.load(open(os.path.join(d, "architect", "structure.json")))
    cards = {}
    pi = os.path.join(d, "gather", "plan-inputs.json")
    if os.path.exists(pi):
        inp = json.load(open(pi))
        for s in inp.get("group_b", {}).get("sections_menu", []):
            for c in s.get("evidence", []):
                cards[str(c.get("card_id"))] = c
            for h in s.get("h3", []):
                for c in h.get("evidence", []):
                    cards[str(c.get("card_id"))] = c
    ep = os.path.join(d, "architect", "enriched-cards.json")
    if os.path.exists(ep):
        for cid, c in json.load(open(ep)).items():
            cards[str(cid)] = c
    work = os.path.join(d, "architect", "_work")

    def _w(name):
        p = os.path.join(work, name)
        return json.load(open(p)) if os.path.exists(p) else {}

    return st, cards, _w("heading-map.json"), _w("section-keywords.json")


# --------------------------------------------------------------------------- index
def build_index(slugs, meta):
    steps_html = []
    for s in copy.STEPS:
        body = "".join(f"<p>{_e(x)}</p>" for x in s["detail"])
        steps_html.append(
            f'<div class="step"><div class="dot">{s["n"]}</div><div class="step-body">'
            f'<h3>{_e(s["name"])} <span class="pill n">{_e(s["one_line"])}</span></h3>'
            f'{body}<p><b>What comes out:</b> {_e(s["produces"])}</p></div></div>')

    fills = "".join(f"<tr><td><span class=\"tok\">{_e(t)}</span></td><td>{_e(m)}</td><td>{_e(src)}</td></tr>"
                    for t, m, src in copy.COMMON_FILLS)

    arts = []
    for slug in slugs:
        m = meta[slug]
        arts.append(
            f'<div class="card"><h4><a href="article-{_e(slug)}.html">{_e(m["h1"])}</a></h4>'
            f'<p><span class="pill">{_e(m["format"])}</span>'
            f'<span class="pill n">{m["n_sections"]} sections</span>'
            f'<span class="pill n">{m["n_cards"]} fact cards</span></p></div>')

    body = f"""
<header><div class="wrap">
  <span class="kicker">Testlify content engine &middot; the write phase</span>
  <h1>The <span class="hl">Architect</span></h1>
  <p class="lede">The step between the research and the writing. It takes a pile of researched facts and a
  rough outline, and turns them into the blueprint an article gets written from: the sections, their order,
  what each one has to do, which facts go in it, how long it runs, and the exact wording of every heading.
  Nothing here writes a sentence of the article. It is all planning.</p>
</div></header>

<nav><div class="wrap">
  <a href="#idea">The one idea</a>
  <a href="#words">The words you need</a>
  <a href="#steps">The five steps</a>
  <a href="#fills">How the prompts get filled in</a>
  <a href="prompts.html">All 18 prompts &rarr;</a>
  <a href="#articles">The finished blueprints &rarr;</a>
</div></nav>

<div class="wrap">

<section id="idea">
  <h2><span class="num">01</span>The one idea</h2>
  <p class="sub">Three things happen in order, and the architect is the middle one.</p>
  <div class="grid three">
    <div class="card"><span class="ic">&#128269;</span><h4>Research, before</h4>
      <p>Already done. It hands over a pile of facts, each one a card with its source, plus a rough outline
      and a main search keyword.</p></div>
    <div class="card"><span class="ic">&#128208;</span><h4>The architect, here</h4>
      <p>Turns that pile into a blueprint. Which sections exist, in what order, what each has to deliver,
      which facts sit in it, how many words it gets, and what its heading says.</p></div>
    <div class="card"><span class="ic">&#9997;</span><h4>The writer, after</h4>
      <p>Takes the blueprint one section at a time and writes the prose. It can only use the facts the
      architect placed in front of it.</p></div>
  </div>
  <div class="note orange"><span class="tag">The rule that governs everything</span>
  A card can be well evidenced, well written and genuinely interesting, and still belong to a different
  field or be written for the wrong person. Advice for the candidate in an article for the recruiter. The
  clinical use of a word we use commercially. The architect is the last step that can catch one of those,
  because after it, a section gets written. So almost every prompt on this site carries two lines saying
  what the article <b>is</b> about and what it is <b>not</b> about, and the AI is told to read them before
  it places anything.</div>
</section>

<section id="words">
  <h2><span class="num">02</span>The words you need first</h2>
  <p class="sub">Six terms that turn up on every page here. Each one is defined once.</p>
  <div class="define"><b>Card</b>: one fact, written down with its source. A card holds a one-line
  summary (so it can be scanned) and the full passage it came from (so the writer can use it). If it is not
  written inside a card, the writer never sees it.</div>
  <div class="define"><b>Box</b>: a small group of cards on one narrow sub-topic, numbered #1, #2, #3.
  The architect is handed the material as numbered boxes so it can design by answering with numbers instead
  of retyping the research.</div>
  <div class="define"><b>The spine</b>: one paragraph saying what the whole article argues, who it is
  for, and what the reader can do at the end. Written by the architect in step 1, then carried into every
  later decision as the thing each section has to serve.</div>
  <div class="define"><b>The job</b>: what one section has to deliver, written before its heading is
  written. A heading is a label and can be vague; the job is what the section actually owes the reader.</div>
  <div class="define"><b>The angle</b>: the one thing this article is built to deliver that the pages
  already ranking for the subject do not. Decided when the topic was chosen, long before this.</div>
  <div class="define"><b>Fill-ins</b>: the words in double curly brackets inside a prompt, like
  <span class="tok">{{{{TITLE}}}}</span>. They are blanks. Before the prompt is sent, real values are pasted
  in. Section 04 below explains where each one comes from.</div>
</section>

<section id="steps">
  <h2><span class="num">03</span>The five steps</h2>
  <p class="sub">One command runs all five, in order. Each one writes a file the next one reads, so a run can
  stop halfway and pick up where it left off.</p>
  <div class="flow">{''.join(steps_html)}</div>
</section>

<section id="fills">
  <h2><span class="num">04</span>How the prompts get filled in</h2>
  <p class="sub">Every prompt is a template with blanks in it. This is the part worth understanding before
  you read them.</p>
  <p>A prompt file on the next page is not what the AI receives. It is the shape of what the AI receives.
  Anywhere you see double curly brackets, a real value gets pasted in first. So this line in the file:</p>
  <pre class="prompt">THE ARTICLE (what we are building):
- Asset title: {{{{TITLE}}}}
- Distinct angle (what this article is built to deliver): {{{{ANGLE}}}}</pre>
  <p>arrives at the AI looking like this:</p>
  <pre class="prompt">THE ARTICLE (what we are building):
- Asset title: The Real Cost of Recruitment in 2026
- Distinct angle (what this article is built to deliver): the fully-loaded cost of a hire,
  including the internal time nobody bills for</pre>
  <p>That matters for two reasons. It is why the same prompt file works for any company and any article. And
  it is why a mistake in a fill-in is invisible in the prompt itself: the wording can be perfect and the
  value pasted in can still be the wrong thing.</p>
  <h3>The fill-ins that appear again and again</h3>
  <div class="tablewrap"><table>
    <tr><th>Fill-in</th><th>What it is</th><th>Where the value comes from</th></tr>
    {fills}
  </table></div>
  <div class="note"><span class="tag">Worth knowing</span>
  Numbers like <span class="tok">{{{{WORDS_PER_SECTION}}}}</span> are settings, not AI decisions. They live
  in one settings file and get pasted into the prompt so the instruction and the code can never drift apart.
  A section is 300 words, a sentence is 25 words, a paragraph is 4 sentences. Change the setting and every
  prompt that mentions it changes with it.</div>
  <p><a href="prompts.html"><b>Read all 18 prompts &rarr;</b></a></p>
</section>

<section id="articles">
  <h2><span class="num">05</span>The finished blueprints</h2>
  <p class="sub">Four articles have been through the rebuilt architect. Each page below shows the whole
  blueprint: the spine, every section with its job, its word target and its keyword, and every single fact
  card sitting underneath it.</p>
  <div class="grid two">{''.join(arts)}</div>
</section>

</div>
<footer><div class="wrap">The Architect &middot; the write phase of the Testlify content engine &middot;
design the sections &rarr; research the gaps &rarr; set the lengths &rarr; find the keywords &rarr;
write the headings</div></footer>
"""
    return _page("The Architect", body,
                 "A plain-English walkthrough of the architect: what it does, every prompt it runs, and the "
                 "finished blueprint of every article.")


# --------------------------------------------------------------------------- prompts
def build_prompts():
    by_step = {}
    for p in copy.PROMPTS:
        by_step.setdefault(p["step"], []).append(p)

    out = []
    for s in copy.STEPS:
        items = by_step.get(s["n"]) or []
        if not items:
            continue
        cards = []
        for p in items:
            text = open(os.path.join(config.PROMPTS, p["file"])).read().rstrip()
            words = len(text.split())
            fills = []
            for token, meaning in p["fills"]:
                if meaning == "common":
                    meaning = next((m for t, m, _ in copy.COMMON_FILLS if t.startswith(token)), "See the table on the front page.")
                tok = (f'<span class="tok">{_e(token)}</span>' if token.startswith("{{")
                       else f'<i>{_e(token)}</i>')
                fills.append(f"<tr><td>{tok}</td><td>{_e(meaning)}</td></tr>")
            what = "".join(f"<li>{_e(x)}</li>" for x in p["what"])
            cards.append(f"""
<div class="pcard" id="{_e(p['file'].replace('.md', ''))}">
  <h3>{_e(p['title'])}</h3>
  <p><span class="pfile">{_e(p['file'])}</span> <span class="pill n">{_e(p['when'])}</span></p>
  <h4 style="margin:16px 0 6px;font-size:15px">What it is asking for</h4>
  <ul>{what}</ul>
  <h4 style="margin:18px 0 6px;font-size:15px">The blanks that get filled in</h4>
  <div class="tablewrap"><table><tr><th style="width:34%">Fill-in</th><th>What gets pasted in</th></tr>
  {''.join(fills)}</table></div>
  <details><summary>Read the full prompt, exactly as the AI receives it ({words:,} words)</summary>
  <div class="inner"><pre class="prompt">{_tokens(text)}</pre></div></details>
</div>""")
        out.append(f'<section id="step{s["n"]}"><h2><span class="num">0{s["n"]}</span>Step {s["n"]}: '
                   f'{_e(s["name"])}</h2><p class="sub">{_e(s["one_line"])}</p>{"".join(cards)}</section>')

    nav = "".join(f'<a href="#step{s["n"]}">{s["n"]}. {_e(s["name"])}</a>' for s in copy.STEPS)
    body = f"""
<header><div class="wrap">
  <a class="back" href="index.html">&larr; Back to the architect</a>
  <span class="kicker">Every AI call the architect makes</span>
  <h1>The <span class="hl">prompts</span>, in full</h1>
  <p class="lede">Eighteen prompts, in the order they run. Each one shows what it is being asked to decide,
  which blanks get filled in before it is sent, and then the complete text, word for word. The chips like
  <span class="tok">{{{{ANGLE}}}}</span> inside a prompt are the blanks.</p>
</div></header>
<nav><div class="wrap"><a href="index.html">Overview</a>{nav}</div></nav>
<div class="wrap">{''.join(out)}</div>
<footer><div class="wrap">Prompt text is read straight from the engine, so this page is never out of date
with what actually runs.</div></footer>
"""
    return _page("The Architect: every prompt", body,
                 "All 18 prompts the architect runs, verbatim, with every fill-in explained.")


# --------------------------------------------------------------------------- one article
def _card_html(n, cid, cards):
    c = cards.get(str(cid)) or {}
    gloss = (c.get("gloss") or "").strip()
    full = (c.get("verbatim") or "").strip()
    if not gloss and not full:
        return ""
    srcs = c.get("source_urls") or []
    src = ""
    if srcs:
        src = ('<div class="crd-src">Source: ' +
               " &middot; ".join(f'<a href="{_e(u)}" target="_blank" rel="noopener">{_e(_domain(u))}</a>'
                                 for u in srcs[:3]) + "</div>")
    found = ""
    try:
        if int(cid) >= 9001:
            found = '<span class="pill g">found by the architect</span>'
    except (TypeError, ValueError):
        pass
    more = ""
    if full and full != gloss:
        more = (f'<details><summary>The whole card, as the writer sees it</summary>'
                f'<div class="inner">{_e(full)}</div></details>')
    return (f'<div class="crd"><div class="crd-n">Card {n} {found}</div>'
            f'<div class="crd-g">{_e(gloss or full[:220])}</div>{src}{more}</div>')


def build_article(slug):
    st, cards, hmap, skw = _load(slug)
    secs = st.get("sections") or []
    wb = st.get("word_budget") or {}
    kw = st.get("keywords") or {}
    was_by_n = {h["n"]: h for h in (hmap.get("headings") or [])}
    picks = {}
    for r in (skw.get("sections") or []):
        if r.get("pick"):
            picks[r["n"]] = r["pick"]

    n_cards = 0
    blocks = []
    for i, s in enumerate(secs, 1):
        rec = was_by_n.get(i) or {}
        pills = []
        if s.get("word_target"):
            pills.append(f'<span class="pill n">about {s["word_target"]} words</span>')
        if s.get("is_item"):
            pills.append('<span class="pill b">one of the list items</span>')
        # the researched keyword and the keyword the heading actually ended up carrying are two
        # different things: a well-researched phrase that does not fit is allowed to be dropped.
        p = picks.get(i)
        used = (rec.get("keyword_used") or "").strip()
        if used:
            vol = f' &middot; {p["volume"]}/mo &middot; difficulty {p["kd"]}' if p and p["keyword"] == used else ""
            pills.append(f'<span class="pill">targets: {_e(used)}{vol}</span>')
        if p and p["keyword"] != used:
            pills.append(f'<span class="pill n">researched &ldquo;{_e(p["keyword"])}&rdquo; '
                         f'({p.get("volume", "?")}/mo), not used in the heading</span>')
        if s.get("table"):
            pills.append(f'<span class="pill">renders a table: {_e(" | ".join(s["table"]["columns"]))}</span>')
        if s.get("list"):
            pills.append(f'<span class="pill">renders a {_e(s["list"]["kind"])} list</span>')

        was = ""
        if rec.get("was") and rec["was"] != s["headline"]:
            was = (f'<p class="job"><b>The draft heading was:</b> &ldquo;{_e(rec["was"])}&rdquo;'
                   + (f' &nbsp;<span class="muted">({_e(rec.get("why"))})</span>' if rec.get("why") else "")
                   + "</p>")

        groups = []
        cn = 0
        lead = s.get("lead") or {}
        lead_ids = lead.get("card_ids") or []
        if lead_ids:
            rows = []
            for cid in lead_ids:
                cn += 1
                rows.append(_card_html(cn, cid, cards))
            groups.append(f'<div class="grp"><div class="grp-h">The opening: {len(lead_ids)} '
                          f'fact{"s" if len(lead_ids) != 1 else ""}</div>{"".join(rows)}</div>')
        for h in s.get("h3s") or []:
            ids = h.get("card_ids") or []
            rows = []
            for cid in ids:
                cn += 1
                rows.append(_card_html(cn, cid, cards))
            groups.append(f'<div class="grp"><div class="grp-h sub3">Sub-heading: {_e(h.get("h3"))} '
                          f'<span class="muted" style="font-size:13px">&middot; {len(ids)} '
                          f'fact{"s" if len(ids) != 1 else ""}</span></div>{"".join(rows)}</div>')
        n_cards += cn
        if not groups:
            groups.append('<p class="muted">This section holds no fact cards.</p>')

        nr = "".join(f'<div class="note"><span class="tag">Research the architect asked for</span>'
                     f'{_e(x.get("topic"))}<br><span class="muted">Goes into: '
                     f'{_e(x.get("goes_to", "the opening"))}</span></div>'
                     for x in (s.get("needs_research") or []))

        blocks.append(f"""
<div class="sec">
  <div class="sec-head">
    <h3><span class="sec-n">{i}.</span>{_e(s["headline"])}</h3>
    <div>{''.join(pills)}</div>
    <p class="job"><b>What this section has to do:</b> {_e(s.get("job"))}</p>
    {was}
  </div>
  <div class="sec-body">{nr}{''.join(groups)}</div>
</div>""")

    # the honest tail: what was left out, and what did not work
    tail = []
    unused = st.get("unused_boxes") or []
    if unused:
        rows = "".join(f"<tr><td>{_e(b.get('h3'))}</td><td>{b.get('cards', 0)}</td>"
                       f"<td>{_e(b.get('why_benched') or 'no reason given')}</td></tr>" for b in unused)
        tail.append(f'<h3>Material the architect deliberately left out ({len(unused)} groups)</h3>'
                    f'<p class="muted">Nothing is ever dropped silently. Every group left out of the article '
                    f'has to come with a reason.</p><div class="tablewrap"><table>'
                    f'<tr><th>What it was about</th><th>Facts</th><th>Why it is not in the article</th></tr>'
                    f'{rows}</table></div>')
    fails = st.get("research_failures") or []
    if fails:
        rows = "".join(f"<tr><td>{_e(x.get('section'))}</td><td>{_e(x.get('h3'))[:160]}</td>"
                       f"<td>{_e(x.get('status'))}</td></tr>" for x in fails)
        tail.append(f'<h3>Research that came back empty ({len(fails)})</h3>'
                    f'<p class="muted">These sections stay in the article thinner than they were designed '
                    f'to be. It is recorded rather than hidden.</p><div class="tablewrap"><table>'
                    f'<tr><th>Section</th><th>What we went looking for</th><th>What happened</th></tr>'
                    f'{rows}</table></div>')
    dropped = st.get("dropped_items") or []
    if dropped:
        rows = "".join(f"<tr><td>{_e(d.get('item'))}</td><td>{_e(d.get('why'))}</td></tr>" for d in dropped)
        tail.append(f'<h3>List items dropped to fit the word budget ({len(dropped)})</h3>'
                    f'<div class="tablewrap"><table><tr><th>Item</th><th>Why</th></tr>{rows}</table></div>')
    removed = st.get("empty_subheadings_removed") or []
    if removed:
        rows = "".join(f"<tr><td>{_e(x.get('section'))}</td><td>{_e(x.get('h3'))}</td></tr>" for x in removed)
        tail.append(f'<h3>Sub-headings removed because the research never filled them ({len(removed)})</h3>'
                    f'<div class="tablewrap"><table><tr><th>Section</th><th>The sub-heading</th></tr>'
                    f'{rows}</table></div>')

    planned = hmap.get("h1_planned") or ""
    h1_note = ""
    if planned and planned != st.get("h1"):
        h1_note = (f'<div class="note"><span class="tag">The H1 was rewritten at the end</span>'
                   f'<b>Planned:</b> {_e(planned)}<br><b>Final:</b> {_e(st.get("h1"))}'
                   + (f'<br><span class="muted">{_e(hmap.get("why_h1"))}</span>' if hmap.get("why_h1") else "")
                   + "</div>")

    n_h3 = sum(len(s.get("h3s") or []) for s in secs)
    fmt = st.get("format_archetype", "")
    band = wb.get("band") or {}
    item_fields = st.get("item_fields") or []
    contract = ""
    if item_fields:
        contract = (f'<div class="note orange"><span class="tag">The per-item contract</span>'
                    f'Every list item in this article has to end with the same labelled parts, in this order: '
                    f'<b>{_e(" &middot; ".join(item_fields))}</b>. That is what lets a reader compare the '
                    f'items instead of just reading them.</div>')

    body = f"""
<header><div class="wrap">
  <a class="back" href="index.html">&larr; Back to the architect</a>
  <span class="kicker">A finished blueprint &middot; {_e(fmt)}</span>
  <h1>{_e(st.get("h1"))}</h1>
  <p class="lede">{_e(st.get("spine"))}</p>
</div></header>
<nav><div class="wrap"><a href="index.html">Overview</a><a href="prompts.html">The prompts</a>
<a href="#sections">The sections</a><a href="#tail">What was left out</a></div></nav>
<div class="wrap">
<section>
  <h2><span class="num">01</span>At a glance</h2>
  <p><span class="pill">{_e(fmt)}</span>
     <span class="pill n">{len(secs)} sections</span>
     <span class="pill n">{n_h3} sub-headings</span>
     <span class="pill n">{n_cards} fact cards placed</span>
     <span class="pill n">target {band.get('min', '?')}&ndash;{band.get('max', '?')} words</span>
     <span class="pill">main keyword: {_e(kw.get('primary') or 'none')}</span></p>
  {h1_note}
  {contract}
  <div class="note"><span class="tag">How to read the pages below</span>
  Each section shows its final heading, how many words it is allowed, and <b>what that section has to
  do</b>, written before the heading was, so the heading has something to be judged against. Underneath,
  every fact card the writer will be given, in order. Open a card to read the whole passage it came from.
  <br><br>Where a section carries a keyword, the chip says <b>targets</b>. Where a keyword was researched
  and bought but the heading did not take it, that is shown too. Dropping a researched keyword that does
  not fit is allowed, and it happens on purpose.</div>
</section>
<section id="sections">
  <h2><span class="num">02</span>The article, section by section</h2>
  <p class="sub">{len(secs)} sections in the order they will be read.</p>
  {''.join(blocks)}
</section>
<section id="tail">
  <h2><span class="num">03</span>What was left out, and what did not work</h2>
  <p class="sub">The parts of a run that are easy to hide. They are written down on purpose.</p>
  {''.join(tail) or '<p class="muted">Nothing was left out and nothing failed on this run.</p>'}
</section>
</div>
<footer><div class="wrap">{_e(st.get("h1"))} &middot; blueprint produced by the architect</div></footer>
"""
    meta = {"h1": st.get("h1") or slug, "format": fmt, "n_sections": len(secs), "n_cards": n_cards}
    return _page(st.get("h1") or slug, body, (st.get("spine") or "")[:200]), meta


# --------------------------------------------------------------------------- run
def build(out_dir=None):
    out_dir = out_dir or os.path.join(os.path.dirname(config.WRITE_OUT), "architect-review")
    os.makedirs(out_dir, exist_ok=True)
    slugs = _slugs()
    meta = {}
    for slug in slugs:
        page, m = build_article(slug)
        meta[slug] = m
        config.write_text(os.path.join(out_dir, f"article-{slug}.html"), page)
        print(f"  article-{slug}.html   {m['n_sections']} sections | {m['n_cards']} cards")
    config.write_text(os.path.join(out_dir, "prompts.html"), build_prompts())
    print(f"  prompts.html          {len(copy.PROMPTS)} prompts")
    config.write_text(os.path.join(out_dir, "index.html"), build_index(slugs, meta))
    print(f"  index.html")
    print(f"-> {out_dir}")
    return out_dir


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build the public architect review site.")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    build(a.out)
