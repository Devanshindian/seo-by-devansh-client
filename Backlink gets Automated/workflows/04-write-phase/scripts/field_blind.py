#!/usr/bin/env python3
"""Field source: TEAMBLIND. Public pages only. No login, no account, no credentials anywhere.

Blind is a Next.js app: the page ships its data inside `self.__next_f.push([1,"..."])` chunks that
concatenate into one JSON payload. The post body and the whole comment tree are in there, and every
poster carries a VERIFIED EMPLOYER, which is the one thing no other source in this set can give.

Its search has NO date filter, NO channel filter and NO operators, and returns 20 results with no
working pagination. So the planner is told to send several narrow queries rather than one broad one.

The adapter contract:
    search(query, **opts) -> [ {title, url, where, comments, score, preview} ]
    fetch(thread)         -> {body, comments: [ {who, likes, text} ]}
"""
import json, re, time, urllib.parse, urllib.request
import config

NAME = "blind"
NEEDS = ()                       # nothing to configure; a query is the whole input

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


class _R308(urllib.request.HTTPRedirectHandler):
    """Search returns /article/<id>; the real page is /post/<slug> behind a 308, which Python's own
    redirect handler does not follow."""
    def http_error_308(self, req, fp, code, msg, headers):
        return self.http_error_301(req, fp, 301, msg, headers)


_OPENER = urllib.request.build_opener(_R308)


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9"})
    return _OPENER.open(req, timeout=40).read().decode("utf-8", "ignore")


def _flight(html_text):
    chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*"((?:[^"\\]|\\.)*)"\]\)', html_text)
    return "".join(json.loads('"%s"' % c) for c in chunks)


def _balanced(payload, start):
    open_ch = payload[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth, in_str, esc = 0, False, False
    for i in range(start, len(payload)):
        c = payload[i]
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
                return payload[start:i + 1]
    return None


def search(query, limit=20, **_):
    try:
        p = _flight(_get("https://www.teamblind.com/search/" + urllib.parse.quote(query)))
    except Exception:
        return []
    i = p.find('"articleList"')
    if i < 0:
        return []
    try:
        rows = json.loads(_balanced(p, p.find("[", i)))
    except Exception:
        return []
    out = []
    for r in rows[:limit]:
        if not isinstance(r, dict) or not r.get("title"):
            continue
        out.append({"title": (r.get("title") or "").strip(),
                    "url": "https://www.teamblind.com" + (r.get("scheme") or ""),
                    # the channel is visible on a result but cannot be searched inside
                    "where": (r.get("channelDetails") or {}).get("displayName", "") or "Blind",
                    "score": int(r.get("likeCnt") or 0), "comments": int(r.get("commentCnt") or 0),
                    "preview": (r.get("content") or "")[:300], "src": NAME,
                    "poster": r.get("memberCompanyName") or ""})
    time.sleep(config.FIELD_THROTTLE)
    return out


def _flatten(nodes, depth=0, acc=None):
    acc = acc if acc is not None else []
    for c in nodes or []:
        t = (c.get("contentRaw") or c.get("content") or "").strip()
        if t:
            acc.append({"who": c.get("companyName", ""), "likes": int(c.get("likeCnt") or 0), "text": t})
        _flatten(c.get("recomments"), depth + 1, acc)
    return acc


def fetch(thread):
    try:
        p = _flight(_get(thread["url"]))
    except Exception:
        return {"body": "", "comments": []}
    comments = []
    i = p.find('"commentList"')
    if i >= 0:
        try:
            comments = _flatten(json.loads(_balanced(p, p.find("[", i))))
        except Exception:
            pass
    body = ""
    m = re.search(r'"contentRaw":"((?:[^"\\]|\\.)*)"', p)
    if m:
        body = json.loads('"%s"' % m.group(1))[:800]
    return {"body": body, "comments": comments}
