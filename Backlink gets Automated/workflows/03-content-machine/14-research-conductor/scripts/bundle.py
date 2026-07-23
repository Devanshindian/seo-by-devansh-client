#!/usr/bin/env python3
"""Step 5 — the write-ready bundle assembler. Packages one topic's handoff for the (AI) writer:
copies the blueprint in, picks the reader persona + author byline, and writes a Markdown cover sheet that
points to the shared brand constants. Blueprint COPIED; everything else POINTED-TO (single source of truth).

Reads:  research-structure/out/<slug>/structure-<slug>.json (carries the persona picked upstream) + voices.md
        (+ persona.md only on the fallback path, when a blueprint has no persona).
Writes: research-bundle/<slug>/bundle-<slug>.md + structure-<slug>.json (copied).

Persona is picked ONCE upstream (research-structure Step 1a) and embedded in the blueprint; this step REUSES it
and only decides the author (single source of truth). If an old blueprint has no persona, it falls back to
picking both here.
"""
import os, sys, json, shutil, argparse, csv, re
import config, llm

csv.field_size_limit(1 << 24)


def _queue_row(slug):
    """The idea's research-log row — carries the write-phase signals (target_words / format / reuse_verdict)."""
    try:
        with open(config.LOG_CSV, newline="") as f:
            return next((r for r in csv.DictReader(f) if r.get("slug") == slug), {})
    except FileNotFoundError:
        return {}


# The word-target has two candidate sources that can DISAGREE (F1 — decide it once, name the authority):
#   1. clubbed '# words' (queue.target_words) — a coarse asset-engine estimate (median len of ranking pages, taken
#      once, cluster-wide).
#   2. DataForSEO's build-spec **Word band** — computed PER TOPIC from the live SERP the day we researched it.
# Devansh's call (2026-07-23): DataForSEO WINS — it actually looked at this keyword's current SERP. So the bundle
# surfaces the DFS band as the target, and only falls back to the clubbed median if the brief has no band.
# Tolerant of markdown around the label ('**Word band:**', '**Word band**:', 'Word band -') — match the phrase,
# skip any non-digit run, then capture the 'N,NNN-N,NNN' range.
_WORD_BAND_RE = re.compile(r"Word band[^\d]{0,12}([\d,]{3,})\s*(?:-|–|—|to)\s*([\d,]{3,})", re.I)


def _hub(slug):
    """The pillar slug for a spoke (from its queue row's 'spoke-of:' source), or '' for a hub. Every engine's
    output nests under this for a spoke — so all of them (dataforseo/gap-check/storm/structure/bundle) agree."""
    src = (_queue_row(slug).get("source") or "")
    return src.split("spoke-of:", 1)[1].strip() if "spoke-of:" in src else ""


def _dfs_word_band(slug):
    """The authoritative word target: DataForSEO's build-spec band (live-SERP read). Returns 'min-max' or ''."""
    try:
        with open(os.path.join(config.DFS_OUT, _hub(slug), slug, f"research-doc-{slug}.md")) as f:
            m = _WORD_BAND_RE.search(f.read())
        return f"{m.group(1)}-{m.group(2)}" if m else ""
    except Exception:
        return ""


def _bundle_dir(slug):
    """Where this topic's bundle lands. A SPOKE nests under its pillar: research-bundle/<hub-slug>/<spoke-slug>/;
    a hub/normal idea stays flat: research-bundle/<slug>/. (Hub found from the queue row's 'spoke-of:' source.)"""
    hub = _hub(slug)
    return os.path.join(config.BUNDLE_OUT, hub, slug) if hub else os.path.join(config.BUNDLE_OUT, slug)

PICK = llm.load_prompt("pick-persona-author.md")   # fallback: pick BOTH (old blueprint with no persona)
PICK_AUTHOR = llm.load_prompt("pick-author.md")    # normal path: persona already decided upstream


def _read(path):
    return open(path).read() if os.path.exists(path) else ""


def _rel(p):
    """Path relative to the repo root — stable + readable in the cover sheet."""
    return os.path.relpath(p, config.REPO_ROOT)


def pick_persona_author(asset, angle):
    """FALLBACK only (old blueprint with no persona): pick BOTH persona + author from the docs."""
    p = (PICK.replace("{{BRAND}}", config.BRAND)
         .replace("{{ASSET_TITLE}}", asset).replace("{{ANGLE}}", angle or "")
         .replace("{{PERSONA_DOC}}", _read(os.path.join(config.BRAND_CTX, "persona.md")))
         .replace("{{VOICES_DOC}}", _read(os.path.join(config.BRAND_CTX, "voices.md"))))
    out = llm.call_json(p)
    print(f"  persona (picked here — no upstream): {out.get('persona',{}).get('name')} · author: {out.get('author',{}).get('display_name')}")
    return out


def pick_author(asset, angle):
    """Normal path: the persona is already decided upstream — only route the author (voices.md 'Auto-route')."""
    p = (PICK_AUTHOR.replace("{{BRAND}}", config.BRAND)
         .replace("{{ASSET_TITLE}}", asset).replace("{{ANGLE}}", angle or "")
         .replace("{{VOICES_DOC}}", _read(os.path.join(config.BRAND_CTX, "voices.md"))))
    return llm.call_json(p)


def _picks_for(slug, asset, angle):
    """Reuse the persona picked upstream (in the blueprint); pick only the author. Fallback: pick both."""
    src = os.path.join(config.STRUCT_OUT, _hub(slug), slug, f"structure-{slug}.json")
    persona = {}
    if os.path.exists(src):
        persona = (json.load(open(src)).get("persona") or {})
    if persona.get("name"):
        author = pick_author(asset, angle)
        print(f"  persona (reused from blueprint): {persona.get('name')} · author: {author.get('display_name')}")
        return {"persona": persona, "author": author}
    return pick_persona_author(asset, angle)      # fallback for a blueprint with no persona


def _cover_sheet(slug, asset, angle, picks):
    ctx = config.BRAND_CTX
    j = os.path.join
    dfs = j(config.DFS_OUT, _hub(slug), slug)                        # this topic's DataForSEO run dir (nested for spokes)
    blueprint = _rel(j(_bundle_dir(slug), f"structure-{slug}.json"))   # the copied-in plan, real path (nested for spokes)
    persona = picks.get("persona", {}) or {}
    author = picks.get("author", {}) or {}
    # write-phase signals carried from the clubbed idea (via the research-log row)
    q = _queue_row(slug)
    tw = (q.get("target_words") or "").strip()
    fmt = (q.get("format") or "").strip()
    verdict = (q.get("reuse_verdict") or "").strip()
    chosen = (q.get("chosen_links") or "").strip()
    dfs_band = _dfs_word_band(slug)   # AUTHORITATIVE (live-SERP band); beats the clubbed median if present
    if dfs_band:
        word_line = (f"- **Target length: {dfs_band} words** — DataForSEO's live-SERP band for THIS keyword (the"
                     f" authoritative target: it read the pages actually ranking now). A GUIDE, not a floor —"
                     f" cover the topic fully; don't pad to hit it.")
    elif tw:
        word_line = (f"- **Target length: ~{tw} words** — median length of ranking pages (asset-engine estimate;"
                     f" no live-SERP band on file). A GUIDE, not a floor.")
    else:
        word_line = ""
    fmt_line = f"- **Format (write it in this shape):** {fmt}" if fmt else ""
    reuse_line = (f"- ⚠️ **Improve existing** — this UPGRADES an existing page, not a new article. Extend / refresh"
                  f" / re-angle THIS page: {chosen}") if verdict == "Improve existing" and chosen else \
                 (f"- Reuse verdict: {verdict}" if verdict else "")
    cann = (q.get("cannibalization") or "").strip()
    cann_url = (q.get("cannibalization_url") or "").strip()
    cann_line = (f"- ⚠️ **Cannibalisation — TEAM SHOULD KNOW:** we already rank for '{cann}' via {cann_url}."
                 f" Building anyway; this article must clearly outperform that page.") if cann else ""
    _extra = [l for l in (fmt_line, word_line, reuse_line, cann_line) if l]  # only the ones that apply (keeps blank spacers intact)
    return "\n".join([
        f"# Research bundle — {asset.split(':')[0].strip()}", "",
        "> Everything to write this article. Division 1 is the plan (WHAT to write); the rest is HOW.", "",
        f"**Title:** {asset}",
        f"**Distinct angle:** {angle}", "",
        "**This article at a glance**",
        f"- Slug: `{slug}`",
        *_extra,
        f"- Reader persona (write TO this depth/angle — never name them): **{persona.get('name','')}**"
        f"  → full lens: {_rel(j(ctx,'persona.md'))}",
        f"- Author byline: **{author.get('display_name','')}** — `{author.get('byline_line','')}`"
        f"  → voice detail: {_rel(j(ctx,'voices.md'))}", "",
        "---", "",
        "## Orientation (who this is for — write in this frame)",
        f"**{config.BRAND}** — {config.TENANT.get('brand_oneliner', '')}",
        f"On-topic scope: {config.TENANT.get('niche_definition', '')}." if config.TENANT.get('niche_definition') else "",
        "Write as this company, to its audience; never name the reader persona in the article.", "",
        "---", "",
        "## 1. The plan (your article skeleton) — COPIED IN",
        f"**File:** `{blueprint}`",
        "headings · per-H2 keywords · evidence · internal/external links · FAQ · write_guidance", "",
        f"## 2. Voice → `{_rel(j(ctx,'brand-voice.md'))}`",
        f"## 3. Style & mechanics → `{_rel(j(ctx,'style-guide.md'))}`",
        f"## 4. Product facts → `{_rel(j(ctx,'features.md'))}`",
        f"## 5. SEO/AEO/GEO checklist → `{_rel(config.SEO_CHECKLIST)}`",
        f"## 6. Cite-from material → `{_rel(j(ctx,'stats.md'))}` · `{_rel(j(ctx,'opinions.md'))}` · `{_rel(j(ctx,'stories.md'))}`",
        f"## 7. Worked examples → `{_rel(j(ctx,'writing-examples.md'))}`",
        f"## 8. Writing integrity → `{_rel(j(ctx,'writing-integrity.md'))}`",
        f"## 9. Anti-AI writing check → `{_rel(config.AVOID_AI)}`", "",
        "## 10. DataForSEO research detail (open for depth the blueprint doesn't fully carry)",
        f"### SERP snapshot → `{_rel(j(dfs, 'proof', '04-serp-snapshot.md'))}`",
        "who ranks · featured-snippet target · AI-Overview skeleton + who it cites (GEO gap) · PAA on/off-angle · related searches + demand signals", "",
        f"### What the winners cover → `{_rel(j(dfs, 'proof', '05-winners.md'))}`",
        "competitor format + depth · common H2s · where winners drift · gaps we can own", "",
        f"### Full brief → `{_rel(j(dfs, f'research-doc-{slug}.md'))}`",
        "verdict · full keyword rationale · build spec (word band · primary sources to cite · snippet target · close/CTA)",
        "",
    ])


def run(slug, asset, angle):
    out = _bundle_dir(slug)                                  # nested under the pillar for spokes; flat for hubs
    os.makedirs(out, exist_ok=True)
    src = os.path.join(config.STRUCT_OUT, _hub(slug), slug, f"structure-{slug}.json")
    if not os.path.exists(src):
        sys.exit(f"  ! no blueprint at {src} — run the research steps first")
    shutil.copy(src, os.path.join(out, f"structure-{slug}.json"))     # the ONLY copied file
    picks = _picks_for(slug, asset, angle)
    config.write_text(os.path.join(out, f"bundle-{slug}.md"), _cover_sheet(slug, asset, angle, picks))
    print(f"  -> {_rel(out)}/  (bundle-{slug}.md + structure-{slug}.json)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="build the full bundle for this slug (needs an existing blueprint)")
    ap.add_argument("--asset", required=True)
    ap.add_argument("--angle", default="")
    a = ap.parse_args()
    if a.slug:
        run(a.slug, a.asset, a.angle)
    else:
        print(json.dumps(_picks_for("_test_", a.asset, a.angle), indent=2))   # picker-only test mode (falls back to picking both)
