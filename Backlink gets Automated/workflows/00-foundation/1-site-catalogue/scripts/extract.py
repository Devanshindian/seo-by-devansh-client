#!/usr/bin/env python3
"""The extractor stack + escalation ladder — turns cached pages into the catalogue.

Reads:  RECONCILED (reconciled.json) + the raw cache. OFFLINE by design: the only network rung is
        the optional Playwright render for SPA pages that have nothing in their HTML.
Writes: CATALOGUE_CSV (content-database.csv) — Traffic/Intent left blank; traffic.py fills them.

Two stages:

1. EXTRACT each page, keeping everything the page holds (menu, article, footer). The ladder is
   triggered by MEASURED OUTCOME only, never by a framework marker:
     rung 1  CMS body (WordPress REST) — used only when it is a fair SHARE of the live page
     rung 2  the stack over cached HTML (dom / trafilatura / resiliparse), keep the LONGEST
     rung 3  JSON-LD articleBody / <article> baseline
     rung 4  Playwright render (empty SPA roots only; one browser, many contexts)
     rung 5  body_status = failed  (NEVER silently blank)

2. DE-BOILERPLATE across the whole site, per language. A line that appears on >= DEBOILER_FRAC of a
   language's pages is site chrome (menu / header / footer) — a UNIQUE article sentence appears on
   one page only, so this can never delete real content. Per-language so a TRANSLATED menu (the
   Spanish menu on ~every Spanish page) is caught too. This is the whole cleaning step: extract
   keeps too much, then repetition — a fact, not a guess — decides what is chrome.
"""
import csv
import json
import os
import re
import signal
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy

from lxml import html as lxml_html

import config

# Semantic tags that never carry body text — dropped while serialising the DOM.
DROP_TAGS = {"script", "style", "noscript", "svg", "iframe", "form", "nav", "header", "footer",
             "template"}
# Block-level tags that force a line break when serialising (so headings/paragraphs stay separate).
_BLOCK_EL = {"p", "div", "section", "article", "li", "ul", "ol", "tr", "table", "h1", "h2", "h3",
             "h4", "h5", "h6", "br", "blockquote", "figcaption", "dt", "dd", "main", "aside",
             "pre", "figure"}
# Stripped BEFORE any text measurement — Next.js embeds huge JSON blobs in <script> that would
# otherwise be counted as page text.
_NOISE_TAGS = {"script", "style", "noscript", "template"}
EXTRACT_WORKERS = 4

# De-boilerplate: a line on >= this fraction of a LANGUAGE's pages is chrome, removed site-wide.
DEBOILER_FRAC = float(os.environ.get("CAT_DEBOILER_FRAC", "0.75"))
DEBOILER_MIN_PAGES = 8        # a language group smaller than this has too little repetition signal


# ---- text / DOM plumbing (runs inside worker processes) -------------------------------------

def _lines(text):
    return [ln.strip() for ln in (text or "").split("\n") if ln.strip()]


def _strip_noise(root):
    """Remove what a READER never sees: tags that hold no prose, and elements the page itself
    marks as not displayed. The second half matters — a page builder ships conditional blocks in
    the HTML and hides them, so an extractor that reads the markup picks up text no visitor ever
    sees. Measured 2026-07-19: 2,241 rows (21% of the sheet) carried the hidden editorial note
    'Conditional Psychometric Logo Section (Only shown for specific test)'. Hidden is a statement
    by the page about its own content, so honouring it is reading the page correctly, not guessing.
    """
    for el in list(root.iter()):
        if not isinstance(el.tag, str) or el.getparent() is None:
            continue
        if el.tag in _NOISE_TAGS:
            el.getparent().remove(el)
            continue
        style = (el.get("style") or "").replace(" ", "").lower()
        if ("display:none" in style or "visibility:hidden" in style
                or el.get("hidden") is not None
                or (el.get("aria-hidden") or "").lower() == "true"):
            el.getparent().remove(el)


def _mark_headings(root):
    """h1/h2/h3 -> inline '# ' / '## ' / '### ' markers. Downstream splits on these."""
    for level, tag in ((1, "h1"), (2, "h2"), (3, "h3")):
        for el in root.iter(tag):
            el.text = "#" * level + " " + (el.text or "")


def _dom_text(root):
    """Serialise a (marked) tree to text with block breaks and '- ' list bullets."""
    out = []
    def walk(n):
        tag = n.tag if isinstance(n.tag, str) else ""
        if tag in DROP_TAGS:
            out.append(n.tail or "")
            return
        if tag == "li":
            out.append("\n- ")
        elif tag in _BLOCK_EL:
            out.append("\n")
        out.append(n.text or "")
        for c in n:
            walk(c)
        if tag in _BLOCK_EL:
            out.append("\n")
        out.append(n.tail or "")
    walk(root)
    text = "".join(out)
    text = re.sub(r"[ \t\r\xa0]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _scope(doc):
    for xp in ("//main", "//*[@role='main']", "//article", "//body"):
        found = doc.xpath(xp)
        if found:
            return found[0]
    return doc


def _text_len(el):
    return len(" ".join(el.text_content().split()))


def _noise_stripped(doc):
    d = deepcopy(doc)
    _strip_noise(d)
    return d


# ---- the extractors -------------------------------------------------------------------------

def extract_dom(doc):
    """DOM serialiser: focus on the main region, keep everything it holds. Chrome is removed later
    by the de-boilerplate pass, not here — so no content is ever cut by a guess at this stage."""
    scope = deepcopy(_scope(doc))
    _mark_headings(scope)
    return _dom_text(scope)


def extract_trafilatura(html_str):
    import trafilatura
    return trafilatura.extract(
        html_str, output_format="markdown", include_comments=False,
        include_links=False, deduplicate=False, favor_recall=True) or ""


def extract_resiliparse(marked_html_str):
    from resiliparse.extract.html2text import extract_plain_text
    from resiliparse.process_guard import time_guard, ExecutionTimeout
    try:
        with time_guard(timeout=config.EXTRACT_TIMEOUT):
            return extract_plain_text(marked_html_str, main_content=True, alt_texts=False)
    except ExecutionTimeout:
        return ""


def extract_html2txt(marked_html_str):
    import trafilatura
    return trafilatura.html2txt(marked_html_str) or ""     # the floor — never returns None


def _jsonld_body(doc):
    best = ""
    def dig(o):
        nonlocal best
        if isinstance(o, dict):
            b = o.get("articleBody")
            if isinstance(b, str) and len(b) > len(best):
                best = b
            for v in o.values():
                dig(v)
        elif isinstance(o, list):
            for v in o:
                dig(v)
    for s in doc.xpath("//script[@type='application/ld+json']/text()"):
        try:
            dig(json.loads(s))
        except json.JSONDecodeError:
            continue
    return best.strip()


def _spa_root(doc):
    body = doc.xpath("//body")
    if not body:
        return False
    if len(" ".join(body[0].text_content().split())) >= 200:
        return False
    return bool(doc.xpath("//*[@id='root' or @id='app' or @id='__next' or @id='___gatsby']"))


def _marked_html(doc):
    d = deepcopy(doc)
    _mark_headings(d)
    return lxml_html.tostring(d, encoding="unicode")


def _meta(doc, rec):
    title = rec.get("title") or ""
    if not title:
        t = doc.xpath("//title/text()")
        title = t[0].strip() if t else ""
    desc = rec.get("description") or ""
    if not desc:
        m = doc.xpath("//meta[@name='description']/@content")
        desc = (m[0] or "").strip() if m else ""
    lang = (doc.xpath("//html/@lang") or [""])[0].strip()[:5]
    return title, desc, lang


# ---- body tidy (text-level, applied to every extractor's output) ----------------------------
# Rubbish that survives EVERY extractor because it is real text in the rendered page, not markup:
# page-builder placeholder tokens, bare CSS selectors, and the "Skip to content" skip-link that
# always sits immediately before a site's nav. None of it can be a sentence, so removing it by
# shape is safe.
_TEMPLATE_TOKEN_RE = re.compile(r"^\s*(?:\[/?element-\d+\]|\[/?et_pb_\w+\]|\.[a-z][\w-]{2,}"
                                r"|#[a-z][\w-]{2,}|\{[^}]*\}|/\*.*\*/)\s*$", re.I)
_SKIPLINK_RE = re.compile(r"^\s*skip to (?:content|main)", re.I)


def _tidy(text):
    if not text:
        return text
    lines = [ln.replace("\t", " ").rstrip() for ln in text.split("\n")]
    lines = [ln for ln in lines if not _TEMPLATE_TOKEN_RE.match(ln)]
    for i, ln in enumerate(lines[:80]):                   # cut a leading skip-link nav block
        if _SKIPLINK_RE.match(ln):
            for j in range(i + 1, len(lines)):
                s = lines[j].strip()
                if s.startswith("#") or len(s) > 60:
                    lines = lines[j:]
                    break
            break
    out, blank = [], 0
    for ln in lines:                                      # collapse whitespace runs
        if not ln.strip():
            blank += 1
            if blank > 1 or not out:
                continue
            out.append("")
        else:
            blank = 0
            out.append(ln)
    return "\n".join(out).strip()


def _status(body, extractor):
    if extractor in ("", "timeout") or extractor.startswith("error:"):
        return "failed" if len(body) < config.EXTRACT_FAIL_CHARS else "ok"
    if len(body) < config.EXTRACT_FAIL_CHARS:
        return "failed"
    if len(body) < config.EXTRACT_STUB_CHARS:
        return "stub"
    return "ok"


def _row(url, rec, body, extractor, title, desc, lang):
    body = _tidy(body)
    plain = re.sub(r"^#{1,3} ", "", body, flags=re.M)
    return {
        "URL": url, "Type": rec.get("type", ""), "Title": title,
        "Description": desc, "Full content": body,
        "canonical": rec.get("canonical_declared", ""),
        "word_count": len(plain.split()),
        "modified": rec.get("modified", ""), "lang": lang,
        "source": "+".join(rec.get("sources", [])),
        "extractor": extractor, "body_status": _status(body, extractor),
    }


class _Alarm(Exception):
    pass


def _worker(payload):
    """One page, inside a worker process, wall-clock-capped by SIGALRM (real kill — trafilatura's
    own timeout is signal-based, which is why this must be a PROCESS, not a thread)."""
    url, rec, live_html, rest_html = payload
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(_Alarm()))
    signal.alarm(config.EXTRACT_TIMEOUT * 3)
    try:
        return _extract_one(url, rec, live_html, rest_html)
    except _Alarm:
        return _row(url, rec, "", "timeout", "", "", "")
    except Exception as e:                        # a broken page must not kill the run
        return _row(url, rec, "", f"error:{type(e).__name__}", "", "", "")
    finally:
        signal.alarm(0)


def _extract_one(url, rec, live_html, rest_html):
    doc = None
    title = desc = lang = ""
    if live_html:
        try:
            doc = lxml_html.fromstring(live_html)
        except Exception:
            doc = None
    if doc is not None:
        title, desc, lang = _meta(doc, rec)
    else:
        title, desc = rec.get("title", ""), rec.get("description", "")

    # rung 1 — the CMS body. PREFERRED but never trusted blindly: on a page-builder site the CMS
    # field often holds only a FRAGMENT (commonly just the FAQ) while the real page is assembled at
    # render time. Keep it only when it is a fair SHARE of what the live page holds; else fall
    # through. Ties go to the CMS body — it is cleaner by construction.
    rest_body = ""
    if rest_html and rest_html.strip():
        try:
            frag = lxml_html.fromstring(rest_html)
            _mark_headings(frag)
            rest_body = _dom_text(frag)
        except Exception:
            rest_body = ""
        if len(rest_body) >= config.EXTRACT_FAIL_CHARS and (
                doc is None or len(rest_body) >= config.REST_MIN_SHARE * _text_len(doc)):
            return _row(url, rec, rest_body, "rest", title, desc, lang)

    # rung 2 — the stack over the noise-stripped DOM; keep the LONGEST (all keep-everything, so
    # longest = most complete). The CMS body stays in the running as a floor.
    best, best_name = (rest_body, "rest") if len(rest_body) >= config.EXTRACT_FAIL_CHARS else ("", "")
    if doc is not None:
        clean = _noise_stripped(doc)
        marked = _marked_html(clean)
        for name, text in (("dom", extract_dom(clean)),
                           ("trafilatura", extract_trafilatura(lxml_html.tostring(clean, encoding="unicode"))),
                           ("resiliparse", extract_resiliparse(marked))):
            if len(text) > len(best):
                best, best_name = text, name

        # rung 3 — JSON-LD articleBody / bare <article> baseline
        if len(best) < config.EXTRACT_FAIL_CHARS:
            jb = _jsonld_body(doc)
            if len(jb) > len(best):
                best, best_name = jb, "jsonld"
            art = clean.xpath("//article")
            if art:
                a = deepcopy(art[0])
                _mark_headings(a)
                at = _dom_text(a)
                if len(at) > len(best):
                    best, best_name = at, "article"

        # floor — raw html2txt, last resort only
        if len(best) < config.EXTRACT_FAIL_CHARS:
            h = extract_html2txt(marked)
            if len(h) > len(best):
                best, best_name = h, "html2txt"

        # rung 4 — empty SPA root -> hand to the Playwright pass (parent decides)
        if len(best) < config.EXTRACT_FAIL_CHARS and _spa_root(doc):
            row = _row(url, rec, best, best_name or "none", title, desc, lang)
            row["body_status"] = "spa_candidate"
            return row

    return _row(url, rec, best, best_name or "none", title, desc, lang)


# ---- parent orchestration (offline over the cache) ------------------------------------------

def _rest_bodies(pages):
    """link -> content.rendered, re-read OFFLINE from the cached WP API pages."""
    import fetch
    from reconcile import _store_norm
    api_pages = sorted({rec.get("api_page") for rec in pages.values() if rec.get("api_page")})
    bodies = {}
    for ap in api_pages:
        r = fetch.get(ap)                          # cache — zero network
        try:
            items = json.loads(r.text)
        except json.JSONDecodeError:
            continue
        for it in items if isinstance(items, list) else []:
            link = _store_norm(it.get("link", ""))
            body = ((it.get("content") or {}).get("rendered", "")) or ""
            if link and body:
                bodies[link] = body
    return bodies


def _render_spa(urls):
    """Rung 4: real browser render, one browser, many contexts. Lazy — most sites never get here."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(f"   !! {len(urls)} SPA pages need Playwright: pip install playwright && "
              f"playwright install chromium — marking them failed for now")
        return {}
    rendered = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for url in urls:
            ctx = browser.new_context(user_agent=config.USER_AGENT)
            page = ctx.new_page()
            page.route("**/*", lambda route: route.abort()
                       if route.request.resource_type in ("image", "font", "media")
                       else route.continue_())
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_selector("main, article, h1", timeout=10000)
                rendered[url] = page.content()
            except Exception as e:
                print(f"   !! render failed: {url} ({type(e).__name__})")
            finally:
                ctx.close()
        browser.close()
    return rendered


# The concatenated language-switcher line (a run of language names glued together) and a lone
# language-code line ("EN", "ES") vary page to page, so line-frequency misses them — dropped by shape.
_SWITCHER_RE = re.compile(r"^(?:Dansk|Deutsch|English|Españ|Franç|Italiano|日本語|"
                          r"Nederlands|Norsk|Polski|Portugu|Svenska){2,}", re.U)


def _is_switcher(line):
    return (len(line) <= 3 and line.isupper()) or (" " not in line and bool(_SWITCHER_RE.match(line)))


def _lang_key(row):
    la = (row.get("lang") or "").strip().lower()[:2]
    if la:
        return la
    m = re.match(r"https?://[^/]+/([a-z]{2})/", row["URL"])
    return m.group(1) if m else "en"


def _deboilerplate(rows):
    """Remove site chrome by REPETITION, per language. A line on >= DEBOILER_FRAC of a language's
    pages is menu/header/footer; a unique article sentence is on one page and can never be removed.
    Mutates each row's Full content, then re-derives word_count and body_status from the result."""
    import collections
    groups = collections.defaultdict(list)
    for r in rows:
        groups[_lang_key(r)].append(r)
    total_removed = 0
    for la, grp in sorted(groups.items()):
        if len(grp) < DEBOILER_MIN_PAGES:
            continue
        freq = collections.Counter()
        for r in grp:
            for ln in set(_lines(r["Full content"])):
                freq[ln] += 1
        cutoff = max(5, int(DEBOILER_FRAC * len(grp)))
        boiler = frozenset(ln for ln, c in freq.items() if c >= cutoff)
        for r in grp:
            kept = [ln for ln in _lines(r["Full content"])
                    if ln not in boiler and not _is_switcher(ln)]
            r["Full content"] = _tidy("\n".join(kept))
        total_removed += len(boiler)
        print(f"   de-boilerplate [{la}]: removed {len(boiler)} repeated lines across {len(grp)} pages")
    for r in rows:                                        # re-derive from the cleaned body
        plain = re.sub(r"^#{1,3} ", "", r["Full content"], flags=re.M)
        r["word_count"] = len(plain.split())
        if r["body_status"] in ("ok", "stub", "flagged"):
            r["body_status"] = _status(r["Full content"], r["extractor"])
    print(f"   de-boilerplate: {total_removed} chrome lines removed in total")


def run():
    import fetch
    rec_doc = json.load(open(config.RECONCILED))
    pages = rec_doc["pages"]
    workers = int(os.environ.get("CAT_EXTRACT_WORKERS", EXTRACT_WORKERS))
    print(f"   {len(pages)} pages to extract (offline, {workers} processes)")

    rest = _rest_bodies(pages)
    print(f"   REST bodies available for {len(rest)} pages")

    def payload(url, rec):
        # OFFLINE by contract — reconcile already fetched every page into the raw cache, so read the
        # CACHE, never the network. A page absent from the cache is one reconcile could not get; its
        # body_status records that. (A live fetch here could hit a permanently-forbidden URL and
        # stall the whole stage cooling down a global rate bucket over one page.)
        hit = fetch._cached(url)
        r = hit[0] if hit else None
        live = (r.content if r and r.status == 200
                and "html" in (r.content_type or "").lower() else None)
        return (url, rec, live, rest.get(url))

    rows, spa = [], []
    def collect(row, i):
        (spa if row["body_status"] == "spa_candidate" else rows).append(row)
        if i % 500 == 0:
            print(f"   .. {i}/{len(pages)}")
    if workers <= 1:
        for i, (u, rec) in enumerate(pages.items(), 1):
            collect(_worker(payload(u, rec)), i)
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_worker, payload(u, rec)): u for u, rec in pages.items()}
            for i, fut in enumerate(as_completed(futs), 1):
                collect(fut.result(), i)

    if spa:
        print(f"   {len(spa)} SPA candidates -> Playwright rung")
        rendered = _render_spa([r["URL"] for r in spa])
        for row in spa:
            html = rendered.get(row["URL"])
            if html:
                row2 = _extract_one(row["URL"], pages[row["URL"]], html.encode(), None)
                row2["extractor"] = "playwright"
                rows.append(row2)
            else:
                row["body_status"] = "failed"
                rows.append(row)

    # STAGE 2 — de-boilerplate the whole site, per language (the one cleaning step)
    _deboilerplate(rows)

    # flag pages whose body is far below their type's median (a single global % hides this)
    med = {t: (statistics.median(lens) if lens else 0) for t, lens in _group_lens(rows).items()}
    for row in rows:
        m = med.get(row["Type"], 0)
        if row["body_status"] == "ok" and m and len(row["Full content"]) < config.FLAG_MEDIAN_FRAC * m:
            row["body_status"] = "flagged"

    rows.sort(key=lambda r: r["URL"])
    cols = ["URL", "Type", "Title", "Description", "Full content", "Traffic", "Intent",
            "canonical", "word_count", "modified", "lang", "source", "extractor", "body_status"]
    def write(f):
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in rows:
            w.writerow({**{c: "" for c in cols}, **row})
    config._atomic_write(config.CATALOGUE_CSV, write)

    n_ok = sum(1 for r in rows if r["body_status"] in ("ok", "stub"))
    print(f"   wrote {len(rows)} rows -> {config.CATALOGUE_CSV}")
    print(f"   bodies: {n_ok} ok/stub, "
          f"{sum(1 for r in rows if r['body_status'] == 'flagged')} flagged, "
          f"{sum(1 for r in rows if r['body_status'] == 'failed')} failed")


def _group_lens(rows):
    g = {}
    for row in rows:
        if row["body_status"] in ("ok", "stub"):
            g.setdefault(row["Type"], []).append(len(row["Full content"]))
    return g


if __name__ == "__main__":
    run()
