#!/usr/bin/env python3
"""The API-usage page — what one article actually cost, per step.

Reads:  <repo>/_usage/ledger.jsonl (written by usage_meter.py from three call sites: the DataForSEO
        client, the research-structure LLM caller, and the write-phase LLM caller).
Writes: <slug>/usage-review.html  — this article's spend
        <repo>/_usage/usage-all.html — every article on one page

Pure read-and-render, same as eval_pages: it decides nothing, so it can be rebuilt at any time for any
past run. Numbers are the providers' OWN figures — DataForSEO returns `cost` on every response and
DeepSeek returns a `usage` block on every completion. Nothing here is estimated except the dollar
conversion of DeepSeek tokens, which uses the published per-million rates in usage_meter.py.
"""
import argparse
import os
import sys
from collections import defaultdict

import config
import eval_pages as ep

sys.path.insert(0, config.REPO_ROOT)
try:
    import usage_meter
except Exception:
    usage_meter = None

E = ep.E

# which engine a step belongs to, so the page can answer "what did the writer cost vs the planner"
ENGINE = {
    "build_structure.py": "research", "harvest_storm.py": "research", "cluster.py": "research",
    "name_clusters.py": "research", "score_cards.py": "research", "attach.py": "research",
    "keywords.py": "research", "orphan.py": "research", "faq_order.py": "research",
    "keyword_set.py": "research", "pick_persona.py": "research", "redecide_differentiator.py": "research",
    "filter_sources.py": "research", "competitors.py": "research", "harvest_brief.py": "research",
    "harvest_ownpages.py": "research", "bundle.py": "research", "render.py": "research",
    "gather_inputs.py": "planner", "plan_select.py": "planner", "verify_sources.py": "planner",
    "fmt_router.py": "planner", "freeze.py": "planner",
    "shape.py": "architect", "enrich.py": "architect", "allocate_words.py": "architect",
    "section_keywords.py": "architect", "headings.py": "architect",
    "write_body.py": "writer", "blend.py": "writer", "wrapper.py": "writer",
    "slop_pass.py": "writer", "links_pass.py": "writer", "assemble.py": "writer", "clean.py": "writer",
}

# What each step actually DOES, in one plain line. Shown under its cost row, so a bill is never a list
# of filenames. Add a line here whenever a new step starts making metered calls.
WHAT = {
    # --- research: turning the raw research into fact cards and a bundle ---
    "harvest_storm.py": "Turns the deep-research document into individual fact cards, each with its source.",
    "harvest_brief.py": "Pulls fact cards out of the DataForSEO keyword-and-competitor brief.",
    "harvest_ownpages.py": "Pulls fact cards out of the company's own existing pages.",
    "pick_persona.py": "Decides who this article is written for.",
    "score_cards.py": "Scores every card against the article's angle and drops the off-topic ones.",
    "cluster.py": "Groups thousands of loose cards into coherent topics.",
    "name_clusters.py": "Names each topic group and splits any that grew too big.",
    "redecide_differentiator.py": "Decides which parts are genuinely our own angle, not everyone's.",
    "filter_sources.py": "Removes anything sourced from a competitor.",
    "attach.py": "Attaches each card to the section it belongs under.",
    "competitors.py": "Looks up who else ranks for this topic.",
    "keywords.py": "Buys a target keyword for each section from DataForSEO.",
    "keyword_set.py": "Picks the primary keyword and its variations.",
    "orphan.py": "Finds a home for cards that ended up in no section.",
    "faq_order.py": "Builds the FAQ and puts the sections in reading order.",
    "render.py": "Writes the research blueprint out for a human to read.",
    "bundle.py": "Packs everything into the write-ready research bundle.",
    "build_structure.py": "Runs the whole research-to-blueprint sequence.",
    # --- planner: deciding what goes in ---
    "fmt_router.py": "Decides what kind of article this is (listicle, comparison, how-to...).",
    "gather_inputs.py": "Collects all the research into one file, and drops off-angle questions.",
    "plan_select.py": "Tags every sub-topic and decides which earn a place. The rest are cut.",
    "verify_sources.py": "Checks every number really appears on the page it credits, and hunts the web for a replacement when it does not. Usually the most expensive step in the run.",
    "freeze.py": "Final shape check before the plan is locked.",
    # --- architect: designing the article ---
    "shape.py": "Designs the sections, their order and what each one must deliver.",
    "enrich.py": "Goes to the web for fresh facts where the architect judged a section too thin.",
    "allocate_words.py": "Decides how many words each section gets, by importance.",
    "section_keywords.py": "Decides which sections deserve a search keyword, and researches one for each.",
    "headings.py": "Writes every final heading and the H1, from each section's own evidence.",
    # --- writer: writing it ---
    "write_body.py": "Writes each section of the article. One call per section, run in parallel.",
    "blend.py": "Stitches the separately-written sections into one piece and weaves the keywords in.",
    "wrapper.py": "Writes the intro, the FAQ and the closing.",
    "slop_pass.py": "Strips the tells that make writing read as machine-made.",
    "links_pass.py": "Chooses the internal links, read-more pointers and external sources.",
    "clean.py": "Mechanical scrub of characters and spacing. Pure code, so it costs nothing.",
    "assemble.py": "Builds the finished article and counts the keyword coverage.",
}

ORDER = ["research", "planner", "architect", "writer", "other"]


def _money(x):
    return f"${x:,.2f}" if x >= 0.005 else (f"${x:.4f}" if x else "$0")


def _agg(rows):
    """(totals, per-step, per-engine) from raw ledger rows."""
    tot = {"cost": 0.0, "calls": 0, "ds_cost": 0.0, "ds_calls": 0, "dfs_cost": 0.0, "dfs_calls": 0,
           "in": 0, "out": 0, "cached": 0}
    step = defaultdict(lambda: {"cost": 0.0, "calls": 0, "in": 0, "out": 0, "cached": 0, "kind": set()})
    for r in rows:
        c = float(r.get("cost_usd") or 0.0)
        k = r.get("kind")
        if k == "timing":
            continue
        name = r.get("step") or r.get("script") or "(unknown)"
        tot["cost"] += c
        tot["calls"] += 1
        s = step[name]
        s["cost"] += c
        s["calls"] += 1
        s["kind"].add(k)
        if k == "deepseek":
            tot["ds_cost"] += c
            tot["ds_calls"] += 1
            for a, b in (("in", "prompt_tokens"), ("out", "completion_tokens"), ("cached", "cached_tokens")):
                tot[a] += int(r.get(b) or 0)
                s[a] += int(r.get(b) or 0)
        elif k == "dataforseo":
            tot["dfs_cost"] += c
            tot["dfs_calls"] += 1
    eng = defaultdict(lambda: {"cost": 0.0, "calls": 0})
    for name, s in step.items():
        e = ENGINE.get(name, "other")
        eng[e]["cost"] += s["cost"]
        eng[e]["calls"] += s["calls"]
    return tot, step, eng



def _dur(sec):
    sec = float(sec or 0)
    if sec < 60:
        return f"{sec:.0f}s"
    if sec < 3600:
        return f"{int(sec // 60)}m {int(sec % 60):02d}s"
    return f"{int(sec // 3600)}h {int((sec % 3600) // 60):02d}m"


def _timing(rows):
    """How long each step took, and the article end to end. Timing rows are written by the
    orchestrators (usage_meter.record_step), so they cover steps that spend nothing as well."""
    t = [r for r in rows if r.get("kind") == "timing"]
    if not t:
        return ('<h2>Time</h2><p class="note">No timings on file for this article. The orchestrators record '
                'one row per step; a run that finished before timing was switched on will not appear here.</p>')
    by_phase, total = defaultdict(float), 0.0
    per = []
    for r in t:
        sec = float(r.get("seconds") or 0)
        total += sec
        by_phase[r.get("phase") or "other"] += sec
        per.append((r.get("step") or "?", r.get("phase") or "", sec))
    mx = max((s for _, _, s in per), default=1) or 1
    prows = "".join(
        f'<div class="row"><div class="t">{E(n)}<span class="chip">{_dur(s)}</span>'
        f'<span class="chip">{E(ph)}</span></div>'
        + (f'<div class="reason">{E(WHAT[n])}</div>' if n in WHAT else "")
        + f'<div class="bar"><i style="width:{max(2, round(100 * s / mx))}%"></i></div></div>'
        for n, ph, s in sorted(per, key=lambda x: -x[2]))
    ph = "".join(
        f'<div class="row"><div class="t">{E(k)}<span class="chip">{_dur(by_phase[k])}</span>'
        f'<span class="chip">{by_phase[k] / total * 100:.0f}% of the run</span></div></div>'
        for k in ORDER if k in by_phase)
    return ('<h2>Time — end to end</h2>'
            + f'<p class="note">This article took <b>{_dur(total)}</b> of machine time, start to finish. '
              'Steps run one after another, so these add up.</p>'
            + '<div class="panel">' + ph + "</div>"
            + '<h2>Slowest steps first</h2>'
            + '<p class="note">Where the wall-clock time actually went. The dearest step and the slowest step '
              'are often not the same one.</p>'
            + '<div class="panel">' + prows + "</div>")


def _body(rows, title_note):
    tot, step, eng = _agg(rows)
    timing = _timing(rows)
    if not rows:
        return ('<div class="panel"><p class="q">No metered calls on file yet. The meter records every '
                'DeepSeek completion and every DataForSEO call from the moment it was switched on — a run '
                'that finished earlier will not appear here.</p></div>')

    hit = (tot["cached"] / tot["in"] * 100) if tot["in"] else 0
    nums = ep._nums([
        ("total spend", _money(tot["cost"])),
        ("DeepSeek", _money(tot["ds_cost"])),
        ("DataForSEO", _money(tot["dfs_cost"])),
        ("AI calls", f'{tot["ds_calls"]:,}'),
        ("DataForSEO calls", f'{tot["dfs_calls"]:,}'),
        ("tokens in / out", f'{tot["in"]:,} / {tot["out"]:,}'),
        ("prompt cache hits", f"{hit:.0f}%"),
    ])

    # per-engine
    mx_e = max((v["cost"] for v in eng.values()), default=1) or 1
    erows = "".join(
        f'<div class="row"><div class="t">{E(name)}<span class="chip">{eng[name]["calls"]:,} call(s)</span>'
        f'<span class="chip">{_money(eng[name]["cost"])}</span></div>'
        f'<div class="bar"><i style="width:{max(2, round(100 * eng[name]["cost"] / mx_e))}%"></i></div></div>'
        for name in ORDER if name in eng)

    # per-step, dearest first — the question this page exists to answer
    mx_s = max((v["cost"] for v in step.values()), default=1) or 1
    srows = []
    for name, s in sorted(step.items(), key=lambda kv: -kv[1]["cost"]):
        kinds = "+".join(sorted(x for x in s["kind"] if x))
        tokens = (f' · {s["in"]:,} in / {s["out"]:,} out'
                  + (f' · {s["cached"]:,} cached' if s["cached"] else "")) if s["in"] or s["out"] else ""
        srows.append(
            f'<div class="row"><div class="t">{E(name)}'
            f'<span class="chip">{_money(s["cost"])}</span>'
            f'<span class="chip">{ENGINE.get(name, "other")}</span></div>'
            + (f'<div class="reason">{E(WHAT[name])}</div>' if name in WHAT else "")
            + f'<div class="m">{s["calls"]:,} {E(kinds)} call(s){tokens}</div>'
            f'<div class="bar"><i style="width:{max(2, round(100 * s["cost"] / mx_s))}%"></i></div></div>')

    return (nums
            + f'<p class="note">{title_note}</p>'
            + '<h2>Where the money went, by engine</h2>'
            + '<p class="note">research = building the cards and the bundle · planner = choosing and '
              'source-checking · architect = designing and enriching · writer = writing and polishing.</p>'
            + '<div class="panel">' + (erows or '<p class="q">nothing</p>') + "</div>"
            + '<h2>Every step, dearest first</h2>'
            + '<p class="note">The step name is the script that made the call. Read the top row first: that '
              'is the one worth optimising, and everything below it is noise by comparison.</p>'
            + '<div class="panel">' + "".join(srows) + "</div>"
            + '<h2>How these numbers are produced</h2><div class="panel">'
              '<div class="row"><div class="t">DataForSEO</div><div class="m">The exact <code>cost</code> '
              'DataForSEO returns on every response. Not estimated.</div></div>'
              '<div class="row"><div class="t">DeepSeek</div><div class="m">The exact token counts DeepSeek '
              'returns on every completion, priced at the published per-million rates. Cached prompt tokens '
              'are billed at a tenth of fresh ones, so a high cache-hit rate is money saved.</div></div>'
              '<div class="row"><div class="t">Claude / Codex</div><div class="m">Not metered — they run on '
              'your subscription through the local CLI, so there is no per-call charge to record.</div></div>'
            + "</div>"
            + timing)


def build(slug):
    rows = usage_meter.read(slug) if usage_meter else []
    body = ep._nav("", base="") + _body(rows, f"Every metered API call made while building <b>{E(slug)}</b>.")
    out = os.path.join(config.out_dir(slug), "time-and-usage.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)     # the page can be built before the run creates the dir
    config.write_text(out, ep._page("Time and API usage", f"{slug} — how long it took and what it cost", body))
    return out


def build_all():
    rows = usage_meter.read() if usage_meter else []
    by_slug = defaultdict(list)
    for r in rows:
        by_slug[r.get("slug") or "(no slug)"].append(r)
    tbl = ""
    if by_slug:
        tbl = ('<h2>Per article</h2><div class="panel">' + "".join(
            f'<div class="row"><div class="t">{E(s)}<span class="chip">'
            f'{_money(sum(float(x.get("cost_usd") or 0) for x in rs))}</span></div>'
            f'<div class="m">{len(rs):,} metered call(s)</div></div>'
            for s, rs in sorted(by_slug.items(), key=lambda kv: -sum(float(x.get("cost_usd") or 0) for x in kv[1])))
            + "</div>")
    body = _body(rows, "Every metered API call across <b>all</b> articles.") + tbl
    out = os.path.join(usage_meter.LEDGER_DIR, "time-and-usage-all.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    config.write_text(out, ep._page("Time and API usage — everything", "all articles", body))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Render the API-usage page(s) from the ledger.")
    ap.add_argument("--slug", default=None)
    a = ap.parse_args()
    if a.slug:
        print("->", build(a.slug))
    print("->", build_all())
