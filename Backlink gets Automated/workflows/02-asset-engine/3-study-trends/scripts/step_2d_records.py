#!/usr/bin/env python3
"""Stage 2d — build the tension record per tension -> tensions.csv.

Reads:  _work/tensions_base.json · _work/post-tension-map.tsv · scraped Posts tab
Writes: output/tensions.csv   one row per tension: LLM fields (core pain / audience / emotion / best example /
                              quotes / sub-questions / implied data) + mechanical counts. Verdict cols blank (Stage 3).

Written AFTER merge-check.md (Stage 2b) — the verify gate checks that timestamp order. LLM + mechanical.
"""
import argparse, collections, csv, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c
sys.path.insert(0, c.SHARED)
import llm
import _posts

COLS = ["tension_id", "Tension", "Phrases", "Core pain", "Audience", "Emotion", "# posts", "Post list",
        "Total upvotes", "Total comments", "Avg debate ratio", "Subreddit spread", "Best example",
        "Representative quotes", "Sub-questions", "Implied data point",
        "Linkability verdict", "Ownability verdict", "Verdict"]


def run(redo=False):
    tensions = json.load(open(os.path.join(c.WORK, "tensions_base.json")))
    posts = {p["post_id"]: p for p in _posts.load_posts()}
    pile = collections.defaultdict(list)
    for row in csv.DictReader(open(os.path.join(c.WORK, "post-tension-map.tsv")), delimiter="\t"):
        if row["tension"] != "misc":
            pile[row["tension"]].append(row["post_id"])

    # LLM judgment fields — SHARDED over tensions (one batched call chokes on many tensions' rich output), parallel
    PROMPT = llm.load_prompt("2d-records.md")

    def _block(t):
        titles = "; ".join((posts.get(pid, {}).get("title") or "")[:80] for pid in pile.get(t["tension_id"], [])[:8])
        return (f"{t['tension_id']} | {t['tension']}\n   phrases: " +
                "; ".join(ph["phrase"] for ph in t["phrases"]) + f"\n   sample post titles: {titles}")

    def _shard(batch):
        p = (PROMPT.replace("{{BRAND}}", c.BRAND).replace("{{EMOTIONS}}", ", ".join(c.EMOTIONS))
             .replace("{{TENSIONS}}", "\n".join(_block(t) for t in batch)))
        try:
            return {str(r["tension_id"]): r for r in llm.call_json(p).get("records", []) if "tension_id" in r}
        except Exception as e:
            print(f"   !! a records shard failed ({str(e)[:40]}) — those tensions get defaults")
            return {}

    shards = [tensions[i:i + c.RECORDS_SHARD] for i in range(0, len(tensions), c.RECORDS_SHARD)]
    print(f"   building {len(tensions)} records in {len(shards)} shards ({c.PHRASE_WORKERS} parallel) ...")
    recs = {}
    with ThreadPoolExecutor(max_workers=c.PHRASE_WORKERS) as ex:
        for fut in as_completed([ex.submit(_shard, s) for s in shards]):
            recs.update(fut.result())

    rows = []
    for t in tensions:
        tid = t["tension_id"]
        ids = pile.get(tid, [])
        ps = [posts[i] for i in ids if i in posts]
        up = sum(int(x.get("score") or 0) for x in ps)
        com = sum(int(x.get("comment_count") or 0) for x in ps)
        rec = recs.get(tid, {})
        emo = (rec.get("emotion") or "").lower()
        if emo not in c.EMOTIONS:
            emo = "anger"
        best = rec.get("best_example")
        if best not in ids:                                       # fall back to the loudest post in the pile
            best = max(ids, key=lambda i: int(posts.get(i, {}).get("score") or 0)) if ids else ""
        rows.append({
            "tension_id": tid, "Tension": t["tension"],
            "Phrases": "; ".join(ph["phrase"] for ph in t["phrases"]),
            "Core pain": rec.get("core_pain", ""), "Audience": rec.get("audience", ""), "Emotion": emo,
            "# posts": len(ids), "Post list": " ".join(ids),
            "Total upvotes": up, "Total comments": com,
            "Avg debate ratio": round(com / up, 3) if up else 0,
            "Subreddit spread": ", ".join(sorted({posts.get(i, {}).get("subreddit", "") for i in ids} - {""})),
            "Best example": (posts.get(best, {}).get("url") or best),
            "Representative quotes": " || ".join(rec.get("representative_quotes", []) or []),
            "Sub-questions": "; ".join(rec.get("sub_questions", []) or []),
            "Implied data point": rec.get("implied_data_point", ""),
            "Linkability verdict": "", "Ownability verdict": "", "Verdict": "",
        })
    os.makedirs(c.OUT, exist_ok=True)
    path = os.path.join(c.OUT, "tensions.csv")
    with open(path + ".tmp", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    os.replace(path + ".tmp", path)
    print(f"   {len(rows)} tension records -> {c.rel(path)}")
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
