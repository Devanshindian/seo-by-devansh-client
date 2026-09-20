"""The brand's reader personas, rendered for prompts. Generalized: reads the persona table in
projects/<company>/01-brand-context/persona.md (config.PERSONA_MD), so a new company only needs its
own persona.md — nothing here is Testlify-specific.

Reads: config.PERSONA_MD (a markdown table; each persona row starts "| **Name** | who | ...").
Exposes: block() -> the "- Name — who" lines used as {{PERSONAS}} in score-cards.md and cluster.md.
"""
import os
import re
import config

_FALLBACK = "- A practitioner making a real decision about what the brand offers (not an academic)."


def block():
    """One line per persona: '- Name — who they are'. Falls back to a generic reader line if the
    file is missing or the table can't be parsed (never crashes a run over a display block)."""
    if not os.path.exists(config.PERSONA_MD):
        return _FALLBACK
    lines = []
    for row in open(config.PERSONA_MD, encoding="utf-8").read().splitlines():
        m = re.match(r"\|\s*\*\*(.+?)\*\*\s*\|([^|]+)\|", row)
        if m:
            name = m.group(1).strip()
            who = " ".join(m.group(2).split()).strip()
            lines.append(f"- {name} — {who}")
    return "\n".join(lines) if lines else _FALLBACK
