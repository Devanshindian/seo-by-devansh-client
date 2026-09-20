"""Step 3 — targeted STORM re-run on the gap queries. Runs STORM's own runner once per query and saves
each fresh run as an iteration folder INSIDE the original topic's STORM out dir:
  projects/testlify/content-machine/storm/out/<Topic>/iteration-1/, iteration-2/, ...
The original dossier is never touched. STORM's shim is auto-started if it isn't already up.

Reads:  gap-queries.json + the original dossier path (locates the topic's out dir).
Writes: projects/testlify/content-machine/storm/out/<Topic>/iteration-<i>/ (a full STORM run) + <run_dir>/storm-iterations.json (manifest).
"""
import os, sys, json, time, shutil, subprocess, urllib.request
import config

STORM_OUT = config.STORM_OUT


def _shim_ok():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8081/health", timeout=5) as r:
            return json.load(r).get("provider") == config.LLM_PROVIDER
    except Exception:
        return False


def _ensure_shim(log_dir=None):
    if _shim_ok():
        return
    print("  shim down -> starting it")
    # Shim logs go under the run dir (projects/<company>/...), not the tool folder — convention A1. [Phase 0.5]
    log_dir = log_dir or os.path.join(config.STORM_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log = open(os.path.join(log_dir, "shim.out"), "a")
    env = dict(os.environ, SHIM_PROVIDER=config.LLM_PROVIDER, SHIM_LOG_DIR=log_dir)
    if config.LLM_MODEL:
        env["SHIM_MODEL"] = config.LLM_MODEL
    subprocess.Popen([config.STORM_PYTHON, os.path.join(config.STORM_DIR, "scripts", "shim.py")],
                     cwd=config.STORM_DIR, env=env, stdout=log, stderr=log, start_new_session=True)
    for _ in range(30):
        time.sleep(1)
        if _shim_ok():
            print("  shim up")
            return
    sys.exit(f"STORM shim did not come up on :8081 — check {os.path.join(log_dir, 'shim.out')}")


def _iteration_done(dest):
    """An iteration counts as complete if its polished article exists and is non-empty (same bar as the STORM gate)."""
    p = os.path.join(dest, "storm_gen_article_polished.txt")
    return os.path.exists(p) and os.path.getsize(p) > 0


def run(queries_path, run_dir, dossier_path, redo=False):
    queries = json.load(open(queries_path)).get("queries", [])
    topic_dir = os.path.dirname(os.path.abspath(dossier_path))        # projects/testlify/content-machine/storm/out/<Topic>
    manifest_p = os.path.join(run_dir, "storm-iterations.json")
    if not queries:
        config.write_json(manifest_p, {"iterations": []})
        print("no gap queries -> no re-run")
        return

    # The topic's brief (2026-08-03): the conductor's spine.json sits with the main dossier. Each gap
    # iteration keeps its own gap QUERY as the research subject but carries the same article brief, so
    # the fill research stays inside the article's world instead of running blind.
    spine_file = os.path.join(topic_dir, "spine.json")
    hub_rel = os.path.relpath(topic_dir, STORM_OUT)   # "<Topic>" for hubs, "<hub>/<Topic>" for spokes

    iterations, shim_started = [], False
    for i, q in enumerate(queries, 1):
        dest = os.path.join(topic_dir, f"iteration-{i}")
        # RESUMABLE: skip a query whose iteration already completed (unless --redo). This makes a crash mid-Step-3
        # resume where it stopped instead of re-firing every ~7-min STORM run from scratch.
        if not redo and _iteration_done(dest):
            print(f">>> STORM iteration {i}/{len(queries)}: reusing existing (resume)")
            iterations.append({"i": i, "query": q["query"], "fills": q.get("fills", []),
                               "dir": os.path.relpath(dest, STORM_OUT)})
            continue
        if not shim_started:
            _ensure_shim(log_dir=os.path.join(run_dir, "_shim-logs")); shim_started = True
        if os.path.exists(dest):                     # a partial/failed attempt — clear it, the run rewrites in full
            shutil.rmtree(dest)
        print(f">>> STORM iteration {i}/{len(queries)}: {q['query']}")
        # --hub/--folder aim STORM's output straight at iteration-<i> (2026-08-03) — replaces the old
        # newest-folder-then-move detection, which guessed the fresh dir by mtime.
        cmd = [config.STORM_PYTHON, config.STORM_RUNNER, q["query"], "--provider", config.LLM_PROVIDER,
               "--turns", "4", "--topk", "5", "--article", "--polish",
               "--hub", hub_rel, "--folder", f"iteration-{i}"]
        if os.path.exists(spine_file):
            cmd += ["--spine-file", spine_file, "--perspectives", "4"]
        if config.LLM_MODEL:
            cmd += ["--model", config.LLM_MODEL]
        subprocess.run(cmd,
                       cwd=config.STORM_DIR, check=True)
        iterations.append({"i": i, "query": q["query"], "fills": q.get("fills", []),
                           "dir": os.path.relpath(dest, STORM_OUT) if _iteration_done(dest) else None})
    config.write_json(manifest_p, {"iterations": iterations})
    print(f"gap-fill STORM: {len(iterations)} iteration(s) -> {topic_dir}/iteration-*")


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3], redo="--redo" in sys.argv)
