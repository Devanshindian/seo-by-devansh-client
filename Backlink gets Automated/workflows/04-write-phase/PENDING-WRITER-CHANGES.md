---
type: the parking file for every WRITER-phase change we have decided but not built
purpose: so nothing found during the architect work is lost before the writer is revamped
companion: formats/_craft/ (the format-specific wrapper rules, parked the same way)
opened: 2026-08-08
---

# Writer-phase changes, decided and waiting

**Nothing here is built.** Every item is a decision already taken during the architect work. When the
writer phase is revamped, this file is the input.

Each item says where it came from: `[reviewer]` the Testlify review of the first 4 articles ·
`[Devansh]` a decision made in the architect session · `[measured]` verified against a real run.

---

## A. The three fields the architect now sets that the writer ignores

These are live in `architect/structure.json` from 2026-08-08 and **have no effect until the writer
reads them**. This is the highest-value group, because the planning half is already done.

- [ ] **`h3s` are now real, authored sub-headings.** The architect writes them itself and says which
  boxes sit under each. The writer must render them as `###` headings. `[Devansh]`
  *Why it matters:* `[measured]` 3 of the first 4 articles shipped with **zero H3s on the page**, and
  the fourth rendered 4 in one section by accident. The writer's prompt lists sub-topics under
  `{{H3S}}` and never tells it to make them headings.

- [ ] **`lead` holds the boxes above the first H3.** The writer must open with those, then work
  through the H3s in order. `[Devansh]`
  *Already patched:* the cards in `lead` are visible to the writer, so no fact is lost today. What is
  missing is the writer using the split to shape the section.

- [ ] **`list` marks a section as a list, `{"kind": "numbered|bulleted", "of": "..."}`.** The writer
  must render it, the same way it already renders `table`. `[Devansh]`
  *And:* a section marked as a list must NOT be only bullets. It still needs prose around them. A
  section that is nothing but a list reads as a slide deck.

- [ ] **`is_item` marks a listicle section as an item or a supporting section.** `[Devansh]`
  *Why it matters:* `[measured]` on the strategic-questions article the per-item contract
  (`Strong Answer` / `Weak Answer` / `Scoring line`) was applied to **all 27 sections**, including the
  7 that are not questions at all. "Build an Interview Question Bank" and "3 Frameworks for Scoring
  Interview Answers" both end with a Strong Answer and a Weak Answer. The code check in
  `write_body.py` reported **zero misses**, because it checks every section rather than every item.
  Two changes needed: the writer's prompt must only carry the contract into `is_item: true` sections,
  and the code check must only count those.

---

## B. How a sentence and a paragraph must read

All of these belong in `prompts/write-body.md`, and most of them are **already written there and
being ignored**. Adding a twelfth rule to a prompt losing the first eleven will not fix them. The
lever is a code check per section plus a targeted re-ask, using the shape that already exists in
`write_body.py` (the per-item contract check counts misses and prints them, but never re-asks).

- [ ] **Sentences never exceed 25 words.** `[reviewer]` The prompt currently says "keep most sentences
  under 20 words", which is a suggestion with no ceiling.
- [ ] **Paragraphs are at most 4 sentences.** `[Devansh]` Not in the prompt at all today.
- [ ] **Sentence length must VARY and be irregular.** `[reviewer]` Not all long, and not all short
  either. Uniform rhythm reads machine-made.
- [ ] **Explain a complex term in brackets, short and plain.** `[Devansh]` The rule exists but asks for
  "its meaning in the same sentence"; the requested form is a parenthetical gloss.
- [ ] Tables and lists do NOT count towards a section's paragraph budget. `[Devansh]`

### The checks that would make these real
- [ ] Longest sentence per section, flag anything over 25 words.
- [ ] Sentences per paragraph, flag anything over 4.
- [ ] Standard deviation of sentence length, so "every sentence the same length" fails too.
- [ ] Section word count against its `word_target`, which already exists and nothing acts on.
- [ ] **Does the section answer its own heading?** See section C.

---

## C. Answering the heading

- [ ] **A section must answer its heading, near the start, and give the reader a takeaway.**
  `[reviewer, Devansh]`
  *The real example:* on the cost-per-hire article, four consecutive paragraphs explained which SHRM
  edition each figure came from, which editions superseded which, and why they cannot be compared.
  The section never reached an answer.
  *Why the check can only live here:* every section carries a `job` field saying what it must deliver.
  It is written by the architect, passed to the writer, and **checked by nobody**. It is the most
  under-used field in the machine, and it disappears after the writer.
- [ ] The architect half of this is **done**: the structure prompts now require that a section's boxes
  can answer its headline, and that the headline changes or research is raised when they cannot.

---

## D. The wrapper (intro, FAQ, close)

All in `prompts/wrapper.md`.

- [ ] **FAQ answers: 2 to 3 sentences, maximum 4, and never more than 40 words.** `[reviewer]`
  Currently "2 to 4 sentences" with no word cap.
- [ ] **The intro should do more work:** bust a myth where there is one, run problem then agitate then
  solution, state what the article is for, and say who it is for. `[reviewer, Devansh]`
- [ ] `[reviewer]` "Nobody states who the article is for." The spine names an audience and the article
  never says it out loud.
- [ ] The wrapper step is **format-blind**. Every article gets the same intro instructions whatever
  its format. `formats/_craft/` holds the per-format rules it should read.

---

## E. Links

- [ ] **External links capped at 4 or 5.** `[reviewer]` Currently hardcoded `MAX=10` at
  `links_pass.py:617`.
- [ ] **Named credible sources (SHRM, Forbes) get the link on the source name in the prose**, not on a
  citation marker. `[reviewer]` The machinery exists (`external-links.md` returns an `anchor_phrase`).
  It needs checking on a real run, not rebuilding.

---

## F. Length, and where it is actually decided

- [ ] **`[Devansh]` TO CHASE: the house length.** The reviewer asked for 1,500 to 2,000 words. Our word
  bands are 2,400 to 7,500 and they are set in the **research phase**, not the write phase. Until that
  changes, everything downstream is splitting a band that is already too big.
  *What the architect can do, and now does:* the section count is a hard ceiling, the no-band fallback
  is 1,500, and a listicle carries at most 12 items.
  *What it cannot do:* change the band.
- [ ] **`[measured]` nothing acts on an overshoot.** `assemble.py` already prints
  `!! LENGTH: 10,677 words — 42.4% OVER` and records it. No step trims and no gate refuses to ship.

---

## G. Repetition and shape

- [ ] `[reviewer]` "Under most headers, there's an explanation, followed by a paragraph on good vs bad
  answers, another on scoring, and then examples. Some of this could be consolidated."
  This is the per-item contract firing on every section. The architect fix is in (section A). What is
  left is the writer honouring it.
- [ ] `[reviewer]` "Some headings could potentially be combined or removed." The cross-section heading
  pass (`headings.py` 5b) is the natural place, and it is **explicitly forbidden** from adding,
  removing or reordering sections. Same count in, same count out.

---

## H. Checks that do not exist at all

- [ ] **Readability.** `[reviewer]` Nothing measures reading level. Plain code, using `textstat`.
  Target: around 12th-grade English.
- [ ] **A review pass** that sorts findings into critical, high and quick-win, then edits.
- [ ] **A publish gate**: one checklist that must pass before anything ships.
- [ ] **Awkward sentences.** `[reviewer]` The slop pass hunts known AI tells. It never asks whether a
  sentence simply reads badly. Two that got through:
  - "Once the decision is locked, a rubric can be built backward from it, ensuring every point ties to
    a defensible outcome, not a guess."
  - "And the majority of every hire, 60 to 70 percent of the cost, is soft."
