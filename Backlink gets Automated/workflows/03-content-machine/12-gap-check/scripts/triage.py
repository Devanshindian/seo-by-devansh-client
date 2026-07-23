"""Step 2 — Gap triage + STORM query writer. One Prompt-2 call over all the misses.
Reads:  coverage-verdicts.json (from judge). Takes only verdict in {no, partial}.
Writes: gap-queries.json — { "queries": [ {query, fills, why}, ... ] }  (0 to 3 queries)
"""
import sys, json
import config
import llm

TEMPLATE = llm.load_prompt("gap-triage.md")

# The coverage judge may only emit these three (mirrors report.py MARK). An UNKNOWN verdict must be a hard
# error, not a silent "not a miss" — otherwise a judge that writes "not covered" / "yes" / "unclear" drops the
# item off the miss list and it is treated as covered. That is the exact fail-open [A#17] this guards against.
VALID_VERDICTS = ("covered", "no", "partial")
MISS_VERDICTS = ("no", "partial")


def run(verdicts_path, out_path):
    data = json.load(open(verdicts_path))
    bad = [v for v in data["verdicts"] if v.get("verdict") not in VALID_VERDICTS]
    if bad:
        sample = "; ".join(f"{v.get('item','?')!r}={v.get('verdict')!r}" for v in bad[:5])
        raise ValueError(f"{len(bad)} coverage verdict(s) outside {VALID_VERDICTS}: {sample}. "
                         f"Refusing to triage — an unrecognised verdict silently reads as 'covered'.")
    misses = [v for v in data["verdicts"] if v["verdict"] in MISS_VERDICTS]
    if not misses:
        config.write_json(out_path, {"queries": []})
        print(f"no misses -> 0 queries -> {out_path}")
        return {"queries": []}

    lines = [f"- [{v['verdict']}] ({v['type']}) {v['item']} — judge: {v['reason']}" for v in misses]
    prompt = (TEMPLATE
              .replace("{{ASSET_TITLE}}", data["asset_title"])
              .replace("{{DISTINCT_ANGLE}}", data["distinct_angle"])
              .replace("{{NO_AND_PARTIAL_ITEMS}}", "\n".join(lines)))
    result = llm.call_json(prompt)
    queries = result.get("queries", [])[:3]         # hard cap at 3
    config.write_json(out_path, {"queries": queries})
    print(f"{len(misses)} misses -> {len(queries)} STORM queries -> {out_path}")
    for q in queries:
        print(f"  Q: {q['query']}")
    return {"queries": queries}


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
