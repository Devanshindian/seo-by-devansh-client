#!/usr/bin/env python3
"""THE WRITER — one entry point. Pure sequencing: it calls each step's run() in order, nothing else.

  Step 1  write_body   -> writer/_work/body.json      (one AI per section, in parallel)
  Step 2  blend        -> writer/_work/blend.json     (the editor: code counts, it cuts + weaves keywords)
  Step 3  wrapper      -> writer/_work/wrapper.json   (h1, intro, FAQ, close + touch-ups)
  Step 4  coherence    -> writer/_work/coherent.json  (reads the article WHOLE; fixes what only that reveals)
  Step 5  readable     -> writer/_work/readable.json   (rewrites the whole article to be READ)
  Step 6  sentences    -> writer/_work/sentences.json   (re-shapes the sentences; length + facts locked)
  Step 7  slop         -> writer/_work/polish.json      (AI strips the writing tells)
  Step 8  links        -> writer/_work/linked.json      (internal, read-more and external links)
  Step 9  clean        -> writer/_work/scrubbed.json    (mechanical scrub: characters + spacing, NO AI)
  Step 10 assemble     -> writer/draft.md + keyword-coverage.json + article.html

Readable owns DENSITY: it deletes facts and spends the freed words explaining the survivors, so it
changes the length and the sections. The sentence pass owns SENTENCE SHAPE and changes nothing else:
same length, same facts, same sections, every one of those checked in code. Two briefs, two steps —
put them in one prompt and they contradict each other, which was tried.

Readable sits BEFORE the three finishing steps on purpose: they then polish its wording rather than
wording it is about to replace, and the links land on the sentences a reader actually gets.

Clean runs LAST before assemble, so it scrubs the finished text: every earlier step can introduce an
invisible character or a stray dash of its own, and it is the cheapest step in the chain to re-run.

Resumable: every step reuses its output file unless --redo is passed.
"""
import argparse

import write_body
import blend
import wrapper
import coherence
import sentence_pass
import slop_pass
import links_pass
import clean
import assemble
import readable
import eval_pages
import build_share_site
import usage_page
import time as _time
import sys as _s, os as _o
_s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))))
try:
    import usage_meter as _meter
except Exception:
    _meter = None


STEPS = [("write-body", write_body), ("blend", blend), ("wrapper", wrapper),
         ("coherence", coherence), ("readable", readable), ("sentences", sentence_pass),
         ("slop", slop_pass), ("links", links_pass), ("clean", clean), ("assemble", assemble)]

# PER-STEP PROVIDER (2026-08-05). Two steps write the prose a reader actually meets — the body of every
# section, and the intro/FAQ/close. Those can be pinned to a different model from the rest.
#   PROSE_PROVIDER=claude  -> run just those two on Claude, everything else on the run's normal provider.
# Deliberately NOT the whole writer station: llm.max_workers() drops to 1 on a local CLI (they hang under
# concurrent load), so slop and links — which fan out over every block and are mechanical, code-guarded
# edits — would go serial and cost hours for no gain in prose quality.
# llm.py reads LLM_PROVIDER on every call, so setting it around a step is enough; the provider chain still
# falls through to the others if the pinned one fails, so a CLI usage limit cannot stall the run.
PROSE_STEPS = {"write-body", "wrapper"}

# The inverse switch (2026-08-06). Some steps are mechanical and code-guarded — the slop pass removes
# writing tells one block at a time, and code then verifies every number and every [c] tag survived.
# On a local CLI those run SERIALLY (llm.max_workers() == 1), so 19 blocks per article is ~13 minutes
# of wall clock on a step where the model makes no difference to what a reader sees.
#   BULK_PROVIDER=deepseek  -> run just these on the fast parallel provider, everything else on Claude.
BULK_STEPS = {"slop"}


def run(slug, redo=False, until=None):
    """Run the writer for one article. Returns True when the whole chain finished, False when
    --until stopped it early.

    THE STATION'S LOGIC LIVES HERE, NOT IN main() (2026-08-26). It used to sit inside main(), behind
    argparse, so the only way to run the writer was to type its command in a terminal. The other three
    stations already exposed run(slug, redo), which is why run_article.py can call them directly and
    could not call this one. Moving the body out is the whole change: main() is now a thin wrapper and
    `python3 run_writer.py --slug x` behaves exactly as it did before.
    """
    names = [n for n, _ in STEPS]
    if until:
        print(f"== stopping after {until}: {', '.join(names[:names.index(until) + 1])} ==")
    prose = (_o.environ.get("PROSE_PROVIDER") or "").strip().lower()
    base = _o.environ.get("LLM_PROVIDER", "deepseek")
    if prose:
        print(f"== provider: {base} · prose steps ({', '.join(sorted(PROSE_STEPS))}) on {prose} ==")
    for i, (name, mod) in enumerate(STEPS, 1):
        bulk = (_o.environ.get("BULK_PROVIDER") or "").strip().lower()
        use = (prose if (prose and name in PROSE_STEPS)
               else bulk if (bulk and name in BULK_STEPS)
               else base)
        print(f"== writer · Step {i} of {len(STEPS)}: {name} — {slug} [{use}] ==")
        _t0 = _time.time()
        _o.environ["LLM_PROVIDER"] = use
        try:
            mod.run(slug, redo=redo)
        finally:
            _o.environ["LLM_PROVIDER"] = base        # always hand the next step the normal provider
        if _meter:
            _meter.record_step(name, _time.time() - _t0, "writer", slug)
        if until and name == until:
            break
    if until and until != STEPS[-1][0]:
        # The pages that CAN be built are worth building; the rest need files that do not exist yet.
        try:
            eval_pages.build_all(slug)
        except Exception as e:
            print(f"  (page rebuild skipped: {str(e)[:70]})")
        print(f"== WRITER STOPPED AFTER {until.upper()} — {slug} ==")
        return False
    # REBUILD EVERY PAGE (2026-08-05, widened 2026-08-13). The architect builds pages too, but that runs
    # BEFORE the writer, so every writer-stage row — the article, the slop page, the links page, the
    # draft — rendered as "not built yet" and had no link. Rebuilding here, after the last file is
    # written, is the fix.
    # It called build_INDEX only, so a FULL run produced the front door and nothing behind it: the body,
    # blend, wrapper, coherence and clean review pages, and every stage read, were built ONLY on an
    # early-stopped `--until` run. build_all ends with build_index, so this covers both.
    try:
        eval_pages.build_all(slug)
    except Exception as e:
        print(f"  (page rebuild skipped: {str(e)[:70]})")
    # THE READER'S COPY (2026-08-06). writer/article.html is the REVIEW artifact — it carries keyword
    # highlights, hover tooltips and a scoring panel, so anyone sent that link reads our SEO machinery
    # instead of the article. Every run now also produces a clean page under out/<slug>/share/, plus a
    # refreshed index across every finished article. Read-only, never allowed to fail a run.
    try:
        build_share_site.run(slug)
        build_share_site.build_all()
    except Exception as e:
        print(f"  (share page skipped: {str(e)[:70]})")
    try:                                 # the cost page: read-only, and never allowed to fail a run
        usage_page.build(slug)
        usage_page.build_all()
    except Exception as e:
        print(f"  (usage page skipped: {str(e)[:70]})")
    print(f"== WRITER DONE — {slug} ==")
    return True


def main():
    ap = argparse.ArgumentParser(description="Run the writer end to end for one article.")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--redo", action="store_true", help="rerun every step instead of reusing outputs")
    # STOP EARLY. The last four steps (slop, links, clean, assemble) polish and publish; when you are
    # judging what the WRITING steps produced, running them wastes time and spends link credits on a
    # draft you are about to throw away. --until coherence stops after step 4.
    ap.add_argument("--until", choices=[n for n, _ in STEPS],
                    help="stop after this step instead of running all nine")
    a = ap.parse_args()
    if not run(a.slug, redo=a.redo, until=a.until):
        raise SystemExit(0)


if __name__ == "__main__":
    main()
