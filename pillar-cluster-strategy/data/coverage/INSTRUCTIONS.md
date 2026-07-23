# Subagent task — Does a PILLAR PAGE already exist for each pillar?

For each content pillar (a tight cluster of blog posts), decide whether Testlify has **already built a hub/pillar page** that these posts could link up to — or whether that hub page is **missing**.

## Inputs
- `data/coverage/existing-pages.txt` — the AUTHORITATIVE list of every real marketing page on testlify.com (English, from the live sitemap). These are the only pages that actually exist.
- `data/coverage/in/<key>.json` — your theme's pillars (name, size, sample spokes).

## Critical rule — no hallucinated URLs
A page counts as "existing" ONLY if its slug appears in `existing-pages.txt`. **Never invent a URL.** If you can't find a matching slug in that file, the status is `missing` and `hub_url` is null. Always copy the hub_url slug exactly as it appears in the file.

## Decide a status for each pillar
- **`built`** — a dedicated existing page clearly serves as the hub for this pillar's exact topic. (e.g. pillar "Coding & Programming Tests" → page `coding-tests` exists → built.)
- **`partial`** — a real page exists that's related but broader, narrower, or only tangential — it covers the pillar only loosely, not a dedicated hub. (e.g. pillar "React Developer Interview Questions" and only a generic `interview-as-a-service` page exists.)
- **`missing`** — no existing page serves as a hub for this topic.

Be strict: a generic product page is NOT a pillar page for a specific blog topic. When unsure between built and partial, choose `partial`.

## Output
Write JSON to `data/coverage/out/<key>.json`:
```json
{
  "theme": "<theme name>",
  "key": "<key>",
  "pillars": [
    {"pillar": "Coding & Programming Tests", "status": "built",
     "hub_url": "coding-tests", "note": "dedicated test-type page exists"},
    {"pillar": "React Developer Interview Questions", "status": "missing",
     "hub_url": null, "note": "no interview-questions hub page exists"}
  ]
}
```
Every pillar in your input must appear exactly once in the output. After writing, reply ONE line: `<key>: built X / partial Y / missing Z (of N)`.
