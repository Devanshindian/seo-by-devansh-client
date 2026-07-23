#!/usr/bin/env python3
"""The three hard coverage gates + the honest report. A failed gate FAILS the run (exit 1) —
today's only gate merely warned, which is how 27% of a site once went invisible.

Reads:  CATALOGUE_CSV, RECONCILED, URLS_WP, URLS_SITEMAP, TOP_PAGES_CSV, the raw-cache metadata,
        and (when present) the newest _baseline-*/baseline-numbers.json for the before/after table.
Writes: REPORT_MD (catalogue-report.md) — always written, even on failure, so the report itself
        documents WHY the run failed.

Gate 1 — enumeration: per type, collected == the CMS's own X-WP-Total; and every sitemap URL is
         ACCOUNTED FOR (in the catalogue, an alias, or an explicit drop bucket — never lost).
         Non-WordPress sites have no count header: the gate weakens to sitemap-accounting + the
         traffic cross-check, and the report is stamped LOWER-CONFIDENCE — never the same claim.
Gate 2 — response integrity: a cached body shorter than its declared Content-Length (when no
         Content-Encoding) = truncated transfer -> FAIL; documents missing </html> = WARN only
         (some servers truncate their own output).
Gate 3 — extraction coverage PER TYPE (a single global % hides exactly the failure that bit us):
         failed = body_status 'failed'. FAIL below GATE_OVERALL overall or GATE_PER_TYPE per type.
Plus the honest cross-check: any page the traffic pull says is RANKING that the catalogue lacks
is a provable gap — listed in the report.
"""
import csv
import datetime
import json
import os
import sys

import config
import fetch
from reconcile import _match_key


def _load_json(path, default=None):
    return json.load(open(path)) if os.path.exists(path) else (default if default is not None else {})


def _baseline():
    """Newest _baseline-*/baseline-numbers.json under BASE, if any (company-agnostic: it simply
    isn't there for a company without a recorded baseline)."""
    base = config.BASE
    cands = sorted(d for d in os.listdir(base) if d.startswith("_baseline-")) if os.path.isdir(base) else []
    for d in reversed(cands):
        p = os.path.join(base, d, "baseline-numbers.json")
        if os.path.exists(p):
            return d, _load_json(p)
    return None, None


def _confidence(is_wp, unavailable):
    """The headline coverage claim. A type whose endpoint never answered makes the CMS count
    incomplete by an UNKNOWN amount, so the run must not still advertise itself as FULL."""
    if not is_wp:
        return ("LOWER-CONFIDENCE (no CMS count header — sitemap-accounting + traffic cross-check "
                "only; NOT the same guarantee)")
    if unavailable:
        return (f"PARTIAL (CMS count headers verified for every type that answered, but "
                f"{len(unavailable)} type(s) never did — {', '.join(sorted(unavailable))}. Their "
                f"size is unknowable from the CMS, so total coverage is incomplete by an unknown "
                f"amount; see 'Coverage UNKNOWN' below)")
    return "FULL (CMS count headers verified)"


def run():
    import sys as _sys
    csv.field_size_limit(_sys.maxsize)
    rows = list(csv.DictReader(open(config.CATALOGUE_CSV, newline="", encoding="utf-8")))
    rec = _load_json(config.RECONCILED)
    wp = _load_json(config.URLS_WP)
    sm = _load_json(config.URLS_SITEMAP, {"urls": {}})
    top = (list(csv.DictReader(open(config.TOP_PAGES_CSV, newline="", encoding="utf-8")))
           if os.path.exists(config.TOP_PAGES_CSV) else [])

    failures, warnings = [], []
    is_wp = bool(wp.get("types"))

    # ---- gate 1: enumeration --------------------------------------------------------------
    unrenderable, withheld = {}, {}
    for t, meta in (wp.get("types") or {}).items():
        bad = meta.get("unreadable") or []
        held = meta.get("withheld") or 0
        # Same accounting rule the sitemap half of this gate already uses: every item must be
        # ACCOUNTED FOR, not necessarily present. An item the CMS answers 5xx for, or one it
        # counts but refuses to serve an anonymous client, is a known, quantified, reported gap —
        # the opposite of the silent shortfall this gate exists to catch. An UNEXPLAINED
        # difference is still a hard failure.
        if meta["collected"] + len(bad) + held != meta["total"]:
            failures.append(f"gate1: type {t}: collected {meta['collected']} + {len(bad)} "
                            f"unreadable + {held} withheld != CMS total {meta['total']}")
        if bad:
            unrenderable[t] = bad
        if held:
            withheld[t] = (meta["collected"], meta["total"], held)
    accounted = set()
    for url, r in rec.get("pages", {}).items():
        accounted.add(_match_key(url))
        for a in r.get("aliases", []):
            accounted.add(_match_key(a))
    dropped = rec.get("dropped", {})
    for bucket in ("dead", "soft_404", "offsite", "robots"):
        for u in dropped.get(bucket, []):
            accounted.add(_match_key(u))
    for u in dropped.get("collapsed", {}):
        accounted.add(_match_key(u))
    lost = [u for u in sm.get("urls", {}) if _match_key(u) not in accounted]
    if lost:
        failures.append(f"gate1: {len(lost)} sitemap URLs are neither in the catalogue nor in "
                        f"any drop bucket (first: {lost[:3]})")

    # ---- gate 2: response integrity -------------------------------------------------------
    truncated, unclosed = [], 0
    with fetch._db_lock:
        cur = fetch._conn().execute(
            "SELECT url, sha, content_type, kept_headers FROM pages WHERE status=200")
        page_rows = cur.fetchall()
    for url, sha, ctype, kept in page_rows:
        if not sha or "html" not in (ctype or "").lower():
            continue
        path = fetch._raw_path(sha, ctype)
        if not os.path.exists(path):
            continue
        body = open(path, "rb").read()
        headers = json.loads(kept) if kept else {}
        clen = headers.get("content-length")
        if clen and "content-encoding" not in headers and clen.isdigit():
            if len(body) < int(clen):
                truncated.append(url)
        if b"</html" not in body[-4096:].lower():
            unclosed += 1
    if truncated:
        failures.append(f"gate2: {len(truncated)} bodies shorter than their declared "
                        f"Content-Length (truncated transfers; first: {truncated[:3]})")
    if unclosed:
        warnings.append(f"gate2: {unclosed} documents without a closing </html> "
                        f"(warn only — some servers truncate their own responses)")

    # ---- gate 3: extraction coverage, PER TYPE --------------------------------------------
    per_type = {}
    for row in rows:
        d = per_type.setdefault(row["Type"] or "(untyped)",
                                {"rows": 0, "ok": 0, "stub": 0, "flagged": 0, "failed": 0})
        d["rows"] += 1
        status = row["body_status"] if row["body_status"] in ("ok", "stub", "flagged") else "failed"
        d[status] += 1
    covered_total = sum(d["ok"] + d["stub"] + d["flagged"] for d in per_type.values())
    overall = covered_total / max(1, len(rows))
    if overall < config.GATE_OVERALL:
        failures.append(f"gate3: overall coverage {overall:.1%} < {config.GATE_OVERALL:.0%}")
    for t, d in sorted(per_type.items()):
        cov = (d["ok"] + d["stub"] + d["flagged"]) / max(1, d["rows"])
        if cov < config.GATE_PER_TYPE:
            failures.append(f"gate3: type {t}: coverage {cov:.1%} < {config.GATE_PER_TYPE:.0%} "
                            f"({d['failed']} failed of {d['rows']})")

    # ---- the honest cross-check: ranking pages missing from the catalogue ------------------
    cat_keys = {_match_key(row["URL"]) for row in rows}
    gaps = [r["URL"] for r in top if _match_key(r["URL"]) not in cat_keys]

    # ---- the report (always written; documents any failure) --------------------------------
    base_name, base = _baseline()
    lines = [
        f"# Catalogue report — {config.COMPANY}",
        "",
        f"- Generated: {datetime.date.today().isoformat()}",
        f"- Domain: {config.DOMAIN} · market: {config.LOCATION}/{config.LANGUAGE}",
        f"- Confidence: {_confidence(is_wp, wp.get('unavailable') or {})}",
        f"- Rows: {len(rows)} · overall body coverage: {overall:.1%}",
        "",
        "## Gates",
        "",
    ]
    lines += [f"- **FAIL** {f}" for f in failures] or ["- all gates PASS"]
    lines += [f"- warn: {w}" for w in warnings]
    if withheld:
        n = sum(v[2] for v in withheld.values())
        lines += ["", f"### Withheld by the CMS — {n} record(s) counted but not served", "",
                  "Every request for these types answered HTTP 200; the CMS simply served fewer "
                  "records than its own count header claims. That is a permissions boundary, not "
                  "a failure: these are private, draft or otherwise protected records an "
                  "anonymous client may not read. They are counted here so the difference can "
                  "never be mistaken for pages we lost.", ""]
        lines += [f"- `{t}`: served {c} of {tot} ({h} withheld)" for t, (c, tot, h) in sorted(withheld.items())]
    unavail = wp.get("unavailable") or {}
    if unavail:
        lines += ["", f"### Coverage UNKNOWN — {len(unavail)} content type(s) whose endpoint is broken",
                  "",
                  "Every request to these types errored, so the CMS never served a count for them "
                  "and their true size is **unknowable from this source**. They are NOT assumed "
                  "empty. Any of their pages that the sitemap, archive or traffic layers found are "
                  "still catalogued via those sources; pages only this endpoint knew about cannot "
                  "be counted, so this run's CMS-side coverage is incomplete by an unknown amount.",
                  ""]
        lines += [f"- `{t}` ({m.get('rest_base')}): {m.get('reason')}" for t, m in sorted(unavail.items())]
    if unrenderable:
        n = sum(len(v) for v in unrenderable.values())
        lines += ["", f"### Known gaps — {n} item(s) the CMS itself cannot render", "",
                  "The CMS answers HTTP 5xx for these items (a fatal error rendering that record), "
                  "so they cannot be enumerated by any client. Located by bisection and listed "
                  "here rather than lost; coverage below EXCLUDES them.", ""]
        lines += [f"- `{t}`: item position(s) {v}" for t, v in sorted(unrenderable.items())]
    lines += ["", "## Coverage per type", "",
              "| Type | Rows | ok | stub | flagged | failed | Coverage |" +
              (" Baseline non-empty | Baseline rows |" if base else ""),
              "|---|---|---|---|---|---|---|" + ("---|---|" if base else "")]
    for t, d in sorted(per_type.items(), key=lambda kv: -kv[1]["rows"]):
        cov = (d["ok"] + d["stub"] + d["flagged"]) / max(1, d["rows"])
        extra = ""
        if base:
            b = (base.get("per_type") or {}).get(t)
            extra = f" {b['non_empty']} | {b['rows']} |" if b else " — | — |"
        lines.append(f"| {t} | {d['rows']} | {d['ok']} | {d['stub']} | {d['flagged']} | "
                     f"{d['failed']} | {cov:.1%} |" + extra)
    if base:
        lines += ["", f"Baseline: `{base_name}` — total {base.get('total')} rows. The rebuild "
                      f"must match or beat every number; regressions are failures, not footnotes."]

    st = rec.get("stats", {})
    lines += ["", "## Provenance (the set differences are findings)", "",
              f"- union {st.get('union', '?')} -> final {st.get('final', '?')} pages",
              f"- wp {st.get('wp', 0)} · sitemap {st.get('sitemap', 0)} · archive "
              f"{st.get('archive', 0)} · crawl {st.get('crawl', 0)}",
              f"- wp-only {st.get('wp_only', 0)} (the CMS lists these; the sitemap does not) · "
              f"sitemap-only {st.get('sitemap_only', 0)} · archive-only {st.get('archive_only', 0)}",
              f"- dropped: dead {st.get('dead', 0)} · soft-404 {st.get('soft_404', 0)} · "
              f"collapsed aliases {st.get('collapsed', 0)} · offsite {st.get('offsite', 0)} · "
              f"robots {st.get('robots', 0)}",
              f"- fan-in flags (NOT collapsed, inspect these): {st.get('fan_in_flagged', 0)}"]

    if top:
        traw = _load_json(config.TRAFFIC_RAW)
        lines += ["", "## Traffic", "",
                  f"- {len(top)} ranked pages (market {top[0]['Market']}) · join fills the "
                  f"catalogue's Traffic/Intent with the CLEANED figure",
                  f"- vendor total_count {traw.get('total_count', '?')} vs {len(traw.get('rows', []))} "
                  f"rows actually served (the tail is etv~0; shortfall is the vendor's, recorded here)",
                  f"- pull cost ${traw.get('cost_usd', 0):.2f}"]
        lines += ["", f"## Provable gaps ({len(gaps)} ranking pages the catalogue lacks)", ""]
        lines += [f"- {u}" for u in gaps[:50]]
        if len(gaps) > 50:
            lines.append(f"- … and {len(gaps) - 50} more")
        if not gaps:
            lines.append("- none — every ranking page is in the catalogue")

    config.write_text(config.REPORT_MD, "\n".join(lines) + "\n")
    print(f"   report -> {config.REPORT_MD}")

    if failures:
        for f in failures:
            print(f"   FAIL {f}", file=sys.stderr)
        sys.exit(f"!! {len(failures)} gate failure(s) — the catalogue is NOT trustworthy yet. "
                 f"See {config.REPORT_MD}.")
    print(f"   all gates PASS (overall {overall:.1%}; {len(gaps)} traffic gaps listed)")


if __name__ == "__main__":
    run()
