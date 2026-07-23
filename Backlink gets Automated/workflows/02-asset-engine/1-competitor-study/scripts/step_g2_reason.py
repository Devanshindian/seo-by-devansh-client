#!/usr/bin/env python3
"""Step G2 — per-row reasoning at scale: turn each competitor page into an asset idea (gap→asset→angle).

Reads:  _work/g_sheet.json          (G1: rows + Row ID + text_dup flags)
        output/brand-scope.md       (G0: the approved anchor — MUST exist and be human-approved)
Writes: _work/g2_out/<shard>__<n>.json   (one file per 5-row batch — resumable, re-run skips done)
        _work/g2_sheet.json         (every row with brand_fit / angle_gap / asset / distinct_angle filled)

The recipe's rules, encoded:
 - SHARD BY FORMAT so like pages travel together (cleaner G3 merge).
 - TINY BATCHES (~5 rows). Never a big block — given many rows at once the model pattern-matches ACROSS
   the batch and goes generic. Five keeps its attention on each page. So: many small parallel passes.
 - Fast mid-tier model (Sonnet) for the bulk; the strong model is reserved for G3.
 - Each pass receives the approved brand-scope + the anti-template guardrail (in the prompt) + its ~5
   rows WITH FULL PAGE TEXT (never just the title).

Rows we do NOT send to the model (handled without a paid call):
 - text_dup rows  -> inherit their survivor's idea after stitching (same text = same idea; F1).
 - not-readable   -> brand_fit=SKIP, notes 'SKIP — no readable body' (the recipe's SKIP bucket).
"""
import argparse, json, os, sys, collections
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c
sys.path.insert(0, c.SHARED)
import llm
c.LLM_MODEL = c.G2_MODEL          # mid-tier for the bulk passes; llm.py reads this same module (F5)

_OUTCOLS = ("brand_fit", "angle_gap", "asset", "distinct_angle", "tool_escalation", "g_notes")
PROMPT = None


def _needs_reasoning(r):
    """Readable, unique text, not already a SKIP. text_dup and unreadable rows are handled in code."""
    return (r.get("read_status") == "ok" and (r.get("body") or "").strip()
            and not r.get("text_dup_of"))


def _row_block(r):
    body = (r.get("body") or "")[:c.G2_BODY_CHARS]
    h1 = "; ".join(r.get("h1") or [])
    return (f"### row_id={r['row_id']}\n"
            f"format: {r.get('format','?')}\n"
            f"competitor: {r.get('competitor','?')}\n"
            f"referring domains (follow): {r.get('domains_follow',0)}\n"
            f"url: {r.get('url','')}\n"
            f"title: {(r.get('title') or '')[:160]}\n"
            f"h1: {h1[:200]}\n"
            f"PAGE TEXT:\n{body}")


def reason_batch(batch, scope):
    prompt = (PROMPT.replace("{{BRAND}}", c.BRAND)
              .replace("{{BRAND_SCOPE}}", scope)
              .replace("{{ROWS}}", "\n\n".join(_row_block(r) for r in batch)))
    out = llm.call_json(prompt)
    by_id = {int(o.get("row_id", -1)): o for o in (out.get("rows") or [])}
    res = []
    for r in batch:
        o = by_id.get(r["row_id"]) or {}
        res.append({"row_id": r["row_id"],
                    "brand_fit": o.get("brand_fit") or "SKIP",
                    "angle_gap": o.get("angle_gap") or "",
                    "asset": o.get("asset") or "",
                    "distinct_angle": o.get("distinct_angle") or "",
                    # NB: the model also echoes `format` (to commit to keeping it), but the AUTHORITATIVE
                    # format is the Step D tag already on the row (F1 — decided once). We do NOT overwrite it.
                    "tool_escalation": o.get("tool_escalation") or "",
                    "g_notes": o.get("notes") or ""})
    return res


def run(redo=False):
    global PROMPT
    PROMPT = llm.load_prompt("g2-reason-rows.md")
    scope_path = os.path.join(c.OUT, "brand-scope.md")
    if not os.path.exists(scope_path):
        sys.exit("!! no output/brand-scope.md — run step_g0_scope.py and APPROVE it first (G0 is a gate)")
    scope = open(scope_path).read().strip()
    sheet_path = os.path.join(c.WORK, "g_sheet.json")
    if not os.path.exists(sheet_path):
        sys.exit("!! no _work/g_sheet.json — run step_g1_sheet.py first")
    rows = json.load(open(sheet_path))
    by_id = {r["row_id"]: r for r in rows}

    todo = [r for r in rows if _needs_reasoning(r)]
    # shard by format, then cut each shard into 5-row batches
    shards = collections.defaultdict(list)
    for r in todo:
        shards[(r.get("format") or "UNTAGGED")].append(r)
    batches = []                        # (shard_slug, batch_index, [rows])
    for fmt, frows in shards.items():
        slug = "".join(ch if ch.isalnum() else "-" for ch in fmt.lower())[:32]
        for i in range(0, len(frows), c.G2_BATCH):
            batches.append((slug, i // c.G2_BATCH, frows[i:i + c.G2_BATCH]))
    outdir = os.path.join(c.WORK, "g2_out")
    os.makedirs(outdir, exist_ok=True)
    print(f"   {len(todo)} rows to reason over · {len(batches)} batches of {c.G2_BATCH} "
          f"· model={c.G2_MODEL} · {c.G2_WORKERS} parallel")

    def do(job):
        slug, idx, batch = job
        fp = os.path.join(outdir, f"{slug}__{idx}.json")
        if os.path.exists(fp) and not redo:
            return json.load(open(fp)), True
        res = reason_batch(batch, scope)
        c.write_json(fp, res)
        return res, False

    done_cache = fresh = failed = 0
    with ThreadPoolExecutor(max_workers=c.G2_WORKERS) as ex:
        futs = {ex.submit(do, j): j for j in batches}
        for n, fut in enumerate(as_completed(futs), 1):
            slug, idx, batch = futs[fut]
            try:
                res, cached = fut.result()
                done_cache += cached; fresh += (0 if cached else 1)
            except llm._FatalCLIError as e:
                sys.exit(f"\n!! {e}")
            except Exception as e:
                failed += 1
                print(f"   !! batch {slug}__{idx} failed: {str(e)[:80]}")
            if n % 25 == 0:
                print(f"   ...{n}/{len(batches)} batches")

    # stitch every batch back onto the master rows (by row_id)
    for slug in {b[0] for b in batches}:
        pass
    filled = 0
    for fp in os.listdir(outdir):
        if not fp.endswith(".json"):
            continue
        for o in json.load(open(os.path.join(outdir, fp))):
            r = by_id.get(o["row_id"])
            if not r:
                continue
            r["brand_fit"] = o["brand_fit"]; r["angle_gap"] = o["angle_gap"]
            r["asset"] = o["asset"]; r["distinct_angle"] = o["distinct_angle"]
            r["tool_escalation"] = o.get("tool_escalation", ""); r["g_notes"] = o["g_notes"]
            filled += 1

    # text_dup rows inherit their survivor's idea (same text = same idea); unreadable rows -> SKIP
    for r in rows:
        if r.get("text_dup_of") is not None and r.get("text_dup_of") != "":
            s = by_id.get(r["text_dup_of"])
            if s:
                for col in _OUTCOLS:
                    r[col] = s.get(col, "")
                r["g_notes"] = (r.get("g_notes") or "") + " [text_dup — idea from survivor]"
        elif not _needs_reasoning(r) and r.get("text_dup_of") in (None, ""):
            if not r.get("brand_fit"):
                r["brand_fit"] = "SKIP"; r["g_notes"] = r.get("g_notes") or "SKIP — no readable body"

    c.write_json(os.path.join(c.WORK, "g2_sheet.json"), rows)
    # validate: every row that needed reasoning has a brand_fit
    missing = [r["row_id"] for r in todo if not r.get("brand_fit")]
    print(f"\n   batches: {fresh} fresh, {done_cache} cached, {failed} failed")
    print(f"   rows filled by model: {filled}")
    if missing:
        print(f"   !! {len(missing)} reasoned rows came back empty — RE-RUN to fill (resumable). e.g. {missing[:8]}")
    fits = collections.Counter(r.get("brand_fit") for r in rows if r.get("brand_fit"))
    print(f"   brand_fit spread: {dict(fits)}")
    print(f"   -> {c.rel(os.path.join(c.WORK, 'g2_sheet.json'))}")
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
