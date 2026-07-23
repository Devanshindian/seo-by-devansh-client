#!/usr/bin/env python3
"""Step C — filter each competitor's pages down to the replicable editorial ones.

THE GOVERNING RULE, from the recipe (L213-214): "keep any non-200 with a substantive content path;
only root-variant redirects and 404/410 are dropped." And the scar behind it (L239-245): an earlier
filter dropped every non-200 and "quietly destroyed real editorial — eSkill collapsed to 38 kept pages
and TalentLyft to 22." Verdict: **over-dropping is unrecoverable; over-keeping isn't.**

The second scar (L247-250): matching keywords against the FULL URL made "keep anything with 'test' in
it" match every page on testgorilla.com. So every rule below matches the PATH only, never the domain.

Every drop is recorded with its reason — a silent filter is how you lose 200 pages and never know.

Reads:  _raw/<domain>-pages.json
Writes: _work/candidates/<domain>.json  (kept rows)
        _work/filter-report.json        (kept/dropped per competitor, with reasons)
"""
import argparse, json, os, re, sys
from urllib.parse import urlsplit, parse_qsl, urlencode
import config as c

# Query keys that identify the TRAFFIC SOURCE, never the page. Measured 2026-07-20: adaface's
# /ai/resume-screening arrived four times (bare, trailing slash, ?utm_source=listedai,
# ?utm_source=futurepedia) and imocha's /recruitment-assessment-tools six times — the same article,
# counted six times, its link pull split across the copies. 166 such rows rode the whole pipeline.
_TRACKING = ("utm_", "ref", "referrer", "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid",
             "_hsenc", "_hsmi", "hsctatracking", "igshid", "src", "source", "campaign")


def canon_url(url):
    """The identity of a PAGE, ignoring how a visitor happened to arrive at it.

    Deliberately conservative: only KNOWN tracking keys are dropped, never the whole query string,
    because plenty of real pages are addressed by query (?p=123, ?id=45). Dropping every param would
    silently merge genuinely different pages, and over-merging is unrecoverable here in exactly the
    way over-dropping is (the Step C scar)."""
    try:
        s = urlsplit(url)
    except Exception:
        return (url or "").lower()
    host = (s.netloc or "").lower().split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    keep = [(k, v) for k, v in parse_qsl(s.query, keep_blank_values=True)
            if not any(k.lower() == t or k.lower().startswith(t) for t in _TRACKING)]
    path = (s.path or "/").rstrip("/") or "/"
    return f"{host}{path}" + (f"?{urlencode(sorted(keep))}" if keep else "")


def dedupe(rows):
    """Collapse rows that are the same page. Returns (kept, dropped_count).

    The survivor is the variant with the MOST follow domains, and its counts are left ALONE rather
    than summed: we hold counts, not the referring-domain lists, so adding them would double-count
    any domain that links to two variants. Max is the honest floor — it never inflates a format's
    apparent link pull, and inflation is the one error this study cannot survive."""
    best = {}
    for r in rows:
        k = canon_url(r.get("url") or "")
        cur = best.get(k)
        if cur is None or (r.get("domains_follow") or 0) > (cur.get("domains_follow") or 0):
            best[k] = r
    return list(best.values()), len(rows) - len(best)


def _path(url):
    try:
        return (urlsplit(url).path or "/").lower()
    except Exception:
        return "/"


def _sub(url):
    try:
        host = urlsplit(url).netloc.lower()
        parts = host.split(".")
        return parts[0] if len(parts) > 2 else ""
    except Exception:
        return ""


def _first_seg(path):
    segs = [s for s in path.split("/") if s]
    return segs[0] if segs else ""


def drop_reason(row):
    """Return a reason to drop, or None to keep. PATH-only matching (the brand-in-domain scar)."""
    url = row.get("url") or ""
    if not url:
        return "unparseable"
    path = _path(url)
    segs = [s for s in path.split("/") if s]

    if len(segs) == 0:
        return "homepage/root-variant"                       # the homepage is not a replicable asset
    if row.get("status_code") in (404, 410):
        return "dead-404/410"                                # only truly dead pages go
    sub = _sub(url)
    if sub and sub in c.DENY_SUB:
        return f"non-content-subdomain:{sub}"
    # a language can live in the SUBDOMAIN as easily as the path: fr.example.com/resources/x is the
    # same page as example.com/resources/x. Caught by Step E reading 3 empty fr.makipeople.com pages.
    if sub and sub in c.LOCALES:
        return f"locale-subdomain:{sub}"
    if _first_seg(path) in c.LOCALES:
        return "locale-duplicate"                            # the same asset in another language
    if len(segs) >= 2 and segs[-1].isdigit() and segs[-2] in c.PAGINATION_SEGS:
        return "nav/archive-index"
    if any(s in c.JOB_SEGS for s in segs[:2]) and len(segs) >= 2:
        return "job-posting"                                 # their careers pages, not their assets
    for pat in c.DROP_PATH_SUBSTR:
        if pat in path:
            return f"commercial/utility:{pat}"
    if row.get("domains_follow", 0) < c.MIN_FOLLOW_DOMAINS:
        return f"below-link-floor:<{c.MIN_FOLLOW_DOMAINS}"    # no link pull = nothing to learn from
    return None


def run(redo=False):
    os.makedirs(os.path.join(c.WORK, "candidates"), exist_ok=True)
    report, kept_total = [], 0
    files = sorted(f for f in os.listdir(c.RAW) if f.endswith("-pages.json"))
    if not files:
        sys.exit("!! no _raw/*-pages.json — run step_b_pages.py first")

    for f in files:
        domain = f.replace("-pages.json", "")
        out_path = os.path.join(c.WORK, "candidates", f"{domain}.json")
        if os.path.exists(out_path) and not redo:
            kept = json.load(open(out_path))
            kept_total += len(kept)
            report.append({"competitor": domain, "kept": len(kept), "cached": True})
            continue
        rows = json.load(open(os.path.join(c.RAW, f)))
        kept, reasons = [], {}
        for r in rows:
            why = drop_reason(r)
            if why:
                reasons[why] = reasons.get(why, 0) + 1
            else:
                kept.append(r)
        kept, dup = dedupe(kept)                 # same page, several addresses — count it ONCE
        if dup:
            reasons["duplicate-url(utm/slash/www)"] = dup
        c.write_json(out_path, kept)
        kept_total += len(kept)
        report.append({"competitor": domain, "in": len(rows), "kept": len(kept),
                       "dropped": len(rows) - len(kept), "reasons": reasons, "cached": False})
        flag = ""
        if rows and len(kept) < c.LOW_KEEP_ALARM:
            flag = f"   ← ALARM: only {len(kept)} kept, check the rules"
        print(f"   {domain:26s} {len(rows):>4} -> {len(kept):>4} kept"
              + (f"  ({dup} dupes merged)" if dup else "") + flag)

    c.write_json(os.path.join(c.WORK, "filter-report.json"), report)
    print(f"\n   {kept_total} pages kept across {len(files)} competitors")
    agg = {}
    for r in report:
        for k, v in (r.get("reasons") or {}).items():
            agg[k] = agg.get(k, 0) + v
    if agg:
        print("   dropped, by reason:")
        for k, v in sorted(agg.items(), key=lambda kv: -kv[1]):
            print(f"     {v:>5}  {k}")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
