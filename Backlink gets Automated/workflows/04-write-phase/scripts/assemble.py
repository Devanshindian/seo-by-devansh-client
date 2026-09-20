#!/usr/bin/env python3
"""Writer Step 8 — ASSEMBLE: turn the parts into the finished article, and into a page you can review.

Reads:  writer/_work/wrapper.json (h1, intro, faq, close, the final sections)
        + gather/plan-inputs.json (the cards, for the source links + group_a.keyword_set)
        + architect/enriched-cards.json (the researched cards, ids 9001+)
Writes: writer/draft.md      — the article: H1, intro, sections, FAQ, close, sources
        writer/_work/keyword-coverage.json — keyword coverage, COUNTED from the finished text (never AI-reported)
        writer/article.html  — the review page: hover a stat for its source, hover a keyword for
                               what it is (primary / variation / researched section keyword)

Coverage is arithmetic, so code owns it: the editor decides WHICH keywords to weave, this step
counts what actually landed. A count the AI reported about itself would be a guess.
"""
import argparse
import html
import json
import os
import re
import config
import tags

_MDLINK = re.compile(r"\[([^\]\[]+)\]\((https?://[^)\s]+)\)")


def _plain(text):
    """Markdown links reduced to their anchor text — urls must never feed a count."""
    return _MDLINK.sub(lambda m: m.group(1), text or "")


def _card_index(slug):
    """card_id -> {gloss, url}. Research cards + the architect's enriched cards (9001+)."""
    idx = {}
    inp = json.load(open(config.artifact(slug, "plan-inputs.json")))
    for s in inp["group_b"]["sections_menu"]:
        for c in list(s.get("evidence", [])) + [e for h in s.get("h3", []) for e in h.get("evidence", [])]:
            try:
                idx[int(str(c.get("card_id")).lower().replace("id", "").strip())] = {
                    "gloss": (c.get("gloss") or "").strip(),
                    "url": ((c.get("source_urls") or [None])[0])}
            except ValueError:
                continue
    ep = config.artifact(slug, "enriched-cards.json")
    if os.path.exists(ep):
        for k, c in json.load(open(ep)).items():
            idx[int(k)] = {"gloss": (c.get("gloss") or "").strip(),
                           "url": ((c.get("source_urls") or [None])[0])}
    return idx


def _phrase_re(phrase):
    """A phrase matches however it is punctuated: 'cost per hire' and 'cost-per-hire' are the same
    keyword to a search engine, so counting them separately reports false misses."""
    parts = [re.escape(p) for p in re.split(r"[^a-z0-9]+", (phrase or "").lower()) if p]
    if not parts:
        return None
    joiner = r"[\s\-\u2010-\u2015'\u2018\u2019\"\u201c\u201d]+"     # quotes between words must not break a match
    return re.compile(r"(?<![a-z0-9])" + joiner.join(parts) + r"(?![a-z0-9])", re.I)


def _count(text, phrase):
    """Whole-phrase, case- and hyphen-insensitive occurrences."""
    rx = _phrase_re(phrase)
    return len(rx.findall(text or "")) if rx else 0


def keyword_view(slug):
    """The ONE keyword set coverage is measured against: the architect's decision (structure.json
    "keywords" block). An older run without the block falls back to the research-era set."""
    st = json.load(open(config.artifact(slug, "structure.json")))
    kw = st.get("keywords") or {}
    if kw:
        return {"primary": kw.get("primary") or "",
                "variations": kw.get("variations") or [],
                "h2_keywords": [{"keyword": k} for k in (kw.get("section_keywords") or [])]}
    return (json.load(open(config.artifact(slug, "plan-inputs.json")))["group_a"].get("keyword_set")) or {}


def _coverage(w, ks, sections):
    """Where every target phrase actually landed. Counted, not claimed."""
    primary = ks.get("primary") or ""
    variations = [v for v in (ks.get("variations") or []) if v]
    h2kw = [k.get("keyword") for k in (ks.get("h2_keywords") or []) if k.get("keyword")]
    sections = [dict(s, prose=_plain(s["prose"]), heading=_plain(s["heading"])) for s in sections]
    body = "\n\n".join(s["prose"] for s in sections)
    opening = " ".join((w.get("intro") or "").split())
    first100 = " ".join((opening + " " + body).split()[:100])
    whole = "\n\n".join([w.get("h1") or "", opening,
                         "\n".join(s_["heading"] for s_ in sections), body,
                         "\n".join(f"{f['question']} {f['answer']}" for f in (w.get("faq") or [])),
                         w.get("close") or ""])

    def where(p):
        return {"phrase": p, "total": _count(whole, p),
                "in_h1": bool(_count(w.get("h1") or "", p)),
                "in_first_100_words": bool(_count(first100, p)),
                "in_headings": sum(1 for s in sections if _count(s["heading"], p)),
                "in_close": bool(_count(w.get("close") or "", p)),
                "sections": [s["heading"] for s in sections if _count(s["prose"], p)]}

    prim = where(primary)
    var = [where(v) for v in variations]
    return {"primary": prim,
            "primary_plus_variations_total": prim["total"] + sum(v["total"] for v in var),
            "variations": var,
            "h2_keywords": [where(k) for k in h2kw],
            "checklist": {
                "primary in H1": prim["in_h1"],
                "primary in first 100 words": prim["in_first_100_words"],
                "keywords in at least 2 headings":
                    2 <= sum(1 for s_ in sections
                             if any(_count(s_["heading"], p) for p in [primary] + variations + h2kw)),
                "primary in the close": prim["in_close"],
                "at least one section keyword used": any(_count(whole, k) for k in h2kw)}}


def _md(w, idx, cov):
    """The article as it publishes: the Sources list is the CURATED external set and nothing else,
    numbered 1..N in the order a reader first meets them. A citation whose source did not make that
    list is stripped from display; its provenance stays in the _work files and on the review pages.

    History, so nobody re-litigates this twice. Curation was ON, then turned OFF on 2026-08-05 after
    a review found 5 of 13 sections with no visible citation at all — because the picker was also
    deciding who got CREDITED. It is ON again from 2026-08-13 (Devansh, explicitly, twice): a reader
    should meet a short, checkable source list, not thirty entries of which two thirds are blog
    write-ups of the studies above them.

    What stops the 2026-08-05 failure repeating is the FLOOR below, not the flag: if curation would
    leave the article with almost nothing to show, we credit everything instead and say so.
    """
    kept_urls = [k["url"] for k in ((w.get("links") or {}).get("external_kept") or [])]
    curated = bool(kept_urls)
    num_of, order, used = {}, [], {}

    # WHERE each over-cited source keeps its marker, chosen by the links step (2026-08-22). One
    # article marked a single source 20 times; the page stopped reading as prose. This counts each
    # source's occurrences in reading order and renders a marker only at the places on the list.
    # The claim, the sentence and the Sources list are all untouched — only the little number goes.
    cite_keep = {int(k): set(v) for k, v in (w.get("citation_keep") or {}).items()}
    seen_count = {}

    def refs(text, capped=True):
        """capped=False for the FAQ: the links step counts intro -> sections -> close and never sees
        the FAQ, so counting FAQ tags against its list would drop them all as "over the cap"."""
        def one(found):
            out = []
            for cid in found:
                u = (idx.get(cid) or {}).get("url")
                if not u:                                  # a card with no link cannot be credited
                    continue
                if curated and u not in kept_urls:         # not on the curated list — no marker
                    continue
                if capped and cid in cite_keep:            # an over-cited source: only its kept places
                    seen_count[cid] = seen_count.get(cid, 0) + 1
                    if seen_count[cid] not in cite_keep[cid]:
                        continue
                if u not in num_of:                        # number per URL, not per card: two cards
                    order.append(u)                        # sharing a source share one number
                    num_of[u] = len(order)                 # 1..N in order of first appearance
                used[cid] = num_of[u]
                out.append(str(num_of[u]))
            return ("[" + "][".join(dict.fromkeys(out)) + "]") if out else ""
        return re.sub(r" +([.,;:])", r"\1", tags.sub(text, one))

    def render():
        seen_count.clear()          # render() runs twice on the uncurated fallback; counts restart
        L = [f"# {w.get('h1')}", "", refs(w.get("intro") or ""), ""]
        # The TL;DR (was "Quick answer" until 2026-09-05 — Testlify house style is a takeaway
        # list, not a mini-article) sits between the intro and the first section: a reader who
        # reads only this still gets the article. It carries no source tags of its own — everything
        # in it is already proved below — so it goes through refs() only to stay consistent.
        if w.get("quick_answer"):
            L += ["## TL;DR", "", refs(w["quick_answer"]), ""]
        bare = 0
        for s in w["sections"]:
            body = refs(s["prose"])
            bare += 0 if re.search(r"\[\d+\]", body) else 1
            L += [f"## {s['heading']}", "", body, ""]
        # THE CLOSE COMES BEFORE THE FAQ (2026-08-20). It used to sit after it, which buried the one
        # paragraph that asks the reader to do something under five questions they may not have.
        # The close ends the argument; the FAQ is reference material that follows it.
        # The close gets its own heading (2026-08-21). It was the one part of the article with no
        # heading above it, so a reader scrolling to the end met a wall of text. The wrapper writes
        # the heading in the same call as the close and the CTA, so the three cannot drift apart.
        if w.get("close_heading"):
            L += [f"## {w['close_heading']}", ""]
        L += [refs(w.get("close") or ""), ""]
        if w.get("faq"):
            L += ["## Frequently asked questions", ""]
            for f in w["faq"]:
                L += [f"**{f['question']}**", "", refs(f["answer"], capped=False), ""]
        L += ["## Sources", ""]
        for i, u in enumerate(order, 1):
            L.append(f"{i}. {u}")
        return L, bare

    L, bare = render()

    # REPORT THE COST, DO NOT OVERRIDE IT (2026-08-13). Curation strips the marker off any fact whose
    # source missed the list, and on 2026-08-05 that shipped an article with 5 of 13 sections carrying
    # no citation at all. This first shipped as a FLOOR that silently reverted to crediting everything
    # when the damage crossed a third of the sections — which meant one article in four quietly
    # ignored the curation and published 38 sources next to its siblings' 10. A rule the reader can
    # see broken is worse than the thing it prevents. Devansh's call, twice: the short list wins.
    # So the count is measured and printed every run, and it changes nothing on its own.
    if curated:
        note = f"  ·  sources: {len(order)} curated (of {len(kept_urls)} kept)"
        if bare:
            note += f" | !! {bare}/{len(w['sections'])} section(s) now carry NO visible citation"
        print(note)

    return "\n".join(L) + "\n", order, used


def run(slug, redo=False):
    outp = config.artifact(slug, "draft.md")
    # STALENESS CHECK (2026-08-05). "The file exists" is not the same as "it is current". This guard
    # silently served a draft from 16:30 after a 22:42 run that had rebuilt the wrapper, the coherence
    # pass and the links — the third time that trap cost a full run. So: reuse only when the draft is
    # NEWER than every input that feeds it. Otherwise rebuild, and say why.
    if os.path.exists(outp) and not redo:
        srcs = [config.artifact(slug, f) for f in
                ("scrubbed.json", "linked.json", "polish.json", "sentences.json",
                 "readable.json", "coherent.json", "wrapper.json")]
        newer = [os.path.basename(p) for p in srcs
                 if os.path.exists(p) and os.path.getmtime(p) > os.path.getmtime(outp)]
        if not newer:
            print(f"  reusing {outp}")
            return outp
        print(f"  draft.md is STALE — {', '.join(newer)} changed since it was written; rebuilding")

    # newest complete stage wins: links -> slop -> wrapper
    w = None
    for name in ("scrubbed.json", "linked.json", "polish.json", "sentences.json",
                 "readable.json", "wrapper.json"):
        p = config.artifact(slug, name)
        if os.path.exists(p):
            w = json.load(open(p))
            break
    ks = keyword_view(slug)
    idx = _card_index(slug)
    cov = _coverage(w, ks, w["sections"])
    md, order, used = _md(w, idx, cov)

    config.write_text(outp, md)
    # Did we land inside the band the SERP said this topic needs? Nothing used to check the finished
    # article against it, so a 28%-over draft shipped without a word being said.
    _plan = json.load(open(config.artifact(slug, "article-plan.json")))
    _wb = _plan.get("word_band") or {}
    _lo, _hi, _n = _wb.get("min") or 0, _wb.get("max") or 0, len(md.split())
    cov["length"] = {"words": _n, "band_min": _lo, "band_max": _hi,
                     "in_band": bool(_lo and _hi and _lo <= _n <= _hi),
                     "over_by_pct": round((_n - _hi) / _hi * 100, 1) if _hi and _n > _hi else 0}
    if _lo and _hi:
        if _n > _hi:
            print(f"  !! LENGTH: {_n:,} words — {cov['length']['over_by_pct']}% OVER the {_lo:,}-{_hi:,} band")
        elif _n < _lo:
            print(f"  !! LENGTH: {_n:,} words — UNDER the {_lo:,}-{_hi:,} band")
        else:
            print(f"  ✓ length {_n:,} words, inside the {_lo:,}-{_hi:,} band")
    config.write_json(config.artifact(slug, "keyword-coverage.json"), cov)
    import review_page
    htmlp = review_page.build(slug, w, ks, idx, cov, sources=order)

    article = md.split("\n## Sources\n")[0]          # the reference list is not article prose
    words = len(re.sub(r"\[\d+\]", "", _plain(article)).split())
    fails = [k for k, v in cov["checklist"].items() if not v]
    print(f"  -> {outp} | {words} words | {len(w['sections'])} sections | {len(w.get('faq') or [])} FAQ | "
          f"{len(order)} sources")
    print(f"  -> {config.artifact(slug, 'keyword-coverage.json')} | primary '{cov['primary']['phrase']}' "
          f"x{cov['primary']['total']} (+variations = {cov['primary_plus_variations_total']})")
    print("     checklist: " + ("all pass" if not fails else "MISSED -> " + "; ".join(fails)))
    print(f"  -> {htmlp}")
    return outp


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Writer Step 8 — assemble the draft, coverage and review page.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Writer Step 8: assemble — {a.slug} ==")
    run(a.slug, redo=a.redo)
