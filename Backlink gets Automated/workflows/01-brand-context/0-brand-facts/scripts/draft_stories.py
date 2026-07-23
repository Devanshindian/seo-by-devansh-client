#!/usr/bin/env python3
"""Step 3 — machine-draft story candidates from the site catalogue.

Reads:  CATALOGUE_CSV — every page whose Type is in STORY_PAGE_TYPES (success stories, press,
        podcasts: the pages where companies tell their own anecdotes).
Writes: DRAFTS/stories-draft.md — every draft marked ⚠️ with its source URL. The REAL stories.md
        is never touched: the human approves at the gate.
"""
import csv, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config, llm, classify_types

csv.field_size_limit(sys.maxsize)
PROMPT = llm.load_prompt("extract-stories.md")
WORKERS = int(os.environ.get("BF_WORKERS", "4"))


def _candidates():
    with open(config.CATALOGUE_CSV, newline="", encoding="utf-8", errors="replace") as f:
        rows = [r for r in csv.DictReader(f) if r.get("body_status") == "ok"]
    roles = classify_types.load()
    if roles:
        types = set(roles.get("story_types", []))
        print(f"   story candidate types (classified for this company): {sorted(types)}")
    else:
        types = {x.strip() for x in config.STORY_PAGE_TYPES}
        print(f"   !! no type-roles.json — falling back to the DEFAULT type names {sorted(types)} (run classify_types first)")
    return [r for r in rows if r.get("Type") in types]


def _extract(row):
    p = (PROMPT.replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
         .replace("{{URL}}", row["URL"]).replace("{{TITLE}}", row.get("Title", ""))
         .replace("{{BODY}}", (row.get("Full content") or "")[:config.BODY_CHAR_CAP]))
    out = llm.call_json(p)
    if isinstance(out, dict) and out.get("story") and not out.get("none"):
        return dict(out, url=row["URL"])
    return None


def _human_confirmed(path):
    """True if a human has confirmed anything here: a table row (or ### entry) with no ⚠️ left on it."""
    if not os.path.exists(path):
        return False
    for line in open(path, encoding="utf-8"):
        t = line.strip()
        if (t.startswith("|") and t.count("|") >= 3 and "⚠️" not in t
                and "---" not in t and not t.lower().startswith("| stat")):
            return True
        if t.startswith("### ") and "⚠️" not in t:
            return True
    return False


def run():
    cands = _candidates()
    if not cands:
        print("   no story-candidate pages in the catalogue (check BF_STORY_TYPES for this CMS) — draft skipped")
        return None
    print(f"   {len(cands)} candidate pages -> LLM extraction ({WORKERS} at a time)")
    stories = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(_extract, r): r["URL"] for r in cands}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                s = fut.result()
                if s:
                    stories.append(s)
            except Exception as e:
                print(f"   !! {futs[fut]}: {str(e)[:90]}")
            if i % 10 == 0:
                print(f"   .. {i}/{len(cands)} pages read")

    lines = [f"# Stories draft — {config.BRAND} (machine-drafted — EVERY entry ⚠️ unconfirmed)",
             "", "> Review each. Approved -> copy into `stories.md` in its format and sign it. Weak/wrong -> delete.",
             f"> Drafted from {len(cands)} story-type pages; {len(stories)} carried a real anecdote.", ""]
    for s in stories:
        lines += [f"### ⚠️ {s.get('title','(untitled)')}",
                  s.get("story", ""),
                  f"- Point it makes: {s.get('point','')}",
                  f"- Number (if any): {s.get('number','')}",
                  f"- Source: {s['url']}  (machine draft — needs approval)", ""]
    out = os.path.join(config.BRAND_CTX, "stories.md")
    if _human_confirmed(out):            # a confirmed row (⚠️ removed) is never clobbered
        out = os.path.join(config.DRAFTS, "stories-new-candidates.md")
        print(f"   !! stories.md carries CONFIRMED rows — writing candidates beside it instead")
    config.write_text(out, "\n".join(lines))
    print(f"   {len(stories)} candidate stories -> {out}")
    return out


if __name__ == "__main__":
    run()
