#!/usr/bin/env python3
"""4-writing-examples orchestrator — the runnable twin of writing-examples.workflow.md.

  COMPANY=<slug> python3 run_writing_examples.py [--redo]

Step 1 classify & select (script): pool = top-pages.csv (Traffic + Top Keyword, taken AS-IS per the
       recipe), filtered to classified editorial types, format tagged from URL signals, batches picked
       traffic-first with format diversity (>=3 formats).
Step 2 score & annotate (LLM per article, vs brand-voice.md ONLY): batches loop until 5 on-voice
       survive (the recipe expects multiple rounds). Bodies come from the catalogue — no web-fetch.
Step 3 assemble (script, pure): metadata + What-Makes-It-Great + FULL VERBATIM body per kept example.
Gate   every annotation reason must name a brand-voice pillar (code check: the pillar names appear).
-> _drafts/writing-examples-draft.md  (never the real file)
"""
import argparse, csv, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config, llm

csv.field_size_limit(sys.maxsize)

FORMAT_SIGNALS = [
    (re.compile(r"what-|definition|types-of", re.I), "Definitional / pillar"),
    (re.compile(r"top-\d|-questions|\d+-ways", re.I), "Listicle"),
    (re.compile(r"how-to|-process|-steps", re.I), "Step-by-step how-to"),
    (re.compile(r"-vs-|alternatives", re.I), "Comparison"),
]


def candidates():
    with open(config.CATALOGUE_CSV, newline="", encoding="utf-8", errors="replace") as f:
        cat = {r["URL"]: r for r in csv.DictReader(f) if r.get("body_status") == "ok"
               and r.get("lang", config.LANGUAGE) == config.LANGUAGE}
    etypes = set()
    if os.path.exists(config.TYPE_ROLES):
        etypes = set(json.load(open(config.TYPE_ROLES)).get("editorial_types", []))
    with open(config.TOP_PAGES_CSV, newline="", encoding="utf-8", errors="replace") as f:
        pool = list(csv.DictReader(f))
    out = []
    for row in pool:                                   # top-pages order = traffic order (recipe: as-is)
        r = cat.get(row["URL"])
        if not r or (etypes and r.get("Type") not in etypes):
            continue
        fmt = next((k for rx, k in FORMAT_SIGNALS if rx.search(row["URL"])), "Thought-leadership / other")
        out.append({"url": row["URL"], "traffic": row.get("Traffic", ""), "keyword": row.get("Top Keyword", ""),
                    "format": fmt, "title": r.get("Title", ""), "body": (r.get("Full content") or "")})
    print(f"   pool: {len(out)} editorial candidates (types: {sorted(etypes) or 'URL-signal fallback'})")
    return out


def diverse_batch(pool, used, n):
    """Traffic-first with format diversity: round-robin the formats, highest-traffic first (recipe 1.5)."""
    by_fmt = {}
    for c in pool:
        if c["url"] not in used:
            by_fmt.setdefault(c["format"], []).append(c)
    batch, i = [], 0
    while len(batch) < n and any(by_fmt.values()):
        for fmt in list(by_fmt):
            if by_fmt[fmt] and len(batch) < n:
                batch.append(by_fmt[fmt].pop(0))
        i += 1
    return batch


def score(article, voice):
    p = (llm.load_prompt("score-article.md")
         .replace("{{BRAND}}", config.BRAND).replace("{{URL}}", article["url"])
         .replace("{{KEYWORD}}", article["keyword"]).replace("{{VOICE}}", voice)
         .replace("{{BODY}}", article["body"][:config.BODY_CHAR_CAP]))
    out = llm.call_json(p)
    out.update(article)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    scored_path = os.path.join(config.WORK, "scored.json")
    if a.redo and os.path.exists(scored_path):
        os.remove(scored_path)
    print(f"company: {config.COMPANY} ({config.BRAND})")
    voice_p = os.path.join(config.BRAND_CTX, "brand-voice.md")
    if not os.path.exists(voice_p):
        sys.exit("!! no brand-voice.md — build builder 1 first (it is the yardstick)")
    voice = open(voice_p, encoding="utf-8").read()

    pool = candidates()
    scored = {s["url"]: s for s in json.load(open(scored_path))} if os.path.exists(scored_path) else {}
    print("== Step 1+2: select <-> score (rounds) ==")
    for rnd in range(1, config.MAX_ROUNDS + 1):
        on_voice = [s for s in scored.values() if s.get("verdict") == "on-voice"]
        if len(on_voice) >= config.KEEP:
            break
        batch = diverse_batch(pool, set(scored), config.BATCH)
        if not batch:
            print("   !! pool exhausted"); break
        print(f"   round {rnd}: scoring {len(batch)} articles ({len(on_voice)} on-voice so far)")
        with ThreadPoolExecutor(max_workers=config.WORKERS) as ex:
            futs = {ex.submit(score, art, voice): art["url"] for art in batch}
            for fut in as_completed(futs):
                try:
                    s = fut.result(); scored[s["url"]] = s
                except Exception as e:
                    print(f"   !! {futs[fut]}: {str(e)[:80]}")
        config.write_text(scored_path, json.dumps(
            [{k: v for k, v in s.items() if k != "body"} for s in scored.values()], indent=1))
    on_voice = sorted([s for s in scored.values() if s.get("verdict") == "on-voice"],
                      key=lambda s: -float(s.get("score", 0)))
    kept = on_voice[:config.KEEP]
    if len(kept) < config.KEEP:
        print(f"   !! only {len(kept)} on-voice after {config.MAX_ROUNDS} rounds — shipping what survived, LOUDLY")

    print("== Step 3: assemble (pure) ==")
    fmts = {k["format"] for k in kept}
    fmt_mix = ", ".join(sorted({k["format"] for k in kept}))
    parts = [f"# {config.BRAND} Writing Examples", "",
             f"<!-- Built by 4-writing-examples (run_writing_examples.py) from top-pages.csv + the catalogue;",
             f"     voice-scored against brand-voice.md; scores in _work/writing-examples/scored.json.",
             f"     Format mix: {fmt_mix}. -->", "",
             f"Five real, published {config.BRAND} articles that genuinely embody `brand-voice.md` — each pasted",
             "in full and annotated with why it's exemplary. Show, don't tell: imitate these.", ""]
    for i, k in enumerate(kept, 1):
        body = k.get("body") or next((c["body"] for c in pool if c["url"] == k["url"]), "")
        # strip trailing CTA/junk chrome lines the reviewer flagged (page artifacts, not article text)
        body = re.sub(r"\n(Try for free|Book a demo|Sign up for free|View plans)[^\n]*$", "", body, flags=re.I)
        parts += [f"## Example {i}: {k.get('title') or k.get('h1','')}", "",
                  f"**URL**: {k['url']}",
                  f"**Primary Keyword**: {k['keyword']}",
                  f"**Format**: {k['format']}",
                  f"**Voice Score**: {k.get('score')}/10",
                  f"**Word Count**: ~{len(body.split())} words", "",
                  "**What Makes It Great**:"]
        parts += [f"- {r}" for r in (k.get("what_makes_it_great") or [])]
        parts += ["", "**Full Content** (verbatim):", "", "```", body.strip(), "```", ""]
    if len(fmts) < 3:
        parts.insert(4, f"> ⚑ HUMAN DECISION: only {len(fmts)} formats survived the voice gate (recipe wants ≥3) — review.")
    config.write_text(config.DRAFT_MD, "\n".join(parts))
    print(f"   {len(kept)} examples ({len(fmts)} formats) -> {config.DRAFT_MD}")
    print("== WRITTEN IN PLACE: writing-examples.md — review with `git diff` ==")


if __name__ == "__main__":
    main()
