#!/usr/bin/env python3
"""2-style-guide orchestrator + steps — the runnable twin of style-guide.workflow.md.

  COMPANY=<slug> python3 run_style_guide.py [--redo]

Step 1 pick the top editorial blogs  (script: classified editorial types + traffic; the recipe's
       URL-signal table backs it up when no classification exists)  -> _work/style-guide/top-blogs.json
Step 2 analyze in batches (LLM per batch — the recipe's 3 sub-agents; prompt file carries the recipe's
       signal list) -> _work/style-guide/analysis.json  (enum signals merged by MAJORITY in code, list
       signals by UNION, per the recipe; free-text signals carried per-batch for the filler to weigh)
Step 3 fill the recipe's template (LLM; template lifted VERBATIM from the recipe MD — F1)
       -> _drafts/style-guide-draft.md  (NEVER style-guide.md — promotion is the human gate)
"""
import argparse, collections, csv, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config, llm

csv.field_size_limit(sys.maxsize)

_BLOG_HINT = re.compile(r"what-|how-to|top-\d|-vs-|types-of|-guide|-tips|-questions|-process|definition|steps", re.I)


def pick_blogs():
    out_path = os.path.join(config.WORK, "top-blogs.json")
    if os.path.exists(out_path):
        return json.load(open(out_path))
    with open(config.CATALOGUE_CSV, newline="", encoding="utf-8", errors="replace") as f:
        rows = [r for r in csv.DictReader(f) if r.get("body_status") == "ok"
                and r.get("lang", config.LANGUAGE) == config.LANGUAGE]
    if os.path.exists(config.TYPE_ROLES):
        etypes = set(json.load(open(config.TYPE_ROLES)).get("editorial_types", []))
        print(f"   editorial types (classified): {sorted(etypes)}")
        blogs = [r for r in rows if r.get("Type") in etypes]
    else:
        print("   !! no type-roles.json — using the recipe's URL-signal fallback")
        blogs = [r for r in rows if _BLOG_HINT.search(r["URL"])]
    blogs.sort(key=lambda r: float(r.get("Traffic") or 0), reverse=True)
    top = [{"url": r["URL"], "title": r.get("Title", ""), "traffic": r.get("Traffic") or "0",
            "body": (r.get("Full content") or "")[:config.BODY_CHAR_CAP]} for r in blogs[:config.TOP_BLOGS]]
    config.write_text(out_path, json.dumps(top, indent=1))
    print(f"   {len(top)} top blogs -> {out_path}")
    return top


ENUM_SIGNALS = ["headline_case", "oxford_comma", "quote_style"]      # majority wins (recipe rule)
LIST_SIGNALS = ["industry_terms", "acronyms", "preferred_words", "avoided_words"]  # union + dedupe
TEXT_SIGNALS = ["brand_naming", "em_dash_usage", "ellipses", "number_style"]       # carried per batch


def analyze(top):
    out_path = os.path.join(config.WORK, "analysis.json")
    if os.path.exists(out_path):
        return json.load(open(out_path))
    prompt_t = llm.load_prompt("analyze-blogs.md")
    n = max(1, len(top) // config.BATCHES)
    batches = [top[i:i + n] for i in range(0, len(top), n)][:config.BATCHES + 1]

    def one(i, batch):
        block = "\n\n".join(f"### {b['title']}\nURL: {b['url']}\n{b['body']}" for b in batch)
        return llm.call_json(prompt_t.replace("{{BRAND}}", config.BRAND).replace("{{BLOGS}}", block))

    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(one, i, b): i for i, b in enumerate(batches)}
        for fut in as_completed(futs):
            results.append(fut.result())
            print(f"   batch {futs[fut] + 1}/{len(batches)} analyzed")
    merged = {}
    for s in ENUM_SIGNALS:
        votes = [r.get(s, "") for r in results if r.get(s)]
        merged[s] = collections.Counter(votes).most_common(1)[0][0] if votes else ""
    for s in LIST_SIGNALS:
        seen, u = set(), []
        for r in results:
            for item in (r.get(s) or []):
                k = str(item).strip().lower()
                if k and k not in seen:
                    seen.add(k); u.append(item)
        merged[s] = u
    for s in TEXT_SIGNALS:
        merged[s] = " | ".join(f"batch{i+1}: {r.get(s,'')}" for i, r in enumerate(results) if r.get(s))
    config.write_text(out_path, json.dumps(merged, indent=1))
    print(f"   merged analysis -> {out_path}")
    return merged


def _template():
    """The recipe's Step-3 template, lifted VERBATIM (F1: the recipe owns it)."""
    text = open(config.RECIPE_MD, encoding="utf-8").read()
    m = re.search(r"```markdown\n(# \[Company\] Style Guide.*?)```", text, re.S)
    if not m:
        raise SystemExit("!! could not find the Step-3 template in the recipe MD")
    return m.group(1)


def fill(top, merged, redo_notes=""):
    blog_table = "\n".join(f"| {i+1} | {b['traffic']} | {b['title'][:60]} | {b['url']} |" for i, b in enumerate(top))
    prompt = (llm.load_prompt("fill-template.md")
              .replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
              .replace("{{TEMPLATE}}", _template())
              .replace("{{ANALYSIS}}", json.dumps(merged, indent=1))
              .replace("{{BLOG_TABLE}}", blog_table)
              .replace("{{REDO_NOTES}}", f"\nREVIEWER FINDINGS to fold in (implement each concretely):\n{redo_notes}\n" if redo_notes else ""))
    draft = llm.call_text(prompt)
    if draft.startswith("```"):
        draft = re.sub(r"^```[a-z]*\n|\n```$", "", draft.strip())
    config.write_text(config.DRAFT_MD, draft)
    leftovers = re.findall(r"\[(?:BLOGS|STANDARD|COMPANY)[^\]]*\]", draft)
    print(f"   draft -> {config.DRAFT_MD} ({len(draft.split())} words; unresolved tags: {len(leftovers)})")
    if leftovers:
        print(f"   !! unresolved: {leftovers[:5]}")
    return config.DRAFT_MD


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--notes-file", default="", help="reviewer findings to fold into the fill")
    a = ap.parse_args()
    if a.redo:
        for f in ("top-blogs.json", "analysis.json"):
            p = os.path.join(config.WORK, f)
            if os.path.exists(p): os.remove(p)
    if not os.path.exists(config.CATALOGUE_CSV):
        sys.exit("!! no site catalogue — run Layer 00 first")
    print(f"company: {config.COMPANY} ({config.BRAND})")
    print("== Step 1: pick top blogs ==");    top = pick_blogs()
    print("== Step 2: analyze (batched) =="); merged = analyze(top)
    notes = open(a.notes_file).read() if a.notes_file else ""
    print("== Step 3: fill the template =="); fill(top, merged, redo_notes=notes)
    print("== WRITTEN IN PLACE: style-guide.md — review with `git diff` ==")


if __name__ == "__main__":
    main()
