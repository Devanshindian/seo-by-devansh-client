#!/usr/bin/env python3
"""Step 2 — Stage 3 JUDGE: the LLM verdict per idea (the core — reading + judgment, not similarity).

Reads:  output/clubbed-ideas.csv (RAG candidates filled by step 1)  ·  content-database.csv (page text)
Writes: output/clubbed-ideas.csv  — fills THREE columns (single source of truth):
          Reuse verdict   one of: Already have it / Improve existing / Build from parts / Brand new
          Chosen links    the verdict's link(s) — a SUBSET of RAG candidates (never an invented URL)
          Why             a short paragraph citing what the page(s) have or lack
        _work/reuse-judge-results.jsonl  every landed verdict (append-only, so the run is resumable)

Each idea is judged in parallel against the top-N RAG candidates. The candidate page TEXT is NOT stored
in the clubbed sheet (links only) — it is fetched on demand here, BY URL, from content-database.csv's
`Full content`. Ported from projects/.../clubbed/_work/stage3_judge.py; the LLM call goes through the
shared _shared/llm.py caller (headless CLI, no API key), never a bespoke subprocess.
"""
import argparse, csv, json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c
sys.path.insert(0, c.SHARED)                                  # noqa: E402
import llm                                                    # noqa: E402

csv.field_size_limit(1 << 24)
_URL_RE = re.compile(r"https?://[^\s;()]+")
_lock = threading.Lock()


def _rag_urls(cell):
    """Ordered candidate URLs parsed from a `Title — url (score); ...` RAG-candidates cell."""
    out, seen = [], set()
    for m in _URL_RE.finditer(cell or ""):
        u = m.group(0).rstrip(".,"); k = u.rstrip("/").lower()
        if k not in seen:
            seen.add(k); out.append(u)
    return out


def _load_content(content_csv):
    cmap, tmap = {}, {}
    with open(content_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            u = (row.get("URL") or "").strip()
            if u:
                cmap[u.rstrip("/").lower()] = row.get("Full content", "") or ""
                tmap[u.rstrip("/").lower()] = row.get("Title", "") or ""
    return cmap, tmap


def build_prompt(r, cand_urls, cmap, tmap):
    """Fill the verbatim judge prompt: asset fields + the top-N candidates' FULL TEXT (fetched by URL)."""
    blocks = []
    for i, u in enumerate(cand_urls, 1):
        key = u.rstrip("/").lower()
        body = (cmap.get(key) or "").replace("\x00", " ").strip()
        if not body:
            continue                                          # no text on file -> can't be judged, skip it
        title = tmap.get(key) or ""
        blocks.append(f"--- CANDIDATE {i} — {title} · {u} ---\n{body[: c.JUDGE_DOC_CHARS]}")
    tmpl = llm.load_prompt("reuse-judge.md")
    return (tmpl.replace("{{BRAND}}", c.BRAND)
                .replace("{{ASSET}}", r.get("Asset", "") or "")
                .replace("{{ANGLE}}", r.get("Distinct angle", "") or "")
                .replace("{{FORMAT}}", r.get("Format", "") or "(none specified)")
                .replace("{{CANDIDATES}}", "\n\n".join(blocks) if blocks else "(no candidates)"))


def parse(out):
    """Pull the three fields (stage3_judge.py parse — [ \\t] so 'Chosen links' can't eat the newline)."""
    v = re.search(r'(?im)^[ \t]*Reuse verdict:[ \t]*(.+?)[ \t]*$', out or "")
    l = re.search(r'(?im)^[ \t]*Chosen links:[ \t]*(.*)$', out or "")
    w = re.search(r'(?is)\bWhy:\s*(.+)$', out or "")
    if not v:
        return None
    verdict = re.sub(r'^[^A-Za-z]*', '', v.group(1)).strip()   # strip any emoji/punct prefix
    match = next((vd for vd in c.VERDICTS if vd.lower() in verdict.lower()), None)
    if not match:
        return None
    return {"verdict": match,
            "links": (l.group(1).strip() if l else ""),
            "why": (w.group(1).strip() if w else "")}


def _enforce_subset(links_str, cand_urls):
    """Chosen links ⊆ the candidates the judge saw — drop any invented URL (F2, hard rule)."""
    allowed = {u.rstrip("/").lower(): u for u in cand_urls}
    kept = []
    for m in _URL_RE.finditer(links_str or ""):
        u = m.group(0).rstrip(".,"); k = u.rstrip("/").lower()
        if k in allowed and allowed[k] not in kept:
            kept.append(allowed[k])
    return "; ".join(kept)


def judge_one(i, r, cmap, tmap):
    cand_urls = _rag_urls(r.get("RAG candidates", ""))[: c.JUDGE_READ_WINDOW]
    if not cand_urls:                                         # no candidates -> nothing to reuse -> Brand new
        return i, {"verdict": "Brand new", "links": "",
                   "why": "No existing pages were retrieved for this asset, so there is nothing to reuse — build from scratch."}
    prompt = build_prompt(r, cand_urls, cmap, tmap)
    for _ in range(c.JUDGE_PARSE_RETRIES + 1):
        try:
            out = llm.call_text(prompt)                       # transient CLI failures handled inside llm.py
        except Exception as e:
            print(f"      row {i}: call failed ({str(e)[:50]})", flush=True)
            out = ""
        parsed = parse(out)
        if parsed:
            parsed["links"] = _enforce_subset(parsed["links"], cand_urls) if parsed["verdict"] != "Brand new" else ""
            return i, parsed
    print(f"      row {i}: unparseable after retries (left for resume)", flush=True)
    return i, None


def _merge_into_csv(rows, fields, results):
    for i, d in results.items():
        rows[i]["Reuse verdict"] = d["verdict"]
        rows[i]["Chosen links"] = d["links"]
        rows[i]["Why"] = d["why"]
    d = os.path.dirname(c.CLUBBED) or "."
    import tempfile
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".csv.tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader(); w.writerows(rows)
        os.replace(tmp, c.CLUBBED)
    except BaseException:
        try: os.remove(tmp)
        except OSError: pass
        raise


def run(redo=False):
    if not os.path.exists(c.CLUBBED):
        sys.exit(f"!! no clubbed pool at {c.rel(c.CLUBBED)} — run step 1 first.")
    with open(c.CLUBBED, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f); fields = reader.fieldnames; rows = list(reader)
    for col in c.STAGE3_COLS:
        if col not in fields:
            sys.exit(f"!! clubbed sheet is missing the '{col}' column.")
    cmap, tmap = _load_content(c.CATALOGUE_CSV)

    res_path = os.path.join(c.WORK, "reuse-judge-results.jsonl")
    if redo and os.path.exists(res_path):
        os.remove(res_path)
    results = {}
    if os.path.exists(res_path):
        for line in open(res_path, encoding="utf-8"):
            d = json.loads(line); results[d["i"]] = {"verdict": d["verdict"], "links": d["links"], "why": d["why"]}

    todo = [i for i, r in enumerate(rows)
            if i not in results and (redo or not (r.get("Reuse verdict") or "").strip())]
    print(f"   Stage 3: {len(todo)} to judge, {len(results)} already done, {c.JUDGE_WORKERS} workers", flush=True)

    n = 0
    os.makedirs(c.WORK, exist_ok=True)
    with ThreadPoolExecutor(max_workers=c.JUDGE_WORKERS) as ex:
        futs = {ex.submit(judge_one, i, rows[i], cmap, tmap): i for i in todo}
        for fut in as_completed(futs):
            i, parsed = fut.result()
            if not parsed:
                continue
            results[i] = parsed
            with _lock:
                with open(res_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"i": i, **parsed}) + "\n")
            n += 1
            print(f"      [{n}/{len(todo)}] row {i} -> {parsed['verdict']}", flush=True)
            if n % 50 == 0:
                _merge_into_csv(rows, fields, results); print("      (merged into CSV)", flush=True)

    _merge_into_csv(rows, fields, results)
    c.write_text(c.STAGE3_DONE, "")                           # orchestrator resume marker
    from collections import Counter
    verdicts = Counter(rows[i].get("Reuse verdict", "") for i in range(len(rows)) if rows[i].get("Reuse verdict"))
    print(f"   Stage 3 done: {n} judged this run. verdicts so far: {dict(verdicts)} -> {c.rel(c.CLUBBED)}", flush=True)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
