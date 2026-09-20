#!/usr/bin/env python3
"""9-field-sources orchestrator + steps — the runnable twin of field-sources.workflow.md.

  COMPANY=<slug> python3 run_field_sources.py [--redo]

Step 1 propose candidate subreddits from the company's niche and persona (LLM — it knows the names)
       -> _work/field-sources/candidates.json
Step 2 CHECK every one against Reddit and keep only the live ones (no LLM — this is counting)
       -> _work/field-sources/candidates.json  (verdict + real counts per candidate)
Step 3 write the reference file (LLM) -> field-sources.md

Step 2 is the reason this engine exists. A subreddit name that does not exist returns zero results in
silence, and that is indistinguishable from "nobody discusses this topic". Checking once, here, removes
the ambiguity for every article that follows.
"""
import argparse, datetime, json, os, re, sys, time, urllib.parse, urllib.request
import config, llm

_PERSONA_FILE = os.path.join(config.BRAND_CTX, "persona.md")


# ---- Reddit access: free first, paid only when the free path is blocked -----------------------------

class _R308(urllib.request.HTTPRedirectHandler):
    def http_error_308(self, req, fp, code, msg, headers):
        return self.http_error_301(req, fp, 301, msg, headers)


_OPENER = urllib.request.build_opener(_R308)
_RESULT = re.compile(r'<div class="[^"]*search-result search-result-link.*?'
                     r'<span class="search-score">([\d,]+) point.*?'
                     r'class="search-comments[^"]*"\s*>([\d,]+) comment', re.S)


def _free_probe(sub):
    """(posts, comments) from old.reddit, or None when it is blocking us.

    A rate-limited old.reddit serves a LOGIN PAGE with HTTP 200. Parsed naively that reads as "no
    results", so the marker is checked explicitly and treated as unknown, never as empty."""
    u = (f"https://old.reddit.com/r/{urllib.parse.quote(sub)}/search?q=" +
         urllib.parse.quote("hiring OR interview OR process") + "&restrict_sr=on&sort=top&t=year")
    try:
        req = urllib.request.Request(u, headers={"User-Agent": config.UA})
        page = _OPENER.open(req, timeout=30).read().decode("utf-8", "ignore")
    except Exception:
        return None
    if "search-result" not in page:
        return None                                   # blocked, private, or genuinely gone: cannot tell
    hits = _RESULT.findall(page)
    return len(hits), sum(int(c.replace(",", "")) for _, c in hits)


def _paid_probe(sub, key):
    u = f"{config.SC_BASE}/subreddit/search?" + urllib.parse.urlencode(
        {"subreddit": sub, "query": "hiring", "sort": "top", "timeframe": "year"})
    try:
        d = json.load(urllib.request.urlopen(
            urllib.request.Request(u, headers={"x-api-key": key}), timeout=40))
    except Exception as e:
        return None, str(e)[:60]
    posts = d.get("posts") or d.get("items") or d.get("data") or []
    if not isinstance(posts, list):
        return None, "unexpected shape"
    return (len(posts), sum(int(p.get("num_comments") or 0) for p in posts)), ""


# ---- Step 1 -----------------------------------------------------------------------------------------

def propose(redo=False):
    p = os.path.join(config.WORK, "candidates.json")
    if os.path.exists(p) and not redo:
        d = json.load(open(p))
        if d.get("candidates"):
            print(f"   reusing {p}")
            return d["candidates"]
    persona = ""
    if os.path.exists(_PERSONA_FILE):
        persona = open(_PERSONA_FILE).read()[:6000]
    r = llm.call_json(llm.load_prompt("propose-subreddits.md")
                      .replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
                      .replace("{{PERSONA}}", persona or "(no persona file)")
                      .replace("{{N}}", str(config.CANDIDATES))) or {}
    cands = [c for c in (r.get("subreddits") or []) if str(c.get("name") or "").strip()]
    for c in cands:
        # NOT lstrip("r/") — that strips any leading 'r' or '/' CHARACTER, so "recruiting" came back
        # as "ecruiting" and the four best subreddits were silently rejected as dead (2026-08-11).
        n = str(c["name"]).strip().strip("/")
        for pre in ("r/", "/r/"):
            if n.lower().startswith(pre):
                n = n[len(pre):]
        c["name"] = n.strip("/")
    config.write_json(p, {"candidates": cands})
    print(f"   {len(cands)} candidates -> {p}")
    return cands


# ---- Step 2 -----------------------------------------------------------------------------------------

def verify(cands, redo=False):
    p = os.path.join(config.WORK, "candidates.json")
    if not redo and all("verdict" in c for c in cands):
        print(f"   already checked")
        return cands
    key = config.sc_key()
    if not key:
        print("   !! no ScrapeCreators key — free path only; a rate limit will look like an empty "
              "subreddit and everything will be rejected")
    used_paid = 0
    for c in cands:
        got = _free_probe(c["name"])
        src = "free"
        if got is None and key:
            got, err = _paid_probe(c["name"], key)
            src, used_paid = "paid", used_paid + 1
            if got is None:
                c.update(posts=0, comments=0, checked_via="paid-failed", verdict="unknown", why=err)
                print(f"     r/{c['name']:<22} UNKNOWN  ({err})")
                time.sleep(config.THROTTLE); continue
        if got is None:
            c.update(posts=0, comments=0, checked_via="unreachable", verdict="unknown",
                     why="free path blocked and no paid key")
            print(f"     r/{c['name']:<22} UNKNOWN  (blocked, no key)")
            time.sleep(config.THROTTLE); continue
        posts, comments = got
        ok = posts >= config.MIN_POSTS and comments >= config.MIN_COMMENTS
        c.update(posts=posts, comments=comments, checked_via=src,
                 verdict="keep" if ok else "drop",
                 why="" if ok else f"only {posts} posts / {comments} comments in a year")
        print(f"     r/{c['name']:<22} {posts:>3} posts {comments:>5} comments  "
              f"{'KEEP' if ok else 'drop'}  [{src}]")
        time.sleep(config.THROTTLE)

    # RANK WITHIN EACH ANGLE, NOT ACROSS ALL OF THEM. Raw comment volume favours big general
    # communities over small exact ones: on the first run r/managers (4,589 comments, management in
    # general) knocked out r/humanresources and r/AskHR (769 and 950, the actual audience). So take the
    # best few from each `covers` group first, then fill any remaining slots by volume.
    keep = sorted([c for c in cands if c["verdict"] == "keep"], key=lambda c: -c["comments"])
    per_group, chosen = {}, []
    for c in keep:                                     # pass 1: guarantee every angle is represented
        g = c.get("covers") or "?"
        if per_group.get(g, 0) < config.PER_ANGLE and len(chosen) < config.MAX_KEEP:
            per_group[g] = per_group.get(g, 0) + 1
            chosen.append(c)
    for c in keep:                                     # pass 2: fill what is left by activity
        if len(chosen) >= config.MAX_KEEP:
            break
        if c not in chosen:
            chosen.append(c)
    for c in keep:
        if c not in chosen:
            c["verdict"], c["why"] = "drop", f"outside the top {config.MAX_KEEP} once every angle was covered"
    config.write_json(p, {"candidates": cands})
    n_keep = sum(1 for c in cands if c["verdict"] == "keep")
    print(f"   kept {n_keep} of {len(cands)} (paid checks used: {used_paid}) -> {p}")
    if not n_keep:
        print("   !! NOTHING survived. Either the proposals were wrong or Reddit is blocking every "
              "check — look at candidates.json before trusting this.")
    return cands


# ---- Step 3 -----------------------------------------------------------------------------------------

def write(cands, redo=False):
    if os.path.exists(config.OUT_MD) and not redo:
        print(f"   reusing {config.OUT_MD}")
        return
    def block(rows):
        return "\n".join(f"  {c['name']} — {c.get('who','')} — covers {c.get('covers','?')} — "
                         f"{c.get('posts',0)} posts, {c.get('comments',0)} comments"
                         + (f" — {c['why']}" if c.get("why") else "") for c in rows) or "  (none)"
    kept = [c for c in cands if c["verdict"] == "keep"]
    rej = [c for c in cands if c["verdict"] != "keep"]
    md = llm.call_text(llm.load_prompt("write-field-sources.md")
                       .replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
                       .replace("{{SOURCES}}", open(config.SOURCES_MD).read())
                       .replace("{{KEPT}}", block(kept)).replace("{{REJECTED}}", block(rej))
                       .replace("{{TODAY}}", datetime.date.today().isoformat()))
    md = re.sub(r"^```[a-z]*\n|\n```$", "", md.strip())
    config.write_text(config.OUT_MD, md)
    # VERIFY, DON'T TRUST (C3): every kept subreddit must appear, and no rejected one may.
    missing = [c["name"] for c in kept if c["name"] not in md]
    leaked = [c["name"] for c in rej if re.search(rf"\|\s*{re.escape(c['name'])}\s*\|", md)]
    print(f"   -> {config.OUT_MD} ({len(md.split())} words, {len(kept)} subreddits)")
    if missing:
        print(f"   !! kept but MISSING from the file: {missing}")
    if leaked:
        print(f"   !! rejected but listed in the table: {leaked}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--redo-write", action="store_true", help="re-run step 3 only")
    a = ap.parse_args()
    print(f"company: {config.COMPANY} ({config.BRAND})")
    print("== Step 1: propose candidate subreddits ==")
    cands = propose(redo=a.redo)
    print("== Step 2: check every one against Reddit ==")
    cands = verify(cands, redo=a.redo)
    print("== Step 3: write the reference file ==")
    write(cands, redo=a.redo or a.redo_write)
    print(f"== WRITTEN IN PLACE: field-sources.md — review with `git diff` ==")


if __name__ == "__main__":
    main()
