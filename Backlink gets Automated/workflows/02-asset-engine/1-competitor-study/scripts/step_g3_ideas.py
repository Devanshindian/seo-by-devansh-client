#!/usr/bin/env python3
"""Step G3 (v2) — KEEP the specific grounded ideas, merge only TRUE repeats, rank. Do NOT squish.

Reads:  _work/g2_sheet.json         (every row with its grounded asset / angle_gap / distinct_angle from G2)
Writes: output/ideas.csv            THE DELIVERABLE — one row per DISTINCT specific idea, ranked
        _work/ideas-ranked.json     the same, structured

WHY THIS REPLACES THE OLD MERGE (Devansh + measured, 2026-07-21). The first G3 squished the ~2,100 grounded
per-page ideas down into ~112 broad CATEGORIES. Blind quality eval, three ways:
    per-row grounded ideas (this engine)  4.6   <- BEST
    the old June hand-run                 4.4
    the squished ~112 categories          3.4   <- the squish WRECKED them
The per-page reasoning (Step G2) is excellent — better than the old hand-run. The hard merge threw that away:
"Free Python Test with a live editor (competitor hides theirs)" collapsed into a vague "Coding Test Library".
So: keep every specific idea, and merge ONLY genuine repeats (the same asset several competitors built) — those
become ONE idea carrying ALL their backlink proof, which is a STRONGER signal, not a weaker one. Devansh's rule:
lean to KEEPING; several competitors on one idea is validation, not noise. (Optional grouping under headings is a
separate, later nicety — it is organisation, not the ideas; it must never delete an idea. See G_GROUP note below.)

Dedup is DETERMINISTIC (a normalised-asset-name key), so it is free, reproducible, CLI-safe, and conservative —
it merges only clear same-asset repeats and never an LLM's guess. Near-duplicate semantic merging (e.g. "Python
Skills Test" vs "Coding Assessment (Python)") is deliberately NOT done here: it needs judgment, risks over-merging
(the exact failure above), and the whole point is to KEEP specific ideas. If ever added, it must be conservative
and audited.
"""
import argparse, csv, json, os, re, sys, collections
import config as c

_FIT_ORDER = {"CORE": 0, "TRANSPLANT": 1, "ADJACENT": 2, "SKIP": 9}
_STOP = {"the", "a", "an", "for", "of", "and", "with", "to", "in", "on", "your", "our", "free"}


def _norm_key(asset):
    """A conservative identity for 'the same asset'. Lowercase, drop punctuation and filler words, sort the
    remaining word-stems. So 'Free Python Skills Test' and 'Python Skills Test (Free)' collapse; 'Python Test'
    and 'Java Test' do NOT. Deliberately blunt — it only ever merges obvious repeats, never near-neighbours."""
    words = re.findall(r"[a-z0-9]+", (asset or "").lower())
    stems = sorted(w[:-1] if len(w) > 4 and w.endswith("s") else w for w in words if w not in _STOP)
    return " ".join(stems)


def run(redo=False):
    sheet = os.path.join(c.WORK, "g2_sheet.json")
    if not os.path.exists(sheet):
        sys.exit("!! no _work/g2_sheet.json — run step_g2_reason.py first")
    from urllib.parse import urlsplit
    import statistics
    rows = json.load(open(sheet))

    # per-page word count, keyed by URL, from EVERY row (survivors AND merged-away pages) so an idea can
    # report the typical length of the competitor pages behind it. Source = the real SCRAPED text
    # (len(body.split())); DataForSEO's own `words` is an unreliable fallback (often 0). This is the same
    # count the format-summary median uses — one source of truth for "how long is a page like this".
    def _wc(r):
        if r.get("read_status") == "ok" and (r.get("body") or "").strip():
            return len(r["body"].split())
        w = r.get("words")
        return w if isinstance(w, int) and w > 0 else 0
    url_words = {r.get("url", ""): _wc(r) for r in rows if r.get("url")}

    ideas = [r for r in rows if (r.get("brand_fit") or "") != "SKIP" and (r.get("asset") or "").strip()]
    # SURVIVORS: rows the semantic dedup (Step G2.5) did NOT merge away. If G2.5 never ran, every row is a
    # survivor and the string-key group below is the only dedup (the earlier behaviour). Either way, each
    # survivor already carries its pooled proof (domains/backlinks summed, _merged_urls/_merged_gaps).
    survivors = [r for r in ideas if not r.get("merged_into")]
    if len(survivors) < len(ideas):
        print(f"   {len(ideas)} reasoned ideas -> {len(survivors)} after semantic dedup (G2.5)")
    else:
        print(f"   {len(ideas)} specific grounded ideas (no semantic dedup applied)")

    def _urls(r):
        return r.get("_merged_urls") or [r.get("url", "")]

    def _gaps(r):
        own = [f"[{r.get('url','')}] {r.get('angle_gap','')}"] if r.get("angle_gap") else []
        return own + (r.get("_merged_gaps") or [])

    # backstop string-key group (catches any exact-name twins G2.5's threshold missed), pooling proof
    groups = collections.OrderedDict()
    for r in survivors:
        groups.setdefault(_norm_key(r["asset"]), []).append(r)

    out = []
    for k, members in groups.items():
        members.sort(key=lambda r: -(r.get("domains_follow") or 0))    # strongest phrasing/proof leads
        lead = members[0]
        urls = [u for m in members for u in _urls(m) if u]
        gaps = [g for m in members for g in _gaps(m)]
        comps = len({urlsplit(u).netloc.lower().replace("www.", "") for u in urls if u})
        wcs = [url_words[u] for u in urls if url_words.get(u, 0) > 0]     # typical length of the backing pages
        out.append({
            "asset": lead.get("asset", ""),
            "brand_fit": collections.Counter(m.get("brand_fit", "") for m in members).most_common(1)[0][0],
            "format": collections.Counter(m.get("format", "") for m in members).most_common(1)[0][0],
            "distinct_angle": lead.get("distinct_angle", ""),
            # a build flag rides up if ANY backing page needed one (empty for normal article ideas)
            "tool_escalation": next((m.get("tool_escalation", "") for m in members
                                     if (m.get("tool_escalation") or "").strip()), ""),
            "backing_pages": len(urls),
            "competitors": comps or 1,
            "median_words": int(statistics.median(wcs)) if wcs else 0,    # median beats mean — one huge page can't skew it
            "total_domains": sum(m.get("domains_follow", 0) for m in members),
            "total_backlinks": sum(m.get("backlinks", 0) for m in members),
            "backing_urls": " ; ".join(urls),
            "angle_gaps": " ‖ ".join(gaps),
        })
    merged_away = len(ideas) - len(out)

    # RANK — pure Python, no LLM: brand-fit tier first, then pooled link-pull (the real backlink signal),
    # then fewer backing pages last as a mild tiebreak. Evidence recurring across competitors floats up.
    out.sort(key=lambda x: (_FIT_ORDER.get(x["brand_fit"], 5), -x["total_domains"], -x["competitors"]))
    now_n = int(os.environ.get("CS_NOW_COUNT", "40"))
    for i, x in enumerate(out):
        x["rank"] = i + 1
        x["build_window"] = "NOW" if i < now_n else "LATER"

    os.makedirs(c.OUT, exist_ok=True)
    path = os.path.join(c.OUT, "ideas.csv")
    cols = ["rank", "build_window", "brand_fit", "asset", "format", "tool_escalation", "distinct_angle",
            "backing_pages", "competitors", "median_words", "total_domains", "total_backlinks",
            "backing_urls", "angle_gaps"]
    with open(path + ".tmp", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for x in out:
            w.writerow({k: x.get(k, "") for k in cols})
    os.replace(path + ".tmp", path)
    c.write_json(os.path.join(c.WORK, "ideas-ranked.json"), out)

    fits = collections.Counter(x["brand_fit"] for x in out)
    print(f"   merged {merged_away} true repeats -> {len(out)} distinct ideas ({100*len(out)/max(len(ideas),1):.0f}% kept)")
    print(f"   brand fit: {dict(fits)}")
    print(f"   NOW: {now_n} · LATER: {len(out)-now_n}")
    print(f"\n   TOP 12 (ranked by pooled follow-domains):")
    for x in out[:12]:
        print(f"     #{x['rank']:>3} [{x['brand_fit'][:4]}] d={x['total_domains']:>5} "
              f"({x['competitors']}comp/{x['backing_pages']}pg)  {x['asset'][:58]}")
    print(f"\n   -> {c.rel(path)}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
