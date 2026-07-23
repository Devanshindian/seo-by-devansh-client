"""Step 4c — re-decide is_differentiator ONCE per final section, WITH context the clustering flag never sees.

The flag set during clustering is unreliable (over-applied): the cluster prompt sees only card glosses — never
the asset angle or what competitors cover — and the two-level merge OR-accumulates flags, so it only ever piles
up. This step supersedes it: given the asset's distinct angle + the competitor-covered topics + the gaps we can
own (from the competitor/gap-tagged cards), it re-decides each final section's flag authoritatively (single
source of truth for the flag; kills the blind OR-ratchet).

Reads: sections (named) + cards (for competitor/gap glosses) + the asset angle.
Writes: differentiator-audit.json (audit). Returns: sections with is_differentiator overwritten.
Runs after Step 4 (name) and before Step 5 (attach).
"""
import os, json
import config, llm

TEMPLATE = llm.load_prompt("redecide-differentiator.md")


def run(sections, cards, angle, run_dir):
    competitor = sorted({c["gloss"] for c in cards if c.get("tag") == "competitor" and c.get("gloss")})
    gaps = sorted({c["gloss"] for c in cards if c.get("tag") == "gap" and c.get("gloss")})

    sec_lines = []
    for i, s in enumerate(sections):
        h3s = " | ".join(h["h3"] for h in s.get("h3", []))
        sec_lines.append(f"[{i}] {s['h2']}\n      sub-headings: {h3s}")

    prompt = (TEMPLATE.replace("{{ANGLE}}", angle or "(not specified — judge on the title's intent)")
              .replace("{{COMPETITOR_TOPICS}}", "\n".join("- " + c for c in competitor) or "(none captured)")
              .replace("{{GAPS}}", "\n".join("- " + g for g in gaps) or "(none captured)")
              .replace("{{SECTIONS}}", "\n".join(sec_lines)))
    # On total failure we do NOT silently keep the unreliable clustering flags with no trace. Every section is
    # stamped `diff_source`: "redecided" (this authoritative judge decided it) or "cluster-fallback" (we kept the
    # old OR-ratchet flag because the judge didn't cover it). A run where the whole call failed is loud + visibly
    # all-fallback in the audit, so a downstream reader can distinguish a trusted flag from a degraded one. [A#18]
    try:
        out = llm.call_json(prompt) or {}
        verdicts = {r["index"]: r for r in out.get("sections", []) if isinstance(r, dict) and "index" in r}
        call_ok = True
    except Exception as e:
        print(f"    !! differentiator re-decision FAILED ({str(e)[:80]}) — every section falls back to the "
              f"UNRELIABLE clustering flag (marked diff_source=cluster-fallback)")
        verdicts, call_ok = {}, False

    changed = fallback = 0
    for i, s in enumerate(sections):
        if i in verdicts:
            newv = bool(verdicts[i].get("is_differentiator"))
            if newv != bool(s.get("is_differentiator")):
                changed += 1
            s["is_differentiator"] = newv
            s["diff_source"] = "redecided"
        else:
            s["diff_source"] = "cluster-fallback"       # judge didn't cover it -> old flag stands, flagged as such
            fallback += 1

    n_diff = sum(1 for s in sections if s.get("is_differentiator"))
    config.write_json(os.path.join(run_dir, "differentiator-audit.json"),
                      {"angle": angle, "call_ok": call_ok, "fallback_sections": fallback,
                       "competitor_topics": competitor, "gaps": gaps, "verdicts": out.get("sections", [])})
    tail = f" · {fallback} on cluster-fallback" if fallback else ""
    print(f"  differentiators re-decided: {n_diff}/{len(sections)} ({changed} flipped{tail}) "
          f"-> differentiator-audit.json")
    return sections
