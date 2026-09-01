"""THE ARTICLE CONTEXT — title, angle, spine, persona, and the world (about / not_about), from their owners.

One shared reader (2026-08-04) so the planner, the architect and anything later all judge against the SAME
statement of what this article is and is not. Before this, each step re-derived what it needed and the
world reached almost nothing.

  title + angle   -> the topic queue row (the source every other step already uses)
  spine           -> the ARCHITECT's structure.json once shape has run; before that, the RESEARCH spine
                     from spine.json. The research spine exists from the research phase's Step 2a, so the
                     planner has one too.
  about/not_about -> the research spine.json, next to the dossier. Decided at Step 0b, BEFORE DataForSEO,
                     so it is available to every consumer downstream without exception.
  persona         -> planner/article-plan.json + the company's persona.md. Added here 2026-08-08; see
                     persona() below for why the architect had been running blind to the reader.

Every field degrades to "" rather than raising: a legacy run with no spine.json still works, and callers
fill their prompts with "(not available for this run)".
"""
import json
import os

import config
import fmt_router


def article_context(slug, st=None):
    """Returns {title, angle, spine, about, not_about} — all plain strings, never None."""
    row = fmt_router._queue_row(slug) or {}

    if st is None:                                  # the architect's structure, if it exists yet
        try:
            st = json.load(open(config.artifact(slug, "structure.json")))
        except Exception:
            st = {}

    world = {}
    p = os.path.join(config.STORM_OUT, slug, "spine.json")
    if os.path.exists(p):
        try:
            world = json.load(open(p))
        except Exception:
            world = {}

    return {"title": (row.get("asset") or st.get("h1") or "").strip(),
            "angle": (row.get("angle") or "").strip(),
            "spine": (st.get("spine") or world.get("spine") or "").strip(),
            "about": (world.get("about") or "").strip(),
            "not_about": (world.get("not_about") or "").strip(),
            "persona": persona(slug)}


def or_na(ctx, key):
    """The prompt-ready value: the real text, or an explicit '(not available for this run)'."""
    return ctx.get(key) or "(not available for this run)"


def persona(slug):
    """WHO the article is for, prompt-ready. The chosen persona from article-plan.json plus its row in
    the company's persona.md when we can match one.

    Moved here 2026-08-08 (it lived privately inside write_body.py). The persona sat in the very file
    the ARCHITECT reads and no architect step ever looked at it, so the step that decides which
    sections exist was blind to the reader. That is how an article for hiring managers ended up with
    sections written for candidates — "Tell Me About Yourself", "How to Answer 'Tell Me About a Time
    You Received Feedback'" — which the reviewer caught. One owner now, read by both engines.
    """
    try:
        plan = json.load(open(config.artifact(slug, "article-plan.json")))
    except Exception:
        return "(general professional reader)"
    p = plan.get("persona") or {}
    name = (p.get("name") or "").strip() if isinstance(p, dict) else str(p)
    lens = (p.get("lens") or "").strip() if isinstance(p, dict) else ""
    row = ""
    pf = config.brand_file("persona.md")
    if name and os.path.exists(pf):
        for line in open(pf):
            if line.strip().startswith("|") and name.lower() in line.lower():
                row = line.strip()
                break
    return "\n".join(x for x in [f"{name} — {lens}" if lens else name, row] if x) or "(general professional reader)"
