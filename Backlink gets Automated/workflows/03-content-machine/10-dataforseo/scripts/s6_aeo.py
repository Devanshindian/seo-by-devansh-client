#!/usr/bin/env python3
"""Step 6 — AEO: what AI answers + who it cites, via llm_mentions search.
Usage: python3 s6_aeo.py <run_dir> "<topic keyword>" "<match_type>"    (match_type picked by s6_flow.py)
Note (from the topic-2 run): llm_mentions is often noisy on niche topics. The AI Overview captured by
s4_serp.py (proof/04-serp-extract.json) is usually the more reliable AEO signal — cross-check both.
"""
import os, sys, json
from collections import Counter
import dfs, config

def dom(u):
    u = str(u)
    return u.split("/")[2] if "//" in u else u

def main():
    run, kw = sys.argv[1], sys.argv[2]
    match_type = sys.argv[3] if len(sys.argv) > 3 else "phrase_match"   # 6a chooses this; default tightened from word_match
    proof = os.path.join(run, "proof"); os.makedirs(proof, exist_ok=True)
    resp = dfs.call("/v3/ai_optimization/llm_mentions/search/live", [{
        "target": [{"keyword": kw, "match_type": match_type}],
        "platform": "chat_gpt", "limit": 15, "order_by": ["ai_search_volume,desc"]}])
    config.write_json(f"{proof}/06-aeo.json", resp)
    items = dfs.first_result(resp).get("items") or []
    questions, cites, fan_out = [], Counter(), []
    for it in items:
        q = it.get("keyword") or it.get("question")
        if q: questions.append({"q": q, "ai_search_volume": it.get("ai_search_volume")})
        for s in (it.get("sources") or []):
            cites[dom(s.get("url") or s.get("domain") or "")] += 1
        fan_out += (it.get("fan_out_queries") or [])
    # "Are WE cited?" is a DOMAIN question, not a brand-name question: match the company's own domain
    # (config.DOMAIN) against the cited domains. The old check substring-matched the brand word, which only
    # worked when brand == domain (true for testlify, false in general). [revamp Phase 1.4]
    own = config.DOMAIN.lower().lstrip("www.")
    extract = {"keyword": kw, "questions": questions[:15],
               "cited_domains": cites.most_common(10),
               "fan_out": list(dict.fromkeys(fan_out))[:15],
               "brand_cited": any(d.lower().endswith(own) for d in cites)}
    config.write_json(f"{proof}/06-aeo-extract.json", extract)
    print(f"query='{kw}' match_type={match_type} | AI questions: {len(questions)} | {config.DOMAIN} cited? {extract['brand_cited']}")
    print("cited domains:", extract["cited_domains"][:6])
    print("sample questions:", [q['q'] for q in questions[:6]])
    print(f"saved -> {proof}/06-aeo.json, 06-aeo-extract.json")

if __name__ == "__main__":
    main()
