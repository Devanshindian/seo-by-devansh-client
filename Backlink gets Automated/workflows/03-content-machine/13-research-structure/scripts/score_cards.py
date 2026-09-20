"""Step 1b — spine-relevance filter. Score every card against the article's SPINE (what it argues, for
whom — from the conductor's spine.json) and DROP the off-spine tail BEFORE clustering, so the blueprint
is article-scale (not an encyclopedia). This is the biggest lever on blueprint quality.

Rewritten 2026-08-03: the judge used to score "usefulness to the brand's reader", which let well-sourced
cards about NEIGHBOURING topics (skills-based hiring, assessment validity) sail into a resume-statistics
article — a perfect score on the wrong question. It now judges ONE test — does this card serve the SPINE —
and sees the spine / about / not-about lines plus each card's SOURCE (where a subject shares a word with a
different field, the source is often the only thing that reveals it). All four brand personas are shown
as context, and the Step-1a picked persona (available since 1a runs first) is named as the primary reader.

The card is the atomic unit (one idea each), so this deletes at the finest possible granularity. PROTECT
(never drop): the judge marked `protected` — the card carries a number / % / coefficient / threshold /
statistic, a sample item, or ties a specific named option to an outcome.

Reads: cards (list) + the article context (asset/angle/spine/about/not_about). Writes: dropped-cards.json
(audit). Returns: (kept_cards, report). Runs after harvest (Step 1) and before cluster (Step 2-3).
"""
import json, os, re
from concurrent.futures import ThreadPoolExecutor
import config, llm, personas

TEMPLATE = llm.load_prompt("score-cards.md")


def _card_line(c):
    txt = re.sub(r"\s+", " ", (c.get("verbatim") or c.get("gloss") or "")).strip()[:260]
    src = (c.get("source_urls") or [None])[0] or "-"
    return f"{c['id']} | {c.get('tag')} | {src} | {txt}"


def _score_batch(batch):
    """Score one batch. RAISES on failure — a crashed scorer must NOT silently default its cards to KEEP,
    or a broken run produces a bloated blueprint indistinguishable from a good one. llm.call_json already
    retries once internally, so an exception here is a real, repeated failure. run() aborts the whole step."""
    body = "\n".join(_card_line(c) for c in batch)
    prompt = (TEMPLATE.replace("{{ASSET}}", _A["asset"]).replace("{{ANGLE}}", _A["angle"])
              .replace("{{SPINE}}", _A["spine"]).replace("{{ABOUT}}", _A["about"])
              .replace("{{NOT_ABOUT}}", _A["not_about"]).replace("{{BRAND}}", config.BRAND_ONELINER)
              .replace("{{PERSONAS}}", _A["personas"]).replace("{{PERSONA}}", _A["persona"])
              .replace("{{CARDS}}", body))
    out = llm.call_json(prompt)
    rows = out.get("scores", []) if isinstance(out, dict) else out
    return {int(r["id"]): r for r in rows if isinstance(r, dict) and "id" in r}


_A = {"asset": "", "angle": "", "spine": "", "about": "", "not_about": "", "personas": "", "persona": ""}


def persona_str(persona):
    """Render the Step-1a picked persona dict into one prompt line; generic reader if the pick failed."""
    if isinstance(persona, dict) and (persona.get("name") or persona.get("lens")):
        name = (persona.get("name") or "").strip()
        lens = (persona.get("lens") or "").strip()
        return f"{name} — {lens}" if name and lens else (name or lens)
    return "A practitioner making a real decision about what the brand offers (not an academic)."


def _as_int(v):
    """Coerce a relevance value to int, or None if it isn't a clean integer. A non-integer must NOT slip
    through the `isinstance(rel, int)` guard and silently keep the card — it counts as unscored instead."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().lstrip("-").isdigit():
        return int(v.strip())
    return None


def run(cards, asset, angle, persona, spine_ctx, run_dir):
    """persona = the Step-1a picked reader (dict). spine_ctx = the conductor's spine.json dict
    ({spine, about, not_about}); empty dict on legacy runs."""
    spine_ctx = spine_ctx or {}
    _A.update({"asset": asset, "angle": (angle or asset),
               "spine": (spine_ctx.get("spine") or "").strip() or "(not available for this run)",
               "about": (spine_ctx.get("about") or "").strip() or "(not available for this run)",
               "not_about": (spine_ctx.get("not_about") or "").strip() or "(not available for this run)",
               "personas": personas.block(), "persona": persona_str(persona)})
    batches = [cards[i:i + config.SCORE_BATCH] for i in range(0, len(cards), config.SCORE_BATCH)]
    scores = {}
    # ex.map re-raises the first batch exception when iterated, so a failed batch aborts the whole step
    # (fail closed) rather than leaving its cards to default-KEEP. Non-zero exit is what the orchestrator wants.
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        for res in ex.map(_score_batch, batches):
            scores.update(res)

    kept, dropped, unscored = [], [], 0
    for c in cards:
        s = scores.get(c["id"], {})
        rel = _as_int(s.get("relevance"))
        if rel is None:
            unscored += 1                                        # judge omitted it / non-integer -> safe keep, but counted
        protected = bool(s.get("protected"))
        if not protected and rel is not None and rel <= config.SCORE_KEEP_THRESH:
            dropped.append({"id": c["id"], "tag": c.get("tag"), "gloss": c.get("gloss"),
                            "relevance": rel, "reason": s.get("reason", "")})
        else:
            kept.append(c)

    total = len(cards)
    pct = round(100 * len(dropped) / total, 2) if total else 0.0
    unscored_pct = round(100 * unscored / total, 2) if total else 0.0
    report = {
        "total_cards": total,
        "kept_count": len(kept),
        "dropped_count": len(dropped),
        "dropped_pct_of_cards": pct,
        "keep_threshold": config.SCORE_KEEP_THRESH,     # dropped if relevance <= this and not protected
        "unscored_count": unscored,                     # cards the judge never scored (kept as a safe default)
        "unscored_pct_of_cards": unscored_pct,
        "flag_threshold_pct": config.SCORE_FLAG_PCT,
        # FLAG fires on EITHER side: over-dropping (aggressive) OR too many unscored (the judge under-performed
        # or the scorer silently returned little) — both mean the filter can't be trusted this run.
        "FLAG": pct > config.SCORE_FLAG_PCT or unscored_pct > config.SCORE_FLAG_PCT,
        "dropped": sorted(dropped, key=lambda d: (d["relevance"], d["id"])),
    }
    config.write_json(os.path.join(run_dir, "dropped-cards.json"), report)
    if report["FLAG"]:
        print(f"    !! score_cards FLAG — dropped {pct}% · unscored {unscored_pct}% "
              f"(threshold {config.SCORE_FLAG_PCT}%)")
    return kept, report
