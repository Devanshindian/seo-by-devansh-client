"""Step 8 — FAQ + order.
FAQ = the 'question' cards (PAA / AI questions), deduped — code only.
Order = one LLM call to sequence the H2s into a logical flow; verified as a permutation in code.
"""
import sys, json
import llm

TEMPLATE = llm.load_prompt("order.md")


def faq_from_cards(cards):
    seen, faq = set(), []
    for c in cards:
        if c.get("tag") == "question":
            q = c["gloss"].strip()
            k = q.lower().rstrip("?")
            if k not in seen:
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


def run(sections, cards):
    return order_sections(sections), faq_from_cards(cards)


if __name__ == "__main__":
    sections = json.load(open(sys.argv[1]))["sections"]
    cards = json.load(open(sys.argv[2]))
    secs, faq = run(sections, cards)
    print("FAQ:", faq)
    print("order:", [s["h2"][:40] for s in secs])
