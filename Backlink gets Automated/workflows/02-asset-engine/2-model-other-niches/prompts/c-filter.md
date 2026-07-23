You are the real scored gate for {{BRAND}}'s Method 2 idea pool. Each idea below is an adaptation of a proven
cross-niche format, now with a real subject. Run **every** idea through the SAME two tests Methods 1 and 3 use,
against the SAME brand scope. Be honest — expect to DROP a material chunk; that is the filter working.

## {{BRAND}}'s brand scope (judge against THIS)
{{BRAND_SCOPE}}

## The ideas to filter
{{IDEAS}}

## Test A — Ownability (can {{BRAND}} credibly own it?)
- Does it sit inside the brand scope (CORE / TRANSPLANT / ADJACENT)?
- Does {{BRAND}} have the **data, product, or authority** to speak credibly on it? The idea's distinct angle
  must already name a specific one — if it can't, it FAILS this test.
- Does building it reinforce the brand?

CORE or TRANSPLANT passes; ADJACENT is a maybe. **Out of scope? Run the transplant check BEFORE dropping**
(mandatory): is there a strong, linkable format here we can point at an in-scope subject? If yes, KEEP as
TRANSPLANT and record the move; only if the transplant *also* fails does it DROP. The CORE/TRANSPLANT/ADJACENT
verdict here is the **authoritative brand_fit** (it supersedes the rough pre-screen tag).

## Test B — Linkability (would anyone cite it?) — 4 questions
1. Is there a citable number the asset could produce that a writer would reference?
2. Would a journalist or blogger reference it when writing about the niche?
3. Is it evergreen — not a one-off that dies in a week?
4. Does it fit a proven link-bait format? (For Method 2 this is automatically YES — every input is proven.)
Needs **>= 3 of 4 yes** to pass.

## Verdict
KEEP only ideas that pass **BOTH** tests. Record KEEP / DROP / MAYBE + a one-line reason for each.

## Output — strict JSON only
```
{"verdicts": [
  {"id": <the idea id, integer, from the list>,
   "brand_fit": "<CORE | TRANSPLANT | ADJACENT | OUT>",
   "transplant_note": "<if the subject was out of scope and you transplanted it, say from->to; else empty>",
   "linkability_yes": <0-4>,
   "verdict": "<KEEP | DROP | MAYBE>",
   "reason": "<one line>"}
]}
```
One entry per idea, same ids. KEEP requires brand_fit in {CORE, TRANSPLANT} (ADJACENT = MAYBE) AND linkability_yes >= 3.
