"""A STORM retriever backed by DataForSEO Google organic SERP.
Finds the links via DataForSEO, then FETCHES each page itself (free HTTP) and extracts the
full article text with trafilatura, chunked into passages -> "deep RAG" (always on).
Returns STORM's expected shape: {url, title, description, snippets}."""
import os, re, base64, requests, dspy
try:
    import trafilatura
except Exception:
    trafilatura = None

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")

class DataForSEORM(dspy.Retrieve):
    def __init__(self, login=None, pw=None, k=3, location="United States", language="en",
                 max_passages=14, passage_chars=1200):
        super().__init__(k=k)
        self.auth = base64.b64encode(f"{login or os.environ['DFS_LOGIN']}:{pw or os.environ['DFS_PW']}".encode()).decode()
        self.k = k; self.location = location; self.language = language
        self.max_passages = max_passages; self.passage_chars = passage_chars
        self.usage = 0
        self._cache = {}   # url -> full text (avoid re-fetching)
        self.max_dfs_fallbacks = 25   # cap on DataForSEO content-parse fallbacks per run (bounds time+cost)
        self._dfs_used = 0

    def get_usage_and_reset(self):
        u = self.usage; self.usage = 0; return {"DataForSEORM": u}

    def _serp(self, query):
        r = requests.post(
            "https://api.dataforseo.com/v3/serp/google/organic/live/advanced",
            headers={"Authorization": "Basic " + self.auth, "Content-Type": "application/json"},
            json=[{"keyword": query, "location_name": self.location,
                   "language_code": self.language, "depth": max(self.k, 5)}], timeout=90)
        tasks = r.json().get("tasks") or []
        res = (tasks[0].get("result") or [{}])[0] if tasks else {}
        return res.get("items") or []

    def _fetch_full(self, url):
        if url in self._cache:
            return self._cache[url]
        text = ""
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
            if trafilatura and r.status_code == 200:
                text = trafilatura.extract(r.text, include_comments=False,
                                           include_tables=True, favor_recall=True) or ""
        except Exception:
            text = ""
        # Fallback: trafilatura got ~nothing (JS-rendered / bot-blocked page). Use DataForSEO's server-side
        # content parser (renders JS, rotates IPs). Bounded + fail-safe: on any error we return "" and the
        # caller falls back to the SERP snippet exactly as before — so this can only help, never break.
        if len(text) < 200 and self._dfs_used < self.max_dfs_fallbacks:
            self._dfs_used += 1
            text = self._fetch_dfs(url) or text
            if self._dfs_used == self.max_dfs_fallbacks:
                print(f"  [rm] content-parse fallback budget ({self.max_dfs_fallbacks}) reached — remaining hard pages use snippet only")
        self._cache[url] = text
        return text

    def _fetch_dfs(self, url):
        """Fallback scraper via DataForSEO content-parsing (server-side, JS-rendered). Returns the main body
        text (header/footer/nav skipped). Fail-safe: returns '' on any error/timeout."""
        try:
            r = requests.post("https://api.dataforseo.com/v3/on_page/content_parsing/live",
                              headers={"Authorization": "Basic " + self.auth, "Content-Type": "application/json"},
                              json=[{"url": url, "enable_javascript": True}], timeout=90)
            tasks = r.json().get("tasks") or []
            items = ((tasks[0].get("result") or [{}])[0].get("items") or []) if tasks else []
            pc = items[0].get("page_content") if items else None
            if not pc:
                return ""
            parts = []

            def _walk(o):
                if isinstance(o, dict):
                    t = o.get("text")
                    if isinstance(t, str) and t.strip():
                        parts.append(t.strip())
                    for v in o.values():
                        _walk(v)
                elif isinstance(o, list):
                    for x in o:
                        _walk(x)

            for section in ("main_topic", "secondary_topic"):   # the real content; skip header/footer/cookie/nav
                _walk(pc.get(section))
            return re.sub(r"\s+", " ", " ".join(parts)).strip()
        except Exception:
            return ""

    def _passages(self, text):
        text = re.sub(r"\s+", " ", text).strip()
        cap = self.passage_chars * self.max_passages
        return [text[i:i + self.passage_chars] for i in range(0, min(len(text), cap), self.passage_chars)]

    def forward(self, query_or_queries, exclude_urls=[]):
        queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
        self.usage += len(queries)
        out = []
        for q in queries:
            try:
                cnt = 0
                for it in self._serp(q):
                    if it.get("type") != "organic":
                        continue
                    url = it.get("url"); title = it.get("title")
                    desc = it.get("description") or it.get("snippet") or title
                    if not (url and title) or url in exclude_urls:
                        continue
                    full = self._fetch_full(url)
                    snippets = self._passages(full) if full and len(full) > 200 else [desc]
                    out.append({"url": url, "title": title, "description": desc, "snippets": snippets})
                    cnt += 1
                    if cnt >= self.k:
                        break
            except Exception as e:
                print("DataForSEO RM error:", str(e)[:140])
        return out
