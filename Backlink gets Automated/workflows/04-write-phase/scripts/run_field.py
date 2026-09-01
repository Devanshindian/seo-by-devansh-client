#!/usr/bin/env python3
"""FIELD VOICES — what practitioners actually say about one article's subject.

  COMPANY=<slug> python3 run_field.py --slug <slug> [--redo]

Reads:  architect/structure.json (the sections and their jobs) + the article row
        <brand-context>/field-sources.md (the checked subreddit list)
Writes: out/<slug>/voices-from-the-field.md   — and nothing else, anywhere

Step 1 PLAN    the article decides the queries, for all three sources        (LLM)
Step 2 SEARCH  titles only, no discussions opened yet
Step 3 PROBE   per source: read these / requery / stop. Up to N rounds       (LLM)
Step 4 HARVEST download the comment trees for the shortlisted threads only
Step 5 WRITE   filter everything against the article and write one file      (LLM)

Step 3 is the point. Searching is cheap and opening discussions is not, so the run looks at titles
before it spends anything, and is allowed to stop early. An earlier build scraped 93 discussions on a
subject nobody argues about and produced 192 words.
"""
import argparse, json, os, re, sys
import config, llm, article_ctx, fmt_router
import field_reddit, field_blind, field_linkedin

SOURCES = {"reddit": field_reddit, "blind": field_blind, "linkedin": field_linkedin}


def _fill(name, **kw):
    t = open(os.path.join(config.PROMPTS, name)).read()
    for k, v in kw.items():
        t = t.replace("{{%s}}" % k, str(v))
    return t


def _article(slug):
    st = json.load(open(config.artifact(slug, "structure.json")))
    row = fmt_router._queue_row(slug)
    actx = article_ctx.article_context(slug)
    secs = "\n".join(f"  {i}. {s.get('headline','')}\n     JOB: {s.get('job') or '(none)'}"
                     for i, s in enumerate(st["sections"], 1))
    return {"TITLE": (row.get("asset") or "").strip() or "(none)",
            "ANGLE": (row.get("angle") or "").strip() or "(none)",
            "SPINE": article_ctx.or_na(actx, "spine"),
            "PERSONA": article_ctx.persona(slug), "SECTIONS": secs}


def _allowed_subs():
    """Only subreddits the brand-context step checked and kept. A name outside this list is dropped."""
    if not os.path.exists(config.FIELD_SOURCES_MD):
        return set(), ""
    text = open(config.FIELD_SOURCES_MD).read()
    subs = set()
    for line in text.splitlines():
        m = re.match(r"^\|\s*([A-Za-z0-9_]+)\s*\|", line.strip())
        if m and m.group(1).lower() not in ("subreddit",):
            subs.add(m.group(1))
    return subs, text


def _sub(name):
    """"r/recruiting", "/r/recruiting" and "recruiting" are the same subreddit."""
    n = str(name or "").strip().strip("/")
    for pre in ("r/", "/r/"):
        if n.lower().startswith(pre):
            n = n[len(pre):]
    return n.strip("/")


def _run_queries(plan, allowed, seen, log):
    """Search every source for the queries it was given. Titles only."""
    found = []
    for name, mod in SOURCES.items():
        for item in ((plan.get(name) or {}).get("queries") or []):
            q = str(item.get("q") or "").strip()
            if not q:
                continue
            opts = {}
            if "subreddits" in getattr(mod, "NEEDS", ()):
                # The model writes "r/recruiting" as often as "recruiting". Normalise before the
                # check, or the guard silently drops every subreddit it was given.
                named = [_sub(s) for s in (item.get("subreddits") or [])]
                subs = [s for s in named if s in allowed]
                dropped = [s for s in named if s not in allowed]
                if dropped:
                    log.append(f'dropped unchecked subreddit(s) {dropped} on query "{q}"')
                    print(f'      !! not in the checked list, dropped: {dropped}')
                if not subs:
                    continue
                opts["subreddits"] = subs
            try:
                rows = mod.search(q, **opts)
            except Exception as e:
                log.append(f"{name} search failed on \"{q}\": {e}")
                print(f"      !! {name} '{q}': {str(e)[:70]}")
                continue
            new = 0
            for r in rows:
                if not r.get("url") or r["url"] in seen:
                    continue
                seen.add(r["url"])
                r["query"], r["serves"] = q, item.get("serves", "")
                found.append(r); new += 1
            print(f'      [{name}] "{q}" -> {len(rows)} results, {new} new')
    return found


def run(slug, redo=False):
    # NOT bundle_dir(): that is the research bundle under 03-content-machine. This file belongs
    # beside the article, where the writer looks for it.
    outp = os.path.normpath(os.path.join(
        os.path.dirname(config.artifact(slug, "structure.json")), "..", "voices-from-the-field.md"))
    work = os.path.join(config.architect_work_dir(slug), "field")
    os.makedirs(work, exist_ok=True)
    if os.path.exists(outp) and not redo:
        print(f"  reusing {outp}")
        return outp

    a = _article(slug)
    allowed, sources_text = _allowed_subs()
    if not allowed:
        print("  !! no checked subreddit list — run 01-brand-context/9-field-sources first")
    print(f"  {a['TITLE'][:74]}")
    print(f"  {len(allowed)} checked subreddits available")

    print("== Step 1: plan the searches from the article ==")
    catalogue = (open(config.FIELD_CATALOGUE).read()
                 if os.path.exists(config.FIELD_CATALOGUE) else "(catalogue missing)")
    plan = llm.call_json(_fill("field-plan.md", **a, SOURCES=catalogue,
                               FIELD_SOURCES=sources_text or "(none)")) or {}
    for name in SOURCES:
        for q in ((plan.get(name) or {}).get("queries") or []):
            print(f'     [{name}] "{q.get("q")}" -> serves {q.get("serves")}'
                  + (f' in {q.get("subreddits")}' if q.get("subreddits") else ""))

    # ---- Steps 2 + 3: search titles, probe, maybe requery -------------------------------------------
    seen, pool, shortlist, log = set(), {}, [], []
    live = dict(plan)
    probes = []
    for rnd in range(1, config.FIELD_PROBE_ROUNDS + 1):
        print(f"== Step 2/3: round {rnd} of {config.FIELD_PROBE_ROUNDS} ==")
        found = _run_queries(live, allowed, seen, log)
        if not found and rnd > 1:
            print("     nothing new came back"); break
        for r in found:
            pool[len(pool)] = r
        block = "\n".join(
            f'  [{i}] ({r["src"]}) {r["where"][:26]} | {r["comments"]}c {r["score"]}pts | {r["title"][:96]}'
            for i, r in pool.items() if r not in [pool[j] for j in shortlist])
        already = (f"Already shortlisted for reading: {len(shortlist)} discussion(s)."
                   if shortlist else "Nothing shortlisted yet.")
        last = ("THIS IS THE LAST ROUND. `requery` will not be run again, so choose `read` or `stop`."
                if rnd == config.FIELD_PROBE_ROUNDS else "")
        pr = llm.call_json(_fill("field-probe.md", **a, ROUND=rnd,
                                 MAX_ROUNDS=config.FIELD_PROBE_ROUNDS, ALREADY=already,
                                 RESULTS=block or "(nothing)", LAST_ROUND=last)) or {}
        probes.append(pr)
        nxt = {}
        for name in SOURCES:
            d = pr.get(name) or {}
            act = d.get("action", "stop")
            print(f'     [{name}] {act.upper()}: {str(d.get("why",""))[:88]}')
            if act == "read":
                ids = [int(i) for i in (d.get("read") or []) if str(i).isdigit() and int(i) in pool]
                shortlist += [i for i in ids if i not in shortlist]
                print(f"        shortlisted {len(ids)}")
            elif act == "requery" and rnd < config.FIELD_PROBE_ROUNDS:
                nxt[name] = {"queries": d.get("queries") or []}
        if not nxt:
            break
        live = nxt

    shortlist = sorted(shortlist, key=lambda i: -pool[i]["comments"])[:config.FIELD_MAX_READ]
    print(f"== Step 4: harvest {len(shortlist)} discussion(s) ==")
    bundle = []
    for i in shortlist:
        r = pool[i]
        try:
            d = SOURCES[r["src"]].fetch(r)
        except Exception as e:
            log.append(f"fetch failed {r['url']}: {e}"); continue
        cs = sorted(d.get("comments") or [], key=lambda c: -int(c.get("likes") or 0))
        cs = [c for c in cs if len(c.get("text", "")) > 25][:config.FIELD_COMMENTS_PER]
        bundle.append({"src": r["src"], "where": r["where"], "title": r["title"],
                       "engagement": f'{r["score"]}pts {r["comments"]}c', "query": r["query"],
                       "op": (d.get("body") or r.get("preview") or "")[:400], "comments": cs})
        print(f'     [{r["src"]}] {r["where"][:20]:22} {len(cs):>3} comments  {r["title"][:52]}')

    # COUNTS COME FROM CODE, NEVER FROM THE MODEL. An earlier build let the model write the coverage
    # line and it reported 10,200 comments when 85 had been read.
    n_c = sum(len(b["comments"]) for b in bundle)
    per_src = {}
    for b in bundle:
        per_src[b["src"]] = per_src.get(b["src"], 0) + 1
    coverage = (f"{len(bundle)} discussion(s) read and {n_c} comments, from "
                + (", ".join(f"{v} on {k}" for k, v in sorted(per_src.items())) or "nowhere")
                + f". {len(pool)} results were looked at across {len(probes)} search round(s).")
    print(f"     {coverage}")

    print("== Step 5: filter against the article and write ==")
    blocks = []
    for b in bundle:
        lines = [f'### [{b["src"]}] {b["title"]}  ({b["where"]} · {b["engagement"]} · found by: "{b["query"]}")']
        if b["op"]:
            lines.append(f'  OP: {b["op"]}')
        for c in b["comments"]:
            who = f' [{c["who"]}]' if c.get("who") else ""
            lines.append(f'  ({c.get("likes",0)}){who} {c["text"][:config.FIELD_COMMENT_CHARS]}')
        blocks.append("\n".join(lines))
    md = llm.call_text(_fill("field-write.md", **a, COVERAGE=coverage,
                             BUNDLE="\n\n".join(blocks) or "(nothing was read)"))
    md = re.sub(r"^```[a-z]*\n|\n```$", "", md.strip())
    # The prompt bans em dashes and the model uses them anyway. Ask once, then enforce in code.
    n_dash = md.count("\u2014")
    md = re.sub(r"\s*\u2014\s*", ", ", md)
    config.write_text(outp, md)
    config.write_json(os.path.join(work, "field-run.json"),
                      {"plan": plan, "probes": probes, "shortlist": len(shortlist),
                       "pool": len(pool), "coverage": coverage, "log": log})

    over = [h for h in re.findall(r"^## (.+)$", md, re.M) if len(h.split()) > 12]
    print(f"  -> {outp} ({len(md.split())} words, {len(re.findall(r'^## ', md, re.M))} sections)")
    if over:
        print(f"  !! {len(over)} heading(s) over 12 words: {[h[:44] for h in over]}")
    if n_dash:
        print(f"  ·  {n_dash} em dash(es) replaced with commas")
    if log:
        print(f"  !! {len(log)} problem(s) logged -> {work}/field-run.json")
    return outp


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Field voices for one article.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"====================  FIELD VOICES — {a.slug}  ====================")
    run(a.slug, redo=a.redo)
