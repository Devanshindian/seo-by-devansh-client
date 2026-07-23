Proven cross-niche link-bait format: **{{FORMAT}}** (headline template: `{{HEADLINE_TEMPLATE}}`; earns links
via **{{WHY_LINKS}}**). Source-niche example: **{{EXAMPLE}}**.

Using {{BRAND}}'s brand context below — product, audience, real data — give me the **single strongest {{BRAND}}
adaptation** of this format. Borrow the **shape**, not the source niche's subject. Point it at the in-scope
subject from the swipe row (**{{IN_SCOPE_SUBJECT}}**, brand fit **{{BRAND_FIT}}**), and name the specific
**product, data, or authority** that lets us own it.

## {{BRAND}} brand context
### Brand scope (what we can own)
{{BRAND_SCOPE}}
### Brand voice (how we write our headlines)
{{BRAND_VOICE}}
### Features (the product we can point to)
{{FEATURES}}
### Stats (the real data we hold)
{{STATS}}

## Two rules (the format-honesty rules — same as Method 1)
- **The `asset` name carries NO shape-words.** It says the subject + the angle, never the format. Banned in
  the name: Calculator, Quiz, Generator, Interactive, Dashboard, Tool, Widget, Estimator, Configurator, Index.
  The shape lives in the format label + `what_it_would_be`, never in the title.
- **Be honest about what it takes to build, and FLAG it.** Many imported formats are interactive tools or need
  original data — that's allowed, but it must be tagged in `tool_escalation`, never hidden. A writer with
  public sources can ship an article / list / guide; they CANNOT ship a calculator, quiz, generator, an
  interactive widget, our own survey / original-data study, or new primary research. If the asset needs any of
  those, say so in one line. Leave it empty ONLY when a writer could genuinely build this from desk research.

## Return EXACTLY these fields, in THIS order — work out the substance before you name the thing
Return strict JSON only:
```
{
 "our_topic": "<the specific subject — sharpen the in-scope subject '{{IN_SCOPE_SUBJECT}}' to a precise one, grounded in the brand context>",
 "distinct_angle": "<one line: what makes OUR version the link-magnet. It MUST name the specific product, data, or authority that lets us own it. Anti-generic test: if it could be written without the brand context above, it is too generic — rewrite.>",
 "asset": "<only now, name it: a REAL working title, subject + angle, NO shape-words. NOT '[Format] on [topic]'. e.g. NOT 'Bad-Hire Cost Calculator' -> YES 'What a Bad Hire Really Costs, Per Role (on real customer data)'>",
 "tool_escalation": "<empty '' if a writer could build this from public sources; else a ONE-LINE reason it needs a build — e.g. 'interactive calculator', 'scored quiz/generator', 'needs our own original survey data', 'needs new primary research'>",
 "headline": "<the published H1 in {{BRAND}}'s brand voice, built from the headline template — the marketing headline, distinct from the build-name asset>",
 "what_it_would_be": "<1-2 lines: the actual asset, concretely (inputs, output, what ships)>",
 "source_niche": "<where this format proved itself, from the example — e.g. 'finance', 'real estate', 'B2B SaaS', 'economics'>"
}
```
Do NOT return a `brand_fit` — that is decided elsewhere. One strong idea, not five variations.
