#!/usr/bin/env python3
"""Proper single-idea REUSE check — the real "do we already have content like this?" answer for one idea.

Reuses the asset-engine's machinery, does NOT reinvent it:
  - `_shared/voyage.py` (voyage-4-large embeddings + rerank-2.5),
  - the 02 content-index (title vectors of every existing page),
  - the 02 reuse-judge prompt (the same verdicts: Already have it / Improve existing / Build from parts / Brand new).

Flow: vectorise the idea → nearest existing pages (semantic) → rerank their real content → LLM verdict.
Used by the spoke pipeline (spoke_idea) so a minted spoke gets a genuine reuse verdict, not a string-match guess.
"""
import os, sys, json, csv, re
import numpy as np
import config, llm

csv.field_size_limit(1 << 24)
sys.path.insert(0, os.path.join(config.REPO_ROOT, "workflows", "02-asset-engine", "_shared"))
import voyage  # noqa: E402

INDEX = os.path.join(config.REPO_ROOT, "projects", config.COMPANY, "02-asset-engine", "clubbed", "_work", "content-index")
CDB = os.path.join(config.REPO_ROOT, "projects", config.COMPANY, "00-foundation", "output", "content-database.csv")
JUDGE = os.path.join(config.REPO_ROOT, "workflows", "02-asset-engine", "5-reuse-check", "prompts", "reuse-judge.md")
N_RETRIEVE, TOPK, DOC_CHARS = 40, 6, 3000
VERDICTS = ["Already have it", "Improve existing", "Build from parts", "Brand new"]

_Vt = _Mt = _content = None


def _load():
    """Load the page-title vectors + a url→content map once (cached in module globals)."""
    global _Vt, _Mt, _content
    if _Vt is not None:
        return _Vt is not False
    vp = os.path.join(INDEX, "title", "vectors.npy")
    if not os.path.exists(vp):
        _Vt = False
        return False
    _Vt = np.nan_to_num(np.load(vp).astype(np.float32))          # guard the matmul (empty-title rows embed to ~0)
    _Mt = [json.loads(l) for l in open(os.path.join(INDEX, "title", "meta.jsonl"), encoding="utf-8")]
    _content = {}
    if os.path.exists(CDB):
        for r in csv.DictReader(open(CDB, encoding="utf-8")):
            u = (r.get("URL") or "").strip().rstrip("/").lower()
            if u:
                _content[u] = r.get("Full content") or ""
    return True


def _text(u):
    return (_content.get(u.rstrip("/").lower(), "") or "")[:DOC_CHARS]


def _run_text(prompt):
    """The judge returns free TEXT (not JSON), so it can't use llm.call_json. But it still needs the same
    transient-CLI retry (a brief CLI hiccup would otherwise drop a spoke unnecessarily). Retry _run with backoff."""
    last = None
    for attempt in range(llm.CLI_RETRIES + 1):
        try:
            return llm._run(prompt)
        except Exception as e:
            last = e
            if attempt < llm.CLI_RETRIES:
                llm._sleep_backoff(attempt, str(e)[:40])
    raise last


def check(title, angle="", fmt=""):
    """Return {'verdict','chosen','why'} for one idea vs our existing content, or None if the index is missing."""
    if not _load():
        return None
    query = f"{title} — {angle}".strip(" —")
    q = voyage.embed([query], "query")[0]
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):   # silence a benign macOS BLAS matmul quirk
        order = np.argsort(_Vt @ q)[::-1][:N_RETRIEVE]           # nearest existing pages by title semantics
    cand = [(_Mt[i]["url"], _Mt[i].get("title", "")) for i in order]
    try:
        ranked = voyage.rerank(query, [_text(u) or t for u, t in cand], min(TOPK, len(cand)))
    except Exception:
        ranked = [(k, 0.0) for k in range(min(TOPK, len(cand)))]
    top = [cand[k] for k, _ in ranked]
    block = "\n\n".join(f"[{i+1}] {t} — {u}\n{_text(u) or '(no text on file)'}" for i, (u, t) in enumerate(top))
    prompt = (open(JUDGE).read().replace("{{BRAND}}", config.BRAND).replace("{{ASSET}}", title)
              .replace("{{ANGLE}}", angle or "").replace("{{FORMAT}}", fmt or "article").replace("{{CANDIDATES}}", block))
    raw = _run_text(prompt)                                       # the judge prompt returns TEXT lines, not JSON
    v = re.search(r"(?im)^\s*Reuse verdict:\s*(.+)$", raw)
    ch = re.search(r"(?im)^\s*Chosen links:\s*(.+)$", raw)
    why = re.search(r"(?im)^\s*Why:\s*(.+)$", raw)
    verdict = next((x for x in VERDICTS if v and x.lower() in v.group(1).lower()), "Brand new")
    return {"verdict": verdict, "chosen": (ch.group(1).strip() if ch else ""), "why": (why.group(1).strip() if why else "")}


if __name__ == "__main__":
    print(check(sys.argv[1] if len(sys.argv) > 1 else "Skill Gap Analysis for Hiring",
                "a pre-hire screening framework to catch skills shortfalls before the offer"))
