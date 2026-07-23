#!/usr/bin/env python3
"""Step 2 — free filter on volume + KD (no API). Reads the merged pool, keeps the survivors.
Usage: python3 s2_filter.py <run_dir>
"""
import os, sys, json
import config

def main():
    run = sys.argv[1]
    proof = os.path.join(run, "proof")
    pool = json.load(open(f"{proof}/01-pool.json"))
    short = [v for v in pool if (v["vol"] or 0) >= config.VOL_FLOOR
             and (v["kd"] is None or v["kd"] <= config.KD_CEIL)]
    short.sort(key=lambda x: -(x["vol"] or 0))
    config.write_json(f"{proof}/02-shortlist.json", short)
    print(f"pool {len(pool)} -> shortlist {len(short)} (vol>={config.VOL_FLOOR}, KD<={config.KD_CEIL})")
    print("top 25 by volume (the scorer in Step 3 removes off-topic ones):")
    for v in short[:25]:
        print(f"  {str(v['kw'])[:46]:<46} vol={v['vol']:>7}  KD={v['kd']}")
    print(f"saved -> {proof}/02-shortlist.json")

if __name__ == "__main__":
    main()
