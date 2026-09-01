#!/bin/bash
# RESUME THE 30 AUG REBUILD — architect onward, for the five articles whose research and planner were
# rebuilt on the night of 30 Aug 2026 with the heading fix.
#
#   ./resume_rebuild.sh              # uses DeepSeek if it has credit, else the Claude CLI
#   LLM_PROVIDER=claude ./resume_rebuild.sh
#
# WHAT IS ALREADY DONE and must NOT be repeated (it cost the whole evening):
#   · research structure, rebuilt 22:27-22:42 with the fixed heading namer. 76 question headings -> 0.
#   · the bundles, copied to research-bundle/
#   · the planner, all five, 22:43-23:46
# So this starts at the ARCHITECT. --from architect skips the planner entirely.
#
# WHY --skip-field: the field station scrapes Reddit for quotes. It is slow, optional, and write_body
# treats voices-from-the-field.md as a block that is either there or empty.
#
# WHY WRITE_SOURCE_WEB_MAX=0: the source-hunt step downloads up to 3,750 pages one at a time on the
# Claude CLI. It cost 1h46m on a single article. Sources are still verified; only the hunt for a
# REPLACEMENT source is skipped. Delete this line once DeepSeek has credit and you want it back.

set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || exit 1

export COMPANY=testlify
export WRITE_SOURCE_WEB_MAX="${WRITE_SOURCE_WEB_MAX:-0}"

# Pick the provider once, and say which, so a slow run is never a mystery.
if [ -z "${LLM_PROVIDER:-}" ]; then
  BAL=$(python3 - <<'PY' 2>/dev/null
import json, urllib.request
try:
    k = [l.split("=",1)[1].strip() for l in open("../../../.env") if l.startswith("DEEPSEEK_API_KEY=")][0]
    r = urllib.request.Request("https://api.deepseek.com/user/balance", headers={"Authorization": "Bearer " + k})
    print("yes" if json.load(urllib.request.urlopen(r, timeout=10)).get("is_available") else "no")
except Exception:
    print("no")
PY
)
  if [ "$BAL" = "yes" ]; then export LLM_PROVIDER=deepseek
  else export LLM_PROVIDER=claude; export MAX_WORKERS=1; fi
fi
echo "provider: $LLM_PROVIDER"
[ "$LLM_PROVIDER" = "claude" ] && echo "  (DeepSeek has no credit, so every call is serial on the CLI. Expect hours, not minutes.)"

SLUGS=(ai-recruitment-tools-that-can the-real-cost-recruitment-2026 the-resume-statistics-everyone-cites \
       the-validity-numbers-adverse-impact-data video-interview-software-that-actually)
LOGS="${TMPDIR:-/tmp}/resume-rebuild-logs"; mkdir -p "$LOGS"
PAR=$([ "$LLM_PROVIDER" = "deepseek" ] && echo 5 || echo 2)   # the CLI hangs under load; the API does not
echo "START $(date '+%H:%M')  |  ${#SLUGS[@]} articles, $PAR at a time, logs in $LOGS"

i=0
for s in "${SLUGS[@]}"; do
  ( echo "=== $s $(date '+%H:%M') ==="
    # --redo IS REQUIRED, AND IT IS SAFE HERE (fixed 31 Aug 00:38, after a run "finished" in 3 minutes).
    # Without it every station reuses whatever output file it already has, so the architect re-saved a
    # blueprint built on 28 Aug from the OLD research and the writer never ran at all. --from architect
    # slices the planner out of the station list entirely, so --redo cannot touch last night's planner.
    python3 -u run_article.py --slug "$s" --from architect --redo --skip-field
    echo "=== $s exit=$? $(date '+%H:%M') ===" ) > "$LOGS/$s.log" 2>&1 &
  i=$((i+1)); [ $((i % PAR)) -eq 0 ] && wait
done
wait

echo "ALL ARTICLES DONE $(date '+%H:%M')"
for s in "${SLUGS[@]}"; do printf "  %-44s %s\n" "$s" "$(tail -1 "$LOGS/$s.log" | cut -c1-60)"; done

echo "--- publish $(date '+%H:%M') ---"
python3 -u publish_reviewer.py
echo "PUBLISHED $(date '+%H:%M') -> https://devanshindian.github.io/testlify-articles-0c27c5a4/"
