#!/usr/bin/env python3
"""voyage.py — the ONE shared Voyage client for the whole asset engine (embeddings + reranking).

Used by the competitor-study DEDUP step and (later) the reuse-check — one client, one key, so both the
"are these two ideas the same?" and "is this idea already covered?" jobs run on the same Voyage stack.
Lifted and generalised from projects/.../clubbed/_work/rag.py (which stays as the reuse-check prototype).

THE KEY lives in the environment, never in the repo (D3):
    1. VOYAGE_API_KEY env var, else
    2. the first `pa-...` token in ~/.testlify-access.md (chmod 600, outside the repo)
It is read once and never printed.

Free tier (as of 2026-07): voyage-4-large ~200M tokens/mo, rerank-2.5 ~200M/mo — plenty for both jobs.
"""
import json, os, re, sys, time, urllib.request, urllib.error
import numpy as np

EMB_MODEL = os.environ.get("VOYAGE_EMB_MODEL", "voyage-4-large")   # best general embedder on the free tier
RERANK_MODEL = os.environ.get("VOYAGE_RERANK_MODEL", "rerank-2.5") # best reranker on the free tier
MAX_ITEMS = 64            # Voyage caps items per embed call
MAX_CHARS = 90000         # ...and total chars per call


def get_key():
    k = os.environ.get("VOYAGE_API_KEY")
    if k:
        return k
    p = os.path.expanduser("~/.testlify-access.md")
    if os.path.exists(p):
        m = re.search(r"pa-[A-Za-z0-9_\-]{20,}", open(p).read())
        if m:
            return m.group(0)
    sys.exit("!! no VOYAGE_API_KEY — set the env var, or put your `pa-...` key in ~/.testlify-access.md")


_KEY = None


def _post(url, body):
    global _KEY
    if _KEY is None:
        _KEY = get_key()
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(),
                headers={"Authorization": f"Bearer {_KEY}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            w = 2 ** attempt
            if e.code == 429:                       # rate limited — back off harder
                w = max(w, 15)
            print(f"   voyage HTTP {e.code} retry {w}s {e.read()[:120]!r}", file=sys.stderr); time.sleep(w)
        except Exception as ex:
            print(f"   voyage err {ex} retry", file=sys.stderr); time.sleep(2 ** attempt)
    raise RuntimeError("voyage call failed after retries")


EMB_WORKERS = int(os.environ.get("VOYAGE_EMB_WORKERS", "8"))   # parallel embed POSTs (Voyage has headroom; _post backs off on 429)


def embed(texts, input_type="document"):
    """Return an (N, dim) float32 array of L2-NORMALISED embeddings (so a dot product == cosine).
    Batches are POSTED IN PARALLEL (EMB_WORKERS) — the calls are I/O-bound, so sequential was ~8x too slow."""
    texts = [t if (t and str(t).strip()) else "untitled" for t in texts]   # Voyage 400s on empty strings
    batches, i = [], 0
    while i < len(texts):                                        # split into order-preserving batches first
        batch, chars = [], 0
        while i < len(texts) and len(batch) < MAX_ITEMS and chars + len(texts[i]) <= MAX_CHARS:
            batch.append(texts[i]); chars += len(texts[i]); i += 1
        if not batch:
            batch = [texts[i][:MAX_CHARS]]; i += 1
        batches.append(batch)

    def _do(b):
        d = _post("https://api.voyageai.com/v1/embeddings",
                  {"input": b, "model": EMB_MODEL, "input_type": input_type})
        return [e["embedding"] for e in sorted(d["data"], key=lambda x: x["index"])]

    from concurrent.futures import ThreadPoolExecutor
    out = []
    with ThreadPoolExecutor(max_workers=min(EMB_WORKERS, len(batches)) or 1) as ex:
        for res in ex.map(_do, batches):                        # ex.map preserves input order
            out.extend(res)
    v = np.asarray(out, dtype=np.float32)
    v /= (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)          # normalise -> dot == cosine
    return v


def rerank(query, docs, top_k):
    d = _post("https://api.voyageai.com/v1/rerank",
              {"query": query, "documents": docs, "model": RERANK_MODEL,
               "top_k": top_k, "return_documents": False})
    return [(r["index"], r["relevance_score"]) for r in d["data"]]
