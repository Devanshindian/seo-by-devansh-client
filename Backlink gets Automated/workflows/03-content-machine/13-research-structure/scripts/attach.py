"""Step 5 — attach evidence + links under each H2/H3. Pure code, by card id. No new thinking.
Evidence = the member cards' verbatim + sources. Internal links = member ownpage URLs. External = source URLs.

Reads: sections (named clusters) + cards. Writes: enriched sections into the structure.
"""
import sys, json
import config


def _collect(card_ids, by_id):
    evidence, internal, external = [], [], []
    for i in card_ids:
        c = by_id.get(i)
        if not c:
            continue
        if c.get("verbatim"):
            evidence.append({"card_id": i, "gloss": c["gloss"], "verbatim": c["verbatim"],
                             "source_urls": c["source_urls"], "tag": c["tag"]})
        if c.get("internal_link"):
            internal.append(c["internal_link"])
        # external = genuine OUTSIDE sources only — never a card's own page URL (that's an internal_link, not a source)
        external += [u for u in c.get("source_urls", []) if u != c.get("internal_link")]
    return evidence, list(dict.fromkeys(internal)), list(dict.fromkeys(external))


def run(sections, cards):
    by_id = {c["id"]: c for c in cards}
    out = []
    for s in sections:
        ev, itn, ext = _collect(s["card_ids"], by_id)
        h3s = []
        for h in s["h3"]:
            hev, hitn, hext = _collect(h["card_ids"], by_id)
            h3s.append({"h3": h["h3"], "evidence": hev,
                        "internal_links": hitn, "external_links": hext})
        # section-level rollup (union across the H2's own cards + its H3s)
        all_int = list(dict.fromkeys(itn + [u for h in h3s for u in h["internal_links"]]))
        all_ext = list(dict.fromkeys(ext + [u for h in h3s for u in h["external_links"]]))
        out.append({"h2": s["h2"], "is_differentiator": s["is_differentiator"],
                    "target_keyword": None,          # filled by Step 6
                    "evidence": ev, "internal_links": all_int, "external_links": all_ext,
                    "h3": h3s})
    return out


if __name__ == "__main__":
    sections = json.load(open(sys.argv[1]))["sections"]
    cards = json.load(open(sys.argv[2]))
    config.write_json(sys.argv[3], {"sections": run(sections, cards)})
    print(f"attached -> {sys.argv[3]}")
