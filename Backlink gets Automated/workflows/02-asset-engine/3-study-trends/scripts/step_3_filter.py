#!/usr/bin/env python3
"""Stage 3 — filter tensions: Linkability + Ownability (transplant check) -> verdicts into tensions.csv.

Reads:  output/tensions.csv · brand-scope.md
Writes: output/tensions.csv (in place — Linkability verdict / Ownability verdict / Verdict columns filled)

Verdict uses the gate's closed vocabulary: KEEP-CORE / KEEP-TRANSPLANT / MAYBE (=ADJACENT) / DROP. LLM JUDGMENT.
"""
import argparse, csv, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c
sys.path.insert(0, c.SHARED)
import llm


def run(redo=False):
    path = os.path.join(c.OUT, "tensions.csv")
    rows = list(csv.DictReader(open(path)))
    SCOPE = open(c.BRAND_SCOPE).read()
    PROMPT = llm.load_prompt("3-filter.md")

    def _shard(batch):
        listed = "\n".join(
            f"{r['tension_id']} | {r['Tension']} | core pain: {r['Core pain']} | implied data: {r['Implied data point']}"
            for r in batch)
        p = (PROMPT.replace("{{BRAND}}", c.BRAND).replace("{{BRAND_SCOPE}}", SCOPE)
             .replace("{{LINK_MIN}}", str(c.LINKABILITY_MIN)).replace("{{TENSIONS}}", listed))
        try:
            return {str(x["tension_id"]): x for x in llm.call_json(p).get("verdicts", []) if "tension_id" in x}
        except Exception as e:
            print(f"   !! a filter shard failed ({str(e)[:40]}) — those tensions default to DROP")
            return {}

    shards = [rows[i:i + c.FILTER_SHARD] for i in range(0, len(rows), c.FILTER_SHARD)]
    print(f"   filtering {len(rows)} tensions in {len(shards)} shards ({c.PHRASE_WORKERS} parallel) ...")
    v = {}
    with ThreadPoolExecutor(max_workers=c.PHRASE_WORKERS) as ex:
        for fut in as_completed([ex.submit(_shard, s) for s in shards]):
            v.update(fut.result())

    kept = 0
    for r in rows:
        d = v.get(r["tension_id"], {})
        yes = int(d.get("linkability_yes", 0))
        fit = (d.get("brand_fit") or "OUT").upper()
        verdict = (d.get("verdict") or "DROP").upper()
        if verdict == "KEEP" and fit in ("CORE", "TRANSPLANT") and yes >= c.LINKABILITY_MIN:
            final = f"KEEP-{fit}"
        elif verdict == "MAYBE" or fit == "ADJACENT":
            final = "MAYBE"
        else:
            final = "DROP"
        r["Linkability verdict"] = f"{yes}/4 {'PASS' if yes >= c.LINKABILITY_MIN else 'FAIL'}"
        r["Ownability verdict"] = fit + (f" ({d.get('transplant_note')})" if d.get("transplant_note") else "")
        r["Verdict"] = final
        r["_reason"] = d.get("reason", "")
        if final != "DROP":
            kept += 1

    with open(path + ".tmp", "w", newline="") as f:
        cols = [k for k in rows[0].keys() if k != "_reason"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        w.writerows({k: r[k] for k in cols} for r in rows)
    os.replace(path + ".tmp", path)

    from collections import Counter
    print(f"   {len(rows)} tensions -> {kept} kept, {len(rows)-kept} dropped")
    print(f"   verdicts: {dict(Counter(r['Verdict'] for r in rows))}")
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
