#!/usr/bin/env python3
"""Step 0 — classify THIS company's page types by role (the generalization fix, Devansh 2026-07-19).

Type NAMES differ per CMS ("successstory" vs "case-studies") — so no script may hardcode them. The
script summarises each type (count + sample titles/URLs); the LLM judges what each type HOLDS
(criteria in prompts/classify-types.md); the roles are saved once per company and every candidate
filter reads them.

Reads:  CATALOGUE_CSV.
Writes: BRAND_CTX/_work/type-roles.json  {"stat_types": [...], "story_types": [...],
        "commercial_types": [...], "editorial_types": [...], "notes": "..."}
Shared: 0-brand-facts' draft steps AND 1-brand-voice's shortlist read this file.
"""
import csv, json, os, sys, collections
import config, llm

csv.field_size_limit(sys.maxsize)
ROLES_PATH = os.path.join(config.BRAND_CTX, "_work", "type-roles.json")


def _type_table():
    with open(config.CATALOGUE_CSV, newline="", encoding="utf-8", errors="replace") as f:
        rows = [r for r in csv.DictReader(f) if r.get("body_status") == "ok"]
    by = collections.defaultdict(list)
    for r in rows:
        by[r.get("Type", "")].append(r)
    lines = []
    for t, grp in sorted(by.items(), key=lambda kv: -len(kv[1])):
        samples = "; ".join(f"\"{g.get('Title','')[:60]}\" ({g['URL'][:70]})" for g in grp[:3])
        lines.append(f"- {t} · {len(grp)} pages · samples: {samples}")
    return "\n".join(lines)


def run(redo=False):
    if os.path.exists(ROLES_PATH) and not redo:
        roles = json.load(open(ROLES_PATH))
        print(f"   type roles exist -> {ROLES_PATH} (stat:{roles.get('stat_types')} story:{roles.get('story_types')})")
        return roles
    roles = llm.call_json(llm.load_prompt("classify-types.md")
                          .replace("{{BRAND}}", config.BRAND).replace("{{NICHE}}", config.NICHE)
                          .replace("{{TYPES}}", _type_table()))
    for key in ("stat_types", "story_types", "commercial_types", "editorial_types"):
        roles.setdefault(key, [])
    config.write_text(ROLES_PATH, json.dumps(roles, indent=2))
    print(f"   classified -> {ROLES_PATH}")
    print(f"     stat: {roles['stat_types']}\n     story: {roles['story_types']}\n     commercial: {roles['commercial_types']}")
    if roles.get("notes"):
        print(f"     note: {roles['notes']}")
    return roles


def load():
    """The roles for THIS company, or None — callers fall back to config defaults and SAY SO."""
    return json.load(open(ROLES_PATH)) if os.path.exists(ROLES_PATH) else None


if __name__ == "__main__":
    run(redo="--redo" in sys.argv)
