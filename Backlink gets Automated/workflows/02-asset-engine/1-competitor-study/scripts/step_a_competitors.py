#!/usr/bin/env python3
"""Step A — build the approved competitor list.

Reads:  DataForSEO competitors_domain for the company's own domain (+ any competitors the OPERATOR
        supplies, which are pre-approved and always kept).
Writes: _work/candidates.json      — the raw API list, cached (never re-paid on a re-run)
        _work/shortlist.json       — the LLM's pick, with group + reason per competitor
        output/competitors.md      — THE deliverable, and the human gate's subject

A1 discovery is MECHANICAL (one API call). A2/A3 shortlist + direct/adjacent is LLM JUDGMENT — proven
necessary on 2026-07-20: the raw API list ranked scribd #3, study.com #5, investopedia #8 and
cambridge.org #11 for testlify.com. A4 is a HUMAN GATE.

  COMPANY=<slug> python3 step_a_competitors.py [--add "a.com,b.com"] [--add-file f] [--redo]
"""
import argparse, json, os, sys
import config as c
sys.path.insert(0, c.SHARED)
import dfs, llm
import enrich_candidates, validate_domains

ENDPOINT = "/v3/dataforseo_labs/google/competitors_domain/live"


def discover(redo=False):
    """A1 — one paid call, cached. The API ranks by KEYWORD OVERLAP, so this is a candidate
    generator, never an answer (see _shared/dfs-fit-report.md)."""
    path = os.path.join(c.WORK, "candidates.json")
    if os.path.exists(path) and not redo:
        items = json.load(open(path))
        print(f"   {len(items)} candidates (cached — no spend)")
        return items
    before = dfs.preflight()
    r = dfs.call(ENDPOINT, [{"target": c.DOMAIN, "location_name": c.LOCATION,
                             "language_code": c.LANGUAGE, "limit": c.CANDIDATE_LIMIT,
                             "exclude_top_domains": True, "item_types": ["organic"]}])
    items = dfs.first_result(r).get("items") or []
    dfs.assert_shape(ENDPOINT, items, ["domain", "metrics.organic.count"])
    dfs.spend(f"competitors_domain limit={c.CANDIDATE_LIMIT}", before, dfs.balance())
    out = []
    for it in items:
        m = (it.get("metrics") or {}).get("organic") or {}
        d = (it.get("domain") or "").lower().replace("www.", "")
        if d and d != c.DOMAIN.replace("www.", ""):        # never list ourselves
            out.append({"domain": d, "keywords": m.get("count", 0), "etv": round(m.get("etv", 0))})
    c.write_json(path, out)
    print(f"   {len(out)} candidates -> {c.rel(path)}")
    return out


def _supplied(args):
    """Competitors the OPERATOR names. Pre-approved: always kept, even if the API never saw them.
    Generalized on purpose — the operator knows their market, the API does not. On 2026-07-20 the API
    missed 3 of Testlify's 12 real competitors (recruiterflow, wecp, maki)."""
    names = []
    if args.add:
        names += [x.strip() for x in args.add.split(",")]
    if args.add_file and os.path.exists(args.add_file):
        names += [ln.strip() for ln in open(args.add_file) if ln.strip() and not ln.startswith("#")]
    return [n.lower().replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            for n in names if n]


def shortlist(cands, supplied, redo=False):
    """A2/A3 — LLM judgment. Criteria live in prompts/shortlist-competitors.md (J2)."""
    path = os.path.join(c.WORK, "shortlist.json")
    if os.path.exists(path) and not redo:
        out = json.load(open(path))
        print(f"   {len(out.get('competitors', []))} shortlisted (cached)")
        return out
    def row(x):
        d = (x.get("description") or x.get("title") or "").strip()
        base = f"{x['domain']} · {x['keywords']} kw"
        return f"{base} · {d}" if d else f"{base} · (no description available)"
    table = "\n".join(row(x) for x in cands)
    p = (open(os.path.join(c.PROMPTS, "shortlist-competitors.md")).read()
         .replace("{{BRAND}}", c.BRAND).replace("{{ONELINER}}", c.ONELINER)
         .replace("{{NICHE}}", c.NICHE).replace("{{N}}", str(c.SHORTLIST_N))
         .replace("{{USER_SUPPLIED}}", "\n".join(f"- {s}" for s in supplied) or "(none)")
         .replace("{{CANDIDATES}}", table))
    out = llm.call_json(p)
    # the operator's picks are pre-approved: if the model dropped one, put it back
    # every name the model returned, INCLUDING aliases — otherwise re-adding an operator domain that
    # the model correctly merged under another name recreates the duplicate we just asked it to avoid
    have = set()
    for x in out.get("competitors", []):
        have.add(x.get("domain", "").lower())
        for al in (x.get("aliases") or []):
            have.add(str(al).lower().replace("www.", ""))
    for s in supplied:
        if s not in have:
            out.setdefault("competitors", []).append(
                {"domain": s, "group": "DIRECT", "why": "operator-supplied", "user_supplied": True})
            print(f"   !! model dropped operator-supplied '{s}' — re-added (pre-approved)")
    c.write_json(path, out)
    print(f"   {len(out.get('competitors', []))} shortlisted -> {c.rel(path)}")
    return out


def write_md(sl, supplied):
    """A4's subject — the file the human approves."""
    comps = sl.get("competitors", [])
    direct = [x for x in comps if x.get("group") == "DIRECT"]
    adj = [x for x in comps if x.get("group") != "DIRECT"]
    L = [f"# Competitors — {c.BRAND}", "",
         f"- **Source:** DataForSEO `competitors_domain` ({c.LOCATION} / {c.LANGUAGE}), "
         f"top {c.CANDIDATE_LIMIT} candidates, shortlisted by LLM against the company record.",
         f"- **Operator-supplied (pre-approved):** {', '.join(supplied) if supplied else 'none'}",
         f"- **{len(direct)} direct · {len(adj)} adjacent · {len(comps)} total**", "",
         "> ⚑ THIS IS A GATE. Approve, edit, or add competitors before Step B spends anything.",
         "> Add with: `--add \"one.com,two.com\"` (they are kept whatever the API said).", "",
         "## Direct — sell the same kind of product to the same buyer", ""]
    for x in direct:
        L.append(f"- **{x['domain']}**{' ⟵ operator' if x.get('user_supplied') else ''} — {x.get('why','')}")
    L += ["", "## Adjacent — own the audience, not the product", ""]
    for x in adj:
        L.append(f"- **{x['domain']}**{' ⟵ operator' if x.get('user_supplied') else ''} — {x.get('why','')}")
    if sl.get("excluded_notable"):
        L += ["", "## Notable exclusions (ranked high, deliberately dropped)", ""]
        L += [f"- {e}" for e in sl["excluded_notable"]]
    v = sl.get("validation") or {}
    if v.get("swapped") or v.get("dropped"):
        L += ["", "## Domain validation"]
        for sw in v.get("swapped", []):
            L.append(f"- ⚠️ `{sw['from']}` does not resolve — **using `{sw['to']}`** instead")
        for d in v.get("dropped", []):
            L.append(f"- ❌ `{d}` dropped — dead domain, no live alternative found")
    if sl.get("note"):
        L += ["", f"**Note:** {sl['note']}"]
    path = os.path.join(c.OUT, "competitors.md")
    c.write_text(path, "\n".join(L) + "\n")
    print(f"   -> {c.rel(path)}")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--add", default="", help='competitors YOU name: "a.com,b.com" — always kept')
    ap.add_argument("--add-file", default="", help="a file of competitor domains, one per line")
    ap.add_argument("--redo", action="store_true", help="re-pay for discovery too")
    ap.add_argument("--redo-enrich", action="store_true", help="re-read the homepages (free)")
    ap.add_argument("--redo-shortlist", action="store_true", help="re-run the LLM pick (free)")
    a = ap.parse_args()
    print(f"company: {c.COMPANY} ({c.BRAND})")
    supplied = _supplied(a)
    if supplied:
        print(f"   operator-supplied (pre-approved): {', '.join(supplied)}")
    print("== A1: discover candidates ==");      cands = discover(a.redo)
    print("== A1b: read what each one IS (free) =="); cands = enrich_candidates.run(a.redo_enrich)
    print("== A2/A3: shortlist + categorize =="); sl = shortlist(cands, supplied, a.redo or a.redo_shortlist)
    print("== A3b: check every domain is LIVE (free) =="); sl = validate_domains.run()
    print("== A4: THE GATE ==");                  write_md(sl, supplied)
    print("   review competitors.md, then run step_b_pages.py")


if __name__ == "__main__":
    main()
