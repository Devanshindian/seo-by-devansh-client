#!/usr/bin/env python3
"""8-brand-cards orchestrator + steps — the runnable twin of brand-cards.workflow.md.

  COMPANY=<slug> python3 run_brand_cards.py [--redo]

Step 1 customer results -> cards. DETERMINISTIC: the source file has a fixed per-entry shape, so this is
       parsing, not judgment. No LLM.            -> _work/brand-cards/results.json
Step 2 research study -> cards. An LLM per batch of sections, because deciding WHICH rows are worth a
       sentence is a judgment call.              -> _work/brand-cards/research.json
Step 3 mint ids and write the pool               -> brand-cards.json
"""
import argparse, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config, llm


# ---- Step 1: customer results (deterministic) --------------------------------------------------------

def results_cards(redo=False):
    out_path = os.path.join(config.WORK, "results.json")
    if os.path.exists(out_path) and not redo:
        print(f"   reusing {out_path}")
        return json.load(open(out_path))
    if not os.path.exists(config.RESULTS_MD):
        print(f"   !! no {os.path.basename(config.RESULTS_MD)} — skipping customer results")
        return []

    text = open(config.RESULTS_MD, encoding="utf-8").read()
    # Entries are "### <title>" followed by a prose paragraph and three labelled lines.
    blocks = re.split(r"^### ", text, flags=re.M)[1:]
    out = []
    for b in blocks:
        lines = b.strip().splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:])
        story = "\n".join(l for l in lines[1:] if l.strip() and not l.strip().startswith("-")).strip()

        def field(label):
            m = re.search(rf"^-\s*{label}\s*:\s*(.+)$", body, flags=re.M | re.I)
            return m.group(1).strip() if m else ""

        point, number, source = field("Point it makes"), field(r"Number \(if any\)"), field("Source")
        url = (re.search(r"https?://\S+", source).group(0).rstrip(").,") if re.search(r"https?://\S+", source) else "")
        if not story or not url:
            print(f"   !! skipped (no story text or no source URL): {title[:60]}")
            continue
        out.append({"gloss": point or title,
                    "verbatim": f"{title}. {story}".strip(),
                    "number": number,
                    "source_urls": [url],
                    "tag": "brand-result"})
    config.write_json(out_path, out)
    print(f"   {len(out)} customer results -> {out_path}")
    return out


# ---- Step 2: the research study (LLM per batch) ------------------------------------------------------

def _split(text):
    """(header, [question sections]).

    A QUESTION SECTION is a `## ` block that has `### ` questions under it. Everything before the first
    of those is the header: the study's name, its date, its base and its caveats. Splitting on the first
    `## ` instead loses all of that, because the study's own description usually sits under a `## ` of
    its own ("## The study") — which is exactly what happened on the first run."""
    starts = [m.start() for m in re.finditer(r"^## ", text, flags=re.M)] + [len(text)]
    header_end, sections = len(text), []
    for i in range(len(starts) - 1):
        block = text[starts[i]:starts[i + 1]]
        if re.search(r"^### ", block, flags=re.M):
            if not sections:
                header_end = starts[i]
            sections.append(block.rstrip())
    return text[:header_end].strip(), sections


def _citation(header):
    """The study's own name, taken from the first bold run in the header."""
    m = re.search(r"\*\*(.+?)\*\*", header, flags=re.S)
    return m.group(1).strip().rstrip(".") if m else ""


def research_cards(redo=False):
    out_path = os.path.join(config.WORK, "research.json")
    if os.path.exists(out_path) and not redo:
        print(f"   reusing {out_path}")
        return json.load(open(out_path))
    if not os.path.exists(config.RESEARCH_MD):
        print(f"   !! no {os.path.basename(config.RESEARCH_MD)} — skipping research")
        return []

    text = open(config.RESEARCH_MD, encoding="utf-8").read()
    header, sections = _split(text)
    if not sections:
        print("   !! no question sections found — is the research file in the expected shape?")
        return []
    cite = _citation(header)
    if not cite:
        print("   !! no study name found in the header (expected a **bold** title) — cards will carry "
              "no citation, so a reader cannot tell where the number came from")
    n = config.BATCH_SECTIONS
    batches = ["\n\n".join(sections[i:i + n]) for i in range(0, len(sections), n)]
    prompt_t = llm.load_prompt("extract-research-cards.md")

    def one(chunk):
        return llm.call_json(prompt_t.replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
                             .replace("{{STUDY_HEADER}}", header).replace("{{CONTENT}}", chunk))

    found = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(one, b): i for i, b in enumerate(batches)}
        got = {}
        for fut in as_completed(futs):
            got[futs[fut]] = (fut.result() or {}).get("findings") or []
            print(f"   batch {futs[fut] + 1}/{len(batches)}: {len(got[futs[fut]])} findings")
    for i in range(len(batches)):                      # keep source order, not completion order
        found += got.get(i, [])

    out = []
    for f in found:
        v = str(f.get("verbatim") or "").strip()
        if not v:
            continue
        out.append({"gloss": str(f.get("gloss") or "").strip() or v[:90],
                    "verbatim": v,
                    "topics": [str(t).strip().lower() for t in (f.get("topics") or []) if str(t).strip()],
                    "source_note": cite,
                    "source_urls": [config.RESEARCH_URL] if config.RESEARCH_URL else [],
                    "tag": "brand-research"})
    config.write_json(out_path, out)
    print(f"   {len(out)} research findings -> {out_path}")
    return out


# ---- Step 3: mint ids and write the pool -------------------------------------------------------------

_NUM = re.compile(r"\d")


def build(research, results):
    cards, cid = {"research": [], "results": []}, config.ID_BASE
    for c in research:
        cards["research"].append(dict(c, card_id=cid)); cid += 1
    for c in results:
        cards["results"].append(dict(c, card_id=cid)); cid += 1

    # VERIFY, DON'T TRUST (C3). A card with no digit in it carries no finding, and a research card with
    # no base cannot be quoted honestly — both are surfaced rather than shipped quietly.
    no_number = [c["card_id"] for c in cards["research"] if not _NUM.search(c["verbatim"])]
    no_base = [c["card_id"] for c in cards["research"] if "n=" not in c["verbatim"].lower()]
    no_source = [c["card_id"] for c in cards["results"] if not c.get("source_urls")]

    pool = {"company": config.COMPANY, "brand": config.BRAND,
            "id_base": config.ID_BASE, "next_free_id": cid,
            "research_source": (research[0].get("source_note") if research else ""),
            "research_url": config.RESEARCH_URL,
            "counts": {"research": len(cards["research"]), "results": len(cards["results"])},
            "cards": cards}
    config.write_json(config.OUT_JSON, pool)
    print(f"   pool -> {config.OUT_JSON}")
    print(f"   ids {config.ID_BASE}..{cid - 1} | research {len(cards['research'])} | "
          f"results {len(cards['results'])}")
    if no_number:
        print(f"   !! {len(no_number)} research card(s) carry no number: {no_number[:6]}")
    if no_base:
        print(f"   !! {len(no_base)} research card(s) carry no (n=…) base: {no_base[:6]}")
    if no_source:
        print(f"   !! {len(no_source)} customer result(s) carry no source URL: {no_source[:6]}")
    if not config.RESEARCH_URL:
        print("   ·  research is unpublished: cards carry a written citation and no link. Set "
              "BC_RESEARCH_URL once it has a public home.")
    return pool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(config.RESEARCH_MD) and not os.path.exists(config.RESULTS_MD):
        sys.exit(f"!! neither source file exists in {config.BRAND_CTX}")
    print(f"company: {config.COMPANY} ({config.BRAND})")
    print("== Step 1: customer results -> cards (no LLM) ==")
    results = results_cards(redo=a.redo)
    print("== Step 2: research study -> cards ==")
    research = research_cards(redo=a.redo)
    print("== Step 3: mint ids, write the pool ==")
    build(research, results)
    print(f"== DONE -> {config.OUT_JSON} ==")


if __name__ == "__main__":
    main()
