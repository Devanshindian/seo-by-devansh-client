# DataForSEO quality check — the shared review page

A single self-contained HTML page that runs the eight DataForSEO calls our research phase depends on, one at a
time, and shows each answer as a plain table. Built for a non-technical reviewer to answer one question: **is
DataForSEO giving us good data?**

No build step, no server, no install. The page calls the DataForSEO API straight from the browser (their API
sends `Access-Control-Allow-Origin: *`, so a static page is allowed to talk to it).

## Files

| File | What it is |
|---|---|
| `index.html` | The whole app. HTML, CSS and JS inline. This is the only source file. |
| `_pages-repo/` | The push clone for GitHub Pages. `index.html` is copied into it. |

## The eight endpoints, and where each one comes from

Every endpoint on the page is one our code actually calls. Nothing is included for decoration.

| Page tool | Endpoint | Called by |
|---|---|---|
| Find every phrase people search around one topic | `dataforseo_labs/google/keyword_suggestions/live` | `10-dataforseo/scripts/s1_expand.py:28` |
| Get the numbers for a list of keywords | `dataforseo_labs/google/keyword_overview/live` | `10-dataforseo/scripts/s3_metrics.py:16` |
| See every keyword a competitor ranks for | `dataforseo_labs/google/ranked_keywords/live` | `10-dataforseo/scripts/s1b_ranked.py:23` |
| See Google's first page as it is right now | `serp/google/organic/live/advanced` | `10-dataforseo/scripts/s4_serp.py:13`, `11-storm/scripts/dataforseo_rm.py:31` |
| Pull the readable text out of a page | `on_page/content_parsing/live` | `11-storm/scripts/dataforseo_rm.py:65` |
| Check how much credit is left | `appendix/user_data` | `10-dataforseo/scripts/dfs.py:83` (the credit guard) |
| Find who we really compete with | `dataforseo_labs/google/competitors_domain/live` | `02-asset-engine/1-competitor-study/scripts/step_a_competitors.py:22` |
| A competitor's most linked-to pages | `backlinks/domain_pages/live` | `02-asset-engine/1-competitor-study/scripts/step_b_pages.py:24` |

The first six run on every topic the research pipeline processes. The last two run earlier, in the asset engine,
and decide which topics reach research at all.

Each request body on the page is a copy of the body the matching script sends, including the `order_by` and
`filters` arguments, so what the reviewer sees is what the pipeline sees.

## Credentials

The shared DataForSEO login is embedded in `index.html` (`DEFAULT_LOGIN` / `DEFAULT_PW`), because the page has no
backend to hide it in. Anyone with the URL can spend from the account.

To rotate without redeploying, open the browser console on the page and run:

```js
dfsLogin("new@login.com", "newpassword")
```

That stores the pair in the reviewer's own browser and overrides the built-in default. To change it for everyone,
edit the two constants and redeploy.

Keep the account balance modest. DataForSEO also supports a daily cost limit on the account, which is the real
guard if the URL ever leaks.

## Cost

Nothing runs until the reviewer presses a button, and the exact cost of each call is read from the API's own
`cost` field and shown next to the result. A full pass over all eight, at the default sizes, came to **$0.0857**.
The credit remaining is in the bar at the top and refreshes after every paid call.

## To deploy or update

```bash
cp index.html _pages-repo/index.html
git -C _pages-repo add -A
git -C _pages-repo commit -m "update"
git -C _pages-repo push
```

GitHub Pages redeploys in about a minute. Always push to the same repo so the URL the team has keeps working.

## Verified

- All eight request bodies were sent against the live API; every field the page reads back exists and returns real
  data.
- The page was loaded in Chrome and driven end to end (both render paths, sorting, CSV, raw JSON toggle, the
  balance and spend chips). No console errors.
