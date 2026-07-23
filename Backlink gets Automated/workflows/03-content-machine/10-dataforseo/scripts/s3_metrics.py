#!/usr/bin/env python3
"""Step 3 (metrics half) — volume + KD + intent for a keyword list, via keyword_overview.
Feed it the Step-2 shortlist survivors (candidates always come from the two nets, not brainstorm). The LLM
scorer/judge runs separately (prompts in research-plan.md) on this table.
Usage: python3 s3_metrics.py <run_dir> "<kw1>" "<kw2>" ...   (<=700 keywords)
"""
import os, sys, json
import dfs, config

def main():
    run = sys.argv[1]; kws = sys.argv[2:]
    if not kws:  # default: the Step-2 shortlist survivors
        kws = [v["kw"] for v in json.load(open(os.path.join(run, "proof", "02-shortlist.json"))) if v.get("kw")]
    kws = kws[:700]
    proof = os.path.join(run, "proof"); os.makedirs(proof, exist_ok=True)
    resp = dfs.call("/v3/dataforseo_labs/google/keyword_overview/live",
                    [{"location_name": config.LOCATION, "language_code": config.LANGUAGE, "keywords": kws[:700]}])
    config.write_json(f"{proof}/03-overview.json", resp)
    rows = []
    for it in (dfs.first_result(resp).get("items") or []):
        ki = it.get("keyword_info", {}) or {}; kp = it.get("keyword_properties", {}) or {}
        si = it.get("search_intent_info", {}) or {}
        rows.append({"kw": it.get("keyword"), "vol": ki.get("search_volume"),
                     "kd": kp.get("keyword_difficulty"), "intent": si.get("main_intent")})
    rows.sort(key=lambda x: -(x["vol"] or 0))
    config.write_json(f"{proof}/03-metrics.json", rows)
    print(f"{'keyword':<30}{'vol':>7} {'KD':>4}  intent")
    for r in rows:
        print(f"  {str(r['kw'])[:28]:<28}{str(r['vol']):>7} {str(r['kd']):>4}  {r['intent']}")
    print(f"saved -> {proof}/03-overview.json, 03-metrics.json")

if __name__ == "__main__":
    main()
