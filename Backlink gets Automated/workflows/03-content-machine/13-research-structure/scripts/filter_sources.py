"""Step 4b — competitor-source filter. Strip competitor citations from the cards BEFORE attach,
so no competitor URL survives into the blueprint.

Per card (by the one authoritative list — competitors.py → competitors.md '## Direct competitors'):
  - remove any competitor-domain URL from source_urls;
  - if that empties a card that HAD sources (a competitor was its ONLY source) → DELETE the card
    (its verbatim is competitor-derived + now uncitable);
  - if legit sources remain (mixed case) → KEEP the card with the competitor URL stripped;
  - cards that never had a source are untouched (framing/structural — not competitor citations).

Reads: cards (list). Writes: competitor-drops.json (audit). Returns: (filtered_cards, report).
Runs before attach.py so attach assembles clean sections automatically (attach skips missing card ids).
"""
import json, os
import config, competitors


def run(cards, run_dir):
    domains = competitors.direct_domains()
    kept, deleted, stripped = [], [], []
    all_src, comp_src = set(), set()

    for c in cards:
        su = c.get("source_urls") or []
        for u in su:
            all_src.add(u)
        comp_u = [u for u in su if competitors.is_competitor(u, domains)]
        if not comp_u:
            kept.append(c)
            continue
        for u in comp_u:
            comp_src.add(u)
        remaining = [u for u in su if not competitors.is_competitor(u, domains)]
        if remaining:                                  # mixed: keep the chunk, drop only the competitor link
            kept.append({**c, "source_urls": remaining})
            stripped.append({"id": c["id"], "removed": comp_u, "kept": remaining})
        else:                                          # competitor was the sole source: delete the whole card
            deleted.append({"id": c["id"], "tag": c.get("tag"),
                            "gloss": c.get("gloss"), "competitor_urls": comp_u})

    total = len(cards)
    pct = round(100 * len(deleted) / total, 2) if total else 0.0
    report = {
        "domains_checked": sorted(domains),
        "total_cards": total,
        "distinct_sources": len(all_src),
        "distinct_competitor_sources": sorted(comp_src),
        "deleted_count": len(deleted),
        "deleted_pct_of_cards": pct,
        "stripped_count": len(stripped),          # mixed cards kept with competitor link removed
        "flag_threshold_pct": config.COMPETITOR_DROP_FLAG_PCT,
        "FLAG": pct > config.COMPETITOR_DROP_FLAG_PCT,
        "deleted": deleted,
        "stripped": stripped,
    }
    config.write_json(os.path.join(run_dir, "competitor-drops.json"), report)
    return kept, report
