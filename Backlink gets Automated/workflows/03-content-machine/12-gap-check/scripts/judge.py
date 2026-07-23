"""Step 1 — Coverage judge. One Prompt-1 call per brief item (whole dossier in each call).
Reads:  coverage-items.json (from parse_brief) + the STORM polished dossier.
Writes: coverage-verdicts.json — [ {id, item, type, verdict, reason, evidence}, ... ]
"""
import sys, json
from concurrent.futures import ThreadPoolExecutor, as_completed
import config, llm

TEMPLATE = llm.load_prompt("coverage-judge.md")


def judge_item(item, meta, dossier):
    ctx = f"context: {item['context']}" if item.get("context") else ""
    prompt = (TEMPLATE
              .replace("{{ASSET_TITLE}}", meta["asset_title"])
              .replace("{{DISTINCT_ANGLE}}", meta["distinct_angle"])
              .replace("{{ITEM_TYPE}}", item["type"])
              .replace("{{ITEM_TEXT}}", item["item"])
              .replace("{{ITEM_CONTEXT}}", ctx)
              .replace("{{DOSSIER_TEXT}}", dossier))
    v = llm.call_json(prompt)
    return {"id": item["id"], "type": item["type"], "item": item["item"],
            "verdict": str(v.get("verdict", "")).strip().lower(),
            "reason": v.get("reason", ""), "evidence": v.get("evidence", "")}


def run(items_path, dossier_path, out_path):
    meta = json.load(open(items_path))
    dossier = open(dossier_path).read()
    items = [i for i in meta["items"] if i["type"] in config.JUDGED_TYPES]
    verdicts = [None] * len(items)
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        futs = {ex.submit(judge_item, it, meta, dossier): n for n, it in enumerate(items)}
        for f in as_completed(futs):
            n = futs[f]
            verdicts[n] = f.result()
            v = verdicts[n]
            print(f"  [{v['verdict']:8}] {v['type']:13} {v['item'][:60]}")
    config.write_json(out_path, {"asset_title": meta["asset_title"], "distinct_angle": meta["distinct_angle"],
               "verdicts": verdicts})
    counts = {}
    for v in verdicts:
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
    print(f"judged {len(verdicts)} items -> {out_path}   {counts}")
    return counts


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3])
