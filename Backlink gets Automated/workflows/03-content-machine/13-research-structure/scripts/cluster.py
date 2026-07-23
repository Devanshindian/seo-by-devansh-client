"""Step 2-3 — cluster all cards into MECE groups, verified in code.
Small sets: one clustering call (sees only id + gloss). Large sets (> CLUSTER_SINGLE_MAX): two-level — batch the
cards, cluster each batch in parallel, then merge the batch labels into final themes (keeps each LLM call small
so nothing times out). Then code guarantees every card is placed exactly once (dedupe + a leftover pass).

Reads: cards (list with ids + glosses). Writes: clusters.json — [{ label, card_ids[], is_differentiator }].
"""
import sys, json
from concurrent.futures import ThreadPoolExecutor
import config, llm

TEMPLATE = llm.load_prompt("cluster.md")
MERGE = llm.load_prompt("cluster-merge.md")


def _cluster_call(cards):
    lines = "\n".join(f"{c['id']}: {c['gloss']}" for c in cards)
    return llm.call_json(TEMPLATE.replace("{{CARDS}}", lines)).get("clusters", [])


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

    lines = "\n".join(f"{i}: {p['label']}" for i, p in enumerate(provisional))
    try:
        themes = llm.call_json(MERGE.replace("{{LABELS}}", lines)).get("themes", [])
    except Exception as e:
        print(f"  merge failed ({e}); keeping provisional clusters")
        themes = []

    final, used = [], set()
    for th in themes:
        ids, diff = [], False
        for idx in th.get("member_indices", []):
            if isinstance(idx, int) and 0 <= idx < len(provisional) and idx not in used:
                used.add(idx)
                ids += provisional[idx]["card_ids"]
                diff = diff or provisional[idx].get("is_differentiator", False)
        if ids:
            final.append({"label": (th.get("label") or "").strip() or "Untitled",
                          "card_ids": ids, "is_differentiator": diff})
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
            out.append({"label": cl.get("label", "").strip() or "Untitled",
                        "card_ids": ids, "is_differentiator": bool(cl.get("is_differentiator"))})
    return out, placed


def run(cards, out_path):
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
            clusters.append({"label": "Unsorted (review)", "card_ids": still, "is_differentiator": False})

    # MECE assertion (code)
    all_ids = [i for cl in clusters for i in cl["card_ids"]]
    assert len(all_ids) == len(set(all_ids)) == len(valid), \
        f"MECE broken: {len(all_ids)} placed, {len(set(all_ids))} unique, {len(valid)} cards"

    config.write_json(out_path, {"clusters": clusters})
    print(f"  {len(clusters)} clusters over {len(valid)} cards (MECE verified) -> {out_path}")
    for cl in clusters:
        d = " *" if cl["is_differentiator"] else "  "
        print(f"   {d}{len(cl['card_ids']):3}  {cl['label'][:60]}")
    return clusters


if __name__ == "__main__":
    cards = json.load(open(sys.argv[1]))
    run(cards, sys.argv[2])
