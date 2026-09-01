#!/usr/bin/env python3
"""Planner Step 3 — VERIFY SOURCES: every citable number in the plan gets a REAL source, or the card dies.

Reads:  planner/_work/article-plan.tagged.json (the selector's plan) + gather/plan-inputs.json (the cards).
Writes: planner/_work/article-plan.verified.json — the SAME plan shape, sources verified
        (freeze.py stamps it into planner/article-plan.json, the Planner's ONE final output).
        gather/plan-inputs.json — corrected source_urls written back into the cards (atomic).
        planner/_work/verify-cards.json  — the AI's "worth verifying?" decisions.
        planner/_work/source-police.json — the full log: kept-ok / FIXED / CUT / unverifiable / search-failed.

The flow (Devansh, 2026-07-28):
  1. CODE finds every used card whose text carries a real number (2+ digit pattern — reliable).
  2. ONE AI pass (batched) picks which of those genuinely NEED verification — years-as-dates, step numbers,
     list counts etc. are excluded. A failed batch = those cards kept unverified (never deleted unjudged).
  3. Per worthy card: fetch its claimed source page (one request at a time per host, with a retry) ->
     an AI judge reads the page and answers whether it supports the claim ABOUT THE SAME SUBJECT.
  4. Wrong or missing -> the HUNT, same shape as the enrichment loop:
       source-queries.md (AI plans queries from gloss+verbatim, so the subject is in the query)
       -> DataForSEO organic search if credits, else the Claude URL-fetch fallback
       -> code downloads the pages -> source-judge.md decides per page -> FIX the card's link.
     Still nothing -> CUT the card from the plan.
  5. Every URL proven wrong is remembered; at the end EVERY used card citing one is re-checked, even
     if it was never "worthy" (a bad page is bad for every card that cites it).
  4. Mercy rules: an unloadable original page (paywall) is kept unverified, not punished; a FAILED search
     (outage) keeps the card + flags it; deletion only follows an affirmative verify-verdict + a failed hunt.
  5. An H3 that loses all its cards dies with them (logged); a section that loses all its H3s dies too.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import config
import llm

WEB_MAX = int(os.environ.get("WRITE_SOURCE_WEB_MAX", "250"))    # cap web hunts per article (unattended safety)
QUERIES_PER_CLAIM = int(os.environ.get("SOURCE_QUERIES_PER_CLAIM", "3"))
PAGES_PER_CLAIM = int(os.environ.get("SOURCE_PAGES_PER_CLAIM", "5"))   # candidate pages judged per claim
PAGE_CHARS = int(os.environ.get("SOURCE_PAGE_CHARS", "8000"))
FETCH_RETRIES = int(os.environ.get("SOURCE_FETCH_RETRIES", "2"))       # a throttled 200 reads as "wrong" -> retry
FETCH_GAP = float(os.environ.get("SOURCE_FETCH_GAP", "1.5"))           # seconds between hits on the SAME host
HUNT_WORKERS = int(os.environ.get("SOURCE_HUNT_WORKERS", "8"))         # parallel fetch+judge on the DataForSEO route
BATCH_WAIT = int(os.environ.get("SOURCE_BATCH_WAIT", "900"))           # max seconds to wait for a queued search batch
BATCH_TRIES = int(os.environ.get("SOURCE_BATCH_TRIES", "3"))           # re-poll a slow batch this many times
                                                                       # (the tasks are already paid for — free)
HUNT_WORKERS_FALLBACK = int(os.environ.get("SOURCE_HUNT_WORKERS_FALLBACK", "1"))   # the Claude CLI route stays serial
BATCH = 80                                                       # cards per verify-worthy AI call
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
_NUM = re.compile(r"\$?\d[\d,]*(?:\.\d+)?\s?%?")


def _has_number(t):
    return any(len(re.sub(r"[^\d]", "", m)) >= 2 for m in _NUM.findall(t or ""))


def _norm(s):
    s = (s or "").lower()
    s = re.sub(r"(\d),(\d)", r"\1\2", s)          # 4,683 -> 4683
    return re.sub(r"[^a-z0-9%]+", " ", s).strip()


def _clause_with_number(verbatim):
    """The smallest self-contained claim to hunt: the clause/sentence that carries the number."""
    parts = re.split(r"(?<=[.;:])\s+|\s[–—-]\s|\|", verbatim or "")
    for p in parts:
        if _NUM.search(p) and len(p.split()) >= 3:
            return p.strip()
    return (verbatim or "").strip()


_HOST_LOCKS, _HOST_LAST, _LOCKS_GUARD = {}, {}, threading.Lock()


def _host_of(url):
    return url.split("/")[2].lower() if "://" in url else url


def _fetch_once(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(3_000_000).decode("utf-8", "ignore")
        raw = re.sub(r"<(script|style)\b.*?</\1>", " ", raw, flags=re.S | re.I)
        return html.unescape(re.sub(r"<[^>]+>", " ", raw))
    except Exception as e:
        return f"__ERR__{type(e).__name__}"


def _fetch(url, timeout=15, retries=None):
    """One request at a time per HOST, with a gap and a retry. Bursting a host makes it serve a wall page
    (a 200 with no content), which used to read as 'the claim is wrong' and delete a correct source."""
    retries = FETCH_RETRIES if retries is None else retries
    host = _host_of(url)
    with _LOCKS_GUARD:
        lock = _HOST_LOCKS.setdefault(host, threading.Lock())
    with lock:
        out = "__ERR__none"
        for attempt in range(retries + 1):
            gap = FETCH_GAP - (time.time() - _HOST_LAST.get(host, 0))
            if gap > 0:
                time.sleep(gap)
            out = _fetch_once(url, timeout)
            _HOST_LAST[host] = time.time()
            if not out.startswith("__ERR__") and len(out.strip()) >= 500:
                return out
            if attempt < retries:
                time.sleep(2.0 * (attempt + 1))
        return out


def _number_present(verbatim, text):
    """Cheap pre-filter: is the card's distinctive number anywhere in the page at all?"""
    vn, tn = _norm(verbatim), _norm(text)
    nums = [n for n in re.findall(r"\d[\d]*%?", vn) if len(re.sub(r"[^\d]", "", n)) >= 2]
    return bool(nums) and any(n in tn for n in nums)


def _page_window(verbatim, page):
    """What the judge reads. Taking the page's first N raw characters shows it the site's nav menu and
    nothing else (a 70k-char journal page yielded 796 chars of real text, all of it 'Search / Log in'),
    so every claim on a heavy site was judged unsupported. Collapse the whitespace first, then send the
    page's opening (title + abstract, which carry the SUBJECT) plus the neighbourhood of each number the
    claim depends on — the text that can actually prove or disprove it."""
    text = " ".join(page.split())
    if len(text) <= PAGE_CHARS:
        return text
    head = text[:PAGE_CHARS // 4]                            # title/abstract: keeps the judge subject-aware
    budget, low = PAGE_CHARS - len(head), text.lower()
    nums = [n for n in re.findall(r"\d[\d,.]*%?", _norm(verbatim)) if len(re.sub(r"[^\d]", "", n)) >= 2]
    words = {w for w in re.findall(r"[a-z]{5,}", verbatim.lower())}

    # A bare number matches junk ("10" inside "2010"), so score every whole-number hit by how much of the
    # claim's own wording sits around it, and keep the richest neighbourhoods.
    hits = []
    for n in dict.fromkeys(nums):
        for m in re.finditer(r"(?<!\d)" + re.escape(n.lower()) + r"(?!\d)", low):
            at = m.start()
            near = low[max(0, at - 700):at + 700]
            hits.append((sum(1 for w in words if w in near), at))
    hits.sort(reverse=True)

    windows, taken, used = [], 0, []
    for _score, at in hits:
        span = min(3000, budget - taken)
        if span < 600:
            break
        s = max(0, at - span // 2)
        if any(abs(s - p) < span for p in used):             # don't spend the budget twice on one passage
            continue
        used.append(s)
        windows.append(text[s:s + span])
        taken += span
    return head + ("\n…\n" + "\n…\n".join(windows) if windows else text[len(head):len(head) + budget])


def _judge(card, url, page):
    """AI verdict: does THIS page support THIS claim, about the same subject? (gloss carries the subject)"""
    if not _number_present(card.get("verbatim", ""), page):
        return False, ""                                    # the number is not even on the page
    try:
        r = llm.call_json(_fill("source-judge.md",
                                GLOSS=card.get("gloss", ""), VERBATIM=card.get("verbatim", ""),
                                URL=url, PAGE=_page_window(card.get("verbatim", ""), page))) or {}
        return bool(r.get("supports")), str(r.get("quote") or "")
    except Exception:
        return False, ""


_DFS_SCRIPTS = os.path.join(config.WORKFLOWS, "03-content-machine", "10-dataforseo", "scripts")


def _fill(name, **kw):
    p = llm.load_prompt(name)
    for k, v in kw.items():
        p = p.replace("{{" + k + "}}", str(v))
    return p


def _dfs(pycode, *args, timeout=120):
    try:
        r = subprocess.run([sys.executable, "-c", pycode, *args], cwd=_DFS_SCRIPTS,
                           capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def _dfs_balance():
    out = _dfs("import dfs; print(dfs.balance())", timeout=60)
    try:
        return float(out)
    except ValueError:
        return None


def _claude_urls(queries, maxn):
    """Fallback when DataForSEO has no credits: one small Claude call returns result URLs. (urls, ok)."""
    if config.NO_CLAUDE:                 # the run is pinned off Claude — never spend its quota here
        return [], False
    try:
        prompt = (llm.load_prompt("search-urls.md")
                  .replace("{{QUERIES}}", "\n".join(f"- {q}" for q in queries))
                  .replace("{{MAX}}", str(maxn)))
        r = subprocess.run([config.CLAUDE_BIN, "-p", "--allowedTools", "WebSearch"],
                           input=prompt, capture_output=True, text=True, timeout=config.CLAUDE_TIMEOUT)
        if r.returncode != 0:
            return [], False
        data = llm._extract_json(r.stdout)
        urls = data.get("urls") if isinstance(data, dict) else data
        return [u for u in (urls or []) if isinstance(u, str)], True
    except Exception:
        return [], False


def _interleave(lists):
    out, i = [], 0
    while any(i < len(L) for L in lists):
        for L in lists:
            if i < len(L):
                out.append(L[i])
        i += 1
    seen, res = set(), []
    for u in out:
        if u not in seen:
            seen.add(u)
            res.append(u)
    return res


def _plan_queries(card):
    """AI plans the search queries for one claim (subject included). [] = planning failed."""
    try:
        q = llm.call_json(_fill("source-queries.md", GLOSS=card.get("gloss", ""),
                                VERBATIM=card.get("verbatim", ""), N=QUERIES_PER_CLAIM)) or {}
        return [str(x).strip() for x in (q.get("queries") or []) if str(x).strip()][:QUERIES_PER_CLAIM]
    except Exception:
        return []


def _judge_candidates(card, cand):
    """Fetch candidate pages in rank order; first page an AI judge confirms wins. (url, quote)."""
    checked = 0
    for u in cand:
        if checked >= PAGES_PER_CLAIM:
            break
        page = _fetch(u)
        if page.startswith("__ERR__"):
            continue
        checked += 1
        ok_page, quote = _judge(card, u, page)
        if ok_page:
            return u, quote
    return None, ""


def _dfs_batch_serp(queries):
    """ALL queries through DataForSEO's standard queue in one go: post in bundles of 100, wait,
    collect with the REGULAR fetch (the advanced fetch silently doubles the price — measured).
    $0.0006/search vs $0.002 live. Returns {query: [urls]}, or None if the batch itself failed."""
    if not queries:
        return {}
    # Three failures, all seen for real on 2026-08-02, all fixed here:
    #  1. tasks_ready returns AT MOST 1000 entries. A run that dies mid-collection leaves its finished
    #     tasks on that list forever; once 1000 pile up, a later run's tasks can never appear and it
    #     polls a permanently full list until it gives up. (4,387 stale tasks had accumulated.)
    #     -> DRAIN the ready list before posting, and collect anything ready whether it is ours or not.
    #  2. The result was printed only at the very end, so a wrapper timeout threw away everything already
    #     collected. One article fetched 945 results and reported total failure.  -> print INCREMENTALLY,
    #     one line per result, so a killed process still hands back what it got.
    #  3. Polling and collecting shared one clock, so fetching hundreds of tasks overran the deadline.
    #     -> the deadline guards POLLING only; collection always finishes, and an ENDGAME fetches any
    #        stragglers directly by id, which does not depend on the ready-list at all.
    code = (
        "import json,sys,time; import dfs, config\n"
        "def drain():\n"                       # fix 1: clear the shelf so our own tasks can be seen
        "    for _ in range(8):\n"
        "        try: r = dfs.call('/v3/serp/google/organic/tasks_ready', None)\n"
        "        except Exception: return\n"
        "        ids = [x.get('id') for x in ((r['tasks'] or [{}])[0].get('result') or []) if x.get('id')]\n"
        "        if not ids: return\n"
        "        for t in ids:\n"
        "            try: dfs.call('/v3/serp/google/organic/task_get/regular/' + t, None)\n"
        "            except Exception: pass\n"
        "drain()\n"
        "qs = json.load(open(sys.argv[1]))\n"
        "id2q = {}\n"
        "for i in range(0, len(qs), 100):\n"
        "    tasks = [{'keyword': q, 'location_name': config.LOCATION, 'language_code': config.LANGUAGE,"
        " 'depth': 10} for q in qs[i:i+100]]\n"
        "    r = dfs.call('/v3/serp/google/organic/task_post', tasks)\n"
        "    for t, q in zip(r['tasks'], qs[i:i+100]):\n"
        "        if t.get('id'): id2q[t['id']] = q\n"
        "def emit(tid, q):\n"                  # fix 2: hand back each result the moment we have it
        "    try:\n"
        "        g = dfs.call('/v3/serp/google/organic/task_get/regular/' + tid, None)\n"
        "        items = ((g['tasks'][0].get('result') or [{}])[0].get('items')) or []\n"
        "    except Exception: return False\n"
        "    urls = [i.get('url') for i in items if i.get('type') == 'organic' and i.get('url')]\n"
        "    print(json.dumps([q, urls]), flush=True)\n"
        "    return True\n"
        "deadline = time.time() + " + str(BATCH_WAIT) + "\n"
        "while id2q and time.time() < deadline:\n"   # fix 3: the deadline guards POLLING only
        "    time.sleep(15)\n"
        "    try: r = dfs.call('/v3/serp/google/organic/tasks_ready', None)\n"
        "    except Exception: continue\n"
        "    ready = [x['id'] for x in ((r['tasks'] or [{}])[0].get('result') or []) if x.get('id') in id2q]\n"
        "    for tid in ready:\n"
        "        if emit(tid, id2q[tid]): id2q.pop(tid, None)\n"
        "for tid in list(id2q):\n"              # ENDGAME: ask for the stragglers by id, no ready-list
        "    if emit(tid, id2q[tid]): id2q.pop(tid, None)\n")
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(queries, f)
        qfile = f.name
    try:
        # DataForSEO's queue can run slower than one BATCH_WAIT window. The old loop only retried on a
        # MALFORMED reply, so a well-formed "{}" — every task posted, none ready yet — was accepted as
        # the final answer. That is exactly how one article had 745 of 745 queries silently abandoned and
        # 428 claims shipped unverified while the report read "0 cut". So: retry while the yield is poor.
        # The tasks are already posted and PAID FOR, so waiting longer costs nothing extra.
        # The child prints ONE json line per result, so a partial run is still worth something: whatever
        # arrived before it was killed is kept. Only queries that genuinely never returned are missing.
        got = {}
        for attempt in range(BATCH_TRIES):
            raw = _dfs(code, qfile, timeout=BATCH_WAIT + 900)
            for line in (raw or "").splitlines():
                line = line.strip()
                if not line.startswith("["):
                    continue
                try:
                    q, urls = json.loads(line)
                    got[q] = urls
                except (json.JSONDecodeError, ValueError, TypeError):
                    continue
            missing = len(queries) - len(got)
            if not missing:
                return got
            if attempt < BATCH_TRIES - 1:
                print(f"    batch: {missing} of {len(queries)} not back yet — waiting again "
                      f"(try {attempt + 2}/{BATCH_TRIES}; already paid for, so this is free)")
        missing = len(queries) - len(got)
        if missing:
            print(f"    !! batch: {missing} of {len(queries)} queries never came back after {BATCH_TRIES} "
                  f"attempts — those claims stay UNVERIFIED (not deleted). Kept {len(got)} that did.")
        return got or None
    finally:
        try: os.remove(qfile)
        except OSError: pass


def _hunt(card, use_dfs):
    """The Claude-fallback hunt (no DFS credits): plan -> Claude web search -> fetch -> judge.
    The DataForSEO route no longer passes through here — it is batched in run()."""
    queries = _plan_queries(card)
    if not queries:
        return None, "", [], False
    cand, ok = _claude_urls(queries, PAGES_PER_CLAIM + 5)
    if not ok:
        return None, "", queries, False
    hit, quote = _judge_candidates(card, cand)
    return hit, quote, queries, True


def _nid(x):
    try:
        return int(str(x).lower().replace("id", "").strip())
    except ValueError:
        return x


def _coverage_verdict(todo, kept_ok, fixed, cut, search_failed):
    """Did the check actually HAPPEN? A run where the search died reports 0 cut and 0 bad urls, which
    reads exactly like a clean article. It is the opposite. One article shipped 428 unverified claims
    behind a row of zeros. So the report states its own completeness, and says so out loud."""
    # Count ONLY the claims that were on the to-check list. fixed/cut also contain cards dragged in by
    # propagation, which were never on it — folding those into the numerator pushed this over 100%
    # (a real run printed 475%) and could let a badly-checked article pass on borrowed credit.
    # COUNT CARDS, NOT ROWS. One card can land in two lists — propagation re-hunts a card that phase 1
    # already passed, so it appears in kept_ok AND fixed. Summing the three lists counted it twice and
    # still pushed the total past 100% (a real run printed 138%), which makes the one number meant to
    # signal trustworthiness look broken. Union the ids instead, so each card is counted exactly once.
    todo_ids = {_nid(c.get("card_id")) for c in todo}
    judged_ids = {_nid(r.get("card_id")) for r in list(kept_ok) + list(fixed) + list(cut)}
    want = len(todo_ids)
    reached = len(todo_ids & judged_ids)
    extra = len(judged_ids - todo_ids)                            # propagation: real work, but not the target
    missed = sum(1 for f in search_failed if f.get("card_id") is not None)
    pct = round(reached / want * 100) if want else 100
    ok = pct >= 80
    verdict = {"claims_to_check": want, "actually_judged": reached, "never_checked": missed,
               "also_judged_via_propagation": extra, "percent_judged": pct, "trustworthy": ok}
    banner = ("  ✓ source check COMPLETE — {r} of {w} claims judged ({p}%)" if ok else
              "  !! SOURCE CHECK INCOMPLETE — only {r} of {w} claims were judged ({p}%). {m} were never\n"
              "     checked, so a low CUT count here means NOT CHECKED, not clean. Do not publish on this.")
    print(banner.format(r=reached, w=want, p=pct, m=missed))
    return verdict


def _worthy_ids(cards):
    """The AI pass: which numeric cards genuinely need a verified source. Batched; a failed batch's cards
    are treated as NOT worthy (kept unverified — never deleted unjudged)."""
    worthy, failed_batches = set(), 0
    batches = [cards[i:i + BATCH] for i in range(0, len(cards), BATCH)]

    def _one(batch):
        block = "\n".join(f"- id{c['card_id']}: {(c.get('verbatim') or c.get('gloss') or '')[:400]}" for c in batch)
        r = llm.call_json(llm.load_prompt("verify-worthy.md").replace("{{CARDS}}", block)) or {}
        return {_nid(x) for x in (r.get("verify") or [])}

    with ThreadPoolExecutor(max_workers=llm.max_workers()) as ex:
        futs = {ex.submit(_one, b): b for b in batches}
        for f in as_completed(futs):
            try:
                worthy |= f.result()
            except Exception:
                failed_batches += 1
    return worthy, failed_batches


def run(slug, redo=False):
    out_path = os.path.join(config.planner_work_dir(slug), "article-plan.verified.json")
    tagged_path = os.path.join(config.planner_work_dir(slug), "article-plan.tagged.json")
    if os.path.exists(out_path) and not redo:
        # resume rule: the draft counts as done only if it was produced AFTER the tagged plan
        if os.path.getmtime(out_path) >= os.path.getmtime(tagged_path):
            print(f"  reusing {out_path} (--redo to reverify)")
            return json.load(open(out_path))
    os.environ["RUN_SLUG"], os.environ["RUN_STEP"] = slug, "verify_sources.py"   # the DataForSEO
    # client runs in a subprocess and cannot see --slug or its caller; these let it bill correctly.
    plan = json.load(open(tagged_path))
    inpp = config.artifact(slug, "plan-inputs.json")
    inp = json.load(open(inpp))

    id2card = {}
    for s in inp["group_b"]["sections_menu"]:
        for c in s.get("evidence", []):
            id2card[_nid(c.get("card_id"))] = c
        for h in s.get("h3", []):
            for c in h.get("evidence", []):
                id2card[_nid(c.get("card_id"))] = c

    used_ids = []
    for sec in plan["sections"]:
        for h in sec["h3s"]:
            for cid in h["card_ids"]:
                cid = _nid(cid)
                if cid not in used_ids:
                    used_ids.append(cid)
    numeric = [id2card[c] for c in used_ids if c in id2card and _has_number(id2card[c].get("verbatim", ""))]
    print(f"  used cards: {len(used_ids)} | with numbers: {len(numeric)}")

    worthy, failed_batches = _worthy_ids(numeric)
    config.write_json(os.path.join(config.planner_work_dir(slug), "verify-cards.json"),
                      {"numeric": [c["card_id"] for c in numeric], "worthy": sorted(worthy),
                       "failed_batches": failed_batches})
    todo = [c for c in numeric if _nid(c.get("card_id")) in worthy]
    print(f"  AI verdict: {len(todo)} of {len(numeric)} numeric cards need verification"
          + (f" ({failed_batches} filter batch(es) failed — those cards kept unverified)" if failed_batches else ""))

    # --- phase 1: fetch-verify the claimed sources, in parallel -------------
    kept_ok, unverifiable, need_hunt = [], [], []

    def _check(c):
        """Try EVERY url the card carries (a good backup should not die with a bad primary)."""
        urls = [u for u in (c.get("source_urls") or []) if u]
        if not urls:
            return c, "no-url", None
        unloadable = 0
        for u in urls:
            page = _fetch(u)
            if page.startswith("__ERR__"):
                unloadable += 1
                continue
            ok, _q = _judge(c, u, page)
            if ok:
                if u != urls[0]:
                    c["source_urls"] = [u] + [x for x in urls if x != u]   # promote the one that worked
                return c, "ok", u
        return c, ("unloadable" if unloadable == len(urls) else "wrong"), None

    with ThreadPoolExecutor(max_workers=8) as ex:
        for f in as_completed([ex.submit(_check, c) for c in todo]):
            c, verdict, _u = f.result()
            if verdict == "ok":
                kept_ok.append(c)
            elif verdict == "unloadable":
                unverifiable.append(c)               # paywalled etc. — kept as-is, not punished
            else:
                need_hunt.append((c, verdict))       # wrong page or no url -> hunt
    print(f"  fetch-verify: ok {len(kept_ok)} | unloadable(kept) {len(unverifiable)} | to hunt {len(need_hunt)}")

    # --- phase 2: hunt the wrong/missing ones ---------------------------------
    bal = _dfs_balance()
    use_dfs = bal is not None and bal >= config.DFS_MIN_CREDITS
    print(f"  hunt route: {'DataForSEO ($%.2f)' % bal if use_dfs else 'Claude web fallback (DFS balance: %s)' % bal}")
    fixed, cut, search_failed, bad_urls = [], [], [], set()
    workers = HUNT_WORKERS if use_dfs else HUNT_WORKERS_FALLBACK

    def _hunt_many(cards):
        """Hunt a whole group. DataForSEO route: plan every query, ONE queued batch (see
        _dfs_batch_serp), then fetch+judge in parallel. Claude fallback: the old serial per-card
        path. Returns one (hit, quote, queries, ok) per card, in order."""
        if not cards:
            return []
        if not use_dfs:
            with ThreadPoolExecutor(max_workers=HUNT_WORKERS_FALLBACK) as ex:
                return [f.result() for f in [ex.submit(_hunt, c, False) for c in cards]]
        with ThreadPoolExecutor(max_workers=llm.max_workers()) as ex:
            plans = list(ex.map(_plan_queries, cards))
        uniq = sorted({q for qs in plans for q in qs})
        print(f"    planned {sum(len(q) for q in plans)} queries ({len(uniq)} unique) -> "
              f"one queued batch (~${len(uniq) * 0.0006:.2f})")
        got = _dfs_batch_serp(uniq)

        def _finish(i):
            c, qs = cards[i], plans[i]
            if not qs:
                return (None, "", [], False)                 # planning failed — never a cut signal
            if got is None or all(q not in got for q in qs):
                return (None, "", qs, False)                 # the SEARCH failed — never a cut signal
            hit, quote = _judge_candidates(c, _interleave([got.get(q, []) for q in qs]))
            return (hit, quote, qs, True)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(_finish, range(len(cards))))

    hunt_now, hunt_capped = need_hunt[:WEB_MAX], need_hunt[WEB_MAX:]
    for c, _w in hunt_capped:
        search_failed.append({"card_id": c["card_id"], "reason": f"web cap {WEB_MAX} reached"})
    print(f"  hunting {len(hunt_now)} card(s)"
          + (" via ONE queued search batch" if use_dfs else f", {workers} at a time")
          + (f" | {len(hunt_capped)} left unchecked (cap {WEB_MAX})" if hunt_capped else ""))
    raw = _hunt_many([c for c, _ in hunt_now])
    hunt_results = []
    for (c, why), (hit, quote, queries, ok) in zip(hunt_now, raw):
        old_u = (c.get("source_urls") or [None])[0]
        if not ok:
            hunt_results.append(({"card_id": c["card_id"], "reason": "search failed (outage?)",
                                  "queries": queries}, None))
        elif hit:
            c["source_urls"] = [hit]
            c["source_fixed"] = True
            hunt_results.append((None, {"card_id": c["card_id"], "claim": (c.get("gloss") or "")[:140],
                                        "old": old_u, "new": hit, "quote": quote[:200],
                                        "queries": queries, "how": "ai-judged"}))
        else:
            hunt_results.append((None, {"card_id": c["card_id"], "claim": (c.get("gloss") or "")[:140],
                                        "old": old_u, "why": why, "queries": queries, "_cut": True}))

    for (c, _why), (failed, res) in zip(hunt_now, hunt_results):
        if failed:
            search_failed.append(failed)
            continue
        if res.get("_cut"):
            res.pop("_cut")
            cut.append(res)
            if res.get("old"):
                bad_urls.add(res["old"])
            print(f"    CUT   c{c['card_id']}: {res['claim'][:60]}")
        else:
            fixed.append(res)
            if res.get("old"):
                bad_urls.add(res["old"])
            print(f"    FIXED c{c['card_id']}: {res['claim'][:60]}")

    # --- phase 2b: PROPAGATE. A url proven wrong is wrong for EVERY card citing it, worthy or not. ---
    unsourced = []
    contaminated = [c for cid in used_ids if (c := id2card.get(cid)) is not None
                    and c not in [x for x, _ in need_hunt]
                    and any(u in bad_urls for u in (c.get("source_urls") or []))]
    propagated = []
    if contaminated:
        # A card with NO number cannot be hunted: there is no distinctive figure to search for, and the
        # judge's whole test is "is this number on this page". Cutting it means a neighbour's bad url
        # silently deletes a fact that was never itself examined. Measured on strategic-interview-questions:
        # 225 of 269 cuts were exactly this — no number, never judged, killed by association.
        # So for a prose card we STRIP the bad url and mark it unsourced. The fact survives; the false
        # source does not. Numeric cards keep the hunt, because for them the hunt actually works.
        prose = [c for c in contaminated if not _has_number(c.get("verbatim", ""))]
        for c in prose:
            keep = [u for u in (c.get("source_urls") or []) if u not in bad_urls]
            c["source_urls"] = keep
            if not keep:
                c["needs_source"] = True
            unsourced.append({"card_id": c["card_id"], "claim": (c.get("gloss") or "")[:140],
                              "bad_url": (c.get("source_urls") or [None])[0] if keep else None,
                              "why": "cited a url proven wrong elsewhere; no number to verify by, so the "
                                     "claim is KEPT and the source stripped rather than deleted unjudged"})
        contaminated = [c for c in contaminated if _has_number(c.get("verbatim", ""))]
        print(f"  propagating {len(bad_urls)} proven-bad url(s): {len(unsourced)} prose card(s) kept but "
              f"unsourced, {len(contaminated)} numeric card(s) to re-hunt, {workers} at a time")

        prop_now = contaminated[:WEB_MAX]
        prop_results = _hunt_many(prop_now) if prop_now else []

        for c, (hit, quote, queries, ok) in zip(prop_now, prop_results):
            old_u = (c.get("source_urls") or [None])[0]
            if hit:
                c["source_urls"] = [hit]
                c["source_fixed"] = True
                fixed.append({"card_id": c["card_id"], "claim": (c.get("gloss") or "")[:140], "old": old_u,
                              "new": hit, "quote": quote[:200], "how": "ai-judged (propagated)"})
            elif ok:
                cut.append({"card_id": c["card_id"], "claim": (c.get("gloss") or "")[:140], "old": old_u,
                            "why": "cites a url proven wrong; no replacement found"})
            propagated.append({"card_id": c["card_id"], "bad_url": old_u, "replaced": bool(hit)})
        if len(contaminated) > WEB_MAX:
            search_failed.append({"card_id": None,
                                  "reason": f"{len(contaminated) - WEB_MAX} contaminated card(s) left unchecked (cap)"})

    # --- phase 3: apply the cuts to the plan (H3s/sections die with their last card) ---
    cut_ids = {_nid(x["card_id"]) for x in cut}
    dropped_h3s, dropped_secs = [], []
    for sec in plan["sections"]:
        for h in sec["h3s"]:
            h["card_ids"] = [cid for cid in h["card_ids"] if _nid(cid) not in cut_ids]
        empty = [h for h in sec["h3s"] if not h["card_ids"]]
        for h in empty:
            dropped_h3s.append({"h3": h["h3"], "from_h2": sec["h2"], "why": "all cards cut by source verification"})
        sec["h3s"] = [h for h in sec["h3s"] if h["card_ids"]]
    dead = [sec for sec in plan["sections"] if not sec["h3s"]]
    for sec in dead:
        dropped_secs.append(sec["h2"])
    plan["sections"] = [sec for sec in plan["sections"] if sec["h3s"]]

    config.write_json(inpp, inp)                     # corrected source_urls live with the cards
    config.write_json(out_path, plan)
    config.write_json(os.path.join(config.planner_work_dir(slug), "source-police.json"), {
        "kept_ok": [c["card_id"] for c in kept_ok],
        "fixed": fixed, "cut": cut,
        "unverifiable_kept": [c["card_id"] for c in unverifiable],
        "search_failed": search_failed,
        "kept_unsourced": unsourced,
        "bad_urls": sorted(bad_urls),
        "propagated": propagated,
        "dropped_h3s": dropped_h3s, "dropped_sections": dropped_secs,
        "coverage": _coverage_verdict(todo, kept_ok, fixed, cut, search_failed),
    })
    print(f"  -> {out_path} | ok {len(kept_ok)} | FIXED {len(fixed)} | CUT {len(cut)} | "
          f"unloadable-kept {len(unverifiable)} | search-failed {len(search_failed)} | "
          f"bad-urls {len(bad_urls)} propagated to {len(propagated)} | "
          f"H3s dropped {len(dropped_h3s)} | sections dropped {len(dropped_secs)}")
    return plan


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Planner Step 3 — verify every citable number's source.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Planner Step 3: verify sources — {a.slug} ==")
    run(a.slug, redo=a.redo)
