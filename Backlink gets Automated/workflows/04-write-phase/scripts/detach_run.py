#!/usr/bin/env python3
"""Start a script in its OWN session, so nothing in the terminal that launched it can kill it.

  python3 detach_run.py ./overnight_rebuild.sh /tmp/out.log

WHY (31 Aug 00:43). `nohup ... & disown` was not enough: the overnight run was killed twice when an
unrelated command in the launching shell was terminated, because it was still in that shell's process
group and took the group signal with it. os.setsid() puts the child in a brand new session with no
controlling terminal, which is the actual fix. It then survives the terminal closing, the Claude
session ending, and any signal sent to the original group.
"""
import os, sys, subprocess

script, logpath = sys.argv[1], sys.argv[2]
log = open(logpath, "ab", buffering=0)
p = subprocess.Popen(["caffeinate", "-i", "-s", "-d", script],
                     stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                     start_new_session=True,          # os.setsid() in the child
                     cwd=os.path.dirname(os.path.abspath(script)) or ".")
print(f"detached pid {p.pid} (own session; immune to signals sent to this shell)")
