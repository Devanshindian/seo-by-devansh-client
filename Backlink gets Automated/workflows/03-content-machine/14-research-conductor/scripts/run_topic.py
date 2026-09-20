#!/usr/bin/env python3
"""ONE TOPIC, ALL THE WAY THROUGH — research it, write it, mark both, stop.

  python3 run_topic.py                                  # the next topic in the queue
  python3 run_topic.py --asset "Cost per hire in 2026"   # one named topic
  python3 run_topic.py --research-only                   # stop after research
  python3 run_topic.py --write-only --slug <slug>        # write something already researched

WHY THIS EXISTS (2026-08-26, Devansh). The two halves never met. `run_research.py` researched one
topic, marked research_status done, and stopped, printing "next: /write from the bundle" for a human
to act on. Nothing followed it, so the live queue read `done` on eight rows of research and `pending`
on every row of writing — including four articles that were finished and published.

THE RULE: a topic is finished or it is the one in progress. Never a pile of half-done ones. So this
researches ONE topic, writes it, marks both, and STOPS. It does not roll into the next one. An
overnight run should be something you asked for, not something that surprises you.

IT IS PURE SEQUENCING. Research is `run_research.py`, writing is the write phase's `run_article.py`,
and both are called as they stand. No engine logic lives here.

WHY IT SHELLS OUT rather than importing: the two live in different engines with different
dependencies, and the research conductor already runs every engine this way. Keeping that means this
file adds no new import graph to go wrong.
"""
import argparse
import os
import subprocess
import sys
import tempfile

import config
import topic_pick

# config.ROOT is this ENGINE's folder, not the repo. REPO_ROOT is the repo. Using the wrong one here
# builds a path inside 14-research-conductor and the file simply is not there.
WRITE_RUNNER = os.path.join(config.REPO_ROOT, "workflows", "04-write-phase", "scripts", "run_article.py")
PUBLISHER = os.path.join(config.REPO_ROOT, "workflows", "04-write-phase", "scripts", "publish_reviewer.py")


def publish(note):
    """Push the finished articles to the reviewer's public link. Read-only to the pipeline, and NEVER
    allowed to fail a run: a push problem must not cost an article that is already written.

    Called after EACH finished article, not once at the end, so an overnight run that dies at 4am still
    leaves the morning link holding everything it managed to write.
    """
    env = dict(os.environ)
    env.setdefault("COMPANY", getattr(config, "COMPANY", "testlify"))
    try:
        code = subprocess.run([sys.executable, PUBLISHER, "-m", note], env=env).returncode
        print("   published" if code == 0 else f"   !! publish exited {code} — the article is safe, the link is not updated")
    except Exception as e:
        print(f"   !! publish failed ({type(e).__name__}: {str(e)[:70]}) — the article is safe")


def _bar(msg):
    print(f"\n{'=' * 66}\n{msg}\n{'=' * 66}")


def research(asset=None, provider="claude", model=None, redo=False):
    """Run the research conductor for one topic. Returns the slug it picked, or None."""
    fd, slug_file = tempfile.mkstemp(suffix=".slug")
    os.close(fd)
    cmd = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_research.py"),
           "--slug-out", slug_file, "--provider", provider]
    if model:
        cmd += ["--model", model]
    if asset:
        cmd += ["--asset", asset]
    if redo:
        cmd += ["--redo"]
    code = subprocess.run(cmd).returncode
    slug = ""
    try:
        with open(slug_file) as f:
            slug = f.read().strip()
    except OSError:
        pass
    finally:
        try:
            os.remove(slug_file)
        except OSError:
            pass
    if code != 0:
        print(f"\nX research exited {code} — nothing written. Fix it and run the same command again.")
        return None
    if not slug:
        # pick_next found nothing to do. Not a failure, just an empty queue.
        return None

    # THE SLUG FILE IS WRITTEN AT STEP 0, BEFORE THE GATE (2026-08-27). So "we got a slug back" does not
    # mean "this topic was researched" — a topic the gate refuses, or one DataForSEO drops for having no
    # keyword demand, still names itself on the way past and still exits 0, because neither is a crash.
    # Writing one of those would produce an article for a topic we just decided not to write. The queue
    # is the honest answer: research_status is 'done' only when the research actually finished.
    row = next((r for r in topic_pick.read_queue() if r["slug"] == slug), None)
    status = (row or {}).get("research_status", "")
    if status != "done":
        why = (row or {}).get("remarks") or f"research_status={status or 'missing'}"
        print(f"\n⏭  '{slug}' did not complete research ({why}) — not writing it.")
        return None
    return slug


def write(slug, redo=False, skip_field=False, until=None):
    """Run the write phase for one already-researched slug. Marks write_status either way."""
    cmd = [sys.executable, WRITE_RUNNER, "--slug", slug]
    if redo:
        cmd += ["--redo"]
    if skip_field:
        cmd += ["--skip-field"]
    if until:
        cmd += ["--until", until]
    env = dict(os.environ)
    env.setdefault("COMPANY", getattr(config, "COMPANY", "testlify"))
    code = subprocess.run(cmd, env=env).returncode
    if until:
        # A deliberate early stop is not a finished article, so the queue must not claim one.
        print(f"\n·  stopped after the {until} step — write_status left as it was.")
        return False
    ok = code == 0
    topic_pick.mark_written(slug, "done" if ok else "failed")
    print(f"   queue: {slug} write_status={'done' if ok else 'failed'}")
    return ok


def main():
    ap = argparse.ArgumentParser(
        description="Take one topic all the way: research it, write it, mark both, stop.")
    ap.add_argument("--asset", default=None,
                    help="a specific topic (substring match); omit to take the next one in the queue")
    ap.add_argument("--slug", default=None, help="with --write-only: which researched topic to write")
    # DEEPSEEK IS THE DEFAULT (2026-08-27). The Claude account is nearly out and Codex is quota-locked
    # until 26 September, so DeepSeek is the only provider with real capacity. It is also faster here:
    # it is an HTTP API, so llm.max_workers() returns 8 where a local CLI is pinned to 1.
    ap.add_argument("--provider", choices=["claude", "codex", "deepseek"], default="deepseek")
    ap.add_argument("--model", default=None)
    ap.add_argument("--research-only", action="store_true", help="research it, do not write it")
    ap.add_argument("--write-only", action="store_true", help="skip research; write --slug")
    ap.add_argument("--redo", action="store_true", help="rerun every step instead of reusing outputs")
    ap.add_argument("--skip-field", action="store_true", help="skip the Reddit/Blind/LinkedIn station")
    ap.add_argument("--until", default=None, help="stop after this WRITER step")
    ap.add_argument("--publish", action="store_true",
                    help="push to the reviewer link after every finished article")
    ap.add_argument("--count", type=int, default=1,
                    help="keep going until this many ARTICLES are finished (refused topics do not count)")
    a = ap.parse_args()

    if a.write_only:
        if not a.slug:
            raise SystemExit("--write-only needs --slug")
        _bar(f"WRITE ONLY — {a.slug}")
        raise SystemExit(0 if write(a.slug, a.redo, a.skip_field, a.until) else 1)

    # --count is the OVERNIGHT loop: keep taking topics until N ARTICLES exist. A topic the gate refuses
    # costs a DataForSEO call and does not count — the loop simply moves to the next one. Without this a
    # night of five commands could end with two articles and three refusals.
    done, tried = [], 0
    while len(done) < a.count and tried < a.count + config.MAX_SKIPS_PER_RUN:
        tried += 1
        n = f"[{len(done) + 1} of {a.count}]" if a.count > 1 else ""
        _bar(f"RESEARCH {n}" + (f" — {a.asset}" if a.asset else " — next topic in the queue"))
        slug = research(a.asset, a.provider, a.model, a.redo)
        if not slug:
            if a.asset or a.count == 1:
                print("\nNothing researched. Stopping.")
                raise SystemExit(1)
            print("   moving to the next topic.")
            continue

        if a.research_only:
            print(f"\n== RESEARCH DONE — {slug} ==\n   write it with:  --write-only --slug {slug}")
            raise SystemExit(0)

        _bar(f"WRITE {n} — {slug}")
        ok = write(slug, a.redo, a.skip_field, a.until)
        _bar(f"{'TOPIC DONE' if ok else 'TOPIC INCOMPLETE'} — {slug}")
        if ok:
            done.append(slug)
            if a.publish:
                publish(f"{slug} — {len(done)} of {a.count} finished overnight")
        elif a.count == 1:
            raise SystemExit(1)
        else:
            print("   moving to the next topic.")

    _bar(f"{len(done)} ARTICLE(S) FINISHED")
    for s in done:
        print(f"   · {s}")
    if a.count == 1:
        print("   Stopping here. Run the command again for the next topic.")
    raise SystemExit(0 if done else 1)


if __name__ == "__main__":
    main()
