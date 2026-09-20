#!/bin/bash
# FIVE ARTICLES, OVERNIGHT. Publishes after each one, so a run that dies at 4am still leaves the
# morning link holding everything it managed to finish.
#
#   caffeinate -i ./overnight.sh
#
# Article 1 is already researched, so it only needs writing. The other four go through the whole
# chain: research -> topic gate -> STORM -> blueprint -> planner -> architect -> field -> writer.
# A topic the gate refuses costs one DataForSEO call and does NOT count toward the five.
set -u
cd "$(dirname "$0")"

export COMPANY=testlify
export LLM_PROVIDER=claude
export LLM_PROVIDER_CHAIN=claude,codex
export PROSE_PROVIDER=claude

PUB="../../../04-write-phase/scripts/publish_reviewer.py"

echo "############ 1 of 5 — the-resume-statistics-everyone-cites (already researched) ############"
python3 run_topic.py --write-only --slug the-resume-statistics-everyone-cites
python3 "$PUB" -m "the-resume-statistics-everyone-cites — 1 of 5 finished overnight"

echo "############ 2-5 of 5 — full chain, research and write ############"
python3 run_topic.py --count 4 --publish --provider claude

echo "############ FINAL PUBLISH ############"
python3 "$PUB" -m "Overnight run finished"
echo "############ DONE ############"
