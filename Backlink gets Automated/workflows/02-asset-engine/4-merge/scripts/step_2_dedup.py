#!/usr/bin/env python3
"""Step 2 — cross-method DEDUP: merge the ideas that repeat across methods, then write clubbed-ideas.csv.

Reads:  _work/stacked.json
Writes: output/clubbed-ideas.csv   THE MERGED DELIVERABLE (the research phase reads this)
        _work/merge-report.json      every cluster the model saw + what it decided (auditable)

Same entity-resolution as the competitor-study dedup: EMBED each idea (Voyage) -> BLOCK nearest neighbours into
candidate clusters (the embedding only NOMINATES) -> ADJUDICATE each small cluster with the LLM (SAME / COMBINE
/ SEPARATE). On SAME, the survivor pools every merged idea's Sources + proof, so a row found by two methods
shows 'M1 + M3' and carries both proofs (a stronger bet, not a discarded duplicate). Conservative by design.
"""
import argparse, collections, csv, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import config as c
sys.path.insert(0, c.SHARED)
import voyage, llm

# method-specific evidence cells to POOL (take any non-empty value across merged members)
_POOL_CELLS = ["Format", "Tool escalation", "What it'd be", "# pages", "# words", "Total domains",
               "# comps", "# posts", "Beatability", "Effort"]


def _emb_text(r):
    return f"{r.get('Asset','')} — {r.get('Distinct angle','')}".strip(" —")


def _candidates(rows):
    texts = [_emb_text(r) for r in rows]
    import hashlib
    sig = hashlib.sha256("\n".join(texts).encode()).hexdigest()[:16]
    cache = os.path.join(c.WORK, f"merge-emb-{sig}.npy")
    if os.path.exists(cache):
        V = np.load(cache); print(f"   reusing cached embeddings ({len(rows)} ideas)")
    else:
        print(f"   embedding {len(rows)} ideas (Voyage) ..."); V = voyage.embed(texts, "document"); np.save(cache, V)
    V = np.nan_to_num(V.astype(np.float32))            # an empty asset+angle embeds to all-zero -> NaN in the dot product
    n = len(rows); parent = list(range(n))
    src = [r.get("Sources", "") for r in rows]         # each method already deduped ITSELF; the merge only checks CROSS-method repeats

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    edges = 0
    for i in range(n):
        sims = V @ V[i]; sims[i] = -1
        for j in np.argsort(-sims)[:c.DEDUP_TOPK]:
            j = int(j)
            if src[i] != src[j] and sims[j] >= c.DEDUP_THRESHOLD:   # ONLY nominate cross-method pairs
                ra, rb = find(i), find(j)
                if ra != rb:
                    parent[ra] = rb; edges += 1
    groups = collections.defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    clusters = [g for g in groups.values() if len(g) > 1]
    out = []
    for g in clusters:
        for k in range(0, len(g), c.DEDUP_MAX_CLUSTER):
            out.append(g[k:k + c.DEDUP_MAX_CLUSTER])
    print(f"   {edges} candidate edges -> {len(clusters)} raw clusters -> {len(out)} LLM passes "
          f"({n - sum(len(g) for g in clusters)} ideas have no cross-match, skip the LLM)")
    return out


def _adjudicate(members):
    block = "\n".join(
        f"- id={m['_id']} · [{m.get('Sources','')}] · {m.get('Asset','')[:90]} · [{m.get('Format','?')}] · "
        f"angle: {(m.get('Distinct angle') or '')[:120]}" for m in members)
    prompt = llm.load_prompt("merge-dedup.md").replace("{{BRAND}}", c.BRAND).replace("{{CLUSTER}}", block)
    try:
        return llm.call_json(prompt).get("groups", [])
    except Exception as e:
        print(f"   !! a cluster failed to adjudicate ({str(e)[:40]}) — kept separate")
        return []


def _pool(survivor, dead):
    srcs = [s.strip() for s in survivor.get("Sources", "").replace("+", ",").split(",") if s.strip()]
    for s in dead.get("Sources", "").replace("+", ",").split(","):
        if s.strip() and s.strip() not in srcs:
            srcs.append(s.strip())
    survivor["Sources"] = " + ".join(srcs)
    for col in _POOL_CELLS:
        if not (survivor.get(col) or "").strip() and (dead.get(col) or "").strip():
            survivor[col] = dead[col]
    pu = [u for u in [survivor.get("Proof URLs", ""), dead.get("Proof URLs", "")] if u.strip()]
    survivor["Proof URLs"] = " ; ".join(pu)


def run(redo=False):
    rows = json.load(open(os.path.join(c.WORK, "stacked.json")))
    for i, r in enumerate(rows):
        r["_id"] = i
    clusters = _candidates(rows)

    def _judge(cl):
        return cl, _adjudicate([rows[i] for i in cl])
    results, report = [], []
    with ThreadPoolExecutor(max_workers=c.DEDUP_WORKERS) as ex:
        futs = [ex.submit(_judge, cl) for cl in clusters]
        for n, fut in enumerate(as_completed(futs), 1):
            results.append(fut.result())
            if n % 20 == 0:
                print(f"   ...{n}/{len(clusters)} clusters adjudicated")

    by_id = {r["_id"]: r for r in rows}
    merged_ct = combine_ct = 0
    for cl, groups in results:
        report.append({"cluster": [by_id[i]["Asset"][:60] for i in cl], "groups": groups})
        for g in groups:
            act = g.get("action"); ids = [i for i in g.get("ids", []) if i in by_id]
            if len(ids) < 2:
                continue
            if act == "same":
                keep = g.get("keep") if g.get("keep") in by_id else ids[0]
                for mid in ids:
                    if mid == keep or by_id[mid].get("_gone"):
                        continue
                    _pool(by_id[keep], by_id[mid]); by_id[mid]["_gone"] = True; merged_ct += 1
            elif act == "combine" and g.get("new_asset"):
                keep = ids[0]; sv = by_id[keep]
                if sv.get("_gone"):
                    continue
                sv["Asset"] = g["new_asset"]; sv["Distinct angle"] = g.get("new_angle") or sv.get("Distinct angle", "")
                for mid in ids[1:]:
                    if by_id[mid].get("_gone"):
                        continue
                    _pool(sv, by_id[mid]); by_id[mid]["_gone"] = True; combine_ct += 1

    kept = [r for r in rows if not r.get("_gone")]

    # SORT: brand fit first (CORE -> TRANSPLANT -> ADJACENT), then each idea's OWN strength — follow-domains
    # for M1, post-engagement for M3 — so a strong Reddit tension (0 domains by design) isn't dumped at the
    # bottom under a weak 5-domain competitor idea. The two proof signals are summed (one is 0 for the other
    # source), which interleaves the methods fairly within a tier.
    _FIT = {"CORE": 0, "TRANSPLANT": 1, "ADJACENT": 2}

    def _int(v):
        try:
            return int(float(str(v).replace(",", "")))
        except (ValueError, TypeError):
            return 0

    def _strength(r):
        return _int(r.get("Total domains")) + _int(r.get("# posts"))
    kept.sort(key=lambda r: (_FIT.get((r.get("Brand fit") or "").strip().upper(), 3), -_strength(r)))

    os.makedirs(c.OUT, exist_ok=True)
    with open(c.CLUBBED + ".tmp", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=c.COLS, extrasaction="ignore"); w.writeheader()
        for r in kept:
            w.writerow({k: r.get(k, "") for k in c.COLS})
    os.replace(c.CLUBBED + ".tmp", c.CLUBBED)
    c.write_json(os.path.join(c.WORK, "merge-report.json"), report)

    multi = sum(1 for r in kept if "+" in r.get("Sources", ""))
    src = collections.Counter(r["Sources"] for r in kept)
    print(f"   {len(rows)} stacked -> {len(kept)} distinct ({merged_ct} same-merges, {combine_ct} combines)")
    print(f"   cross-method merged (found by >1 method): {multi}")
    print(f"   sources: {dict(src)}")
    print(f"   -> {c.rel(c.CLUBBED)}")
    return kept


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
