"""The LLM caller: run a prompt through a headless CLI (Claude Code or Codex) OR direct API (DeepSeek) —
set config.LLM_PROVIDER to 'claude' / 'codex' / 'deepseek'; default claude. Two entry points:
  - call_json(prompt): for DATA steps — returns parsed JSON, retries once on a parse failure.
  - call_text(prompt): for PROSE steps (write-ups / assembly) — returns the raw text.
DeepSeek needs DEEPSEEK_API_KEY (real env var, or read straight from the canonical repo .env — same
credential chain as dfs.py, C6). DEEPSEEK_MODEL picks the tier (default 'deepseek-chat' = cheap v4-flash;
set DEEPSEEK_MODEL=deepseek-v4-pro for the top model). No shim, no CLI — one direct HTTPS call.
"""
import json, os, subprocess, tempfile, urllib.request, urllib.error
import os, sys, time
import config


def _extract_json(text):
    """First balanced JSON object/array in `text`, tolerating ```json fences and stray prose."""
    t = text.strip()
    if "```" in t:
        for p in t.split("```"):
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{") or p.startswith("["):
                t = p
                break
    start = next((i for i, c in enumerate(t) if c in "{["), None)
    if start is None:
        raise ValueError("no JSON found in model output")
    open_ch = t[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth, in_str, esc = 0, False, False
    for i in range(start, len(t)):
        c = t[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return json.loads(t[start:i + 1])
    raise ValueError("unbalanced JSON in model output")


# ---- transient-failure retry (shared shape across every engine) ------------------------------------
# TWO different failures used to share one retry budget, with no pause between attempts:
#   * a TRANSIENT CLI failure (the CLI exits non-zero / times out — it hiccups under load). Re-prompting
#     does nothing for this; it needs TIME. Retry the SAME prompt with exponential backoff.
#   * a PARSE failure (the model returned unparseable JSON). Time doesn't help; it needs a nudge.
# One retry with no backoff is almost no retry at all against a briefly rate-limited CLI — it stopped two
# real runs. Budgets are separate and capped, and every attempt is announced so a flaky CLI is visible.
CLI_RETRIES = int(os.environ.get("LLM_CLI_RETRIES", "4"))     # transient CLI failures (capped)
CLI_BACKOFF = float(os.environ.get("LLM_CLI_BACKOFF", "3.0")) # seconds, doubled each attempt


class _TransientCLIError(RuntimeError):
    """The CLI itself failed (non-zero exit / timeout) — retryable with backoff."""


def _sleep_backoff(attempt, why):
    delay = CLI_BACKOFF * (2 ** attempt)
    print(f"    · CLI retry {attempt + 1}/{CLI_RETRIES} in {delay:.0f}s ({why})", file=sys.stderr, flush=True)
    time.sleep(delay)


def _load_deepseek_key():
    """DEEPSEEK_API_KEY: real env var wins; else read it straight from the canonical repo .env —
    mirrors dfs.py's _load_env (C6), so it works whether or not the shell already sourced .env."""
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    _here = os.path.dirname(os.path.abspath(__file__))
    _repo_env = os.path.normpath(os.path.join(_here, "..", "..", "..", "..", ".env"))
    for p in (os.path.join(_here, ".env"), _repo_env):
        if os.path.exists(p):
            for line in open(p):
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    v = line.split("=", 1)[1].strip()
                    if v:
                        return v
    return None


def _run_deepseek(prompt):
    """Direct HTTPS call to DeepSeek's API — no CLI, no shim."""
    key = _load_deepseek_key()
    if not key:
        raise RuntimeError("no DEEPSEEK_API_KEY — set it in the canonical 'Backlink gets Automated/.env'")
    model = config.LLM_MODEL or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.deepseek.com/chat/completions", data=body,
                                  headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=config.CLAUDE_TIMEOUT) as r:
            out = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise _TransientCLIError(f"deepseek HTTP {e.code}: {e.read()[:300].decode('utf-8', 'ignore')}")
    except urllib.error.URLError as e:
        raise _TransientCLIError(f"deepseek network error: {str(e)[:200]}")
    return out["choices"][0]["message"]["content"]


def _run(prompt):
    provider = config.LLM_PROVIDER
    if provider == "deepseek":
        return _run_deepseek(prompt)
    if provider == "codex":
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            output = f.name
        try:
            cmd = ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", "--ephemeral",
                   "--color", "never", "--output-last-message", output]
            if config.LLM_MODEL:
                cmd += ["--model", config.LLM_MODEL]
            r = subprocess.run(cmd + ["-"], input=prompt, capture_output=True, text=True,
                               timeout=config.CLAUDE_TIMEOUT, cwd=tempfile.gettempdir())
            if r.returncode != 0:
                raise _TransientCLIError(f"codex exited {r.returncode}: {r.stderr[:300]}")
            return open(output).read()
        finally:
            try: os.remove(output)
            except OSError: pass
    if provider != "claude":
        raise ValueError("LLM_PROVIDER must be 'claude', 'codex', or 'deepseek'")
    cmd = [config.CLAUDE_BIN, "-p"] + (["--model", config.LLM_MODEL] if config.LLM_MODEL else []) + [prompt]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=config.CLAUDE_TIMEOUT)
    if r.returncode != 0:
        raise _TransientCLIError(f"claude exited {r.returncode}: {r.stderr[:300]}")
    return r.stdout



def call_json(prompt):
    """Run on headless Claude; return parsed JSON. Retries with backoff on a parse/CLI failure."""
    last = None
    total = config.LLM_RETRIES + 1 + CLI_RETRIES
    for attempt in range(total):
        p = prompt if attempt == 0 else prompt + "\n\nReturn ONLY the JSON. No other text."
        try:
            return _extract_json(_run(p))
        except Exception as e:
            last = e
            if attempt < total - 1:          # don't sleep after the FINAL failed attempt
                _sleep_backoff(attempt, str(e)[:40])
    raise last


def call_text(prompt):
    """Run on the headless CLI; return raw text (prose write-ups / assembly).
    Same capped transient-CLI retry as call_json — these steps had NO retry at all, so a single CLI
    hiccup during a write-up killed the whole run."""
    cli_fails = 0
    while True:
        try:
            return _run(prompt).strip()
        except (_TransientCLIError, subprocess.TimeoutExpired) as e:
            cli_fails += 1
            if cli_fails > CLI_RETRIES:
                raise
            _sleep_backoff(cli_fails - 1, str(e)[:70])


def load_prompt(name):
    with open(f"{config.PROMPTS}/{name}") as f:
        return f.read()
