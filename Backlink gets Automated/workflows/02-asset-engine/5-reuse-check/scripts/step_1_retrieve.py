#!/usr/bin/env python3
"""Step 1 — Stage 2 RETRIEVE: the closest existing pages for every clubbed idea (mechanical, no verdict).

Reads:  output/clubbed-ideas.csv (the merged pool)  ·  content-database.csv (URL · Title · Full content)
Writes: output/clubbed-ideas.csv  — fills THREE columns, in one pass (single source of truth):
          RAG candidates       top-15 blended-retrieve -> rerank-2.5, as `Title — url (score)`
          Topic pages we own   deterministic keyword catalogue, as `Title — url`
          Reference links      de-duped union of the two link sets (plain urls) — the fetch list
        _work/content-index/   the two-vector index (title/ + body/), built once, resumable
        _work/topic-keywords.json  the LLM topic labels (cached; reused unless --redo)

The RAG core (two-vector Voyage index -> blended dense score -> rerank-2.5) is ported verbatim from
projects/.../clubbed/_work/rag.py; the foreign-language exclusion from retrieve_top15.py. Embedding and
reranking go through _shared/voyage.py (voyage-4-large + rerank-2.5) — never re-implemented here.
"""
import argparse, csv, json, os, re, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import numpy as np
import config as c
sys.path.insert(0, c.SHARED)                                  # noqa: E402 — the shared clients live here
import voyage, llm                                            # noqa: E402

csv.field_size_limit(1 << 24)


# ---------------- shared helpers ----------------
def is_foreign(url):
    """True for a translation duplicate: the URL's FIRST path segment is an ISO language code (/de/, /fr/...).
    Company-agnostic — checks the path segment only, never a hardcoded domain (retrieve_top15.py, generalised)."""
    seg = urlparse(url).path.strip("/").split("/", 1)[0].lower()
    return seg in c.LOCALES


def _save_npy(path, arr):
    """Atomic .npy save (C5): write a temp in the SAME dir, then rename over the target."""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".npy.tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            np.save(f, arr)                                   # file object -> np.save won't append an extension
        os.replace(tmp, path)
    except BaseException:
        try: os.remove(tmp)
        except OSError: pass
        raise


def _chunks(text):
    """Overlapping char chunks (rag.py L79-88)."""
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= c.CHUNK_CHARS:
        return [text]
    out, s = [], 0
    while s < len(text):
        out.append(text[s:s + c.CHUNK_CHARS]); s += c.CHUNK_CHARS - c.OVERLAP
    return out


def load_pages(content_csv):
    """Every page WITH a title + real body — only these can be reuse candidates (rag.py load_pages)."""
    pages = []
    with open(content_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url = (row.get("URL") or "").strip()
            title = (row.get("Title") or "").strip()
            fc = (row.get("Full content") or "").strip()
            if url and fc:
                pages.append((url, title, fc))
    return pages


# ---------------- INDEX (Stage 1: two vectors per page) ----------------
def do_index(content_csv, idx_dir, reindex=False):
    pages = load_pages(content_csv)
    print(f"   index: {len(pages)} pages with content", flush=True)

    # --- TITLE index: one vector per page (cheap, one shot) ---
    tdir = os.path.join(idx_dir, "title")
    tvec_path = os.path.join(tdir, "vectors.npy")
    if os.path.exists(tvec_path) and not reindex:
        print("   title index already present, skipping", flush=True)
    else:
        os.makedirs(tdir, exist_ok=True)
        tvecs = voyage.embed([t if t else u for u, t, fc in pages], "document")
        _save_npy(tvec_path, tvecs)
        with open(os.path.join(tdir, "meta.jsonl"), "w", encoding="utf-8") as f:
            for u, t, fc in pages:
                f.write(json.dumps({"url": u, "title": t}) + "\n")
        print("   title index done", flush=True)

    # --- BODY index: chunked, resumable (rag.py do_index) ---
    bdir = os.path.join(idx_dir, "body")
    os.makedirs(os.path.join(bdir, "parts"), exist_ok=True)
    state_p = os.path.join(bdir, "state.json")
    meta_p = os.path.join(bdir, "meta.jsonl")
    if reindex:
        for p in (state_p, meta_p):
            if os.path.exists(p): os.remove(p)
        for p in os.listdir(os.path.join(bdir, "parts")):
            os.remove(os.path.join(bdir, "parts", p))
    state = json.load(open(state_p)) if os.path.exists(state_p) else {"done": [], "part": 0}
    done = set(state["done"])
    todo = [(u, t, fc) for u, t, fc in pages if u not in done]
    print(f"   body index: {len(todo)} pages to embed ({len(done)} done)", flush=True)
    meta_f = open(meta_p, "a", encoding="utf-8")
    buf = []
    buf_chunks = 0

    def flush():
        nonlocal buf, buf_chunks
        if not buf:
            return
        texts, metas = [], []
        for u, t, fc in buf:
            for ci, ch in enumerate(_chunks(fc)):
                texts.append(ch); metas.append({"url": u, "title": t, "chunk": ci})
        vecs = voyage.embed(texts, "document")
        _save_npy(os.path.join(bdir, "parts", f"part_{state['part']:05d}.npy"), vecs)
        for m in metas:
            meta_f.write(json.dumps(m) + "\n")
        meta_f.flush()
        state["part"] += 1
        state["done"].extend(u for u, _, _ in buf)
        c.write_json(state_p, state)
        print(f"      flushed {len(buf)} pages / {len(texts)} chunks (done {len(state['done'])})", flush=True)
        buf, buf_chunks = [], 0

    for p in todo:
        buf.append(p); buf_chunks += len(_chunks(p[2]))
        if buf_chunks >= c.INDEX_BATCH_CHUNKS:
            flush()
    flush()
    meta_f.close()
    print("   body index done", flush=True)


def load_vecs(subdir):
    """Load a (title or body) index: normalised vectors + their per-vector meta (rag.py load_vecs)."""
    vp = os.path.join(subdir, "vectors.npy")
    if os.path.exists(vp):
        V = np.load(vp)
    else:
        parts = sorted(os.listdir(os.path.join(subdir, "parts")))
        V = np.concatenate([np.load(os.path.join(subdir, "parts", p)) for p in parts], axis=0)
    M = [json.loads(l) for l in open(os.path.join(subdir, "meta.jsonl"), encoding="utf-8")]
    assert len(M) == len(V), f"{subdir}: meta {len(M)} != vecs {len(V)}"
    V = V.astype(np.float32)
    V /= (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)     # harmless re-normalise -> dot == cosine
    return V, M


# ---------------- QUERY / RETRIEVE (Stage 2) ----------------
def query_text(asset):
    """CLEAN query = the Asset title with parenthetical qualifier detail stripped (rag.py L191-194)."""
    a = re.sub(r"\([^)]*\)", " ", asset or "")
    a = re.sub(r"\s+", " ", a).strip()
    return a or "untitled"


# ---------------- TOPIC CATALOGUE (deterministic; smart label + dumb match) ----------------
_SUFFIXES = ("ings", "ing", "ers", "er", "ed", "es", "s")

def _stem(word):
    """Light stem: strip one trailing plural/verb suffix so screening/screener/screen collapse (workflow)."""
    w = word.lower()
    for suf in _SUFFIXES:
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def _kw_tokens(keyword):
    return [_stem(t) for t in re.findall(r"[a-z0-9]+", (keyword or "").lower()) if len(t) >= 3]


def _matches(tokens, haystack):
    """Every stemmed keyword token must appear as a substring in the lowercased title+url."""
    return bool(tokens) and all(t in haystack for t in tokens)


def label_topic_keywords(rows, redo=False):
    """One LLM pass: 1-3 DISTINCTIVE topic terms per asset (avoiding generic words). Cached + resumable."""
    cache = os.path.join(c.WORK, "topic-keywords.json")
    if os.path.exists(cache) and not redo:
        by_i = {d["i"]: d.get("keywords", []) for d in json.load(open(cache))}
        if all(i in by_i for i in range(len(rows))):
            print(f"   topic keywords: reusing cached labels ({len(by_i)})", flush=True)
            return [by_i.get(i, []) for i in range(len(rows))]
    tmpl = llm.load_prompt("topic-keywords.md")
    batches = [list(range(k, min(k + c.TOPIC_KW_BATCH, len(rows)))) for k in range(0, len(rows), c.TOPIC_KW_BATCH)]

    def _one(idxs):
        listing = "\n".join(f"{i}. {query_text(rows[i].get('Asset',''))}" for i in idxs)
        try:
            out = llm.call_json(tmpl.replace("{{ASSETS}}", listing))
        except Exception as e:
            print(f"   !! topic-keyword batch failed ({str(e)[:40]}) — those ideas get no catalogue", flush=True)
            return {}
        got = {}
        for it in (out if isinstance(out, list) else out.get("items", [])):
            i = it.get("i"); kws = [k for k in (it.get("keywords") or []) if isinstance(k, str) and k.strip()]
            if isinstance(i, int) and i in idxs:
                got[i] = kws[:3]
        return got

    labels = {}
    with ThreadPoolExecutor(max_workers=c.TOPIC_KW_WORKERS) as ex:
        for res in ex.map(_one, batches):
            labels.update(res)
    ordered = [{"i": i, "keywords": labels.get(i, [])} for i in range(len(rows))]
    c.write_json(cache, ordered)
    print(f"   topic keywords: labelled {sum(1 for o in ordered if o['keywords'])}/{len(rows)} ideas", flush=True)
    return [o["keywords"] for o in ordered]


def build_catalogue(keywords_per_idea, catalogue_pages):
    """Deterministic match: for each idea, every English page whose title/url contains a keyword (stemmed).
    Over-generic keywords (matching > CATALOGUE_MAX_MATCH pages) are dropped; the list is capped, count shown."""
    # pre-compute a lowercased title+url haystack per (English) page, once
    hay = [(u, t, (t + " " + u).lower()) for (u, t) in catalogue_pages if not is_foreign(u)]
    cells = []
    for kws in keywords_per_idea:
        hits, seen = [], set()
        for kw in kws:
            tokens = _kw_tokens(kw)
            if not tokens:
                continue
            matched = [(u, t) for (u, t, h) in hay if _matches(tokens, h)]
            if len(matched) > c.CATALOGUE_MAX_MATCH:            # too generic — skip this keyword
                continue
            for u, t in matched:
                k = u.rstrip("/").lower()
                if k not in seen:
                    seen.add(k); hits.append((u, t))
        total = len(hits)
        shown = hits[: c.CATALOGUE_CAP]
        cell = "; ".join(f"{t} — {u}" for u, t in shown)
        if total > c.CATALOGUE_CAP:
            cell += f"; (+{total - c.CATALOGUE_CAP} more of {total})"
        cells.append(cell)
    return cells


# ---------------- the step ----------------
def _write_csv(path, fields, rows):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".csv.tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader(); w.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        try: os.remove(tmp)
        except OSError: pass
        raise


def run(redo=False, reindex=False):
    if not os.path.exists(c.CLUBBED):
        sys.exit(f"!! no clubbed pool at {c.rel(c.CLUBBED)} — run 4-merge first.")
    # 1) build / load the two-vector index (Stage 1)
    do_index(c.CATALOGUE_CSV, c.INDEX_DIR, reindex=reindex)
    Vt, Mt = load_vecs(os.path.join(c.INDEX_DIR, "title"))
    Vb, Mb = load_vecs(os.path.join(c.INDEX_DIR, "body"))
    urls = [m["url"] for m in Mt]                              # title order == page order
    uidx = {u: i for i, u in enumerate(urls)}
    # a body chunk whose page is NOT in the title index (title/body built at different times, content changed
    # between partial builds) would KeyError — drop those orphans and flag a --reindex, never crash.
    _keep = [k for k, m in enumerate(Mb) if m["url"] in uidx]
    if len(_keep) < len(Mb):
        print(f"   ⚠ {len(Mb) - len(_keep)} body chunks have no title-index page (stale index) — dropped; "
              f"run with --reindex for a clean rebuild", flush=True)
        Vb = Vb[_keep]; Mb = [Mb[k] for k in _keep]
    body_uidx = np.array([uidx[m["url"]] for m in Mb])        # url-index per body chunk
    foreign = np.array([is_foreign(u) for u in urls])
    print(f"   retrieve: {len(urls)} pages | {len(Vb)} body chunks", flush=True)

    # url -> (Full content, Title) for building the rerank docs + the catalogue page list
    cmap, tmap, catalogue_pages = {}, {}, []
    for row in csv.DictReader(open(c.CATALOGUE_CSV, encoding="utf-8")):
        u = (row.get("URL") or "").strip()
        if not u:
            continue
        cmap[u] = row.get("Full content", "") or ""
        tmap[u] = row.get("Title", "") or ""
        catalogue_pages.append((u, tmap[u]))

    # 2) read the pool
    with open(c.CLUBBED, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f); fields = reader.fieldnames; rows = list(reader)
    for col in c.STAGE2_COLS:
        if col not in fields:
            sys.exit(f"!! clubbed sheet is missing the '{col}' column — is this the merged schema?")

    # 3) topic catalogue (deterministic) — labels via one LLM pass, then a dumb keyword match
    kws = label_topic_keywords(rows, redo=redo)
    cat_cells = build_catalogue(kws, catalogue_pages)

    # 4) per-idea blended retrieve -> rerank -> write all three Stage-2 columns
    def _mkdoc(u):
        d = (tmap.get(u, "")[:200] + "\n" + cmap.get(u, ""))[: c.RERANK_DOC_CHARS].replace("\x00", " ").strip()
        return d or "(no content)"

    def _retrieve_one(r):
        already = len([x for x in (r.get("RAG candidates") or "").split(";") if x.strip()])
        if already >= c.TOPK and not redo:
            return                                            # resumable: retrieved on a prior run, skip
        qtext = query_text(r.get("Asset", ""))
        q = voyage.embed([qtext], "query")[0]
        tsim = Vt @ q; bsim = Vb @ q                          # Vt/Vb read-only shared; bestbody is thread-local
        bestbody = np.full(len(urls), -1.0, dtype=np.float32)
        np.maximum.at(bestbody, body_uidx, bsim)             # best chunk per page
        blended = c.ALPHA * tsim + (1 - c.ALPHA) * bestbody
        order = [k for k in np.argsort(blended)[::-1] if not foreign[k]][: c.N_RETRIEVE]
        cand = [urls[k] for k in order]
        docs = [_mkdoc(u) for u in cand]
        try:
            ranked = voyage.rerank(qtext, docs, min(c.TOPK, len(cand)))
            top = [(cand[i], sc) for i, sc in ranked]
        except Exception as e:                                # rerank hiccup -> keep dense order, no scores
            top = [(u, 0.0) for u in cand[: c.TOPK]]
        r["RAG candidates"] = "; ".join(f"{tmap.get(u, '')} — {u} ({sc:.2f})" for u, sc in top)   # links only

    # retrieve in PARALLEL — each idea's rerank is an independent I/O call (was the sequential bottleneck)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    todo = [r for r in rows if redo or len([x for x in (r.get("RAG candidates") or "").split(";") if x.strip()]) < c.TOPK]
    print(f"   retrieving {len(todo)} ideas ({c.RETRIEVE_WORKERS} parallel) ...", flush=True)
    n_done = 0
    with ThreadPoolExecutor(max_workers=c.RETRIEVE_WORKERS) as ex:
        for fut in as_completed([ex.submit(_retrieve_one, r) for r in todo]):
            fut.result(); n_done += 1
            if n_done % 200 == 0:
                print(f"      retrieved {n_done}/{len(todo)}", flush=True)
                _write_csv(c.CLUBBED, fields, rows)           # periodic checkpoint (resumable)

    # catalogue + reference links (cheap, serial) for every row
    for n, r in enumerate(rows):
        r["Topic pages we own"] = cat_cells[n]
        ref, seen = [], set()                                 # Reference links = de-duped union of both link sets
        for cell in (r.get("RAG candidates", ""), r.get("Topic pages we own", "")):
            for m in re.finditer(r"https?://[^\s;()]+", cell or ""):
                u = m.group(0).rstrip(".,"); k = u.rstrip("/").lower()
                if k not in seen:
                    seen.add(k); ref.append(u)
        r["Reference links"] = "; ".join(ref)

    _write_csv(c.CLUBBED, fields, rows)
    c.write_text(c.STAGE2_DONE, "")                           # orchestrator resume marker
    print(f"   Stage 2 done: filled RAG candidates / Topic pages we own / Reference links for {len(rows)} ideas "
          f"({n_done} newly retrieved) -> {c.rel(c.CLUBBED)}", flush=True)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true", help="re-retrieve every idea (overwrite RAG candidates)")
    ap.add_argument("--reindex", action="store_true", help="rebuild the content index (content changed)")
    a = ap.parse_args()
    run(redo=a.redo, reindex=a.reindex)
