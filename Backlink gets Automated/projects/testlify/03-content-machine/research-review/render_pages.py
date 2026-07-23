#!/usr/bin/env python3
"""Render the 10 bundle items into standalone HTML pages for the public review site.
Nine are markdown docs (rendered here); one is the already-interactive blueprint HTML (copied, with a back bar).
Output goes into _pages-repo/ next to index.html."""
import os, re, shutil, html

HERE = os.path.dirname(os.path.abspath(__file__))
BGA = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(HERE, "_pages-repo")
S = "testlify-state-skills-based-hiring-2026"

def P(*p): return os.path.join(BGA, *p)
BC = ("projects", "testlify", "01-brand-context")
BB = ("projects", "testlify", "brand-brain", "output")

# ---- minimal markdown -> HTML -------------------------------------------------
def _inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', lambda m: '<code>' + m.group(1) + '</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'<i>\1</i>', s)
    return s

def _strip_md(md):
    md = md.replace("\r\n", "\n")
    md = re.sub(r'\A---\n.*?\n---\n', '', md, flags=re.DOTALL)   # YAML frontmatter
    md = re.sub(r'<!--.*?-->', '', md, flags=re.DOTALL)          # HTML comments (the leak)
    return md

def _render_list(items):
    """items = list of (indent:int, ordered:bool, text:str) -> nested <ul>/<ol> by indent."""
    out, stack = [], []
    for indent, ordered, text in items:
        tag = 'ol' if ordered else 'ul'
        while stack and indent < stack[-1][0]:
            out.append(f"</li></{stack[-1][1]}>"); stack.pop()
        if stack and indent == stack[-1][0]:
            out.append("</li><li>" + _inline(text))
        else:
            out.append(f"<{tag}><li>" + _inline(text)); stack.append((indent, tag))
    while stack:
        out.append(f"</li></{stack[-1][1]}>"); stack.pop()
    return "".join(out)

def md_to_html(md):
    lines = _strip_md(md).split("\n")
    out, i, n, para = [], 0, len(lines), []
    def close_p():
        if para:
            out.append("<p>" + "<br>".join(_inline(x) for x in para) + "</p>"); para.clear()
    while i < n:
        ln = lines[i]
        if ln.strip().startswith("```"):
            close_p(); i += 1; code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(html.escape(lines[i], quote=False)); i += 1
            i += 1; out.append("<pre><code>" + "\n".join(code) + "</code></pre>"); continue
        if "|" in ln and i + 1 < n and re.match(r'^\s*\|?[\s:|-]+\|[\s:|-]*$', lines[i + 1]) and "-" in lines[i + 1]:
            close_p()
            def cells(row): return [c.strip() for c in row.strip().strip("|").split("|")]
            head = cells(ln); i += 2; rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(cells(lines[i])); i += 1
            t = ["<table><thead><tr>"] + ["<th>" + _inline(c) + "</th>" for c in head] + ["</tr></thead><tbody>"]
            for r in rows:
                t.append("<tr>" + "".join("<td>" + _inline(c) + "</td>" for c in r) + "</tr>")
            t.append("</tbody></table>"); out.append("".join(t)); continue
        m = re.match(r'^(#{1,6})\s+(.*)$', ln)
        if m:
            close_p(); lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_inline(m.group(2).strip())}</h{lvl}>"); i += 1; continue
        if re.match(r'^\s*([-*_])\1\1+\s*$', ln):
            close_p(); out.append("<hr>"); i += 1; continue
        if ln.strip().startswith(">"):
            close_p(); q = []
            while i < n and lines[i].strip().startswith(">"):
                q.append(lines[i].strip()[1:].strip()); i += 1
            out.append("<blockquote>" + "<br>".join(_inline(x) for x in q) + "</blockquote>"); continue
        if re.match(r'^\s*([-*+]|\d+\.)\s+', ln):
            close_p(); items = []
            while i < n:
                lm = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.*)$', lines[i])
                if lm:
                    items.append((len(lm.group(1)), bool(re.match(r'\d+\.', lm.group(2))), lm.group(3))); i += 1
                elif lines[i].strip() and lines[i][:1] in (" ", "\t") and items:   # wrapped continuation
                    ind, od, tx = items[-1]; items[-1] = (ind, od, tx + " " + lines[i].strip()); i += 1
                else:
                    break
            out.append(_render_list(items)); continue
        if not ln.strip():
            close_p(); i += 1; continue
        para.append(ln); i += 1
    close_p()
    return "\n".join(out)

# ---- page template ------------------------------------------------------------
STYLE = """
  :root{--ink:#1c1a17;--muted:#6b6459;--line:#efe7d8;--paper:#fff;--cream:#fffdf8;--wash:#fff8ec;
    --yellow:#ffb703;--yellow-soft:#ffe9ad;--orange:#fb7a00;--orange-soft:#ffd9b0;--blue-ink:#2f6fb0;
    --shadow:0 1px 2px rgba(28,26,23,.04),0 8px 24px rgba(28,26,23,.05);}
  *{box-sizing:border-box;} html{scroll-behavior:smooth;}
  body{margin:0;background:var(--paper);color:var(--ink);line-height:1.62;font-size:16px;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;}
  a{color:var(--orange);}
  .bar{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.94);backdrop-filter:blur(8px);
    border-bottom:1px solid var(--line);padding:11px 0;}
  .bar .wrap{display:flex;align-items:center;gap:12px;}
  .back{font-size:13.5px;font-weight:600;color:var(--orange);text-decoration:none;background:var(--wash);
    border:1px solid var(--orange-soft);border-radius:100px;padding:5px 13px;}
  .back:hover{background:var(--orange-soft);}
  .crumb{font-size:12.5px;color:var(--muted);font-weight:600;letter-spacing:.02em;}
  .wrap{max-width:820px;margin:0 auto;padding:0 24px;}
  header{background:linear-gradient(180deg,var(--wash),var(--paper));border-bottom:1px solid var(--line);padding:40px 0 26px;}
  .kicker{display:inline-block;font-size:11.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
    color:var(--orange);background:var(--paper);border:1px solid var(--orange-soft);padding:4px 11px;border-radius:100px;margin-bottom:14px;}
  h1{font-size:clamp(24px,4vw,34px);line-height:1.15;letter-spacing:-.02em;margin:0;}
  main{padding:30px 0 60px;}
  main h1{font-size:26px;margin:30px 0 10px;} main h2{font-size:21px;margin:28px 0 8px;letter-spacing:-.01em;}
  main h3{font-size:17px;margin:22px 0 6px;} main h4{font-size:15px;margin:18px 0 6px;color:var(--muted);}
  p{margin:0 0 13px;} ul,ol{margin:0 0 13px;padding-left:22px;} li{margin:4px 0;}
  b{color:var(--ink);}
  code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.86em;background:var(--wash);
    border:1px solid var(--orange-soft);border-radius:5px;padding:1px 5px;}
  pre{background:var(--cream);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow:auto;font-size:13px;}
  pre code{background:none;border:none;padding:0;}
  blockquote{margin:14px 0;padding:10px 16px;border-left:4px solid var(--yellow);background:var(--cream);
    border-radius:8px;color:var(--muted);}
  hr{border:none;border-top:1px solid var(--line);margin:22px 0;}
  table{width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;border:1px solid var(--line);border-radius:10px;overflow:hidden;}
  th,td{text-align:left;padding:8px 11px;border-bottom:1px solid var(--line);vertical-align:top;}
  th{background:var(--wash);font-size:11.5px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted);}
  tr:last-child td{border-bottom:none;}
  footer{padding:30px 0 50px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);}
"""

def page(title, kicker, body_html):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} — research bundle</title><style>{STYLE}</style></head><body>
<div class="bar"><div class="wrap"><a class="back" href="index.html">&larr; Back to overview</a>
<span class="crumb">Research bundle · {html.escape(title)}</span></div></div>
<header><div class="wrap"><span class="kicker">{html.escape(kicker)}</span><h1>{html.escape(title)}</h1></div></header>
<main><div class="wrap">{body_html}</div></main>
<footer><div class="wrap">Part of the research bundle · <a href="index.html">back to the overview</a></div></footer>
</body></html>"""

def render_md(title, kicker, *paths, intro=""):
    parts = []
    if intro:
        parts.append(f"<blockquote>{intro}</blockquote>")
    for p in paths:
        parts.append(md_to_html(open(p, encoding="utf-8").read()))
    return page(title, kicker, "\n".join(parts))

# ---- build --------------------------------------------------------------------
os.makedirs(OUT, exist_ok=True)
jobs = [
    ("voice.html",     "Voice",                 "How Testlify sounds",       [P(*BC, "brand-voice.md")]),
    ("style.html",     "Style & mechanics",     "Formatting rules",          [P(*BC, "style-guide.md")]),
    ("product.html",   "Product facts",         "What Testlify does",        [P(*BC, "features.md")]),
    ("seo.html",       "SEO / AEO / GEO checklist", "On-page rules",         [P(*BC, "seo-aeo-geo-checklist.md")]),
    ("cite.html",      "Cite-from material",    "Approved stats, opinions, stories", [P(*BB, "stats.md"), P(*BB, "opinions.md"), P(*BB, "stories.md")]),
    ("examples.html",  "Worked examples",       "Writing to match",          [P(*BC, "writing-examples.md")]),
    ("integrity.html", "Writing integrity",     "Honesty & claim rules",     [P(*BC, "writing-integrity.md")]),
    ("anti-ai.html",   "Anti-AI writing check", "The final pass",            [P("workflows", "03-content-machine", "reference", "avoid-ai-writing", "SKILL.md")]),
    ("search.html",    "Keyword & competitor research", "The full search brief", [P("projects", "testlify", "03-content-machine", "dataforseo", "out", S, f"research-doc-{S}.md")]),
    ("gap.html",       "Gap-check report",      "Coverage of what the article needs", [P("projects", "testlify", "03-content-machine", "gap-check", "out", S, "gap-check.md")]),
]
for fname, title, kicker, paths in jobs:
    open(os.path.join(OUT, fname), "w", encoding="utf-8").write(render_md(title, kicker, *paths))
    print("wrote", fname)

# the article plan = the interactive blueprint HTML, copied, with a back bar injected after <body>
bp = open(P("projects", "testlify", "03-content-machine", "research-structure", "out", S, f"structure-{S}.html"), encoding="utf-8").read()
backbar = ('<div style="position:sticky;top:0;z-index:999;background:rgba(255,255,255,.94);'
           'border-bottom:1px solid #efe7d8;padding:10px 24px;font-family:-apple-system,sans-serif;">'
           '<a href="index.html" style="font-size:13.5px;font-weight:600;color:#fb7a00;text-decoration:none;'
           'background:#fff8ec;border:1px solid #ffd9b0;border-radius:100px;padding:5px 13px;">&larr; Back to overview</a></div>')
bp = re.sub(r'(<body[^>]*>)', r'\1' + backbar, bp, count=1)
open(os.path.join(OUT, "plan.html"), "w", encoding="utf-8").write(bp)
print("wrote plan.html (blueprint, with back bar)")

# the evidence pack = the STORM dossier viewer (clickable citations), copied, with the same back bar
DTOP = "State_of_Skills-Based_Hiring:_Annual_Benchmark_Report_—_the_winning_format_here_is_the_annual_benchmark_report"
ev = open(P("projects", "testlify", "03-content-machine", "storm", "out", DTOP, "article.html"), encoding="utf-8").read()
ev = re.sub(r'(<body[^>]*>)', r'\1' + backbar, ev, count=1)
open(os.path.join(OUT, "evidence.html"), "w", encoding="utf-8").write(ev)
print("wrote evidence.html (STORM dossier, with back bar)")
print("DONE ->", OUT)
