# 15-write — the WRITE engine

Turns ONE research bundle into ONE published, checklist-passing article. Reads the bundle + the
research-doc Build spec; writes an article under `projects/<company>/03-content-machine/write/out/<slug>/`.

- **The recipe + full design record:** [`write-phase-architecture.md`](write-phase-architecture.md) — the 8 stations, every kept/dropped decision, the build order. This engine is its runnable twin.
- **Run order in the machine:** last stage of the content-machine (after research layers 10–14 produce the bundle).

## How to run

```bash
cd scripts
python run_write.py --slug <bundle-slug>          # (orchestrator — built at the end of the station sequence)
```

Provider defaults to headless Claude (free, no key). Override with `LLM_PROVIDER=codex|deepseek`.

## File map

```
15-write/
  README.md                     # this file
  scripts/
    config.py                   # ALL paths + tunables from one anchor; company = one setting
    llm.py                      # the one AI caller (call_text / call_json / load_prompt)
    write_atomic.py             # crash-safe save helper (temp-file + rename), reused everywhere
    run_write.py                # (later) the orchestrator — pure sequencing, resumable
    fmt_router.py               # (Station 1) format-name -> archetype lookup
    plan_assert.py              # (Station 1) the Kind-3 assertions that freeze article-plan.json
    clean.py measure.py check_*.py assemble.py edit.py gate.py ...   # (per station)
  prompts/                      # one .md per LLM call — diffable, single-sourced, never inline in code
```

## Status

Scaffold in place (config · llm · write_atomic). Stations built one at a time — see the architecture doc's
build order (Part 6.2).
