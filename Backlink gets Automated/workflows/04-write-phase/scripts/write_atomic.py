#!/usr/bin/env python3
"""Crash-safe file saves, reused by every write-phase step (project conventions C5).

WHY this exists: the pipeline resumes by trusting "output file exists = step done". A step that
crashes mid-write (Ctrl-C, sleep, power, network) would leave a HALF-written file that resume then
wrongly reuses — silent corruption. So we never write the target file directly. We write a temp file
in the SAME directory, then rename it over the target. The rename is atomic on one filesystem, so the
real file is only ever old-complete or new-complete, never half. A crash leaves a stray .tmp (ignored).

Pure helper: imports nothing from the engine, so config.py can import it with no circular dependency.
"""
import os
import json
import tempfile


def write_text(path, text):
    """Atomically write `text` to `path` (temp file in same dir -> os.replace over target)."""
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")   # SAME dir -> the rename is atomic
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.chmod(tmp, 0o644)                           # mkstemp defaults to 0600 — restore normal perms
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def write_json(path, data, indent=2):
    """Atomically write `data` as JSON to `path`."""
    write_text(path, json.dumps(data, indent=indent, ensure_ascii=False))
