# _craft — the per-format wrapper rules (LIVE)

**Read by the wrapper step since 2026-09-05.** `wrapper.py` injects `_craft/<archetype>.md` into
`prompts/wrapper.md` as `{{FORMAT_CRAFT}}`, so the intro, TL;DR, FAQ and close are shaped per
format. Before that date every article got the same wrap whatever its format, which is exactly
what the Testlify review flagged ("same format across every article — Google hates that").

## Why it exists

The files in `formats/` are injected into the architect's structure prompt. The architect designs
the BODY: sections, sub-headings, which evidence goes where. Rules about how the piece opens and
closes are not the architect's to act on, so they live here, one file per format.

## The fixed headings

Every file uses the same four, in this order, and says "nothing specific" where a format has no
rule:

1. **Intro** — what the opening must do for this format
2. **TL;DR** — anything format-specific about the takeaway block
3. **Close and takeaways** — how the article ends
4. **FAQ** — anything format-specific about the questions

A file may end with a *Publishing note* — that line is for the publish step, not the wrapper.

## Companion

`../../PENDING-WRITER-CHANGES.md` holds writer-phase changes that are not format-specific.
