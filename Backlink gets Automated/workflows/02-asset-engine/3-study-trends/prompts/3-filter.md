You are the filter gate for {{BRAND}}'s Method-3 tension pool. Reddit measures ATTENTION, not linkability — the
loud posts are often viral drama nobody would cite. Run both tests per tension against the SAME brand scope
Methods 1 & 2 use. Be honest; expect to DROP the pure-drama tensions.

## {{BRAND}}'s brand scope (the ownership anchor)
{{BRAND_SCOPE}}

## The tensions to filter
{{TENSIONS}}

## Test A — Linkability (would anyone cite an asset about this?) — 4 questions
1. Is there a **citable number** an asset could produce that a writer would reference? ("% of fake-remote listings" = yes; "craziest rejection email" = no)
2. Would a journalist or blogger reference it when writing about the niche?
3. Is it **evergreen** — not a one-off viral moment that dies in a week?
4. Does it fit a proven link-bait format (index / calculator / data report / guide)?
Needs **>= {{LINK_MIN}} of 4 yes** to pass. This is where pure-drama tensions (huge upvotes, no citable substance) die.

## Test B — Ownability (can {{BRAND}} credibly own it?) vs the brand scope
- Does it sit inside scope (CORE / TRANSPLANT / ADJACENT)?
- Does {{BRAND}} have the data, product, or authority to speak credibly?
- **Out of scope? Run the TRANSPLANT check BEFORE dropping (mandatory):** is there a strong linkable format here
  we can point at an in-scope subject? If yes, KEEP as TRANSPLANT and record from->to. Only if the transplant
  *also* fails does it DROP. Record the transplant verdict for EVERY out-of-scope tension (even "no transplant").
CORE or TRANSPLANT passes; ADJACENT is a MAYBE.

## Output — strict JSON only
```
{"verdicts": [
  {"tension_id": "<the tension code EXACTLY as shown, e.g. T01>", "linkability_yes": <0-4>,
   "brand_fit": "CORE|TRANSPLANT|ADJACENT|OUT", "transplant_note": "<from->to, or 'no transplant', or empty>",
   "verdict": "KEEP|DROP|MAYBE", "reason": "<one line>"}
]}
```
One entry per tension. KEEP requires linkability_yes >= {{LINK_MIN}} AND brand_fit in {CORE, TRANSPLANT} (ADJACENT = MAYBE).
