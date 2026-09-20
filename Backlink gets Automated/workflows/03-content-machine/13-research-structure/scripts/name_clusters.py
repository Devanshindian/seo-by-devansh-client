"""Step 4 — name + split each cluster into an H2 (+ H3s). One parallel call per cluster (small context).
Code guarantees every member card lands under the H2 or exactly one H3 (local MECE).

Reads: clusters.json + cards. Writes: sections (list of H2 nodes) into structure (via the orchestrator).
Node: { h2, card_ids[], h3: [ { h3, card_ids[] } ] }
"""
import sys, json
from concurrent.futures import ThreadPoolExecutor
import config, llm

TEMPLATE = llm.load_prompt("name-cluster.md")

# THE STEP USED TO NAME BLIND (2026-08-30, Devansh). This was the only prompt in the engine handed the
# cards and nothing else: no title, no angle, no about/not_about. Its sibling steps (cluster, merge,
# score-cards) all get them. So the naming call could not know whether it was labelling a glossary, a
# ranking or a how-to, and it defaulted to the one shape that fits anything, a question. Measured on the
# six finished articles: 15 to 17 of every ~20 headings came back phrased as a question, including 48
# how-to questions for an article whose title is "A Hiring & Assessment Glossary". A heading written in
# the wrong shape here survives every later stage and reaches the reader, because nothing downstream
# knows what the shape should have been. Same context object as cluster.py, same J2 rule: a model asked
# to make a judgment must see what the judgment depends on.
_A = {"asset": "", "angle": "", "about": "", "not_about": ""}


def _name_one(cluster, gloss_by_id):
    members = cluster["card_ids"]
    lines = "\n".join(f"{i}: {gloss_by_id.get(i, '')}" for i in members)
    try:
        r = llm.call_json(TEMPLATE.replace("{{ASSET}}", _A["asset"])
                          .replace("{{ANGLE}}", _A["angle"])
                          .replace("{{ABOUT}}", _A["about"])
                          .replace("{{NOT_ABOUT}}", _A["not_about"])
                          .replace("{{CARDS}}", lines))
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
            "card_ids": direct, "h3": h3}


def run(clusters, cards, out_path, asset="", angle="", spine_ctx=None):
    spine_ctx = spine_ctx or {}
    _A.update({"asset": asset or "(not available for this run)",
               "angle": (angle or asset) or "(not available for this run)",
               "about": (spine_ctx.get("about") or "").strip() or "(not available for this run)",
               "not_about": (spine_ctx.get("not_about") or "").strip() or "(not available for this run)"})
    gloss_by_id = {c["id"]: c["gloss"] for c in cards}
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        sections = list(ex.map(lambda cl: _name_one(cl, gloss_by_id), clusters))
    config.write_json(out_path, {"sections": sections})
    print(f"  named {len(sections)} H2s -> {out_path}")
    for s in sections:
        print(f"      {s['h2'][:55]}  (h3:{len(s['h3'])})")
    return sections


if __name__ == "__main__":
    clusters = json.load(open(sys.argv[1]))["clusters"]
    cards = json.load(open(sys.argv[2]))
    run(clusters, cards, sys.argv[3], *sys.argv[4:6])
