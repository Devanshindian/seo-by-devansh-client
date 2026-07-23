"""Step 0 — read the DataForSEO brief and pull out the coverage-target items.
An LLM reads the brief by MEANING (not fixed regex), so a brief that drifts from the exact SAMPLE
formatting still parses. Output schema is unchanged:
  { "asset_title", "distinct_angle", "primary", "items": [ {id, type, item, context}, ... ] }
"""
import sys
import config
import llm

TEMPLATE = llm.load_prompt("parse-brief.md")


def parse(md):
    data = llm.call_json(TEMPLATE.replace("{{BRIEF_TEXT}}", md))
    items = []
    for it in data.get("items", []):
        t, text = str(it.get("type", "")).strip(), str(it.get("item", "")).strip()
        if not t or not text:
            continue
        items.append({"id": f"{t}-{sum(1 for i in items if i['type'] == t) + 1}",
                      "type": t, "item": text, "context": str(it.get("context", "")).strip()})
    return {"asset_title": str(data.get("asset_title", "")).strip(),
            "distinct_angle": str(data.get("distinct_angle", "")).strip(),
            "primary": str(data.get("primary", "")).strip(),
            "items": items}


if __name__ == "__main__":
    brief_path, out_path = sys.argv[1], sys.argv[2]
    data = parse(open(brief_path).read())
    config.write_json(out_path, data)
    by_type = {}
    for it in data["items"]:
        by_type[it["type"]] = by_type.get(it["type"], 0) + 1
    print(f"parsed {len(data['items'])} items -> {out_path}")
    print("  primary:", data["primary"])
    for t, n in sorted(by_type.items()):
        print(f"  {t}: {n}")
