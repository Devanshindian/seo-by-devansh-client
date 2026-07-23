#!/usr/bin/env python3
"""Step D — tag every kept page by FORMAT (its shape), the key everything downstream groups by.

CHANGED FROM THE ORIGINAL, deliberately (Devansh approved 2026-07-20). The hand-run tagged format with
a regex over the URL. Measured result: 654 of 2,469 pages (26%) fell into "Other / editorial", and it
found exactly ONE calculator across the whole study — in a niche full of them. Format is the sharding
key for the per-row reasoning AND the clustering key for the merge, so a bad tag poisons everything
after it. Per "script the structure, LLM for the judgment", this is a judgment.

What makes it possible now: DataForSEO returns each page's real H1/H2 headings, word count, image count
and outbound-link count (E0, 2026-07-20) — so the model reads what the page IS instead of guessing from
its address. The old Semrush export carried none of that.

Reads:  _work/candidates/<domain>.json
Writes: _work/formats/<domain>.json      (rows + format/confidence/why)
        _work/format-tags.json           (flat, all competitors)
Resumable per competitor; batched; JSONL-free (structured JSON per batch).
"""
import argparse, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c
sys.path.insert(0, c.SHARED)
import llm

PROMPT = None


def _page_block(rows):
    """What the model sees. Headings first — they are the evidence; the URL is only a hint."""
    out = []
    for r in rows:
        h1 = "; ".join(r.get("h1") or [])[:150]
        h2 = " | ".join(r.get("h2") or [])[:600]
        out.append(
            f"### id={r['_id']}\n"
            f"url: {r.get('url','')}\n"
            f"title: {(r.get('title') or '')[:160]}\n"
            f"h1: {h1 or '(none captured)'}\n"
            f"h2: {h2 or '(none captured)'}\n"
            f"words: {r.get('words') or 'unknown'} · images: {r.get('images') or 0} · "
            f"outbound links: {r.get('ext_links') or 0}")
    return "\n\n".join(out)


def tag_batch(rows):
    p = (PROMPT.replace("{{BRAND}}", c.BRAND).replace("{{PAGES}}", _page_block(rows)))
    out = llm.call_json(p)
    by_id = {str(t.get("id")): t for t in (out.get("tags") or [])}
    for r in rows:
        t = by_id.get(str(r["_id"])) or {}
        r["format"] = t.get("format") or "UNTAGGED"
        r["format_confidence"] = t.get("confidence") or ""
        r["format_why"] = t.get("why") or ""
        r["new_format"] = bool(t.get("new_format"))
    return rows


def run(redo=False):
    global PROMPT
    PROMPT = open(os.path.join(c.PROMPTS, "tag-format.md")).read()
    os.makedirs(os.path.join(c.WORK, "formats"), exist_ok=True)
    cand_dir = os.path.join(c.WORK, "candidates")
    files = sorted(f for f in os.listdir(cand_dir) if f.endswith(".json"))
    if not files:
        sys.exit("!! no _work/candidates/*.json — run step_c_filter.py first")

    flat = []
    for f in files:
        domain = f[:-5]
        out_path = os.path.join(c.WORK, "formats", f)
        if os.path.exists(out_path) and not redo:
            rows = json.load(open(out_path))
            flat += rows
            print(f"   {domain:26s} {len(rows):>4} (cached)")
            continue
        rows = json.load(open(os.path.join(cand_dir, f)))
        if not rows:
            c.write_json(out_path, [])
            print(f"   {domain:26s}    0 (nothing kept)")
            continue
        for i, r in enumerate(rows):
            r["_id"] = f"{domain[:6]}{i}"
        batches = [rows[i:i + c.TAG_BATCH] for i in range(0, len(rows), c.TAG_BATCH)]
        done = []
        with ThreadPoolExecutor(max_workers=c.TAG_WORKERS) as ex:
            futs = {ex.submit(tag_batch, b): b for b in batches}
            for fut in as_completed(futs):
                try:
                    done += fut.result()
                except Exception as e:
                    b = futs[fut]
                    for r in b:
                        r["format"], r["format_why"] = "UNTAGGED", f"tagging failed: {str(e)[:60]}"
                    done += b
                    print(f"   !! a batch failed for {domain}: {str(e)[:70]}")
        done.sort(key=lambda r: -r.get("domains_follow", 0))
        c.write_json(out_path, done)
        flat += done
        untagged = sum(1 for r in done if r["format"] == "UNTAGGED")
        print(f"   {domain:26s} {len(done):>4} tagged" + (f"  !! {untagged} UNTAGGED" if untagged else ""))

    c.write_json(os.path.join(c.WORK, "format-tags.json"), flat)
    counts = {}
    for r in flat:
        counts[r.get("format", "?")] = counts.get(r.get("format", "?"), 0) + 1
    print(f"\n   {len(flat)} pages tagged into {len(counts)} formats")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"     {v:>5}  {k}")
    lazy = sum(v for k, v in counts.items() if k.lower().startswith(("other", "untagged")))
    print(f"\n   'Other'/UNTAGGED: {lazy} = {100*lazy/max(len(flat),1):.0f}%   "
          f"(the regex tagger it replaces: 26%)")
    return flat


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
