#!/usr/bin/env python3
"""DataForSEO client. Loads creds from scripts/.env (DFS_LOGIN, DFS_PW). No secret is stored in this file.

Use as a module:   from dfs import call ; call("/v3/...", [ {...task...} ])
Use as a CLI:       echo '[{...}]' | python3 dfs.py /v3/<endpoint>     (GET if no stdin body)
"""
import os, sys, json, time, base64, socket, urllib.request, urllib.error

# --- usage metering (repo-root usage_meter.py; cross-engine, one ledger) -----------------------
try:
    import sys as _sys, os as _os
    _repo = '/Users/devanshasawa/Desktop/SEO by Devansh/Backlink gets Automated'
    if _repo not in _sys.path:
        _sys.path.insert(0, _repo)
    import usage_meter as _meter
except Exception:
    _meter = None


_HERE = os.path.dirname(os.path.abspath(__file__))
RETRIES = int(os.environ.get("DFS_RETRIES", "3"))      # transient-failure retries per call
BACKOFF = float(os.environ.get("DFS_BACKOFF", "2.0"))  # seconds, doubled each retry

def _load_env():
    # Credential chain (one chokepoint, C6): real env vars win; else THE canonical repo .env
    # ("Backlink gets Automated/.env" — the ONE place to rotate); else the legacy local .env (back-compat).
    env = {}
    _repo_env = os.path.normpath(os.path.join(_HERE, "..", "..", "..", "..", ".env"))
    for p in (os.path.join(_HERE, ".env"), _repo_env):   # canonical read LAST so it overrides the legacy copy
        if os.path.exists(p):
            for line in open(p):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    login = os.environ.get("DFS_LOGIN") or env.get("DFS_LOGIN")
    pw = os.environ.get("DFS_PW") or env.get("DFS_PW")
    if not login or not pw:
        # Library code RAISES (never sys.exit): the caller decides how to fail. [A#21]
        raise RuntimeError("no DFS_LOGIN / DFS_PW — set them in the canonical 'Backlink gets Automated/.env'")
    return login, pw

def _auth():
    login, pw = _load_env()
    return base64.b64encode(f"{login}:{pw}".encode()).decode()

def call(endpoint, body=None):
    """POST body (a list of task dicts) to endpoint, or GET if body is None. Returns parsed JSON.
    Retries TRANSIENT failures (network errors, timeouts, HTTP 5xx / 429) with exponential backoff, then
    raises. A 4xx or a non-20000 API status is a real client error — raised immediately, not retried. [A#21]"""
    url = "https://api.dataforseo.com" + endpoint
    headers = {"Authorization": f"Basic {_auth()}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    last = None
    for attempt in range(RETRIES + 1):
        try:
            resp = json.load(urllib.request.urlopen(
                urllib.request.Request(url, data, headers, method="POST" if data else "GET"), timeout=120))
            if resp.get("status_code") != 20000:
                raise RuntimeError(f"API {resp.get('status_code')}: {resp.get('status_message')}")
            if _meter:
                _meter.record_llm and _meter.record_dfs(endpoint, resp.get("cost"))
            return resp
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == RETRIES:
                raise RuntimeError(f"HTTP {e.code}: {e.read().decode()[:300]}")
            last = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError, json.JSONDecodeError) as e:
            # socket.timeout is a READ timeout from urlopen. On Python 3.9 it is NOT a subclass of TimeoutError
            # (only unified in 3.10), so it escaped this retry and killed a whole run on a network blip. [Issue 6]
            if attempt == RETRIES:
                raise RuntimeError(f"transient call failed after {RETRIES} retries: {str(e)[:200]}")
            last = str(e)[:80]
        time.sleep(BACKOFF * (2 ** attempt))
        print(f"    · dfs retry {attempt + 1}/{RETRIES} ({last}) -> {endpoint}", file=sys.stderr)

def first_result(resp):
    """Convenience: tasks[0].result[0] (or {})."""
    t = (resp.get("tasks") or [{}])[0]
    return (t.get("result") or [{}])[0] if t else {}

def balance():
    r = first_result(call("/v3/appendix/user_data"))
    return r.get("money", {}).get("balance")

if __name__ == "__main__":
    ep = sys.argv[1]
    raw = sys.stdin.read().strip()
    body = json.loads(raw) if raw else None
    print(json.dumps(call(ep, body), indent=2))
