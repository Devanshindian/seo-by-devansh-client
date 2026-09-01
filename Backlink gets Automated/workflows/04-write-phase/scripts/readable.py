#!/usr/bin/env python3
"""Writer Step 5 — READABLE: rewrite the whole article so a person wants to read it.

Reads:  writer/_work/coherent.json   (the article after the contradiction pass)
        the planner's plan + the architect's structure, for the keywords it must not lose,
        the expected topics, Google's own answer, and which format this article is
        formats/<archetype>.md — that format's rule for THIS step, if it has one
Writes: writer/_work/readable.json        — the same shape, rewritten
        writer/_work/readable-report.json — the model's change list + every check code ran

WHY IT SITS HERE AND NOT AT THE END.
It first shipped as step 9, after assemble, writing a second draft beside the finished one. That
worked but wasted three steps: slop stripped AI habits from wording this step then replaced, clean
scrubbed characters out of text that was about to change, and the links step laid its anchors over
words that then moved underneath them. Running before those three means they finish THIS wording,
and the links land on the sentences a reader actually gets.

WHY IT EXISTS AT ALL.
Step 1 writes each section on its own, from a pile of checked facts, blind to every other section.
That is what makes the research trustworthy and the prose stiff: with no room to breathe the writer
compresses four facts into one noun phrase and reaches for a figure of speech where it has no point
to make. An outside reviewer put it plainly — "the concept is good and the information is good, it's
just weirdly written out." Nothing earlier can fix that, because nothing earlier reads the finished
piece as a reader meets it.

THE SECTIONS IT RETURNS REPLACE THE ONES IT WAS GIVEN — there is no matching at all.
It was numbered-and-matched for a while, which is safe when a step only rewords. This one merges,
splits, reorders and deletes sections, so there is nothing stable to match on; worse, the matching
contract was itself what stopped it rebuilding. What guards the output now is the check list, not
the shape: no invented figure, no invented or moved source tag, no expected topic quietly dropped.

EVERY CHECK FLAGS. NONE BLOCK.
A failed article at 3am helps nobody, and the earlier steps already guard themselves. What is
measured here is only what THIS step could break.
"""
import argparse
import json
import os
import re

import assemble          # for keyword_view — the planner+architect keywords, not a later step's output
import config
import llm
import tags

MDLINK = re.compile(r"\[([^\]\[]+)\]\((https?://[^)\s]+)\)")
_REWRITE_SECTION = re.compile(r"^##\s+The rewrite\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
NUM = re.compile(r"\d[\d,]*\.?\d*%?")
# A source tag that has lost its number. [c412] is a citation; [c] points at nothing.
_BARE_TAG = re.compile(r"\[c\](?!\d)")
_SENT = re.compile(r"(?<=[.!?])\s+")


def _format_rule(archetype):
    """The format's own rule for THIS step, or "" when it has none.

    Only a format that needs one carries a `## The rewrite` section in formats/<archetype>.md; every
    other archetype gets its name and nothing more. Deliberately not the whole rulebook: the rewrite
    does not need to know how a how-to guide is built, only that it is looking at one — and one file
    holding all of a format's rules beats the same rule written into two prompts.
    """
    if not archetype:
        return ""
    try:
        body = open(config.format_path(archetype)).read()
    except OSError:
        return ""
    m = _REWRITE_SECTION.search(body)
    if not m:
        return ""
    # drop the file's note-to-maintainers paragraph; the model wants the rule, not the plumbing
    rule = re.sub(r"\A\s*Injected into[^\n]*(?:\n(?!\s*\n)[^\n]*)*\n\s*\n", "", m.group(1).strip(),
                  count=1)
    return "\n" + rule.strip() + "\n"


# ---------------------------------------------------------------- readability
def _syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1 and not w.endswith(("le", "ee")):
        n -= 1
    return max(1, n)


def _plain(w):
    """Every word a reader meets, with the markup taken out."""
    t = "\n\n".join(_texts(w))
    t = tags.sub(t, lambda _found: "")
    return MDLINK.sub(r"\1", t)


def reading_ease(w):
    """Flesch Reading Ease. 60+ is plain English; under 50 is heavy going."""
    p = _plain(w)
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", p)
    sents = [s for s in _SENT.split(p) if len(s.split()) > 2]
    if not words or not sents:
        return 0.0
    return round(206.835 - 1.015 * (len(words) / len(sents))
                 - 84.6 * (sum(_syllables(x) for x in words) / len(words)), 1)


def _subheads(w):
    """The "### " sub-headings a reader meets. In a glossary each one is a term entry; in a ranking
    each is a thing being ranked. Flattening them into prose destroys the format silently."""
    return re.findall(r"^###+\s*(.+?)\s*$", "\n".join(_texts(w)), re.M)


def _fact_ids(w):
    """The distinct research facts a reader meets, counted by their source tags."""
    out = set()
    for ids in _tag_map(w).values():
        out |= set(ids)
    return out


def _words_per_fact(w):
    n = len(_fact_ids(w))
    return (_words(w) / n) if n else 999.0


def _long_sentences(w):
    return [s for s in _SENT.split(_plain(w)) if len(s.split()) > config.WORDS_PER_SENTENCE]


# ---- STOP ASKING THE MODEL TO GUESS ITS OWN SCORE (2026-08-28, Devansh) -------------------------
# The old brief said "aim for a reading ease above 60". A model cannot run the Flesch formula on its
# own draft, so that was a wish, not an instruction — and the measurements show exactly that:
# syllables per word came out at 1.65 going in and 1.65 coming out, on every article, for a week.
# Sentence length improved every time because sentence length is countable. Vocabulary never moved
# because it was not. So code computes the score, the worst sentences and the offending words HERE,
# before the call, and hands them over as a checklist.
def _hard_words(w, top=22):
    """The 4+ syllable words actually in this article, commonest first."""
    seen = {}
    for x in re.findall(r"[A-Za-z][A-Za-z'-]*", _plain(w)):
        if _syllables(x) >= 4:
            k = x.lower()
            seen[k] = seen.get(k, 0) + 1
    return sorted(seen.items(), key=lambda kv: -kv[1])[:top]


def _render_hard_words(w):
    rows = _hard_words(w)
    if not rows:
        return "  (none — the vocabulary is already plain. Keep it that way.)"
    return "\n".join(f"  {word:<22} appears {n}x" for word, n in rows)


def _render_long_sentences(w, top=15):
    """The longest sentences, numbered, so the brief can say 'rewrite every one of these'.

    A table is not a sentence. Without this filter the list came back led by a 93-word run of
    markdown pipes, and telling the model to "rewrite this sentence" would have wrecked the table.
    """
    real = [s for s in _long_sentences(w) if "|" not in s and not s.lstrip().startswith(("-", "*"))]
    longs = sorted(real, key=lambda s: -len(s.split()))[:top]
    if not longs:
        return "  (none over %d words — good. Keep it that way.)" % config.WORDS_PER_SENTENCE
    return "\n".join(f"  {i}. ({len(s.split())} words) {' '.join(s.split())[:150]}"
                     for i, s in enumerate(longs, 1))


def _fat_paragraphs(w):
    out = []
    for para in re.split(r"\n\s*\n", _plain(w)):
        if re.match(r"^\s*(?:[-*+]\s|\d+[.)]\s)", para.strip()):
            continue                                    # a list is not a paragraph
        if len([s for s in _SENT.split(para) if s.strip()]) > config.SENTENCES_PER_PARAGRAPH:
            out.append(para)
    return out


# ---------------------------------------------------------------- the article
def _texts(w):
    """Every block of prose, in reading order. Headings are not prose."""
    out = [str(w.get("intro") or ""), str(w.get("quick_answer") or "")]
    out += [str(s.get("prose") or "") for s in (w.get("sections") or [])]
    out += [str(f.get("answer") or "") for f in (w.get("faq") or [])]
    out.append(str(w.get("close") or ""))
    return [t for t in out if t.strip()]


def _words(w):
    return len(" ".join(_texts(w)).split())


def _render(w):
    """The whole article, as a reader meets it. No section numbering any more (2026-08-26): the
    step used to patch each section in place, so every one had to come back with its number. It
    now REBUILDS — merging, splitting, reordering, turning prose into tables — and a numbering
    contract would have quietly forbidden all of that."""
    L = [f"# {w.get('h1') or ''}", "", "INTRO:", "", str(w.get("intro") or "")]
    if w.get("quick_answer"):
        L += ["", "QUICK ANSWER:", "", str(w.get("quick_answer") or "")]
    for s in w.get("sections") or []:
        L += ["", f"## {s.get('heading','')}", "", str(s.get("prose") or "")]
    if w.get("faq"):
        L += ["", "FREQUENTLY ASKED QUESTIONS"]
        for f in w["faq"]:
            L += ["", f"**{f.get('question','')}**", "", str(f.get("answer") or "")]
    L += ["", f"CLOSE  (it sits under the heading \"{w.get('close_heading') or '(none)'}\"):",
          "", str(w.get("close") or "")]
    return "\n".join(L)


_LEAD_HEADING = re.compile(r"\A\s*#{1,4}\s+[^\n]+\n+")


def _strip_heading(text):
    """Drop a heading the model wrote into the top of a block it does not own.

    The intro and the close are stored as prose; their headings live elsewhere and are printed by
    assemble. A model handed the heading for context will sometimes helpfully include it, and the
    article then shows it twice.
    """
    return _LEAD_HEADING.sub("", str(text or "")).strip()


def apply_reply(w, reply):
    """Fold the reply back in. The sections it returns REPLACE the ones it was given.

    There is no per-section matching left. A rebuild may merge two sections, split one, reorder
    them or drop one, so there is nothing stable to match on — and trying to match was what
    stopped it rebuilding in the first place. What guards the result is not a shape contract but
    the checks below: no invented figure, no invented or moved tag, no expected topic silently
    dropped.
    """
    n = json.loads(json.dumps(w))
    # THE HEADLINE (2026-08-26, Devansh). Every writer step before this one is forbidden from touching
    # the H1 — wrapper.py says so in as many words, because the architect chose it against real search
    # data. This step is the exception, and it has to be: it is the only one that can change what the
    # article IS, so it is the only one that can make the headline a lie. "12 Interview Questions"
    # survived a rebuild that left six sections and no list of twelve.
    # It always returns one. Unchanged means unchanged, so a straight copy is the normal case.
    h1_new = str(reply.get("h1") or "").strip()
    if h1_new:
        n["h1"] = _strip_heading(h1_new).lstrip("#").strip() or n.get("h1")
    if str(reply.get("intro") or "").strip():
        n["intro"] = _strip_heading(str(reply["intro"]))
    if str(reply.get("close") or "").strip():
        n["close"] = _strip_heading(str(reply["close"]))
    if str(reply.get("quick_answer") or "").strip():
        n["quick_answer"] = _strip_heading(str(reply["quick_answer"]))

    secs = [s for s in (reply.get("sections") or [])
            if isinstance(s, dict) and str(s.get("prose") or "").strip()]
    if secs:
        keep = {k: v for k, v in (w.get("sections") or [{}])[0].items()
                if k not in ("heading", "prose")} if w.get("sections") else {}
        n["sections"] = [dict(keep, heading=str(s.get("heading") or "").strip() or "Section",
                              prose=str(s.get("prose")).strip()) for s in secs]

    ans = {str(f.get("question", "")).strip(): str(f.get("answer") or "").strip()
           for f in (reply.get("faq") or []) if isinstance(f, dict)}
    for f in n.get("faq") or []:
        a = ans.get(str(f.get("question", "")).strip())
        if a:
            f["answer"] = a
    return n


# ------------------------------------------------------- 5b: the fat-paragraph fixer
# WHY A SECOND CALL AND NOT A RETRY (2026-08-27, Devansh). The check above has always caught this —
# on the resume-statistics article it read "1 -> 8 over 4 sentences" and the file was written anyway.
# The obvious fix was to re-run the whole rewrite on a fail, but that re-rolls a 2,000-word article to
# repair eight paragraphs and can lose everything that was already right. So this patches instead:
# code finds the offending paragraphs, one call rewrites ONLY those, and code swaps them back by id.
# Every other word of the article is byte-for-byte what the rewrite produced.
_LISTY = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|\||>|#)")


def _paras(text):
    return [p for p in re.split(r"\n\s*\n", str(text or "").strip()) if p.strip()]


def _bare(text):
    """The words a reader meets: source tags out, link text kept, address dropped."""
    return MDLINK.sub(r"\1", tags.sub(str(text or ""), lambda _f: ""))


def _sent_count(para):
    return len([s for s in _SENT.split(_bare(para)) if s.strip()])


def _is_prose(para):
    """A table row, a list item, a blockquote and a heading are not paragraphs."""
    return bool(para.strip()) and not _LISTY.match(para.strip())


def _nums_in(text):
    return {x.rstrip(".,") for x in NUM.findall(tags.sub(str(text or ""), lambda _f: ""))}


def _urls_in(text):
    return {u for _, u in MDLINK.findall(str(text or ""))}


def _block_text(w, key):
    if key[0] == "s" and key[1:].isdigit():
        return str((w.get("sections") or [])[int(key[1:]) - 1].get("prose") or "")
    return str(w.get(key) or "")


def _set_block(w, key, text):
    if key[0] == "s" and key[1:].isdigit():
        (w.get("sections") or [])[int(key[1:]) - 1]["prose"] = text
    else:
        w[key] = text


def _block_keys(w):
    """Every block this step may patch, in reading order.

    FAQ answers are excluded on purpose: the wrapper already caps one at WRAP_FAQ_WORDS, so it cannot
    hold a fat paragraph, and a 40-word answer has no room to be split anyway.
    """
    return (["intro", "quick_answer"]
            + [f"s{i + 1}" for i in range(len(w.get("sections") or []))]
            + ["close"])


def _find_fat(w):
    """Every paragraph over the sentence ceiling, with the room its section has left."""
    out = []
    for key in _block_keys(w):
        ps = _paras(_block_text(w, key))
        room = sum(1 for p in ps if _is_prose(p))
        for j, p in enumerate(ps):
            if _is_prose(p) and _sent_count(p) > config.SENTENCES_PER_PARAGRAPH:
                out.append({"id": f"{key}-p{j + 1}", "key": key, "idx": j, "text": p,
                            "sentences": _sent_count(p), "paras_in_section": room})
    return out


def _judge_fix(old, new, paras_in_section):
    """"" when the replacement is safe to paste in, otherwise the reason it is refused.

    Refused PER PARAGRAPH, never as a whole reply: one bad rewrite costs that paragraph its fix and
    the other seven still land.
    """
    ps = _paras(new)
    if not ps:
        return "came back empty"
    if len(ps) > 2:
        return f"{len(ps)} paragraphs — one split is the limit"
    if paras_in_section - 1 + len(ps) > config.PARAGRAPHS_PER_SECTION:
        return (f"a split would leave the section with {paras_in_section - 1 + len(ps)} paragraphs, "
                f"over the cap of {config.PARAGRAPHS_PER_SECTION}")
    over = [p for p in ps if _sent_count(p) > config.SENTENCES_PER_PARAGRAPH]
    if over:
        return f"still {_sent_count(over[0])} sentences"
    if tags.id_set(new) - tags.id_set(old):
        return f"invented the source tag(s) {sorted(tags.id_set(new) - tags.id_set(old))[:3]}"
    if _nums_in(new) - _nums_in(old):
        return f"invented the figure(s) {sorted(_nums_in(new) - _nums_in(old))[:3]}"
    if _urls_in(new) != _urls_in(old):
        return "changed a link"
    return ""


def fix_fat(w):
    """Rewrite only the paragraphs that run past the sentence ceiling. Returns (article, report)."""
    fat = _find_fat(w)
    if not fat:
        print("    no fat paragraphs — the fixer did not run")
        return w, {"found": 0, "applied": 0, "fixes": []}

    print(f"    {len(fat)} fat paragraph(s): {', '.join(t['id'] for t in fat)}")

    # The whole article, with the offending paragraphs marked. The model needs all of it so a
    # replacement reads correctly against its neighbours — that is the whole reason this is one call
    # over the article rather than one call per paragraph.
    marked = json.loads(json.dumps(w))
    by_block = {}
    for t in fat:
        by_block.setdefault(t["key"], []).append(t)
    for key, ts in by_block.items():
        ps = _paras(_block_text(marked, key))
        for t in ts:
            ps[t["idx"]] = f"[[{t['id']}]] {ps[t['idx']]}"
        _set_block(marked, key, "\n\n".join(ps))

    lines = []
    for t in fat:
        room = config.PARAGRAPHS_PER_SECTION - t["paras_in_section"]
        lines.append(
            f"[{t['id']}] — {t['sentences']} sentences. Its section has {t['paras_in_section']} "
            f"paragraph(s), so " + ("splitting would push it over the cap of "
                                    f"{config.PARAGRAPHS_PER_SECTION} — SHORTEN, do not split."
                                    if room < 1 else
                                    f"there is room for one split (cap is "
                                    f"{config.PARAGRAPHS_PER_SECTION})."))
        lines.append(t["text"])
        lines.append("")

    prompt = (llm.load_prompt("fat-paragraphs.md")
              .replace("{{TARGETS}}", "\n".join(lines))
              .replace("{{ARTICLE}}", _render(marked)))
    try:
        reply = llm.call_json(prompt) or {}
    except Exception as e:
        print(f"    !! the fat-paragraph call failed ({type(e).__name__}) — every paragraph left as it was")
        return w, {"found": len(fat), "applied": 0, "fixes": [], "error": str(e)[:120]}

    got = {str(f.get("id") or "").strip(): f for f in (reply.get("fixes") or []) if isinstance(f, dict)}
    n = json.loads(json.dumps(w))
    report, applied = [], 0
    # Later paragraphs first, so patching one index never shifts the next one.
    for t in sorted(fat, key=lambda x: (x["key"], -x["idx"])):
        f = got.get(t["id"])
        new = str((f or {}).get("prose") or "").strip()
        if not new:
            report.append({"id": t["id"], "applied": False, "why": "no replacement returned"})
            print(f"      ·  {t['id']}: no replacement returned — left as it was")
            continue
        why = _judge_fix(t["text"], new, t["paras_in_section"])
        if why:
            report.append({"id": t["id"], "applied": False, "why": why, "proposed": new})
            print(f"      !! {t['id']}: refused — {why}")
            continue
        ps = _paras(_block_text(n, t["key"]))
        ps[t["idx"]] = new
        _set_block(n, t["key"], "\n\n".join(ps))
        applied += 1
        report.append({"id": t["id"], "applied": True,
                       "how": str((f or {}).get("how") or "").strip(),
                       "sentences_before": t["sentences"],
                       "paragraphs_after": len(_paras(new)),
                       "before": t["text"], "after": new})
        print(f"      ·  {t['id']}: {t['sentences']} sentences -> "
              f"{len(_paras(new))} paragraph(s)  ({str((f or {}).get('how') or '')[:52]})")

    left = len(_find_fat(n))
    print(f"    fat paragraphs {len(fat)} -> {left} ({applied} fixed)")
    return n, {"found": len(fat), "applied": applied, "left": left, "fixes": report}


# ------------------------------------------------------- 5c: the plain-English retry
# THE LOOP THAT WAS MISSING (2026-08-28, Devansh). Every check in this step reported and none acted,
# so "reading ease 44, target 60" was printed on every article for a week and the file was written
# anyway. This is the second attempt the step never had: code measures the score, and if it is short
# it sends the WORST BLOCKS BACK with the offending words named. Same shape as the fat-paragraph
# fixer — code finds the problem, the model fixes only that, code validates each replacement and
# keeps the ones that helped. It runs at most twice, so a stubborn article costs two calls, not ten.
def _block_score(text):
    """Flesch on one block of prose."""
    p = MDLINK.sub(r"\1", tags.sub(str(text or ""), lambda _f: ""))
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", p)
    sents = [s for s in _SENT.split(p) if len(s.split()) > 2]
    if not words or not sents:
        return 100.0
    return round(206.835 - 1.015 * (len(words) / len(sents))
                 - 84.6 * (sum(_syllables(x) for x in words) / len(words)), 1)


def _hard_in(text):
    return [x for x in re.findall(r"[A-Za-z][A-Za-z'-]*", str(text or "")) if _syllables(x) >= 4]


def fix_plain(w, rounds=2):
    """Rewrite the hardest-reading blocks in plainer words. Returns (article, report)."""
    report = {"rounds": [], "ease_before": reading_ease(w)}
    for rnd in range(1, rounds + 1):
        now = reading_ease(w)
        if now >= config.READABLE_EASE:
            print(f"    plain English: {now:.1f} — at target, no rewrite needed")
            break

        # the blocks dragging the score down: worst first, and only ones with real hard words in them
        cands = []
        for key in _block_keys(w):
            t = _block_text(w, key)
            if len(t.split()) < 25:
                continue
            cands.append((_block_score(t), len(_hard_in(t)), key, t))
        cands = [c for c in cands if c[1] >= 2]
        cands.sort(key=lambda c: (c[0], -c[1]))
        picked = cands[:6]
        if not picked:
            print(f"    plain English: {now:.1f} — nothing left worth rewriting")
            break

        print(f"    plain English round {rnd}: {now:.1f} -> needs {config.READABLE_EASE:.0f} "
              f"| rewriting {len(picked)} block(s)")

        marked = json.loads(json.dumps(w))
        for _sc, _n, key, _t in picked:
            _set_block(marked, key, f"[[{key}]] " + _block_text(marked, key))

        lines = []
        for sc, n, key, t in picked:
            words = sorted(set(x.lower() for x in _hard_in(t)))[:10]
            lines += [f"[{key}] — scores {sc:.0f}. Hard words in it: {', '.join(words)}", t, ""]

        prompt = (llm.load_prompt("plain-english.md")
                  .replace("{{EASE_NOW}}", f"{now:.0f}")
                  .replace("{{EASE_TARGET}}", f"{config.READABLE_EASE:.0f}")
                  .replace("{{TARGETS}}", "\n".join(lines))
                  .replace("{{ARTICLE}}", _render(marked)))
        try:
            reply = llm.call_json(prompt) or {}
        except Exception as e:
            print(f"    !! plain-English call failed ({type(e).__name__}) — wording left as it was")
            report["rounds"].append({"round": rnd, "error": str(e)[:120]})
            break

        got = {str(f.get("id") or "").strip(): f for f in (reply.get("fixes") or []) if isinstance(f, dict)}
        n = json.loads(json.dumps(w))
        applied, log = 0, []
        for sc, _h, key, old in picked:
            new_t = str((got.get(key) or {}).get("prose") or "").strip()
            if not new_t:
                log.append({"id": key, "applied": False, "why": "no replacement returned"})
                continue
            why = ""
            if tags.id_set(new_t) - tags.id_set(old):
                why = "invented a source tag"
            elif _BARE_TAG.search(new_t):
                why = "wrote a bare [c]"
            elif _nums_in(new_t) - _nums_in(old):
                why = "invented a figure"
            elif _urls_in(new_t) != _urls_in(old):
                why = "changed a link"
            elif len(new_t.split()) > len(old.split()) * 1.15:
                why = "grew the block"
            elif _block_score(new_t) <= sc + 3:
                why = f"no real gain ({sc:.0f} -> {_block_score(new_t):.0f})"
            if why:
                log.append({"id": key, "applied": False, "why": why})
                print(f"      !! {key}: refused — {why}")
                continue
            _set_block(n, key, new_t)
            applied += 1
            log.append({"id": key, "applied": True, "score_before": sc,
                        "score_after": _block_score(new_t),
                        "swapped": str((got.get(key) or {}).get("swapped") or "")[:80]})
            print(f"      ·  {key}: {sc:.0f} -> {_block_score(new_t):.0f}  "
                  f"({str((got.get(key) or {}).get('swapped') or '')[:46]})")

        after = reading_ease(n)
        report["rounds"].append({"round": rnd, "blocks": len(picked), "applied": applied,
                                 "ease_before": now, "ease_after": after, "log": log})
        # KEEP THE BETTER OF THE TWO. A round that made it worse is thrown away whole.
        if after > now:
            w = n
            print(f"    plain English round {rnd}: {now:.1f} -> {after:.1f} ({applied} block(s) kept)")
        else:
            print(f"    plain English round {rnd}: no improvement ({now:.1f} -> {after:.1f}) — round discarded")
            break

    report["ease_after"] = reading_ease(w)
    return w, report


# ---------------------------------------------------------------- the checks
def _numbers(w):
    """Numbers a reader sees. Source tags are not article numbers, and trailing punctuation is not
    part of one — without both, this cries wolf on "2016," against "2016"."""
    t = tags.sub("\n".join(_texts(w)), lambda _f: "")
    return {x.rstrip(".,") for x in NUM.findall(t)}


def _tag_map(w):
    """Which source tags sit on which block. Keyed by position, so a reworded heading does not
    read as a lost tag."""
    return {i: tags.id_set(t) for i, t in enumerate(_texts(w))}


def judge_coverage(after, stakes, ai_overview):
    """One AI call: which expected topics, and which of Google's own answer, this article covers.

    WHY THIS IS NOT STRING MATCHING (2026-08-26). It was, and it lied. It took each topic's label,
    kept the words longer than four letters, and looked for any of them in the text. So "Definition of
    cost per hire" searched only for "definition" — and an article that defines cost per hire twice, in
    plain words, without ever using that noun, was reported as missing it. Worse, "Type D at work" has
    no word longer than four letters, so the probe list came back EMPTY and any([]) is False: that
    topic could never pass, whatever the article said. Both red crosses were on the review page,
    against articles that were fine.

    Coverage is a judgment about meaning, so it goes to the model. Returns None when the call fails,
    which the checks read as "not checked" rather than as a failure.
    """
    if not (stakes or ai_overview):
        return None
    prompt = (llm.load_prompt("readable-coverage.md")
              .replace("{{TABLE_STAKES}}",
                       "\n".join(f"   - {x}" for x in stakes) or "   (none recorded)")
              .replace("{{AI_OVERVIEW}}", str(ai_overview or "(none captured for this article)"))
              .replace("{{ARTICLE}}", _render(after)))
    try:
        reply = llm.call_json(prompt) or {}
    except Exception as e:
        print(f"    !! coverage call failed ({type(e).__name__}) — those two rows say 'not checked'")
        return None
    ts = [r for r in (reply.get("table_stakes") or []) if isinstance(r, dict)]
    ao = [r for r in (reply.get("ai_overview") or []) if isinstance(r, dict)]
    # A HOMONYM IS NOT A COVERAGE FAILURE (2026-08-27, Devansh). Google's answer for "curriculum vitae
    # statistics" is the statistical coefficient of variation — σ/μ, the population and sample formulas
    # — because "CV" means something else to a statistician. The check duly reported 0/6 covered on a
    # hiring article, a red cross that could never be cleared and should never have been asked for.
    # The judge above now says whether Google is even answering this subject; when it is not, the row
    # says so instead of failing.
    on_topic = reply.get("ai_overview_on_topic")
    off_topic = on_topic is False
    if off_topic:
        ao = []
        print("    · Google's answer for this keyword is a different subject "
              f"({str(reply.get('ai_overview_subject') or 'unrelated')[:50]}) — that check is skipped")
    if not ts and not ao and not off_topic:
        return None
    return {"table_stakes": ts, "ai_overview": ao,
            "ai_overview_off_topic": off_topic,
            "ai_overview_subject": str(reply.get("ai_overview_subject") or "").strip()}


def check(before, after, cov, target=None, stakes=None, judged=None):
    """Every earlier step bought something. Each row here protects one of them."""
    out = []
    b, a = _words(before), _words(after)   # words before/after — several checks below need these

    def add(name, ok, detail, protects):
        out.append({"check": name, "ok": bool(ok), "detail": detail, "protects": protects})

    # THE TOPICS, NOT THE SECTIONS (2026-08-26). This step may now merge, split, reorder and drop
    # sections, so counting them proves nothing. What must survive is the ground a reader expects
    # to find covered — judged against the article's whole text, not against its shape.
    def _row(name, rows, key, protects, allow_missing):
        miss = [str(r.get(key) or "") for r in rows if not r.get("covered")]
        add(name, len(miss) <= allow_missing(len(rows)),
            f"{len(rows) - len(miss)}/{len(rows)} covered"
            + (f" — missing: {'; '.join(m[:40] for m in miss[:2])}" if miss else ""),
            protects)

    if stakes:
        if judged and judged.get("table_stakes"):
            _row("Expected topics survived", judged["table_stakes"], "topic",
                 "a rebuild must not quietly drop the ground readers came for",
                 lambda n: n // 3)
        else:
            add("Expected topics survived", True, "not checked (the coverage call did not answer)",
                "a rebuild must not quietly drop the ground readers came for")

    # GOOGLE'S OWN ANSWER (2026-08-26, Devansh). The AI Overview is captured in research and handed to
    # the architect's structure prompts, and until now NOTHING checked that a word of it reached the
    # page. Table stakes had a check, keywords had a check, this had none — so it was advice the
    # architect could ignore in silence, and on the Type D article it did: Google's answer names
    # lifestyle changes and the DiSC "D" distinction, and neither appears anywhere in the article.
    # This flags it. It does not decide structure, which stays the architect's job.
    if judged and judged.get("ai_overview_off_topic"):
        add("Google's own answer covered", True,
            "skipped — Google's answer for this keyword is a different subject"
            + (f" ({judged.get('ai_overview_subject')})" if judged.get("ai_overview_subject") else ""),
            "the AI Overview is what Google already tells searchers this topic is made of")
    elif judged and judged.get("ai_overview"):
        _row("Google's own answer covered", judged["ai_overview"], "element",
             "the AI Overview is what Google already tells searchers this topic is made of",
             lambda n: n // 3)

    # A DROPPED FIGURE IS NOT A FAULT (2026-08-26). This step is now told to cut a number the
    # argument never leans on, so "every figure survived" is the wrong test — it flagged a clean
    # run that removed 9 unused statistics, which is the rule working. The fault is an INVENTED
    # number: one that was never in the checked research. Drops are reported, not failed.
    nb, na = _numbers(before), _numbers(after)
    made_up = na - nb
    add("No invented figures", not made_up,
        f"none invented ({len(nb - na)} unused figure(s) cut)" if not made_up
        else f"INVENTED {sorted(made_up)[:6]}",
        "a figure that was never in the research would be fabricated")

    # THE TEST IS "NO CLAIM WITHOUT ITS TAG", NOT "EVERY TAG SURVIVES" (2026-08-26). This step is
    # now asked to DELETE what does not earn its place, and a deleted claim takes its tag with it —
    # which the old check called a lost source and flagged. The two faults that actually matter are
    # an INVENTED tag (a source that was never there) and a MOVED one (a tag now proving a different
    # fact). Tags that left with their sentence are reported as a number, not as a failure.
    tb, ta = _tag_map(before), _tag_map(after)
    all_b = set().union(*tb.values()) if tb else set()
    all_a = set().union(*ta.values()) if ta else set()
    invented = all_a - all_b
    dropped = all_b - all_a
    add("No invented sources", not invented,
        f"none invented ({len(dropped)} left with the text they proved)" if not invented
        else f"INVENTED {sorted(invented)[:6]}",
        "a tag that was never in the research would be a fabricated citation")

    # A TAG WITHOUT ITS NUMBER (2026-08-28, Devansh). The rewrite turned every [c412] into a bare
    # [c] on two articles and NOTHING above noticed, because the check only hunts invented tags:
    # a bare [c] does not match the tag pattern, so the "after" set came back empty, "invented"
    # was empty, and the 93 destroyed tags were reported as the normal case — claims deleted along
    # with their sources. Total destruction and total deletion looked identical. This tells them
    # apart. A bare [c] is worse than no tag at all: the claim still looks sourced on the page.
    bare = len(_BARE_TAG.findall("\n".join(_texts(after))))
    add("Source tags kept their numbers", not bare,
        "every tag still carries its id" if not bare
        else f"{bare} tag(s) reduced to a bare [c] — the citation now points at nothing",
        "a tag stripped of its number is a claim pretending to be sourced")

    # FACTS MUST GET ROOM (2026-08-29, Devansh). This replaces "citations cut in step with the text",
    # which enforced exactly the wrong thing: it required tags to leave no faster than words, so the
    # only legal way to hit the word target was to keep every fact and crush each into a clause. That
    # is the register Devansh rejected. The rule is now the opposite and it is the point of the step:
    # cutting words WITHOUT cutting facts is the failure. Measured on the shipped glossary article,
    # density went from 76 words per fact to 47 — the article got twice as dense while calling itself
    # readable. A fact needs a sentence that sets it up and a sentence that says what it means, and
    # neither of those carries a tag, so words-per-fact is the honest measure of whether they exist.
    if all_b and b:
        d0, d1 = _words_per_fact(before), _words_per_fact(after)
        add(f"Facts have room to breathe ({config.READABLE_WORDS_PER_FACT}+ words each)",
            d1 >= min(config.READABLE_WORDS_PER_FACT, d0 * 1.4),
            f"{d0:.0f} -> {d1:.0f} words per fact "
            f"({len(all_b)} -> {len(all_a)} facts, {b:,} -> {a:,} words)",
            "a fact with no room to be explained is a fact the reader cannot use")

    # SUB-HEADINGS MUST SURVIVE THE REBUILD (2026-08-30, Devansh). Measured on the glossary rerun:
    # research produced 267 sub-headings (one per term), the architect kept 3, and THIS step flattened
    # the last 3 to zero — the brief rebuilt the article and never mentioned them, so they were not
    # carried across. For a glossary or a ranking the sub-heading IS the unit the reader came for, so
    # losing them turns the format into an undifferentiated essay. Dropping one WITH its section is
    # fine; dropping one while keeping the section is the fault.
    hb, ha = _subheads(before), _subheads(after)
    if hb:
        kept_secs = min(len(after.get("sections") or []), len(before.get("sections") or []))
        allowed = max(0, len(hb) - (len(before.get("sections") or []) - kept_secs) * 3)
        add("Sub-headings survived", len(ha) >= min(len(hb), allowed),
            f"{len(hb)} -> {len(ha)}"
            + ("" if len(ha) >= len(hb)
               else f" — {len(hb) - len(ha)} flattened into prose"),
            "in a glossary or a ranking the sub-heading is the entry the reader came for")

    ub = {u for _, u in MDLINK.findall("\n".join(_texts(before)))}
    ua = {u for _, u in MDLINK.findall("\n".join(_texts(after)))}
    add("The one link kept", ub == ua,
        f"{len(ua)} link(s): {', '.join(sorted(ua))[:80]}" if ub == ua
        else f"was {sorted(ub)}, now {sorted(ua)}",
        "the wrapper chose the page the close points at")

    sb, sa = len(before.get("sections") or []), len(after.get("sections") or [])
    tb = len(re.findall(r"^\|", "\n".join(_texts(before)), re.M))
    ta = len(re.findall(r"^\|", "\n".join(_texts(after)), re.M))
    add("It rebuilt, not just trimmed", sa != sb or ta > tb,
        f"sections {sb} -> {sa}, table rows {tb} -> {ta}",
        "merging, reordering and tabling is where the words come from")

    primary = ((cov.get("primary") or {}).get("phrase") or "").lower()
    if primary:
        heads = [str(s.get("heading", "")).lower() for s in after.get("sections") or []]
        in_head = sum(1 for h in heads if primary in h)
        first100 = " ".join(_plain(after).split()[:100]).lower()
        add("Primary keyword placed", in_head and primary in first100,
            f'"{primary}" — {in_head} heading(s), first 100 words '
            f'{"yes" if primary in first100 else "NO"}',
            "the architect placed the keyword in the headings")

    over = [f for f in (after.get("faq") or [])
            if len(tags.sub(str(f.get("answer") or ""), lambda _x: "").split()) > config.WRAP_FAQ_WORDS]
    add("FAQ answers short", not over,
        f"{len(after.get('faq') or [])} answers, {len(over)} over {config.WRAP_FAQ_WORDS} words"
        + (f" — {str(over[0].get('question',''))[:44]}" if over else ""),
        "the wrapper caps an answer at what a snippet shows")

    if target:
        # Not "did it grow" — it was ASKED to cut. Within 10% over the target counts as hitting it,
        # because the target is a direction, not a contract. Barely moving is the failure to catch:
        # measured across four articles the old ceiling-shaped rule produced a 3% cut, and one grew.
        # A BAND, NOT A CEILING (2026-08-28). This only ever checked "not too long", so a rewrite
        # that came back at 1,603 against a target of 2,100 was reported as hitting it. Undershooting
        # throws away material every earlier step paid to find, and it is where the citations went.
        floor = target * 0.85 if b > target else 0
        add("Landed in the word band", floor <= a <= target * 1.1,
            f"{b:,} -> {a:,}, asked for {target:,} ({(a - b) / b * 100:+.0f}%)"
            + (f" — {target - a:,} words UNDER the floor of {floor:,.0f}" if floor and a < floor else ""),
            "too long loses the reader; too short throws away what the research bought")
    else:
        add("No longer than before", a <= b, f"{b:,} -> {a:,} words",
            "the architect set a length band and the editor cut to it")

    # A BAND, NOT A FLOOR (2026-08-29, Devansh). The human Testlify articles score 28-35 on this
    # formula, so a floor of 60 was pointing away from the target. Above the ceiling means the prose
    # went clipped: short fragments stacked like bullets, which scores high and reads badly.
    e0, e1 = reading_ease(before), reading_ease(after)
    add(f"Reading ease {config.READABLE_EASE:.0f}-{config.READABLE_EASE_MAX:.0f}",
        config.READABLE_EASE <= e1 <= config.READABLE_EASE_MAX,
        f"{e0} -> {e1}  (band {config.READABLE_EASE:.0f}-{config.READABLE_EASE_MAX:.0f})"
        + (" — ABOVE the band: the prose has gone clipped, not clear"
           if e1 > config.READABLE_EASE_MAX else ""),
        "readable is a band; too high means fragments, too low means textbook")
    add("Long sentences", len(_long_sentences(after)) <= len(_long_sentences(before)),
        f"{len(_long_sentences(before))} -> {len(_long_sentences(after))} "
        f"over {config.WORDS_PER_SENTENCE} words", "this step should not add any")
    add("Fat paragraphs", len(_fat_paragraphs(after)) <= len(_fat_paragraphs(before)),
        f"{len(_fat_paragraphs(before))} -> {len(_fat_paragraphs(after))} "
        f"over {config.SENTENCES_PER_PARAGRAPH} sentences", "this step should not add any")
    return out


# ---------------------------------------------------------------- the step
def run(slug, redo=False, reply_path=None, brief_only=False):
    """reply_path (2026-08-29): a rewrite already written by something that is not a provider call,
    e.g. a Claude subagent holding the same brief. It is loaded INSTEAD of calling the LLM, and then
    goes through every guard below unchanged — apply_reply, the fat-paragraph fixer, the coverage
    judge and all the checks. The step keeps one set of guards whoever wrote the prose."""
    reply_path = reply_path or os.environ.get("READABLE_REPLY") or None
    outp = config.artifact(slug, "readable.json")
    src = config.artifact(slug, "coherent.json")
    if not os.path.exists(src):
        src = config.artifact(slug, "wrapper.json")     # a run that predates the coherence step
    if not redo and not brief_only and config.fresh(outp, src):
        print(f"  reusing {outp}")
        return json.load(open(outp))

    w = json.load(open(src))
    covp = config.artifact(slug, "keyword-coverage.json")
    cov = json.load(open(covp)) if os.path.exists(covp) else {}

    # THE KEYWORDS COME FROM THE PLAN, NOT FROM keyword-coverage.json (2026-08-26).
    # This step is 5 of 9; keyword-coverage.json is written by step 9. So on a first run the file
    # does not exist yet and every keyword read from it was "(none)" — the rule telling this step to
    # protect the bought heading phrases was inert on exactly the runs that mattered, and only looked
    # correct on a re-run because the PREVIOUS run had left the file behind. keyword_view() reads the
    # planner and the architect directly, so it is right on run one.
    ks = assemble.keyword_view(slug)
    prim = ks.get("primary") or "(none)"
    var = ", ".join(ks.get("variations") or []) or "(none)"
    h2 = ", ".join(k["keyword"] for k in (ks.get("h2_keywords") or [])) or "(none)"
    if h2 == "(none)":
        print("    !! no bought heading keywords found — the rewrite is free to reword every heading")

    now = _words(w)
    # THE CEILING IS THE TARGET (2026-08-26). It used to be "cut a quarter off, capped at the
    # ceiling", which let a 6,000-word article settle at 4,500 and still pass. The rule is now the
    # one the prompt states in words: at most READABLE_CEILING, and never longer than it came in.
    target = min(config.READABLE_CEILING, now)
    # the topics a reader expects — the one thing a rebuild must not quietly lose
    _pp = config.artifact(slug, "article-plan.json")
    _plan = json.load(open(_pp)) if os.path.exists(_pp) else {}
    stakes = _plan.get("table_stakes") or []
    ai_overview = _plan.get("ai_overview") or ""

    # THE FORMAT, AS A NAME AND (ONLY WHERE ONE EXISTS) A RULE. Deliberately not the format's whole
    # rulebook: this step does not need to know how a how-to guide is built, only that it is holding
    # one. A listicle needs more, because "merge sections freely" and "the items ARE the article"
    # genuinely conflict — that rule lives in formats/listicle.md, next to the format's other rules.
    archetype = _plan.get("format_archetype") or ""
    rule = _format_rule(archetype)
    if rule:
        print(f"    format rule injected for {archetype}")

    # THE ARITHMETIC THE BRIEF RUNS ON (2026-08-29). Same philosophy as the hard-word list: a model
    # cannot count its own citation density, so code counts it and hands over the target as a number.
    _facts = len(_fact_ids(w))
    _keep = max(6, round(now / max(config.READABLE_WORDS_PER_FACT, 1)))
    _keep = min(_keep, _facts)
    prompt = (llm.load_prompt("readable.md")
              .replace("{{FACTS_NOW}}", f"{_facts:,}")
              .replace("{{WORDS_NOW}}", f"{now:,}")
              .replace("{{WORDS_PER_FACT_NOW}}", f"{_words_per_fact(w):.0f}")
              .replace("{{TARGET_WORDS}}", f"{target:,}")
              .replace("{{FACTS_KEEP}}", f"{max(6, round(target / max(config.READABLE_WORDS_PER_FACT, 1))):,}")
              .replace("{{FACTS_DROP}}", f"{max(0, _facts - max(6, round(target / max(config.READABLE_WORDS_PER_FACT, 1)))):,}")
              .replace("{{ARCHETYPE}}", archetype or "general article")
              .replace("{{FORMAT_RULE}}", rule)
              .replace("{{TABLE_STAKES}}",
                       "\n".join(f"   - {x}" for x in stakes) or "   (none recorded)")
              .replace("{{PRIMARY_KEYWORD}}", prim)
              .replace("{{VARIATIONS}}", var)
              .replace("{{HEADING_KEYWORDS}}", h2)
              # the score, the worst sentences and the offending words — measured, not guessed
              .replace("{{EASE_NOW}}", f"{reading_ease(w):.0f}")
              .replace("{{EASE_TARGET}}", f"{config.READABLE_EASE:.0f}")
              .replace("{{HARD_WORDS}}", _render_hard_words(w))
              .replace("{{LONG_SENTENCES}}", _render_long_sentences(w))
              .replace("{{ARTICLE}}", _render(w)))
    config.write_json(config.artifact(slug, "readable-brief.json"),
                      {"slug": slug, "target_words": target, "facts_now": _facts, "words_now": now,
                       "facts_keep": max(6, round(target / max(config.READABLE_WORDS_PER_FACT, 1))),
                       "prompt": prompt})
    if brief_only:
        print(f"  -> brief only: {config.artifact(slug, 'readable-brief.json')}")
        return None
    print(f"    density: {_facts} facts in {now:,} words = 1 every {_words_per_fact(w):.0f} words "
          f"-> keep ~{max(6, round(target / max(config.READABLE_WORDS_PER_FACT, 1)))} in {target:,} words")
    print(f"    reading ease {reading_ease(w):.1f} (band {config.READABLE_EASE:.0f}-"
          f"{config.READABLE_EASE_MAX:.0f}) | {len(_long_sentences(w))} long sentence(s) named")
    if reply_path:
        print(f"    using the rewrite handed in at {reply_path} (no provider call)")
        reply = json.load(open(reply_path)) or {}
    else:
        reply = llm.call_json(prompt) or {}

    if not reply.get("sections") and not reply.get("intro"):
        print("  !! the reply carried no article — keeping the text as it is")
        config.write_json(outp, w)
        return w

    new = apply_reply(w, reply)
    if (new.get("h1") or "") != (w.get("h1") or ""):
        print(f"    headline corrected: {str(w.get('h1'))[:60]!r}\n"
              f"                     -> {str(new.get('h1'))[:60]!r}")

    # 5b — patch the paragraphs the rebuild left too long, before anything is measured or saved.
    new, fat_report = fix_fat(new)

    # 5c — and the words. This is the one that moves the score; see fix_plain's note.
    new, plain_report = fix_plain(new)

    judged = judge_coverage(new, stakes, ai_overview)
    checks = check(w, new, cov, target, stakes, judged)

    config.write_json(outp, new)
    config.write_json(config.artifact(slug, "readable-report.json"),
                      {"slug": slug, "checks": checks,
                       "archetype": archetype, "format_rule_used": bool(rule),
                       "fat_paragraphs": fat_report,
                       "plain_english": plain_report,
                       "h1_before": w.get("h1"), "h1_after": new.get("h1"),
                       # the per-item verdicts behind the two coverage rows, so the review page can
                       # show WHICH topic was missed rather than only how many
                       "coverage": judged,
                       "words_before": _words(w), "words_after": _words(new),
                       "ease_before": reading_ease(w), "ease_after": reading_ease(new)})

    failed = [c for c in checks if not c["ok"]]
    print(f"  -> {outp} | {_words(w):,} -> {_words(new):,} words "
          f"(asked for {target:,}) | "
          f"reading ease {reading_ease(w)} -> {reading_ease(new)} | "
          f"{len(checks) - len(failed)}/{len(checks)} checks clean")
    for c in failed:
        print(f"    !! {c['check']}: {c['detail']}")
    return new


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Writer Step 5 — rewrite the article to be read.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--reply", help="a rewrite already written as JSON; used instead of an LLM call")
    ap.add_argument("--brief-only", action="store_true", help="write readable-brief.json and stop")
    a = ap.parse_args()
    print(f"== Writer Step 5: readable — {a.slug} ==")
    run(a.slug, redo=a.redo, reply_path=a.reply, brief_only=a.brief_only)
