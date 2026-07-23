#!/usr/bin/env python3
"""Step A — build the swipe library and pre-screen it against the brand scope.

Reads:  the recipe MD (Source 1 = the proven-formats table, the single source of truth for it)
        brand-scope.md (the ownership anchor)
Writes: _work/swipe.json          — every SURVIVING format: 4 carried fields + A3's in_scope_subject/brand_fit
        output/format-swipe.md     — the human-readable swipe library (pure assembly of A1/A2 + A3)
        _work/run-log.md (append)  — formats dropped at A3, with the reason (audit trail)

A1 (parse the table) is MECHANICAL. A2 (agent-knowledge extras) and A3 (brand-fit pre-screen) are LLM JUDGMENT.
A4 is pure assembly — every cell traces to A1/A2 (the four format fields) or A3 (subject + fit), nothing invented.
"""
import argparse, os, re, sys
import config as c
sys.path.insert(0, c.SHARED)
import llm


def _parse_source1_table(md_path):
    """A1 — lift the proven-formats table straight from the recipe (Source 1). Returns list of dicts with
    the four columns. The table is the one under the '# The swipe library — proven formats' heading."""
    text = open(md_path).read()
    m = re.search(r"#\s*The swipe library — proven formats.*?\n(.*?)(?:\n#\s|\Z)", text, re.S)
    if not m:
        sys.exit("!! could not find the 'swipe library — proven formats' table in the recipe MD")
    rows = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [x.strip() for x in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0].lower() in ("format", "") or set(cells[0]) <= set("-: "):   # header / separator
            continue
        fmt = re.sub(r"\*+", "", cells[0])                       # drop bold
        fmt = re.sub(r"\s*\(agent knowledge\)\s*", "", fmt, flags=re.I).strip()
        rows.append({"format": fmt, "example": cells[1], "headline_template": cells[2], "why_links": cells[3]})
    return rows


def _read(path, label):
    if not os.path.exists(path):
        sys.exit(f"!! missing {label}: {c.rel(path)}")
    return open(path).read()


def run(redo=False):
    os.makedirs(c.WORK, exist_ok=True)
    os.makedirs(c.OUT, exist_ok=True)
    scope = _read(c.BRAND_SCOPE, "brand-scope.md (run Method 1 / G0 first)")

    # A1 — Source 1: the proven table (deterministic)
    source1 = _parse_source1_table(c.RECIPE_MD)
    print(f"   A1: {len(source1)} proven formats lifted from the recipe table")

    # A2 — Source 2: agent knowledge (LLM), concatenated onto Source 1
    existing = "\n".join(f"- {r['format']}" for r in source1)
    p = (llm.load_prompt("a2-extra-formats.md")
         .replace("{{BRAND}}", c.BRAND).replace("{{EXISTING_FORMATS}}", existing)
         .replace("{{N}}", str(c.EXTRA_FORMATS)))
    extra = llm.call_json(p).get("formats", [])
    extra = [{"format": e.get("format", "").strip(), "example": e.get("example", ""),
              "headline_template": e.get("headline_template", ""), "why_links": e.get("why_links", "")}
             for e in extra if e.get("format")]
    print(f"   A2: {len(extra)} formats added from agent knowledge")
    formats = source1 + extra

    # A3 — pre-screen every format on brand fit (LLM); transplant check before any drop
    listed = "\n".join(f"{i}. {f['format']} — earns links via {f['why_links']}" for i, f in enumerate(formats))
    p = (llm.load_prompt("a3-prescreen.md")
         .replace("{{BRAND}}", c.BRAND).replace("{{BRAND_SCOPE}}", scope).replace("{{FORMATS}}", listed))
    screened = llm.call_json(p).get("screened", [])
    # align by order (the prompt returns one entry per input format, same order)
    survivors, dropped = [], []
    for i, f in enumerate(formats):
        s = screened[i] if i < len(screened) else {"keep": True, "in_scope_subject": "", "brand_fit": "ADJACENT"}
        if s.get("keep", True):
            survivors.append({**f,
                              "in_scope_subject": s.get("in_scope_subject", ""),
                              "brand_fit": s.get("brand_fit", "ADJACENT"),
                              "transplant_from": s.get("transplant_from", "")})
        else:
            dropped.append((f["format"], s.get("drop_reason", "no in-scope subject")))
    print(f"   A3: {len(survivors)} formats kept, {len(dropped)} dropped (transplant-checked)")

    # A4 — pure assembly: swipe.json + format-swipe.md
    c.write_json(os.path.join(c.WORK, "swipe.json"), survivors)
    _write_swipe_md(survivors)
    if dropped:
        with open(os.path.join(c.WORK, "run-log.md"), "a") as log:
            log.write(f"\n## Step A drops ({len(dropped)})\n")
            for fmt, why in dropped:
                log.write(f"- **{fmt}** — {why}\n")
    print(f"   -> {c.rel(os.path.join(c.OUT, 'format-swipe.md'))}")
    return survivors


def _write_swipe_md(survivors):
    from datetime import date
    lines = [f"# Format swipe library — {c.BRAND} (Method 2)",
             f"Proven cross-niche link-bait formats, brand-fit pre-screened to the ones {c.BRAND} can plausibly own.",
             f"Sources: the link-bait dataset (Source 1) + agent knowledge (Source 2).", "",
             "| Format | Real example(s) | Headline template | Why it earns links | In-scope subject | Brand fit |",
             "|---|---|---|---|---|---|"]
    for s in survivors:
        fit = s["brand_fit"] + (f" (from {s['transplant_from']})" if s.get("transplant_from") else "")
        lines.append(f"| {s['format']} | {s['example']} | {s['headline_template']} | {s['why_links']} "
                     f"| {s['in_scope_subject']} | {fit} |")
    c.write_text(os.path.join(c.OUT, "format-swipe.md"), "\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
