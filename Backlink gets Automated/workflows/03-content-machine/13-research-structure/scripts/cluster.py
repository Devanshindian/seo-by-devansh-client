"""Step 2-3 — cluster all cards into MECE groups, verified in code.
Small sets: one clustering call (sees id + gloss). Large sets (> CLUSTER_SINGLE_MAX): two-level — batch the
cards, cluster each batch in parallel, then merge the batch labels into final themes (keeps each LLM call small
so nothing times out). Then code guarantees every card is placed exactly once (dedupe + a leftover pass).

2026-08-03: the clusterer now sees the ARTICLE — title, angle, spine, about/not-about, the four reader
personas — so it groups for THIS article instead of grouping blind ("what looks similar"). Blind grouping is
what laundered off-spine material into tidy-looking sections (a well-named cluster makes off-topic cards look
like a legitimate chapter). is_differentiator is gone: it fed one extra AI step and a review-page badge the
write phase explicitly ignores.

Reads: cards (list with ids + glosses) + the article context. Writes: clusters.json — [{ label, card_ids[] }].
"""
import sys, json
from concurrent.futures import ThreadPoolExecutor
import config, llm, personas
import score_cards as _sc          # reuse persona_str — one rendering, no second copy

TEMPLATE = llm.load_prompt("cluster.md")
MERGE = llm.load_prompt("cluster-merge.md")

_A = {"asset": "", "angle": "", "spine": "", "about": "", "not_about": "", "personas": "", "persona": ""}


def _cluster_call(cards):
    lines = "\n".join(f"{c['id']}: {c['gloss']}" for c in cards)
    prompt = (TEMPLATE.replace("{{ASSET}}", _A["asset"]).replace("{{ANGLE}}", _A["angle"])
              .replace("{{SPINE}}", _A["spine"]).replace("{{ABOUT}}", _A["about"])
              .replace("{{NOT_ABOUT}}", _A["not_about"]).replace("{{BRAND}}", config.BRAND_ONELINER)
              .replace("{{PERSONAS}}", _A["personas"]).replace("{{PERSONA}}", _A["persona"])
              .replace("{{CARDS}}", lines))
    return llm.call_json(prompt).get("clusters", [])


def _two_level(cards):
    """Batch -> cluster each batch in parallel -> merge batch labels into final themes."""
    batches = [cards[i:i + config.CLUSTER_BATCH] for i in range(0, len(cards), config.CLUSTER_BATCH)]
    print(f"  two-level: {len(batches)} batches of ~{config.CLUSTER_BATCH}")

    def _do(batch):
        cl, _ = _dedupe(_cluster_call(batch), {c["id"] for c in batch})
        return cl

    provisional = []
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        for cl in ex.map(_do, batches):
            provisional += cl
    print(f"  {len(provisional)} provisional clusters -> merging")

    # The merge step gets the SAME article context as the batch clusterer (2026-08-04). Without it the
    # merger saw only a list of label strings: it could spot duplicates but had no idea what was off-spine
    # and no pressure to collapse. Live proof — strategic-interview (1,243 cards, 7 batches) came out with
    # 37 sections, 7 of them starved and 4 of them candidate-side coaching its own not_about forbids.
    lines = "\n".join(f"{i}: {p['label']}" for i, p in enumerate(provisional))
    merge_prompt = (MERGE.replace("{{ASSET}}", _A["asset"]).replace("{{ANGLE}}", _A["angle"])
                    .replace("{{SPINE}}", _A["spine"]).replace("{{ABOUT}}", _A["about"])
                    .replace("{{NOT_ABOUT}}", _A["not_about"]).replace("{{BRAND}}", config.BRAND_ONELINER)
                    .replace("{{PERSONAS}}", _A["personas"]).replace("{{PERSONA}}", _A["persona"])
                    .replace("{{LABELS}}", lines))
    try:
        themes = llm.call_json(merge_prompt).get("themes", [])
    except Exception as e:
        print(f"  merge failed ({e}); keeping provisional clusters")
        themes = []

    final, used = [], set()
    for th in themes:
        ids = []
        for idx in th.get("member_indices", []):
            if isinstance(idx, int) and 0 <= idx < len(provisional) and idx not in used:
                used.add(idx)
                ids += provisional[idx]["card_ids"]
        if ids:
            final.append({"label": (th.get("label") or "").strip() or "Untitled", "card_ids": ids})
    for i, p in enumerate(provisional):            # any provisional cluster not merged stays on its own
        if i not in used:
            final.append(p)
    return final


def _dedupe(clusters, valid_ids):
    """Keep each id in its first cluster only; drop unknown ids. Returns clusters + the set placed."""
    placed, out = set(), []
    for cl in clusters:
        ids = []
        for i in cl.get("card_ids", []):
            if i in valid_ids and i not in placed:
                placed.add(i)
                ids.append(i)
        if ids:
            out.append({"label": cl.get("label", "").strip() or "Untitled", "card_ids": ids})
    return out, placed


def run(cards, out_path, asset="", angle="", spine_ctx=None, persona=None):
    spine_ctx = spine_ctx or {}
    _A.update({"asset": asset, "angle": (angle or asset),
               "spine": (spine_ctx.get("spine") or "").strip() or "(not available for this run)",
               "about": (spine_ctx.get("about") or "").strip() or "(not available for this run)",
               "not_about": (spine_ctx.get("not_about") or "").strip() or "(not available for this run)",
               "personas": personas.block(), "persona": _sc.persona_str(persona)})
    valid = {c["id"] for c in cards}
    raw = _cluster_call(cards) if len(cards) <= config.CLUSTER_SINGLE_MAX else _two_level(cards)
    clusters, placed = _dedupe(raw, valid)

    missing = [c for c in cards if c["id"] not in placed]
    if missing:
        print(f"  {len(missing)} cards unplaced -> leftover pass")
        extra = _cluster_call(missing)
        extra, placed2 = _dedupe(extra, {c["id"] for c in missing})
        clusters += extra
        still = [c["id"] for c in missing if c["id"] not in placed2]
        if still:                                   # last resort so MECE always holds
            clusters.append({"label": "Unsorted (review)", "card_ids": still})

    # MECE assertion (code)
    all_ids = [i for cl in clusters for i in cl["card_ids"]]
    assert len(all_ids) == len(set(all_ids)) == len(valid), \
        f"MECE broken: {len(all_ids)} placed, {len(set(all_ids))} unique, {len(valid)} cards"

    config.write_json(out_path, {"clusters": clusters})
    print(f"  {len(clusters)} clusters over {len(valid)} cards (MECE verified) -> {out_path}")
    for cl in clusters:
        print(f"    {len(cl['card_ids']):3}  {cl['label'][:60]}")
    return clusters


if __name__ == "__main__":
    cards = json.load(open(sys.argv[1]))
    run(cards, sys.argv[2])
