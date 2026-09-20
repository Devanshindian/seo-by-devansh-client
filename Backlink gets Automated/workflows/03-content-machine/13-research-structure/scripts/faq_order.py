"""Step 8 — FAQ + order.
FAQ = the PAA questions straight from the DataForSEO SERP extract, deduped — code only. (Until 2026-08-03
these came via brief-harvested 'question' CARDS — same data, laundered through clustering with no evidence
behind it; the write phase reads the same SERP extract itself, so this list is display/blueprint context.)
Order = one LLM call to sequence the H2s into a logical flow; verified as a permutation in code.
"""
import os, sys, json
import config, llm

TEMPLATE = llm.load_prompt("order.md")


def faq_from_serp(slug, hub=""):
    """PAA questions from <dfs run>/proof/04-serp-extract.json; [] when the file is absent (never fatal)."""
    p = os.path.join(config.DFS_RUNS, hub, slug, "proof", "04-serp-extract.json")
    if not os.path.exists(p):
        return []
    try:
        paa = json.load(open(p)).get("paa") or []
    except Exception:
        return []
    seen, faq = set(), []
    for q in paa:
        q = str(q).strip()
        k = q.lower().rstrip("?")
        if q and k not in seen:
            seen.add(k)
            faq.append(q if q.endswith("?") else q + "?")
    return faq


def order_sections(sections):
    if len(sections) <= 1:
        return sections
    lines = "\n".join(f"{i}: {s['h2']}" for i, s in enumerate(sections))
    try:
        order = llm.call_json(TEMPLATE.replace("{{SECTIONS}}", lines)).get("order", [])
    except Exception:
        order = []
    if sorted(order) == list(range(len(sections))):        # valid permutation only
        return [sections[i] for i in order]
    return sections                                        # fallback: keep as-is


def run(sections, slug, hub=""):
    return order_sections(sections), faq_from_serp(slug, hub)


if __name__ == "__main__":
    sections = json.load(open(sys.argv[1]))["sections"]
    secs, faq = run(sections, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    print("FAQ:", faq)
    print("order:", [s["h2"][:40] for s in secs])
