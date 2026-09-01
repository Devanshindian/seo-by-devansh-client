#!/usr/bin/env python3
"""Writer Step 6 — SENTENCE PASS: re-shape the sentences so a reader gets through them.

Reads:  writer/_work/readable.json  (the article after the readability rebuild)
        + prompts/sentence-pass.md  (the five moves — THE place to tune how it writes)
Writes: writer/_work/sentences.json        — readable.json's shape, prose re-shaped
        writer/_work/sentence-report.json  — per block: the counts, the verdict, the model's moves
        writer/sentence-review.html        — the side-by-side page: what came out, what went in

WHY THIS IS NOT PART OF THE READABLE STEP.
Readable owns DENSITY: it deletes facts and spends the freed words explaining the ones it keeps, so
it merges sections, drops sections and changes the length. This step owns SENTENCE SHAPE, and its
whole contract is that nothing changes except wording: same length, same facts, same sections. Put
the two briefs in one prompt and they contradict each other — one says delete, the other says
preserve exactly — and the model does neither well. It was tried; that is why there are two steps.

WHY IT RUNS HERE.
After readable, so it re-shapes the wording a reader will actually get rather than wording readable
is about to replace. Before slop, links and clean, so those three finish THIS wording and the link
anchors land on the final sentences. Same reasoning readable's own docstring gives for its position.

WHY PER BLOCK AND NOT PER ARTICLE.
Sentence shape is local: no sentence needs to see another section to be re-shaped, so whole-article
context buys nothing. Per block buys three things. It fans out over llm.max_workers(). The word
budget is enforced per block, which is what actually holds an article's shape (holding the total
while sections drift is how the balance between sections quietly moves). And one block failing its
checks costs that block, not the article.

THE AI PROPOSES, CODE VERIFIES, per block, against the block it was given:
  - word count within max(8, 5%)     — "make it easier" reads to a model as "make it shorter", and
                                       what it cuts is the explanation an earlier step paid to add.
                                       The whole ARTICLE is then checked to 1%, which is the number
                                       that matters: one block grows, another shrinks, total holds
  - the set of numbers               — none lost, none invented (a repeat is a split sentence)
  - the multiset of [c…] tags        — identical, so provenance survives the re-shaping
  - every markdown link              — words and address both, so the links step's work is not undone
  - every "### " sub-heading line    — verbatim; each carries a keyword bought for its section
  - every table row and bullet       — verbatim; a table flattened into prose is a lost comparison
  - average sentence length          — must not RISE (the step did nothing), and on a block of 60+
                                       words must not fall under 8.5 either (chopped to a stutter)
One retry, told what it broke. Then the block keeps its ORIGINAL text, loudly logged. The article can
only stay the same or improve; it can never be damaged here.
"""
import argparse
import difflib
import statistics
import html as _html
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

import config
import llm
import tags

# A number as a reader meets it. The trailing separator is stripped, because "70," and "70 " are the
# same fact and a signature that keeps the comma rejects a rewrite that only moved the punctuation.
# (slop_pass.py carries the un-stripped version of this regex and has the same latent false reject.)
_NUMS = re.compile(r"\d[\d,\.]*")
_MDLINK = re.compile(r"\[([^\]\[]+)\]\((https?://[^)\s]+)\)")
_TAG = re.compile(r"\[c[\d,\s c]*\]")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

# A block shorter than this is a caption, not prose: re-shaping it can only churn the wording.
MIN_BLOCK_WORDS = 25
# The band a rewrite must land in, as a share of the block it replaces (floor in words, for the FAQ).
# 5%, not 2%: the hand-edited ground truth this step was built against moved individual blocks by up
# to 7% while the ARTICLE total held to 0.1%, because a block that grew paid for one that shrank. A
# 2% block band rejected five of its seventeen sections. The total is guarded separately, below.
WORD_TOLERANCE = 0.05
WORD_FLOOR = 8
# How far the WHOLE article may drift before the run says so. Nothing to fall back to at article
# level, so this reports rather than rejects — but it is the number that actually matters.
# 2.5%, measured: splitting "A, and B, and C" into three sentences makes each one restate its
# subject, so a real sentence pass GROWS an article slightly. The first live run came in at +1.48%
# with every block inside its own band and no padding anywhere. A 1% ceiling fired on a good run,
# and a guard that always fires is one nobody reads. Past 2.5% it is padding, not splitting.
ARTICLE_DRIFT = 0.025
# Average sentence length is allowed to drift up by this much before the rewrite counts as pointless.
AVG_SLACK = 0.5
# ...and a floor under it, because the failure at the other end is real: a run of six-word sentences
# reads like a machine and, on a subject the reader came to learn, reads as condescending. Only
# applied to blocks big enough for the average to mean anything — a 30-word FAQ answer written as
# three fragments is correct. No block of 60+ words in the first live run fell below 10.0, so this
# is a backstop against a future prompt edit, not a limit on the current one.
AVG_FLOOR = 8.5
AVG_FLOOR_MIN_WORDS = 60
# RHYTHM, and why it is REPORTED rather than rejected. A flattened article is a real fault: the first
# live run levelled every sentence into one band and read worse than the draft it replaced. But it is
# not rejectable per block — every threshold tried that caught the flattened blocks also rejected two
# to seven blocks of a hand-written version of the same article, and a guard that throws away good
# work is worse than no guard. So the prompt carries the rule and this carries the verdict.
#
# THE VERDICT IS ABOUT THE OUTPUT, NOT THE LOSS, and that correction cost a batch to learn. The first
# version of this guard compared the output's spread to the INPUT's and failed anything under 0.80.
# Run over six articles it got the answer backwards on five of them: it passed the flattest article
# in the set (spread 4.80, 14% long sentences) because that article arrived flat and so lost nothing,
# and it failed the liveliest (spread 5.89, 29% long) because that one arrived very uneven and a pass
# that splits three-clause monsters is SUPPOSED to reduce spread. Reading the two confirmed it: the
# "passing" article was the choppy one. A ratio measures what changed; a reader meets what is there.
#
# So the floors below are absolute, benchmarked against a hand-written rewrite that was judged good
# (spread 6.07, 22% of sentences at 18+ words), set at roughly 90% and 80% of it. The ratio survives
# only as an escape hatch: an article handed to this step already flat cannot be made varied here,
# because the step is not allowed to lengthen anything, so keeping what it was given is a pass.
# Calibrated on six articles and one hand-written benchmark. Widen the sample before trusting it hard.
SPREAD_OUT_FLOOR = 5.5          # absolute spread of sentence lengths in the finished article
LONG_OUT_FLOOR = 0.18           # share of sentences still running 18+ words
SPREAD_KEPT_FLOOR = 0.90        # ...or it simply kept the variety it arrived with
# The share of a block's long sentences that must SURVIVE. Measured, not guessed: a hand-written
# rewrite of the glossary kept 0.65 of them and held its spread at 0.94. The two articles that came
# back flat kept 0.41 and 0.53. 0.70 sits above both failures and below the known-good run.
# This one is SOFT: it buys a retry, it never discards a block. Rhythm is a matter of degree, and
# throwing away an otherwise-correct rewrite over it costs more than it saves.
LONG_KEEP_RATIO = 0.70


# --- measuring ---------------------------------------------------------------

def _prose_lines(text):
    """The lines a reader reads as sentences: not headings, not table rows, not bullets."""
    out = []
    for line in (text or "").split("\n"):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("|") or s.startswith(("- ", "* ", "+ ")):
            continue
        if re.match(r"^\d+\.\s", s):
            continue
        out.append(s)
    return out


def _plain(text):
    """The text as a reader meets it: source tags gone, a link reduced to its words."""
    t = _MDLINK.sub(r"\1", text or "")
    t = _TAG.sub("", t)
    return t


def words(text):
    return len(_plain(text).split())


def sentences(text):
    joined = " ".join(_prose_lines(_plain(text)))
    return [s for s in _SENT_SPLIT.split(joined) if len(s.split()) > 1]


def avg_sentence(text):
    ss = sentences(text)
    return round(sum(len(s.split()) for s in ss) / len(ss), 1) if ss else 0.0


def spread(text):
    """How much sentence lengths VARY. A page where every sentence is the same size reads like a
    form, whatever its average is, so this is the number that says whether the rhythm survived."""
    L = [len(s.split()) for s in sentences(text)]
    return round(statistics.pstdev(L), 2) if len(L) > 2 else 0.0


def long_share(text, k=18):
    """The share of sentences still running long. The first run took this from 0.24 to 0.01."""
    L = [len(s.split()) for s in sentences(text)]
    return round(sum(1 for x in L if x >= k) / len(L), 3) if L else 0.0


# --- the guards --------------------------------------------------------------

def _num_sig(text):
    """The SET of figures, not the multiset. Splitting one sentence into two often repeats the
    subject, and the subject is sometimes a figure: "A raw score of 28 out of 40 lands at the 80th
    percentile ... The same 28 lands at the 55th." Nothing is lost and nothing is invented there, but
    the count of "28" goes from one to two, and a multiset check rejects the whole section over it.
    What must never happen is a figure DISAPPEARING or a new one APPEARING. How often a figure is
    repeated is wording, which is what this step is for. Tags and links stay multisets, because a
    duplicated citation or a duplicated link is a real fault."""
    return {n.rstrip(",.") for n in _NUMS.findall(text or "")}
def _tag_sig(text):   return sorted(tags.ids(text))
def _link_sig(text):  return sorted(_MDLINK.findall(text or ""))


def _head_sig(text):
    return [l.strip() for l in (text or "").split("\n") if l.strip().startswith("#")]


def _struct_sig(text):
    """Table rows and bullets, verbatim. These are copied, never rewritten."""
    return [l.strip() for l in (text or "").split("\n")
            if l.strip().startswith("|") or l.strip().startswith(("- ", "* ", "+ "))
            or re.match(r"^\d+\.\s", l.strip())]


def _violations(before, after):
    """Every contract the rewrite broke, in plain words. Empty list means accept it."""
    bad = []
    n = words(before)
    tol = max(WORD_FLOOR, round(n * WORD_TOLERANCE))
    m = words(after)
    if abs(m - n) > tol:
        bad.append(f"word count {m}, must be {n - tol}-{n + tol}")
    lost = sorted(_num_sig(before) - _num_sig(after))
    made = sorted(_num_sig(after) - _num_sig(before))
    if lost:
        bad.append(f"a number went missing: {', '.join(lost[:4])}")
    if made:
        bad.append(f"a number appeared that was not there: {', '.join(made[:4])}")
    if _tag_sig(after) != _tag_sig(before):
        bad.append("a [c] source tag changed")
    if _link_sig(after) != _link_sig(before):
        bad.append("a markdown link changed")
    if _head_sig(after) != _head_sig(before):
        bad.append("a ### sub-heading changed")
    if _struct_sig(after) != _struct_sig(before):
        bad.append("a table row or bullet changed")
    if avg_sentence(after) > avg_sentence(before) + AVG_SLACK:
        bad.append(f"average sentence length rose ({avg_sentence(before)} to {avg_sentence(after)})")
    if n >= AVG_FLOOR_MIN_WORDS and avg_sentence(after) < AVG_FLOOR:
        bad.append(f"chopped too fine (average sentence {avg_sentence(after)} words)")
    return bad


# --- the step ----------------------------------------------------------------

def _longest(text):
    L = [len(s.split()) for s in sentences(text)]
    return max(L) if L else 0


def _long_count(text, k=18):
    return sum(1 for s in sentences(text) if len(s.split()) >= k)


def _rhythm_short(before, after):
    """The SOFT check. Returns a reason to try again, or "" to accept.

    Separate from _violations because the consequence is different. A hard violation means the
    rewrite is wrong and the original is safer. This one means the rewrite is CORRECT but duller
    than it should be, and a duller-but-correct block still beats no rewrite, so the worst it can
    do is ask once more."""
    want = _long_target(before)
    got = _long_count(after)
    if want and got < want:
        return (f"only {got} sentence(s) of 18+ words came back, and this block needs at least "
                f"{want} to keep the variety it arrived with")
    return ""


def _long_target(text):
    n = _long_count(text)
    return max(1, round(n * LONG_KEEP_RATIO)) if n else 0


def _reader_noun(slug):
    """The word the article's own reader would use, for the register rule in the prompt."""
    try:
        plan = json.load(open(config.artifact(slug, "article-plan.json")))
        name = ((plan.get("persona") or {}).get("name") or "").strip()
        return name.lower() or "reader"
    except Exception:
        return "reader"


def _shape_block(reader, label, text):
    """One block through the AI, then the guards. Returns (final, moves, verdict)."""
    if words(text) < MIN_BLOCK_WORDS:
        return text, [], "too short — left alone"

    n = words(text)
    tol = max(WORD_FLOOR, round(n * WORD_TOLERANCE))
    base = (llm.load_prompt("sentence-pass.md")
            .replace("{{WORDS_NOW}}", str(n))
            .replace("{{WORDS_MIN}}", str(n - tol))
            .replace("{{WORDS_MAX}}", str(n + tol))
            .replace("{{AVG_NOW}}", str(avg_sentence(text)))
            .replace("{{LONGEST_NOW}}", str(_longest(text)))
            .replace("{{LONGEST_KEEP}}", str(max(18, int(_longest(text) * 0.8))))
            .replace("{{SENT_NOW}}", str(len(sentences(text))))
            .replace("{{LONG_NOW}}", str(_long_count(text)))
            .replace("{{LONG_KEEP}}", str(_long_target(text)))
            .replace("{{READER}}", reader)
            .replace("{{TEXT}}", text))

    prompt, last, best = base, [], None
    for attempt in (1, 2):
        try:
            out = llm.call_json(prompt) or {}
        except Exception as e:
            return (best or (text, [], f"call failed: {type(e).__name__}"))
        prose = str(out.get("prose") or "")
        if not prose.strip():
            return best or (text, [], "empty reply — original kept")
        last = _violations(text, prose)
        moves = [str(m) for m in (out.get("moves") or []) if str(m).strip()]
        if not last:
            soft = _rhythm_short(text, prose)
            verdict = "reshaped" if prose.strip() != text.strip() else "already plain"
            if not soft or attempt == 2:
                # a soft miss on the second attempt is ACCEPTED: keep whichever try held more variety
                if soft and best and _long_count(best[0]) > _long_count(prose):
                    return best[0], best[1], best[2] + " (kept the first, livelier attempt)"
                return prose, moves, verdict + (" — flatter than it should be" if soft else "")
            best = (prose, moves, verdict)
            prompt = (base + "\n\n════════════════════════════════════════\n"
                      "READ THE RHYTHM SECTION AGAIN. " + soft + ".\nHand back the same block, same "
                      "length, same facts, but leave the long sentences that carry ONE idea alone. "
                      "Only split the ones carrying two or three.")
            continue
        if attempt == 1:
            prompt = (base + "\n\n════════════════════════════════════════\n"
                      "YOUR LAST REPLY WAS REJECTED BY THE CODE CHECK: " + "; ".join(last) +
                      ".\nRe-shape the SAME block again and fix exactly that. Re-say the sentences "
                      "at the same length; do not delete anything to make room.")
    return best or (text, [], "REJECTED: " + "; ".join(last) + " — original kept")


def run(slug, redo=False):
    outp = config.artifact(slug, "sentences.json")
    if not redo and config.fresh(outp, config.artifact(slug, "readable.json"),
                                 config.artifact(slug, "coherent.json"),
                                 config.artifact(slug, "wrapper.json")):
        print(f"  reusing {outp}")
        return json.load(open(outp))

    # The latest article on the chain. readable (step 5) rewrites what coherence produced; the two
    # fallbacks are for a run that predates either step.
    src = next((config.artifact(slug, f) for f in ("readable.json", "coherent.json", "wrapper.json")
                if os.path.exists(config.artifact(slug, f))), config.artifact(slug, "wrapper.json"))
    w = json.load(open(src))
    reader = _reader_noun(slug)

    blocks = [("intro", w.get("intro") or "")]
    blocks += [("quick answer", w.get("quick_answer") or "")] if w.get("quick_answer") else []
    blocks += [(s["heading"], s["prose"]) for s in w.get("sections") or []]
    blocks += [(f"FAQ: {f['question'][:60]}", f["answer"]) for f in w.get("faq") or []]
    blocks.append(("close", w.get("close") or ""))

    whole_before = "\n\n".join(t for _, t in blocks)
    print(f"  {len(blocks)} blocks | {words(whole_before)} words | "
          f"avg sentence {avg_sentence(whole_before)} | reader: {reader}")

    with ThreadPoolExecutor(max_workers=llm.max_workers()) as ex:
        results = list(ex.map(lambda b: _shape_block(reader, *b), blocks))

    out = json.loads(json.dumps(w))                      # deep copy
    i = 0
    out["intro"] = results[i][0]; i += 1
    if w.get("quick_answer"):
        out["quick_answer"] = results[i][0]; i += 1
    for s in out.get("sections") or []:
        s["prose"] = results[i][0]; i += 1
    for f in out.get("faq") or []:
        f["answer"] = results[i][0]; i += 1
    out["close"] = results[i][0]; i += 1

    whole_after = "\n\n".join([results[k][0] for k in range(len(blocks))])
    report = {
        "slug": slug,
        "before": {"words": words(whole_before), "sentences": len(sentences(whole_before)),
                   "avg_sentence": avg_sentence(whole_before), "spread": spread(whole_before),
                   "long_share": long_share(whole_before)},
        "after": {"words": words(whole_after), "sentences": len(sentences(whole_after)),
                  "avg_sentence": avg_sentence(whole_after), "spread": spread(whole_after),
                  "long_share": long_share(whole_after)},
        "blocks": [{"block": lbl,
                    "verdict": verdict,
                    "words_before": words(orig), "words_after": words(final),
                    "avg_before": avg_sentence(orig), "avg_after": avg_sentence(final),
                    "moves": moves, "original": orig, "final": final}
                   for (lbl, orig), (final, moves, verdict) in zip(blocks, results)],
    }
    drift = (report["after"]["words"] - report["before"]["words"]) / max(1, report["before"]["words"])
    report["drift"] = round(drift * 100, 2)
    report["drift_ok"] = abs(drift) <= ARTICLE_DRIFT
    ratio = (report["after"]["spread"] / report["before"]["spread"]) if report["before"]["spread"] else 1.0
    report["spread_ratio"] = round(ratio, 2)
    report["rhythm_ok"] = ((report["after"]["spread"] >= SPREAD_OUT_FLOOR
                            and report["after"]["long_share"] >= LONG_OUT_FLOOR)
                           or ratio >= SPREAD_KEPT_FLOOR)
    rejected = [b for b in report["blocks"] if b["verdict"].startswith("REJECTED")]
    reshaped = [b for b in report["blocks"] if b["verdict"] == "reshaped"]

    config.write_json(outp, out)
    config.write_json(config.artifact(slug, "sentence-report.json"), report)
    _render(slug, report)

    print(f"  -> {outp} | reshaped {len(reshaped)}/{len(blocks)} blocks | rejected {len(rejected)}")
    print(f"  words {report['before']['words']} -> {report['after']['words']} | "
          f"avg sentence {report['before']['avg_sentence']} -> {report['after']['avg_sentence']} | "
          f"sentences {report['before']['sentences']} -> {report['after']['sentences']}")
    print(f"  rhythm: spread {report['before']['spread']} -> {report['after']['spread']} "
          f"(x{report['spread_ratio']}) | 18+ word sentences "
          f"{report['before']['long_share']:.0%} -> {report['after']['long_share']:.0%}")
    if not report["rhythm_ok"]:
        print(f"    !! RHYTHM FLAT — the finished article has a spread of {report['after']['spread']} "
              f"(floor {SPREAD_OUT_FLOOR}) and {report['after']['long_share']:.0%} of sentences at 18+ words "
              f"(floor {LONG_OUT_FLOOR:.0%}), and it kept only x{report['spread_ratio']} of what it was "
              f"given. Every sentence is landing in the same band; read it before shipping.")
    if not report["drift_ok"]:
        print(f"    !! the ARTICLE drifted {report['drift']:+.2f}% — blocks each passed, the total did not")
    for b in rejected:
        print(f"    !! {b['block'][:50]}: {b['verdict']}")
    return out


# --- the review page ---------------------------------------------------------

_TOK = re.compile(r"\[[^\]]*\]\([^)]*\)|\s+|[^\s]+")


def _diff_cols(before, after):
    """Word-level diff of one block, as two columns of HTML. Pure code, no AI."""
    E = _html.escape
    ta, tb = _TOK.findall(before or ""), _TOK.findall(after or "")
    norm = lambda t: t.strip().lower().strip(".,;:()")
    sm = difflib.SequenceMatcher(None, [norm(x) for x in ta], [norm(x) for x in tb], autojunk=False)

    def emit(toks, flags, cls):
        # merge a changed run with the spaces inside it, so one edit is one highlight
        for i, (t, ch) in enumerate(zip(toks, flags)):
            if ch or t.strip():
                continue
            prev = next((c for x, c in zip(toks[:i][::-1], flags[:i][::-1]) if x.strip()), False)
            nxt = next((c for x, c in zip(toks[i + 1:], flags[i + 1:]) if x.strip()), False)
            if prev and nxt:
                flags[i] = True
        html_out, run = [], []
        for t, ch in zip(toks, flags):
            if ch:
                run.append(t)
                continue
            if run:
                html_out.append(f'<span class="{cls}">{E("".join(run))}</span>'); run = []
            html_out.append(E(t))
        if run:
            html_out.append(f'<span class="{cls}">{E("".join(run))}</span>')
        return "".join(html_out).replace("\n", "<br>")

    fa, fb = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        eq = tag == "equal"
        fa += [not eq] * (i2 - i1)
        fb += [not eq] * (j2 - j1)
    return emit(ta, fa, "cut"), emit(tb, fb, "add")


def _render(slug, report):
    """Side by side, one row per block: what came out on the left, what went in on the right."""
    E = _html.escape
    import eval_pages
    css = """
:root{--bg:#fffdf8;--ink:#1c1a17;--mut:#6b6459;--line:#efe7d8;--card:#fff;--wash:#fff8ec;
      --acc:#fb7a00;--ok:#2e7d43;--no:#c2603a;
      --shadow:0 1px 2px rgba(28,26,23,.04),0 8px 24px rgba(28,26,23,.05)}
body{margin:0;background:var(--bg);color:var(--ink);
     font:15.5px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:40px 24px 100px}
h1{font-size:clamp(24px,4vw,32px);margin:0 0 4px;letter-spacing:-.02em}
.sub{color:var(--mut);margin:0 0 22px}
.nums{display:flex;gap:26px;flex-wrap:wrap;background:linear-gradient(180deg,var(--wash),var(--card));
      border:1px solid var(--line);border-radius:12px;padding:15px 20px;margin-bottom:22px;box-shadow:var(--shadow)}
.nums b{font-size:1.45em;display:block}.nums span{color:var(--mut);font-size:.78em}
h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--acc);margin:30px 0 8px;
   border-bottom:1px solid var(--line);padding-bottom:6px;font-weight:700}
h2 .st{float:right;text-transform:none;letter-spacing:0;color:var(--mut);font-weight:400;font-size:12px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.pane{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;
      box-shadow:var(--shadow)}
.pane .h{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin-bottom:8px}
.cut{background:#fdf3f0;color:var(--no);border-radius:3px;padding:0 2px}
.add{background:#e8f5ec;color:var(--ok);border-radius:3px;padding:0 2px}
.moves{margin:10px 0 0;padding-left:18px;color:var(--mut);font-size:13px}
.rej{color:var(--no);font-weight:600}
.q{color:var(--mut)}
a{color:var(--acc);overflow-wrap:anywhere}
@media(max-width:820px){.pair{grid-template-columns:1fr}}
""" + eval_pages.MAP_CSS
    b, a = report["before"], report["after"]
    nums = "".join(f'<div><b>{b[k]} → {a[k]}</b><span>{k.replace("_", " ")}</span></div>'
                   for k in ("words", "sentences", "avg_sentence"))
    body = [f'<div class="nums">{nums}</div>']
    for blk in report["blocks"]:
        if blk["verdict"] in ("too short — left alone", "already plain"):
            continue
        rej = blk["verdict"].startswith("REJECTED")
        st = (f'<span class="st">{blk["words_before"]} → {blk["words_after"]} words · '
              f'avg {blk["avg_before"]} → {blk["avg_after"]}</span>')
        body.append(f'<h2>{E(blk["block"])}'
                    + (f' — <span class="rej">{E(blk["verdict"])}</span>' if rej else "") + st + "</h2>")
        if rej:
            body.append('<p class="q">The original was kept. Nothing below changed.</p>')
            continue
        left, right = _diff_cols(blk["original"], blk["final"])
        body.append(f'<div class="pair"><div class="pane"><div class="h">Before</div>{left}</div>'
                    f'<div class="pane"><div class="h">After</div>{right}</div></div>')
        if blk["moves"]:
            body.append('<ul class="moves">' + "".join(f"<li>{E(m)}</li>" for m in blk["moves"]) + "</ul>")
    if len(body) == 1:
        body.append('<p class="q">No block was re-shaped — every one was already plain, or too short.</p>')
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Sentence pass — {E(slug)}</title><style>{css}</style></head><body><div class="wrap">'
            f'<h1>The sentence pass</h1>'
            f'<p class="sub">{E(slug)} — same length, same facts, shorter sentences</p>'
            + eval_pages._nav("Sentences")
            + eval_pages.reads_link("sentences")
            + "".join(body) + "</div></body></html>")
    config.write_text(config.artifact(slug, "sentence-review.html"), page)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Writer Step 6 — re-shape the sentences, with receipts.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Writer Step 6: sentence pass — {a.slug} ==")
    run(a.slug, redo=a.redo)
