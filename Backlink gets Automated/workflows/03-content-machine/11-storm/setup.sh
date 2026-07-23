#!/usr/bin/env bash
# Rebuild the self-contained STORM venv from scratch (disaster recovery).
# The venv and the full source both live inside this folder — nothing in your home dir.
set -e
cd "$(dirname "$0")"

echo ">> creating local venv (Python 3.11)"
uv venv venv --python 3.11

# Install the exact working dependency set. dspy-ai declares an old `datasets` pin that
# conflicts with the newer datasets we need (the HF-stack fix), so install it --no-deps.
echo ">> installing dependencies from requirements.lock"
grep -iv '^dspy-ai' requirements.lock > /tmp/storm-req.txt
uv pip install --python venv/bin/python -r /tmp/storm-req.txt
uv pip install --python venv/bin/python --no-deps dspy-ai==2.4.9

# Point the venv at the VISIBLE local source (./engine/knowledge_storm), so our edits are what runs.
echo "$PWD/engine" > venv/lib/python3.11/site-packages/_storm_local.pth

echo ">> done. Test with:"
echo "   venv/bin/python -c 'import knowledge_storm; print(knowledge_storm.__file__)'"
