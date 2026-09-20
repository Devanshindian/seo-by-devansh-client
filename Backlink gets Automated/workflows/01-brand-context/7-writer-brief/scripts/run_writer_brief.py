#!/usr/bin/env python3
"""7-writer-brief orchestrator + steps — the runnable twin of writer-brief.workflow.md.

  COMPANY=<slug> python3 run_writer_brief.py [--redo] [--redo-assemble]

Step 1 classify every section of every rule-carrying brand file (LLM per file, in parallel; the three
       questions are actionable / scope / kind, and the KEEP-or-DROP verdict is derived in code, never
       asked for)                                        -> _work/writer-brief/classified.json
Step 2 assemble the brief from everything kept, resolving the places the sources disagree (LLM; the
       template is lifted VERBATIM from the recipe MD — F1)
       -> writer-brief.md, plus _work/writer-brief/dropped.md
"""
import argparse, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config, llm


# ---- Step 1 ----------------------------------------------------------------------------------------

DROP_REASONS = {
    "not-the-writers-job": "the writer cannot act on it",
    "a-fact": "a fact, not a rule about writing",
    "a-lookup-list": "a lookup list a human consults, not something applied while writing",
    "general-craft": "true for any company, so it is not this company's brief",
}


def _verdict(sec):
    """Derived in code, never asked of the model — one answer cannot disagree with itself (F1/J2).
    Returns (keep|drop, reason). The order below is the recipe's order, word for word."""
    if not sec.get("actionable"):
        return "drop", "not-the-writers-job"
    if sec.get("kind") == "fact":
        return "drop", "a-fact"
    if sec.get("kind") == "reference":
        return "drop", "a-lookup-list"
    if sec.get("scope") == "universal":
        return "drop", "general-craft"
    return "keep", ""


def classify(redo=False):
    out_path = os.path.join(config.WORK, "classified.json")
    if os.path.exists(out_path) and not redo:
        print(f"   reusing {out_path}")
        return json.load(open(out_path))

    prompt_t = llm.load_prompt("classify-sections.md")

    def one(name):
        path = os.path.join(config.BRAND_CTX, name)
        if not os.path.exists(path):
            print(f"   !! missing {name} — skipped")
            return None
        body = open(path, encoding="utf-8").read()[:config.SECTION_CHAR_CAP]
        return llm.call_json(prompt_t.replace("{{BRAND}}", config.BRAND)
                             .replace("{{NICHE}}", config.NICHE)
                             .replace("{{FILENAME}}", name)
                             .replace("{{CONTENT}}", body))

    sections = []
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        futs = {ex.submit(one, n): n for n in config.SOURCE_FILES}
        for fut in as_completed(futs):
            name, r = futs[fut], fut.result()
            if not r:
                continue
            got = r.get("sections") or []
            for s in got:
                s["file"] = name
                if s.get("kind") not in {"rule", "fact", "reference"}:    # verify, don't trust (C3)
                    print(f"   !! {name}: unknown kind {s.get('kind')!r} -> treated as 'reference'")
                    s["kind"] = "reference"
                s["verdict"], s["drop_reason"] = _verdict(s)
            sections += got
            print(f"   {name}: {len(got)} sections")

    config.write_text(out_path, json.dumps({"sections": sections}, indent=1))
    kept = sum(1 for s in sections if s["verdict"] == "keep")
    tally = {}
    for s in sections:
        if s["verdict"] == "drop":
            tally[s["drop_reason"]] = tally.get(s["drop_reason"], 0) + 1
    print(f"   {len(sections)} sections -> {out_path}")
    print(f"   kept {kept}; dropped " + " · ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    return {"sections": sections}


# ---- Step 2 ----------------------------------------------------------------------------------------

def _kept_block(sections):
    out = []
    for s in sections:
        if s.get("verdict") == "keep" and (s.get("carry") or "").strip():
            out.append(f"### {s['file']} — {s.get('heading','')}\n"
                       f"({s.get('summary','')})\n\n{s['carry'].strip()}")
    return "\n\n".join(out)


def _template():
    """The recipe's template, lifted VERBATIM (F1: the recipe owns it)."""
    text = open(config.RECIPE_MD, encoding="utf-8").read()
    m = re.search(r"```markdown\n(# Writer brief — \[Company\].*?)```", text, re.S)
    if not m:
        raise SystemExit("!! could not find the template in the recipe MD")
    return m.group(1)


_PUNCT = re.compile(r"[*`_\"'“”‘’.,;:!?()\[\]]+")


def _norm(s):
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", s)).strip().lower()


def _atoms(text):
    """The CONCRETE items the source gave us: table cells and the head of each list item. Losing one of
    these is the failure mode that matters, so they are counted rather than trusted (C3).

    An atom is only ever the thing that must SURVIVE, so an arrow pair keeps its left side: the source's
    'clients -> not customers' becomes 'clients', which then matches however the brief formats it."""
    out = set()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):        # a table rule row
                continue
            pieces = cells
        elif re.match(r"^([-*·]|\d+\.)\s+", line):
            head = re.sub(r"^([-*·]|\d+\.)\s+", "", line)
            pieces = [re.split(r"[:—(]", head)[0]]
        else:
            continue
        for p in pieces:
            p = re.split(r"→|->|\bnot\b", p)[0]                  # keep the side that must survive
            # A cell often lists alternatives ("same-day / next-day"). Each is its own
            # item, and the brief may re-join them with a comma, so compare them separately.
            for part in re.split(r"\s*/\s*|\s*·\s*", p):
                part = _norm(part)
                if 2 < len(part) < 60:
                    out.add(part)
    return out


def assemble(sections, redo=False):
    if os.path.exists(config.OUT_MD) and not redo:
        print(f"   reusing {config.OUT_MD}")
        return config.OUT_MD
    kept = _kept_block(sections)
    rulings = "*(none — nothing has been overridden by hand)*"
    if os.path.exists(config.RULINGS_MD):
        rulings = open(config.RULINGS_MD, encoding="utf-8").read().strip()
        print(f"   house decisions from {config.RULINGS_MD}")
    draft = llm.call_text(llm.load_prompt("assemble-brief.md")
                          .replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
                          .replace("{{KEPT}}", kept).replace("{{RULINGS}}", rulings)
                          .replace("{{TEMPLATE}}", _template()))
    if draft.startswith("```"):
        draft = re.sub(r"^```[a-z]*\n|\n```$", "", draft.strip())
    config.write_text(config.OUT_MD, draft)

    # Search the WHOLE normalised brief, not a set of output atoms — the brief is allowed to reformat a
    # bullet into a table cell, and an atom-to-atom compare called every such reformat a loss.
    want, blob = _atoms(kept), _norm(draft)
    missing = sorted(a for a in want if a not in blob)
    print(f"   brief -> {config.OUT_MD} ({len(draft.split())} words)")
    print(f"   concrete items: {len(want) - len(missing)}/{len(want)} carried through")
    if missing:
        print(f"   !! {len(missing)} missing, e.g. {missing[:8]}")
    return config.OUT_MD


def dropped(sections):
    """A record of what did not make the brief, and why — so nothing is silently lost.

    The `general-craft` group is written out IN FULL, with its rules, not just its headings. Those
    sections passed "can the writer act on it" and failed only "is it this company's own", so they are
    good writing rules that simply are not brand. Listing them by heading alone loses them for good;
    listing their text makes the group usable by whoever writes the general instructions."""
    by = {}
    for s in sections:
        if s.get("verdict") == "keep":
            continue
        by.setdefault(s.get("drop_reason", "?"), []).append(s)
    lines = [f"# What did not make the writer brief — {config.BRAND}", "",
             "A record. Nothing here was deleted from any source file.", ""]
    for reason in sorted(by):
        group = by[reason]
        lines.append(f"## {reason} — {DROP_REASONS.get(reason, '')}  ({len(group)})")
        lines.append("")
        if reason == "general-craft":
            lines.append("Good writing rules that are true for any company. Kept in full, because this "
                         "group is the one worth reusing elsewhere.")
            lines.append("")
            for s in group:
                lines.append(f"### {s['file']} — {s.get('heading','')}")
                lines.append(f"*{s.get('why','')}*")
                lines.append("")
                lines.append((s.get("carry") or "*(no text captured)*").strip())
                lines.append("")
        else:
            for s in group:
                lines.append(f"- **{s['file']} — {s.get('heading','')}** · {s.get('why','')}")
            lines.append("")
    p = os.path.join(config.WORK, "dropped.md")
    config.write_text(p, "\n".join(lines))
    n_craft = len(by.get("general-craft", []))
    print(f"   record -> {p}  ({n_craft} general-craft rules kept in full)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true", help="re-run both steps")
    ap.add_argument("--redo-assemble", action="store_true", help="re-run Step 2 only")
    a = ap.parse_args()

    missing = [n for n in config.SOURCE_FILES if not os.path.exists(os.path.join(config.BRAND_CTX, n))]
    if len(missing) == len(config.SOURCE_FILES):
        sys.exit(f"!! none of the source files exist in {config.BRAND_CTX} — run engines 1, 2 and 6 first")

    print(f"company: {config.COMPANY} ({config.BRAND})")
    print("== Step 1: classify every section ==")
    data = classify(redo=a.redo)
    print("== Step 2: assemble the brief ==")
    assemble(data["sections"], redo=a.redo or a.redo_assemble)
    dropped(data["sections"])
    print("== WRITTEN IN PLACE: writer-brief.md — review with `git diff` ==")


if __name__ == "__main__":
    main()
