#!/usr/bin/env python3
"""Step A1c — never trust a domain, whoever supplied it.

Why this exists (measured 2026-07-20): three approved competitors came back from Step B with ZERO
pages. Two of them were not small — they were DEAD DOMAINS that never resolve:
    maki.people  -> does not resolve; the real company is makipeople.com
    wecp.io      -> does not resolve; the real company is wecreateproblems.com
Both were operator-supplied, and the engine trusted them without checking. Money was spent on API
calls for domains that cannot exist. An operator typing a brand name instead of a domain, or a
slightly wrong TLD, is an ordinary mistake — the engine must catch it, not inherit it.

What this does, for EVERY domain (operator-supplied and model-picked alike):
  1. check it actually resolves,
  2. if it does not, look for a live alternative — the model's own `aliases`, then near-matches in
     the candidate list (which is real data, so anything in it demonstrably exists),
  3. swap to the live one and record the swap, or drop it with a stated reason.

Reads:  _work/shortlist.json + _work/candidates.json
Writes: _work/shortlist.json (in place, with `resolved`/`swapped_from`/`dropped_reason`)
"""
import json, os, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0"
TIMEOUT = int(os.environ.get("CS_DNS_TIMEOUT", "10"))


def resolves(domain):
    """Live? Any HTTP answer at all counts — a 403 still proves the domain exists."""
    for scheme in ("https://", "https://www."):
        try:
            req = urllib.request.Request(scheme + domain, headers={"User-Agent": UA}, method="HEAD")
            urllib.request.urlopen(req, timeout=TIMEOUT)
            return True
        except urllib.error.HTTPError:
            return True                       # 403/404 from a real server = the domain exists
        except Exception:
            continue
    return False


def _repairs(dead):
    """Obvious repairs for a dead domain, generalized. An operator writing a brand name rather than a
    real domain is an ordinary mistake — and a brand's WORDS may be split across the dot, so the odd
    'TLD' is often part of the name: 'maki.people' is the company Maki People at makipeople.com.
    Every candidate is only used if it actually resolves, so a wrong guess can never enter the study."""
    parts = [p for p in dead.split(".") if p]
    out = []
    if len(parts) > 1:
        joined = "".join(parts)                    # maki.people -> makipeople
        out += [joined + ".com", "-".join(parts) + ".com"]
        head = "".join(parts[:-1])                 # treat the last part as a real TLD
        out += [head + ".com", head.replace("-", "") + ".com"]
    flat = dead.replace("-", "")
    if flat != dead:
        out.append(flat)
    seen, uniq = set(), []
    for d in out:
        if d and d != dead and d not in seen:
            seen.add(d); uniq.append(d)
    return uniq


def _near(dead, cand_domains):
    """A live candidate that is plainly the same company: 'maki.people' -> 'makipeople.com'."""
    stem = dead.split(".")[0].replace("-", "")
    flat = dead.replace(".", "").replace("-", "")
    for d in cand_domains:
        dflat = d.replace(".", "").replace("-", "")
        if dflat.startswith(flat) or flat.startswith(dflat.split("com")[0]) or \
           (len(stem) >= 4 and dflat.startswith(stem)):
            return d
    return None


def run():
    sl_path = os.path.join(c.WORK, "shortlist.json")
    if not os.path.exists(sl_path):
        sys.exit("!! no shortlist.json — run the shortlist first")
    sl = json.load(open(sl_path))
    comps = sl.get("competitors", [])
    cand_domains = [x["domain"] for x in json.load(open(os.path.join(c.WORK, "candidates.json")))]

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(resolves, x["domain"]): x for x in comps}
        for fut in as_completed(futs):
            futs[fut]["resolved"] = bool(fut.result())

    kept, swapped, dropped = [], [], []
    for x in comps:
        if x.get("resolved"):
            kept.append(x); continue
        dead = x["domain"]
        # 1) the model's own alias  2) a near-match in the candidate list  3) an obvious repair
        alt = next((a for a in (x.get("aliases") or []) if resolves(a)), None)
        if not alt:
            near = _near(dead, cand_domains)
            alt = near if (near and resolves(near)) else None
        if not alt:
            alt = next((r for r in _repairs(dead) if resolves(r)), None)
        if alt and resolves(alt):
            x["swapped_from"], x["domain"], x["resolved"] = dead, alt, True
            x.setdefault("aliases", []).append(dead)
            swapped.append((dead, alt)); kept.append(x)
        else:
            x["dropped_reason"] = "domain does not resolve and no live alternative found"
            dropped.append(dead)

    sl["competitors"] = kept
    sl["validation"] = {"swapped": [{"from": a, "to": b} for a, b in swapped], "dropped": dropped}
    c.write_json(sl_path, sl)

    print(f"   {len(kept)} live · {len(swapped)} swapped · {len(dropped)} dropped")
    for a, b in swapped:
        print(f"     !! '{a}' does not resolve -> using '{b}' instead")
    for d in dropped:
        print(f"     !! '{d}' dropped — dead domain, no live alternative")
    return sl


if __name__ == "__main__":
    run()
