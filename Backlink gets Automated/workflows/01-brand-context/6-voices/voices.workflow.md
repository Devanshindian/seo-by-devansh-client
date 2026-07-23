---
type: workflow-recipe
stage: content-machine (Stage 0 — brand context)
reusable: any company
reads:
  - projects/[company]/01-brand-context/brand-voice.md   # tone/voice reference for drafting bios (optional)
produces:
  - projects/[company]/01-brand-context/voices.md        # the byline / author (E-E-A-T) set + auto-route
last_updated: 2026-07-12
---

# Voices (author / E-E-A-T) — build workflow

## What this does
Capture the company's **bylines** — the real, named voices content is published under — so the write phase has
a true author for the theme's author box (E-E-A-T lever 2) and an **auto-route** for which byline a piece gets.
Built **once per company** by **asking the team** the questions below, then assembling `voices.md`.

## The one rule (do not break)
**Every byline is a REAL person or the real company team — never invented.** The author is distinct from the
reader **persona** (that's a different workflow). Default to the **company-wide byline**; use a named individual
only where the piece genuinely warrants it (founder POV) or the user explicitly asks. E-E-A-T comes from real
credentials + cited data + the bio, never a fabricated personal story.

## The steps (in order) — this is mostly a questionnaire for the team

### Step 1 — Ask for the DEFAULT company byline (always exists)
Ask the team and record: **display name** (e.g. "Acme Team") · **author page URL** (verify it's live) · **tone** ·
**person** (2nd person for how-tos; 1st-person-plural for collective experience markers) · **collective first-hand
markers** ("Across the teams we work with…" — never a fabricated individual memory) · **E-E-A-T bio** (one line) ·
**byline line** (`Name | Company | author-page`). Note: company byline = no personal email.

### Step 2 — Ask for the FOUNDER / leadership voice (usually one)
The named exec whose byline leadership/vision/strategy/PR pieces carry. Record: **name + role** · **use-for**
(topics/formats) · **tone** · **person** · **first-hand markers** · **credential line** (`Name | Role, Company |
email | LinkedIn`).

### Step 3 — Ask for any OTHER named authors (0..n, optional)
Real content/HR authors available for **explicit** attribution (not auto-routed to). Per author: **name + role** ·
**use-for** · **tone** · **person** · **credential line** (email · author page).

### Step 4 — Confirm the AUTO-ROUTE rules
How a piece gets its byline, in order:
1. Leadership / vision / strategy-at-scale / future-of, OR press release / white paper / PR pitch → **founder**.
2. **Everything else → the company-wide default byline.**
3. A named individual byline is used **only when the user explicitly asks** — never auto-routed.

### Step 5 — Assemble `voices.md`
Write it to `projects/[company]/01-brand-context/voices.md` in the shape shown in the worked example
below (default byline table · founder voice · named individual bylines · auto-route rules). **No minimum-typing
trigger table, no "when to ask" section** — just the bylines + the 3 auto-route rules.

## Output — what `voices.md` holds
Default byline (table) → founder voice (table) → named individual bylines (tables) → the 3 auto-route rules. Each
byline carries the fields the write phase needs to render the author box: display name, credential/byline line,
tone, person, first-hand markers, bio.

## Gotchas
- Real people only (the one rule). Verify each author page is live.
- Default is the **company byline**; don't over-attribute to individuals.
- Author ≠ reader persona — keep them separate.

---

## Worked example — the target shape (GENERICIZED)

> **PII rule (2026-07-19):** real people's names, emails and profiles live ONLY in the company's own
> `projects/<company>/01-brand-context/voices.md` (SEED) — never in this reusable tools tree.
> Testlify's real, filled instance lives there. The shape:

- **Default byline table** — display name "<Brand> Team" · verified author-page URL · tone · person ·
  collective first-hand markers · one-line E-E-A-T bio · byline line. No personal email.
- **Voice 1 — founder/leadership** — use-for (vision/strategy/press) · tone · person rules per format ·
  real first-hand markers · credential line (`<Name> | <Role>, <Brand> | <email> | <LinkedIn>`).
- **Named individual bylines (0..n)** — one table each, used only on explicit request.
- **The 3 auto-route rules** — founder topics/formats → founder; everything else → the team byline;
  named individuals never auto-routed.

## Build/run checklist
- [ ] Ask the team: default company byline (Step 1).
- [ ] Ask: founder/leadership voice (Step 2).
- [ ] Ask: any other named authors (Step 3).
- [ ] Confirm the 3 auto-route rules (Step 4).
- [ ] Assemble `voices.md` (no trigger table, no "when to ask").
