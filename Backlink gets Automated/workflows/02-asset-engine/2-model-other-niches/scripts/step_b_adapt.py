#!/usr/bin/env python3
"""Step B — generate the {company} adaptation of each surviving format (one per format, in parallel).

Reads:  _work/swipe.json      (the surviving formats + their in-scope subject / brand fit)
        brand-scope + brand-voice + features + stats (the grounding context)
Writes: _work/adaptations.json — one adaptation per format: our_topic / distinct_angle / asset / headline /
                                 what_it_would_be, PLUS the carried swipe fields (format, example, why_links).

One row -> one adaptation (the recipe's rule: most formats yield ONE strong idea, not five). LLM JUDGMENT.
"""
import argparse, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import config as c
sys.path.insert(0, c.SHARED)
import llm

PROMPT = SCOPE = VOICE = FEATURES = STATS = None


def _load_context():
    global PROMPT, SCOPE, VOICE, FEATURES, STATS
    PROMPT = llm.load_prompt("b-adapt.md")
    SCOPE = open(c.BRAND_SCOPE).read()
    VOICE = open(c.BRAND_VOICE).read() if os.path.exists(c.BRAND_VOICE) else ""
    FEATURES = open(c.FEATURES).read() if os.path.exists(c.FEATURES) else ""
    STATS = open(c.STATS).read() if os.path.exists(c.STATS) else ""


def _adapt(s):
    p = (PROMPT.replace("{{BRAND}}", c.BRAND).replace("{{FORMAT}}", s["format"])
         .replace("{{HEADLINE_TEMPLATE}}", s.get("headline_template", ""))
         .replace("{{WHY_LINKS}}", s.get("why_links", "")).replace("{{EXAMPLE}}", s.get("example", ""))
         .replace("{{IN_SCOPE_SUBJECT}}", s.get("in_scope_subject", "")).replace("{{BRAND_FIT}}", s.get("brand_fit", ""))
         .replace("{{BRAND_SCOPE}}", SCOPE).replace("{{BRAND_VOICE}}", VOICE)
         .replace("{{FEATURES}}", FEATURES).replace("{{STATS}}", STATS))
    try:
        out = llm.call_json(p)
    except Exception as e:
        print(f"   !! adapt failed for {s['format'][:40]} ({str(e)[:40]})")
        return None
    return {"format": s["format"], "example": s.get("example", ""), "why_links": s.get("why_links", ""),
            "prescreen_fit": s.get("brand_fit", ""),
            "our_topic": out.get("our_topic", ""), "distinct_angle": out.get("distinct_angle", ""),
            "asset": out.get("asset", ""), "tool_escalation": out.get("tool_escalation", ""),
            "headline": out.get("headline", ""),
            "what_it_would_be": out.get("what_it_would_be", ""),
            "source_niche": out.get("source_niche", "")}


def run(redo=False):
    _load_context()
    swipe = json.load(open(os.path.join(c.WORK, "swipe.json")))
    print(f"   adapting {len(swipe)} formats ({c.ADAPT_WORKERS} parallel) ...")
    out = [None] * len(swipe)
    with ThreadPoolExecutor(max_workers=c.ADAPT_WORKERS) as ex:
        futs = {ex.submit(_adapt, s): i for i, s in enumerate(swipe)}
        for n, fut in enumerate(as_completed(futs), 1):
            out[futs[fut]] = fut.result()
            if n % 5 == 0:
                print(f"   ...{n}/{len(swipe)} adapted")
    out = [r for r in out if r and r.get("asset")]              # keep order, drop failures
    c.write_json(os.path.join(c.WORK, "adaptations.json"), out)
    print(f"   {len(out)} adaptations written -> {c.rel(os.path.join(c.WORK, 'adaptations.json'))}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--redo", action="store_true")
    run(ap.parse_args().redo)
