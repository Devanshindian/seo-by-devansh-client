#!/usr/bin/env python3
"""THE one DataForSEO client for the asset engine. One credential, one chokepoint (convention C6).

Three things this does that the old client did not, each earned:
  1. PRE-FLIGHT BALANCE CHECK — below MIN_CREDITS the run exits cleanly having spent NOTHING.
  2. RESPONSE-SHAPE ASSERTION — the first call to each endpoint checks the fields we depend on are
     really there. Earned on 2026-07-20: reading `item.url` (the URL is actually `item.page`) produced
     a silent empty column that looked exactly like a real "0 overlap" negative result. A missing field
     must be LOUD, never silently empty.
  3. COST LOGGING — every call's real cost recorded, so a run's spend is always provable.

Credentials come from the existing single source (10-dataforseo/scripts/.env) — one account, one place.
"""
import base64, json, os, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
# The canonical credential file — ONE place to rotate (convention C6/D3), the same chain
# 10-dataforseo/scripts/dfs.py uses. Repo root: "Backlink gets Automated/.env".
_REPO_ENV = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".env"))
_LEGACY_ENV = os.path.normpath(os.path.join(HERE, "..", "..",
                               "03-content-machine", "10-dataforseo", "scripts", ".env"))

HOST = "https://api.dataforseo.com"
TIMEOUT = int(os.environ.get("DFS_TIMEOUT", "180"))
RETRIES = int(os.environ.get("DFS_RETRIES", "4"))
MIN_CREDITS = float(os.environ.get("DFS_MIN_CREDITS", "1.00"))   # exit cleanly below this
COST_LOG = os.environ.get("DFS_COST_LOG", "")                    # set by an engine to record spend


def _creds():
    """Real env vars win; else the legacy local .env; else the CANONICAL repo-root .env (read last
    so it overrides). Same chain as 10-dataforseo — one account, one place to rotate."""
    env = {}
    for p in (_LEGACY_ENV, _REPO_ENV):
        if os.path.exists(p):
            for line in open(p):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    login = os.environ.get("DFS_LOGIN") or env.get("DFS_LOGIN")
    pw = os.environ.get("DFS_PW") or env.get("DFS_PW")
    if not (login and pw):
        sys.exit(f"!! no DFS_LOGIN / DFS_PW — set them in the canonical {_REPO_ENV}")
    return login, pw


def call(endpoint, body=None):
    login, pw = _creds()
    auth = base64.b64encode(f"{login}:{pw}".encode()).decode()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        HOST + endpoint, data=data,
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
        method="POST" if data else "GET")
    last = None
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (401, 403):                      # auth is NOT transient — stop now
                sys.exit(f"!! DataForSEO auth failed ({e.code}) on {endpoint} — check the credentials. "
                         f"STOPPING so no further calls are made.")
        except Exception as e:
            last = str(e)[:120]
        if attempt < RETRIES - 1:
            time.sleep(2 ** attempt)
            print(f"    · dfs retry {attempt+1}/{RETRIES} ({last}) -> {endpoint}", file=sys.stderr)
    sys.exit(f"!! DataForSEO failed after {RETRIES} attempts on {endpoint}: {last}")


def first_result(resp):
    t = (resp.get("tasks") or [{}])[0]
    return (t.get("result") or [{}])[0] if t else {}


def balance():
    return first_result(call("/v3/appendix/user_data")).get("money", {}).get("balance")


def preflight(need=None):
    """Read the balance BEFORE spending. Below MIN_CREDITS: exit cleanly, having spent nothing."""
    b = balance()
    if b is None:
        print("  !! could not read the DataForSEO balance — continuing (paid calls fail loudly anyway)")
        return None
    print(f"  DataForSEO balance: ${b:.4f}")
    if b < MIN_CREDITS:
        sys.exit(f"!! NOT ENOUGH CREDITS: ${b:.4f} < ${MIN_CREDITS:.2f} minimum. "
                 f"Top up, then re-run — every completed step is cached and will be skipped.")
    if need and b < need:
        sys.exit(f"!! balance ${b:.4f} is below this run's estimated ${need:.2f}. Top up or reduce scope.")
    return b


_ASSERTED = set()

def assert_shape(endpoint, items, required):
    """The first time we use an endpoint, prove the fields we depend on are really populated.
    A missing field must be LOUD — a silently empty column is indistinguishable from a real negative."""
    if endpoint in _ASSERTED or not items:
        return
    _ASSERTED.add(endpoint)
    probe, missing = items[0], []
    for path in required:
        cur, ok = probe, True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False; break
        if not ok or cur in (None, ""):
            missing.append(path)
    if missing:
        sys.exit(f"!! {endpoint} did NOT return the fields this step depends on: {missing}\n"
                 f"   Available top-level keys: {sorted(probe.keys())}\n"
                 f"   Fix the field path before trusting any output (2026-07-20: `url` vs `page`).")
    print(f"  ✓ {endpoint} shape OK ({len(required)} required fields present)")


def spend(label, before, after):
    """Record what a run really cost. Call ONCE per run with the opening and closing balance —
    NOT around every call: balance() is itself an API request, and hammering it makes it return
    None, which produced impossible costs (-$12.58 then +$12.51) on 2026-07-20."""
    if before is None or after is None:
        print(f"  cost: unknown — a balance read failed ({label})")
        return None
    cost = before - after
    print(f"  cost: ${cost:.4f}   ({label})")
    if COST_LOG:
        log = []
        if os.path.exists(COST_LOG):
            try: log = json.load(open(COST_LOG))
            except Exception: log = []
        log.append({"label": label, "cost": round(cost, 4), "balance_after": after})
        d = os.path.dirname(COST_LOG) or "."
        os.makedirs(d, exist_ok=True)
        with open(COST_LOG, "w") as f:
            json.dump(log, f, indent=2)
    return cost


if __name__ == "__main__":
    print(f"balance: ${balance():.4f}")
