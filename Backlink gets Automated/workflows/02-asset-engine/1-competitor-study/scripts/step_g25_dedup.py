#!/usr/bin/env python3
"""Step G2.5 — SEMANTIC de-dup: merge ideas that are the same BUILD, keep the rest. Voyage + LLM.

Reads:  _work/g2_sheet.json   (every reasoned idea: asset / distinct_angle / format / brand_fit / domains)
Writes: _work/g2_sheet.json   (in place — each merged row gets `merged_into`=<survivor row_id>; survivors
                               get their evidence pooled: backing_urls, domains, backlinks, angle gaps)
        _work/dedup-report.json  (every cluster the model saw + what it decided — fully auditable)

WHY THIS REPLACES THE STRING-MATCH DEDUP (Devansh, 2026-07-21). G3's old dedup merged only byte-identical
titles, so it missed "Python Skills Test" vs "Coding Assessment (Python)" (same build, different words).
An LLM turned loose on ALL ideas over-merged into vague categories (the 3.4 disaster). The fix is the
textbook entity-resolution pattern, and it's Devansh's design:
  1. EMBED every idea (Voyage voyage-4-large — the same stack the reuse-check uses).
  2. BLOCK: for each idea, gather its top-K nearest neighbours ABOVE a cosine threshold into candidate
     clusters. The embedding only PROPOSES — it never merges on its own (measured: a glossary and a test
     library can sit at 0.75, which would be a wrong merge).
  3. ADJUDICATE: hand each small cluster to the LLM. It may MERGE same-build ideas (naming the survivor),
     KEEP genuinely different ones separate, and it may NOT edit a single word of any title or angle. It
     leans toward merging when two are ~mostly the same. It only ever sees a handful of ideas at once, so
     it cannot squish across the whole set.

No target count — could stay at 2,000, could drop to 1,200. Whatever the data honestly is.
The Voyage key comes from the env / ~/.testlify-access.md via _shared/voyage.py (never in the repo).
"""
import argparse, json, os, sys, collections
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import config as c
sys.path.insert(0, c.SHARED)
import voyage, llm

PROMPT = None


def _emb_text(r):
    """What we embed = the BUILD IDENTITY (title + format), not the whole angle — keeps twins close."""
    return f"{r.get('asset','')} — {r.get('format','')}".strip(" —")


def _candidates(rows):
    """Return clusters (lists of row indices) of ideas that MIGHT be the same, for the LLM to judge.
    Union-find over 'i and j are within threshold' edges; only multi-member clusters need the LLM."""
    import hashlib
    n = len(rows)
    texts = [_emb_text(r) for r in rows]
    sig = hashlib.sha256("\n".join(texts).encode()).hexdigest()[:16]
    cache = os.path.join(c.WORK, f"dedup-emb-{sig}.npy")           # reuse embeddings across re-runs (free tokens)
    if os.path.exists(cache):
        V = np.load(cache)
        print(f"   reusing cached embeddings for {n} ideas ({voyage.EMB_MODEL})")
    else:
        print(f"   embedding {n} ideas via Voyage ({voyage.EMB_MODEL}) ...")
        V = voyage.embed(texts, "document")                        # (n, dim), L2-normalised -> dot=cosine
        np.save(cache, V)
    V = np.nan_to_num(np.asarray(V, dtype=np.float32))             # an empty asset+format embeds to zero -> guard the matmul (same as 4-merge dedup)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    edges = 0
    for i in range(n):
        sims = V @ V[i]
        sims[i] = -1.0
        for j in np.argsort(-sims)[:c.DEDUP_TOPK]:
            if sims[int(j)] >= c.DEDUP_THRESHOLD:
                union(i, int(j)); edges += 1
    groups = collections.defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    clusters = [g for g in groups.values() if len(g) > 1]
    # break any oversized cluster into <= MAX_CLUSTER chunks so each LLM pass stays small
    out = []
    for g in clusters:
        if len(g) <= c.DEDUP_MAX_CLUSTER:
            out.append(g)
        else:
            for k in range(0, len(g), c.DEDUP_MAX_CLUSTER):
                out.append(g[k:k + c.DEDUP_MAX_CLUSTER])
    print(f"   {edges} candidate edges -> {len(clusters)} raw clusters -> {len(out)} LLM passes "
          f"(the {n - sum(len(g) for g in clusters)} ideas with no near-twin skip the LLM)")
    return out


def _adjudicate(members):
    """Ask the LLM which of this cluster's ideas are the same build. Returns [{'same':[ids],'keep':id}]."""
    block = "\n".join(
        f"- id={m['row_id']} · {m.get('asset','')[:90]} · [{m.get('format','?')}] · "
        f"angle: {(m.get('distinct_angle') or '')[:120]}" for m in members)
    prompt = PROMPT.replace("{{BRAND}}", c.BRAND).replace("{{CLUSTER}}", block)
    try:
        out = llm.call_json(prompt)
        return out.get("groups", [])
    except llm._FatalCLIError:
        raise
    except Exception as e:
        print(f"   !! a cluster failed to adjudicate ({str(e)[:50]}) — kept all separate")
        return []


def _pool(survivor, dead):
    """Pool a merged idea's proof into its survivor (stronger signal, nothing lost)."""
    survivor["domains_follow"] = (survivor.get("domains_follow") or 0) + (dead.get("domains_follow") or 0)
    survivor["backlinks"] = (survivor.get("backlinks") or 0) + (dead.get("backlinks") or 0)
    su = survivor.setdefault("_merged_urls", [survivor.get("url", "")])
    su.append(dead.get("url", ""))
    sg = survivor.setdefault("_merged_gaps", [])
    if dead.get("angle_gap"):
        sg.append(f"[{dead.get('url','')}] {dead.get('angle_gap','')}")
    # a build-flag survives the merge: if the survivor has none but the merged idea did, carry it up
    if not (survivor.get("tool_escalation") or "").strip() and (dead.get("tool_escalation") or "").strip():
        survivor["tool_escalation"] = dead["tool_escalation"]


def export_clusters():
    """Write every candidate cluster (with member titles/angles) so an external adjudicator — subagents in
    this session, or a re-run — can decide the merges without re-embedding. Used for the free/fast path."""
    sheet = os.path.join(c.WORK, "g2_sheet.json")
    rows = json.load(open(sheet))
    ideas = [r for r in rows if (r.get("brand_fit") or "") != "SKIP" and (r.get("asset") or "").strip()]
    clusters = _candidates(ideas)
    out = [{"cluster": i, "members": [
                {"id": ideas[j]["row_id"], "asset": ideas[j].get("asset", ""),
                 "format": ideas[j].get("format", ""), "angle": (ideas[j].get("distinct_angle") or "")[:160],
                 "domains": ideas[j].get("domains_follow", 0)} for j in cl]}
            for i, cl in enumerate(clusters)]
    c.write_json(os.path.join(c.WORK, "dedup-clusters.json"), out)
    print(f"   exported {len(out)} clusters -> _work/dedup-clusters.json (for subagent adjudication)")
    return out


def apply_decisions(decisions):
    """Apply a list of per-cluster decisions (from subagents or a re-run) to the master sheet. Same
    merge/combine/pool logic as the live path — the adjudicator is swappable, the apply is one place (F1)."""
    sheet = os.path.join(c.WORK, "g2_sheet.json")
    rows = json.load(open(sheet))
    by_id = {r["row_id"]: r for r in rows}
    merged_ct = 0
    for d in decisions:
        for g in d.get("groups", []):
            act = g.get("action"); ids = [i for i in g.get("ids", []) if i in by_id]
            if len(ids) < 2:
                continue
            if act == "same":
                keep = g.get("keep") if g.get("keep") in by_id else ids[0]
                for mid in ids:
                    if mid == keep or by_id[mid].get("merged_into") is not None:
                        continue
                    by_id[mid]["merged_into"] = keep; _pool(by_id[keep], by_id[mid]); merged_ct += 1
            elif act == "combine" and g.get("new_asset"):
                keep = ids[0]; sv = by_id[keep]
                sv["asset"] = g["new_asset"]; sv["distinct_angle"] = g.get("new_angle") or sv.get("distinct_angle", "")
                sv["combined_from"] = ids
                for mid in ids[1:]:
                    if by_id[mid].get("merged_into") is not None:
                        continue
                    by_id[mid]["merged_into"] = keep; _pool(sv, by_id[mid]); merged_ct += 1
    c.write_json(sheet, rows)
    ideas = [r for r in rows if (r.get("brand_fit") or "") != "SKIP" and (r.get("asset") or "").strip()]
    survivors = sum(1 for r in ideas if r.get("merged_into") is None)
    print(f"   applied: merged {merged_ct} ideas -> {survivors} distinct kept ({100*survivors/max(len(ideas),1):.0f}%)")
    return survivors


def run(sample=0, redo=False):
    global PROMPT
    PROMPT = llm.load_prompt("g-dedup.md")
    sheet = os.path.join(c.WORK, "g2_sheet.json")
    if not os.path.exists(sheet):
        sys.exit("!! no _work/g2_sheet.json — run step_g2_reason.py first")
    rows = json.load(open(sheet))
    ideas = [r for r in rows if (r.get("brand_fit") or "") != "SKIP" and (r.get("asset") or "").strip()]
    by_id = {r["row_id"]: r for r in ideas}

    clusters = _candidates(ideas)
    if sample:
        clusters = clusters[:sample]
        print(f"\n   === SAMPLE MODE: adjudicating the first {len(clusters)} clusters only ===")

    # ADJUDICATE ALL CLUSTERS IN PARALLEL (they're independent) — the CLI equivalent of fanning out
    # subagents. Decisions are collected first, then applied serially (so pooling never races).
    def _judge(cl):
        members = [ideas[i] for i in cl]
        return cl, members, ([] if sample and False else _adjudicate(members))

    order = list(enumerate(clusters, 1))
    results = {}
    if sample:
        for ci, cl in order:                       # sample: serial + printed, so it reads top-to-bottom
            results[ci] = _judge(cl)
    else:
        with ThreadPoolExecutor(max_workers=c.DEDUP_WORKERS) as ex:
            futs = {ex.submit(_judge, cl): ci for ci, cl in order}
            for n, fut in enumerate(as_completed(futs), 1):
                results[futs[fut]] = fut.result()
                if n % 25 == 0:
                    print(f"   ...{n}/{len(clusters)} clusters adjudicated")

    report, merged_ct = [], 0
    for ci, cl in order:
        cl, members, groups = results[ci]
        decision = {"cluster": [{"id": m["row_id"], "asset": m.get("asset", ""),
                                 "format": m.get("format", ""), "domains": m.get("domains_follow", 0)}
                                for m in members], "groups": groups}
        report.append(decision)
        if sample:
            print(f"\n   --- cluster {ci} ({len(members)} candidates) ---")
            for m in members:
                print(f"       id={m['row_id']:>4} d={m.get('domains_follow',0):>4} · {m.get('asset','')[:66]}")
            if not groups:
                print("       -> all SEPARATE (LLM merged nothing)")
            for g in groups:
                act, ids = g.get("action"), g.get("ids", [])
                if act == "same":
                    keep = g.get("keep")
                    kn = (by_id.get(keep) or {}).get("asset", "?")
                    print(f"       -> SAME: keep id={keep} «{kn[:44]}» · delete {[i for i in ids if i != keep]}")
                elif act == "combine":
                    print(f"       -> COMBINE {ids} into a NEW richer idea:")
                    print(f"             asset: {g.get('new_asset','')[:64]}")
                    print(f"             angle: {g.get('new_angle','')[:64]}")
        else:
            # apply for real
            for g in groups:
                act = g.get("action")
                ids = [i for i in g.get("ids", []) if i in by_id]
                if len(ids) < 2:
                    continue
                if act == "same":
                    keep = g.get("keep") if g.get("keep") in by_id else ids[0]
                    for mid in ids:
                        if mid == keep or by_id[mid].get("merged_into") is not None:
                            continue
                        by_id[mid]["merged_into"] = keep
                        _pool(by_id[keep], by_id[mid]); merged_ct += 1
                elif act == "combine" and g.get("new_asset"):
                    keep = ids[0]                                  # survivor CARRIES the new combined idea
                    sv = by_id[keep]
                    sv["asset"] = g["new_asset"]                   # the one case text is rewritten (a richer merge)
                    sv["distinct_angle"] = g.get("new_angle") or sv.get("distinct_angle", "")
                    sv["combined_from"] = ids
                    for mid in ids[1:]:
                        if by_id[mid].get("merged_into") is not None:
                            continue
                        by_id[mid]["merged_into"] = keep
                        _pool(sv, by_id[mid]); merged_ct += 1

    c.write_json(os.path.join(c.WORK, "dedup-report.json"), report)
    if sample:
        print(f"\n   (sample only — nothing written to the master. report -> _work/dedup-report.json)")
        return report
    c.write_json(sheet, rows)
    survivors = sum(1 for r in ideas if r.get("merged_into") is None)
    print(f"\n   merged {merged_ct} ideas into survivors -> {survivors} distinct ideas "
          f"({100*survivors/max(len(ideas),1):.0f}% kept)")
    print(f"   -> {c.rel(sheet)} (merged rows tagged `merged_into`) · report -> _work/dedup-report.json")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0, help="adjudicate only the first N clusters and PRINT them (no writes)")
    ap.add_argument("--export", action="store_true", help="write clusters to _work/dedup-clusters.json for external (subagent) adjudication")
    ap.add_argument("--apply", default="", help="apply a decisions JSON file (a list of {cluster, groups}) to the master")
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    if a.export:
        export_clusters()
    elif a.apply:
        apply_decisions(json.load(open(a.apply)))
    else:
        run(sample=a.sample, redo=a.redo)
