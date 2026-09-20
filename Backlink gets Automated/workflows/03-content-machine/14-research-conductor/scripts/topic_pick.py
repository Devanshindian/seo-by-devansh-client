#!/usr/bin/env python3
"""Step 0 — the topic chooser + the queue (research-log.csv). Pure bookkeeping; no research here.

The queue is the single source of truth for STATUS; the clubbed CSV stays the source of truth for idea DATA.
Pick order: next unfinished row in the queue — 'pending', or 'in_progress' RECLAIMED (a prior run started it but
never finished, so it's retried, not orphaned). Spokes were inserted right after their hub → depth-first per
cluster. If the queue has nothing unfinished, pull the next eligible idea from clubbed-ideas.csv and enqueue it.

Reads/writes: config.LOG_CSV. Reads: config.CLUBBED_CSV.
"""
import os, csv, io, re, datetime
import config

FIELDS = ["slug", "asset", "angle", "source", "research_status", "write_status", "run_dir",
          "attempts", "created", "updated",
          # write-phase signals carried from the clubbed idea (2026-07-22):
          "format",          # the idea's Format (shape) — for the write phase's format handling
          "target_words",    # clubbed '# words' = median length of the pages that rank (a guide band, not a floor)
          "reuse_verdict",   # Brand new / Build from parts / Improve existing
          "chosen_links",    # for 'Improve existing': the existing page(s) to upgrade
          "tool_build",      # 'yes' when the idea needs a real build (a tool) — never auto-written
          "tool_reason",     # the one-line reason (from Tool escalation)
          "cannibalization",     # the existing ranking keyword we'd compete with (flag only — we still build)
          "cannibalization_url", # the existing page that already ranks for it
          "remarks"]             # free-text note for terminal outcomes (e.g. 'skipped: no keyword demand')


def _today():
    return datetime.date.today().isoformat()


def slugify(title):
    """Short kebab nickname from the (unique) title — the natural head before any colon, first few
    meaningful words, capped. E.g. 'Recruiting Metrics Benchmark Report: ...' -> 'recruiting-metrics-benchmark-report'."""
    head = title.split(":", 1)[0]           # many asset titles are 'Short Title: long description'
    words = re.sub(r"[^a-z0-9\s-]", " ", head.lower()).split()
    stop = {"the", "a", "an", "of", "for", "to", "and", "by", "in", "on", "with", "your", "how", "what"}
    kept, out = 0, []
    for w in words:
        if w in stop and out:
            continue
        out.append(w); kept += 1
        if kept >= config.SLUG_MAX_WORDS or len("-".join(out)) >= config.SLUG_MAX_LEN:
            break
    slug = "-".join(out)[:config.SLUG_MAX_LEN].strip("-")
    return slug or "topic"


def read_queue():
    if not os.path.exists(config.LOG_CSV):
        return []
    with open(config.LOG_CSV, newline="") as f:
        return list(csv.DictReader(f))


def write_queue(rows):
    # Atomic write (convention C5): the queue is the single source of truth for status, so a crash mid-write
    # must NOT truncate it (a corrupt CSV loses the state of every topic). Build the text in memory, then route
    # through config.write_text (temp file in the same dir -> os.replace over the target).
    os.makedirs(os.path.dirname(config.LOG_CSV), exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in FIELDS})
    config.write_text(config.LOG_CSV, buf.getvalue())


def _unique_slug(slug, rows):
    existing = {r["slug"] for r in rows}
    if slug not in existing:
        return slug
    n = 2
    while f"{slug}-{n}" in existing:
        n += 1
    return f"{slug}-{n}"


def _clubbed_meta(row):
    """The write-phase signals we carry from a clubbed idea row (the new columns)."""
    return {"asset": (row.get("Asset") or "").strip(),
            "angle": (row.get("Distinct angle") or "").strip(), "source": "clubbed-hub",
            "format": (row.get("Format") or "").strip(),
            "target_words": (row.get("# words") or "").strip(),
            "reuse_verdict": (row.get("Reuse verdict") or "").strip(),
            "chosen_links": (row.get("Chosen links") or "").strip()}


def _next_from_clubbed(rows):
    """Enqueue TOOL ideas as terminal 'tool-build' markers (never auto-written — Change 1), then return the
    next WRITABLE idea, in priority order: PRIMARY verdicts first, 'Improve existing' LAST (Change 3).
    Carries the write-phase signals (format / target_words / reuse_verdict / chosen_links)."""
    queued = {r["asset"].strip() for r in rows}
    with open(config.CLUBBED_CSV, newline="") as f:
        clubbed = [r for r in csv.DictReader(f)
                   if (r.get("Asset") or "").strip() and (r.get("Asset") or "").strip() not in queued]

    # 1. TOOL ideas: needs a real build, not a write. Drop a terminal marker row so a human can see it, and
    #    it is never picked for writing. (research_status 'tool-build' is not pending/in_progress -> skipped.)
    for row in clubbed:
        te = (row.get("Tool escalation") or "").strip()
        if not te:
            continue
        asset = (row.get("Asset") or "").strip()
        rows.append({"slug": _unique_slug(slugify(asset), rows), "asset": asset,
                     "angle": (row.get("Distinct angle") or "").strip(), "source": "clubbed-hub",
                     "research_status": "tool-build", "write_status": "n/a", "run_dir": "", "attempts": "0",
                     "created": _today(), "updated": _today(), "format": (row.get("Format") or "").strip(),
                     "reuse_verdict": (row.get("Reuse verdict") or "").strip(), "tool_build": "yes", "tool_reason": te})
        queued.add(asset)

    # 2. next WRITABLE idea — primary verdicts first, 'Improve existing' pushed to the bottom (Change 3)
    def _find(verdicts):
        for row in clubbed:
            asset = (row.get("Asset") or "").strip()
            if asset in queued or (row.get("Tool escalation") or "").strip():
                continue
            if (row.get("Reuse verdict") or "").strip() in verdicts:
                return _clubbed_meta(row)
        return None
    return _find(config.REUSE_PRIMARY) or _find(config.REUSE_LAST)


def pick_next(force_asset=None):
    """Return the topic dict to research this run (and mark it in_progress). None if nothing left."""
    rows = read_queue()

    if force_asset:  # explicit topic (testing / manual) — reuse its queue row or make one
        match = next((r for r in rows if force_asset.lower() in r["asset"].lower()), None)
        if not match:
            # find it in clubbed to grab the real title + angle
            with open(config.CLUBBED_CSV, newline="") as f:
                crow = next((c for c in csv.DictReader(f) if force_asset.lower() in (c.get("Asset") or "").lower()), None)
            if not crow:
                raise SystemExit(f"'{force_asset}' not in the queue or clubbed CSV")
            match = {"slug": _unique_slug(slugify(crow["Asset"]), rows), "asset": crow["Asset"].strip(),
                     "angle": (crow.get("Distinct angle") or "").strip(), "source": "clubbed-hub",
                     "research_status": "pending", "write_status": "pending", "run_dir": "",
                     "created": _today(), "updated": _today(),
                     "format": (crow.get("Format") or "").strip(), "target_words": (crow.get("# words") or "").strip(),
                     "reuse_verdict": (crow.get("Reuse verdict") or "").strip(),
                     "chosen_links": (crow.get("Chosen links") or "").strip()}
            rows.append(match)
        chosen = match
    else:
        # pick the next unfinished row. "in_progress" is RECLAIMED: a prior run started this topic but never
        # reached mark_done (crash / usage-limit / Ctrl-C), so it is retried — not orphaned. Runs are sequential
        # (one topic per run), so an in_progress row is never a concurrently-active one. Resume skips completed
        # steps via each engine's have()-guards, so reclaiming wastes no work.
        # RETRY CAP: a row that has already been attempted MAX_ATTEMPTS times is marked 'failed' (terminal) and
        # skipped, instead of being reclaimed forever — otherwise a deterministically-failing topic blocks the
        # queue and pays for DataForSEO/STORM on every attempt. [A#3 / revamp Phase 0.4]
        chosen = None
        for r in rows:
            if r.get("research_status") not in ("pending", "in_progress"):
                continue                                    # done / failed -> skip
            if int(r.get("attempts") or 0) >= config.MAX_ATTEMPTS:
                r["research_status"] = "failed"; r["updated"] = _today()
                print(f"  !! '{r['slug']}' hit {config.MAX_ATTEMPTS} attempts -> marked failed (dead-lettered)")
                continue
            chosen = r
            break
        if chosen is None:  # queue exhausted (or all remaining failed) → pull from clubbed
            nxt = _next_from_clubbed(rows)
            if not nxt:
                write_queue(rows)                           # persist any rows just marked 'failed'
                return None
            chosen = {"slug": _unique_slug(slugify(nxt["asset"]), rows), "asset": nxt["asset"],
                      "angle": nxt["angle"], "source": nxt["source"],
                      "research_status": "pending", "write_status": "pending", "run_dir": "",
                      "attempts": "0", "created": _today(), "updated": _today(),
                      "format": nxt.get("format", ""), "target_words": nxt.get("target_words", ""),
                      "reuse_verdict": nxt.get("reuse_verdict", ""), "chosen_links": nxt.get("chosen_links", "")}
            rows.append(chosen)

    chosen["attempts"] = str(int(chosen.get("attempts") or 0) + 1)   # count this attempt
    chosen["research_status"] = "in_progress"
    chosen["run_dir"] = os.path.join(config.DFS_OUT, chosen["slug"])
    chosen["updated"] = _today()
    write_queue(rows)
    return chosen


def mark_done(slug):
    rows = read_queue()
    for r in rows:
        if r["slug"] == slug:
            r["research_status"] = "done"; r["updated"] = _today()
    write_queue(rows)


def mark_written(slug, status="done"):
    """Close the OTHER half of the loop (2026-08-26).

    research_status has always been maintained. write_status never was — nothing in the codebase
    wrote that column, so every row read 'pending' forever, including four articles that were
    finished and published. The queue could tell you what had been researched and not what had been
    written, which is half a queue.

    status is 'done' or 'failed'. A failed write leaves the row honest — research done, write failed —
    rather than looking like a topic nobody has started.
    """
    rows = read_queue()
    hit = False
    for r in rows:
        if r["slug"] == slug:
            r["write_status"] = status
            r["updated"] = _today()
            hit = True
    if hit:
        write_queue(rows)
    return hit


def set_meta(slug, **fields):
    """Write extra fields onto a queue row (e.g. the cannibalisation flag found mid-run). Persists immediately."""
    rows = read_queue()
    for r in rows:
        if r["slug"] == slug:
            for k, v in fields.items():
                r[k] = v
            r["updated"] = _today()
    write_queue(rows)


# ---------------------------------------------------------------- the spokes sheet
# Its own file, its own columns. `parent` and `keyword` are the two the queue never had: a spoke only
# means anything next to the hub it hangs off, and the keyword is what it was minted from.
SPOKE_FIELDS = ["slug", "parent", "keyword", "asset", "angle",
                "research_status", "write_status", "run_dir", "attempts",
                "created", "updated", "reuse_verdict", "chosen_links", "remarks"]


def read_spokes():
    if not os.path.exists(config.SPOKES_CSV):
        return []
    with open(config.SPOKES_CSV, newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def write_spokes(rows):
    os.makedirs(os.path.dirname(config.SPOKES_CSV), exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=SPOKE_FIELDS, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in SPOKE_FIELDS})
    tmp = config.SPOKES_CSV + ".tmp"
    with open(tmp, "w", newline="") as f:
        f.write(buf.getvalue())
    os.replace(tmp, config.SPOKES_CSV)          # atomic: the file is old-complete or new-complete, never half


def insert_spokes(hub_slug, hub_asset, hub_angle, spokes):
    """Record this hub's spokes in spokes.csv. spokes = list of {keyword, why}. Each bare keyword is first
    MINTED into a real idea (title + angle) grounded in the pillar (spoke_idea.accept, which also re-angles
    off duplicates), so a spoke carries the raw material a normal idea has. Slug = spoke-N-<kw>.

    THEY NO LONGER GO INTO THE QUEUE (2026-08-27, Devansh). They used to be inserted directly after the hub
    row in research-log.csv, which meant a hub finishing pushed its spokes ahead of every real idea — not a
    decision anyone made, just where the code put them. The queue is now only ideas from clubbed-ideas.csv.
    A spoke is recorded here against its parent and run when a person decides to run it.

    Dedup is checked against BOTH sheets: a spoke must not repeat another spoke, and must not repeat a real
    idea already queued.
    """
    import spoke_idea
    rows = read_spokes()
    queued = {r["asset"].strip().lower() for r in read_queue()}
    existing = {r["asset"].strip().lower() for r in rows} | queued
    new = []
    for n, sp in enumerate(spokes, 1):
        kw = ((sp.get("keyword") if isinstance(sp, dict) else sp) or "").strip()
        why = ((sp.get("why") if isinstance(sp, dict) else "") or "").strip()
        if not kw:
            continue
        idea = spoke_idea.accept(kw, hub_asset, hub_angle, signals=why)      # bare keyword -> real title + angle
        title = idea.get("title") or kw
        if title.strip().lower() in existing:
            continue
        existing.add(title.strip().lower())
        new.append({"slug": _unique_slug(f"spoke-{n}-{slugify(kw)}", rows + new),
                    "parent": hub_slug, "keyword": kw, "asset": title,
                    "angle": (idea.get("angle") or why),
                    "research_status": "pending", "write_status": "pending",
                    "run_dir": "", "attempts": "0", "created": _today(), "updated": _today(),
                    "reuse_verdict": idea.get("verdict", ""),      # the real semantic reuse verdict for the spoke
                    "chosen_links": idea.get("chosen", ""), "remarks": ""})
    write_spokes(rows + new)
    return [r["asset"] for r in new]


if __name__ == "__main__":
    import sys
    t = pick_next(sys.argv[1] if len(sys.argv) > 1 else None)
    print("picked:", t["slug"], "|", t["asset"][:60] if t else None) if t else print("nothing to do")
