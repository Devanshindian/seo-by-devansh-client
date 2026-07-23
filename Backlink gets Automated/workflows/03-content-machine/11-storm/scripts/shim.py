"""
Local OpenAI-compatible shim. STORM (via dspy/litellm/openai-sdk) POSTs chat-completion
requests here; we answer each by shelling out to `claude -p` or `codex exec`.
Both options use the locally authenticated CLI, so no API key is needed. Text in, text out.
"""
import asyncio, os, subprocess, threading, time, uuid, json, sys
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn

app = FastAPI()
CLAUDE = os.environ.get("CLAUDE_BIN", "claude")
CODEX = os.environ.get("CODEX_BIN", "codex")
PROVIDER = os.environ.get("SHIM_PROVIDER", "claude").lower()
MODEL = os.environ.get("SHIM_MODEL", "")   # optional: force a specific/cheaper model (e.g. 'sonnet'); blank = CLI default
TIMEOUT = int(os.environ.get("SHIM_TIMEOUT", "240"))
SEM = threading.Semaphore(int(os.environ.get("SHIM_CONCURRENCY", "3")))  # cap concurrent claude procs
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # the storm/ folder
# Log location is env-overridable so the caller can point it at the run's _work/ dir (per convention A1, a tool
# folder holds only recipe+code — run artefacts belong under projects/<company>/). Defaults to the local logs/,
# which is gitignored and truncated on startup so it can never accumulate across runs.
LOG_DIR = os.environ.get("SHIM_LOG_DIR", os.path.join(BASE, "logs"))
os.makedirs(LOG_DIR, exist_ok=True)
LOG = os.path.join(LOG_DIR, "shim.log")
CALLS = os.path.join(LOG_DIR, "calls.jsonl")
# The rich per-call trace (full prompt+response excerpts) is a DEBUG aid, off by default. It was only ever needed
# once, to diagnose the GUARD refusal. Set SHIM_DEBUG=1 to re-enable. Off = no 3.4MB file grows every run.
DEBUG = os.environ.get("SHIM_DEBUG", "").lower() in ("1", "true", "yes")
_n = {"calls": 0, "errors": 0}

def log(msg):
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")

# A benign FORMATTING note only — must NOT read like a system directive, or the model flags it as prompt
# injection and refuses on large inputs. (History of the incident it fixes: CHANGES.md.)
GUARD = ("Formatting note for this task: reply with only the requested content itself — no opening such as "
         "'Here is' or 'Sure', and no closing commentary or sign-off, and don't wrap the whole reply in code "
         "fences unless the task explicitly asks for them.\n\n---\n\n")

# Aligned with the engines' llm.py (same env-var shape, same exponential backoff, same default cap):
# a transient CLI hiccup needs TIME, not a re-prompt. 4 attempts, 3s doubling.
RETRIES = int(os.environ.get("SHIM_RETRIES", os.environ.get("LLM_CLI_RETRIES", "4")))
BACKOFF = float(os.environ.get("SHIM_BACKOFF", os.environ.get("LLM_CLI_BACKOFF", "3.0")))


def run_provider(prompt: str) -> str:
    """Run the CLI and return its text. A transient CLI hiccup (one bad exit / timeout / empty reply on one of
    STORM's ~230 calls) is RETRIED up to SHIM_RETRIES times before hard-failing — so a single blip no longer
    halts an hour-long run. A genuinely repeated failure still RAISES → handle() returns a real HTTP error →
    STORM stops instead of silently writing a thin dossier. [A#15 + 0.7]"""
    last = None
    for attempt in range(RETRIES + 1):
        try:
            return _run_provider_once(prompt)
        except Exception as e:
            last = e
            if attempt < RETRIES:
                delay = BACKOFF * (2 ** attempt)
                log(f"RETRY {attempt + 1}/{RETRIES} in {delay:.0f}s after: {str(e)[:120]}")
                time.sleep(delay)
    raise last


def _run_provider_once(prompt: str) -> str:
    prompt = GUARD + prompt
    with SEM:
        if PROVIDER == "claude":
            p = subprocess.run([CLAUDE, "-p", "--output-format", "text"] + (["--model", MODEL] if MODEL else []),
                               input=prompt.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=TIMEOUT)
            out = p.stdout.decode("utf-8", "ignore").strip()
        elif PROVIDER == "codex":
            output = os.path.join(LOG_DIR, f"codex-{uuid.uuid4().hex}.txt")
            cmd = [CODEX, "exec", "--sandbox", "read-only", "--skip-git-repo-check", "--ephemeral",
                   "--color", "never", "--output-last-message", output]
            if MODEL:
                cmd += ["--model", MODEL]
            p = subprocess.run(cmd + ["-"], input=prompt.encode("utf-8"), stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=TIMEOUT)
            out = open(output).read().strip() if os.path.exists(output) else ""
            try: os.remove(output)
            except OSError: pass
        else:
            raise ValueError("SHIM_PROVIDER must be 'claude' or 'codex'")
        err = p.stderr.decode("utf-8", "ignore")[:300]
        if p.returncode != 0:
            raise RuntimeError(f"{PROVIDER} exited {p.returncode}: {err}")
        if not out:
            raise RuntimeError(f"{PROVIDER} returned empty output (rc=0); stderr={err}")
        return out

def messages_to_prompt(messages):
    parts = []
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):  # openai "parts" format
            content = "".join(c.get("text", "") for c in content if isinstance(c, dict))
        content = (content or "").strip()
        if not content:
            continue
        if role == "system":
            parts.append(content)
        elif role == "assistant":
            parts.append("[Assistant previously said]\n" + content)
        else:
            parts.append(content)
    return "\n\n".join(parts)

async def handle(req: Request):
    body = await req.json()
    prompt = messages_to_prompt(body.get("messages", []))
    _n["calls"] += 1
    n = _n["calls"]
    log(f"CALL #{n} promptchars={len(prompt)}")
    try:
        out = await asyncio.get_event_loop().run_in_executor(None, run_provider, prompt)
    except subprocess.TimeoutExpired:
        _n["errors"] += 1
        log(f"ERROR #{n}: TIMEOUT after {TIMEOUT}s")
        return JSONResponse(status_code=504, content={"error": {
            "message": f"provider timed out after {TIMEOUT}s", "type": "upstream_timeout",
            "code": "provider_timeout"}})
    except Exception as e:
        _n["errors"] += 1
        log(f"ERROR #{n}: {str(e)[:200]}")
        return JSONResponse(status_code=502, content={"error": {
            "message": str(e)[:500], "type": "upstream_error", "code": "provider_failed"}})
    log(f"DONE #{n} outchars={len(out)}")
    # rich per-call trace — DEBUG only (SHIM_DEBUG=1). Off by default so this never grows unbounded again.
    if DEBUG:
        try:
            with open(CALLS, "a") as f:
                f.write(json.dumps({"n": n, "t": time.strftime("%H:%M:%S"),
                                    "prompt": prompt[:1200], "response": out[:1200]}) + "\n")
        except Exception:
            pass
    pt, ct = max(1, len(prompt) // 4), max(1, len(out) // 4)
    cid = "chatcmpl-" + uuid.uuid4().hex[:16]
    created = int(time.time())
    model = body.get("model", "claude-code")

    # Streaming clients (e.g. GPT-Researcher via langchain) ask for stream=true. We can't stream
    # from `claude -p`, so we emit the finished text as one SSE chunk + a stop chunk + [DONE].
    # Non-streaming callers (dspy/STORM) fall through to the plain JSON body below — unchanged.
    if body.get("stream"):
        def sse():
            first = {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
                     "choices": [{"index": 0, "delta": {"role": "assistant", "content": out},
                                  "finish_reason": None}]}
            yield f"data: {json.dumps(first)}\n\n"
            last = {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
            yield f"data: {json.dumps(last)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(sse(), media_type="text/event-stream")

    return {
        "id": cid,
        "object": "chat.completion",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": out},
                     "finish_reason": "stop"}],
        "usage": {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct},
    }

app.add_api_route("/v1/chat/completions", handle, methods=["POST"])
app.add_api_route("/chat/completions", handle, methods=["POST"])

@app.get("/health")
def health():
    return {"ok": True, "provider": PROVIDER, "calls": _n["calls"], "errors": _n["errors"]}

if __name__ == "__main__":
    open(LOG, "w").close()
    if DEBUG:
        open(CALLS, "w").close()        # truncate the trace on startup too — worst case is one run's worth
    port = int(os.environ.get("SHIM_PORT", "8081"))
    print(f"shim on :{port} -> {PROVIDER}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
