"""The LLM caller: run a prompt through a headless CLI — Claude Code or Codex (set config.LLM_PROVIDER;
default claude) — and pull the JSON back out. No API key, no shim; the chosen CLI is already on this machine.
"""
import json, os, subprocess, tempfile
import os, sys, time
import config


def _extract_json(text):
    """Return the first balanced JSON object/array in `text`, tolerating ```json fences and stray prose."""
    t = text.strip()
    if "```" in t:                       # strip a markdown code fence if the model added one
        parts = t.split("```")
        for p in parts:
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

def call_json(prompt):
    """Run the prompt on headless Claude Code or Codex and return parsed JSON."""
    provider = config.LLM_PROVIDER
    if provider not in {"claude", "codex"}:
        raise ValueError("LLM_PROVIDER must be 'claude' or 'codex'")
    last_err = None
    cli_fails = parse_fails = 0
    for attempt in range(config.JUDGE_RETRIES + 1 + CLI_RETRIES):
        p = prompt if attempt == 0 else prompt + "\n\nReturn ONLY the JSON object. No other text."
        try:
            if provider == "claude":
                ccmd = [config.CLAUDE_BIN, "-p"] + (["--model", config.LLM_MODEL] if config.LLM_MODEL else []) + [p]
                r = subprocess.run(ccmd, capture_output=True, text=True,
                                   timeout=config.CLAUDE_TIMEOUT)
                if r.returncode != 0:
                    raise _TransientCLIError(f"claude exited {r.returncode}: {r.stderr[:300]}")
                text = r.stdout
            else:
                with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
                    output = f.name
                try:
                    cmd = ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", "--ephemeral",
                           "--color", "never", "--output-last-message", output]
                    if config.LLM_MODEL:
                        cmd += ["--model", config.LLM_MODEL]
                    r = subprocess.run(cmd + ["-"], input=p, capture_output=True, text=True,
                                       timeout=config.CLAUDE_TIMEOUT, cwd=tempfile.gettempdir())
                    if r.returncode != 0:
                        raise _TransientCLIError(f"codex exited {r.returncode}: {r.stderr[:300]}")
                    text = open(output).read()
                finally:
                    try: os.remove(output)
                    except OSError: pass
            return _extract_json(text)
        except (_TransientCLIError, subprocess.TimeoutExpired) as e:
            last_err = e
            cli_fails += 1
            if cli_fails > CLI_RETRIES:
                raise
            _sleep_backoff(cli_fails - 1, str(e)[:70])
        except Exception as e:                      # parse failure: nudge, don't wait
            last_err = e
            parse_fails += 1
            if parse_fails > config.JUDGE_RETRIES:
                raise
    raise last_err


def load_prompt(name):
    with open(f"{config.PROMPTS}/{name}") as f:
        return f.read()
