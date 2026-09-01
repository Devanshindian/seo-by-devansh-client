#!/usr/bin/env python3
"""Build the write-body REVIEW page. Three tabs: the prompt, the output, and voices from the field.

  COMPANY=<slug> python3 build_body_review.py [--with-output]

The PROMPT tab is the real prompt, printed as-is, with every {{placeholder}} turned into something you
can click. Clicking one opens what that blank is for and the real value it gets filled with, taken from
a real article. Nothing is summarised or rewritten; the point is to read the actual instructions.

The OUTPUT tab is empty until --with-output is passed. It is left empty on purpose whenever the prompt
has changed and the articles have not been written again, because showing prose from an older prompt
next to a newer prompt is worse than showing nothing.

The FIELD tab shows the file behind {{FIELD}}: what real practitioners say, scraped from Reddit,
Teamblind and LinkedIn, filtered down to what this article can use. Two real ones are shown in full,
plus the empty case, because a reviewer needs to see that it returns nothing rather than inventing
something when a topic is not discussed in public.
"""
import argparse, html, json, os, re, subprocess, sys, tempfile
import config, article_ctx, fmt_router, write_body as wb

TAG = re.compile(r"\[c(\d+)\]")
PH = re.compile(r"\{\{(\w+)\}\}")
SLUGS = ["the-real-cost-recruitment-2026", "running-hiring-hackathon-that-screens",
         "strategic-interview-questions-paired-strong", "the-type-d-personality-label"]


def e(t):
    return html.escape(str(t or ""))


def values(slug):
    """What each blank is for, and the real value it is filled with on this article."""
    st = json.load(open(config.artifact(slug, "structure.json")))
    row = fmt_router._queue_row(slug)
    actx = article_ctx.article_context(slug)
    sec = st["sections"][0]
    idx = wb._card_index(slug)
    plan = "\n".join(f'{i}. {s.get("headline","")}\n   JOB: {s.get("job","")}'
                     for i, s in enumerate(st["sections"], 1))
    # The whole block, rules and all — not just the article's file. The rules live in
    # prompts/field-block.md and only reach the writer through this placeholder, so showing the bare
    # file here would hide half of what {{FIELD}} actually is.
    field = wb._field(slug).strip()
    return {
        "BRAND": ("Who publishes the article.", config.BRAND),
        "ABOUT": ("One line on what the company does.", config.ABOUT or ""),
        "TITLE": ("The article's title.", (row.get("asset") or "").strip()),
        "ANGLE": ("What makes this article different from every other one on the topic.",
                  (row.get("angle") or "").strip()),
        "SPINE": ("The single argument the whole article makes.", article_ctx.or_na(actx, "spine")),
        "PERSONA": ("Who it is written for. The writer thinks about them, never addresses them.",
                    article_ctx.persona(slug)),
        "PLAN": ("Every section's heading and brief. All sections are written at the same time by "
                 "separate calls, so this is how they avoid covering the same ground.", plan),
        "HEADING": ("This section's heading. Written earlier; the writer renders it exactly.",
                    sec.get("headline", "")),
        "JOB": ("The only brief this section gets. What it must settle.", sec.get("job", "")),
        "WORD_TARGET": ("How long this section should run.", str(sec.get("word_target") or "")),
        "SHAPE": ("The sub-headings for this section, and every researched fact that sits under each "
                  "one. Each fact carries an id and its source link.", wb._render_shape(sec, idx)),
        "BRIEF": ("The brand file: what the company believes, who is speaking, the words it uses and "
                  "the words it refuses.", wb._brief()),
        "FIELD": ("What real practitioners say about this topic, gathered from Reddit, Teamblind and "
                  "LinkedIn. It brings its own rules with it. Only appears when there was something "
                  "to find.",
                  field or "(nothing found for this article, so the whole block is absent)"),
        "PRODUCT_RULE": ("Whether the company may be named in this section.",
                         f"Name {config.BRAND} as little as you can. This article earns trust by being "
                         f"useful, not by selling. Never make {config.BRAND} the answer to the "
                         f"reader's problem."),
        "THIN": ("Appears only when this section's research came back empty. Usually blank.", ""),
        "ITEM_CONTRACT": ("Appears only on listicles. Usually blank.", ""),
        "TABLE": ("Appears only when the section must render a table. Usually blank.", ""),
        "LIST": ("Appears only when the section must render a list. Usually blank.", ""),
    }


CSS = """<style>
:root{--ink:#1c1a17;--muted:#6b6459;--line:#efe7d8;--paper:#fff;--cream:#fffdf8;--wash:#fff8ec;
--yellow:#ffb703;--yellow-soft:#ffe9ad;--orange:#fb7a00;--orange-soft:#ffd9b0;
--shadow:0 1px 2px rgba(28,26,23,.04),0 8px 24px rgba(28,26,23,.05);}
*{box-sizing:border-box;}
body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;line-height:1.62;font-size:16.5px;-webkit-font-smoothing:antialiased;}
.wrap{max-width:940px;margin:0 auto;padding:0 24px;}
header{background:linear-gradient(180deg,var(--wash),var(--paper));border-bottom:1px solid var(--line);padding:52px 0 30px;}
.kicker{display:inline-block;font-size:12.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--orange);background:var(--paper);border:1px solid var(--orange-soft);padding:5px 12px;border-radius:100px;margin-bottom:18px;}
h1{font-size:clamp(28px,5vw,40px);line-height:1.1;margin:0 0 12px;letter-spacing:-.02em;}
h1 .hl{background:linear-gradient(180deg,transparent 62%,var(--yellow-soft) 62%);padding:0 2px;}
.lede{font-size:18px;color:var(--muted);max-width:700px;margin:0;}
.tabs{display:flex;gap:6px;border-bottom:1px solid var(--line);margin:26px 0 0;}
.tab{font-size:15px;font-weight:700;color:var(--muted);background:none;border:none;border-bottom:3px solid transparent;padding:11px 18px;cursor:pointer;font-family:inherit;}
.tab.on{color:var(--ink);border-bottom-color:var(--orange);}
.pane{display:none;padding:34px 0 70px;} .pane.on{display:block;}
.note{background:var(--cream);border:1px solid var(--line);border-left:4px solid var(--yellow);border-radius:12px;padding:15px 18px;margin:0 0 26px;font-size:15.5px;}
.note b{color:var(--ink);}
pre.prompt{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;line-height:1.72;
  white-space:pre-wrap;word-break:break-word;background:var(--paper);border:1px solid var(--line);
  border-radius:14px;padding:24px 26px;box-shadow:var(--shadow);margin:0;}
.ph{font-family:inherit;font-size:12.5px;font-weight:800;color:#fff;background:var(--orange);
  border:none;border-radius:6px;padding:2px 8px;cursor:pointer;white-space:nowrap;}
.ph:hover{background:#d96800;}
.ph.open{background:var(--ink);}
.pv{display:none;margin:10px 0 14px;border:1px solid var(--orange-soft);border-radius:12px;background:var(--wash);}
.pv.on{display:block;}
.pv .h{padding:11px 16px;border-bottom:1px dashed var(--orange-soft);font-size:14px;font-family:-apple-system,sans-serif;color:var(--ink);}
.pv .h b{color:var(--orange);}
.pv .val{padding:14px 16px;font-size:12.5px;line-height:1.66;white-space:pre-wrap;max-height:440px;overflow:auto;color:var(--ink);}
.pv .empty{padding:14px 16px;font-size:14px;color:var(--muted);font-family:-apple-system,sans-serif;}
.idx{display:flex;gap:7px;flex-wrap:wrap;align-items:center;background:var(--cream);
border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:0 0 22px;}
.idx .k{font-size:11.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);width:100%;margin-bottom:4px;}
.exh{margin:34px 0 12px;padding-bottom:10px;border-bottom:1px solid var(--line);}
.exh .n{font-size:11.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--orange);}
.exh h3{margin:5px 0 0;font-size:19px;line-height:1.3;letter-spacing:-.01em;}
.exh .m{margin:7px 0 0;font-size:14px;color:var(--muted);}
.empty-tab{text-align:center;padding:70px 20px;color:var(--muted);}
.empty-tab .em{font-size:40px;} .empty-tab h3{color:var(--ink);margin:14px 0 8px;font-size:20px;}
.empty-tab p{max-width:520px;margin:0 auto 10px;font-size:15.5px;}
footer{padding:30px 0 60px;color:var(--muted);font-size:13.5px;border-top:1px solid var(--line);}
</style>"""

JS = """<script>
document.querySelectorAll('.tab').forEach(function(t){
  t.onclick=function(){
    document.querySelectorAll('.tab').forEach(function(x){x.classList.remove('on');});
    document.querySelectorAll('.pane').forEach(function(x){x.classList.remove('on');});
    t.classList.add('on');
    document.getElementById(t.dataset.pane).classList.add('on');
  };
});
document.querySelectorAll('.ph').forEach(function(b){
  b.onclick=function(){
    var v=document.getElementById(b.dataset.for);
    var open=v.classList.contains('on');
    document.querySelectorAll('.pv').forEach(function(x){x.classList.remove('on');});
    document.querySelectorAll('.ph').forEach(function(x){x.classList.remove('open');});
    if(!open){ v.classList.add('on'); b.classList.add('open');
      v.scrollIntoView({behavior:'smooth',block:'nearest'}); }
  };
});
</script>"""


def field_pane():
    """The {{FIELD}} file, in full, for real articles. Shown, not described.

    Two that found something, then one that did not. The empty one is the point: the step is allowed to
    come back with nothing, and when it does the whole block is dropped from the writer's prompt rather
    than a thin finding being passed off as a pattern."""
    found, empty = [], []
    for slug in SLUGS:
        p = config.artifact_optional(slug, "voices-from-the-field.md")
        if not os.path.exists(p):
            continue
        txt = open(p).read().strip()
        n = len([h for h in re.findall(r"^## (.+)$", txt, re.M)
                 if "did not show up" not in h.lower()])
        cov = next((l for l in txt.split("\n") if l.startswith("**Coverage.**")), "")
        cov = re.sub(r"\*\*", "", cov).replace("Coverage.", "").strip()
        row = fmt_router._queue_row(slug)
        item = {"title": (row.get("asset") or slug).strip(), "text": txt, "n": n, "cov": cov}
        (found if n >= 2 else empty).append(item)

    def card(it, kicker):
        # kicker is ours, never user text, so it is written straight in and may carry an entity
        return (f'<div class="exh"><div class="n">{kicker}</div><h3>{e(it["title"])}</h3>'
                f'<p class="m">{e(it["cov"])}</p></div>'
                f'<pre class="prompt">{e(it["text"])}</pre>')

    blocks = [card(it, f"Example {i} &middot; {it['n']} findings kept")
              for i, it in enumerate(found[:2], 1)]
    if empty:
        blocks.append(card(empty[0], "And when there is nothing to find"))

    if not blocks:
        return ("""<div class="wrap"><div class="empty-tab"><div class="em">&#128172;</div>
<h3>Nothing gathered yet</h3><p>No article has been through the field step.</p></div></div>""")

    tail = ("" if not empty else
            "<p>The third one is not a failure. That topic is not argued about in public, so the step "
            "said so and stopped. When that happens the whole block is removed from the writer's "
            "instructions, because one weak finding costs the writer more attention than an absent "
            "file does, and it invites leaning on something that was never solid.</p>")
    return f"""<div class="wrap">
<div class="note"><b>What this is.</b> Before an article is written, we search Reddit, Teamblind and
LinkedIn for people who actually do this work, read the threads, and cut what came back down to the
few patterns this article can use. The writer gets the file below and is told to write it as what
people say, never as fact: no numbers from it, no source tag, no quoting or naming anyone. It is what
stops a section reading like an encyclopedia entry.{tail}</div>
{''.join(blocks)}
</div>"""


def build(with_output=False):
    prompt = open(os.path.join(config.PROMPTS, "write-body.md")).read()
    vals = values(SLUGS[0])
    row = fmt_router._queue_row(SLUGS[0])

    # Render the prompt verbatim, swapping each {{BLANK}} for a button, and dropping its panel in
    # after the line it appeared on so the value opens next to where it is used.
    seen, out_lines = [], []
    for line in prompt.split("\n"):
        names = PH.findall(line)
        out_lines.append(PH.sub(
            lambda m: f'<button class="ph" data-for="v-{m.group(1)}">{{{{{m.group(1)}}}}}</button>', e(line)))
        for n in names:
            if n in seen:
                continue
            seen.append(n)
            what, val = vals.get(n, ("", ""))
            inner = (f'<div class="val">{e(val)}</div>' if val else
                     '<div class="empty">Blank on this section. It only appears when the section '
                     'needs it.</div>')
            out_lines.append(
                f'<div class="pv" id="v-{n}"><div class="h"><b>{{{{{n}}}}}</b> &nbsp;{e(what)}</div>'
                f'{inner}</div>')

    # An index of every blank, at the top. Without it {{BRIEF}} sits 65% down a wall of monospace and
    # a reviewer simply never finds it.
    idx_btns = "".join(
        f'<button class="ph" data-for="v-{n}">{{{{{n}}}}}</button>' for n in seen)

    body_pane = ""
    if with_output:
        body_pane = "<div class='wrap'><p>(output rendering not enabled in this build)</p></div>"
    else:
        body_pane = """<div class="wrap"><div class="empty-tab"><div class="em">&#128221;</div>
<h3>Empty on purpose</h3>
<p>The instructions on the other tab were changed after the last set of articles was written, so the
drafts we have came from an older version. Showing them here would mean judging new instructions by old
work.</p>
<p>The articles are being written again. This tab fills up when they are done.</p></div></div>"""

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Write-body &mdash; the prompt</title>{CSS}</head><body>
<header><div class="wrap"><div class="kicker">Write phase &middot; the writing step</div>
<h1>The instructions we give the <span class="hl">writer</span></h1>
<p class="lede">Every section of an article is written by its own separate call, using the instructions
below. The orange blanks are filled in per section. Click any one to see what it is and the real value
it gets.</p>
<div class="tabs">
<button class="tab on" data-pane="p-prompt">The prompt</button>
<button class="tab" data-pane="p-out">The output</button>
<button class="tab" data-pane="p-field">Voices from the field</button>
</div></div></header>

<div class="pane on" id="p-prompt"><div class="wrap">
<div class="note"><b>How to read this.</b> This is the real file, unedited. The orange blanks are
filled in per section. Click any one to see what it is and the real value it gets, taken from
<b>{e((row.get('asset') or '').strip())}</b>.</div>
<div class="idx"><span class="k">Every blank, if you would rather not scroll</span>{idx_btns}</div>
<pre class="prompt">{chr(10).join(out_lines)}</pre>
</div></div>

<div class="pane" id="p-out">{body_pane}</div>

<div class="pane" id="p-field">{field_pane()}</div>

<footer><div class="wrap">The writing step &middot; one call per section &middot;
{len(prompt.split()):,} words of instructions, plus that section's own facts.</div></footer>
{JS}</body></html>"""

    # NOT inside projects/. This page exists to be published, and a published page has no business
    # sitting in the article output. It is written to a temp dir; --publish clones the Pages repo,
    # drops it in, pushes, and removes the clone, so nothing persists in the tree.
    out = os.path.join(tempfile.gettempdir(), "write-body-review.html")
    config.write_text(out, page)
    print(f"  prompt {len(prompt.split()):,} words · {len(seen)} clickable blanks · "
          f"output tab {'filled' if with_output else 'EMPTY'}")
    print(f"  -> {out}")
    return out


PAGES_REPO = "https://github.com/Devanshindian/write-phase-97c578f8.git"


def publish(path):
    """Clone, drop the page in, push, delete the clone. Nothing is left behind in the project."""
    clone = os.path.join(tempfile.mkdtemp(prefix="pages-"), "repo")
    subprocess.run(["git", "clone", "--depth", "1", "-q", PAGES_REPO, clone], check=True)
    import shutil
    shutil.copy(path, os.path.join(clone, "write-body.html"))
    subprocess.run(["git", "-C", clone, "add", "-A"], check=True)
    r = subprocess.run(["git", "-C", clone, "-c", "user.email=marketing@testlify.com",
                        "-c", "user.name=devansh", "commit", "-q", "-m",
                        "Update the write-body page"], capture_output=True, text=True)
    if "nothing to commit" in (r.stdout + r.stderr):
        print("  nothing changed since the last publish")
    else:
        subprocess.run(["git", "-C", clone, "push", "-q", "origin", "main"], check=True)
        print("  pushed -> https://devanshindian.github.io/write-phase-97c578f8/write-body.html")
    shutil.rmtree(os.path.dirname(clone), ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-output", action="store_true",
                    help="fill the output tab. Only pass this once the articles have been rewritten "
                         "with the current prompt.")
    ap.add_argument("--publish", action="store_true", help="push it to the public page")
    a = ap.parse_args()
    out = build(a.with_output)
    if a.publish:
        publish(out)
