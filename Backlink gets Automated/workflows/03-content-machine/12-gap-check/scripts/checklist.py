"""Step 0 — build the coverage checklist in PURE CODE (no AI, no markdown parsing).

Replaces parse_brief.py (2026-08-04, decided with Devansh). That step paid an AI to re-read the brief's
markdown and extract items — but after the checklist was cut to three types, every one of them already
exists as clean JSON next to the brief:
  gap_we_own    <- proof/07-competitor-read.json  -> gaps_to_own        (written by the conductor's spine step)
  winner_h2     <- proof/07-competitor-read.json  -> winners_common_h2s
  aio_subtopic  <- proof/04-serp-extract.json     -> ai_overview.text   (one item: the answer skeleton)
The article context (title / angle / spine / about / not_about) comes from spine.json, which lives with
the dossier. DROPPED from the old checklist: secondary_kw + in_body (keyword strings, not coverage
targets — section keywords are the architect's job now) and paa (the write phase's FAQ builder can only
use facts already in the article, so an unanswerable question self-corrects) and aeo_faq (the AEO step
was deleted; nothing consumed it).

Reads:  the brief's proof/ dir + the dossier dir's spine.json.
Writes: coverage-items.json — {asset_title, distinct_angle, spine, about, not_about, primary, items[]}.
"""
import os
import json


def _load(path, default=None):
    try:
        return json.load(open(path))
    except Exception:
        return default if default is not None else {}


def build(brief_path, dossier_path):
    """brief_path = .../research-doc-<slug>.md (its dir holds proof/); dossier_path sits next to spine.json."""
    proof = os.path.join(os.path.dirname(os.path.abspath(brief_path)), "proof")
    spine = _load(os.path.join(os.path.dirname(os.path.abspath(dossier_path)), "spine.json"))
    comp = _load(os.path.join(proof, "07-competitor-read.json"))
    serp = _load(os.path.join(proof, "04-serp-extract.json"))
    final = _load(os.path.join(proof, "03-final.json"))

    items = []

    def add(typ, text):
        text = str(text or "").strip()
        if text:
            items.append({"id": f"{typ}-{sum(1 for i in items if i['type'] == typ) + 1}",
                          "type": typ, "item": text})

    for g in comp.get("gaps_to_own") or []:
        add("gap_we_own", g)
    for h in comp.get("winners_common_h2s") or []:
        add("winner_h2", h)
    aio = serp.get("ai_overview") or {}
    if isinstance(aio, dict) and (aio.get("text") or "").strip():
        add("aio_subtopic", aio["text"].strip())

    return {"asset_title": (spine.get("title") or "").strip(),
            "distinct_angle": (spine.get("angle") or "").strip(),
            "spine": (spine.get("spine") or "").strip(),
            "about": (spine.get("about") or "").strip(),
            "not_about": (spine.get("not_about") or "").strip(),
            "primary": ((final.get("primary") or {}).get("keyword") or "").strip(),
            "items": items}


if __name__ == "__main__":
    import sys
    data = build(sys.argv[1], sys.argv[2])
    by = {}
    for it in data["items"]:
        by[it["type"]] = by.get(it["type"], 0) + 1
    print(json.dumps({k: v for k, v in data.items() if k != "items"}, indent=2)[:400])
    print("items:", by)
