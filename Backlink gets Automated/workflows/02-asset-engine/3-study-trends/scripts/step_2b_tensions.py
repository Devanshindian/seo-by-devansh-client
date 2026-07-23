#!/usr/bin/env python3
"""Stage 2b — consolidate phrases into tensions, by MEANING (embeddings), through the merge-check gate.

Reads:  _work/all-phrases.tsv
Writes: _work/merge-check.md      the gate's evidence — written BEFORE tensions.csv (verify checks timestamp order)
        output/phrase-map.csv     phrase -> tension_id -> source_post_ids  (audit trail)
        _work/tensions_base.json   [{tension_id, tension, phrases:[{phrase, post_ids}]}]  (input to 2c/2d)

WHY EMBEDDINGS (measured 2026-07-22): the 425 posts yield 1224 distinct phrases but only 18 repeat verbatim —
recurrence lives at the level of *meaning*, not exact string, and 1224 phrases won't fit one consolidate call.
So: EMBED every phrase (Voyage) -> CLUSTER by cosine (union-find) -> NAME each cluster's tension(s) with a small
parallel LLM call (which SPLITS a cluster that holds >1 pain) -> DEDUP near-identical tension sentences. The
naming call is the merge-check (per-cluster shared-pain judgment); its record is merge-check.md. LLM + embeddings.
"""
import argparse, collections, csv, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import config as c
sys.path.insert(0, c.SHARED)
import llm, voyage

PROMPT = None


def _load_phrases():
    m = collections.OrderedDict()
    for row in csv.DictReader(open(os.path.join(c.WORK, "all-phrases.tsv")), delimiter="\t"):
        for ph in [x.strip() for x in (row.get("phrases") or "").split(",") if x.strip()]:
            m.setdefault(ph, set()).add(row["post_id"])
    return collections.OrderedDict((k, sorted(v)) for k, v in m.items())


def _cluster_groups(V, n_clusters=None, sim=None):
    """Cluster L2-normalised vectors. Give EITHER a target n_clusters -> **KMeans** (balanced, controlled size:
    agglomerative average-linkage made one 584-phrase mega-cluster on this dense space, whose naming call hung),
    OR a similarity floor `sim` -> agglomerative threshold merge (used for the small tension-sentence dedup).
    Returns list of index-lists."""
    from sklearn.cluster import AgglomerativeClustering, KMeans
    n = len(V)
    if n <= 1:
        return [[i] for i in range(n)]
    V = np.nan_to_num(V.astype(np.float32))                     # guard: an empty-phrase embedding can be all-zero -> NaN
    if n_clusters is not None:
        labels = KMeans(n_clusters=min(n_clusters, n), n_init=4, random_state=0).fit_predict(V)
    else:
        labels = AgglomerativeClustering(n_clusters=None, distance_threshold=1.0 - sim,
                                         metric="cosine", linkage="average").fit_predict(V)
    groups = collections.defaultdict(list)
    for i, lab in enumerate(labels):
        groups[int(lab)].append(i)
    return list(groups.values())


def _name(phrases):
    """Name the tension(s) in one cluster of phrases (may split)."""
    block = "\n".join(f"- {p}" for p in phrases)
    prompt = PROMPT.replace("{{BRAND}}", c.BRAND).replace("{{PHRASES}}", block)
    try:
        out = llm.call_json(prompt)
        return out.get("tensions", []), out.get("orphans", [])
    except Exception as e:
        print(f"   !! naming failed for a {len(phrases)}-phrase cluster ({str(e)[:40]})")
        return [], phrases


def run(redo=False):
    global PROMPT
    PROMPT = llm.load_prompt("2b-name-cluster.md")
    phrase_posts = _load_phrases()
    phrases = list(phrase_posts)
    print(f"   {len(phrases)} distinct phrases — embedding (Voyage) ...")

    import hashlib
    sig = hashlib.sha256("\n".join(phrases).encode()).hexdigest()[:16]
    cache = os.path.join(c.WORK, f"phrase-emb-{sig}.npy")
    if os.path.exists(cache) and not redo:
        V = np.load(cache)
    else:
        V = voyage.embed(phrases, "document"); np.save(cache, V)
    chunks = _cluster_groups(V, n_clusters=c.TARGET_CLUSTERS)
    print(f"   {len(chunks)} phrase clusters (target {c.TARGET_CLUSTERS}) -> naming ({c.PHRASE_WORKERS} parallel) ...")

    # NAME each cluster (parallel). Collect candidate tensions + the merge-check record per cluster.
    def _job(idx_cl):
        ci, cl = idx_cl
        cps = [phrases[i] for i in cl]
        tens, orph = _name(cps)
        return ci, cps, tens, orph

    results = [None] * len(chunks)
    with ThreadPoolExecutor(max_workers=c.PHRASE_WORKERS) as ex:
        futs = {ex.submit(_job, (i, cl)): i for i, cl in enumerate(chunks)}
        for n, fut in enumerate(as_completed(futs), 1):
            ci, cps, tens, orph = fut.result(); results[ci] = (cps, tens, orph)
            if n % 20 == 0:
                print(f"   ...{n}/{len(chunks)} clusters named")

    # collect candidate tensions (each: sentence + member phrases)
    cand = []
    mc_blocks = []
    for cps, tens, orph in results:
        got = tens or []
        for t in got:
            names = [p for p in (t.get("phrases") or []) if p in phrase_posts]
            if t.get("tension") and names:
                cand.append({"tension": t["tension"].replace("\t", " ").strip(), "phrases": names})
        mc_blocks.append((cps, got, orph))

    # MERGE ONLY TRUE DUPLICATES — cluster the candidate SENTENCES at a TIGHT similarity (the same pain named by
    # two zones), keeping every distinct pain. No forced count (keep-specific; Stage 3's brand-scope filter is the
    # real cut). Representative = the candidate with the most phrases; its phrases pool together.
    final = []
    if cand:
        TV = voyage.embed([t["tension"] for t in cand], "document")
        for grp in _cluster_groups(TV, sim=c.MERGE_SIM):
            grp = sorted(grp, key=lambda gi: -len(cand[gi]["phrases"]))
            lead = cand[grp[0]]
            allph = sorted({p for gi in grp for p in cand[gi]["phrases"]})
            final.append({"tension": lead["tension"], "phrases": allph})
    dropped = [t for t in final if len(t["phrases"]) < c.TENSION_MIN_PHRASES]
    final = [t for t in final if len(t["phrases"]) >= c.TENSION_MIN_PHRASES]
    final.sort(key=lambda t: -len(t["phrases"]))               # strongest (most phrases) first
    for i, t in enumerate(final, 1):
        t["tension_id"] = f"T{i:02d}"
    print(f"   {len(cand)} candidates -> {len(final)} tensions after dedup "
          f"(+{len(dropped)} 1-phrase fragments dropped to misc)")

    # merge-check.md — MUST contain every final tension_id. Written NOW (before 2d writes tensions.csv).
    os.makedirs(c.WORK, exist_ok=True)
    lines = [f"# Merge check — {c.BRAND} (Stage 2b gate)",
             "Phrases were clustered by meaning (embeddings), then each cluster named into its shared-pain tension(s),",
             "splitting any cluster that held more than one pain. Near-identical tensions were then merged.", "",
             "## Final tensions (each formed through the per-cluster shared-pain gate)"]
    for t in final:
        lines.append(f"- **{t['tension_id']}**: {t['tension']}  ({len(t['phrases'])} phrases)")
    lines.append("\n## Per-cluster naming record")
    for cps, tens, orph in mc_blocks:
        lines.append(f"- cluster of {len(cps)} phrases: " + "; ".join(cps[:8]) + (" …" if len(cps) > 8 else ""))
        for t in (tens or []):
            lines.append(f"  → PASS: {t.get('tension','')}")
        if orph:
            lines.append(f"  → orphans: {', '.join(orph[:6])}")
    c.write_text(os.path.join(c.WORK, "merge-check.md"), "\n".join(lines) + "\n")

    # phrase-map.csv — one row per distinct phrase -> tension_id -> source_post_ids
    seen, pm = set(), []
    for t in final:
        for ph in t["phrases"]:
            if ph in seen:
                continue
            seen.add(ph)
            pm.append({"phrase": ph, "tension": t["tension_id"], "source_post_ids": " ".join(phrase_posts[ph])})
    os.makedirs(c.OUT, exist_ok=True)
    with open(os.path.join(c.OUT, "phrase-map.csv") + ".tmp", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["phrase", "tension", "source_post_ids"]); w.writeheader(); w.writerows(pm)
    os.replace(os.path.join(c.OUT, "phrase-map.csv") + ".tmp", os.path.join(c.OUT, "phrase-map.csv"))

    base = [{"tension_id": t["tension_id"], "tension": t["tension"],
             "phrases": [{"phrase": ph, "post_ids": phrase_posts[ph]} for ph in t["phrases"]]} for t in final]
    c.write_json(os.path.join(c.WORK, "tensions_base.json"), base)
    print(f"   -> {len(final)} tensions · merge-check.md + phrase-map.csv ({len(pm)} phrases) + tensions_base.json")
    return base


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
