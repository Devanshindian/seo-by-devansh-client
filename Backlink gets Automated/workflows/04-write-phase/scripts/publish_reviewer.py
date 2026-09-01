#!/usr/bin/env python3
"""PUBLISH the finished articles to the reviewer's public link.

  COMPANY=<slug> python3 publish_reviewer.py [--dry-run]

Reads:  writer/draft.md for every finished slug, and writer/_work/polish.json for the
        "Every source" tab (the article before the linking step curated its sources down).
Writes: <stage>/reviewer/_pages-repo/, then commits and pushes.

WHERE IT PUBLISHES is decided by the push clone's git remote, never by anything hardcoded here.
Clone the Pages repo into <stage>/reviewer/_pages-repo once; after that this always lands in the
same place, so the link already sent to a reviewer keeps working.

WHY IT LIVES HERE. It ran from a scratch folder for its first few weeks, and the scratch folder is
wiped between sessions — so the one command needed to update a link people already hold went
missing exactly when it was next wanted. A tool that ships work to someone outside belongs with the
engine that makes the work.

TWO PAGES PER ARTICLE, and no version chooser. The readability rewrite used to run after assemble
and write a second draft beside the first, so the site offered Version 0 and Version 1. It is now
step 5 of the writer, so there is only ONE finished article and the chooser has nothing to choose
between. The old urls (<slug>-v1.html, v0.html, v1.html) still resolve onto the current article, so
nothing already sent out breaks.
"""
import argparse
import html
import os
import re
import shutil
import subprocess

import config
import build_share_site as share
import build_stage_reads as reads
import review_page
import assemble

PHASE = os.path.dirname(config.WRITE_OUT)
SHARE = os.path.join(PHASE, "share")
REPO = os.path.join(PHASE, "reviewer", "_pages-repo")

TABS_CSS = """
.tabs{max-width:760px;margin:0 auto;padding:16px 24px 0;display:flex;gap:8px;flex-wrap:wrap}
.tabs a{display:inline-block;padding:8px 15px;border-radius:999px;font-size:13.5px;font-weight:600;
 text-decoration:none;color:var(--mut);background:var(--wash);border:1px solid var(--line)}
.tabs a:hover{color:var(--ink);border-color:var(--acc)}
.tabs a.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.tabs .home{margin-left:auto;background:none;border:none;color:var(--acc)}
.whatis{max-width:760px;margin:0 auto 6px;padding:16px 24px 0;color:var(--mut);font-size:15px}
"""

BLURB = {
    "art": "The finished article, exactly as it would publish.",
    "src": "The same article before the linking step, showing every source it drew on rather than "
           "only the handful the finished page credits.",
}


def _tabs(slug, now):
    on = ' class="on"'
    return ('<div class="tabs">'
            f'<a href="{slug}.html"{on if now == "art" else ""}>The article</a>'
            f'<a href="{slug}-before-links.html"{on if now == "src" else ""}>Every source</a>'
            '<a class="home" href="index.html">all articles</a></div>')


def _wrap(title, tabs, blurb, body):
    p = share._page(title, body, nav=tabs + f'<p class="whatis">{html.escape(blurb)}</p>')
    return p.replace("</style>", TABS_CSS + "</style>")


def build():
    os.makedirs(REPO, exist_ok=True)
    # Filter on the DRAFT, never on the share page: share/ keeps the last build, so an article that
    # did not finish this run still has a stale page there and would publish yesterday's text.
    slugs = [s for s in sorted(os.listdir(config.WRITE_OUT))
             if os.path.exists(config.artifact(s, "draft.md"))]
    # AN ARTICLE MID-REBUILD HAS NO DRAFT, AND MUST NOT VANISH FROM THE INDEX (2026-08-26).
    # A run deletes writer/ before rebuilding it, so publishing halfway through would drop those
    # articles from the contents page and 404 every link already sent for them. Anything already
    # live that has no draft right now keeps the page it has, and stays listed.
    live = {f[:-5] for f in os.listdir(REPO) if f.endswith(".html")} if os.path.isdir(REPO) else set()
    holding = [s for s in sorted(os.listdir(config.WRITE_OUT))
               if s not in slugs and s in live]
    for s in holding:
        print(f"  {s}: mid-rebuild — keeping the page already published")
    cards = []
    for slug in slugs:
        md = open(config.artifact(slug, "draft.md")).read()
        h1, body_md, srcs = share._split(md)
        words = len(body_md.split())
        n_sec = len(re.findall(r"^##\s+", body_md, re.M)) - len(share._extra_h2s(slug, body_md))

        art = (f"<h1>{html.escape(h1)}</h1>"
               f'<p class="meta">{words:,} words &middot; {n_sec} sections &middot; {len(srcs)} sources</p>'
               + share._faq_details(share._cite_links(review_page._md_to_html(body_md), srcs))
               + share._srcs_block(srcs))
        page = _wrap(h1, _tabs(slug, "art"), BLURB["art"], art)
        for name in (f"{slug}.html", f"{slug}-v1.html"):     # the old url still resolves
            config.write_text(os.path.join(REPO, name), page)
        sp = os.path.join(SHARE, f"{slug}.md")
        if os.path.exists(sp):
            shutil.copy(sp, os.path.join(REPO, f"{slug}.md"))

        pre = reads._stage_md(slug, "polish.json", "full")
        if pre and pre.strip():
            numbered, psrcs = reads._number_refs(pre, assemble._card_index(slug))
            body = (f"<h1>{html.escape(h1)}</h1>"
                    f'<p class="meta">{len(numbered.split()):,} words &middot; '
                    f'{len(psrcs)} sources</p>'
                    + share._faq_details(share._cite_links(review_page._md_to_html(numbered), psrcs))
                    + share._srcs_block(psrcs))
            config.write_text(os.path.join(REPO, f"{slug}-before-links.html"),
                              _wrap(f"{h1} — every source", _tabs(slug, "src"), BLURB["src"], body))
        cards.append({"slug": slug, "h1": h1, "w": words, "s": n_sec, "src": len(srcs)})
        print(f"  {slug}: {words:,}w, {n_sec} sections, {len(srcs)} sources")

    # A held-back article keeps its card, read back off the page already on the site, so the
    # contents page still lists it while its rebuild finishes.
    for s in holding:
        try:
            page = open(os.path.join(REPO, f"{s}.html")).read()
        except OSError:
            continue
        h1 = re.search(r"<h1>(.*?)</h1>", page, re.S)
        meta = re.search(r'<p class="meta">(.*?)</p>', page, re.S)
        cards.append({"slug": s, "held": True,
                      "h1": re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else s,
                      "meta_html": meta.group(1) if meta else "being rebuilt"})

    def card(c):
        n = (c["meta_html"] if c.get("held") else
             f'{c["w"]:,} words &middot; {c["s"]} sections &middot; {c["src"]} sources')
        return (f'<div class="card"><h3>{html.escape(c["h1"])}</h3>'
                f'<p class="n">{n}</p>'
                f'<div class="go"><a class="p" href="{c["slug"]}.html">Read it</a>'
                f'<a href="{c["slug"]}-before-links.html">Every source</a>'
                f'<a href="{c["slug"]}.md" download>Markdown</a></div></div>')

    rows = "".join(card(c) for c in cards)
    idx = share._page(f"{config.BRAND} articles for review",
                      f'<h1>{html.escape(config.BRAND)} articles for review</h1>'
                      '<p class="lead">Each one is shown as it would publish. Every source marker in '
                      'the text is a link, and the full list sits at the foot of the article. '
                      '<b>Every source</b> shows the same piece before the linking step, with every '
                      'source it drew on.</p>'
                      f'<div class="cards">{rows}</div>')
    for name in ("index.html", "v0.html", "v1.html"):        # old chooser urls still resolve
        config.write_text(os.path.join(REPO, name), idx)
    return len(cards)


def push(n, message):
    if not os.path.isdir(os.path.join(REPO, ".git")):
        print(f"  !! no push clone at {REPO} — clone the Pages repo there first")
        return
    subprocess.run(["git", "add", "-A"], cwd=REPO, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO).returncode == 0:
        print("  nothing changed since the last push")
        return
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=REPO, check=True)
    subprocess.run(["git", "push", "-q"], cwd=REPO, check=True)
    url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=REPO,
                         capture_output=True, text=True).stdout.strip()
    m = re.search(r"github\.com/([^/]+)/([^/\s]+?)(?:\.git)?$", url)
    print(f"  -> https://{m.group(1).lower()}.github.io/{m.group(2)}/" if m else f"  -> pushed to {url}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Publish the finished articles to the reviewer's link.")
    ap.add_argument("--dry-run", action="store_true", help="build the pages, do not push")
    ap.add_argument("-m", "--message", default="The finished articles, rebuilt")
    a = ap.parse_args()
    n = build()
    if a.dry_run:
        print(f"  built {n} article(s) into {REPO} — not pushed")
    else:
        push(n, a.message)
