#!/usr/bin/env python3
"""Writer Step 6 — LINKS: internal links, read-more pointers, and the curated external links.

Reads:  writer/_work/polish.json (the cleaned article; falls back to wrapper.json)
        + gather/plan-inputs.json (cards + the research-matched internal links; bundle fallback)
        + the company's embedded site index (projects/<co>/02-asset-engine/clubbed/_work/content-index)
        + the company's competitor list (projects/<co>/02-asset-engine/competitor-study/output/competitors.md)
Writes: writer/_work/linked.json      — the article with links laid in (assemble reads this first)
        writer/_work/links-report.json — every decision: used, rejected (with reasons), integrity
        writer/links-review.html      — the human page, grouped by pool

Three pools, three judges, everything else code:
  1. INLINE (3-5): candidates = own-brand urls on this article's cards + the research-matched
     list. The judge lays anchors over EXISTING words only.
  2. READ-MORE (0-2, usually 0): candidates = top-5 cosine matches of the article's fingerprint
     against the pre-embedded site index (voyage-4-large, built by the reuse-check work). The one
     added-line exception; may lightly smooth the two neighbouring sentences — every adjustment
     reported and audited.
  3. EXTERNAL (<=10): candidates = the article's own verified citations, competitors (direct list)
     and own-domain removed. Comparison articles keep competitor citations. The kept ten become
     the ONLY visible source links; the rest stay as internal provenance.

THE INTEGRITY CHECK (code): undo every declared insertion/adjustment and the text must equal the
pre-links article exactly. Anything undeclared -> that block is reverted and the failure logged.
"""
import argparse
import html as _html
import json
import os
import re
import sys
import subprocess
import time

import config
import llm
import tags


def _map_css():
    """The step map's styles, taken from eval_pages so one stylesheet defines it."""
    import eval_pages
    return eval_pages.MAP_CSS


def _map(now):
    """The same step map every other review page carries, so this page is never a dead end."""
    import eval_pages
    return eval_pages._nav(now)


def _reads():
    """The link to the clean read of the article as it stands after this step."""
    import eval_pages
    return eval_pages.reads_link("links")


_SHARED = os.path.join(config.WORKFLOWS, "02-asset-engine", "_shared")
_MDLINK = re.compile(r"\[([^\]\[]+)\]\((https?://[^)\s]+)\)")


# ---------------------------------------------------------------- inputs
def _company_dirs():
    proj = os.path.dirname(os.path.dirname(config.WRITE_OUT))          # projects/<company>
    return (os.path.join(proj, "02-asset-engine", "clubbed", "_work", "content-index", "title"),
            os.path.join(proj, "02-asset-engine", "competitor-study", "output", "competitors.md"))


def _site_index():
    """url -> title for every live page, + the embedding matrix. Built once by the reuse-check work."""
    idx_dir, _ = _company_dirs()
    meta, order = {}, []
    with open(os.path.join(idx_dir, "meta.jsonl")) as f:
        for line in f:
            d = json.loads(line)
            meta[d["url"]] = d.get("title") or ""
            order.append(d["url"])
    return meta, order, os.path.join(idx_dir, "vectors.npy")


def _own_domain(order):
    from collections import Counter
    host = Counter(u.split("/")[2] for u in order if "://" in u).most_common(1)
    dom = (config.TENANT.get("domain") or (host[0][0] if host else "")).lower()
    return dom.removeprefix("www.")


def _competitor_domains():
    """The DIRECT rivals only — adjacent audience sites (SHRM etc.) are prime citation targets."""
    _, comp_path = _company_dirs()
    if not os.path.exists(comp_path):
        return set()
    text = open(comp_path).read()
    direct = text.split("## Direct", 1)[-1].split("## ", 1)[0]
    return {m.group(1).lower() for m in re.finditer(r"\*\*([a-z0-9.-]+\.[a-z]{2,})\*\*", direct)}


def _fill(name, **kw):
    p = llm.load_prompt(name)
    for k, v in kw.items():
        p = p.replace("{{" + k + "}}", str(v))
    return p


def _article_text(w):
    parts = [("intro", w.get("intro") or "")]
    parts += [(s["heading"], s["prose"]) for s in w.get("sections") or []]
    # The KEY stays "close": _prose_of / _set_prose look blocks up by it. Only what a reader sees
    # gained a heading, and a heading is not editable prose, so it is deliberately not in this text.
    parts.append(("close", w.get("close") or ""))
    return parts


def _render_article(parts):
    return "\n\n".join(f"## {h}\n\n{t}" for h, t in parts)



# ---------------------------------------------------------------- judge 4: where a source is marked
def _citation_places(w, idx, cap):
    """Choose WHERE each over-cited source keeps its marker. Returns {card_id: {place indexes kept}}.

    Measured on the finished articles (2026-08-22): one source was marked 20 times in a single piece,
    another 19. A reader needs to know where a figure came from; they do not need telling twenty
    times, and the page stops reading as prose and starts reading as a reference list.

    Keeping the FIRST three would be code, and wrong: a source is often introduced in passing early
    and does its real work in the middle. So the choice is a judgment — but a tightly bounded one.
    Occurrences are NUMBERED on the way out and matched by number on the way back, so the reply can
    never be half-applied, and anything invalid falls back to keeping the first `cap`.

    Nothing is deleted. The [c] tags stay in the _work files and on the review pages; only the
    markers a reader sees are thinned.
    """
    places = {}                       # card_id -> [(block name, sentence)]
    for name, text in _article_text(w):
        for sent in re.split(r"(?<=[.!?])\s+", text or ""):
            for cid in tags.ids(sent):
                places.setdefault(cid, []).append((name, " ".join(sent.split())[:110]))

    over = {c: p for c, p in places.items() if len(p) > cap}
    if not over:
        return {}, 0

    blocks = []
    for cid, ps in sorted(over.items(), key=lambda kv: -len(kv[1])):
        gloss = ((idx.get(cid) or {}).get("gloss") or "")[:90]
        lines = [f"SOURCE {cid} — {gloss}", f"  marked in {len(ps)} places, keep at most {cap}:"]
        lines += [f"   {i}. \"{s}\"   (in: {b[:44]})" for i, (b, s) in enumerate(ps, 1)]
        blocks.append("\n".join(lines))

    reply = llm.call_json(_fill("citation-places.md", MAX=cap,
                                OCCURRENCES="\n\n".join(blocks))) or {}
    keep = {}
    srcs = reply.get("sources")
    for r in (srcs if isinstance(srcs, list) else []):
        if not isinstance(r, dict):
            continue                                  # a reply shaped wrong must never crash the step
        try:
            cid = int(r.get("source"))
        except (TypeError, ValueError):
            continue
        if cid not in over:
            continue
        want = [i for i in (r.get("keep") or []) if isinstance(i, int) and 1 <= i <= len(over[cid])]
        keep[cid] = set(sorted(want)[:cap]) if want else set(range(1, cap + 1))
    for cid in over:                                  # a source the judge skipped keeps the first N
        keep.setdefault(cid, set(range(1, cap + 1)))
    return keep, len(over)


# ---------------------------------------------------------------- read-more retrieval
_CATALOGUE = None


def _catalogue():
    """url -> the page's already-extracted text, from the site catalogue the crawl produced.

    Added 2026-08-05 after a plain question: why fetch a page we already read? The site catalogue
    holds Full content for every page — clean prose, headings intact, no CSS, no cookie banner. We
    were re-downloading each candidate over HTTP and mangling it, then judging the page a stub. Read
    once, cached for the process; the live fetch stays only as a fallback for a url not in it.
    """
    global _CATALOGUE
    if _CATALOGUE is not None:
        return _CATALOGUE
    _CATALOGUE = {}
    proj = os.path.dirname(os.path.dirname(config.WRITE_OUT))
    path = os.path.join(proj, "00-foundation", "output", "content-database.csv")
    if not os.path.exists(path):
        return _CATALOGUE
    import csv
    csv.field_size_limit(sys.maxsize)
    try:
        with open(path, newline="", encoding="utf-8", errors="ignore") as fh:
            r = csv.reader(fh)
            hdr = next(r)
            iu, ic = hdr.index("URL"), hdr.index("Full content")
            for row in r:
                if len(row) > ic and row[ic]:
                    _CATALOGUE[(row[iu] or "").rstrip("/")] = row[ic]
    except Exception as e:
        print(f"    (site catalogue unreadable: {str(e)[:60]})")
    return _CATALOGUE


def _fetch_excerpt(url, chars=2500):
    """The page's real opening text, so the depth judgment reads content rather than boilerplate.

    Rewritten 2026-08-05. The old version read the first 600KB and stripped <style>/<script> with a
    paired-tag regex. Testlify pages open with ~20 inline style blocks, so 600KB landed INSIDE one of
    them: the block had no closing tag to match, its CSS survived, and the article body was never
    reached. Every candidate therefore looked like a stub, and read-more rejected all five on every
    article — "opening is pure CSS", "only a cookie consent script". That was not a strict judge, it
    was a broken reader. Now: read enough, drop unclosed blocks too, and start from the real content
    container when the page has one.
    """
    cat = _catalogue().get(url.rstrip("/"))
    if cat and len(cat) > 300:
        return " ".join(cat.split())[:chars]                # already clean — no stripping needed
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh) Chrome/120"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read(3_000_000).decode("utf-8", "ignore")
    except Exception:
        return ""
    # jump to the real content container when there is one — skips the whole head and nav
    for tag in ("<article", "<main", 'class="entry-content"', 'class="post-content"'):
        i = raw.find(tag)
        if i > 0:
            raw = raw[i:]
            break
    raw = re.sub(r"<(script|style|nav|header|footer|svg|noscript)\b[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<(script|style|svg|noscript)\b[^>]*>.*", " ", raw, flags=re.S | re.I)   # unclosed, truncated
    raw = re.sub(r"<!--.*?-->", " ", raw, flags=re.S)
    text = " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())
    # a stray CSS rule that still slipped through is not prose — drop anything brace-heavy
    if text.count("{") > 5:
        text = re.sub(r"[^{}]*\{[^}]*\}", " ", text)
        text = " ".join(text.split())
    return text[:chars] if len(text) > 300 else ""


# Codes that mean "you are a bot", NOT "this page is gone". Academic publishers and news sites answer
# a scripted request with 403 while serving the identical url perfectly to a human browser. Treating
# those as dead silently deleted real citations: the Type D run dropped two ScienceDirect papers and a
# Tilburg University PDF, all three of which load fine in a browser. Only a genuine "not there"
# (404/410) or a failure to connect at all counts as dead.
_BOT_BLOCKED = {401, 403, 405, 406, 429, 451}


def _alive(url):
    """Does the link answer with a real page? (the checklist's every-link-returns-200 rule)"""
    import urllib.error
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh) Chrome/120"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.status < 400
    except urllib.error.HTTPError as e:
        if e.code in _BOT_BLOCKED:
            print(f"    (kept — HTTP {e.code} is a bot block, not a dead page: {url[:70]})")
            return True
        return False
    except Exception:
        return False



PRODUCT_PATHS = ("/pricing", "/test-library", "/coding-tests", "/personality-tests", "/skills-tests",
                 "/video-interviewing", "/calculator", "/alternatives", "/hr-glossary", "/templates")


def _is_product(u):
    return any(p in u.lower() for p in PRODUCT_PATHS)


def _rank_of(c):
    """The one number a candidate is ordered and floored by: the reranker's when we have it."""
    rr = c.get("rr")
    return float(rr) if rr is not None else float(c.get("sim") or 0.0)


def _body_best(Q, order, idx_dir):
    """Best body-chunk cosine per page, per section query. Returns (n_queries, n_pages), or None.

    The body index is ~33k chunks (~137MB as float32), so it is walked ONE part file at a time and
    reduced into a running per-page maximum. Nothing larger than a single part is ever resident.
    Best-chunk, not mean-chunk: a 4,000-word page covering six subjects should match on the one
    passage that is genuinely about this section, and averaging buries exactly that.
    """
    import numpy as np
    bdir = os.path.join(idx_dir, "body")
    pdir, mpath = os.path.join(bdir, "parts"), os.path.join(bdir, "meta.jsonl")
    if not (os.path.isdir(pdir) and os.path.exists(mpath)):
        return None
    pos = {u: i for i, u in enumerate(order)}
    best = np.zeros((Q.shape[0], len(order)), dtype=np.float32)
    seen = 0
    with open(mpath, encoding="utf-8") as mf:
        rows = (json.loads(l) for l in mf)
        for part in sorted(p for p in os.listdir(pdir) if p.endswith(".npy")):
            V = np.load(os.path.join(pdir, part), mmap_mode="r")
            cols = [pos.get((next(rows, None) or {}).get("url", ""), -1) for _ in range(V.shape[0])]
            Vn = np.nan_to_num(np.asarray(V, dtype=np.float32), posinf=0.0, neginf=0.0)
            Vn /= (np.linalg.norm(Vn, axis=1, keepdims=True) + 1e-9)     # meta order == concat order
            # errstate: macOS Accelerate raises a spurious divide-by-zero on this matmul. Checked on
            # the real index — all 33,434 chunk vectors are finite and so is the product. Silencing
            # the artifact only; the nan_to_num either side stays as the actual guard.
            with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                sims = np.nan_to_num(Q @ Vn.T)                           # (queries, chunks in this part)
            for j, p in enumerate(cols):
                if p >= 0:
                    np.maximum(best[:, p], sims[:, j], out=best[:, p])
            seen += V.shape[0]
    return best if seen else None


def _section_candidates(w, jobs, meta, order, vec_path, own, per=None):
    """Per-SECTION shortlist of pages to link to. Returns {section heading: [candidate, ...]}.

    Rebuilt 2026-08-05, replacing a whole-article search. That version glued every heading into one
    query, so a 17-section article got ONE blurry average of itself — the AI-policy section and the
    calibration section were mashed together and neither surfaced its own best pages. Each section
    now queries with its own heading + job, so the shortlist is actually about that section.

    Rebuilt again 2026-08-06. That version still scored against the TITLE index alone: one vector per
    page, built from the page's headline and nothing else. So a section heading was compared to a page
    headline and neither side ever carried a word of real content — which is how "work sample test"
    was handed the job-simulation page. It now runs the retrieval 02's reuse-check already proved on a
    49-asset ground truth: blend the title score with the best BODY-chunk score, then rerank the top
    LINK_N_RETRIEVE with rerank-2.5, a model that reads the query and the page together.

    Cost stays small: voyage.embed takes a list, so every section is still embedded in ONE batched
    call. Page text for the reranker comes from the site catalogue already on disk, so no page is
    downloaded here either.
    """
    import numpy as np
    sys.path.insert(0, _SHARED)
    import voyage
    per = per or config.LINK_PER_SECTION
    heads = [s_["heading"] for s_ in w.get("sections") or []]
    if not heads:
        return {}
    queries = [f"{h} — {jobs.get(h, '')}".strip(" —") for h in heads]
    Q = np.nan_to_num(np.array(voyage.embed(queries, input_type="query")))   # ONE call for all sections
    V = np.nan_to_num(np.load(vec_path))
    Vn = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):     # macOS BLAS artifact; see _body_best
        T = np.nan_to_num(Q @ Vn.T)                                         # (queries, pages) title score

    idx_dir = os.path.dirname(os.path.dirname(vec_path))
    B = _body_best(Q, order, idx_dir)
    if B is None:
        print("    !! no body index — falling back to TITLE-ONLY matching (weaker; rebuild 02's index)")
        blend = T
    else:
        a = config.LINK_ALPHA
        blend = a * T + (1 - a) * B
    print(f"    candidates: {'title+body blend' if B is not None else 'title only'}"
          f" -> top {config.LINK_N_RETRIEVE} -> rerank-2.5 -> {per}")

    skip = ("/login", "/signup", "/contact", "/about", "/careers", "/terms", "/privacy", "/cdn-cgi")
    cat = _catalogue()
    out, rerank_jobs = {}, []
    for qi, h in enumerate(heads):
        dense = []
        for i in np.argsort(-blend[qi]):
            u = order[i]
            t = meta.get(u, "")
            if not t or not t.isascii() or "%" in u or own not in u or any(b in u for b in skip):
                continue
            dense.append({"url": u, "title": t,
                          "sim": round(float(blend[qi][i]), 3),
                          "title_sim": round(float(T[qi][i]), 3),
                          "body_sim": round(float(B[qi][i]), 3) if B is not None else None,
                          "rr": None,
                          "kind": "product" if _is_product(u) else "article"})
            if len(dense) >= config.LINK_N_RETRIEVE:
                break
        out[h] = dense
        rerank_jobs.append((h, queries[qi], dense))

    def _rr(job):
        h, q, dense = job
        docs = [(cat.get(c["url"].rstrip("/")) or c["title"])[:config.LINK_RERANK_DOC_CHARS]
                for c in dense]
        if not docs:
            return h, dense
        try:
            # ALL of them, not just the top `per`. A partial rerank leaves the rest scored by the
            # dense blend, and the two scales overlap: on the strategic article the reranked winners
            # ran 0.37-0.50 while un-reranked blends reached 0.42, so sorting them together compared
            # two different measurements and could seat a blend-ranked page above a reranked one.
            for i, s in voyage.rerank(q, docs, len(docs)):
                dense[i]["rr"] = round(float(s), 3)
        except Exception as e:                       # a rerank hiccup must not lose the whole section
            print(f"    (rerank failed for {h[:40]!r}: {str(e)[:60]} — keeping dense order)")
        return h, dense

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=6) as ex:    # each section's rerank is an independent call
        for h, dense in ex.map(_rr, rerank_jobs):
            ranked = sorted(dense, key=_rank_of, reverse=True)[:per]
            kept = [c for c in ranked if _rank_of(c) >= config.LINK_MIN_SCORE]
            if len(kept) < len(ranked):
                print(f"    floor cut {len(ranked) - len(kept)} candidate(s) under "
                      f"{config.LINK_MIN_SCORE} for {h[:40]!r}")
            for c in kept:                           # the judge must SEE the page, not just its title
                c["excerpt"] = " ".join((cat.get(c["url"].rstrip("/")) or "").split())[:config.LINK_EXCERPT_CHARS]
            out[h] = kept
    return out


def _read_more_candidates(w, meta, order, vec_path, own, exclude):
    """Top-5 site pages by meaning. The article's fingerprint is the query — nobody writes one."""
    import numpy as np
    sys.path.insert(0, _SHARED)
    import voyage                                                     # the shared caller (voyage-4-large)
    fingerprint = " · ".join([w.get("h1") or ""] + [s["heading"] for s in w.get("sections") or []])
    q = np.array(voyage.embed([fingerprint], input_type="query")[0])
    V = np.load(vec_path)
    V = np.nan_to_num(V)
    q = np.nan_to_num(q)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):    # macOS BLAS artifact; see _body_best
        sims = np.nan_to_num(V @ q / (np.linalg.norm(V, axis=1) * np.linalg.norm(q) + 1e-9))
    bad_path = ("/pricing", "/login", "/signup", "/contact", "/about", "/careers", "/terms", "/privacy")
    out = []
    for i in np.argsort(-sims):
        u = order[i]
        t = meta.get(u, "")
        if u in exclude or "%" in u or not t or not t.isascii() or len(t) < 15:
            continue
        if own not in u or any(b in u for b in bad_path) or u.rstrip("/").count("/") <= 2:
            continue
        out.append({"url": u, "title": t, "sim": round(float(sims[i]), 3)})
        if len(out) == 5:
            break
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as ex:
        for c, exc in zip(out, ex.map(lambda c: _fetch_excerpt(c["url"]), out)):
            c["excerpt"] = exc
    return [c for c in out if c["excerpt"]]                 # a page that will not load cannot be judged


# ---------------------------------------------------------------- insertion + guards

_SMART = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
          "\u2013": "-", "\u2014": "-", "\u00a0": " "}


def _plain(t):
    """Typography-insensitive form for MATCHING only — never for output.

    A read-more pointer named the section "A Bad Hire's True Cost" with a straight apostrophe; the
    real heading has a curly one. The exact-match lookup failed and a correct, useful pointer was
    silently dropped. Same class of failure can kill an anchor. Match on this, insert the original.
    """
    for a, b in _SMART.items():
        t = t.replace(a, b)
    return " ".join(t.split())


def _mask_links(text):
    return _MDLINK.sub(lambda m: "\x00" * len(m.group(0)), text)


def _insert_anchor(prose, anchor, url):
    """Lay [.…](url) over the first occurrence of the anchor WORDS not already inside a link.
    Tolerant matching: case, hyphens and spacing may differ — but the linked text is always the
    article's own span, untouched. The judge's wording never replaces the article's wording."""
    parts = [re.escape(p) for p in re.split(r"[^0-9A-Za-z%$]+", anchor) if p]
    if not parts:
        return None
    # Separators between the anchor's words. The old class allowed only spaces, hyphens and
    # apostrophes, so any anchor containing a comma or a bracket could never match — four links on one
    # article were lost to exactly that: "RICE, ICE, MoSCoW, the Eisenhower Matrix" and
    # "behaviorally anchored rating scale (BARS)". Allow any short run of non-alphanumerics, but keep
    # it to 4 characters so it can never bridge a sentence break or a [c...] tag.
    rx = re.compile(r"[^0-9A-Za-z]{1,4}".join(parts), re.I)
    m = rx.search(_mask_links(prose))
    if not m:
        return None
    found = prose[m.start():m.end()]
    return prose[:m.start()] + f"[{found}]({url})" + prose[m.end():]


def _unlink(text):
    return _MDLINK.sub(lambda m: m.group(1), text)



def _free_mb():
    """Free + inactive memory in MB, from vm_stat. Returns None if it cannot be read."""
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
        page = int(re.search(r"page size of (\d+)", out).group(1))
        free = int(re.search(r"Pages free:\s+(\d+)", out).group(1))
        inact = int(re.search(r"Pages inactive:\s+(\d+)", out).group(1))
        return (free + inact) * page // (1024 * 1024)
    except Exception:
        return None


def _wait_for_memory(need_mb=1200, minutes=30):
    """This step loads the site's page embeddings and does a big matrix multiply. On a machine with
    almost nothing free, macOS KILLS the process outright — no exception, no traceback, the run just
    vanishes mid-article. That happened three times on 2026-08-05 and each time looked like a pipeline
    bug rather than what it was. So: check first, wait, and say so out loud."""
    waited = 0
    while True:
        mb = _free_mb()
        if mb is None or mb >= need_mb:
            if mb is not None and waited:
                print(f"  memory recovered ({mb} MB free) — continuing")
            return
        if waited >= minutes * 60:
            print(f"  !! still only {mb} MB free after {minutes} min — going ahead; if this step "
                  f"disappears with no error, that is the OS killing it, not a crash")
            return
        if waited == 0:
            print(f"  !! only {mb} MB free, need ~{need_mb} MB. WAITING — close some apps "
                  f"(browser tabs, editors) and this continues on its own.")
        time.sleep(20)
        waited += 20


def run(slug, redo=False):
    outp = config.artifact(slug, "linked.json")
    if not redo and config.fresh(outp, config.artifact(slug, "polish.json")):
        print(f"  reusing {outp}")
        return json.load(open(outp))
    _wait_for_memory()

    src = config.artifact(slug, "polish.json")
    if not os.path.exists(src):
        src = config.artifact(slug, "wrapper.json")
    w = json.load(open(src))
    st = json.load(open(config.artifact(slug, "structure.json")))
    meta, order, vec_path = _site_index()
    own = _own_domain(order)
    inp = json.load(open(config.artifact(slug, "plan-inputs.json")))

    # cards' own-brand urls + which cards each supports (for the external pool too)
    from collections import defaultdict
    url_cards, id2card = defaultdict(list), {}
    for s in inp["group_b"]["sections_menu"]:
        for c in list(s.get("evidence", [])) + [e for h in s.get("h3", []) for e in h.get("evidence", [])]:
            try:
                cid = int(str(c.get("card_id")).lower().replace("id", "").strip())
            except ValueError:
                continue
            id2card[cid] = c
    # The architect's ENRICHED cards (ids 9001+) were fetched fresh from the web for exactly the gaps
    # this article had, so they carry the newest and often the most authoritative urls we hold. They
    # live in their own file and were never loaded here, so every one of them was invisible to the
    # external-link judge — which is a large part of why a 8,600-word article shipped with 4 sources.
    _ep = config.artifact(slug, "enriched-cards.json")
    if os.path.exists(_ep):
        for _k, _c in json.load(open(_ep)).items():
            try:
                id2card[int(_k)] = _c
            except (TypeError, ValueError):
                continue
    used_ids = set()
    for _h, t in _article_text(w):
        used_ids |= tags.id_set(t)
    for cid in used_ids:
        c = id2card.get(cid)
        if c:
            for u in (c.get("source_urls") or [])[:1]:
                url_cards[u].append(c)

    article_md = _render_article(_article_text(w))

    # ---- JUDGE 1: inline internal links, SECTION BY SECTION -------------------
    # Each section gets its own shortlist (its heading + job as the query), then ONE call sees every
    # section together — so it can say "this page belongs to section 4, not section 9" and spread the
    # links out. A per-section call could not do that, and the old whole-article search could not
    # produce a shortlist worth choosing from.
    jobs = {}
    try:
        for s_ in json.load(open(config.artifact(slug, "structure.json"))).get("sections") or []:
            jobs[s_.get("headline") or ""] = (s_.get("job") or "")[:220]
    except Exception:
        pass
    per_sec = _section_candidates(w, jobs, meta, order, vec_path, own)
    # the article's own cited own-brand urls belong to whichever section cites them
    for name, txt in _article_text(w):
        for cid in tags.id_set(txt):
            c = id2card.get(cid)
            for u in (c.get("source_urls") or [])[:1] if c else []:
                if own in u.split("/")[2].lower() and name in per_sec:
                    if not any(x["url"] == u for x in per_sec[name]):
                        # the article already cites this page, so it is relevant by construction —
                        # scored 1.0 on both so it survives the floor and sorts to the front
                        per_sec[name].insert(0, {"url": u, "title": meta.get(u, ""), "sim": 1.0,
                                                 "title_sim": None, "body_sim": None, "rr": 1.0,
                                                 "excerpt": " ".join(
                                                     (_catalogue().get(u.rstrip("/")) or "").split()
                                                 )[:config.LINK_EXCERPT_CHARS],
                                                 "why_here": "this article already cites this page",
                                                 "kind": "product" if _is_product(u) else "article"})
    # every candidate's score, so a placed link can be audited afterwards: (section, url) -> candidate
    cand_by = {(h, c["url"]): c for h, cs in per_sec.items() for c in cs}
    blocks, cand_urls = [], set()
    for s_ in w.get("sections") or []:
        h = s_["heading"]
        cs = per_sec.get(h) or []
        cand_urls |= {c["url"] for c in cs}
        blocks.append(
            f"SECTION: {h}\n"
            f"WHAT IT MUST DELIVER: {jobs.get(h, '(not recorded)')}\n"
            f"ITS TEXT:\n{(s_.get('prose') or '')[:2600]}\n"
            f"PAGES SHORTLISTED FOR THIS SECTION:\n"
            + ("\n\n".join(
                f"  - [{c['kind'].upper()}] {c['url']} · {c['title'] or '(no title)'}\n"
                f"    MATCH SCORE: {_rank_of(c):.2f}"
                + (f" ({c['why_here']})" if c.get("why_here") else "")
                + "\n    WHAT IS ACTUALLY ON THAT PAGE: "
                + (c.get("excerpt") or "(page text unavailable — judge on the title alone, and be stricter)")
                for c in cs)
               or "  (none)"))
    n_prod = sum(1 for cs in per_sec.values() for c in cs if c["kind"] == "product")
    # The allowance SCALES WITH LENGTH. A flat "3 to 5" gave a 5,000-word article the same budget as a
    # 900-word one, and the rejection log showed good candidates dropped purely to stay under it.
    words = sum(len((s_.get("prose") or "").split()) for s_ in (w.get("sections") or []))
    want = max(config.MIN_INTERNAL_LINKS, round(words / config.WORDS_PER_INTERNAL_LINK))
    print(f"    inline: {len(per_sec)} sections shortlisted, "
          f"{len(cand_urls)} distinct candidates ({n_prod} product surfaces) | "
          f"{words:,}w -> aim for ~{want} link(s)")
    j1 = llm.call_json(_fill("inline-links.md", BRAND=config.BRAND,
                             HOW_MANY=want, HOW_MANY_LOW=max(config.MIN_INTERNAL_LINKS, want - 2),
                             WORDS=f"{words:,}",
                             SECTIONS="\n\n────────────────────────────────────────\n\n".join(blocks))) or {}
    raw = [l for l in (j1.get("links") or [])
           if isinstance(l, dict) and l.get("url") in cand_urls and l.get("anchor") and l.get("section")]

    # CODE: one link per section, and never the same url twice — keep the best-reasoned first
    inline, seen_sec, seen_url = [], set(), set()
    for l in raw:
        if l["section"] in seen_sec or l["url"] in seen_url:
            continue
        seen_sec.add(l["section"]); seen_url.add(l["url"])
        inline.append(l)
    inline = inline[:5]
    if len(raw) != len(inline):
        print(f"    dropped {len(raw) - len(inline)} link(s): duplicate section or url, or over the cap")

    # ---- JUDGE 2: read-more pointers ----------------------------------------
    rm_c = _read_more_candidates(w, meta, order, vec_path, own,
                                 exclude={l["url"] for l in inline})
    j2 = llm.call_json(_fill("read-more.md", BRAND=config.BRAND, ARTICLE=article_md,
                             CANDIDATES="\n\n".join(
                                 f"  - {c['url']} · {c['title']}\n    THE PAGE'S OPENING: {c['excerpt'][:2200]}"
                                 for c in rm_c) or "  (none)")) or {}
    rm_urls = {c["url"] for c in rm_c}
    pointers = [p for p in (j2.get("pointers") or [])
                if isinstance(p, dict) and p.get("url") in rm_urls and p.get("line")
                and not re.search(r"\d", re.sub(r"\(https?[^)]*\)", "", p["line"]))
                and "—" not in p["line"] and "--" not in re.sub(r"\(https?[^)]*\)", "", p["line"])][:2]

    # ---- JUDGE 3: external curation -----------------------------------------
    comp = _competitor_domains()
    is_comparison = "comparison" in (st.get("format_archetype") or "")
    ext, dropped_comp = [], []
    for u, cs in url_cards.items():
        host = u.split("/")[2].lower().removeprefix("www.")
        if own in host:
            continue
        if any(host == d or host.endswith("." + d) for d in comp) and not is_comparison:
            dropped_comp.append(u)
            continue
        claims = [("★ " if re.search(r"\d\d", c.get("verbatim") or "") else "") + (c.get("gloss") or "")[:90]
                  for c in cs[:3]]
        ext.append({"url": u, "host": host, "n": len(cs), "claims": claims})
    ext.sort(key=lambda x: -x["n"])
    j3 = llm.call_json(_fill("external-links.md", BRAND=config.BRAND, TOTAL=len(ext),
                             MAX=config.EXTERNAL_LINKS_MAX,
                             CANDIDATES="\n".join(
                                 f"  - {e['host']} · {e['url']}\n    supports {e['n']} claim(s): "
                                 + " | ".join(e["claims"]) for e in ext[:120]) or "  (none)")) or {}
    ext_urls = {e["url"] for e in ext}
    kept = [k for k in (j3.get("kept") or [])
            if isinstance(k, dict) and k.get("url") in ext_urls][:config.EXTERNAL_LINKS_MAX]

    # ---- CODE: every chosen link must be ALIVE before anything is inserted ----
    from concurrent.futures import ThreadPoolExecutor as _TPE
    chosen = list(dict.fromkeys([l["url"] for l in inline] + [p["url"] for p in pointers]
                                + [k["url"] for k in kept]))
    with _TPE(max_workers=8) as ex:
        alive = dict(zip(chosen, ex.map(_alive, chosen)))
    dead = [u for u, ok in alive.items() if not ok]
    inline = [l for l in inline if alive.get(l["url"])]
    pointers = [p for p in pointers if alive.get(p["url"])]
    kept = [k for k in kept if alive.get(k["url"])]
    if dead:
        print(f"    dead links dropped: {len(dead)}")

    # ---- CODE: insert, then prove nothing else changed -----------------------
    out = json.loads(json.dumps(w))
    sec_by_head = {s["heading"]: s for s in out.get("sections") or []}
    placed, failed = [], []

    def _prose_of(name):
        if name == "intro":
            return out.get("intro") or ""
        if name == "close":
            return out.get("close") or ""
        return (sec_by_head.get(name) or {}).get("prose", "")

    def _set_prose(name, text):
        if name == "intro":
            out["intro"] = text
        elif name == "close":
            out["close"] = text
        elif name in sec_by_head:
            sec_by_head[name]["prose"] = text

    for l in inline:
        prose = _prose_of(l.get("section") or "")
        new = _insert_anchor(prose, l["anchor"], l["url"]) if prose else None
        if new is None:
            failed.append({"kind": "inline", "why": "anchor not found verbatim", **l})
        else:
            _set_prose(l["section"], new)
            # carry the retrieval scores onto the placed row. Until 2026-08-06 every placed link
            # stored sim: None, so nobody could tell a confident match from a desperate one after
            # the fact — and the floor could not be tuned without that number.
            c = cand_by.get((l.get("section") or "", l.get("url") or "")) or {}
            placed.append({"kind": "inline", **l,
                           "sim": c.get("sim"), "rr": c.get("rr"),
                           "title_sim": c.get("title_sim"), "body_sim": c.get("body_sim")})

    _head_by_plain = {_plain(h): h for h in list(sec_by_head) + ["intro", "close"]}
    for p in pointers:
        name = p.get("after_section") or ""
        prose = _prose_of(name)
        if not prose:                                       # try again ignoring smart punctuation
            name = _head_by_plain.get(_plain(name), name)
            prose = _prose_of(name)
            if prose:
                p["after_section"] = name
        if not prose:
            failed.append({"kind": "read-more", "why": "section not found", **p})
            continue
        adjustments = []
        for key in ("adjust_before", "adjust_after"):
            adj = p.get(key)
            if isinstance(adj, dict) and adj.get("old") and adj.get("new"):
                if prose.count(adj["old"]) == 1 and tags.ids(adj["old"]) == tags.ids(adj["new"]) \
                        and sorted(re.findall(r"\d[\d,\.]*", adj["old"])) == sorted(re.findall(r"\d[\d,\.]*", adj["new"])):
                    prose = prose.replace(adj["old"], adj["new"])
                    adjustments.append({key: adj})
                else:
                    failed.append({"kind": "read-more-adjust", "why": "sentence not found once, or touched a number/tag", **adj})
        prose = prose.rstrip() + "\n\n" + p["line"].strip()
        _set_prose(name, prose)
        placed.append({"kind": "read-more", "after_section": name, "line": p["line"].strip(),
                       "url": p["url"], "why": p.get("why"), "adjustments": adjustments})

    for k in kept:                                          # external: mask the naming phrase where given
        ph = k.get("anchor_phrase")
        if not ph:
            continue
        for name in ["intro"] + [s["heading"] for s in out.get("sections") or []] + ["close"]:
            prose = _prose_of(name)
            new = _insert_anchor(prose, ph, k["url"]) if ph in _mask_links(prose) else None
            if new is not None:
                _set_prose(name, new)
                placed.append({"kind": "external-anchor", "section": name, "anchor": ph, "url": k["url"]})
                break
        else:
            k["anchor_phrase"] = None                       # falls back to the linked citation marker

    # THE INTEGRITY DIFF: undo everything declared -> must equal the pre-links text exactly.
    #
    # BOTH SIDES ARE UNLINKED (2026-08-21). This compared _unlink(after) against the raw `before`,
    # which assumed the article arrived carrying no links of its own. That stopped being true when
    # the wrapper started writing the call-to-action link into the close: stripping links from one
    # side only made the close differ from itself every single run, so it was reported as drift and
    # REVERTED — silently throwing away any link this step had legitimately placed there. Comparing
    # like with like is what the check always meant. A link this step wrongly DELETED is caught by
    # the separate url check below, not by this one.
    integrity = []
    orig = dict(_article_text(w))
    for name, before in orig.items():
        after = _prose_of(name)
        reverted = _unlink(after)
        for pl in placed:
            if pl["kind"] == "read-more" and pl["after_section"] == name:
                reverted = reverted.replace("\n\n" + _unlink(pl["line"]), "")
                for adj in pl["adjustments"]:
                    a = list(adj.values())[0]
                    reverted = reverted.replace(a["new"], a["old"])
        ok = " ".join(reverted.split()) == " ".join(_unlink(before).split())
        # A link the article ARRIVED with (today: the wrapper's CTA) must still be there.
        kept_urls_before = {u for _, u in _MDLINK.findall(before)}
        lost = kept_urls_before - {u for _, u in _MDLINK.findall(after)}
        if lost:
            ok = False
        if not ok:
            _set_prose(name, before)                        # undeclared drift -> that block reverts
        integrity.append({"block": name, "ok": ok,
                          **({"lost_links": sorted(lost)} if lost else {})})
    clean = all(i["ok"] for i in integrity)

    # WHERE each over-cited source keeps its marker. Runs on the FINAL text, after every insertion
    # and after the integrity revert, so it judges the article a reader will actually get.
    cite_keep, n_over = _citation_places(out, id2card, config.CITATION_MAX_REPEATS)
    if n_over:
        print(f"    citations: {n_over} source(s) marked more than {config.CITATION_MAX_REPEATS} times "
              f"-> thinned to the places that earn it")

    out["citation_keep"] = {str(c): sorted(v) for c, v in cite_keep.items()}
    report_citations = [{"card": c, "kept": len(v)} for c, v in sorted(cite_keep.items())]
    out["links"] = {"inline": [p for p in placed if p["kind"] == "inline"],
                    "read_more": [p for p in placed if p["kind"] == "read-more"],
                    "external_kept": kept}
    report = {"slug": slug, "own_domain": own, "comparison_article": is_comparison,
              "citations_thinned": report_citations, "citation_cap": config.CITATION_MAX_REPEATS,
              "external_kept": kept,
              "placed": placed, "failed": failed,
              "inline_rejected": j1.get("rejected") or [], "read_more_rejected": j2.get("rejected") or [],
              "external_rejected": j3.get("rejected_examples") or [],
              "competitor_urls_blocked": dropped_comp, "dead_links_dropped": dead,
              "integrity": integrity, "integrity_clean": clean}
    config.write_json(outp, out)
    config.write_json(config.artifact(slug, "links-report.json"), report)
    _render_review(slug, report, meta)

    anchored = [p for p in placed if p["kind"] == "external-anchor"]
    print(f"  -> {outp} | inline {len(out['links']['inline'])} | read-more {len(out['links']['read_more'])} | "
          f"external kept {len(kept)}/{len(ext)} ({len(anchored)} anchored in prose) | "
          f"competitor urls blocked {len(dropped_comp)} | "
          f"integrity {'CLEAN' if clean else 'DRIFT — block(s) reverted'}")
    # SAY IT WHEN THE CURATION BOUGHT NOTHING (2026-08-13). Four articles shipped with 35 curated
    # external sources between them and NOT ONE anchored into the prose, because the judge answered
    # "anchor_phrase": null every time — while the body named SHRM 35 times in one of them. Nothing
    # printed, so the step read as a success. A judged step that changes nothing is a finding.
    if kept and not anchored:
        print(f"    !! {len(kept)} external source(s) kept and NONE became a link in the prose — "
              f"every anchor_phrase came back null. The reader sees them only as citation numbers.")
    for f_ in failed[:6]:
        print(f"    !! {f_['kind']}: {f_.get('why')}")
    return out


# ---------------------------------------------------------------- the review page
def _render_review(slug, r, meta):
    E = _html.escape
    css = """
:root{--bg:#fffdf8;--ink:#1c1a17;--mut:#6b6459;--line:#efe7d8;--card:#fff;--wash:#fff8ec;
      --acc:#fb7a00;--ok:#2e7d43;--no:#c2603a;
      --shadow:0 1px 2px rgba(28,26,23,.04),0 8px 24px rgba(28,26,23,.05)}
body{margin:0;background:var(--bg);color:var(--ink);
     font:15.5px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:880px;margin:0 auto;padding:40px 24px 100px}
h1{font-size:clamp(24px,4vw,32px);margin:0 0 4px;letter-spacing:-.02em}
.sub{color:var(--mut);margin:0 0 22px}
.nums{display:flex;gap:26px;flex-wrap:wrap;background:linear-gradient(180deg,var(--wash),var(--card));
      border:1px solid var(--line);border-radius:12px;padding:15px 20px;margin-bottom:22px;box-shadow:var(--shadow)}
.nums b{font-size:1.45em;display:block}.nums span{color:var(--mut);font-size:.78em}
h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--acc);margin:28px 0 8px;
   border-bottom:1px solid var(--line);padding-bottom:6px;font-weight:700}
.row,.chg{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;
          margin:8px 0;box-shadow:var(--shadow)}
.row .m{color:var(--mut);font-size:.86em}
.chg .rule{font-size:.72em;color:var(--acc);text-transform:uppercase;letter-spacing:.08em;font-weight:700}
.chip{display:inline-block;background:var(--wash);border:1px solid var(--line);border-radius:100px;
      padding:1px 9px;font-size:.74em;color:var(--mut);margin-left:6px}
del{color:var(--no);background:#fdf3f0;text-decoration:line-through;border-radius:3px;padding:0 2px}
ins{color:var(--ok);background:#e8f5ec;text-decoration:none;border-radius:3px;padding:0 2px}
.arrow{color:var(--mut);margin:0 6px}
.rej{color:var(--no);font-weight:600}
.ok{color:var(--ok);font-weight:600}.no{color:var(--no);font-weight:600}
.q{color:var(--mut)}
a{color:var(--acc);overflow-wrap:anywhere}
mark{background:#ffe9ad;color:#1c1a17;border-radius:3px;padding:0 3px}
""" + _map_css()

    def sec(title, rows, empty):
        return f"<h2>{E(title)}</h2>" + ("".join(rows) if rows else f'<p class="q">{E(empty)}</p>')

    def _score_chip(p):
        """How strong the match was. Blank before 2026-08-06 — the number was computed then thrown
        away, so no reader could tell a confident pick from the least-bad page on the shelf."""
        rr, sim = p.get("rr"), p.get("sim")
        if rr is None and sim is None:
            return ""
        bits = []
        if rr is not None:
            bits.append(f"match {rr:.2f}")
        if sim is not None:
            bits.append(f"search {sim:.2f}")
        weak = (rr if rr is not None else sim) < config.LINK_WEAK_SCORE
        return (f'<span class="chip" style="{"color:var(--no);font-weight:600" if weak else ""}">'
                f'{E(" · ".join(bits))}{" — weak" if weak else ""}</span>')

    inline = [f'<div class="row"><mark>{E(p["anchor"])}</mark> → <a href="{E(p["url"])}">{E(p["url"])}</a>'
              f'<span class="chip">{E(str(p.get("section")))}</span>{_score_chip(p)}'
              f'<div class="m">{E(str(p.get("why") or ""))}</div></div>'
              for p in r["placed"] if p["kind"] == "inline"]
    rm = [f'<div class="row">{E(p["line"])}<span class="chip">after: {E(p["after_section"])}</span>'
          f'<div class="m">{E(str(p.get("why") or ""))}</div>'
          + "".join(f'<div class="m">smoothed: “{E(list(a.values())[0]["old"])}” → “{E(list(a.values())[0]["new"])}”</div>'
                    for a in p.get("adjustments") or []) + "</div>"
          for p in r["placed"] if p["kind"] == "read-more"]
    ext = [f'<div class="row"><a href="{E(k["url"])}">{E(k["url"])}</a>'
           + (f'<span class="chip">anchored on “{E(k["anchor_phrase"])}”</span>' if k.get("anchor_phrase") else
              '<span class="chip">linked at its citation marker</span>')
           + f'<div class="m">{E(str(k.get("why") or ""))}</div></div>' for k in r.get("external_kept") or []]
    rej = [f'<div class="row"><span class="m">{E(str(x.get("url") or ""))} — {E(str(x.get("why") or ""))}</span></div>'
           for x in (r["inline_rejected"] + r["read_more_rejected"] + r["external_rejected"])[:15]]
    integ = ('<p class="ok">✓ Nothing changed beyond the declared insertions — verified by code, '
             'every block reverts to the original exactly.</p>' if r["integrity_clean"] else
             '<p class="no">✗ Undeclared drift found — the affected block(s) were REVERTED to the original.</p>')

    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Links — {E(slug)}</title><style>{css}</style></head><body><div class="wrap">'
            f'<h1>The links pass</h1><p class="sub">{E(slug)}</p>'
            + _map("Links") + integ
            + _reads()
            + sec("Internal links laid into the text", inline, "none placed")
            + sec("Read-more pointers", rm, "none — nothing qualified (the normal outcome)")
            + sec(f'External sources kept ({len(r["external_kept"])} of the citations become visible links)',
                  ext, "none kept")
            + ((f'<h2>Sources marked too often</h2>'
                f'<p class="q">{len(r["citations_thinned"])} source(s) were marked more than '
                f'{r["citation_cap"]} times. A reader needs to know where a figure came from; they do '
                f'not need telling twenty times. An AI judge picked the places each one is doing real '
                f'work, spread across the article, and the rest read as prose. Nothing was deleted: '
                f'every source tag is still in the working files, and the Sources list is unchanged.</p>'
                + '<div class="panel">'
                + "".join(f'<div class="row"><span class="t">card {c["card"]}</span>'
                          f'<div>kept in {c["kept"]} place(s)</div></div>'
                          for c in r["citations_thinned"]) + "</div>")
               if r.get("citations_thinned") else "")
            + sec("Notable rejections, with reasons", rej, "—")
            + (f'<h2>Competitor citations blocked</h2><p class="q">{len(r["competitor_urls_blocked"])} url(s)</p>'
               if r["competitor_urls_blocked"] else "")
            + (('<h2>Dead links dropped (page did not answer)</h2>'
                + "".join(f'<div class="row"><span class="m">{E(u)}</span></div>'
                          for u in r["dead_links_dropped"]))
               if r.get("dead_links_dropped") else "")
            + "</div></body></html>")
    config.write_text(config.artifact(slug, "links-review.html"), page)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Writer Step 6 — lay in the links, with receipts.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Writer Step 6: links — {a.slug} ==")
    run(a.slug, redo=a.redo)
