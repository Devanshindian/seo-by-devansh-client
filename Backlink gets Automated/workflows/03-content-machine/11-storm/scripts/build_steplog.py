"""Render STORM's llm_call_history.jsonl into a human-readable step-by-step log.
Each LLM call = one step; we label it by the prompt so you can see exactly what STORM did.
Usage: python build_steplog.py <run_dir>
"""
import sys, os, json

def label(p):
    p = (p or "").lower()
    if "what do you type in the search box" in p or ("search" in p and "queries" in p and "google" in p):
        return "SEARCH QUERY — expert turns the question into Google queries"
    if "persona" in p or ("perspective" in p and ("identify" in p or "list" in p or "generate" in p)):
        return "PERSPECTIVES — generate the different viewpoints/personas"
    if "related" in p and ("wikipedia" in p or "topic" in p):
        return "RELATED TOPICS — find similar pages to seed perspectives"
    if "you are an experienced wikipedia writer and want to edit" in p or "ask the next question" in p or ("ask" in p and "question" in p and "conversation" in p):
        return "ASK — the writer (in a persona) asks the expert a question"
    if "you are an expert" in p or "gather information" in p or "answer the question" in p or ("use the information" in p and "answer" in p):
        return "ANSWER — the grounded expert answers from search results"
    if "write an outline" in p or "table of contents" in p or ("outline" in p and "wikipedia" in p):
        return "OUTLINE — build the article outline"
    if "write a wikipedia section" in p or "write the section" in p or ("section" in p and "write" in p):
        return "WRITE SECTION — write one section with citations"
    if "lead section" in p or "polish" in p or "summarize the" in p or "summary of the" in p:
        return "POLISH — write lead/summary, dedupe"
    return "LLM step"

def firstq(prompt):
    # try to surface the actual question/instruction, not the giant boilerplate
    lines = [l.strip() for l in (prompt or "").split("\n") if l.strip()]
    # prefer a line ending with '?' near the end (the real question)
    qs = [l for l in lines if l.endswith("?")]
    if qs:
        return qs[-1][:220]
    return (lines[0] if lines else "")[:220]

def main(run_dir):
    hist = os.path.join(run_dir, "llm_call_history.jsonl")
    if not os.path.exists(hist):
        print("no history in", run_dir); return
    rows = [json.loads(l) for l in open(hist).read().splitlines() if l.strip()]
    tot_pt = sum((r.get("usage") or {}).get("prompt_tokens", 0) for r in rows)
    tot_ct = sum((r.get("usage") or {}).get("completion_tokens", 0) for r in rows)
    out = [f"# STORM step-by-step log", f"**Run:** {os.path.basename(run_dir)}",
           f"**Total LLM steps (Claude calls):** {len(rows)}  ·  approx tokens in/out: {tot_pt}/{tot_ct}",
           "", "Each step below is one Claude call the shim answered. Labelled by what STORM was doing.", "", "---", ""]
    from collections import Counter
    phases = Counter()
    for i, r in enumerate(rows, 1):
        prompt = r.get("prompt", "")
        outs = r.get("outputs") or []
        got = (outs[0] if outs else "")
        lab = label(prompt)
        phases[lab.split(" —")[0]] += 1
        out.append(f"### Step {i} — {lab}")
        out.append(f"- **Asked:** {firstq(prompt)}")
        out.append(f"- **Got:** {str(got)[:500].strip()}")
        out.append("")
    # phase summary at top
    summ = ["## Phase summary"] + [f"- {k}: {v} calls" for k, v in phases.most_common()] + ["", "---", ""]
    out = out[:6] + summ + out[6:]
    dest = os.path.join(run_dir, "STEP-LOG.md")
    open(dest, "w").write("\n".join(out))
    print("wrote", dest, "with", len(rows), "steps")

if __name__ == "__main__":
    main(sys.argv[1])
