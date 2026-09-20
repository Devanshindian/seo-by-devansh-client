"""Step 8b — the consolidated KEYWORD SET, so the write phase can later check the article covers it.

PURE CODE since 2026-08-04. This used to pay an AI to re-read the brief's markdown "## Keywords" section —
but DataForSEO already saves the exact same fields as clean JSON (proof/03-final.json), so the round trip
(JSON → rendered markdown → AI reads it back into JSON) was one paid call that could only ever drift from
its own source. Now: open the JSON, flatten, done.

h2_keywords is GONE from the set (same date): the per-H2 keyword step bought keywords for the research
blueprint's headings, which the architect redesigns away — real per-section keywords are the architect's
job, done after the real sections exist.

Reads:  <dfs run>/proof/03-final.json (hub-aware). Writes: nothing of its own (the orchestrator snapshots).
Returns: { primary, variations[], secondaries[], in_body[] } — all plain strings, same shape as before.
"""
import os, sys, json
import config


def _kw(x):
    """A keyword entry may be a dict {keyword, volume, kd} or a bare string — return the string."""
    if isinstance(x, dict):
        return str(x.get("keyword") or "").strip()
    return str(x or "").strip()


def run(slug, run_dir, sections=None, brief_path=None, hub=""):
    """sections is accepted (and ignored) for call-site compatibility; brief_path overrides for testing."""
    path = brief_path or os.path.join(config.DFS_RUNS, hub, slug, "proof", "03-final.json")
    final = json.load(open(path))
    ks = {
        "primary": _kw(final.get("primary")),
        "variations": [k for k in (_kw(v) for v in (final.get("variations") or [])) if k],
        "secondaries": [k for k in (_kw(v) for v in (final.get("secondary") or [])) if k],
        "in_body": [k for k in (_kw(v) for v in (final.get("in_body") or [])) if k],
    }
    # dedupe, preserving order, and never let the primary appear again in another list
    seen = {ks["primary"].lower()} if ks["primary"] else set()
    for key in ("variations", "secondaries", "in_body"):
        out = []
        for k in ks[key]:
            if k.lower() not in seen:
                seen.add(k.lower())
                out.append(k)
        ks[key] = out
    print(f"  keyword-set (from 03-final.json): primary={ks['primary']!r} · "
          f"{len(ks['variations'])} variations · {len(ks['secondaries'])} secondaries · {len(ks['in_body'])} in-body")
    return ks


if __name__ == "__main__":
    slug = sys.argv[1]
    hub = sys.argv[2] if len(sys.argv) > 2 else ""
    print(json.dumps(run(slug, "", hub=hub), indent=2))
