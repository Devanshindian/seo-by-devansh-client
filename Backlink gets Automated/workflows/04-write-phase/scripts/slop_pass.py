#!/usr/bin/env python3
"""Writer Step 5 — SLOP PASS: strip AI writing tells from the finished article.

Reads:  writer/_work/wrapper.json (the complete article: sections + intro/faq/close)
        + prompts/slop-rules.md (the curated ruleset — THE place to tune a rule).
Writes: writer/_work/polish.json      — wrapper.json's shape, prose cleaned (assemble reads this)
        writer/_work/slop-report.json — every change (before/after/rule), before/after tell counts,
                                  and every block REJECTED by the guards
        writer/slop-review.html — the human page: red = removed, green = replaced-with

The AI proposes, CODE verifies, per block:
  - the multiset of numbers must be identical before and after (facts survive style)
  - the multiset of [c…] tags must be identical (provenance survives)
  - a malformed reply, or any violation -> that block keeps its ORIGINAL text, loudly logged.
Clean text passes through untouched — a block with no tells returns byte-identical.
"""
import argparse
import html as _html
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
import config
import llm
import tags

_NUMS = re.compile(r"\d[\d,\.]*")
_TIER1 = ["delve", "leverage", "robust", "seamless", "comprehensive", "landscape", "navigate",
          "crucial", "pivotal", "foster", "bolster", "underscore", "harness", "unlock", "elevate",
          "streamline", "empower", "myriad", "plethora", "utilize", "facilitate", "testament",
          "realm", "embark", "game-chang", "cutting-edge"]


def _map_css():
    """The step map's styles, taken from eval_pages so one stylesheet defines it."""
    import eval_pages
    return eval_pages.MAP_CSS


def _map(now):
    """The same step map every other review page carries, so this page is never a dead end."""
    import eval_pages
    return eval_pages._nav(now)


def _reads():
    """The link to the clean read of the article as it stands after this step."""
    import eval_pages
    return eval_pages.reads_link("slop")

def _rules():
    p = os.path.join(config.PROMPTS, "slop-rules.md") if hasattr(config, "PROMPTS") else None
    path = p if p and os.path.exists(p) else os.path.join(os.path.dirname(llm.__file__), "..", "prompts", "slop-rules.md")
    return open(path).read()


def _counts(text):
    low = (text or "").lower()
    return {"em_dashes": text.count("—"),
            "tier1_words": sum(low.count(w) for w in _TIER1),
            "not_just": len(re.findall(r"\bnot (?:just|only)\b", low)),
            "lets": len(re.findall(r"\blet'?s \b", low)),
            "in_conclusion": len(re.findall(r"\bin conclusion\b|\bat the end of the day\b", low))}


def _num_sig(text):
    return sorted(_NUMS.findall(text or ""))


def _tag_sig(text):
    return sorted(tags.ids(text))


def _clean_block(rules, label, text):
    """One block through the AI, then the guards. Returns (final_text, changes, verdict)."""
    if not (text or "").strip():
        return text, [], "empty"
    prompt = llm.load_prompt("slop.md").replace("{{RULES}}", rules).replace("{{TEXT}}", text)
    try:
        out = llm.call_json(prompt) or {}
    except Exception as e:
        return text, [], f"call failed: {type(e).__name__}"
    prose = str(out.get("prose") or "")
    if not prose.strip():
        return text, [], "empty reply — original kept"
    if _num_sig(prose) != _num_sig(text):
        return text, [], "REJECTED: a number changed — original kept"
    if _tag_sig(prose) != _tag_sig(text):
        return text, [], "REJECTED: a [c] tag changed — original kept"
    changes = [c for c in (out.get("changes") or []) if isinstance(c, dict) and c.get("before")]
    return prose, changes, "cleaned" if prose != text else "already clean"


def run(slug, redo=False):
    outp = config.artifact(slug, "polish.json")
    if not redo and config.fresh(outp, config.artifact(slug, "sentences.json"),
                                 config.artifact(slug, "readable.json"),
                                 config.artifact(slug, "coherent.json"), config.artifact(slug, "wrapper.json")):
        print(f"  reusing {outp}")
        return json.load(open(outp))

    # Read the LATEST article on the chain. readable (step 5) rewrites what coherence produced, so
    # its output is the current text; coherence and then the wrapper are the fallbacks for a run
    # that predates either step. Reading the wrong one would strip AI habits from wording that has
    # already been replaced.
    src = next((config.artifact(slug, f) for f in ("sentences.json", "readable.json", "coherent.json", "wrapper.json")
                if os.path.exists(config.artifact(slug, f))), config.artifact(slug, "wrapper.json"))
    w = json.load(open(src))
    rules = _rules()

    # the blocks: every piece of prose the reader will see
    blocks = [("intro", w.get("intro") or "")]
    blocks += [(s["heading"], s["prose"]) for s in w.get("sections") or []]
    blocks += [(f"FAQ: {f['question'][:60]}", f["answer"]) for f in w.get("faq") or []]
    blocks.append(("close", w.get("close") or ""))

    before_all = _counts("\n\n".join(t for _, t in blocks))
    print(f"  {len(blocks)} blocks | before: {before_all}")

    with ThreadPoolExecutor(max_workers=llm.max_workers()) as ex:
        results = list(ex.map(lambda b: _clean_block(rules, *b), blocks))

    # place the cleaned text back into the wrapper shape
    out = json.loads(json.dumps(w))                       # deep copy
    i = 0
    out["intro"] = results[i][0]; i += 1
    for s in out.get("sections") or []:
        s["prose"] = results[i][0]; i += 1
    for f in out.get("faq") or []:
        f["answer"] = results[i][0]; i += 1
    out["close"] = results[i][0]; i += 1

    after_all = _counts("\n\n".join([out.get("intro") or ""]
                                    + [s["prose"] for s in out.get("sections") or []]
                                    + [f["answer"] for f in out.get("faq") or []]
                                    + [out.get("close") or ""]))

    report = {"slug": slug, "before": before_all, "after": after_all,
              "blocks": [{"block": lbl, "verdict": verdict, "changes": changes}
                         for (lbl, _), (_, changes, verdict) in zip(blocks, results)]}
    rejected = [b for b in report["blocks"] if b["verdict"].startswith("REJECTED")]
    changed = [b for b in report["blocks"] if b["verdict"] == "cleaned"]

    config.write_json(outp, out)
    config.write_json(config.artifact(slug, "slop-report.json"), report)
    _render(slug, report)

    print(f"  -> {outp} | cleaned {len(changed)}/{len(blocks)} blocks | "
          f"{sum(len(b['changes']) for b in report['blocks'])} changes | rejected {len(rejected)}")
    print(f"  after : {after_all}")
    for b in rejected:
        print(f"    !! {b['block'][:50]}: {b['verdict']}")
    return out


def _render(slug, report):
    """The review page: every change, red -> green, grouped by block. Pure code, no AI."""
    E = _html.escape
    css = """
:root{--bg:#fffdf8;--ink:#1c1a17;--mut:#6b6459;--line:#efe7d8;--card:#fff;--wash:#fff8ec;
      --acc:#fb7a00;--ok:#2e7d43;--no:#c2603a;
      --shadow:0 1px 2px rgba(28,26,23,.04),0 8px 24px rgba(28,26,23,.05)}
body{margin:0;background:var(--bg);color:var(--ink);
     font:15.5px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:880px;margin:0 auto;padding:40px 24px 100px}
h1{font-size:clamp(24px,4vw,32px);margin:0 0 4px;letter-spacing:-.02em}
.sub{color:var(--mut);margin:0 0 22px}
.nums{display:flex;gap:26px;flex-wrap:wrap;background:linear-gradient(180deg,var(--wash),var(--card));
      border:1px solid var(--line);border-radius:12px;padding:15px 20px;margin-bottom:22px;box-shadow:var(--shadow)}
.nums b{font-size:1.45em;display:block}.nums span{color:var(--mut);font-size:.78em}
h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--acc);margin:28px 0 8px;
   border-bottom:1px solid var(--line);padding-bottom:6px;font-weight:700}
.row,.chg{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;
          margin:8px 0;box-shadow:var(--shadow)}
.row .m{color:var(--mut);font-size:.86em}
.chg .rule{font-size:.72em;color:var(--acc);text-transform:uppercase;letter-spacing:.08em;font-weight:700}
.chip{display:inline-block;background:var(--wash);border:1px solid var(--line);border-radius:100px;
      padding:1px 9px;font-size:.74em;color:var(--mut);margin-left:6px}
del{color:var(--no);background:#fdf3f0;text-decoration:line-through;border-radius:3px;padding:0 2px}
ins{color:var(--ok);background:#e8f5ec;text-decoration:none;border-radius:3px;padding:0 2px}
.arrow{color:var(--mut);margin:0 6px}
.rej{color:var(--no);font-weight:600}
.ok{color:var(--ok);font-weight:600}.no{color:var(--no);font-weight:600}
.q{color:var(--mut)}
a{color:var(--acc);overflow-wrap:anywhere}
mark{background:#ffe9ad;color:#1c1a17;border-radius:3px;padding:0 3px}
""" + _map_css()
    b, a = report["before"], report["after"]
    blocks = report.get("blocks") or []
    n_changes = sum(len(x.get("changes") or []) for x in blocks)
    n_rej = sum(1 for x in blocks if str(x.get("verdict") or "").startswith("REJECTED"))
    n_touched = sum(1 for x in blocks if x.get("changes"))
    # The old headline was five raw-key counters that read 0 → 0 on every run, above a page full of
    # real rewrites: the counters track literal tells (em dashes, "not just"), and the model rewrites
    # the phrasing instead of leaving one behind. Count the work that actually happened.
    nums = "".join(f"<div><b>{v}</b><span>{k}</span></div>" for k, v in (
        ("changes made", n_changes), ("blocks touched", n_touched),
        ("blocks rejected", n_rej), ("blocks read", len(blocks))))
    tells = ", ".join(f'{k.replace("_", " ")} {b[k]}&nbsp;→&nbsp;{a[k]}' for k in b)
    body = [f'<div class="nums">{nums}</div>',
            '<p class="q">This step strips the tells that mark writing as machine-made: the em dash '
            'used as a pause, the inflated word, the "not just X but Y" shape, the throat-clearing '
            'opener. It rewrites the phrasing rather than deleting a word, so the literal counters '
            f'below usually read zero even on a page full of changes. Literal tells: {tells}.</p>']
    for blk in report["blocks"]:
        if not blk["changes"] and not blk["verdict"].startswith("REJECTED"):
            continue
        body.append(f'<h2>{E(blk["block"])}'
                    + (f' — <span class="rej">{E(blk["verdict"])}</span>' if blk["verdict"].startswith("REJECTED") else "")
                    + "</h2>")
        for c in blk["changes"]:
            body.append(f'<div class="chg"><div class="rule">{E(str(c.get("rule") or ""))}</div>'
                        f'<del>{E(str(c.get("before") or ""))}</del><span class="arrow">→</span>'
                        f'<ins>{E(str(c.get("after") or "")) or "(removed)"}</ins></div>')
    if len(body) == 1:
        body.append('<p class="q">No changes — the article had no tells the ruleset catches.</p>')
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Slop pass — {E(slug)}</title><style>{css}</style></head><body><div class="wrap">'
            f'<h1>The AI-slop pass</h1>'
            f'<p class="sub">{E(slug)} — what was removed, and what replaced it</p>'
            + _map("Slop pass")
            + _reads()
            + "".join(body) + "</div></body></html>")
    config.write_text(config.artifact(slug, "slop-review.html"), page)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Writer Step 5 — strip AI writing tells, with receipts.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    print(f"== Writer Step 5: slop pass — {a.slug} ==")
    run(a.slug, redo=a.redo)
