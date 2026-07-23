#!/usr/bin/env python3
"""Build the interactive HTML map from data/final-clusters.json.
3 levels: THEME > PILLAR > spoke posts. Native <details> (reliable). Search included."""
import json, html as H, collections

d = json.load(open("data/final-clusters.json"))
themes = d["themes"]; orphans = d["orphans"]; T = d["totals"]
U = "https://testlify.com"
def esc(s): return H.escape(str(s))

npil = T["pillars"]
avg = round(T["posts_in_pillars"] / npil, 1)
nbuild = sum(1 for v in themes.values() if v["status"] == "BUILD")

def spokes_html(slugs):
    return '<div class="spokes">' + "".join(
        f'<a class="spoke" target="_blank" href="{U}/{s}/">{esc(s)}</a>' for s in slugs) + '</div>'

STLABEL = {"pillar_working":"PILLAR WORKING", "pillar_weak":"PILLAR — WEAK LINKS",
           "page_orphaned":"PAGE EXISTS · 0 CLUSTER LINKS", "article":"LEAD ARTICLE ONLY",
           "partial":"THIN PAGE ONLY", "missing":"NO HUB"}
STCLASS = {"pillar_working":"working","pillar_weak":"weak","page_orphaned":"orphan",
           "article":"article","partial":"partial","missing":"missing"}
def pillar_html(p):
    st = p.get("status", "missing")
    hub = p.get("hub_url")
    hubslug = hub.replace("https://testlify.com/","") if hub else ""
    link = f' → <a class="hub-link" target="_blank" href="{esc(hub)}/">{esc(hubslug)}</a>' if hub else ""
    badge = f'<span class="st st-{STCLASS[st]}">{STLABEL[st]}</span>'
    if st in ("pillar_working","pillar_weak","page_orphaned"):
        detail = f'Hub page exists{link} but links to <b>{p.get("linked",0)} of {p.get("n_sp",p["n"])}</b> of its cluster posts.'
    elif st == "article":
        detail = f'Only a single lead article exists{link} — no structured hub that links the cluster.'
    elif st == "partial":
        detail = f'Only a thin glossary/tools page exists{link} — not a real pillar.'
    else:
        detail = 'No hub page exists for this cluster — build one.'
    body = f'<div class="hub">Live link-check: {detail}</div>' + spokes_html(p["spokes"])
    return (f'<details class="pillar st-row-{STCLASS[st]}"><summary>'
            f'<span class="cnt">{p["n"]}</span><b>{esc(p["pillar"])}</b>{badge}'
            f'</summary>{body}</details>')

def theme_html(name, v):
    c = v.get("cov", {})
    work = c.get("pillar_working",0)+c.get("pillar_weak",0)
    bar = (f'<span class="mini st-working">{work} working</span>'
           f'<span class="mini st-orphan">{c.get("page_orphaned",0)} orphan-page</span>'
           f'<span class="mini st-article">{c.get("article",0)} lead-art</span>'
           f'<span class="mini st-partial">{c.get("partial",0)} thin</span>'
           f'<span class="mini st-missing">{c.get("missing",0)} none</span>')
    body = (f'<div class="hub">Suggested hub: {esc(v["hub"])}</div>'
            + "".join(pillar_html(p) for p in v["pillars"]))
    return (f'<details class="theme" data-s="{esc(name.lower())}"><summary>'
            f'<span class="ptitle">{esc(name)}</span>'
            f'<span class="pcount">{v["n_pillars"]} pillars · {v["n_posts"]} posts</span>'
            f'</summary><div class="covbar">{bar}</div>{body}</details>')

cov = collections.Counter()
for v in themes.values():
    for p in v["pillars"]: cov[p.get("status","missing")] += 1
working = cov["pillar_working"] + cov["pillar_weak"]
stats = [(T["blog"], "Blog posts"), (npil, "Pillars"),
         (working, "✅ Working pillars"), (cov["page_orphaned"], "⚠️ Orphan pages"),
         (cov["article"], "Lead-article only"), (cov["partial"]+cov["missing"], "No real hub")]
stats_html = "".join(f'<div class="stat"><b>{v:,}</b><span>{t}</span></div>'
                     if isinstance(v, int) else f'<div class="stat"><b>{v}</b><span>{t}</span></div>'
                     for v, t in stats)
themes_html = "".join(theme_html(n, v) for n, v in themes.items())
orphan_html = (f'<details class="theme"><summary><span class="ptitle">Orphans — one-off posts</span>'
               f'<span class="pcount">{len(orphans)} posts</span></summary>'
               f'<div class="hub">No group of 3+ related posts — standalone or candidates to expand into a cluster.</div>'
               f'{spokes_html(orphans)}</details>')

PAGE = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Testlify — Pillar &amp; Cluster Map</title>
<style>
:root{{--mut:#9aa3c4;--line:#2e3860;--card:#1a1f35;--card2:#232a45;--accent:#6c8cff;
--exist:#2ecc71;--build:#ff8c42;--txt:#e7ebf5;}}
*{{box-sizing:border-box}} body{{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
background:linear-gradient(180deg,#0c0f1c,#12162a);color:var(--txt);padding:0 0 80px}}
.wrap{{max-width:1000px;margin:0 auto;padding:0 22px}} header{{padding:30px 22px 4px;max-width:1000px;margin:0 auto}}
h1{{margin:0 0 4px;font-size:25px}} .sub{{color:var(--mut);font-size:13.5px}}
.how{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:14px 0;color:var(--mut);font-size:13.5px}}
.how b{{color:var(--txt)}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:11px 15px;min-width:104px}}
.stat b{{display:block;font-size:21px}} .stat span{{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.5px}}
#q{{width:100%;padding:12px 14px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--txt);font-size:15px;margin:6px 0 4px}}
.hint{{color:var(--mut);font-size:12px;min-height:16px}}
details{{border:1px solid var(--line);border-radius:12px;margin:10px 0;background:var(--card);overflow:hidden}}
details.pillar{{margin:7px 0;background:var(--card2)}}
summary{{list-style:none;cursor:pointer;padding:13px 16px;display:flex;align-items:center;gap:10px;user-select:none}}
summary::-webkit-details-marker{{display:none}}
summary::before{{content:"▸";color:var(--mut);font-size:13px;transition:transform .12s;flex:0 0 auto}}
details[open]>summary::before{{transform:rotate(90deg)}}
.pillar>summary{{padding:9px 14px;font-size:14px}}
.ptitle{{font-size:16.5px;font-weight:650;flex:1}}
.pcount{{color:var(--mut);font-size:12.5px;flex:0 0 auto;text-align:right}}
.badge{{font-size:10px;font-weight:800;padding:3px 8px;border-radius:20px;letter-spacing:.3px;flex:0 0 auto}}
.b-exist{{background:rgba(46,204,113,.16);color:var(--exist);border:1px solid rgba(46,204,113,.35)}}
.b-build{{background:rgba(255,140,66,.16);color:var(--build);border:1px solid rgba(255,140,66,.4)}}
.cnt{{display:inline-grid;place-items:center;min-width:30px;height:20px;padding:0 6px;font-size:11.5px;font-weight:700;
color:var(--txt);background:#39406a;border-radius:20px;flex:0 0 auto}}
.pillar b{{flex:1;font-weight:600}}
.intent{{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;padding:2px 7px;border-radius:20px;flex:0 0 auto}}
.i-informational{{background:#1e2a44;color:#7fa8ff}} .i-commercial{{background:#2a2340;color:#c79bff}}
.i-comparison{{background:#2a2036;color:#ff9bce}} .i-mixed{{background:#22314a;color:#8fd0ff}}
.hub{{color:var(--mut);font-size:13px;margin:2px 16px 12px;border-left:3px solid var(--line);padding-left:12px}}
.spokes{{display:flex;flex-wrap:wrap;gap:6px;padding:2px 14px 13px}}
.spoke{{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:var(--mut);background:#141830;border:1px solid var(--line);border-radius:6px;padding:3px 8px;text-decoration:none}}
.spoke:hover{{color:var(--txt);border-color:var(--accent)}}
.foot{{color:var(--mut);font-size:12px;margin-top:24px;border-top:1px solid var(--line);padding-top:14px}}
.st{{font-size:9.5px;font-weight:800;padding:3px 8px;border-radius:20px;letter-spacing:.3px;flex:0 0 auto}}
.st-working{{background:rgba(46,204,113,.16);color:#2ecc71;border:1px solid rgba(46,204,113,.4)}}
.st-weak{{background:rgba(120,220,180,.14);color:#7fe0b8;border:1px solid rgba(120,220,180,.35)}}
.st-orphan{{background:rgba(255,140,66,.16);color:#ff9d5c;border:1px solid rgba(255,140,66,.4)}}
.st-article{{background:rgba(108,140,255,.16);color:#8fb0ff;border:1px solid rgba(108,140,255,.4)}}
.st-partial{{background:rgba(255,193,7,.14);color:#ffcf4d;border:1px solid rgba(255,193,7,.35)}}
.st-missing{{background:rgba(255,99,99,.15);color:#ff8a8a;border:1px solid rgba(255,99,99,.4)}}
.hub-link{{font-family:ui-monospace,Menlo,monospace;font-size:11.5px}}
.covbar{{display:flex;gap:8px;flex-wrap:wrap;margin:0 16px 8px}}
.mini{{font-size:11px;font-weight:700;padding:3px 9px;border-radius:20px}}
.st-row-orphan>summary{{background:rgba(255,140,66,.05)}}
.st-row-missing>summary{{background:rgba(255,99,99,.05)}}
</style></head><body>
<header><h1>Testlify — Pillar &amp; Topic-Cluster Map</h1>
<div class="sub">Read by an LLM from the live sitemap, one post at a time · cap = 15 spokes/pillar · 2026-07-07</div></header>
<div class="wrap">
<div class="how"><b>How to read this:</b> 11 <b>THEMES</b> → <b>PILLARS</b> (≤15-post clusters) → the actual posts. Each pillar was
<b>live-checked twice</b>: does a hub page exist, AND does that hub actually link down to its cluster posts (its "children")?
A pillar only works if both are true.<br>
<span class="st st-working">PILLAR WORKING</span> hub exists &amp; links to its cluster &nbsp;
<span class="st st-orphan">PAGE EXISTS · 0 CLUSTER LINKS</span> page exists but links to none of its posts &nbsp;
<span class="st st-article">LEAD ARTICLE ONLY</span> one post, no hub &nbsp;
<span class="st st-partial">THIN PAGE ONLY</span> glossary/tool page &nbsp;
<span class="st st-missing">NO HUB</span> nothing.<br>
<b>Verdict: of 373 clusters, only a handful are working pillars — the rest either have no hub, or a page that never links to its cluster.</b>
</div>
<div class="stats">{stats_html}</div>
<input id="q" placeholder="Search a post slug, pillar or theme… (e.g. 'react', 'disc', 'onboarding', 'sales')">
<div class="hint" id="hint"></div>
{themes_html}
{orphan_html}
<div class="foot">Source: <code>data/final-clusters.json</code> — 373 pillars, every slug links to its live page.
Clusters were judged from post titles (slugs) by an LLM; a few posts may sit in a debatable pillar — edit the JSON to correct.
Rebuild with <code>python3 final_assemble.py &amp;&amp; python3 build_html.py</code>.</div>
</div>
<script>
const q=document.getElementById('q'),hint=document.getElementById('hint');
q.addEventListener('input',()=>{{
  const t=q.value.trim().toLowerCase();
  document.querySelectorAll('.theme').forEach(th=>{{
    if(!t){{th.style.display='';th.open=false;
      th.querySelectorAll('details').forEach(x=>x.open=false);
      th.querySelectorAll('.spoke,.pillar').forEach(x=>x.style.display='');return;}}
    let hit=false;
    th.querySelectorAll('.pillar').forEach(p=>{{
      const nameHit=p.querySelector('b').textContent.toLowerCase().includes(t);
      let spHit=false;
      p.querySelectorAll('.spoke').forEach(s=>{{
        const m=s.textContent.toLowerCase().includes(t);
        s.style.display=m?'':'none'; if(m)spHit=true;}});
      const show=nameHit||spHit; p.style.display=show?'':'none';
      if(show){{hit=true; p.open=spHit;
        if(nameHit&&!spHit)p.querySelectorAll('.spoke').forEach(s=>s.style.display='');}}
    }});
    const themeHit=th.querySelector('.ptitle').textContent.toLowerCase().includes(t);
    if(themeHit){{hit=true; th.querySelectorAll('.pillar').forEach(p=>p.style.display='');}}
    th.style.display=hit?'':'none'; th.open=hit;
  }});
  hint.textContent=t?`Filtering for “${{t}}”.`:'';
}});
</script></body></html>"""

open("pillar-cluster-map.html", "w").write(PAGE)
print(f"wrote pillar-cluster-map.html — {npil} pillars, {len(themes)} themes")
