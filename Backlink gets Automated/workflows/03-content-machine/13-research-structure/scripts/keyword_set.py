"""Step 8b — extract the consolidated KEYWORD-SET from the DataForSEO brief.
Pulls primary + variations + secondaries + in-body into a clean structured set so the write-phase
keyword-coverage check has a list to verify the draft against. (Variations are now their own subsection in
the brief; for older briefs the prompt still recovers them from the Primary entry's prose.)

Reads: the brief (dataforseo/out/<slug>/research-doc-<slug>.md). Writes: keyword-set.json
  { primary, variations[], secondaries[], in_body[] }.  Returns the dict.
"""
import os, sys, json
import config, llm

TEMPLATE = llm.load_prompt("keyword-set.md")


def _brief_path(slug):
    return os.path.join(config.DFS_RUNS, slug, f"research-doc-{slug}.md")


def run(slug, run_dir, sections=None, brief_path=None):
    path = brief_path or _brief_path(slug)
    md = open(path, encoding="utf-8").read()
    raw = llm.call_json(TEMPLATE.replace("{{BRIEF_TEXT}}", md))
    ks = {
        "primary": (raw.get("primary") or "").strip(),
        "variations": raw.get("variations") or [],
        "secondaries": raw.get("secondaries") or [],
        "in_body": raw.get("in_body") or [],
    }
    # ALSO capture the per-H2 keywords (bottom-up, found from each heading in Step 6) — deduped, with vol/KD.
    # So the keyword-set = the brief's top-down picks PLUS what the headings actually target.
    h2, seen = [], set()
    for s in (sections or []):
        tk = s.get("target_keyword") or {}
        kw = (tk.get("keyword") or "").strip()
        if kw and kw.lower() not in seen:
            seen.add(kw.lower())
            h2.append({"keyword": kw, "volume": tk.get("volume"), "kd": tk.get("kd")})
    ks["h2_keywords"] = h2
    config.write_json(os.path.join(run_dir, "keyword-set.json"), ks)
    print(f"  keyword-set: primary='{ks['primary']}' · {len(ks['variations'])} variations · "
          f"{len(ks['secondaries'])} brief-secondaries · {len(ks['h2_keywords'])} per-H2 keywords · {len(ks['in_body'])} in-body")
    return ks


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1], sys.argv[2]), indent=2))
