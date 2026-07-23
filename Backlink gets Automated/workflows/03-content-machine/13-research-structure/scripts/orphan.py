"""Step 7 — orphan check. Against the brief's EXISTING keyword pool (no new API calls): any high-demand
keyword no H2 covers is flagged (a searched topic the content-first build may have missed).

Reads: the sections + the DataForSEO run's proof/03-metrics.json (the broad pool). Returns an orphan list.
"""
import os, sys, json
import config, llm

TEMPLATE = llm.load_prompt("orphan.md")
HIGH_VOL = config.HIGH_VOL    # "high-demand" bar for the orphan check (lives in config, C1)


def run(sections, slug, pool_path=None):
    path = pool_path or os.path.join(config.DFS_RUNS, slug, "proof", "03-metrics.json")
    if not os.path.exists(path):
        print("  orphan check skipped (no keyword pool found)")
        return []
    pool = json.load(open(path))
    hot = [r for r in pool if (r.get("vol") or 0) >= HIGH_VOL
           and r.get("kd") is not None and r["kd"] < config.KD_CEIL]
    hot.sort(key=lambda x: -(x["vol"] or 0))
    hot = hot[:40]
    if not hot:
        return []
    secs = "\n".join(f"- {s['h2']}" for s in sections)
    kws = "\n".join(f"{r['kw']} | {r['vol']}" for r in hot)
    try:
        orphans = llm.call_json(TEMPLATE.replace("{{SECTIONS}}", secs)
                                .replace("{{KEYWORDS}}", kws)).get("orphans", [])
    except Exception as e:
        print(f"  orphan check failed: {e}")
        return []
    print(f"  orphan keywords: {len(orphans)}")
    for o in orphans:
        print(f"    - {o.get('keyword')} ({o.get('volume')})")
    return orphans


if __name__ == "__main__":
    sections = json.load(open(sys.argv[1]))["sections"]
    print(json.dumps(run(sections, sys.argv[2]), indent=2))
