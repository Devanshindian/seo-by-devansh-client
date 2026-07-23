---
type: workflow-step
parent: asset-engine (Method 3 of 3)
reusable: any company
needs: the Reddit scraper tool (workflows/02-asset-engine/3-study-trends/scripts/reddit/) · the approved brand-scope.md (from Method 1 / G0 — for ownability judgment)
produces: projects/[company]/02-asset-engine/study-trends/output/ (deliverables); _raw/ + _work/ alongside
last_updated: 2026-06-24
---

# Idea Backlog — Method 3: Study Trends

Read what the niche is fired up about right now, distil it into recurring tensions, and shape each into a link-worthy asset. It supplies what Method 1 (proven winners) and Method 2 (proven formats) can't: timeliness — current-events angles that only exist because people are talking about them this month.

Method 3 of 3 — separate idea pool, merged at the end.

**The one rule that matters:** Reddit measures attention, not linkability — the top posts are often viral drama nobody would cite. The value is the filtering: keep only tensions that are timely and something a writer would cite an asset about.

## Output (under projects/[company]/02-asset-engine/study-trends/output/)

Built in order:

```
study-trends/
  output/                      ← the deliverables
    study-trends-ideas.csv     ← ★ THE DELIVERABLE: final asset ideas + Reddit signals
    tensions.csv               ← working file: one row per tension + evidence + KEEP/DROP verdicts
    phrase-map.csv             ← working file: every phrase → the tension it rolled up into (audit trail)
  _raw/                        ← Reddit scraper output: [company]-reddit-trends.xlsx + reddit-json/ (per-post comment JSON)
                                 (a `phrases` column is added to that xlsx's Posts tab in Stage 2a)
  _work/                       ← intermediates: merge-check.md, post-tension-map.tsv, agent_out/, cards/,
                                 run-log.md (was RUN-LOG-problems.md)
```

This method has two phases: **(A)** gather the data with the Reddit scraper tool, then **(B)** mine it into tensions → ideas.

---

# PHASE A — Gather the data

Run the Reddit scraper tool per its own guide at `workflows/02-asset-engine/3-study-trends/scripts/reddit/reddit-scraper.md`. That guide covers the full tool operation. The Method-3 specifics:

### A1 — Discover subreddits

Run the discover command for the niche:

```bash
python3 reddit-scrape.py discover "skills based hiring" --limit 15
```

Returns a list of candidate subreddits with name and description. **Vet candidates by real activity using our own scraper, not subscriber counts** — run `reddit-scrape.py posts <sub> --sort top --time year --limit 5` per candidate and judge by the upvotes/comments on its top posts; drop dead/empty subs (the `r/talentacquisition`/`r/JobInterview` lesson). This is free and a truer signal than member counts. (If the client hands you a target subreddit list directly, that list *is* the approval — skip discovery and just sanity-check each sub is alive with the same `posts` activity check.)

Favour a mix of on-target practitioner subs over just the loud, drama-heavy giants. Bigger is not better — large candidate-side subs (r/jobs, r/recruitinghell) skew to viral venting; smaller practitioner subs (r/recruiting, r/humanresources) are more on-target for B2B buyers.

### A2 — Get approval (this is a gate)

Present the candidate subreddits to the user — name · activity (top-post upvotes/comments) · description · why it's relevant — and wait for sign-off. **Do not run the scrape on a self-chosen list.** Picking from memory is exactly how a dead or empty sub slips in. The user approves the set; only then proceed. *(If the client supplied the list, it's already approved — just sanity-check each sub is alive.)*

### A3 — Run the scraper

```bash
python3 reddit-scrape.py run "sub1,sub2,sub3" \
  --posts 25 --threads 15 --sort top --time year \
  --out "projects/[company]/02-asset-engine/study-trends/_raw/[company]-reddit-trends.xlsx" \
  --raw "projects/[company]/02-asset-engine/study-trends/_raw/reddit-json"
```

This pulls the top 25 posts of the year from each subreddit, plus each post's body text, OCR'd image text, and top-15 comment threads (fully expanded), into one `.xlsx`. Resumable — if interrupted, re-run the same command and it skips what's already saved.

**What the scraper produces** — one `.xlsx` with three tabs:

| Tab | One row = | Key columns used in Phase B |
|---|---|---|
| Subreddits | a community | subreddit, subscribers |
| Posts | a post | post_id, subreddit, score, title, body, image_text, comment_count, top_comments, url |
| Comments | a comment | post_id, comment_id, parent_id, depth, score, text |

`body` = the post's own text. `image_text` = OCR'd text from image posts. `top_comments` = the top 15 comment threads, fully expanded. Together these are what Phase B reads as the "content card" for each post.

Save the output to `_raw/` and move to Phase B.

---

# PHASE B — Mine the data into tensions → ideas

Term: a **tension** = one sentence stating the underlying conflict or pain (not just a topic label). Its full evidence row in tensions.csv (counts, quotes, verdicts) is just "the tension's row" — tension is the only unit.

**Where the LLM does the work (everything else is mechanical counting/summing).** Phase B is mostly judgment, so it's worth seeing up front which calls are the model's:

| Step | LLM call | Mechanical |
|---|---|---|
| Stage 1 | reads each post as a content card | — |
| 2a | writes the 2–3 phrases per post | — |
| 2b | groups phrases → tension sentences | — |
| 2c | assigns each post to its real tension | — |
| 2d | core pain · audience · emotion · best example · quotes · sub-questions · implied data point | # posts · upvotes · comments · debate ratio · subreddit spread (all summed/counted from the Posts tab) |
| Stage 3 | judges Linkability + Ownability against the brand-scope doc | — |
| Stage 4 | writes the asset idea + title | carries the Reddit signal numbers across |

## STAGE 1 — Read each post as a content card

Go through every post in the Posts tab reading it as one unit: title + body + image_text + top_comments + score + comment_count + subreddit. No output yet — you're absorbing the full picture of what's being said and how people are reacting.

## STAGE 2 — Extract phrases, consolidate into tensions, build tensions.csv

Four sub-steps.

### 2a — Tag each post with phrases, written into the Posts tab

Do this post-by-post during Stage 1, not as a separate end pass. For each post, read the whole row — **title + body + image_text + top_comments + score + comment_count + subreddit** — and pull out the 2–3 phrases that **best capture what this post is about**: (1) the post's **core complaint or claim** (what the OP is actually angry or anxious about), plus (2) **any point that multiple *different* commenters converge on** — several independent voices landing on the same thing is real signal, not one person repeating themselves. Write them **straight into a new `phrases` column on the Posts tab** of the scraper xlsx, on that post's own row, **separated by commas**. (Keeping the phrases next to their post_id means every phrase stays tied to the post it came from, so the evidence trail never breaks.)

Don't try to measure recurrence *inside* one post — that's the wrong level. True recurrence (a phrase showing up across many posts) is what makes a tension strong, and it's counted later in 2b via the **# posts** field. Here you're just capturing each post faithfully so that cross-post pattern can emerge. Expect ~2–3 phrases per post; some thin posts yield one or none.

Always tight phrases (2–4 words), never single words — "remote" is noise; "fake remote listings" is a signal. Single words are too vague to act on.

Prune filler phrases ("at the end of the day", "in this economy") — don't even write them down. What's left in the `phrases` column is an objective, post-grounded phrase list.

**⚙️ How to run 2a at scale — parallel Sonnet sub-agents (the proven method).** Phrase extraction is embarrassingly parallel (each post is tagged independently), and a wide run (e.g. 25+ subreddits ≈ 600+ posts ≈ hundreds of thousands of tokens) is too big to read in one context without degrading the later holistic consolidation. So shard it:
1. Export one **content-card file per subreddit** (`_work/cards/<sub>.txt`) — each post as `### <post_id> | r/<sub> | <score>up <comments>c` + trimmed TITLE / BODY / IMG_TEXT / TOP_COMMENTS.
2. Dispatch **parallel Sonnet sub-agents** (≈2 subreddits each), giving every agent the 2a rules above and having it write `post_id<TAB>phrases` to `_work/agent_out/<sub>.tsv` — every post_id included, even if it gets 0 phrases.
3. **Reassemble + validate centrally:** load all tsvs, confirm **every post_id from the Posts tab is covered exactly once (0 missing / 0 extra)**, check phrases are 2–4 words, and only then proceed. The main context now holds just the compact phrase list — clean for 2b. *(This mirrors the Competitor-Study sub-agent pattern. Sub-agents do the per-post reading; the consolidation in 2b is NOT delegated — see the hard line below.)*

### 2b — Consolidate phrases into tensions

Related phrases collapse into one tension. The tension is always **one sentence stating the actual conflict**, not a topic label. This forces you to articulate why people are angry or anxious — which is exactly what the asset needs to exploit.

- ❌ Theme (too vague): "fake remote jobs"
- ✅ Tension (actionable): "Candidates are being baited into applying for roles listed as remote that turn out to be secretly onsite."

**The criterion — when do two phrases belong to the same tension?**
Merge by **shared pain, never by shared topic.** Two phrases belong together if one honest conflict sentence can describe the pain behind both — the same *who is frustrated with what* — even when the surface words differ. If describing them truthfully needs two different conflict sentences, they're two tensions.

✅ Worked example — these phrases all roll into ONE tension:
- "fake remote listings" · "secretly onsite" · "remote then RTO" · "bait and switch remote"
- → **Tension:** *"Candidates apply for roles advertised as remote that turn out to be onsite, or quietly revert to office later."*
- Different words, one conflict: remote promise vs. onsite reality.

❌ Counter-example — these look related but are TWO tensions (do **not** merge):
- "ghosted after interview" → *"Candidates hear nothing back after investing hours in interviews."* — pain = silence / disrespect
- "endless interview rounds" → *"Candidates are dragged through 5+ rounds for a single role."* — pain = process length
- Both are "interview complaints", but the pain is different (silence vs. length), so they stay separate. Merging them under the topic "interviews" would blur what the asset has to say.

**The consolidation prompt — run this once over the full phrase list to produce the first-pass tensions** (then validate each with the merge check below):

> You are grouping Reddit phrases into **tensions** for [COMPANY]'s niche.
> A **tension = ONE sentence stating a specific shared pain** (who is frustrated with what) — never a topic label.
>
> **Rule:** group phrases by **shared pain, not shared topic.** Two phrases belong together only if *one honest conflict sentence* describes the pain behind both. If you'd need two different conflict sentences, they are two tensions. (E.g. "ghosted after interview" = silence; "endless interview rounds" = process length → two tensions, even though both are about interviews.) Don't lean on vague words ("broken / doesn't work / unfair / outdated") to stretch a sentence over phrases — that's a topic, split it.
>
> Here are the phrases, each with its source post_id:
> **[paste the `phrases` column — every phrase + its post_id]**
>
> Return a list of tensions. For **each** tension give:
> - its one-sentence pain (specific, no vague stretch-words),
> - the exact phrases that belong to it, with their post_ids.
> Put any phrase that fits no clear shared pain under **ORPHANS** — do **not** force it into a tension.

> # 🚨🚨 HARD LINE — NEVER FORGET (read this before writing a single tension) 🚨🚨
> **The merge check below is a GATE, not paperwork. Run it FOR REAL, per-phrase, and produce `_work/merge-check.md` BEFORE `tensions.csv` exists — never after.**
> - **The consolidation (2b) is NOT delegated to a sub-agent and is NOT a single-pass "group it in your head" job.** You personally write the one shared-pain sentence for each candidate tension and test EVERY phrase against it, logging PASS/SPLIT as you go.
> - **`merge-check.md` is a byproduct of doing the work, never a reconstruction of it.** If `tensions.csv`'s timestamp is older than `merge-check.md`'s, you have failed this step — full stop. (This happened on the 2026-06-25 Testlify Wide-26 run: tensions were grouped in one pass and the merge-check was written *afterward* to look done; a real per-phrase pass then found 12 misassigned posts + 2 topic-blob tensions. The user caught it by checking file timestamps. Do not repeat this.)
> - **If you shortcut anything, SAY SO in the run log — plainly.** Never imply rigor that didn't happen. An honest "I did a single pass, not the full loop" is respected; a fake evidence file is not.
> - The whole point: this gate is what stops merging-by-topic. Skipping it silently *guarantees* the topic-blob failure it exists to catch.

**🚦 REQUIRED MERGE CHECK — run this for every candidate tension *before* it's written into the phrase-map or tensions.csv.** This is the gate that stops merging-by-topic (the failure that, on the first Testlify run, collapsed ~5 distinct pains into one vague "résumés don't predict performance" tension and cost 4 asset ideas). Write the result into an intermediate working file **`_work/merge-check.md`** — one short block per candidate tension — so there is *evidence* the check was actually done, not just claimed. For each group of phrases you're about to call one tension:

1. **Write the one shared-pain sentence.** In a single sentence, state the *specific* pain behind **all** the phrases in the group. Shape: *"[who] [is hurt because / can't / is dragged through] [one specific thing]."*
2. **Test it against every phrase, one by one.** For each phrase ask: *"Does this exact sentence describe the pain behind THIS phrase — specifically, not loosely?"*
   - Every phrase a clear **YES** → **PASS** (genuinely one tension).
   - Had to stretch the sentence to fit any phrase → **SPLIT**.
3. **Vague-predicate tripwire.** If your sentence only holds together because it leans on a stretch-word, it's a *topic*, not a tension — **SPLIT**. Banned stretch-words: *"doesn't work · is broken · is a mess · is frustrating · is flawed · barely predicts · is unfair · is outdated · has problems with · struggles with · is bad at."* A real tension names a specific conflict ("candidates are dragged through 5+ rounds"), not a category verdict ("interviews are broken").
4. **On SPLIT — re-derive the correct tension(s) from this exact group of phrases.** Take all the phrases from the group that failed and hand them *back* with the context of why it failed, asking the model to find the right tensions hiding inside. Use a re-prompt like this:

   > *"These phrases were merged into one tension: **'[the failed sentence]'**. That merge **failed the specificity check** — it looks like more than one distinct pain is bundled here. The phrases are: **[list every phrase in the group]**. Re-derive the **proper tension(s)** these phrases actually represent — there may be 2, 3 or more. For **each** tension, give its one specific shared-pain sentence and list exactly which phrases belong to it. If any phrase fits **none** of the tensions, list it under **ORPHANS** rather than forcing it in."*

   Then: **run the merge check (steps 1–3) on each tension that comes back** — a fresh split should now PASS; anything that still fails gets re-split the same way. Two clean-ups so nothing is lost or duplicated:
   - **Orphans** (phrases that fit none of the new tensions) → place each one individually: attach it to a *different* existing tension where it truly shares the pain, or hold it in `misc`. **After one recheck, any phrase that still won't club with others just stays in `misc` — that's fine. Not every phrase has to become a tension; don't loop endlessly, and don't force a leftover in (that pollutes the evidence more than leaving it aside).**
   - **Dedup against existing tensions** → if a newly split-out tension is really the same pain as one you already have, **merge them** instead of keeping a near-duplicate.

   Stop when every phrase from the failed group sits in a tension that PASSES (or is a logged orphan). *(Phrase extraction (2a) is never re-run — the phrases stand; you're only re-deciding the tension they form.)*

**📏 Size alarm (a split tripwire, not a hard cap).** If a candidate tension ends up with **more than ~8 posts OR ~15 phrases**, treat it as *presumed merged-by-topic* — that size almost always means several pains got lumped. Re-run the merge check and split, unless you can write one specific shared-pain sentence (step 1) that honestly covers all of them. (First Testlify run had two tensions at 40+ phrases that were each really 4–5 pains — this alarm is what catches that.)

Tag each tension with the niche's audience split — define the split for this niche (e.g. for hiring: employer / candidate / both) and apply it consistently. (Exactly how you decide audience is spelled out in 2d.)

**Output the phrase map → phrase-map.csv.** As you assign phrases to tensions, log every assignment: **one row per *distinct* phrase** (not one row per occurrence — if a phrase shows up in several posts, list those post_ids comma-separated in that single row), the tension it rolled into, and the post_id(s) it came from. This is the audit trail from raw words → tensions — anyone can see exactly which phrases justify each tension, and trace each back to a real post.

| phrase | tension | source post_id(s) |
|---|---|---|
| fake remote listings | Candidates apply for roles advertised as remote that turn out to be onsite… | t3_abc, t3_def |
| secretly onsite | Candidates apply for roles advertised as remote that turn out to be onsite… | t3_ghi |
| ghosted after interview | Candidates hear nothing back after investing hours in interviews… | t3_jkl |

### 2c — Assign every post to a tension

Using the cards you already read in Stage 1 (no re-reading needed):

- Pick the tension by the **dominant pain**, not surface words or an incidental detail. Use top_comments to confirm. **Watch the trap:** a post about a marathon interview that *also* mentions pay belongs in the interview-rounds tension — don't let the secondary salary mention drag it into a salary pile. (That exact mistake undercounted the interview-rounds tension on the first Testlify run.)
- One **primary** tension per post + optionally one secondary cross-reference. Each post lives in one pile (primary); the secondary is a note, it doesn't move the post.
- **There is NO "off-brand" or "ignore" bucket in Stage 2.** Whether a tension is right for *this company* is a **Stage 3** decision, made with a written reason — never a silent delete here. Every coherent pain becomes a tension regardless of brand fit.
- **Don't force bad fits → `misc`.** `misc` is **only** for posts that share no pain with any other post — *not* a dumping ground for off-brand-but-coherent posts (those still get a real tension). Some posts genuinely staying in `misc` after a recheck is fine — leaving a true no-fit aside beats forcing it into the wrong pile.
- **Re-mine `misc` (required, not optional).** After sorting, scan `misc`: for every group of **3+ posts** sharing an issue, promote it to a real tension. **Write down the misc count**; if `misc` holds more than ~15% of all posts, the sort was lazy — go back and re-mine it.
- Flag genuinely unclear posts as "needs review" rather than guessing.

### 2d — Build the tension record per tension → tensions.csv

One row per tension. The **How it's produced** column says, field by field, what you read and whether it's an LLM judgment or a mechanical count. **LLM** = the model decides it by reading; **mechanical** = a count/sum straight off the Posts tab, no judgment.

| Field | What it holds | How it's produced |
|---|---|---|
| Tension | The one-sentence conflict statement | **LLM** — written in 2b from the grouped phrases + the posts under them |
| Phrases | The phrases that rolled into this tension | Mechanical — pulled from phrase-map.csv (all phrases whose tension = this row). Including them here means each tension carries the raw words people used |
| Core pain | What's actually hurting people, in 1 line | **LLM** — read this tension's **phrases** and name the hurt *under* them. Tension = the conflict; core pain = why it stings. (Tension: "remote turns out onsite" → core pain: "people relocate / rearrange their life around a promise that was false") *Derived from the phrases — they're the distilled pain already, so no re-reading of posts needed.* |
| Audience | employer / candidate / both (or niche equivalent) | **LLM** — infer from this tension's **phrases** who's speaking. **Don't default to "both"** — pick "both" only when *both sides genuinely argue* inside the pile; if it's recruiters venting (e.g. r/recruiting, r/ModernHiring), it's "employer". *Read from the phrases; phrases drop the speaker, so this is an approximation, fine for how it's used.* |
| Emotion | anger / anxiety / disbelief / ridicule | **LLM** — pick **exactly one from this closed set** (anger / anxiety / disbelief / ridicule). No free-text emotions — "frustration / indignation / despair / contempt" are not allowed; map them to the nearest of the four. *Read from the phrases (tone is approximate, fine here).* |
| # posts | How many posts in this pile | Mechanical — count of posts assigned to this tension in 2c |
| Post list | post_ids / titles | Mechanical — the post_ids from 2c |
| Total upvotes | Summed across the pile | Mechanical — sum of `score` over the pile |
| Total comments | Summed across the pile | Mechanical — sum of `comment_count` over the pile |
| Avg debate ratio | avg comments ÷ upvotes = how heated the tension is | Mechanical — computed from the two columns above |
| Subreddit spread | Which communities it spans | Mechanical — distinct `subreddit` values in the pile |
| Best example | The single strongest post + URL | **LLM judgment** — the one post that most clearly embodies the tension |
| Representative quotes | 2–3 verbatim top_comments (the authentic language people use) | **LLM selection** — the most vivid real quotes from the pile, copied verbatim |
| Sub-questions | The distinct questions inside the tension (potential content angles) | **LLM** — only what people **actually argue about in the posts**. Do **NOT** include solution/product questions ("would [product] fix it?", "do skills tests solve this?") — that's Stage 4 leaking backwards into the evidence. Keep it to the real debate. |
| Implied data point | A number the company could measure or publish (e.g. "% of 'remote' listings that are secretly onsite") | **LLM** — the measurable stat the tension is begging for |
| Linkability verdict | (Stage 3) | Stage 3 — **LLM** judgment |
| Ownability verdict | (Stage 3) | Stage 3 — **LLM** judgment vs. brand-scope.md |
| Asset idea | (Stage 4) | Stage 4 — **LLM** |

End of Stage 2: **tensions.csv** — one row per tension + its full evidence (now including its phrases); and **phrase-map.csv** — the phrase→tension audit trail.

### 🚦 Stage 2.5 — self-audit gate (pass this before any filtering)

Tick every box in writing before starting Stage 3. If any fails, fix Stage 2 first — don't filter on a bad sort.

- ☐ **Every tension sentence is specific** — names one concrete conflict, no banned vague predicate (2b tripwire). `_work/merge-check.md` exists and shows the PASS/SPLIT call per tension.
- ☐ **No oversized tension** left un-split — anything >~8 posts / >~15 phrases was either split or carries a written "genuinely one pain" justification.
- ☐ **`misc` was re-mined** — count recorded, every 3+ cluster promoted; misc is not a hidden "off-brand" dump and is not >~15% of posts.
- ☐ **Fields are in their closed vocabularies** — emotion ∈ {anger, anxiety, disbelief, ridicule}; audience not lazily "both"; sub-questions carry no product/solution questions.
- ☐ **phrase-map.csv is one row per distinct phrase** (post_ids comma-separated).

Only when all five pass → Stage 3.

---

## STAGE 3 — Filter the tensions

Two explicit tests per tension — scored, not gut feel. Both are **LLM judgment calls**, just structured ones. Write the verdicts into tensions.csv.

### Test A — Linkability (would anyone cite an asset about this?)

Ask four questions:
1. Is there a citable number? — a stat an asset could produce that a writer would reference ("% of fake-remote listings" = yes; "craziest rejection email" = no)
2. Would a journalist or blogger reference it when writing about the niche?
3. Is it evergreen enough — not a one-off viral moment that dies in a week?
4. Does it fit a proven link-bait format (index / calculator / data report / guide)?

Needs **≥3 of 4 yes** to pass. This is the gate where pure-drama tensions — huge upvotes, no citable substance — die.

### Test B — Ownability (can this company credibly own it?)

Run the tension against the approved **brand-scope.md** (the same G0 document built in Method 1 — it lives at `projects/[company]/02-asset-engine/competitor-study/output/brand-scope.md`, e.g. for Testlify `projects/testlify/02-asset-engine/competitor-study/output/brand-scope.md`). Ask:
- Does this tension sit inside the brand scope (CORE / TRANSPLANT / ADJACENT)?
- Does the company have the data, product, or authority to speak credibly on it?
- Does building it reinforce the brand?

A CORE or TRANSPLANT verdict passes. ADJACENT is a maybe.

**Out-of-scope? You MUST run the transplant check before dropping — don't bin it on ownability alone.** This is a required two-step, not an afterthought:
1. **In scope?** If yes → CORE/ADJACENT, done.
2. **If no → transplant check (mandatory):** is there a strong, *linkable* format here we can point at an **in-scope** subject? If yes, KEEP as **TRANSPLANT** and record the move; only if the transplant *also* fails does the tension DROP.

Record the transplant verdict explicitly for **every** out-of-scope tension (even when it's "no transplant — drop"), so the audit shows the check happened. Worked examples: *salary-game tension (off-brand) → transplant "% of candidates clients lose between offer and accept, and what predicts it" (in scope: hiring outcomes); ghost-jobs tension → transplant "the phantom-posting index" pointed at screening integrity.* (On the first Testlify run, salary and ghost-jobs tensions were dropped on ownability with no transplant attempt — this step is what stops that.)

Using brand-scope.md here keeps the ownability judgment consistent with Method 1 — the same approved anchor, not a fresh ad hoc call.

### Decide & record

Each tension → **KEEP / DROP / MAYBE** + a one-line reason in the verdict columns.

🚫 Present the KEEP/DROP list to the user and get sign-off before Stage 4. This is a gate — no effort goes into shaping ideas until the user approves the surviving tensions.

End of Stage 3: filtered tensions.csv — only link-worthy, company-ownable tensions survive.

---

## STAGE 4 — Tensions → asset ideas → study-trends-ideas.csv

Walk the kept tensions and turn each into one asset idea (**this is an LLM step**). No format-borrowing here — picking a proven format is Methods 1 and 2's job. Method 3's edge is the tension itself, so the asset's shape comes straight from what the tension is calling for.

**What goes into generating one idea.** For each kept tension, the prompt gets *all* of its evidence, not just the headline:

- From the tension's row in tensions.csv: **tension sentence · core pain · the phrases** (all of them — the real words) **· representative quotes · audience · emotion · implied data point · sub-questions · subreddit spread + the Reddit signal numbers** (# posts, upvotes).
- From Stage 3: the **brand-fit verdict** (CORE / TRANSPLANT / ADJACENT) and its reason.
- From the layers before: **brand-voice.md + features.md + stats.md** (voice, product, data) and **brand-scope.md**.

The implied data point usually *is* the asset (e.g. "% of 'remote' jobs that are secretly onsite" → a data report); the sub-questions can become a content series. Then **carry the Reddit signals** into the output row so ideas can be prioritised by heat.

**Example prompt** (run once per kept tension — fill the `<…>` from that tension's row):

```
You are generating ONE link-worthy asset idea for [COMPANY].

BRAND BRAIN (voice, product, data, authority):
<paste the relevant summary from brand-context/brand-voice.md + features.md>

BRAND-SCOPE verdict for this tension: <CORE / TRANSPLANT / ADJACENT> — <one-line reason from Stage 3>

THE TENSION (all of its evidence):
- Tension:            <one-sentence conflict>
- Core pain:          <1 line>
- Phrases people used: <phrase 1> · <phrase 2> · <phrase 3> · <phrase 4> …   (use ALL of them — this is the real language)
- Audience:           <employer / candidate / both>
- Emotion:            <anger / anxiety / disbelief / ridicule>
- Implied data point: <the measurable number this tension implies>
- Sub-questions:      <q1; q2; q3>
- Representative quotes: "<verbatim quote 1>"  /  "<verbatim quote 2>"
- Reddit signal:      <# posts> posts · <total upvotes> upvotes · spans <subreddits>

TASK:
1. Propose ONE asset [COMPANY] can credibly own that resolves or quantifies this tension.
2. Its SHAPE must come from the tension itself — the implied data point usually IS the asset;
   the sub-questions can become a series. Do NOT borrow a generic format.
3. Write a real working title in the company's voice, with the tension visible in it
   (not a format label like "Data report on remote jobs").
4. Name the unfair advantage — the product, data, or authority that lets THIS company own it.

Return exactly: Asset title · What it'd be (1–2 lines) · Brand fit · Unfair advantage.
```

### Output columns — study-trends-ideas.csv

| Column | What it holds |
|---|---|
| Tension | The one-sentence conflict from Stage 2 |
| Asset title | Working title in the company's voice — a real title, not a format label |
| What it'd be | 1–2 lines: what the asset actually is |
| Brand fit | CORE / TRANSPLANT / ADJACENT (from brand-scope.md) |
| Unfair advantage | The product, data, or authority that lets this company own it |
| # posts | How many distinct posts the tension appeared in |
| Audience | employer / candidate / both |
| Emotion | anger / anxiety / disbelief |
| Best example URL | One post URL — the proof the tension is real |

**Asset title rules** (same standard as Method 1):
- A real working title a writer could open a doc with — not a format label like "Data report on remote jobs"
- The tension should be visible in the title
- ❌ "Report on fake remote listings" → ✅ "The Remote Job Mirage: What % of 'Remote' Listings Are Actually Onsite?"

End of Method 3: study-trends-ideas.csv — the timely-tension idea pool, each idea backed by real Reddit engagement signals.

---

# 🔒 STAGE 5 — FINAL VERIFY GATE (the run is NOT done until this passes)

Self-attestation failed before (a checklist the agent *claimed* it ticked). So the final check is a **script the
harness runs, not the agent's word.** From the `study-trends/` directory:

```bash
python3 ../../../../workflows/02-asset-engine/3-study-trends/scripts/study-trends-verify.py .
# (or pass the absolute path to the study-trends/ dir)
```

It **exits non-zero and the run is incomplete** if any of these fail (each maps to a real past failure):
- **ORDER** — `_work/merge-check.md` must predate `tensions.csv` (you can't write the gate after the tensions). *If you edit merge-check.md later, you must rebuild tensions/ideas after it, or this fails.*
- **COVERAGE** — every scraped post_id assigned exactly once; `misc` ≤ 15%.
- **OFF-BRAND** — no DROP bucket > 8 posts unless it's examined by name in merge-check.md (kills the "junk drawer").
- **SIZE-ALARM** — every kept tension with > 15 phrases is justified by name in merge-check.md.
- **GATE** — every kept tension appears in merge-check.md (formed through the gate, not bolted on after).
- **PRODUCT-LEAK** — kept tensions' sub-questions contain no solution/product words (no Stage-4 bleed-back).
- **IDEAS** — kept-tension count == idea count.

Do not report the run as complete, and do not hand the pool to D1, until `VERIFY: PASS`. Paste the PASS line into
RUN-LOG-problems.md. (The script is company-agnostic; it powers every Method-3 run, not just the first.)

---

# ✅ RUN CHECKLIST

Copy into RUN-LOG-problems.md and tick as you go.

**Phase A**
- ☐ Subreddits discovered (or client-supplied), then **vetted by real activity from our own scraper** (top-of-year upvotes/comments; drop dead/empty subs) — not by subscriber counts — before presenting to user
- ☐ User approved the subreddit set (gate passed)
- ☐ Scraper run completed; output saved to `_raw/`
- ☐ Output validated (Posts tab has real content — body + top_comments populated, not just titles)

**Phase B — Stage 2**
- ☐ Every post read as a content card (title + body + image_text + top_comments)
- ☐ Phrases tagged for **every** post — via parallel Sonnet sub-agents (Stage 2a) → reassembled and **validated: every post_id covered exactly once (0 missing / 0 extra)**
- ☐ Every phrase is 2–4 words (no single-word phrases)
- ☐ **Merge check run per candidate tension** (shared-pain sentence + PASS/SPLIT + vague-predicate tripwire), recorded in `_work/merge-check.md` — **written BEFORE `tensions.csv` exists** (the gate runs first; see the 🚨 hard line)
- ☐ **Size alarm cleared** — no tension >~8 posts / >~15 phrases left un-split-or-unjustified
- ☐ Every tension is a sentence stating a *specific* conflict, not a topic label
- ☐ Every post assigned to its **dominant**-pain primary tension (or misc); **no "off-brand/ignore" bucket** in Stage 2
- ☐ **Misc re-mined** — count recorded, 3+ clusters promoted, misc ≤ ~15% of posts
- ☐ phrase-map.csv = one row per distinct phrase; tensions.csv written (incl. Phrases field); fields in closed vocab
- ☐ **Stage 2.5 self-audit gate passed** (all five boxes) before any filtering

**Phase B — Stage 3**
- ☐ Both tests run per tension (Linkability ≥3/4 · Ownability vs brand-scope.md)
- ☐ **Transplant check run for every out-of-scope tension** before any DROP (verdict recorded, even "no transplant")
- ☐ KEEP / DROP / MAYBE verdicts written with one-line reasons
- ☐ User reviewed and approved the surviving tensions (gate passed)

**Phase B — Stage 4**
- ☐ Every kept tension has an asset title (real working title, not a format label)
- ☐ Every row has a Best example URL (proof the tension is real)
- ☐ study-trends-ideas.csv written with all columns populated

**Stage 5 — final gate**
- ☐ `study-trends-verify.py` run and **VERIFY: PASS** (paste the line here). The run is not done until it passes.

---

# Gotchas

**Attention ≠ links** — the single most important filter (Stage 3 Test A). Raw upvotes point at viral drama that earns nothing; keep only the citable tensions.

**Tensions, not topics** — a topic label ("fake remote jobs") tells you nothing about what to build. A tension sentence ("candidates are being baited into applying for secretly-onsite roles") tells you exactly what the asset needs to say.

**Phrases, not words** — always 2–4 word phrases during extraction; single words are too vague to consolidate into real tensions.

**Post count beats upvotes** — one viral post can inflate total upvotes for a thin tension. Trust # distinct posts as the primary signal; upvotes are a magnitude check only.

**Timely but perishable** — trends die. Build a Method-3 asset while the wave is live. Re-run periodically (using `--sort hot` or `--sort rising`) to refresh the tension pool.

**Brand-scope.md is the ownability anchor** — use the same approved document from Method 1's G0, not a fresh ad hoc judgment. Consistency across methods matters when the pools are merged at D1.

---

# How it fits the idea backlog

Method 3's study-trends-ideas.csv is a separate pool from Methods 1 and 2. All three pools are merged at the end of the idea-backlog stage (D1), then validated and prioritised in D2. Method 3's unique contribution to that merge is the timely, current-events tension no other method can surface.