#!/usr/bin/env python3
"""Search-traffic view — one bulk DataForSEO pull, grouped per page, joined into the catalogue.

Reads:  the company record (domain, location, language) + DataForSEO ranked_keywords (PAID).
Writes: TRAFFIC_RAW (traffic-raw.json — every row, the resume/evidence file; an existing one is
        reused so the paid pull never repeats by accident) and TOP_PAGES_CSV (top-pages.csv).
        Then fills the catalogue's Traffic/Intent columns in place (if the catalogue exists yet).

Rules (each priced or measured):
- BULK, never per-page: one paginated ranked_keywords pull ($2.50) vs per-page calls ($35.80) —
  the per-call base fee dominates.
- Pre-flight credit guard: below MIN_CREDITS the run exits cleanly having spent NOTHING (fail
  open if the balance check itself errors — the paid calls error loudly anyway).
- A vendor's aggregate is confidently wrong: we pull RAW rows and compute BOTH figures —
  `Traffic` (raw etv sum) and `Traffic_clean` (drop is_another_language rows, collapse
  near-duplicate keywords onto keyword_properties.core_keyword taking each core's MAX etv once).
  Emitting both keeps the distortion visible. Downstream builders rank by the CLEANED figure
  (decision locked 2026-07-18).
- Credentials: DFS_LOGIN/DFS_PW from the environment or the canonical repo .env — never here.

top-pages.csv columns: URL · Traffic · Traffic_clean · Top Keyword · Primary Intent · Market
"""
import base64
import csv
import json
import os
import time
import urllib.error
import urllib.request

import config

API = "https://api.dataforseo.com"
TRAFFIC_MAX_ROWS = 50000     # loud safety ceiling on the paginated pull (never a silent cap)


# ---- the one credential chokepoint ----------------------------------------------------------
def _auth():
    login = os.environ.get("DFS_LOGIN", "")
    pw = os.environ.get("DFS_PW", "")
    if not (login and pw):
        env_path = os.path.join(config.REPO_ROOT, ".env")
        if os.path.exists(env_path):
            for line in open(env_path):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "DFS_LOGIN" and not login:
                        login = v.strip()
                    if k.strip() == "DFS_PW" and not pw:
                        pw = v.strip()
    if not (login and pw):
        raise RuntimeError("no DFS_LOGIN / DFS_PW in env or the canonical repo .env")
    return base64.b64encode(f"{login}:{pw}".encode()).decode()


def _call(endpoint, body=None, retries=3):
    req = urllib.request.Request(
        API + endpoint,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Basic " + _auth(), "Content-Type": "application/json"},
        method="POST" if body is not None else "GET")
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                doc = json.loads(r.read().decode())
            if doc.get("status_code") != 20000:
                raise RuntimeError(f"DataForSEO API error {doc.get('status_code')}: "
                                   f"{doc.get('status_message')}")
            return doc
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"DataForSEO unreachable after {retries} tries: {last}")


def _credit_guard():
    """Below MIN_CREDITS -> exit cleanly having spent nothing. Fail OPEN on check errors."""
    try:
        doc = _call("/v3/appendix/user_data")
        balance = doc["tasks"][0]["result"][0]["money"]["balance"]
    except Exception as e:
        print(f"   balance check failed ({e}) — proceeding; the paid call will error loudly if broke")
        return
    print(f"   DataForSEO balance: ${balance:.2f}")
    if balance < config.MIN_CREDITS:
        raise SystemExit(f"!! balance ${balance:.2f} < MIN_CREDITS ${config.MIN_CREDITS} — "
                         f"stopping BEFORE spending. Top up, then re-run.")


def _pull_rows():
    """The bulk pull: ranked_keywords, limit DFS_LIMIT, offset-paginated on total_count."""
    rows, offset, total, cost = [], 0, None, 0.0
    while True:
        task = {"target": config.DOMAIN, "location_name": config.LOCATION,
                "language_code": config.LANGUAGE, "limit": config.DFS_LIMIT, "offset": offset,
                "order_by": ["ranked_serp_element.serp_item.etv,desc"]}
        doc = _call("/v3/dataforseo_labs/google/ranked_keywords/live", [task])
        t = doc["tasks"][0]
        cost += t.get("cost") or 0
        result = (t.get("result") or [{}])[0]
        if total is None:
            total = result.get("total_count") or 0
            print(f"   total_count={total}, pulling in pages of {config.DFS_LIMIT}")
        items = result.get("items") or []
        # The etv-desc sort is UNSTABLE server-side: the same offset can return 28 rows on one
        # call and 676 on the next. A short page gets ONE re-ask; the larger answer wins.
        expected = min(config.DFS_LIMIT, max(0, total - offset))
        if len(items) < expected:
            doc2 = _call("/v3/dataforseo_labs/google/ranked_keywords/live", [task])
            t2 = doc2["tasks"][0]
            cost += t2.get("cost") or 0
            items2 = ((t2.get("result") or [{}])[0].get("items")) or []
            if len(items2) > len(items):
                items = items2
            if len(items) < expected:
                print(f"   .. offset {offset}: {len(items)}/{expected} rows after retry "
                      f"(vendor total_count overstates; shortfall recorded)")
        rows += items
        offset += config.DFS_LIMIT
        if offset >= total or not items:
            break
        if offset >= TRAFFIC_MAX_ROWS:
            print(f"   !! TRAFFIC_MAX_ROWS ceiling hit at {offset} of {total} — rows beyond "
                  f"this are NOT pulled (raise the ceiling in config to get them)")
            break
    print(f"   pulled {len(rows)} rows, API cost ${cost:.2f}")
    return rows, total, cost


def _group(rows):
    """Per URL: raw sum, cleaned sum, top keyword, intent."""
    pages = {}
    for it in rows:
        kd = it.get("keyword_data") or {}
        serp = ((it.get("ranked_serp_element") or {}).get("serp_item")) or {}
        url = serp.get("url") or ""
        if not url:
            continue
        etv = serp.get("etv") or 0.0
        props = kd.get("keyword_properties") or {}
        p = pages.setdefault(url, {"raw": 0.0, "best_etv": -1.0, "kw": "", "intent": "",
                                   "clean_groups": {}})
        p["raw"] += etv
        if etv > p["best_etv"]:
            p["best_etv"] = etv
            p["kw"] = kd.get("keyword", "")
            p["intent"] = ((kd.get("search_intent_info") or {}).get("main_intent")) or ""
        if not props.get("is_another_language"):
            core = props.get("core_keyword") or kd.get("keyword", "")
            g = p["clean_groups"]
            g[core] = max(g.get(core, 0.0), etv)    # each core keyword counted ONCE (max, not sum)
    out = {}
    for url, p in pages.items():
        out[url] = {"Traffic": round(p["raw"]), "Traffic_clean": round(sum(p["clean_groups"].values())),
                    "Top Keyword": p["kw"], "Primary Intent": p["intent"]}
    return out


def _join_catalogue(per_url):
    """Fill Traffic/Intent in content-database.csv in place (cleaned figure — locked decision)."""
    if not os.path.exists(config.CATALOGUE_CSV):
        print("   catalogue not written yet — join will happen on the full sequenced run")
        return
    from reconcile import _match_key
    by_key = {_match_key(u): v for u, v in per_url.items()}
    import sys as _sys
    csv.field_size_limit(_sys.maxsize)
    with open(config.CATALOGUE_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        cols = rows[0].keys() if rows else []
    hit = 0
    for row in rows:
        m = by_key.get(_match_key(row["URL"]))
        if m:
            row["Traffic"] = m["Traffic_clean"]     # builders rank by the CLEANED figure
            row["Intent"] = m["Primary Intent"]
            hit += 1
    def write(f):
        w = csv.DictWriter(f, fieldnames=list(cols))
        w.writeheader()
        w.writerows(rows)
    config._atomic_write(config.CATALOGUE_CSV, write)
    print(f"   joined traffic into {hit}/{len(rows)} catalogue rows")


def run():
    if os.path.exists(config.TRAFFIC_RAW):
        print(f"   reusing existing {os.path.basename(config.TRAFFIC_RAW)} — the paid pull "
              f"never repeats by accident (delete it or --redo the stage to refetch)")
        raw_doc = json.load(open(config.TRAFFIC_RAW))
    else:
        _credit_guard()
        rows, total, cost = _pull_rows()
        raw_doc = {"market": f"{config.LOCATION}/{config.LANGUAGE}", "total_count": total,
                   "cost_usd": cost, "rows": rows}
        config.write_json(config.TRAFFIC_RAW, raw_doc)

    per_url = _group(raw_doc["rows"])
    market = raw_doc.get("market", f"{config.LOCATION}/{config.LANGUAGE}")
    ranked = sorted(per_url.items(), key=lambda kv: -kv[1]["Traffic_clean"])
    def write(f):
        w = csv.writer(f)
        w.writerow(["URL", "Traffic", "Traffic_clean", "Top Keyword", "Primary Intent", "Market"])
        for url, m in ranked:
            w.writerow([url, m["Traffic"], m["Traffic_clean"], m["Top Keyword"],
                        m["Primary Intent"], market])
    config._atomic_write(config.TOP_PAGES_CSV, write)
    print(f"   {len(per_url)} pages -> {config.TOP_PAGES_CSV}")

    _join_catalogue(per_url)


if __name__ == "__main__":
    run()
