---
type: tool-guide
tool: reddit-scrape.py (+ ocr-mac)
reusable: any company / any purpose
used_by: asset-engine / study-trends (Method 3) — and anything else needing Reddit data
last_updated: 2026-06-23
---

# Reddit Scraper — operation guide

A **free** Reddit data tool. It reads Reddit's **public `old.reddit` HTML pages** (no API key, no login) and
gives you subreddits, posts (with body text + OCR'd image text), and full nested comment trees — exported to
one Excel file. Built because Reddit killed the easy paths in 2026 (the `.json` endpoint 403s, official API
app-creation is gated). This tool is the practical free way in.

> **Honest scope:** Reddit exposes **no view counts** — we rank by **upvotes + comment count** only.
> Scraping is technically against Reddit's ToS; at our low volume (a handful of subreddits, occasionally,
> from one machine) the exposure is negligible — but know it.

**Files (both in this `scripts/reddit/` folder):**
- `reddit-scrape.py` — the scraper (5 commands).
- `ocr-mac.swift` / `ocr-mac` — free native macOS OCR, used automatically to read text inside image posts.

---

## Quick start (the one command you'll use most)
```bash
cd "workflows/02-asset-engine/3-study-trends/scripts/reddit"
python3 reddit-scrape.py run "recruiting,humanresources,AskHR" \
  --posts 25 --threads 15 --out "/path/to/output.xlsx"
```
This pulls the top 25 posts of the year from each subreddit, plus each post's body, image-text (OCR), and
top-15 comment threads (fully expanded), into one `.xlsx`. **Resumable** — if it's interrupted (e.g. laptop
sleeps), just run the same command again and it skips what's already saved.

---

## Prerequisites (one-time)
- **Python 3** + `openpyxl` (`pip3 install openpyxl`) — for the Excel export.
- **OCR (optional but recommended)** — compile the native macOS OCR tool once:
  ```bash
  swiftc -O ocr-mac.swift -o ocr-mac
  ```
  If `ocr-mac` isn't present, everything still works — image posts just get an empty `image_text`.

---

## The 5 commands

### 1. `discover` — find subreddits for a topic
```bash
python3 reddit-scrape.py discover "skills based hiring" --limit 15
```
Prints JSON: `[{subreddit, subscribers, description}, …]`. **Always run this first** for a new niche.

> 🚫 **HARD RULE — never skip the approval gate.** After `discover`, the agent **must present the candidate
> subreddits to the user** (name · subscriber count · description · why it's relevant) and **wait for the
> user to approve / edit the set**. **Do NOT run the scrape on a self-chosen list.** Picking subreddits from
> memory is exactly how a dead/empty sub slips in (the 23-member `r/talentacquisition` lesson). The user
> approves the set; only then do you `run`.

> ⚠️ Subscriber counts here are *best-effort* (old.reddit often omits them). Don't gate on member counts —
> **vet candidates by real activity** instead: run `posts <sub> --sort top --time year --limit 5` per
> candidate and judge by the upvotes/comments on its top posts. That's free, and a truer signal than size.

### 2. `posts` — top posts of one subreddit
```bash
python3 reddit-scrape.py posts recruiting --sort top --time year --limit 25
```
Prints JSON of posts: `post_id, subreddit, score, comment_count, flair, date, author, title, image_url, url`.
- `--sort` = `top` | `hot` | `new` | `rising` | `controversial`
- `--time` = `year` | `month` | `week` | `all` (applies to `top`)
- *(Body + image_text are filled by `run`, not here — they require visiting each post page.)*

### 3. `comments` — the full discussion under one post
```bash
python3 reddit-scrape.py comments "https://old.reddit.com/r/recruiting/comments/XXXX/slug/" --threads 15
```
Prints `{ "body": "<post text>", "comments": [ {comment_id, parent_id, depth, score, author, text}, … ] }`.
`--threads` = how many **top-level** comment threads to keep; **each is fully expanded** (all nested replies).

### 4. `run` — the full pipeline (what you'll normally use)
```bash
python3 reddit-scrape.py run "sub1,sub2,sub3" --posts 25 --threads 15 \
  --sort top --time year --out "output.xlsx" --raw "raw"
```
For **each** subreddit → top N posts; for **each** post → body + image OCR + comment tree. Writes one `.xlsx`
(3 tabs) + a `raw/` JSON backup. **Resumable** and **network-resilient** (retries on 429 + connection drops).

### 5. `build` — rebuild the Excel from saved data
```bash
python3 reddit-scrape.py build --raw "raw" --out "output.xlsx"
```
Reassembles the `.xlsx` from whatever's in `raw/` — use after an interrupted run, or to regenerate the sheet.

---

## What you get (the output)
One `.xlsx` with three tabs, plus a `raw/` folder.

| Tab | One row = | Columns |
|---|---|---|
| **Subreddits** | a community | `subreddit, posts_pulled` (+ `subscribers, description` if enriched) |
| **Posts** | a post | `post_id, subreddit, score, flair, date, author, title, body, image_url, image_text, comment_count, top_comments (top 15), url` |
| **Comments** | a comment | `post_id, subreddit, comment_id, parent_id, depth, score (= comment upvotes), author, text` |

- **`body`** = the post's own text (text posts). **`image_text`** = OCR'd text from image posts. Together they
  capture the *actual content*, not just the title.
- **The comment tree:** `post_id` links a comment to its post; `parent_id` + `depth` rebuild the reply tree
  (depth 0 = top-level, 1 = a reply, etc.); `subreddit` is on every row so you can filter by community.
- **`raw/`** = lossless JSON (one file per subreddit's posts + one per post's comments) — the backup `build`
  reads from, and your safety net if a run is interrupted.

---

## Operational notes
- **Throttle:** 2.5s between requests (deliberate, to avoid Reddit's 429 rate-limit). This — not compute — is
  why a full run takes minutes. Rough timing: ~6 subs × 25 posts ≈ **10–15 min**.
- **Keep the machine awake — wrap long runs in `caffeinate`.** Because a run takes 10–20 min, idle sleep can
  kill it (and any background-completion notification) mid-way. Always prefix with `caffeinate -i`:
  `caffeinate -i python3 reddit-scrape.py run …`. The run is resumable, but don't rely on that across a sleep.
- **OCR speed:** near-instant (on-device Apple Vision). A ~50-image run adds only a few minutes (download +
  a 1s pause per image).
- **Resume:** safe to re-run the same `run` command after any interruption — it reuses saved posts/comments.
- **Don't hand-edit the output `.xlsx` while a run might overwrite it.** If you need to annotate it, copy it
  to a new filename first.

### Subscriber counts — don't gate on them
DIY `discover` may not return member counts, and that's fine: **member size is not how we choose subs.**
Vet by real activity instead — `posts <sub> --sort top --time year --limit 5` and read the upvotes/comments
on the top posts. A small, active practitioner sub beats a huge dead one.

---

## The access ladder (when the free path breaks)
1. **DIY old.reddit scraper (this tool)** — free default. Use it.
2. **Official Reddit API (PRAW)** — the "proper" long-term path *if* an aged/trusted Reddit account ever gets
   approved (new accounts are gated). Then switch to it.

---

## Known limits & gotchas
- **No view counts** — Reddit doesn't expose them; rank by upvotes + comments.
- **No subscriber counts from old.reddit (as of 2026-06)** — the search results and sidebar no longer expose member counts to the scraper, so `discover` returns `subscribers: null`. Don't worry about it — **vet by activity** (top-post upvotes/comments), not member size. (Search-page markup also changed in 2026-06 — `discover`'s anchor regex was updated to match the new absolute-href / class-order layout.)
- **`old.reddit` dependency** — if Reddit retires the old design, this exact method breaks; fall back to the
  ladder above.
- **Gallery / video posts** — `image_url` is captured only for single images (`i.redd.it` / `imgur` /
  `preview.redd.it`); multi-image galleries and videos are skipped for OCR.
- **Run `discover` first** — picking subreddit names from memory risks a dead/empty sub (the
  `r/talentacquisition` lesson). Check size + activity before scraping.
- **Bigger ≠ better** — giant candidate-side subs (r/jobs, r/recruitinghell) are loud but skew to viral
  *drama*; smaller practitioner subs (r/recruiting, r/humanresources) are more on-target for B2B buyers.

---

## Recommended flow (for trend-hunting)
1. **`discover <niche>`** → vet each candidate by activity (`posts <sub> --sort top --time year --limit 5`) →
   **present the candidate subreddits to the user (name · activity · description · relevance) and ASK them to
   approve / edit the set.**
   🚫 **This is a gate — do not proceed until the user signs off.**
2. **`run <approved subs> --out sheet.xlsx`** → the full dataset (posts + body + image OCR + comments).
3. **Open the sheet** → mine seeds: rank by engagement, then **filter for linkability** (a hot topic isn't a
   link magnet unless someone would *cite* an asset about it) → turn seeds into ideas.

> **Asset Engine note:** this tool is the data engine for **study-trends (Method 3)**. That
> workflow references this guide rather than duplicating it — keeping the tool reusable for any other purpose.
