---
type: workflow-recipe
stage: content-machine (Stage 0 — brand context)
reusable: any company
reads:
  - projects/[company]/01-brand-context/brand-voice.md   # the audience + voice already captured
produces:
  - projects/[company]/01-brand-context/persona.md       # 3–4 reader personas + how to pick one per article
last_updated: 2026-07-12
---

# Persona — build workflow

## What this does
Define the **3–4 reader personas** the content is written **to**, so every article is pitched at a specific
buyer at a depth they respect — not generic "HR." Recommends the set by reading `brand-voice.md` (the audience is
already captured there), the user confirms, and it saves `persona.md`. Built **once per company** (like
brand-voice / style-guide). At research/write time each article is tagged with the best-fit persona.

## The one rule (do not break)
**A persona is the READER we write TO — never the author byline.** It sets the lens, depth, vocabulary, and
angle. It is NOT a claim about who wrote the piece (the real named author + credentials come from the separate
author/E-E-A-T workflow). **Never invent or imply a fake author identity.** Picking your own audience (e.g. an HR
leader, when the company sells to HR leaders) is correct — that's the point.

**And when writing: think about the persona, but NEVER name/address them explicitly in the article** (no "as an
HR leader, you…"). The persona calibrates depth and angle only — naming it fences the piece to one reader when
others (a recruiter, a hiring manager) may read it too. Write so the target persona feels it's for them without
ever being told so.

## The steps (in order)

### Step 1 — Read `brand-voice.md`
Read the **Audience Understanding** section (primary + secondary audiences, what they care about, pain points).
That's the raw material — do not invent personas from thin air.

### Step 2 — Propose 3–4 reader personas (one LLM call)
Run the prompt below (headless Claude, free) with `brand-voice.md` pasted in. It returns 3–4 **distinct** reader
sub-personas that together cover the company's real buyers, each with the fields the writer needs.

**The exact prompt:**
```
You are defining READER personas for a company's content — the specific buyers each article is written TO.
These are NOT authors; never invent an author identity.

Here is the company's brand-voice / audience document:
<<<
{{BRAND_VOICE}}
>>>

Return 3–4 DISTINCT reader sub-personas that together cover the real audience (don't overlap; don't say "HR" in
general — split it into the specific roles who read different kinds of pieces). Return ONLY JSON:

{
  "personas": [
    {
      "name": "short role label (e.g. TA / Recruiting Leader)",
      "who": "one line — their role, seniority, company size",
      "reads": "the kinds of articles this persona is the right reader for",
      "cares_about": "top 2–3 things they want / decide on",
      "depth_and_angle": "how to pitch to them — vocabulary, depth, what proof convinces them",
      "not_this": "what would feel off / too junior / too generic for them"
    }
  ],
  "how_to_pick": "one or two sentences on how to choose the right persona for a given article topic"
}
```

### Step 3 — Show the user, confirm
Show the proposed personas. The user edits/removes/adds and approves the final 3–4. This is the one human gate.

### Step 4 — Save `persona.md`
Write the approved set to `projects/[company]/01-brand-context/persona.md` — the persona table +
the "how to pick one per article" note. That's the deliverable.

## Output — what `persona.md` holds
A short doc: a row per persona (`name · who · reads · cares_about · depth_and_angle · not_this`) + a
**"how to pick per article"** rule (match the article's topic/intent to the persona who'd actually read it —
strategy → the exec persona; role/skill how-to → the hands-on persona; etc.).

## Gotchas
- Persona = **reader**, not author (the one rule). If you ever catch yourself writing "by an HR leader," stop.
- **3–4, distinct.** Two personas that read the same pieces are one persona — merge them.
- Pitch each article to **one** persona, chosen by topic — not "everyone in HR."

## Build/run checklist
- [ ] Read `brand-voice.md` Audience section.
- [ ] Run the prompt → 3–4 distinct reader personas.
- [ ] Show the user; get approval (edit as needed).
- [ ] Save `persona.md` to `projects/[company]/01-brand-context/`.
