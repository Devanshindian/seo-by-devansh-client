#!/usr/bin/env python3
"""Field source: REDDIT. Free through old.reddit HTML; the paid endpoint takes over when that blocks.

The adapter contract, shared by every field source:
    search(query, **opts) -> [ {title, url, where, comments, score, preview} ]
    fetch(thread)         -> {body, comments: [ {who, likes, text} ]}

Reddit needs subreddits named. That is what 01-brand-context/9-field-sources produces.

Two things learned the hard way and encoded here:
  * old.reddit SEARCH pages use `search-result` markup, not the `thing` markup of a listing page.
  * A rate-limited old.reddit returns a LOGIN PAGE with HTTP 200. Parsed naively that reads as "no
    results", which is indistinguishable from an empty subreddit. It is detected explicitly.
"""
import json, re, time, urllib.parse, urllib.request
import config

NAME = "reddit"
NEEDS = ("subreddits",)          # the planner must supply these


class _R308(urllib.request.HTTPRedirectHandler):
    def http_error_308(self, req, fp, code, msg, headers):
        return self.http_error_301(req, fp, 301, msg, headers)


_OPENER = urllib.request.build_opener(_R308)
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

_RESULT = re.compile(
    r'<div class="[^"]*search-result search-result-link.*?'
    r'<a href="(?P<url>[^"]+)" class="search-title[^"]*"\s*>(?P<title>.*?)</a>.*?'
    r'<span class="search-score">(?P<score>[\d,]+) point.*?'
    r'class="search-comments[^"]*"\s*>(?P<comments>[\d,]+) comment', re.S)
_TAG = re.compile(r"<[^>]+>")


def _clean(t):
    import html
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", t or ""))).strip()


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    return _OPENER.open(req, timeout=timeout).read().decode("utf-8", "ignore")


def _paid(path, params):
    key = config.sc_key()
    if not key:
        return None
    u = f"{config.SC_REDDIT}/{path}?" + urllib.parse.urlencode(params)
    try:
        return json.load(urllib.request.urlopen(
            urllib.request.Request(u, headers={"x-api-key": key}), timeout=45))
    except Exception:
        return None


def search(query, subreddits=(), limit=8, **_):
    """One search per subreddit. Free path first; the paid one only when free is blocked."""
    out = []
    for sub in subreddits:
        rows, blocked = [], False
        u = (f"https://old.reddit.com/r/{urllib.parse.quote(sub)}/search?q={urllib.parse.quote(query)}"
             f"&restrict_sr=on&sort=top&t=year")
        try:
            page = _get(u)
            if "search-result" not in page:
                blocked = True                     # login wall, not an empty result set
            else:
                for m in _RESULT.finditer(page):
                    rows.append({"title": _clean(m.group("title")), "url": m.group("url"),
                                 "where": f"r/{sub}", "score": int(m.group("score").replace(",", "")),
                                 "comments": int(m.group("comments").replace(",", "")),
                                 "preview": "", "src": NAME, "via": "free"})
                    if len(rows) >= limit:
                        break
        except Exception:
            blocked = True
        if blocked:
            d = _paid("subreddit/search", {"subreddit": sub, "query": query,
                                           "sort": "top", "timeframe": "year"})
            for p in ((d or {}).get("posts") or (d or {}).get("items") or (d or {}).get("data") or [])[:limit]:
                url = p.get("url") or p.get("permalink") or ""
                rows.append({"title": str(p.get("title") or ""),
                             "url": url if url.startswith("http") else "https://www.reddit.com" + url,
                             "where": f"r/{sub}", "score": int(p.get("score") or 0),
                             "comments": int(p.get("num_comments") or 0),
                             "preview": str(p.get("selftext") or "")[:300], "src": NAME, "via": "paid"})
        out += rows
        time.sleep(config.FIELD_THROTTLE)
    return out


_CBODY = re.compile(r'<div class="md">(.*?)</div>', re.S)


def fetch(thread):
    """Full comment tree for one thread. Free path first, paid fallback."""
    url = thread["url"].split("?")[0].rstrip("/")
    try:
        page = _get(url + "/?sort=top&limit=500")
        if "sitetable" in page or 'class="md"' in page:
            bodies = [_clean(b) for b in _CBODY.findall(page)]
            scores = [int(s.replace(",", "")) for s in re.findall(r"(\d[\d,]*) point", page)]
            cs = [{"who": "", "likes": (scores[i] if i < len(scores) else 0), "text": b}
                  for i, b in enumerate(bodies)
                  if b and b not in ("[removed]", "[deleted]")]
            if cs:
                return {"body": cs[0]["text"][:800], "comments": cs[1:]}
    except Exception:
        pass
    d = _paid("post/comments", {"url": url})
    raw = (d or {}).get("comments") or (d or {}).get("data") or []
    cs = []
    for c in raw if isinstance(raw, list) else []:
        t = str(c.get("body") or c.get("text") or "").strip()
        if t and t not in ("[removed]", "[deleted]"):
            cs.append({"who": "", "likes": int(c.get("score") or 0), "text": t})
    return {"body": "", "comments": cs}
