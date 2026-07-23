#!/usr/bin/env python3
"""Stage 4 — turn each KEPT tension into one asset idea -> study-trends-ideas.csv (THE DELIVERABLE).

Reads:  output/tensions.csv (kept rows) · brand-voice/features/stats
Writes: output/study-trends-ideas.csv   Tension · Asset title · What it'd be · Brand fit · Unfair advantage ·
                                        # posts · Audience · Emotion · Best example URL

The verify gate requires: idea count == kept-tension count. LLM JUDGMENT.
"""
import argparse, csv, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c
sys.path.insert(0, c.SHARED)
import llm

KEEP = {"KEEP-CORE", "KEEP-ADJACENT", "KEEP-TRANSPLANT", "MAYBE"}
COLS = ["Tension", "Asset title", "What it'd be", "Brand fit", "Unfair advantage",
        "# posts", "Audience", "Emotion", "Best example URL"]
PROMPT = VOICE = FEATURES = STATS = None


def _fit(verdict):
    return {"KEEP-CORE": "CORE", "KEEP-TRANSPLANT": "TRANSPLANT", "KEEP-ADJACENT": "ADJACENT", "MAYBE": "ADJACENT"}.get(verdict, "ADJACENT")


def _idea(r):
    fit = _fit(r["Verdict"])
    p = (PROMPT.replace("{{BRAND}}", c.BRAND).replace("{{BRAND_VOICE}}", VOICE).replace("{{FEATURES}}", FEATURES)
         .replace("{{STATS}}", STATS).replace("{{BRAND_FIT}}", fit).replace("{{FIT_REASON}}", r.get("Ownability verdict", ""))
         .replace("{{TENSION}}", r["Tension"]).replace("{{CORE_PAIN}}", r["Core pain"])
         .replace("{{PHRASES}}", r["Phrases"]).replace("{{AUDIENCE}}", r["Audience"]).replace("{{EMOTION}}", r["Emotion"])
         .replace("{{IMPLIED_DATA}}", r["Implied data point"]).replace("{{SUB_QUESTIONS}}", r["Sub-questions"])
         .replace("{{QUOTES}}", r["Representative quotes"]).replace("{{NPOSTS}}", str(r["# posts"]))
         .replace("{{UPVOTES}}", str(r["Total upvotes"])).replace("{{SPREAD}}", r["Subreddit spread"]))
    try:
        out = llm.call_json(p)
    except Exception as e:
        print(f"   !! idea failed for {r['tension_id']} ({str(e)[:40]})")
        return None
    return {"Tension": r["Tension"], "Asset title": out.get("asset_title", ""),
            "What it'd be": out.get("what_it_would_be", ""), "Brand fit": fit,
            "Unfair advantage": out.get("unfair_advantage", ""), "# posts": r["# posts"],
            "Audience": r["Audience"], "Emotion": r["Emotion"], "Best example URL": r["Best example"]}


def run(redo=False):
    global PROMPT, VOICE, FEATURES, STATS
    PROMPT = llm.load_prompt("4-idea.md")
    n = c.IDEA_CTX_CHARS                                        # cap each doc: full context x 100+ ideas is slow + costly
    VOICE = (open(c.BRAND_VOICE).read()[:n] if os.path.exists(c.BRAND_VOICE) else "")
    FEATURES = (open(c.FEATURES).read()[:n] if os.path.exists(c.FEATURES) else "")
    STATS = (open(c.STATS).read()[:n] if os.path.exists(c.STATS) else "")
    kept = [r for r in csv.DictReader(open(os.path.join(c.OUT, "tensions.csv"))) if r["Verdict"] in KEEP]
    print(f"   generating {len(kept)} ideas (one per kept tension) ...")
    out = [None] * len(kept)
    with ThreadPoolExecutor(max_workers=c.PHRASE_WORKERS) as ex:
        futs = {ex.submit(_idea, r): i for i, r in enumerate(kept)}
        for fut in as_completed(futs):
            out[futs[fut]] = fut.result()
    out = [r for r in out if r]
    if len(out) != len(kept):
        sys.exit(f"!! idea count {len(out)} != kept tensions {len(kept)} — the verify gate needs them equal; re-run stage 4")
    path = os.path.join(c.OUT, "study-trends-ideas.csv")
    with open(path + ".tmp", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(out)
    os.replace(path + ".tmp", path)
    print(f"   {len(out)} ideas -> {c.rel(path)}")
    for r in out[:8]:
        print(f"     [{r['Brand fit'][:4]}] {r['Asset title'][:64]}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
