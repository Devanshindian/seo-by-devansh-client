#!/usr/bin/env python3
"""Stage 2c — assign every post to its dominant-pain tension (parallel, sharded).

Reads:  scraped Posts tab + _work/tensions_base.json
Writes: _work/post-tension-map.tsv    post_id<TAB>tension_id (or 'misc')   — every post exactly once

The verify gate (COVERAGE) requires: every scraped post_id present exactly once, misc <= 15%. LLM JUDGMENT.
"""
import argparse, csv, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c
sys.path.insert(0, c.SHARED)
import llm
import _posts

PROMPT = TLIST = None
VALID = set()


def _shard(cards):
    block = "\n\n".join(_posts.card(p) for p in cards)
    prompt = PROMPT.replace("{{BRAND}}", c.BRAND).replace("{{TENSIONS}}", TLIST).replace("{{CARDS}}", block)
    try:
        out = llm.call_json(prompt).get("assignments", [])
    except Exception as e:
        print(f"   !! an assign shard failed ({str(e)[:40]}) — its posts -> misc")
        return {p["post_id"]: "misc" for p in cards}
    got = {a.get("post_id"): a.get("tension_id", "misc") for a in out if a.get("post_id")}
    return {p["post_id"]: (got.get(p["post_id"]) if got.get(p["post_id"]) in VALID else "misc") for p in cards}


def run(redo=False):
    global PROMPT, TLIST, VALID
    PROMPT = llm.load_prompt("2c-assign.md")
    tensions = json.load(open(os.path.join(c.WORK, "tensions_base.json")))
    VALID = {t["tension_id"] for t in tensions}
    TLIST = "\n".join(f"{t['tension_id']} | {t['tension']}" for t in tensions)
    posts = _posts.load_posts()
    shards = [posts[i:i + c.ASSIGN_SHARD] for i in range(0, len(posts), c.ASSIGN_SHARD)]
    print(f"   assigning {len(posts)} posts to {len(tensions)} tensions ({len(shards)} shards) ...")
    amap = {}
    with ThreadPoolExecutor(max_workers=c.PHRASE_WORKERS) as ex:
        futs = [ex.submit(_shard, s) for s in shards]
        for fut in as_completed(futs):
            amap.update(fut.result())

    ids = [p["post_id"] for p in posts]
    for pid in ids:
        amap.setdefault(pid, "misc")
    assert set(amap) == set(ids), "assignment coverage broke"
    path = os.path.join(c.WORK, "post-tension-map.tsv")
    with open(path + ".tmp", "w") as f:
        f.write("post_id\ttension\n")
        for pid in ids:
            f.write(f"{pid}\t{amap[pid]}\n")
    os.replace(path + ".tmp", path)
    misc = sum(1 for pid in ids if amap[pid] == "misc")
    pct = 100 * misc / max(len(ids), 1)
    print(f"   assigned {len(ids)} posts · misc {misc} ({pct:.0f}%) -> {c.rel(path)}")
    if pct > c.MISC_MAX_PCT:
        print(f"   ⚠ misc {pct:.0f}% exceeds {c.MISC_MAX_PCT:.0f}% — the verify gate will fail; consider fewer/looser tensions")
    return amap


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
