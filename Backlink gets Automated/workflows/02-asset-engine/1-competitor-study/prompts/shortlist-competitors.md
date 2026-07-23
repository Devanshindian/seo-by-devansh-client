You are building the competitor shortlist for **{{BRAND}}** — {{ONELINER}}

On-topic scope for this company: {{NICHE}}

## Your job

From the CANDIDATE LIST below, pick the **{{N}}** competitors worth studying, and split them into two
groups. The candidate list came from a keyword-overlap API, so it is **full of sites that are not
competitors at all** — big publishers, dictionaries, universities, job boards and general media that
merely rank for similar words. Your first job is to throw those out.

## The two groups

- **DIRECT** — sells the *same kind of product* to the *same buyer* as {{BRAND}} does. If a buyer could
  realistically choose them *instead of* {{BRAND}}, they are direct. Aim for roughly two thirds.
- **ADJACENT** — does **not** sell the product, but **owns the audience**: the authority sites, industry
  bodies and content leaders this buyer already reads and links to. They matter because their pages show
  which *formats* earn links in this world. Aim for roughly one third.

## HARD EXCLUSIONS — these are absolute, no exceptions, however well they rank

A site in ANY of these classes is excluded even if it is famous, authoritative, or highly relevant to
the industry. Being *about* the industry is not the same as being a competitor or a content leader
worth studying.

- **General business / management media** — Harvard Business Review, Forbes, Inc., Fast Company,
  Business Insider, Entrepreneur, and anything of that kind. They publish on every industry; they do
  not own THIS audience. *(hbr.org slipped through on 2026-07-20 — do not repeat it.)*
- **News and consumer media** of any kind.
- **Reference / encyclopedia / dictionary / academic** sites and universities.
- **Software review and directory sites** — G2, Capterra, TrustRadius, GetApp, SoftwareAdvice.
  They list the category; they are not in it. *(g2.com slipped through — do not repeat it.)*
- **Document-sharing, Q&A, forum, course, quiz and general e-learning** platforms.
- **Job boards and general career sites**, unless the company genuinely sells against them.
- Anything whose overlap is clearly incidental — it ranks for a shared word, not a shared business.

An ADJACENT pick must own **this specific buyer's** attention: a professional body, a specialist
industry publication, a training academy, or a vendor whose content library this exact buyer reads.
If you cannot name that buyer relationship in one line, it is not adjacent — it is excluded.

## HOW TO WORK — order matters

1. **First, sweep the WHOLE list for DIRECT competitors and take every one you find.** Be exhaustive.
   Do not stop early because a candidate sits low in the list — the list is ranked by keyword overlap,
   not by how directly a company competes, so real rivals appear deep down. (Measured 2026-07-20:
   four genuine direct rivals sat at ranks 52, 100, 120 and 134 and were missed.)
2. **Only then** fill the remaining slots with the strongest ADJACENT sites.
3. If the direct competitors alone exceed {{N}}, **return them all** — going over is fine; missing a
   direct rival is not.

Read each candidate's description before judging it. Where a description is present, it is what the
company says it is in its own words — trust it over what the domain name suggests.

## Rules

- **Pick only from the candidate list**, except for the pre-approved entries described below.
- **ONE COMPANY = ONE ROW.** Some companies appear in the list under two domains (a brand domain and a
  legacy or alternate one, e.g. `wecp.io` and `wecreateproblems.com` are both WeCP). Return the company
  ONCE. If one of its domains is in the USER-SUPPLIED list, **return that exact domain string** and put
  the other in an `aliases` array. Never return the same business twice under two names.
- **PRE-APPROVED (must all appear in your output, marked `user_supplied: true`):** any domain in the
  USER-SUPPLIED list below is included **whatever** the API said, and even if it is absent from the
  candidate list. The operator knows this market; the API does not. Place each in the right group.
- Judge from the domain and the numbers. Say plainly when you are unsure rather than inventing detail.
- If fewer than {{N}} genuine competitors exist in the list, **return fewer** — do not pad it with
  publishers to reach a number.

## BEFORE YOU RETURN — audit your own list

Re-read every row you are about to output and delete any that fails:
1. Does it break a HARD EXCLUSION above? → delete it.
2. Is it the same company as another row? → merge them into one.
3. For an ADJACENT row: can you name in one line why THIS buyer reads it? If not → delete it.
4. For a DIRECT row: would a buyer realistically choose it INSTEAD of {{BRAND}}? If not, either move it
   to ADJACENT (if it owns the audience) or delete it.

A shorter, purer list is the goal. Never pad to reach a number, and never keep a borderline row "just
in case" — a junk competitor pollutes every downstream step of this study.

## Return ONLY JSON

```
{"competitors": [
   {"domain": "...", "group": "DIRECT|ADJACENT", "why": "one short line — what they sell / whose audience they own",
    "user_supplied": false}
 ],
 "excluded_notable": ["domain — why it was thrown out (only the ones that ranked high and might surprise the operator)"],
 "note": "one line on anything the operator should know (e.g. a competitor you expected and could not find)"}
```

## USER-SUPPLIED (pre-approved — include every one)
{{USER_SUPPLIED}}

## CANDIDATE LIST (domain · shared keywords · traffic value · from the keyword-overlap API)
{{CANDIDATES}}
