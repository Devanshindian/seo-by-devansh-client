#!/usr/bin/env python3
"""Step 0 — shortlist the voice pages (the job inherited from the retired brand-brain).

Reads:  TOP_PAGES_CSV + CATALOGUE_CSV (Layer 00). Script assembles the candidate table; the LLM makes
        the PICK (top-traffic winners + deliberately-added commercial pages — criteria in
        prompts/pick-pages.md, per J2); script writes the outputs.
Writes: SHORTLIST_MD (grouped, same shape as the hand-built original) + PAGES_DIR/<nnn>-<slug>.md
        (each picked page's body, straight from the catalogue's Full content — no refetch).
Skips itself if SHORTLIST_MD already exists (the human may have curated it — it is then input, not output).
"""
import csv, os, re, sys
import config, llm

csv.field_size_limit(sys.maxsize)


def _catalogue():
    with open(config.CATALOGUE_CSV, newline="", encoding="utf-8", errors="replace") as f:
        return {r["URL"]: r for r in csv.DictReader(f) if r.get("body_status") == "ok"}


def _traffic_map():
    if not os.path.exists(config.TOP_PAGES_CSV):
        return {}
    with open(config.TOP_PAGES_CSV, newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))
    key = "Traffic_clean" if rows and "Traffic_clean" in rows[0] else "Traffic"
    out = {}
    for r in rows:
        try:
            out[r["URL"]] = float(r.get(key) or 0)
        except ValueError:
            out[r["URL"]] = 0.0
    return out


_COMMERCIAL_HINT = re.compile(r"pricing|compare|plans|alternatives|-vs-|why-|integrations?|demo|features?", re.I)


def _commercial_types():
    """This company's commercial page types, CLASSIFIED by 0-brand-facts' type step (type names differ
    per CMS — never hardcoded). Falls back to a URL-pattern hint alone, and says so."""
    import json
    p = os.path.join(config.BRAND_CTX, "_work", "type-roles.json")
    if os.path.exists(p):
        roles = json.load(open(p))
        types = set(roles.get("commercial_types", []))
        print(f"   commercial types (classified for this company): {sorted(types)}")
        return types
    print("   !! no type-roles.json — commercial candidates come from URL patterns only (run 0-brand-facts step 0 first)")
    return set()


def _candidates(cat, traffic):
    """Top-traffic winners + the commercial/positioning pages raw traffic misses (script-side filter;
    the LLM picks from what it is shown, so the shown set must contain both halves)."""
    ranked = sorted(cat.values(), key=lambda r: traffic.get(r["URL"], 0), reverse=True)
    shown = ranked[:config.CAND_TOP_TRAFFIC]
    ctypes = _commercial_types()
    import urllib.parse as _up
    def _depth1(u):
        return len(_up.urlsplit(u).path.strip("/").split("/")) == 1
    # EVERY shallow primary-language commercial-type page is ALWAYS shown — the company's core
    # positioning pages (/pricing/, /why-us/) are shallow and often zero-traffic, and a traffic-ordered
    # cap hid them from the picker twice (measured 2026-07-19). Deeper hint-matchers fill the rest.
    primary_lang = (config.TENANT.get("language") or "en")[:2]   # from the company record — never hardcoded
    core = [r for r in cat.values()
            if r not in shown and r.get("Type") in ctypes and _depth1(r["URL"])
            and r.get("lang", primary_lang) == primary_lang]
    deep = [r for r in cat.values()
            if r not in shown and r not in core
            and (r.get("Type") in ctypes or _COMMERCIAL_HINT.search(r["URL"]))]
    deep.sort(key=lambda r: -traffic.get(r["URL"], 0))
    shown += core + deep[:max(0, config.CAND_COMMERCIAL - len(core))]
    home = cat.get(f"https://{config.DOMAIN}/") or cat.get(f"https://{config.DOMAIN}")
    if home and home not in shown:
        shown.append(home)
    return shown


def _slug(url):
    path = url.rstrip("/").split("/")[-1] or "homepage"
    return re.sub(r"[^a-z0-9-]", "", path.lower())[:50] or "page"


def run():
    if os.path.exists(config.SHORTLIST_MD):
        print(f"   shortlist exists -> {config.SHORTLIST_MD} (curated input — kept; delete it to regenerate)")
        return config.SHORTLIST_MD
    cat, traffic = _catalogue(), _traffic_map()
    cands = _candidates(cat, traffic)
    table = "\n".join(f"{r.get('Type','')} · {int(traffic.get(r['URL'], 0))} · {r['URL']} · {r.get('Title','')[:70]}"
                      for r in cands)
    prompt = (llm.load_prompt("pick-pages.md")
              .replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
              .replace("{{MIN}}", str(config.SHORTLIST_MIN)).replace("{{MAX}}", str(config.SHORTLIST_MAX))
              .replace("{{CANDIDATES}}", table))
    picks = llm.call_json(prompt).get("picks", [])
    picks = [p for p in picks if p.get("url") in cat]          # never accept an invented URL
    if not (config.SHORTLIST_MIN <= len(picks) <= config.SHORTLIST_MAX):
        print(f"   !! picker returned {len(picks)} pages (band {config.SHORTLIST_MIN}-{config.SHORTLIST_MAX}) — review before trusting")

    # save each picked page's body from the catalogue (offline; the site was already fetched in Layer 00)
    os.makedirs(config.PAGES_DIR, exist_ok=True)
    lines = [f"# Page shortlist — {config.BRAND}", "",
             f"- **Source:** the site catalogue (`content-database.csv` + `top-pages.csv`), picked by the",
             f"  shortlist step of the brand-voice engine (criteria: top-traffic winners + deliberately-added",
             f"  commercial/positioning pages).",
             f"- **The number beside each page = estimated monthly organic traffic (DataForSEO).**", ""]
    by_bucket = {}
    for p in picks:
        by_bucket.setdefault((p.get("bucket", "?"), p.get("bucket_name", "")), []).append(p)
    for i, ((b, bn), grp) in enumerate(sorted(by_bucket.items())):
        lines.append(f"## {b}. {bn}")
        for p in grp:
            lines.append(f"- {p['url']}  ({int(p.get('traffic', 0))}, {p.get('note','')})")
        lines.append("")
    for n, p in enumerate(picks, 1):
        r = cat[p["url"]]
        config.write_text(os.path.join(config.PAGES_DIR, f"{n:03d}-{_slug(p['url'])}.md"),
                          f"# {r.get('Title','')}\nSource: {p['url']}\n\n{r.get('Full content','')}")
    lines.append(f"---\nThese {len(picks)} pages are saved in `_pages/` beside this file.")
    config.write_text(config.SHORTLIST_MD, "\n".join(lines))
    print(f"   {len(picks)} pages picked -> {config.SHORTLIST_MD} (+ bodies in _pages/)")
    return config.SHORTLIST_MD


if __name__ == "__main__":
    run()
