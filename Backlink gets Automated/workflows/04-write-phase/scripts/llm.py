"""The ONE "ask the AI" door for the write phase — headless Claude (default), Codex, or DeepSeek API.

  - call_text(prompt): the model's raw text. For prose steps (write a section, edit for craft).
  - call_json(prompt): parsed JSON via a tolerant extractor (handles code fences + stray prose),
    retries once with a nudge on a parse failure. For judgment steps (plan, review, gate ticks).
  - load_prompt(name): read a prompt template from prompts/.

Provider switch = LLM_PROVIDER env (claude | codex | deepseek); Claude is the repo default (free, no key).
Copied from the research-conductor engine so behaviour is identical across the repo (C2). DeepSeek reads
DEEPSEEK_API_KEY from the env or the canonical repo .env — same credential chain as the paid clients (C6).
"""
import json, os, subprocess, tempfile, urllib.request, urllib.error, sys, time
import config

# --- usage metering (repo-root usage_meter.py; cross-engine, one ledger) -----------------------
try:
    import sys as _sys, os as _os
    _repo = '/Users/devanshasawa/Desktop/SEO by Devansh/Backlink gets Automated'
    if _repo not in _sys.path:
        _sys.path.insert(0, _repo)
    import usage_meter as _meter
except Exception:
    _meter = None



def _load_deepseek_key():
    """DEEPSEEK_API_KEY: real env var wins; else read it straight from the canonical repo .env."""
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    here = os.path.dirname(os.path.abspath(__file__))
    repo_env = os.path.join(config.REPO_ROOT, ".env")   # robust: the real repo anchor, not a depth-fragile ../../../../
    for p in (os.path.join(here, ".env"), repo_env):
        if os.path.exists(p):
            for line in open(p):
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    v = line.split("=", 1)[1].strip()
                    if v:
                        return v
    return None


def _run_deepseek(prompt):
    key = _load_deepseek_key()
    if not key:
        raise RuntimeError("no DEEPSEEK_API_KEY — set it in the canonical 'Backlink gets Automated/.env'")
    # IGNORE A CLI MODEL NAME IN LLM_MODEL (2026-08-27). The mirror of _cli_model() below, and we nearly
    # shipped the bug it prevents: a run exported LLM_MODEL=sonnet for the Claude CLI, then switched
    # provider to DeepSeek, and "sonnet" would have gone up as the DeepSeek model name — every call
    # rejected, on the one provider with credit left. LLM_MODEL only counts here if it names a DeepSeek
    # model; otherwise DEEPSEEK_MODEL decides.
    _m = os.environ.get("LLM_MODEL", "")
    model = (_m if _m.startswith("deepseek") else "") or os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")  # DEFAULT = the TOP model; v4-flash = cheap
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
    if _meter:
        _meter.record_llm("deepseek", model, out.get("usage"))
    return out["choices"][0]["message"]["content"]


def _extract_json(text):
    """First balanced JSON object/array in `text`, tolerating ```json fences + stray prose."""
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
    open_ch = t[start]; close_ch = "}" if open_ch == "{" else "]"
    depth, in_str, esc = 0, False, False
    for i in range(start, len(t)):
        c = t[i]
        if in_str:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': in_str = False
            continue
        if c == '"': in_str = True
        elif c == open_ch: depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return json.loads(t[start:i + 1])
    raise ValueError("unbalanced JSON in model output")


def _cli_model():
    """The model for a CLI provider (claude/codex). IGNORE a deepseek-specific LLM_MODEL so a DeepSeek-first run
    can fall back to the claude/codex CLI without passing them a model name they don't know."""
    m = os.environ.get("LLM_MODEL", "")
    return "" if m.lower().startswith("deepseek") else m


def _run_one(provider, prompt):
    """Run ONE provider. Raises _TransientCLIError on a retryable hiccup, or a plain error on a hard failure."""
    if provider == "deepseek":
        return _run_deepseek(prompt)
    if provider == "codex":
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            output = f.name
        try:
            cmd = ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", "--ephemeral",
                   "--color", "never", "--output-last-message", output]
            model = _cli_model()
            if model:
                cmd += ["--model", model]
            r = subprocess.run(cmd + ["-"], input=prompt, capture_output=True, text=True,
                               timeout=config.CLAUDE_TIMEOUT, cwd=tempfile.gettempdir())
            if r.returncode != 0:
                raise _TransientCLIError(f"codex exited {r.returncode}: {r.stderr[:300]}")
            return open(output).read()
        finally:
            try: os.remove(output)
            except OSError: pass
    if provider == "claude":
        model = _cli_model()
        # The prompt goes on STDIN, never as an argument. A write-phase prompt carries the article's cards
        # and runs to ~1.2 MB, past the OS argument limit (ARG_MAX = 1,048,576 on macOS), so passing it as
        # an argv entry raised "OSError [Errno 7] Argument list too long" — which surfaced as "claude
        # failed" and silently fell through to the next provider. Claude could never run a real article.
        cmd = [config.CLAUDE_BIN, "-p", "--output-format", "text"] + (["--model", model] if model else [])
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=config.CLAUDE_TIMEOUT)
        if r.returncode != 0:
            raise _TransientCLIError(f"claude exited {r.returncode}: {r.stderr[:300]}")
        return r.stdout
    raise ValueError(f"unknown LLM provider {provider!r}")


def _provider_chain():
    """The provider order to try. Default = DeepSeek (top model) → Claude → Codex; the PRIMARY is LLM_PROVIDER (so
    the existing env still works), and the rest are automatic fallbacks. LLM_PROVIDER_CHAIN overrides the whole list."""
    if os.environ.get("LLM_PROVIDER_CHAIN"):
        order = [p.strip().lower() for p in os.environ["LLM_PROVIDER_CHAIN"].split(",") if p.strip()]
    else:
        primary = os.environ.get("LLM_PROVIDER", "deepseek").lower()
        # CODEX IS OUT OF THE DEFAULT CHAIN (2026-08-27). Its account hit its usage limit and does not
        # reset until 26 September, so every call to it exits 1 immediately. Left in the chain it was
        # not a fallback, it was 45 seconds of guaranteed-failing retries between each real attempt —
        # which is how a blend timeout turned into a thirty-minute stall. Put it back by naming it
        # explicitly in LLM_PROVIDER_CHAIN, or here once the quota resets.
        order = [primary] + [p for p in ("deepseek", "claude") if p != primary]
    seen = set()
    return [p for p in order if not (p in seen or seen.add(p))]


def _run(prompt):
    """Try each provider in the chain; a provider that keeps failing is skipped and the next one takes over. Only
    when EVERY provider has failed do we raise. Transient hiccups get a few backoff retries per provider first."""
    chain = _provider_chain()
    last = None
    for i, provider in enumerate(chain):
        for attempt in range(PROVIDER_ATTEMPTS):
            try:
                return _run_one(provider, prompt)
            except _TransientCLIError as e:
                last = e
                if attempt < PROVIDER_ATTEMPTS - 1:
                    _sleep_backoff(attempt, f"{provider}: {str(e)[:30]}")
            except Exception as e:          # hard failure (no key, bad model, bad provider) — don't retry, fall back
                last = e
                break
        if i < len(chain) - 1:
            print(f"    · LLM fallback: {provider} failed → trying {chain[i + 1]} ({str(last)[:45]})",
                  file=sys.stderr, flush=True)
    raise last if last else RuntimeError("all LLM providers failed")


# ---- transient-failure retry (shared shape across every engine) ------------
# A TRANSIENT CLI failure (non-zero exit / timeout — the CLI hiccups under load) needs TIME, so retry the
# SAME prompt with exponential backoff. A PARSE failure (unparseable JSON) needs a NUDGE, not time.
CLI_RETRIES = int(os.environ.get("LLM_CLI_RETRIES", "4"))
CLI_BACKOFF = float(os.environ.get("LLM_CLI_BACKOFF", "3.0"))
PROVIDER_ATTEMPTS = int(os.environ.get("LLM_PROVIDER_ATTEMPTS", "3"))   # attempts per provider before falling back to the next


class _TransientCLIError(RuntimeError):
    """The CLI itself failed (non-zero exit / timeout) — retryable with backoff."""


def _sleep_backoff(attempt, why):
    delay = CLI_BACKOFF * (2 ** attempt)
    print(f"    · CLI retry {attempt + 1}/{CLI_RETRIES} in {delay:.0f}s ({why})", file=sys.stderr, flush=True)
    time.sleep(delay)


def call_text(prompt):
    """Raw model text, with transient-CLI backoff retries. For prose steps."""
    last = None
    total = CLI_RETRIES + 1
    for attempt in range(total):
        try:
            return _run(prompt).strip()
        except _TransientCLIError as e:
            last = e
            if attempt < total - 1:
                _sleep_backoff(attempt, str(e)[:40])
    raise last


def call_json(prompt):
    """Parsed JSON, with a parse-nudge retry on top of the transient-CLI backoff. For judgment steps."""
    last = None
    total = config.LLM_RETRIES + 1 + CLI_RETRIES
    for attempt in range(total):
        p = prompt if attempt == 0 else prompt + "\n\nReturn ONLY the JSON. No other text."
        try:
            return _extract_json(_run(p))
        except Exception as e:
            last = e
            if attempt < total - 1:
                _sleep_backoff(attempt, str(e)[:40])
    raise last


def load_prompt(name):
    with open(f"{config.PROMPTS}/{name}") as f:
        return f.read()


def max_workers():
    """Safe parallelism for the ACTIVE provider — call this instead of a fixed concurrency number.
    DeepSeek is an HTTP API, so parallelise freely. The local Claude/Codex CLIs DEGRADE / HANG under concurrent
    load (a real incident we hit), so they run SERIALLY unless the caller explicitly raises CLI_CONCURRENCY."""
    provider = _provider_chain()[0]                       # match whatever _run will ACTUALLY use first (fixes the split)
    if provider == "deepseek":
        return config.SELECT_CONCURRENCY                  # single owner: the config value (env-overridable there)
    return int(os.environ.get("CLI_CONCURRENCY", "1"))   # claude / codex local CLI: serial by default
