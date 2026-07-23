#!/usr/bin/env python3
"""Step 4 — read the live SERP for the primary keyword. Saves raw + a structured extract.
Pulls the AI Overview block here (reliable AEO signal) instead of the noisy llm_mentions.
Usage: python3 s4_serp.py <run_dir> "<primary keyword>"
"""
import os, sys, json
from collections import Counter
import dfs, config

def main():
    run, kw = sys.argv[1], sys.argv[2]
    proof = os.path.join(run, "proof"); os.makedirs(proof, exist_ok=True)
    resp = dfs.call("/v3/serp/google/organic/live/advanced", [{
        "keyword": kw, "location_name": config.LOCATION, "language_code": config.LANGUAGE,
        "depth": config.SERP_DEPTH, "people_also_ask_click_depth": config.PAA_CLICK_DEPTH,
        "load_async_ai_overview": True}])
    config.write_json(f"{proof}/04-serp.json", resp)
    items = dfs.first_result(resp).get("items") or []

    top = [{"rank": i.get("rank_group"), "domain": i.get("domain"), "title": i.get("title"),
            "url": i.get("url")} for i in items if i.get("type") == "organic"][:10]
    snippet, paa, ai_ov, related = None, [], None, []
    for i in items:
        t = i.get("type")
        if t == "featured_snippet":
            snippet = {"domain": i.get("domain"), "text": i.get("description") or i.get("title")}
        elif t == "people_also_ask":
            paa = [e.get("title") for e in (i.get("items") or []) if e.get("title")]
        elif t == "ai_overview":
            txt = " ".join((e.get("text") or "") for e in (i.get("items") or []))
            refs = [r.get("domain") for r in (i.get("references") or []) if r.get("domain")]
            ai_ov = {"text": txt.strip(), "cites": refs}
        elif t == "related_searches":
            related += (i.get("items") or [])

    extract = {"keyword": kw, "features": dict(Counter(i.get("type") for i in items)),
               "top_organic": top, "featured_snippet": snippet, "paa": paa,
               "ai_overview": ai_ov, "related_searches": related}
    config.write_json(f"{proof}/04-serp-extract.json", extract)

    print(f"cost noted in raw | features: {extract['features']}")
    print("top organic:")
    for r in top[:6]:
        print(f"  {r['rank']}. {str(r['domain'])[:30]:<30} {str(r['title'])[:44]}")
    print(f"featured snippet: {snippet['domain'] if snippet else 'none'}")
    print(f"AI Overview: {'present, cites ' + ', '.join(ai_ov['cites'][:6]) if ai_ov else 'absent'}")
    print("PAA:", paa[:6])
    print(f"saved -> {proof}/04-serp.json, 04-serp-extract.json")

if __name__ == "__main__":
    main()
