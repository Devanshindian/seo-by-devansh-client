"""The article BRIEF — our addition (2026-08-03), not Stanford's.

One process-wide registry holding the article context STORM is being run for: title, distinct angle,
working spine, and the about / not-about world lines (built upstream by the conductor's spine step and
passed in by scripts/run_storm.py via --spine-file).

Why a registry and not function arguments: the engine's module chain (engine.run -> knowledge curation ->
conv simulator -> question asker, and the outline/section writers) is Stanford's code; threading five new
parameters through every signature would touch a dozen call sites of vendored code. One explicit
set-once/read-many module keeps our diff small. A CLI run is one process, one topic, so a module global is
safe here.

Backwards compatible: when set_brief() was never called (a bare `run_storm.py "topic"` run), get_block()
returns "" and every prompt behaves as before.
"""

_BRIEF = {}


def set_brief(title="", angle="", spine="", about="", not_about="", brand="", about_brand=""):
    """Store the article context for this run. Called once by run_storm.py before the runner starts.
    brand / about_brand (the company and its one-liner) are used only by the researcher picker."""
    global _BRIEF
    _BRIEF = {"title": (title or "").strip(), "angle": (angle or "").strip(),
              "spine": (spine or "").strip(), "about": (about or "").strip(),
              "not_about": (not_about or "").strip(),
              "brand": (brand or "").strip(), "about_brand": (about_brand or "").strip()}


def get_brief():
    """The raw fields (empty dict when no brief was set)."""
    return dict(_BRIEF)


def has_brief():
    # brand/about_brand alone don't make a brief — the article fields do
    return any(_BRIEF.get(k) for k in ("title", "angle", "spine", "about", "not_about"))


def get_block(heading="THE ARTICLE THIS RESEARCH IS FOR"):
    """The formatted context block pasted into the question / outline / section prompts.
    Empty string when no brief was set, so legacy runs are untouched."""
    if not has_brief():
        return ""
    b = _BRIEF
    lines = [heading]
    if b["title"]:
        lines.append(f"- Title: {b['title']}")
    if b["angle"]:
        lines.append(f"- Distinct angle: {b['angle']}")
    if b["spine"]:
        lines.append(f"- The spine (what this article argues, for whom, what the reader can do at the end): {b['spine']}")
    if b["about"]:
        lines.append(f"- What this is about: {b['about']}")
    if b["not_about"]:
        lines.append(f"- What this is NOT about: {b['not_about']}")
    return "\n".join(lines)
