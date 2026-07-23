"""Render a STORM output folder into ONE self-contained, viewable HTML — clickable citations + references.
Uses STORM's own citation logic (url_to_unified_index -> [n] -> source url; bibliography from title+url),
exactly like its Streamlit demo (frontend/demo_light/demo_util.py). Does NOT touch the STORM pipeline.
Usage: python view-article.py <out/topic-dir>   ->  writes article.html in that dir.
"""
import os, sys, re, json, html

d = sys.argv[1] if len(sys.argv) > 1 else "out/Recruiting_metrics_benchmarks"
art = open(os.path.join(d, "storm_gen_article_polished.txt")).read()
uti = json.load(open(os.path.join(d, "url_to_info.json")))

# --- STORM's exact citation mapping: unified index n -> {url, title} ---
idx_to_src = {}
for url, n in uti["url_to_unified_index"].items():
    info = uti["url_to_info"][url]
    idx_to_src[int(n)] = {"url": url, "title": info.get("title") or url}

def domain(u):
    m = re.search(r"https?://(?:www\.)?([^/]+)", u or "")
    return m.group(1) if m else ""

# --- render markdown -> HTML body (headings, paragraphs, clickable [n] citations) ---
def link_citations(text):
    # [n] -> superscript clickable link to the source (title as tooltip)
    def repl(m):
        n = int(m.group(1)); s = idx_to_src.get(n)
        if not s: return m.group(0)
        t = html.escape(s["title"])[:140]
        return f'<a class="cite" href="#ref-{n}" title="{t}">{n}</a>'
    return re.sub(r"\[(\d+)\]", repl, text)

toc, body, cited = [], [], set()
for raw in art.split("\n"):
    line = raw.rstrip()
    for n in re.findall(r"\[(\d+)\]", line): cited.add(int(n))
    if not line.strip():
        continue
    h = re.match(r"^(#{1,4})\s+(.*)$", line)
    if h:
        lvl = len(h.group(1)); txt = h.group(2).strip()
        if txt.lower() == "summary": txt = "Summary"
        slug = re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")
        if lvl <= 2:
            toc.append((lvl, txt, slug))
        body.append(f'<h{lvl} id="{slug}">{html.escape(txt)}</h{lvl}>')
    else:
        body.append(f"<p>{link_citations(html.escape(line))}</p>")
body_html = "\n".join(body)
toc_html = "\n".join(
    f'<a class="toc-l{lvl}" href="#{slug}">{html.escape(txt)}</a>' for lvl, txt, slug in toc)

# --- references (STORM's bibliography: sorted by index, title + url) ---
refs = []
for n in sorted(idx_to_src):
    s = idx_to_src[n]
    refs.append(f'<li id="ref-{n}"><span class="rn">{n}</span>'
                f'<a href="{html.escape(s["url"])}" target="_blank">{html.escape(s["title"])}</a>'
                f'<span class="dom">{html.escape(domain(s["url"]))}</span></li>')
refs_html = "\n".join(refs)

words = len(re.sub(r"\[\d+\]", "", art).split())
# Title from the topic folder name (e.g. out/eq_test -> "Eq test"), not hardcoded — the preview must match the topic.
_t = os.path.basename(os.path.normpath(d)).replace("_", " ").strip()
title = (_t[:1].upper() + _t[1:]) if _t else "STORM dossier"

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{html.escape(title)}</title>
<style>
:root{{--ink:#1c1a17;--muted:#6b6459;--line:#efe7d8;--wash:#fff8ec;--yellow:#ffb703;--orange:#fb7a00;--orange-soft:#ffd9b0;}}
*{{box-sizing:border-box;}} html{{scroll-behavior:smooth;}}
body{{margin:0;background:#fff;color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Georgia,serif;line-height:1.7;font-size:17px;}}
.layout{{display:grid;grid-template-columns:250px 1fr;max-width:1120px;margin:0 auto;gap:36px;padding:0 24px;}}
aside{{position:sticky;top:0;align-self:start;height:100vh;overflow:auto;padding:28px 0;border-right:1px solid var(--line);}}
aside .k{{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--orange);margin:0 0 12px;}}
aside a{{display:block;color:var(--muted);text-decoration:none;font-size:13.5px;padding:3px 0;line-height:1.35;font-family:-apple-system,sans-serif;}}
aside a:hover{{color:var(--ink);}} aside a.toc-l2{{padding-left:14px;font-size:12.5px;}}
main{{padding:40px 0 80px;max-width:760px;}}
.hero{{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:8px;}}
.eyebrow{{font-family:-apple-system,sans-serif;font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--orange);}}
h1.title{{font-size:36px;line-height:1.12;letter-spacing:-.02em;margin:10px 0 12px;}}
.meta{{font-family:-apple-system,sans-serif;font-size:13.5px;color:var(--muted);}}
.meta b{{color:var(--ink);}}
h1{{font-size:26px;letter-spacing:-.01em;margin:38px 0 10px;padding-top:6px;}}
h2{{font-size:21px;margin:30px 0 8px;}} h3{{font-size:18px;margin:24px 0 6px;color:#2b2621;}}
main p{{margin:0 0 15px;}}
a.cite{{font-family:-apple-system,sans-serif;font-size:11px;font-weight:700;vertical-align:super;line-height:0;text-decoration:none;color:#fff;background:var(--orange);border-radius:5px;padding:1px 5px;margin:0 1px;}}
a.cite:hover{{background:var(--ink);}}
.refs{{margin-top:50px;border-top:2px solid var(--line);padding-top:22px;}}
.refs h2{{font-size:20px;margin:0 0 14px;}}
.refs ol{{list-style:none;padding:0;margin:0;}}
.refs li{{font-family:-apple-system,sans-serif;font-size:14px;padding:7px 0;border-bottom:1px solid var(--line);display:flex;gap:10px;align-items:baseline;scroll-margin-top:20px;}}
.refs li:target{{background:var(--wash);}}
.rn{{flex:none;width:26px;height:22px;display:grid;place-items:center;background:var(--wash);border:1px solid var(--orange-soft);border-radius:6px;font-size:11px;font-weight:700;color:var(--orange);}}
.refs a{{color:var(--ink);text-decoration:none;}} .refs a:hover{{color:var(--orange);text-decoration:underline;}}
.dom{{color:var(--muted);font-size:12px;margin-left:auto;white-space:nowrap;}}
@media(max-width:820px){{.layout{{grid-template-columns:1fr;}}aside{{display:none;}}}}
</style></head><body>
<div class="layout">
<aside><p class="k">Contents</p>{toc_html}</aside>
<main>
<div class="hero">
<span class="eyebrow">STORM · Evidence Dossier</span>
<h1 class="title">{html.escape(title)}</h1>
<p class="meta"><b>{words:,}</b> words · <b>{len(idx_to_src)}</b> sources cited · rendered from the STORM output with clickable citations</p>
</div>
{body_html}
<div class="refs"><h2>References</h2><ol>{refs_html}</ol></div>
</main></div></body></html>"""

out_path = os.path.join(d, "article.html")
open(out_path, "w").write(HTML)
print(f"wrote {out_path}  ({words} words, {len(idx_to_src)} cited sources)")
