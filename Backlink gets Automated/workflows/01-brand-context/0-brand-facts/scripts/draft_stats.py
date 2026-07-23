#!/usr/bin/env python3
"""Step 2 — machine-draft stats candidates from the site catalogue.

Reads:  CATALOGUE_CSV (layer 00's content-database.csv) — candidate pages only: the homepage +
        the top STAT_TOP_PAGES `page`-type rows by Traffic + every STAT_PAGE_TYPES page.
Writes: DRAFTS/stats-draft.md — every row marked ⚠️ with its source URL. The REAL stats.md is
        never touched: the human merges confirmed rows at the gate.

The LLM sees the extraction criteria in prompts/extract-stats.md (J2: a judge must see what defines
its verdict); the script only filters, dedupes and assembles (F2: pure assembly).
"""
import csv, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config, llm, classify_types

csv.field_size_limit(sys.maxsize)
PROMPT = llm.load_prompt("extract-stats.md")
WORKERS = int(os.environ.get("BF_WORKERS", "4"))      # concurrent CLI calls (each is one page)


def _candidates():
    """The homepage + top-traffic `page` rows + every page of the other STAT_PAGE_TYPES."""
    with open(config.CATALOGUE_CSV, newline="", encoding="utf-8", errors="replace") as f:
        rows = [r for r in csv.DictReader(f) if r.get("body_status") == "ok"]
    home = [r for r in rows if r["URL"].rstrip("/") in
            (f"https://{config.DOMAIN}", f"https://www.{config.DOMAIN}")]
    picked = {r["URL"]: r for r in home}
    roles = classify_types.load()
    if roles:
        types = sorted(set(roles.get("stat_types", [])))
        print(f"   stat candidate types (classified for this company): {types}")
    else:
        types = config.STAT_PAGE_TYPES
        print(f"   !! no type-roles.json — falling back to the DEFAULT type names {types} (run classify_types first)")
    for t in types:
        t = t.strip()
        grp = [r for r in rows if r.get("Type") == t]
        if len(grp) > config.STAT_TOP_PAGES:           # any big generic bucket: cap by traffic
            grp.sort(key=lambda r: float(r.get("Traffic") or 0), reverse=True)
            grp = grp[:config.STAT_TOP_PAGES]
        for r in grp:
            picked[r["URL"]] = r
    return list(picked.values())


def _extract(row):
    p = (PROMPT.replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
         .replace("{{URL}}", row["URL"]).replace("{{TITLE}}", row.get("Title", ""))
         .replace("{{BODY}}", (row.get("Full content") or "")[:config.BODY_CHAR_CAP]))
    out = llm.call_json(p)
    return [dict(s, url=row["URL"]) for s in out if isinstance(s, dict) and s.get("value")]


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
        print("   no stat-candidate pages in the catalogue (check BF_STAT_TYPES for this CMS) — draft skipped")
        return None
    print(f"   {len(cands)} candidate pages -> LLM extraction ({WORKERS} at a time)")
    found = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(_extract, r): r["URL"] for r in cands}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                found.extend(fut.result())
            except Exception as e:                     # one bad page never kills the draft — but say so
                print(f"   !! {futs[fut]}: {str(e)[:90]}")
            if i % 10 == 0:
                print(f"   .. {i}/{len(cands)} pages read")

    # dedupe: same normalised value + similar label keeps the first (highest-traffic page came first)
    seen, rows = set(), []
    for s in found:
        key = (s["value"].strip().lower(), s["stat"].strip().lower()[:30])
        if key in seen:
            continue
        seen.add(key)
        rows.append(s)

    by_bucket = {"scale": [], "results": [], "credibility": []}
    for s in rows:
        by_bucket.setdefault(s.get("bucket", "scale"), by_bucket["scale"]).append(s)

    lines = [f"# Stats draft — {config.BRAND} (machine-drafted {os.environ.get('BF_DATE','')} — EVERY row ⚠️ unconfirmed)",
             "", "> Review each row. Confirmed -> copy into `stats.md` and drop the ⚠️. Wrong/duplicate -> delete.",
             f"> Drafted from {len(cands)} pages of the company's own site; {len(rows)} unique candidates.", ""]
    titles = {"scale": "Product / scale", "results": "Results / proof", "credibility": "Credibility"}
    for b in ["scale", "results", "credibility"]:
        lines += [f"## {titles[b]}", "| Stat | Value | Source-note |", "|---|---|---|"]
        for s in by_bucket[b]:
            lines.append(f"| {s['stat']} | {s['value']} | ⚠️ {s['url']} — \"{s.get('quote','')[:80]}\" |")
        lines.append("")
    out = os.path.join(config.BRAND_CTX, "stats.md")
    if _human_confirmed(out):            # a confirmed row (⚠️ removed) is never clobbered
        out = os.path.join(config.DRAFTS, "stats-new-candidates.md")
        print(f"   !! stats.md carries CONFIRMED rows — writing candidates beside it instead")
    config.write_text(out, "\n".join(lines))
    print(f"   {len(rows)} candidate stats -> {out}")
    return out


if __name__ == "__main__":
    run()
