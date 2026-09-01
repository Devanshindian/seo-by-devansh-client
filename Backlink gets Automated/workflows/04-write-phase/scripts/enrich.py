#!/usr/bin/env python3
"""Architect Step 2 — ENRICH: run the research the structure asked for, build new sourced cards, finalize.

Reads:  architect/_work/structure.shaped.json (a legacy architect/structure.json is adopted as shaped)
        + planner/article-plan.json (for the coverage lists in the final view) + the queue row.
Writes: architect/structure.json  — THE architect's FINAL output (enriched H3s attached in place)
        architect/structure.md    — the human view, rendered from the final version
        architect/enriched-cards.json — the new cards, full text + source links (ids 9001+)
        architect/_work/enrichment.json — the full log per researched H3.

Per research request (a section's needs_research entry: {topic, goes_to}), the loop:
  1. plan-queries.md   -> up to ENRICH_QUERIES_PER_H3 web queries
  2. search            -> DataForSEO SERP, ORGANIC results only, balance-guarded (DFS_MIN_CREDITS);
                          fallback: one Claude-web call (search-urls.md) that returns result URLs
  3. download          -> ranks interleaved across queries, deduped, best-loading pages until
                          ENRICH_PAGES_PER_H3; each page's top ENRICH_PAGE_CHARS chars kept
  4. extract-cards.md  -> any number of cards; each summarizes ONE page only; gloss+summary+link
  5. validate + place  -> card links must be fetched pages; ids 9001+; the cards join the destination
                          the ARCHITECT named (the section's opening, or one of its sub-headings).
                          This step never invents a heading. Any sub-heading left with no cards at
                          the end is removed and recorded.
Zero markers = instant promotion of the shaped structure. A failed search/H3 never blocks the rest.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
import article_ctx
import config
import llm
import fmt_router
import shape

_DFS_SCRIPTS = os.path.join(config.WORKFLOWS, "03-content-machine", "10-dataforseo", "scripts")
ENRICH_WORKERS = int(os.environ.get("ENRICH_WORKERS", "8"))                  # parallel markers on the DataForSEO route
ENRICH_WORKERS_FALLBACK = int(os.environ.get("ENRICH_WORKERS_FALLBACK", "1"))  # the Claude CLI route stays serial
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def _fetch(url, timeout=15):
    """The page as plain text, or an __ERR__ marker. PDFs are refused (2026-08-08).

    This strips HTML tags. A PDF has none, so it used to come back as decoded binary — comfortably
    over the 500-character floor, so it PASSED as a good page, consumed one of the 15 download slots,
    and reached the card builder as gibberish. Real cost: the cost-per-hire run downloaded a SHRM PDF
    and a law-firm PDF while hunting for survey methodology, and found nothing.
    """
    if url.lower().split("?")[0].endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip")):
        return "__ERR__NotHTML"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ctype = (r.headers.get("Content-Type") or "").lower()
            if ctype and "html" not in ctype and "text/plain" not in ctype:
                return "__ERR__NotHTML"          # a PDF served without a .pdf suffix
            raw = r.read(3_000_000).decode("utf-8", "ignore")
        if raw.lstrip()[:5] == "%PDF-":          # ... or served as text/html and lying about it
            return "__ERR__NotHTML"
        raw = re.sub(r"<(script|style)\b.*?</\1>", " ", raw, flags=re.S | re.I)
        return html.unescape(re.sub(r"<[^>]+>", " ", raw))
    except Exception as e:
        return f"__ERR__{type(e).__name__}"


def _dfs(pycode, *args, timeout=120):
    try:
        p = subprocess.run([sys.executable, "-c", pycode, *args], cwd=_DFS_SCRIPTS,
                           capture_output=True, text=True, timeout=timeout)
        return p.stdout.strip()
    except Exception:
        return ""


def _dfs_balance():
    out = _dfs("import dfs; print(dfs.balance())", timeout=60)
    try:
        return float(out)
    except ValueError:
        return None


def _dfs_serp(query):
    """Top ORGANIC result urls for one query (ads and every non-organic block excluded)."""
    code = ("import json,sys; import dfs, config; "
            "resp=dfs.call('/v3/serp/google/organic/live/advanced',[{'keyword':sys.argv[1],"
            "'location_name':config.LOCATION,'language_code':config.LANGUAGE,'depth':10}]); "
            "items=dfs.first_result(resp).get('items') or []; "
            "print(json.dumps([i.get('url') for i in items if i.get('type')=='organic' and i.get('url')]))")
    out = _dfs(code, query)
    try:
        return json.loads(out or "[]")
    except json.JSONDecodeError:
        return []


def _claude_urls(queries, maxn):
    """Fallback: one Claude-web call returns result URLs for the planned queries. (candidates, ok)."""
    if config.NO_CLAUDE:                 # the run is pinned off Claude — never spend its quota here
        return [], False
    try:
        prompt = (llm.load_prompt("search-urls.md")
                  .replace("{{QUERIES}}", "\n".join(f"- {q}" for q in queries))
                  .replace("{{MAX}}", str(maxn)))
        r = subprocess.run([config.CLAUDE_BIN, "-p", "--allowedTools", "WebSearch"],
                           input=prompt, capture_output=True, text=True, timeout=config.CLAUDE_TIMEOUT)
        if r.returncode != 0:
            return [], False
        data = llm._extract_json(r.stdout)
        urls = [u for u in (data.get("urls") if isinstance(data, dict) else data) if isinstance(u, str)]
        return urls, True
    except Exception:
        return [], False


def _interleave(lists):
    """Rank-interleave candidate urls across queries, deduped, order preserved."""
    out, i = [], 0
    while any(i < len(L) for L in lists):
        for L in lists:
            if i < len(L):
                out.append(L[i])
        i += 1
    seen, res = set(), []
    for u in out:
        if u not in seen:
            seen.add(u)
            res.append(u)
    return res


def _fill(name, **kw):
    p = llm.load_prompt(name)
    for k, v in kw.items():
        p = p.replace("{{" + k + "}}", str(v))
    return p


def run(slug, redo=False):
    outp = config.artifact(slug, "structure.json")
    shaped_p = os.path.join(config.architect_work_dir(slug), "structure.shaped.json")
    if not os.path.exists(shaped_p) and os.path.exists(outp):
        shutil.move(outp, shaped_p)                        # adopt a legacy pre-enrich structure
        print(f"  adopted legacy structure -> {shaped_p}")
    shaped = json.load(open(shaped_p))
    if os.path.exists(outp) and not redo and os.path.getmtime(outp) >= os.path.getmtime(shaped_p):
        print(f"  reusing {outp}")
        return json.load(open(outp))
    os.environ["RUN_SLUG"], os.environ["RUN_STEP"] = slug, "enrich.py"   # the DataForSEO
    # client runs in a subprocess and cannot see --slug or its caller; these let it bill correctly.
    plan = json.load(open(config.artifact(slug, "article-plan.json")))
    row = fmt_router._queue_row(slug)
    title, angle = (row.get("asset") or "").strip(), (row.get("angle") or "").strip()
    # The world (about / not_about) rides into the query planner: an enrichment query that drifts pulls
    # real pages from a NEIGHBOURING field, and every card built from them reads plausible. [2026-08-04]
    _actx = article_ctx.article_context(slug)
    ctx = {"BRAND": config.BRAND, "ABOUT": config.ABOUT or "(no description on file)",
           "TITLE": title or "(none)", "ANGLE": angle or "(none)",
           "WORLD_ABOUT": article_ctx.or_na(_actx, "about"),
           "WORLD_NOT_ABOUT": article_ctx.or_na(_actx, "not_about"),
           "PERSONA": article_ctx.persona(slug)}

    # A marker is now {topic, goes_to} (2026-08-09). The topic is the research brief; goes_to names
    # where the answer belongs — this section's opening, or one of its existing sub-headings. A plain
    # string (the old shape) still works and defaults to the opening.
    markers = []
    for si, sec in enumerate(shaped["sections"]):
        for r in (sec.get("needs_research") or []):
            if isinstance(r, str):
                markers.append((si, r.strip(), "opening"))
            elif isinstance(r, dict) and str(r.get("topic") or "").strip():
                markers.append((si, str(r["topic"]).strip(), str(r.get("goes_to") or "opening").strip()))
    log, enriched, next_id = [], {}, 9001

    if markers:
        bal = _dfs_balance()
        use_dfs = bal is not None and bal >= config.DFS_MIN_CREDITS
        route = f"DataForSEO (balance ${bal:.2f})" if use_dfs else f"Claude web fallback (DFS balance: {bal})"
        print(f"  {len(markers)} research marker(s) | route: {route}")

    def _one_marker(si, h3, dest):
        """Research ONE marker. Touches no shared state, so many can run at once. Returns
        (log_entry, cards) — card ids are minted afterwards, in marker order, so runs stay identical."""
        sec = shaped["sections"][si]
        e = {"section": sec["headline"], "h3": h3, "goes_to": dest}
        found = []
        try:
            # the section's JOB rides in too (2026-08-08). This was the only step in the architect
            # that never saw it, and it is the step that decides what we go out and buy: a heading is
            # a label and can be vague ("Appendix: Full Methodology"), the job says what the section
            # actually has to deliver.
            q = llm.call_json(_fill("plan-queries.md", **ctx, SECTION_HEADLINE=sec["headline"],
                                    SECTION_JOB=sec.get("job") or "(none given)",
                                    H3=h3, N=config.ENRICH_QUERIES_PER_H3)) or {}
            queries = [str(x).strip() for x in (q.get("queries") or []) if str(x).strip()][:config.ENRICH_QUERIES_PER_H3]
            e["queries"] = queries
            if not queries:
                e["status"] = "no queries planned"
                return e, found
            if use_dfs:
                cand = _interleave([_dfs_serp(x) for x in queries])
                e["route"] = "dataforseo"
            else:
                cand, ok = _claude_urls(queries, config.ENRICH_PAGES_PER_H3 + 10)
                e["route"] = "claude-web"
                if not ok:
                    e["status"] = "search failed (fallback call errored)"
                    return e, found
            pages = []
            for u in cand:
                if len(pages) >= config.ENRICH_PAGES_PER_H3:
                    break
                t = _fetch(u)
                if t.startswith("__ERR__") or len(t.strip()) < 500:
                    continue
                # collapse whitespace BEFORE truncating: raw html-stripped text is mostly blank space and
                # nav, so a raw slice of a heavy page hands the extractor a menu instead of the article
                pages.append((u, " ".join(t.split())[:config.ENRICH_PAGE_CHARS]))
            e["candidates"] = len(cand)
            e["pages"] = [u for u, _ in pages]
            if not pages:
                e["status"] = "no pages loaded"
                return e, found
            block = "\n\n".join(f"SOURCE URL: {u}\nTEXT:\n{t}" for u, t in pages)
            out = llm.call_json(_fill("extract-cards.md", **ctx, SECTION_HEADLINE=sec["headline"],
                                      H3=h3, PAGES=block)) or {}
            ok_urls = {u for u, _ in pages}
            rejected = 0
            for c in out.get("cards") or []:
                g = (c.get("gloss") or "").strip()
                s_ = (c.get("summary") or "").strip()
                u = (c.get("source_url") or "").strip()
                if not g or not s_ or u not in ok_urls:
                    rejected += 1
                    continue
                found.append({"gloss": g, "verbatim": s_, "source_urls": [u], "tag": "enriched"})
            e["cards_kept"], e["cards_rejected"] = len(found), rejected
            e["status"] = "ok" if found else "nothing usable found"
        except Exception as ex:
            e["status"] = f"error: {type(ex).__name__}: {str(ex)[:120]}"
        return e, found

    if markers:
        # DataForSEO is an API and takes the load; the Claude CLI fallback cannot, so it stays serial.
        workers = ENRICH_WORKERS if use_dfs else ENRICH_WORKERS_FALLBACK
        print(f"  researching {len(markers)} marker(s), {workers} at a time")
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_one_marker, si, h3, dest) for si, h3, dest in markers]
            results = [f.result() for f in futs]        # in marker order, so ids and the log are stable
    else:
        results = []

    # PLACED WHERE THE ARCHITECT SAID (2026-08-09). This step used to APPEND a new sub-heading per
    # marker, titled with the research brief itself. Those briefs are search queries, not headings —
    # one real example ran 200 characters, "Exact SHRM report titles, publication years, sample sizes
    # and methodology notes for the $4,700 (2022)..." — and now that the writer renders sub-headings,
    # it would have gone on the page as one. It also bypassed the architect's paragraph rule, since a
    # section deliberately given no sub-headings could gain one here. Enrich no longer invents
    # headings: the cards join the opening, or an existing sub-heading the architect named.
    for (si, h3, dest), (e, found) in zip(markers, results):
        sec = shaped["sections"][si]
        kept = []
        for c in found:
            enriched[next_id] = dict(c, card_id=next_id)
            kept.append(next_id)
            next_id += 1
        if kept:
            target = None
            if dest.lower() != "opening":
                target = next((h for h in sec.get("h3s") or [] if h.get("h3") == dest), None)
            if target is None:
                sec.setdefault("lead", {"h3": "", "boxes": [], "card_ids": [], "is_lead": True})
                sec["lead"].setdefault("card_ids", []).extend(kept)
                e["placed_in"] = "opening"
            else:
                target.setdefault("card_ids", []).extend(kept)
                e["placed_in"] = dest
        log.append(e)
        print(f"    [{e.get('status')}] {h3[:48]} -> {e.get('placed_in', dest)[:28]} | "
              f"queries {len(e.get('queries', []))} | pages {len(e.get('pages', []))} | "
              f"cards {e.get('cards_kept', 0)}")

    # THE SAFETY NET. The architect may create a sub-heading with no boxes and rely on research to
    # fill it. When the research fails, that leaves a heading with nothing under it — so it is removed
    # here and recorded. Also catches an empty sub-heading created by mistake.
    emptied = []
    for sec in shaped["sections"]:
        keep = []
        for h in sec.get("h3s") or []:
            if h.get("card_ids"):
                keep.append(h)
            else:
                emptied.append({"section": sec["headline"], "h3": h.get("h3", "")})
        sec["h3s"] = keep
    if emptied:
        shaped["empty_subheadings_removed"] = emptied
        print(f"  !! {len(emptied)} sub-heading(s) had no material and were REMOVED:")
        for x in emptied:
            print(f"       {x['section'][:36]} -> \"{x['h3'][:46]}\"")

    config.write_json(os.path.join(config.architect_work_dir(slug), "enrichment.json"), log)
    if enriched:
        config.write_json(config.artifact(slug, "enriched-cards.json"), enriched)

    # A FAILED MARKER IS NOW LOUD (2026-08-08). A section asked for research, the research came back
    # empty, and the section stayed in the article thinner than it was designed to be — with one quiet
    # line in the log and nothing anywhere a human would look. Two of five failed on the cost-per-hire
    # run and nobody was told. It still does not stop the run: the section is real and the rest of its
    # material is fine. It is recorded in the structure so the review page and structure.md can show it.
    failed = [{"section": x.get("section"), "h3": x.get("h3"), "status": x.get("status"),
               "queries": x.get("queries") or [], "pages_loaded": len(x.get("pages") or [])}
              for x in log if x.get("status") != "ok"]
    if failed:
        shaped["research_failures"] = failed
    config.write_json(outp, shaped)
    shape.render_md(slug, shaped, plan)
    ok_n = sum(1 for x in log if x.get("status") == "ok")
    print(f"  -> {outp} | markers {len(markers)} | resolved {ok_n} | new cards {len(enriched)}")
    if failed:
        print(f"  !! {len(failed)} of {len(markers)} research marker(s) CAME BACK EMPTY — those sections "
              f"stay in the article thinner than they were designed to be:")
        for x in failed:
            print(f"       [{x['status']}] {x['section'][:38]} -> {x['h3'][:44]}")
            print(f"          tried: {' | '.join(q[:44] for q in x['queries'][:3]) or '(no queries planned)'}")
    return shaped


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Architect Step 2 — enrich the structure with researched cards.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Architect Step 2: enrich — {a.slug} ==")
    run(a.slug, redo=a.redo)
