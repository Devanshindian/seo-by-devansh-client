You are tagging competitor pages by **FORMAT** — the *shape* of the page, never its topic.

This is the most important label in the whole study. Everything downstream groups by it: which formats
earn the most links, and therefore what {{BRAND}} should build. A wrong tag poisons that answer.

## Format means SHAPE, not subject

- "10 Best Payroll Tools" and "10 Best CRMs" are the **same format** (a ranking listicle) on different subjects.
- A glossary of HR terms and a glossary of legal terms are the **same format**.
- Ask: *if I stripped the topic out, what KIND of page is this?*

## The starting catalog

Use these where they fit. They are a starting set, **not a cage**:

- **Glossary / dictionary** — many short defined terms, usually an index page plus term pages
- **Calculator / estimator / generator / tool** — the reader inputs something and gets an output back
- **Data report / original research** — the company's own survey, study or benchmark, with figures
- **Statistics roundup** — a collected list of stats gathered from other sources, with citations
- **Rankings / best-of / comparison** — "top N tools", "X vs Y", alternatives pages
- **Templates / examples pack** — downloadable or copyable artefacts (emails, policies, JDs, checklists)
- **Interview-questions listicle** — a long list of questions for a role or skill
- **How-to / step-by-step guide** — a numbered process the reader follows
- **Definitional explainer ("what is X")** — explains one concept in depth
- **Pillar / definitive guide** — a long, structured hub covering a whole subject
- **Checklist / cheat sheet** — a short actionable list meant to be used while working
- **Quiz / assessment / test** — the reader answers questions and is scored
- **Case study** — one named customer or company, what happened, with results
- **Jobs / careers listing** — a directory of roles
- **Free product / library page** — a usable free thing the product itself provides
- **Commercial / sales page** — a page whose job is to SELL: a product/solution overview, a pricing or
  plans page, a "book a demo" / "talk to sales" landing page, a features tour, an integrations directory.
  It describes what the company offers and pushes a demo/trial/purchase. Nobody links to it as a free
  resource — so it is NOT a content asset we can model.

**If a page genuinely fits none of these, invent a new named format** — give it a short name and use it
consistently. Say so by setting `"new_format": true`. Do not force a bad fit.

## The one boundary that matters most: a USABLE ASSET vs a SALES page

This is the label people get wrong, and it decides whether we build on the page or drop it. Judge by what
the page IS FOR, not by who owns it:

- If the page gives the reader a **usable free thing** — a test they can take, a tool/calculator they can
  run, a template they can download, a glossary they can read — tag it by **that asset** (Quiz /
  assessment / test · Calculator / tool · Templates · Glossary · Free product / library page). A company's
  own free skills-test page is a **Quiz / assessment / test**, NOT a sales page, even though the company
  also sells — because the test itself is the usable asset and that's what earns links.
- Tag **Commercial / sales page** ONLY when the page's whole purpose is to SELL and there is no usable free
  asset on it — pricing, plans, "book a demo", a solution/product overview, a feature tour. Tell-tales:
  "Request a demo", "Talk to an expert", "Start free trial", "Trusted by N clients", pricing tiers.
- When a page has BOTH a real usable test/tool AND a sales pitch around it, the **asset wins** — tag it by
  the asset. Only pure sell-pages with nothing usable are Commercial / sales page.

## Use the evidence, not the URL

For each page you get: the URL, the page title, its H1 and H2 headings, its word count, its image count
and its outbound-link count. **The headings are the strongest signal** — they tell you the page's real
structure. Use the numbers too:

- many H2s that are all short noun phrases → often a glossary, listicle or ranking
- very high image count → often an infographic or a visual/interactive asset
- very high outbound-link count → often a statistics roundup or a resource list
- low word count with an interactive-sounding title → often a calculator or tool
- numbered/step-like H2s → a how-to

**Never tag from the URL alone.** A URL is a hint; the headings are the evidence.

## Guard against the lazy bucket

"Other / editorial" is a **last resort**. A previous run put 26% of all pages there and found only ONE
calculator across 2,469 pages in a niche full of them — that is what failure looks like here. If you
find yourself reaching for "Other", look again at the headings and pick the real shape, or name a new
format.

## Return ONLY JSON — one object per page, in the same order you received them

```
{"tags": [
  {"id": "<the id given>", "format": "<one format name>", "confidence": "high|medium|low",
   "why": "<max 12 words — the evidence that decided it, ideally a heading>", "new_format": false}
]}
```

Return exactly one object for every page given. Never skip one.

## THE PAGES
{{PAGES}}
