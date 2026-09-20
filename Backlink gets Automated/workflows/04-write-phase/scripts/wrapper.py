#!/usr/bin/env python3
"""Writer Step 3 — WRAPPER: write what sits around the finished article.

Reads:  writer/_work/blend.json (the edited article) + planner/article-plan.json (h1, primary keyword,
        the researched PAA questions) + gather/plan-inputs.json (group_a.keyword_set)
        + architect/structure.json (the spine) + the brand's features.md + the queue row.
Writes: writer/_work/wrapper.json — h1, intro, faq, dropped_questions, close, and the
        touch-ups already APPLIED to the sections, so the next step reads one finished article.

REBUILT 2026-08-11, on the SEO reviewer's two notes.

  THE INTRO now follows PAS: problem, agitate, solution. The third beat is the ARTICLE'S answer, not
  the product; the product belongs in the close and nowhere else. AIDA and FAB were offered too and
  deliberately not used: both end in selling something, and the body is product-free.

  THE FAQ may now go BEYOND the article, and answer from what the model knows. The old rule said every
  answer had to be built from facts in the body, which collided with the other rule saying a question
  must not duplicate a heading. The window between them was so narrow that 16 of 20 slots across four
  articles went to questions the model invented rather than to real searched ones. The reviewer settles
  it: an answer the article already gives is a wasted slot, because a search engine lifts that
  section's own sentence. `draws_on` went with the rule it enforced. Five is now a ceiling, not a
  target, because three real questions beat five padded.

The intro, the close and the touch-ups are still SOURCELESS: they see prose, never cards, so CODE
audits every [c<id>] tag in them and strips any that never existed in the body. A malformed reply
leaves the article untouched and is reported.

THE FAQ IS MEASURED, NEVER EDITED (_faq_measure). Answer length and any figure not found in the
article are recorded and shown on the review page. Nothing is dropped. A version that deleted
over-long answers and answers carrying outside figures was built and removed the same day: the FAQ is
deliberately allowed to answer past the article, so an outside figure is expected rather than a
fault, and a long answer is something to see rather than something code removes behind your back.
"""
import argparse
import json
import os
import re
import config
import llm
import fmt_router

import tags


_NUM = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def _features():
    p = config.brand_file("features.md")
    if not os.path.exists(p):
        return "(no features file on record)"
    return open(p).read().strip()[:config.WRAP_FEATURES_CHARS]


def _fill(name, **kw):
    t = llm.load_prompt(name)
    for k, v in kw.items():
        t = t.replace("{{%s}}" % k, str(v))
    return t


def _format_craft(archetype):
    """The format's wrapper rules from formats/_craft/<archetype>.md, or a plain fallback.

    Live since 2026-09-05 (the Testlify review: every article opened and closed the same way,
    whatever its format). The _craft files were parked for exactly this step; now it reads them.
    """
    if archetype:
        p = os.path.join(config.FORMATS, "_craft", f"{archetype}.md")
        try:
            body = open(p).read().strip()
            if body:
                return body
        except OSError:
            pass
    return "(this format has no wrap rules of its own — the general shapes above stand)"


_CTA_URL = re.compile(r"^- Page:\s*(\S+)", re.M)


def _cta_pages():
    """The pages a close may link to, and the set code checks the reply against.

    Built by the features engine from the crawl (3-features/scripts/build_cta_pages.py), so every
    URL here was fetched and is live. Kept apart from features.md on purpose: that file is prose a
    writer reads, this is a lookup a link has to be exactly right against.
    """
    p = config.brand_file("cta-pages.md")
    if not os.path.exists(p):
        return "(no CTA page list on record — do not link the close)", set()
    text = open(p).read().strip()
    return text[:config.WRAP_CTA_CHARS], set(_CTA_URL.findall(text))


_BANNED_CLOSE = ("conclusion", "final thought", "wrapping up", "in summary",
                 "key takeaway", "bottom line", "closing thought", "summary")


def _close_heading_check(heading, section_headings):
    """The close's heading, checked the way its link is.

    "Do not be generic" is advice a model can talk itself out of; a list of eight exact phrases
    matched in code is not. Every other part of the article sits under a heading — until 2026-08-21
    the close did not, so a reader scrolling to the end met a wall of text with nothing naming it.
    """
    h = (heading or "").strip()
    if not h:
        return ['The close has no heading. Return one as "close_heading".']
    bad, low = [], h.lower()
    if any(b in low for b in _BANNED_CLOSE):
        bad.append(f'"{h}" is a filler heading — it says the article is over, not what it is about. '
                   f"Name what the reader should do next instead.")
    if low in {s.lower().strip() for s in section_headings}:
        bad.append(f'"{h}" repeats a heading already in the article.')
    if len(h) > 60:
        bad.append(f'"{h}" is {len(h)} characters. Keep it under 60.')
    return bad


def _cta_check(close, declared, allowed):
    """Every way the close's link can be wrong, named in words the retry can act on."""
    found = re.findall(r"\[[^\]\[]+\]\((https?://[^)\s]+)\)", close)
    if not allowed:
        return []                                   # nothing to link to: not the reply's fault
    if not found:
        return ["The close carries NO link. It must link exactly one capability to its page."]
    bad = []
    if len(found) > 1:
        bad.append(f"The close carries {len(found)} links. It must carry exactly one.")
    for u in found:
        if u not in allowed:
            bad.append(f"{u} is not on the list of pages a close may link to. Pick one that is.")
    if declared and declared not in found:
        bad.append(f'You declared cta_link "{declared}" but the close does not contain it.')
    if not declared:
        bad.append('You did not return "cta_link". Return the url you linked to.')
    return bad


def _faq_measure(faq, article_text):
    """MEASURE the FAQ. Never touch it. (Devansh, 2026-08-11.)

    An earlier version of this dropped answers: one carrying a number the article did not have, one
    running over a word ceiling. That was wrong on both counts. The FAQ is the one place the writer is
    deliberately allowed to go past the article and answer from what it knows, so a figure the body
    does not contain is expected, not a fault. And a long answer is a style problem, which is a thing
    to see on the review page, not a thing for code to delete behind your back.

    So: two measurements per answer, both visible, neither acted on.
      words / over_target  — against WRAP_FAQ_WORDS, the length a search engine will lift
      outside_numbers      — figures not found in the article, so a human can spot-check them
    """
    known = set(_NUM.findall(article_text))
    for f in faq:
        ans = f.get("answer") or ""
        f["words"] = n = len(ans.split())
        f["over_target"] = n > config.WRAP_FAQ_WORDS
        f["outside_numbers"] = sorted(set(_NUM.findall(ans)) - known)
    return faq


def _voice():
    """How Testlify writes — the three files that govern the sound of a sentence, trimmed."""
    parts = []
    for name in config.WRAP_VOICE_FILES:
        p = config.brand_file(name)
        if os.path.exists(p):
            parts.append(f"### {name}\n{open(p).read().strip()[:config.WRAP_VOICE_CHARS]}")
    return "\n\n".join(parts) or "(no brand voice files found)"


def run(slug, redo=False):
    outp = config.artifact(slug, "wrapper.json")
    if not redo and config.fresh(outp, config.artifact(slug, "blend.json")):
        print(f"  reusing {outp}")
        return json.load(open(outp))

    bl = json.load(open(config.artifact(slug, "blend.json")))
    plan = json.load(open(config.artifact(slug, "article-plan.json")))
    st = json.load(open(config.artifact(slug, "structure.json")))
    kw = st.get("keywords") or {}
    ks = (json.load(open(config.artifact(slug, "plan-inputs.json")))["group_a"].get("keyword_set")) or {}
    primary = kw.get("primary") or ks.get("primary") or plan.get("primary_keyword") or "(none)"
    variations = kw.get("variations") if kw else (ks.get("variations") or [])
    row = fmt_router._queue_row(slug)
    h1 = st.get("h1") or plan.get("h1") or (row.get("asset") or "").strip() or "(none)"
    p = (json.load(open(config.artifact(slug, "plan-inputs.json")))["group_a"]).get("persona") or {}
    persona = (f"{p.get('name','')} — {p.get('lens','')}".strip(" —") if isinstance(p, dict) else str(p)) \
        or "(no persona on file)"

    secs = bl["sections"]
    block = "\n\n".join(f"## {s['heading']}\n\n{s['prose']}" for s in secs)
    paa = plan.get("paa_pool") or []
    prompt = (llm.load_prompt("wrapper.md")
              .replace("{{BRAND}}", config.BRAND)
              .replace("{{ABOUT}}", config.ABOUT or "(no description on file)")
              .replace("{{H1}}", h1)
              .replace("{{ANGLE}}", (row.get("angle") or "").strip() or "(none)")
              .replace("{{SPINE}}", st.get("spine") or "(none)")
              .replace("{{PERSONA}}", persona)
              .replace("{{PRIMARY}}", primary)
              .replace("{{VARIATIONS}}", ", ".join(variations or []) or "(none)")
              .replace("{{PAA}}", "\n".join(f"  - {q}" for q in paa)
                       or "  (none researched for this article, so every question is yours to find)")
              .replace("{{FAQ_WORDS}}", str(config.WRAP_FAQ_WORDS))
              .replace("{{FAQ_WORDS_SOFT}}", str(config.WRAP_FAQ_WORDS + 5))
              .replace("{{FEATURES}}", _features())
              .replace("{{CTA_PAGES}}", _cta_pages()[0])
              .replace("{{VOICE}}", _voice())
              .replace("{{ARCHETYPE}}", plan.get("format_archetype") or "general article")
              .replace("{{FORMAT_CRAFT}}", _format_craft(plan.get("format_archetype") or ""))
              .replace("{{SECTIONS}}", block))
    out = llm.call_json(prompt) or {}

    # THE CTA LINK, CHECKED AND RE-ASKED ONCE (2026-08-20). Until now the close named the brand and
    # linked nothing: 0 links across four finished articles. The links step could not help, because
    # it shortlists pages per SECTION using that section's heading and job, and the close has
    # neither — it was never handed a candidate. So the close is linked where it is WRITTEN, by the
    # step that already holds the feature list. Code then verifies it, and a failure is worth one
    # re-ask: blocking the run helps nobody at 3am, and a warning alone gets read the next morning.
    # The heading rides the SAME retry (2026-08-21). Both faults live in the closing block and both
    # are cheap to re-ask, so they go in one call rather than two: a second round trip per article
    # for a heading is not worth the wall clock.
    allowed = _cta_pages()[1]
    heads = [s.get("heading", "") for s in secs]

    def _close_problems(d):
        return (_cta_check(str(d.get("close") or ""), str(d.get("cta_link") or ""), allowed)
                + _close_heading_check(str(d.get("close_heading") or ""), heads))

    cta_problems = _close_problems(out)
    if cta_problems:
        print("  !! the close needs another pass — asking once more")
        for w in cta_problems:
            print(f"     · {w}")
        retry = llm.call_json(
            _fill("wrapper-cta-retry.md",
                  BRAND=config.BRAND, CLOSE=str(out.get("close") or ""),
                  HEADING=str(out.get("close_heading") or "(none returned)"),
                  HEADINGS="\n".join(f"- {h}" for h in heads),
                  PROBLEMS="\n".join(f"- {w}" for w in cta_problems),
                  CTA_PAGES=_cta_pages()[0])) or {}
        if retry.get("close"):
            merged = {"close": retry["close"],
                      "cta_link": retry.get("cta_link") or out.get("cta_link"),
                      "close_heading": retry.get("close_heading") or out.get("close_heading")}
            again = _close_problems(merged)
            if not again:
                out.update(merged)
                cta_problems = []
                print("     fixed on the retry")
            else:
                print(f"     still wrong after the retry ({len(again)} problem(s)) — kept as written")
                cta_problems = again

    known = set()
    for s in secs:
        known |= tags.id_set(s["prose"])

    stripped = [0]

    def clean(text):
        """Drop any [c] tag that was never in the body — the wrapper has no sources of its own."""
        text = str(text or "")
        bad = tags.id_set(text) - known
        if bad:
            text = tags.drop(text, bad)
            stripped[0] += len(bad)
        return text.strip()

    intro = clean(out.get("intro"))
    close = clean(out.get("close"))
    # THE QUICK ANSWER (2026-08-22). The one block a reader who reads nothing else still gets the
    # article from. Testlify's own blog runs it 350+ times, always in this slot; the reviewer's rule
    # is about its CONTENT — a genuinely shorter article, never a list of generic takeaways.
    quick = clean(out.get("quick_answer"))
    # draws_on is GONE (2026-08-11). It existed to prove an answer pulled from two or more sections,
    # which enforced the old rule that an answer could only come from the body. The FAQ may now go
    # beyond the article, so the field had no job left. _faq_measure records length instead.
    faq = [{"question": clean(f.get("question")), "answer": clean(f.get("answer")),
            "origin": f.get("origin") or "researched"}
           for f in (out.get("faq") or []) if isinstance(f, dict) and str(f.get("question") or "").strip()
           and str(f.get("answer") or "").strip()]
    dropped = [d for d in (out.get("dropped_questions") or []) if isinstance(d, dict)]
    faq = _faq_measure(faq, "\n".join(s["prose"] for s in secs))

    # apply the touch-ups in place; a touch-up naming an unknown heading is ignored, not guessed at
    by_head = {s["heading"]: s for s in secs}
    applied, ignored = [], []
    for t in (out.get("touch_ups") or []):
        if not isinstance(t, dict):
            continue
        h, prose = t.get("heading"), clean(t.get("prose"))
        if h in by_head and prose:
            by_head[h]["prose"] = prose
            applied.append({"heading": h, "what": t.get("what"), "why": t.get("why")})
        else:
            ignored.append(h)

    ok = bool(intro) and bool(close)
    if not ok:
        print("  !! wrapper reply malformed (no intro/close) — the article is unchanged")

    final = {"slug": slug,
             "h1": h1,                               # the architect owns the H1 — never the reply
             "intro": intro, "quick_answer": quick, "faq": faq,
             "dropped_questions": dropped, "close": close,
             "close_heading": clean(out.get("close_heading")),
             "cta_link": str(out.get("cta_link") or ""), "cta_problems": cta_problems,
             "sections": secs,                       # touch-ups already applied
             "touch_ups_applied": applied, "touch_ups_ignored": ignored,
             "invented_tags_stripped": stripped[0], "ok": ok}
    config.write_json(outp, final)
    words = [f["words"] for f in faq]
    over = sum(1 for f in faq if f.get("over_target"))
    outside = sum(1 for f in faq if f.get("outside_numbers"))
    qw = len(quick.split())
    print(f"  -> {outp} | intro {len(intro.split())}w | quick answer {qw}w"
          + ("" if config.QUICK_MIN <= qw <= config.QUICK_MAX else f" (OUTSIDE {config.QUICK_MIN}-{config.QUICK_MAX})")
          + " | "
          f"{len(faq)}/{config.WRAP_FAQ_COUNT} FAQ ({len(dropped)} dropped by the writer) | "
          f"answers {min(words) if words else 0}-{max(words) if words else 0}w, "
          f"{over} over {config.WRAP_FAQ_WORDS} | close {len(close.split())}w"
          + (f' under "{final["close_heading"]}"' if final.get("close_heading") else "")
          + (f" -> {final['cta_link']}" if final["cta_link"] and not cta_problems else "")
          + f" | {len(applied)} touch-up(s)"
          + (f" | STRIPPED {stripped[0]} invented tag(s)" if stripped[0] else ""))
    for w in cta_problems:
        print(f"    !! CLOSE: {w}")
    for f in faq:
        if f.get("outside_numbers"):
            print(f"    ~ figures not in the article, worth a look: "
                  f"{', '.join(f['outside_numbers'][:6])} — \"{str(f.get('question',''))[:46]}\"")
    for t in applied:
        print(f"    [{t.get('what','?')}] {str(t.get('heading',''))[:44]}: {str(t.get('why',''))[:60]}")
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Writer Step 3 — write the intro, FAQ and close.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Writer Step 3: wrapper — {a.slug} ==")
    run(a.slug, redo=a.redo)
