#!/usr/bin/env python3
"""Field source: LINKEDIN. One HTTP call per search, through a ScrapeCreators key.

What it is good for is narrow and worth stating plainly: LinkedIn posts are written for an audience, so
nobody complains here about a test they failed. What you get is the PREVAILING TAKE, which is useful for
finding what an article should push against, or stop repeating as though it were new.

Comments come back attached to the post, so there is no second call: search() returns them and fetch()
just hands them over.

The adapter contract:
    search(query, **opts) -> [ {title, url, where, comments, score, preview} ]
    fetch(thread)         -> {body, comments: [ {who, likes, text} ]}
"""
import json, time, urllib.parse, urllib.request
import config

NAME = "linkedin"
NEEDS = ()                       # nothing to configure; a query is the whole input

_BASE = "https://api.scrapecreators.com/v1/linkedin"
_CACHE = {}                      # url -> comments, filled by search() so fetch() costs nothing


# The API only accepts "last-week" or "last-month". Anything else returns zero results with
# no error, which reads as "nobody posts about this" — it is not.
def search(query, date_posted="last-month", limit=10, **_):
    key = config.sc_key()
    if not key:
        return []
    u = f"{_BASE}/search/posts?" + urllib.parse.urlencode({"query": query, "date_posted": date_posted})
    try:
        d = json.load(urllib.request.urlopen(
            urllib.request.Request(u, headers={"x-api-key": key}), timeout=45))
    except Exception:
        return []
    posts = d.get("posts") or d.get("items") or d.get("data") or []
    out = []
    for p in posts[:limit]:
        if not isinstance(p, dict):
            continue
        text = str(p.get("description") or p.get("text") or "").strip()
        if not text:
            continue
        url = str(p.get("url") or "")
        author = p.get("author") or {}
        who = author.get("name", "") if isinstance(author, dict) else str(author)
        _CACHE[url] = [{"who": str(c.get("author") or ""), "likes": 0,
                        "text": str(c.get("text") or "").strip()}
                       for c in (p.get("comments") or []) if str(c.get("text") or "").strip()]
        out.append({"title": text[:120], "url": url, "where": f"LinkedIn · {who}"[:60],
                    "score": int(p.get("likeCount") or 0),
                    "comments": int(p.get("commentCount") or 0),
                    "preview": text[:400], "src": NAME, "body": text})
    time.sleep(config.FIELD_THROTTLE)
    return out


def fetch(thread):
    """No second call. The post text and its comments already came back with the search."""
    return {"body": thread.get("body") or thread.get("preview") or "",
            "comments": _CACHE.get(thread.get("url"), [])}
