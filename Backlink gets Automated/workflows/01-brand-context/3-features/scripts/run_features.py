#!/usr/bin/env python3
"""3-features orchestrator + steps — the runnable twin of features.workflow.md.

  COMPANY=<slug> python3 run_features.py [--redo]

Step 1 discover the commercial/product pages — script filters by the CLASSIFIED commercial types +
       the recipe's URL signals; per-kind traffic caps keep a 3,600-page product catalogue sane
       (the recipe predates the Type column — this replaces its URL-chunk sub-agents; deviation
       recorded in README).  -> _work/features/source-pages.json
Step 2 collect the facts — one LLM call per page with the recipe's EXACT fact categories
       (no live-fetch: the new catalogue's keep-everything extraction retains pricing tables).
       Resumable per page.  -> _work/features/facts.json
Step 3 fill the schema — LLM, pure assembly; Appendix A AND the consolidation method + mapping
       table lifted VERBATIM from the recipe (F1).  -> _drafts/features-draft.md
Step 4 quality gate (LLM judge: completeness/facts-only/consolidation) — loops back to 3, capped.
"""
import argparse, csv, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config, llm

csv.field_size_limit(sys.maxsize)

_KIND_HINTS = [
    (re.compile(r"/(pricing|plans|compare)", re.I), "pricing / plans / compare"),
    (re.compile(r"alternatives|-vs-", re.I), "competitor comparison"),
    (re.compile(r"integration", re.I), "integrations"),
]


def discover():
    out_path = os.path.join(config.WORK, "source-pages.json")
    if os.path.exists(out_path):
        return json.load(open(out_path))
    with open(config.CATALOGUE_CSV, newline="", encoding="utf-8", errors="replace") as f:
        rows = [r for r in csv.DictReader(f) if r.get("body_status") == "ok"
                and r.get("lang", config.LANGUAGE) == config.LANGUAGE]
    roles = json.load(open(config.TYPE_ROLES)) if os.path.exists(config.TYPE_ROLES) else {}
    ctypes = set(roles.get("commercial_types", []) + roles.get("stat_types", []))
    if not ctypes:
        print("   !! no type-roles.json — URL signals only")
    picked = {}
    for r in rows:
        url = r["URL"]
        kind = next((k for rx, k in _KIND_HINTS if rx.search(url)), None)
        if kind is None and r.get("Type") in ctypes:
            kind = "homepage" if url.rstrip("/").count("/") == 2 and url.rstrip("/").endswith(config.TENANT.get("domain", "")) \
                else "product or feature page"
        if kind:
            picked[url] = {"url": url, "kind": kind, "traffic": float(r.get("Traffic") or 0),
                           "title": r.get("Title", ""), "body": (r.get("Full content") or "")[:config.BODY_CHAR_CAP]}
    # per-kind caps by traffic: pricing/compare + homepage always ALL; big kinds capped
    by_kind = {}
    for p in picked.values():
        by_kind.setdefault(p["kind"], []).append(p)
    final = []
    for kind, grp in by_kind.items():
        grp.sort(key=lambda p: -p["traffic"])
        cap = len(grp) if kind in ("homepage", "pricing / plans / compare", "integrations") else config.PER_KIND_CAP
        final.extend(grp[:cap])
        if len(grp) > cap:
            print(f"   {kind}: {len(grp)} found, top {cap} kept (FT_KIND_CAP)")
    config.write_text(out_path, json.dumps(final, indent=1))
    print(f"   {len(final)} source pages ({len(by_kind)} kinds) -> {out_path}")
    return final


def collect(pages):
    out_path = os.path.join(config.WORK, "facts.json")
    done = {}
    if os.path.exists(out_path):
        done = {f["url"]: f for f in json.load(open(out_path))}
    prompt_t = llm.load_prompt("extract-facts.md")
    todo = [p for p in pages if p["url"] not in done]
    print(f"   {len(done)} cached, {len(todo)} pages to read ({config.WORKERS} at a time)")

    def one(p):
        out = llm.call_json(prompt_t.replace("{{BRAND}}", config.BRAND)
                            .replace("{{URL}}", p["url"]).replace("{{KIND}}", p["kind"])
                            .replace("{{BODY}}", p["body"]))
        out.update(url=p["url"], kind=p["kind"])
        return out

    with ThreadPoolExecutor(max_workers=config.WORKERS) as ex:
        futs = {ex.submit(one, p): p["url"] for p in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                r = fut.result(); done[r["url"]] = r
            except Exception as e:
                print(f"   !! {futs[fut]}: {str(e)[:80]}")
            if i % 10 == 0 or i == len(todo):
                config.write_text(out_path, json.dumps(list(done.values()), indent=1))
                print(f"   .. {i}/{len(todo)}")
    config.write_text(out_path, json.dumps(list(done.values()), indent=1))
    print(f"   facts pool: {len(done)} pages -> {out_path}")
    return list(done.values())


def _lift(pattern, what):
    text = open(config.RECIPE_MD, encoding="utf-8").read()
    m = re.search(pattern, text, re.S)
    if not m:
        raise SystemExit(f"!! could not lift {what} from the recipe MD")
    return m.group(1)


def _seed():
    """HUMAN-VERIFIED facts the crawler cannot reach (JS-rendered prices, etc.). Authoritative:
    the fill must carry these verbatim. Testlify 2026-07-20: the pricing table is absent from the
    catalogue AND the raw HTML — only a browser sees it, so it can only ever be seed."""
    p = os.path.join(config.BRAND_CTX, "_seed", "features-seed.md")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def fill(facts, redo_notes=""):
    schema = _lift(r"# Appendix A[^\n]*\n.*?```markdown\n(.*?)```", "Appendix A")
    method = _lift(r"(\*\*The core method — consolidate.*?)\n\n\| Fill this section", "the consolidation method")
    mapping = _lift(r"(\| Fill this section \|.*?)\n\n\*\*", "the mapping table")
    voice = ""
    if os.path.exists(os.path.join(config.BRAND_CTX, "brand-voice.md")):
        voice = open(os.path.join(config.BRAND_CTX, "brand-voice.md"), encoding="utf-8").read()[:6000]
    pool = "\n\n".join(f"## {f['url']}  ({f['kind']})\n" +
                       "\n".join(f"- {k}: {json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v}"
                                 for k, v in f.items() if k not in ("url", "kind") and v)
                       for f in facts)
    prompt = (llm.load_prompt("fill-schema.md")
              .replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
              .replace("{{SCHEMA}}", schema).replace("{{METHOD}}", method).replace("{{MAPPING}}", mapping)
              .replace("{{VOICE}}", voice).replace("{{FACTS}}", pool)
              .replace("{{SEED}}", _seed())
              .replace("{{REDO_NOTES}}", f"\nREDO NOTES (fix these):\n{redo_notes}\n" if redo_notes else ""))
    draft = llm.call_text(prompt)
    if draft.startswith("```"):
        draft = re.sub(r"^```[a-z]*\n|\n```$", "", draft.strip())
    config.write_text(config.DRAFT_MD, draft)
    print(f"   draft -> {config.DRAFT_MD} ({len(draft.split())} words)")
    return draft


def gate(round_n):
    draft = open(config.DRAFT_MD, encoding="utf-8").read()
    v = llm.call_json(llm.load_prompt("quality-gate.md")
                      .replace("{{BRAND}}", config.BRAND).replace("{{DRAFT}}", draft))
    config.write_text(os.path.join(config.WORK, f"gate-round-{round_n}.json"), json.dumps(v, indent=1))
    print(f"   gate round {round_n}: {'PASS' if v.get('overall_pass') else 'FAIL'}")
    return v


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    ap.add_argument("--notes-file", default="")
    a = ap.parse_args()
    if a.redo:
        for f in ("source-pages.json", "facts.json"):
            p = os.path.join(config.WORK, f)
            if os.path.exists(p): os.remove(p)
    print(f"company: {config.COMPANY} ({config.BRAND})")
    print("== Step 1: discover ==");  pages = discover()
    print("== Step 2: collect facts =="); facts = collect(pages)
    print("== Step 3+4: fill <-> gate ==")
    notes = open(a.notes_file).read() if a.notes_file else ""
    fill(facts, redo_notes=notes)
    for n in range(1, 4):
        v = gate(n)
        if v.get("overall_pass"): break
        if n < 3: fill(facts, redo_notes=v.get("redo_notes", ""))
    # THE LINK TARGETS (2026-08-20). features.md says what we sell; it carries no URLs, because the
    # model that writes it is composing prose. The close of an article has to LINK to a page, so the
    # same crawl is also emitted as a plain lookup. Code, not a model: a clumsy line in features.md
    # costs nothing, a wrong URL in a call to action sends the reader to the wrong page.
    print("== Step 5: the CTA page list ==")
    import build_cta_pages
    build_cta_pages.build()
    print("== WRITTEN IN PLACE: features.md + cta-pages.md — review with `git diff` ==")


if __name__ == "__main__":
    main()
