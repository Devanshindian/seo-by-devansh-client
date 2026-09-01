#!/bin/bash
# OVERNIGHT: wait for the Claude usage limit to renew, then finish the rebuild and push to GitHub.
#
#   caffeinate -i -s ./overnight_rebuild.sh > /tmp/overnight.log 2>&1 &
#
# WHY THIS EXISTS. On the night of 30 Aug the account was at ~80% of its usage limit with about three
# hours until it renewed, and the machine was being left on charge overnight. Nothing needs a human
# awake for any of it: this probes cheaply until the limit clears, runs the work, and only exits once
# the articles are published. It survives the Claude session ending, because it is just a shell script.
#
# It does NOT repeat what was already done on the 30th (research structure, bundles, planner, all five).
# resume_rebuild.sh starts at the architect. See memory note rebuild-paused-30-aug.

set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$HERE" || exit 1
LOG="${TMPDIR:-/tmp}/overnight-rebuild.log"
say() { echo "[$(date '+%d %b %H:%M')] $*" | tee -a "$LOG"; }

PROBE_EVERY=600          # 10 min between probes; the limit renews on the hour, not on our schedule
MAX_WAIT_HOURS=10        # per wait. The limit renews in ~3.5h, so this has a wide margin.
RUN_TRIES=12             # each retry WAITS for capacity first, so this is 12 real attempts, not 12 quick failures

say "=== overnight rebuild armed ==="

# ---------------------------------------------------------------- 1. wait for capacity
# A one-word prompt is the cheapest possible probe. If the limit is exhausted the CLI errors or says
# so in its output; either way we are not ready. DeepSeek is checked first because if it ever gets
# topped up it is both faster and does not touch the Claude quota at all.
deepseek_live() {
  python3 - <<'PY' 2>/dev/null
import json, urllib.request
try:
    k = [l.split("=",1)[1].strip() for l in open("../../../.env") if l.startswith("DEEPSEEK_API_KEY=")][0]
    r = urllib.request.Request("https://api.deepseek.com/user/balance", headers={"Authorization": "Bearer " + k})
    print("yes" if json.load(urllib.request.urlopen(r, timeout=10)).get("is_available") else "no")
except Exception:
    print("no")
PY
}

# WHITELIST, NOT BLACKLIST (hardened 31 Aug 00:52). The first version listed the error phrases it knew
# about and treated anything else as success. That is backwards: one unrecognised wording for "limit
# reached" and the probe reports capacity that is not there, every attempt fails instantly, and the 12
# retries burn out in half an hour — at 01:15, hours before the quota actually renews. So the test is
# now positive: the CLI must return the exact word we asked for. Anything else, for any reason, counts
# as no capacity and we keep waiting. A false "not ready" costs 10 minutes; a false "ready" costs the night.
claude_live() {
  # macOS has no `timeout`; perl's alarm is the portable equivalent and is always present.
  out=$(echo "Reply with the single word: ready" | perl -e 'alarm 120; exec @ARGV' claude -p --output-format text 2>&1)
  [ $? -eq 0 ] || return 1
  case "$(printf '%s' "$out" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:][:punct:]')" in
    ready) return 0 ;;
  esac
  return 1
}

# THIS IS A FUNCTION, NOT A ONE-TIME WAIT, AND THAT IS THE WHOLE POINT (fixed before launch).
# The first version waited for capacity once, then allowed 3 retries 10 minutes apart. That is a
# 30-minute retry budget against a usage limit that renews in HOURS: the run would exhaust its
# retries around 01:00 and publish a half-finished set at exactly the moment it should have been
# waiting. Every attempt now waits for real capacity first, so the script sleeps through the whole
# outage however long it lasts and starts the moment the quota is back.
wait_for_capacity() {
  local waited=0
  while :; do
    if [ "$(deepseek_live)" = "yes" ]; then
      say "DeepSeek has credit — using it (fast path, no Claude quota used)"
      export LLM_PROVIDER=deepseek; unset MAX_WORKERS 2>/dev/null || true
      return 0
    fi
    if claude_live; then
      say "Claude CLI is answering — capacity is available"
      export LLM_PROVIDER=claude MAX_WORKERS=1
      return 0
    fi
    waited=$((waited + PROBE_EVERY))
    if [ $waited -ge $((MAX_WAIT_HOURS * 3600)) ]; then
      say "!! still no capacity after ${MAX_WAIT_HOURS}h of waiting"
      return 1
    fi
    say "no capacity yet (waited $((waited/60)) min) — probing again in $((PROBE_EVERY/60)) min"
    sleep "$PROBE_EVERY"
  done
}

wait_for_capacity || { say "!! never got capacity — nothing run"; exit 1; }

# ---------------------------------------------------------------- 2. run it, retrying if it dies
# A HANG IS THE REAL RISK, NOT AN ERROR. When the Claude CLI runs out of quota it does not always fail
# cleanly — on 30 Aug a run sat at 0% CPU with every thread blocked for 45 minutes before it was noticed.
# So each attempt gets a hard wall-clock ceiling. If it is exceeded the attempt is killed and retried,
# and because every step reuses its finished output file, the retry picks up where the last one stopped.
RUN_CEILING=$((4 * 3600))
ok=0
for try in $(seq 1 $RUN_TRIES); do
  say "--- run attempt $try of $RUN_TRIES (ceiling $((RUN_CEILING/3600))h) ---"
  perl -e "alarm $RUN_CEILING; exec @ARGV" ./resume_rebuild.sh >> "$LOG" 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then ok=1; say "run attempt $try finished"; break; fi
  if [ $rc -eq 142 ] || [ $rc -eq 14 ]; then
    say "!! attempt $try hit the ${RUN_CEILING}s ceiling and was killed — almost certainly a CLI hang"
    pkill -f "run_article.py --slug" 2>/dev/null
  else
    say "!! attempt $try exited $rc"
  fi
  # 15 min floor between attempts: 12 attempts then span at least 3 hours, which covers the renewal
  # window even if the probe is wrong about capacity.
  say "   waiting 15 min, then for capacity, before retrying (finished steps are reused, nothing repeats)"
  sleep 900
  wait_for_capacity || { say "!! no capacity for the retry — publishing what finished"; break; }
done
[ $ok -eq 1 ] || say "!! all $RUN_TRIES attempts failed — publishing whatever finished anyway"

# ---------------------------------------------------------------- 3. publish, and PROVE it landed
# resume_rebuild.sh publishes at the end, but it may not have reached that line. Publishing twice is
# harmless (the push is a no-op when nothing changed), and never publishing is the failure that matters.
say "--- publishing ---"
COMPANY=testlify python3 -u publish_reviewer.py >> "$LOG" 2>&1
REPO="../../../projects/testlify/04-write-phase/reviewer/_pages-repo"
say "last commit: $(git -C "$REPO" log -1 --format='%h %ad %s' --date=format:'%d %b %H:%M' 2>/dev/null)"
say "unpushed commits: $(git -C "$REPO" rev-list --count @{u}..HEAD 2>/dev/null || echo '?')"

for i in $(seq 1 20); do
  code=$(curl -s -m 20 -o /dev/null -w '%{http_code}' https://devanshindian.github.io/testlify-articles-0c27c5a4/)
  [ "$code" = "200" ] && { say "live: HTTP 200"; break; }
  sleep 30
done

say "=== DONE — https://devanshindian.github.io/testlify-articles-0c27c5a4/ ==="
