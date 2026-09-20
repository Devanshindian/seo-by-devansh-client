#!/usr/bin/env python3
"""THE REVIEWER SITE — one public link, two tabs per article.

  COMPANY=<slug> python3 build_reviewer_site.py [--publish]

The share site (build_share_site.py) shows the finished article and nothing else. A reviewer
checking our sourcing needs one more view: the article as it stood BEFORE the links step, when every
citation is still there and nothing has been turned into an internal link yet. Comparing the two is
how you see what the links step spent and what it left alone.

So every article here gets two tabs:

  Before links   — the article out of the slop pass (writer/_work/polish.json), the exact text the
                   links step is handed. Every source it drew on, numbered and clickable.
  The article    — writer/draft.md, exactly as it would publish: internal links laid in, the
                   curated external sources anchored, the same full source list at the foot.

Reads:  writer/_work/polish.json + writer/draft.md, per slug under WRITE_OUT.
Writes: <stage>/reviewer/index.html + <slug>.html + <slug>-before-links.html
        --publish also pushes that folder to the GitHub Pages repo in reviewer/_pages-repo.

Read-only over the run: it opens finished output and writes pages. It never runs a writer step.
"""
import argparse
import html
import json
import os
import re
import subprocess

import config
import build_share_site as share
import build_stage_reads as reads
import review_page
import assemble

TITLE = "Testlify articles for review"

TABS_CSS = """
.tabs{max-width:760px;margin:0 auto;padding:16px 24px 0;display:flex;gap:8px;flex-wrap:wrap}
.tabs a{display:inline-block;padding:8px 15px;border-radius:999px;font-size:13.5px;font-weight:600;
 text-decoration:none;color:#6b6459;background:#f3ede1;border:1px solid #e7dcc7}
.tabs a:hover{color:#1c1a17;border-color:#fb7a00}
.tabs a.on{background:#1c1a17;color:#fff;border-color:#1c1a17}
.tabs .home{margin-left:auto;background:none;border:none;color:#fb7a00}
.whatis{max-width:760px;margin:0 auto 6px;padding:16px 24px 0;color:#6b6459;font-size:15px}
"""

VIEWS = [
    ("before-links", "Before links", "polish.json",
     "The article as the links step received it. Nothing has been turned into a link yet, so every "
     "source the piece draws on is here, numbered and clickable."),
    ("article", "The finished article", None,
     "Exactly as it would publish: internal links laid in, the curated external sources anchored, "
     "and the full source list at the foot."),
]


def _tabs(slug, now):
    bits = []
    for key, label, _, _ in VIEWS:
        href = f"{slug}.html" if key == "article" else f"{slug}-{key}.html"
        cls = ' class="on"' if key == now else ""
        bits.append(f'<a href="{html.escape(href)}"{cls}>{html.escape(label)}</a>')
    bits.append('<a class="home" href="index.html">all articles</a>')
    return f'<div class="tabs">{"".join(bits)}</div>'


def _page(title, tabs, blurb, body):
    p = share._page(title, body, nav=tabs + f'<p class="whatis">{html.escape(blurb)}</p>')
    return p.replace("</style>", TABS_CSS + "</style>")


def build_one(slug, out_dir, idx):
    """Both tabs for one article. Returns its index-card data, or None when it has not finished."""
    draft = config.artifact(slug, "draft.md")
    if not os.path.exists(draft):
        print(f"  (skipping {slug} — no draft yet)")
        return None

    # ---- tab 2: the finished article -------------------------------------
    h1, body_md, srcs = share._split(open(draft).read())
    words = len(body_md.split())
    # Match the share site exactly: the FAQ and the close have headings but are not sections.
    n_sec = len(re.findall(r"^##\s+", body_md, re.M)) - len(share._extra_h2s(slug, body_md))
    # The keyword scorecard belongs on the reviewer's copy, not the client's (2026-09-04).
    art = (f"<h1>{html.escape(h1)}</h1>" + share._kw_block(slug, words)
           + share._cite_links(review_page._md_to_html(body_md), srcs)
           + share._srcs_block(srcs))
    config.write_text(os.path.join(out_dir, f"{slug}.html"),
                      _page(h1, _tabs(slug, "article"), VIEWS[1][3], art))

    # ---- tab 1: the same article before the links step -------------------
    pre_md = reads._stage_md(slug, "polish.json", "full")
    n_pre = 0
    if pre_md and pre_md.strip():
        numbered, pre_srcs = reads._number_refs(pre_md, idx)
        n_pre = len(pre_srcs)
        pre = (f"<h1>{html.escape(h1)}</h1>"
               + share._cite_links(review_page._md_to_html(numbered), pre_srcs)
               + share._srcs_block(pre_srcs))
        config.write_text(os.path.join(out_dir, f"{slug}-before-links.html"),
                          _page(f"{h1} — before links", _tabs(slug, "before-links"), VIEWS[0][3], pre))

    print(f"  {slug}: {words:,}w · {n_sec} sections · {len(srcs)} sources "
          f"(before links: {n_pre})")
    return {"slug": slug, "h1": h1, "words": words, "secs": n_sec, "srcs": len(srcs)}


def build(slugs=None, out_dir=None):
    root = config.WRITE_OUT
    if not slugs:
        slugs = [s for s in sorted(os.listdir(root))
                 if os.path.exists(os.path.join(root, s, "writer", "draft.md"))]
        slugs.sort(key=lambda s: os.path.getmtime(os.path.join(root, s, "writer", "draft.md")),
                   reverse=True)
    out_dir = os.path.abspath(out_dir or os.path.join(root, "..", "reviewer"))
    os.makedirs(out_dir, exist_ok=True)

    cards = []
    for s in slugs:
        c = build_one(s, out_dir, assemble._card_index(s))
        if c:
            cards.append(c)

    body = [f'<h1>{html.escape(TITLE)}</h1>',
            '<p class="lead">Each article opens on two tabs. <b>Before links</b> is the piece as our '
            'linking step received it, with every source it drew on numbered and clickable. '
            '<b>The finished article</b> is what would publish. Every source marker in either view '
            'is a link, and the full list sits at the foot of the page.</p>',
            '<div class="cards">']
    for c in cards:
        body.append(
            f'<div class="card"><h3>{html.escape(c["h1"])}</h3>'
            f'<p class="n">{c["words"]:,} words &middot; {c["secs"]} sections &middot; '
            f'{c["srcs"]} sources</p>'
            f'<div class="go"><a class="p" href="{c["slug"]}.html">The finished article</a>'
            f'<a href="{c["slug"]}-before-links.html">Before links</a></div></div>')
    body.append("</div>")
    config.write_text(os.path.join(out_dir, "index.html"), share._page(TITLE, "".join(body)))
    print(f"  -> {out_dir}/index.html  ({len(cards)} article(s))")
    return out_dir, cards


def publish(out_dir, message, cards=None):
    """Copy the built pages into the push clone and push. The clone's remote is the single source of
    truth for WHERE this publishes — nothing here hardcodes a repo."""
    repo = os.path.join(out_dir, "_pages-repo")
    if not os.path.isdir(os.path.join(repo, ".git")):
        print(f"  !! no push clone at {repo} — clone the Pages repo there first, then re-run")
        return None
    # Copy ONLY what this build produced. Copying the whole folder published three retired
    # articles at guessable URLs, long after they were dropped from the index.
    want = {"index.html"}
    if not cards:                                    # nothing to filter against: copy as before
        want = None
    for c in cards or []:
        want |= {f'{c["slug"]}.html', f'{c["slug"]}.md', f'{c["slug"]}-before-links.html'}
    for f in os.listdir(out_dir):
        if f.endswith((".html", ".md")) and (want is None or f in want):
            config.write_text(os.path.join(repo, f), open(os.path.join(out_dir, f)).read())
    if cards:                                        # and drop what is no longer ours
        for f in os.listdir(repo):
            if f.endswith((".html", ".md")) and f not in want:
                os.remove(os.path.join(repo, f))
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo).returncode == 0:
        print("  nothing changed since the last push")
        return repo
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True)
    subprocess.run(["git", "push"], cwd=repo, check=True)
    url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=repo,
                         capture_output=True, text=True).stdout.strip()
    m = re.search(r"github\.com/([^/]+)/([^/\s]+?)(?:\.git)?$", url)
    if m:
        print(f"  -> https://{m.group(1).lower()}.github.io/{m.group(2)}/")
    return repo


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build (and optionally publish) the reviewer site.")
    ap.add_argument("--slugs", nargs="*")
    ap.add_argument("--out")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("-m", "--message", default="Every article on two tabs: before links, and finished")
    a = ap.parse_args()
    d, built = build(a.slugs, a.out)
    if a.publish:
        publish(d, a.message, built)
