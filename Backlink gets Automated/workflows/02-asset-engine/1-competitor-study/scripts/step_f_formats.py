#!/usr/bin/env python3
"""Step F — aggregate by FORMAT. The table that answers "what should we build?".

The recipe has this step but NO script was ever written for it — the hand-run produced its
format-summary.csv some other way. It is a plain group-by, so it is code.

WHY IT IS THE POINT OF THE WHOLE STUDY: this is where "glossaries earn 119 referring domains per page
while answer-bait earns 27" comes from. Everything before it exists to make this table honest.

RANKED ON FOLLOW DOMAINS (Devansh, 2026-07-20). The hand-run summed raw referring domains. Measured on
this data: 452 of 6,652 pages are >50% nofollow, including pages that looked like top magnets — one
with 343 referring domains had 340 of them nofollow. Nofollow passes no authority, and routing
authority to money pages is the entire point of the reverse-silo, so the ranking column is
`domains_follow`. The raw total is kept beside it so nothing is hidden.

Reads:  _work/read/<domain>.json   (or _work/formats/ if the read step has not run)
Writes: output/format-summary.csv  + _work/format-summary.json
"""
import argparse, collections, csv, json, os, statistics, sys
import config as c


def _rows():
    """Prefer read rows (they carry body length); fall back to tagged rows."""
    for sub in ("read", "formats"):
        d = os.path.join(c.WORK, sub)
        if os.path.isdir(d):
            files = [f for f in os.listdir(d) if f.endswith(".json")]
            if files:
                rows = [r for f in files for r in json.load(open(os.path.join(d, f)))]
                if rows:
                    return rows, sub
    sys.exit("!! nothing to aggregate — run step_d_format.py (and ideally step_e_read.py) first")


def run():
    rows, src = _rows()
    print(f"   aggregating {len(rows)} pages (from _work/{src})")
    # exclude shapes the canonicaliser flagged as not-a-content-asset (user profiles, help pages,
    # homepages, spam). They survived the URL filter but are not things anyone would study or build.
    junk = [r for r in rows if r.get("format_junk")]
    rows = [r for r in rows if not r.get("format_junk")]
    if junk:
        print(f"   excluded {len(junk)} pages whose FORMAT is not a content asset "
              f"(user profiles, help pages, homepages, spam)")
    by = collections.defaultdict(list)
    for r in rows:
        by[r.get("format") or "UNTAGGED"].append(r)

    out = []
    for fmt, group in by.items():
        follow = [g.get("domains_follow", 0) for g in group]
        total = [g.get("domains_total", 0) for g in group]
        words = [len((g.get("body") or "").split()) for g in group if g.get("read_status") == "ok"]
        ages = [g.get("first_seen", "")[:4] for g in group if g.get("first_seen")]
        out.append({
            "Format": fmt,
            "# pages": len(group),
            "Total follow domains": sum(follow),
            "Avg follow domains": round(sum(follow) / max(len(group), 1), 1),
            "Best page follow domains": max(follow) if follow else 0,
            "Total domains (incl nofollow)": sum(total),
            "# competitors": len({g["competitor"] for g in group}),
            "Median words": int(statistics.median(words)) if words else 0,
            "Oldest page": min(ages) if ages else "",
        })
    # THE ranking: average follow domains per page = how much link pull this SHAPE earns
    out.sort(key=lambda x: -x["Avg follow domains"])

    os.makedirs(c.OUT, exist_ok=True)
    path = os.path.join(c.OUT, "format-summary.csv")
    with open(path + ".tmp", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    os.replace(path + ".tmp", path)
    c.write_json(os.path.join(c.WORK, "format-summary.json"), out)

    print(f"\n   {'FORMAT':38s} {'pages':>6} {'avg follow':>11} {'best':>6} {'comps':>6}")
    for r in out[:22]:
        star = "  ←" if r["# competitors"] >= c.FORMAT_MIN_COMPETITORS and r["# pages"] >= c.FORMAT_MIN_PAGES else ""
        print(f"   {r['Format'][:38]:38s} {r['# pages']:>6} {r['Avg follow domains']:>11} "
              f"{r['Best page follow domains']:>6} {r['# competitors']:>6}{star}")
    print(f"\n   ← = proven across >={c.FORMAT_MIN_COMPETITORS} competitors on >={c.FORMAT_MIN_PAGES} pages "
          f"(a format one competitor happens to own is not a proven format)")
    print(f"   -> {c.rel(path)}")
    return out


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    run()
