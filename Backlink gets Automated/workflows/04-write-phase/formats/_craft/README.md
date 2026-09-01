# _craft — the parked format rules

**Nothing here is read by any running code.** This is a parking lot, on purpose.

## Why it exists

The files in `formats/` are injected into the architect's structure prompt. The architect designs the
BODY: sections, sub-headings, which evidence goes where. But those files had accumulated rules the
architect cannot act on — how the intro should open, how the close should land, whether the page is
gated behind a form. It read them on every run and quietly ignored them.

So the body rules stayed in `formats/<archetype>.md`, and everything about the wrapper moved here,
one file per format, same headings every time.

## When these get used

When the writer phase is rebuilt. The wrapper step (intro, FAQ, close) and the publishing step have
no format-awareness at all today: every article gets the same intro instructions whatever its format.
These files are what they should read.

Until then this folder is a record of decisions already made, so nobody has to rediscover them.

## The fixed headings

Every file uses the same five, in this order, and says "nothing specific" where a format has no rule:

1. **Intro** — what the opening must do for this format
2. **Key-findings menu** — a summary block near the top, where the format wants one
3. **Close and takeaways** — how the article ends
4. **FAQ** — anything format-specific about the questions
5. **Publishing** — how and where the page goes out

## Companion

`../../PENDING-WRITER-CHANGES.md` holds the writer-phase changes that are not format-specific.
