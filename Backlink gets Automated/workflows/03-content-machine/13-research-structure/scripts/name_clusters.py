"""Step 4 — name + split each cluster into an H2 (+ H3s). One parallel call per cluster (small context).
Code guarantees every member card lands under the H2 or exactly one H3 (local MECE).

Reads: clusters.json + cards. Writes: sections (list of H2 nodes) into structure (via the orchestrator).
Node: { h2, is_differentiator, card_ids[], h3: [ { h3, card_ids[] } ] }
"""
import sys, json
from concurrent.futures import ThreadPoolExecutor
import config, llm

TEMPLATE = llm.load_prompt("name-cluster.md")


def _name_one(cluster, gloss_by_id):
    members = cluster["card_ids"]
    lines = "\n".join(f"{i}: {gloss_by_id.get(i, '')}" for i in members)
    try:
        r = llm.call_json(TEMPLATE.replace("{{CARDS}}", lines))
    except Exception as e:
        print(f"    ! name failed '{cluster['label'][:30]}': {e}")
        r = {"h2": cluster["label"], "h3": [], "card_ids": members}

    mset = set(members)
    placed, h3 = set(), []
    for sub in r.get("h3", []) or []:
        ids = [i for i in sub.get("card_ids", []) if i in mset and i not in placed]
        placed.update(ids)
        if ids:
            h3.append({"h3": (sub.get("h3") or "").strip() or "Untitled", "card_ids": ids})
    direct = [i for i in r.get("card_ids", []) if i in mset and i not in placed]
    placed.update(direct)
    direct += [i for i in members if i not in placed]        # nothing lost
    return {"h2": (r.get("h2") or "").strip() or cluster["label"],
            "is_differentiator": cluster.get("is_differentiator", False),
            "card_ids": direct, "h3": h3}


def run(clusters, cards, out_path):
    gloss_by_id = {c["id"]: c["gloss"] for c in cards}
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        sections = list(ex.map(lambda cl: _name_one(cl, gloss_by_id), clusters))
    config.write_json(out_path, {"sections": sections})
    print(f"  named {len(sections)} H2s -> {out_path}")
    for s in sections:
        print(f"    {'*' if s['is_differentiator'] else ' '} {s['h2'][:55]}  (h3:{len(s['h3'])})")
    return sections


if __name__ == "__main__":
    clusters = json.load(open(sys.argv[1]))["clusters"]
    cards = json.load(open(sys.argv[2]))
    run(clusters, cards, sys.argv[3])
