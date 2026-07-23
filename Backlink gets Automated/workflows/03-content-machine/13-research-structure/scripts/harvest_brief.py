"""Step 1 (brief) — turn the DataForSEO brief into cards: competitor H2s, gaps, questions.
These are already short and structured, so gloss = the item text and verbatim = None.

Card: { gloss, verbatim=None, source_urls=[], internal_link=None, tag in competitor|gap|question }
"""
import os, sys, json
import config, llm

TEMPLATE = llm.load_prompt("harvest-brief.md")


def _brief_path(slug):
    return os.path.join(config.DFS_RUNS, slug, f"research-doc-{slug}.md")


def harvest(slug, brief_path=None):
    path = brief_path or _brief_path(slug)
    md = open(path).read()
    items = llm.call_json(TEMPLATE.replace("{{BRIEF_TEXT}}", md))
    cards = []
    for it in items:
        gloss = (it.get("gloss") or "").strip()
        tag = (it.get("tag") or "").strip()
        if gloss and tag in ("competitor", "gap", "question"):
            cards.append({"gloss": gloss, "verbatim": None, "source_urls": [],
                          "internal_link": None, "tag": tag, "origin": f"brief/{tag}"})
    by = {}
    for c in cards:
        by[c["tag"]] = by.get(c["tag"], 0) + 1
    print(f"  brief: {len(cards)} cards  {by}")
    return cards


if __name__ == "__main__":
    slug, out_path = sys.argv[1], sys.argv[2]
    cards = harvest(slug, sys.argv[3] if len(sys.argv) > 3 else None)
    config.write_json(out_path, cards)
    print(f"-> {out_path}")
