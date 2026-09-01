#!/usr/bin/env python3
"""Writer Step 7 — CLEAN: the mechanical scrub. Pure code, ZERO judgment, no AI, no cost.

Reads:  writer/_work/linked.json (falls back to polish.json, then wrapper.json)
Writes: writer/_work/scrubbed.json    — the same shape, characters and spacing fixed (assemble reads this first)
        writer/_work/clean-report.json — every fix, counted per rule and per field (the review page reads this)

Why this is code and not the AI slop pass: an AI asked to strip invisible characters misses some, costs money,
and answers differently on two runs. A regex misses none, is free, and is repeatable. So the split is strict —
CODE touches characters and spacing, the AI touches meaning. This step NEVER rewrites a word.

The four jobs (Station 3 of write-phase-architecture.md):
  1. INVISIBLES  — drop every Unicode format/control character; turn exotic spaces into a normal space.
                   Measured on a real draft: 31 narrow no-break spaces (U+202F) survived every other pass,
                   sitting inside "85 %" and "New York City". No human types one; it is a machine fingerprint.
  2. DASHES      — em AND en dash. The slop pass only names em dashes, so 7 en dashes shipped in that draft.
                   A numeric range ("60-90 minutes") becomes "to", never a comma, or the sentence breaks.
  3. WHITESPACE  — runs of spaces mid-line, spaces before punctuation, trailing spaces, 3+ blank lines.
  4. IDEMPOTENT  — running twice changes nothing. Asserted in code below.

Deliberately NOT done: curly quotes are LEFT ALONE. Word, Docs, macOS and iOS all curl quotes, so they are
normal in finished prose (34 in that same draft) — stripping them is a change with no reader benefit.
"""
import argparse
import json
import os
import re
import unicodedata

import config

# --- what counts as an invisible ------------------------------------------------------------------
# Exotic spaces -> a normal space (they LOOK like a space, so deleting them would join two words).
_SPACES = dict.fromkeys(
    [0x00A0, 0x1680, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007,
     0x2008, 0x2009, 0x200A, 0x202F, 0x205F, 0x3000], " ")
# Everything else in Cf/Cc/Co/Cs (zero-width joiners, BOM, soft hyphen, bidi marks…) is DELETED.
_KEEP_CONTROL = {"\n", "\t"}

# LOOKALIKES — characters that render like an ASCII one but are not it, so search, find-replace and
# exact-match all quietly fail on them. The non-breaking hyphen was the single most common non-ASCII
# character in a real finished draft (63 of them, vs 31 invisible spaces): "role‑specific" does not
# match a search for "role-specific", and nothing else in the pipeline was catching it.
_LOOKALIKE = {0x2010: "-", 0x2011: "-", 0x2012: "-", 0x2212: "-", 0x2044: "/"}

# DELIBERATELY LEFT ALONE: curly quotes (U+2018/2019/201C/201D) are normal in finished prose, and the
# maths symbols the article genuinely needs — ≥ (U+2265), ≈ (U+2248), × (U+00D7) — carry meaning.

_MDLINK = re.compile(r"\[([^\]]*)\]\((\S+?)\)")          # protect the url half of a markdown link
_TAG = re.compile(r"\[\s*c\s*\d+(?:\s*,\s*c?\s*\d+)*\s*\]", re.I)   # protect [c412] source tags
_URL = re.compile(r"https?://\S+")


def _protect(text):
    """Stash urls / markdown links / source tags so no rule can touch their insides."""
    box = []

    def keep(m):
        box.append(m.group(0))
        return f"\x00{len(box) - 1}\x00"

    for pat in (_MDLINK, _URL, _TAG):
        text = pat.sub(keep, text)
    return text, box


def _restore(text, box):
    for i, original in enumerate(box):
        text = text.replace(f"\x00{i}\x00", original)
    return text


def scrub(text, tally=None):
    """The whole scrub for one string. `tally` (a dict) accumulates counts per rule."""
    if not text:
        return text
    t, box = _protect(text)

    def bump(rule, n=1):
        if tally is not None and n:
            tally[rule] = tally.get(rule, 0) + n

    # --- 1. invisibles -----------------------------------------------------------------------
    out = []
    for ch in t:
        if ord(ch) in _SPACES:
            bump(f"invisible space U+{ord(ch):04X} -> normal space")
            out.append(" ")
            continue
        if ord(ch) in _LOOKALIKE:
            bump(f"lookalike U+{ord(ch):04X} -> '{_LOOKALIKE[ord(ch)]}'")
            out.append(_LOOKALIKE[ord(ch)])
            continue
        if ch not in _KEEP_CONTROL and ch != "\x00" and unicodedata.category(ch) in ("Cf", "Cc", "Co", "Cs"):
            bump(f"invisible U+{ord(ch):04X} removed")
            continue
        out.append(ch)
    t = "".join(out)

    # --- 2. dashes ---------------------------------------------------------------------------
    # A numeric range must read as a range: "60-90 minutes" -> "60 to 90 minutes", never a comma.
    t, n = re.subn(r"(?<=\d)\s*[–—]\s*(?=\d)", " to ", t)
    bump("dash in a number range -> 'to'", n)
    # An em dash sets off a clause: comma reads best.
    t, n = re.subn(r"\s*—\s*", ", ", t)
    bump("em dash -> comma", n)
    # A remaining en dash is standing in for a hyphen or a comma; a hyphen is the safe read.
    t, n = re.subn(r"\s*–\s*", "-", t)
    bump("en dash -> hyphen", n)

    # --- 3. whitespace -----------------------------------------------------------------------
    t, n = re.subn(r"(?<=\S)[ \t]{2,}(?=\S)", " ", t)      # runs of spaces INSIDE a line only:
    bump("repeated spaces collapsed", n)                    # leading indent is markdown structure
    # A leading decimal is NOT a stray space before a full stop. "a validity of .42" is correct English
    # for a correlation, and the naive rule turned it into "a validity of.42" — 15 times across one run,
    # in the most quotable sentences in the articles. Never close up a stop that a digit follows.
    t, n = re.subn(r"[ \t]+([.,;:!?])(?!\d)", r"\1", t)
    bump("space before punctuation removed", n)
    # "85 %" — what an invisible narrow space leaves behind once it becomes a normal one. Digit-then-unit
    # closes up; a bare "%" after a word ("a % of") is left alone.
    t, n = re.subn(r"(?<=\d)[ \t]+(?=%)", "", t)
    bump("space before % removed", n)
    t, n = re.subn(r"[ \t]+$", "", t, flags=re.M)
    bump("trailing space removed", n)
    t, n = re.subn(r"\n{3,}", "\n\n", t)
    bump("blank lines capped at 2", n)
    t, n = re.subn(r",\s*,", ",", t)                        # ", ," from a dash swap next to a comma
    bump("doubled comma fixed", n)

    return _restore(t.strip("\n") if text.strip("\n") != text else t, box)


# --- which fields hold prose (everything else is structure and must not be touched) ---------------
def _clean_article(w, tally_by_field):
    """Scrub every prose field of the article object, in place on a copy."""
    out = json.loads(json.dumps(w))

    def do(field, value):
        t = tally_by_field.setdefault(field, {})
        return scrub(value, t)

    for k in ("h1", "intro", "close"):
        if isinstance(out.get(k), str):
            out[k] = do(k, out[k])
    for f in out.get("faq") or []:
        f["question"] = do("faq", f.get("question") or "")
        f["answer"] = do("faq", f.get("answer") or "")
    for s in out.get("sections") or []:
        s["heading"] = do("headings", s.get("heading") or "")
        s["prose"] = do(f'section: {(s.get("heading") or "?")[:44]}', s.get("prose") or "")
    return out


def run(slug, redo=False):
    outp = config.artifact(slug, "scrubbed.json")
    if not redo and config.fresh(outp, config.artifact(slug, "linked.json"), config.artifact(slug, "polish.json")):
        print(f"  reusing {outp}")
        return json.load(open(outp))

    src = None
    for name in ("linked.json", "polish.json", "wrapper.json"):
        p = config.artifact(slug, name)
        if os.path.exists(p):
            src = p
            break
    if not src:
        raise SystemExit("!! nothing to clean — run the writer first")
    w = json.load(open(src))

    by_field = {}
    cleaned = _clean_article(w, by_field)

    # IDEMPOTENCY — the rule the spec is firm about: a second pass must change nothing.
    again = {}
    twice = _clean_article(cleaned, again)
    assert twice == cleaned, "scrub is not idempotent — a rule is fighting another rule"

    rules, total = {}, 0
    for field, t in by_field.items():
        for rule, n in t.items():
            rules[rule] = rules.get(rule, 0) + n
            total += n

    report = {"slug": slug, "source": os.path.basename(src), "total_fixes": total,
              "by_rule": dict(sorted(rules.items(), key=lambda kv: -kv[1])),
              "by_field": {f: dict(sorted(t.items(), key=lambda kv: -kv[1]))
                           for f, t in sorted(by_field.items()) if t}}
    config.write_json(outp, cleaned)
    config.write_json(config.artifact(slug, "clean-report.json"), report)
    print(f"  -> {outp} | {total} mechanical fix(es) across {len([f for f, t in by_field.items() if t])} field(s)"
          + (f" | {'; '.join(f'{k}: {v}' for k, v in list(report['by_rule'].items())[:3])}" if rules else ""))
    return cleaned


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Writer Step 7 — CLEAN (mechanical scrub, no AI).")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== clean — {a.slug} ==")
    run(a.slug, redo=a.redo)
