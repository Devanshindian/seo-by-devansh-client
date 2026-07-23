#!/usr/bin/env python3
"""Stage 2a — tag every post with 2-3 phrases (parallel, sharded).

Reads:  the scraped Posts tab
Writes: _work/all-phrases.tsv    post_id<TAB>comma-joined phrases   (every post_id, even if empty)

Embarrassingly parallel: each shard of posts is read independently (the CLI equivalent of the recipe's
parallel Sonnet sub-agents). Validate: every post covered exactly once. LLM JUDGMENT.
"""
import argparse, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c
sys.path.insert(0, c.SHARED)
import llm
import _posts

PROMPT = None


def _shard(cards):
    block = "\n\n".join(_posts.card(p) for p in cards)
    prompt = PROMPT.replace("{{BRAND}}", c.BRAND).replace("{{CARDS}}", block)
    try:
        out = llm.call_json(prompt).get("posts", [])
    except Exception as e:
        print(f"   !! a shard failed ({str(e)[:40]}) — its posts get empty phrases")
        return {p["post_id"]: [] for p in cards}
    got = {r.get("post_id"): [x for x in r.get("phrases", []) if x] for r in out if r.get("post_id")}
    return {p["post_id"]: got.get(p["post_id"], []) for p in cards}    # force every post_id present


def run(redo=False):
    global PROMPT
    PROMPT = llm.load_prompt("2a-phrases.md")
    posts = _posts.load_posts()
    shards = [posts[i:i + c.PHRASE_SHARD] for i in range(0, len(posts), c.PHRASE_SHARD)]
    print(f"   {len(posts)} posts -> {len(shards)} shards ({c.PHRASE_WORKERS} parallel) ...")
    phrases = {}
    with ThreadPoolExecutor(max_workers=c.PHRASE_WORKERS) as ex:
        futs = [ex.submit(_shard, s) for s in shards]
        for n, fut in enumerate(as_completed(futs), 1):
            phrases.update(fut.result())
            if n % 5 == 0:
                print(f"   ...{n}/{len(shards)} shards done")

    ids = [p["post_id"] for p in posts]
    assert set(phrases) == set(ids), f"phrase coverage broke: missing {set(ids) - set(phrases)}"
    os.makedirs(c.WORK, exist_ok=True)
    path = os.path.join(c.WORK, "all-phrases.tsv")
    with open(path + ".tmp", "w") as f:
        f.write("post_id\tphrases\n")
        for pid in ids:
            f.write(f"{pid}\t{', '.join(phrases[pid])}\n")
    os.replace(path + ".tmp", path)
    tagged = sum(1 for pid in ids if phrases[pid])
    print(f"   {tagged}/{len(ids)} posts got phrases -> {c.rel(path)}")
    return phrases


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
