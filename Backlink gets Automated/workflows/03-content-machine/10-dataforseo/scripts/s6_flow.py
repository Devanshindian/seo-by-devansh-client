#!/usr/bin/env python3
"""Step 6 (thinking) — the AEO loop: 6a query gate (LLM) -> 6b fetch (s6_aeo.py) -> 6c relevance+writeup (LLM).
Bounded to ~4 anchored tries; if every pull drifts off-topic it reports "no usable signal" (never borrows).

Reads:  primary keyword + distinct angle. Calls s6_aeo.py (which writes 06-aeo.json / 06-aeo-extract.json).
Writes: <run_dir>/proof/06a-query.json (attempt log) · 06-aeo.md (the section).
"""
import os, sys, json, argparse, subprocess
import config, llm

QUERY = llm.load_prompt("aeo-query.md")
WRITE = llm.load_prompt("aeo-writeup.md")
MAX_TRIES = 4


def _fetch(run_dir, query, match_type):
    subprocess.run([sys.executable, os.path.join(config.HERE, "s6_aeo.py"), run_dir, query, match_type],
                   check=True, capture_output=True, text=True, timeout=config.CLAUDE_TIMEOUT)
    return json.load(open(os.path.join(run_dir, "proof", "06-aeo-extract.json")))


def _writeup(primary, angle, extract, attempts):
    ex = extract or {}
    p = (WRITE.replace("{{BRAND}}", config.BRAND).replace("{{PRIMARY_KEYWORD}}", primary)
         .replace("{{DISTINCT_ANGLE}}", angle)
         .replace("{{QUESTIONS}}", json.dumps([q.get("q") for q in ex.get("questions", [])]))
         .replace("{{FAN_OUT}}", json.dumps(ex.get("fan_out", [])))
         .replace("{{CITED_DOMAINS}}", json.dumps(ex.get("cited_domains", [])))
         .replace("{{BRAND_CITED}}", str(ex.get("brand_cited", False)))
         .replace("{{ATTEMPTS}}", json.dumps(attempts)))
    return llm.call_text(p)


def run(run_dir, primary, angle):
    proof = os.path.join(run_dir, "proof"); os.makedirs(proof, exist_ok=True)
    attempts, stop_why, usable_md, last_extract = [], None, None, None

    for _ in range(MAX_TRIES):
        gp = (QUERY.replace("{{PRIMARY_KEYWORD}}", primary).replace("{{DISTINCT_ANGLE}}", angle)
              .replace("{{ATTEMPTS}}", json.dumps(attempts)))
        gate = llm.call_json(gp)
        if gate.get("stop"):
            stop_why = gate.get("why", "no usable signal"); break
        q, mt = gate.get("query"), gate.get("match_type", "phrase_match")
        try:
            ex = _fetch(run_dir, q, mt)
        except Exception as e:
            attempts.append({"query": q, "match_type": mt, "result": f"fetch error: {str(e)[:80]}"}); continue
        last_extract = ex
        md = _writeup(primary, angle, ex, attempts)
        n = len(ex.get("questions", []))
        if "Status: usable" in md:
            usable_md = md
            attempts.append({"query": q, "match_type": mt, "result": f"{n} items — on-topic, kept"})
            break
        sample = [x.get("q") for x in ex.get("questions", [])[:2]]
        attempts.append({"query": q, "match_type": mt, "result": f"{n} items — off-topic ({sample})"})

    config.write_json(os.path.join(proof, "06a-query.json"), {"primary_keyword": primary, "attempts": attempts,
               "stop": usable_md is None, "why": stop_why or ("kept a usable pull" if usable_md else
               "every anchored query drifted off-topic; corpus lacks this topic")})

    md = usable_md or _writeup(primary, angle, last_extract, attempts)
    config.write_text(os.path.join(proof, "06-aeo.md"), md.rstrip() + "\n")
    print(f"  -> 06-aeo.md ({'usable' if usable_md else 'no usable signal'}) · {len(attempts)} attempts")
    return md


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--primary", required=True); ap.add_argument("--angle", default="")
    a = ap.parse_args()
    run(a.run_dir, a.primary, a.angle)
