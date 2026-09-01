"""The COPY for the architect review site — plain-English explainers, written for a non-technical reader.

Kept apart from build_architect_review.py so the prose is editable without touching the rendering.

PROMPTS is the ordered list of every AI call the architect makes, in run order. For each one:
  file    the prompt file in prompts/ (its full text is read from disk, never duplicated here)
  step    which of the five architect steps it belongs to
  when    when it runs (always, or only for one kind of article)
  what    2-4 plain lines: what this call is being asked to decide
  fills   one row per {{FILL-IN}}: the token, what it is, where its value comes from
Every fill row was read off the calling script, not remembered.
"""

STEPS = [
    {"n": 1, "id": "shape", "name": "Shape",
     "one_line": "Decide which sections the article has, in what order, and what goes in each one.",
     "detail": [
         "This is the big one. It reads every fact the research phase collected, grouped into numbered "
         "boxes, and designs the article: the running order, what each section has to do, which facts "
         "go where, and what is left out.",
         "It also writes the spine: one paragraph saying what the whole article argues, who for, and "
         "what the reader can do by the end. Every later step is judged against that paragraph.",
         "Anything the design needs but the research never found gets flagged as a research request, "
         "which step 2 then goes and buys.",
     ],
     "produces": "The draft blueprint: sections, order, jobs, sub-headings, and a list of what is missing."},
    {"n": 2, "id": "enrich", "name": "Enrich",
     "one_line": "Go out to the web and find the facts step 1 said were missing.",
     "detail": [
         "For each gap, it writes a few search queries, runs them, downloads the best pages that load, "
         "and turns what it reads into new fact cards.",
         "The rule that governs it: the writer who comes later cannot open a link or search the web. "
         "So a card that says 'the report gives an average cost per hire' is worthless. The number has "
         "to be inside the card, with who said it and when.",
         "When a search comes back with nothing, that is recorded loudly rather than hidden. The "
         "section stays, thinner than it was designed to be.",
     ],
     "produces": "The blueprint again, now with the bought-in facts attached where they were asked for."},
    {"n": 3, "id": "allocate", "name": "Allocate",
     "one_line": "Decide how many words each section gets.",
     "detail": [
         "One AI call splits the article's word budget across the sections as percentages.",
         "It works in two passes, and the order matters. First: how much does this section matter to "
         "the argument? That sets the number. Second: can it actually be written to that length from "
         "the facts it holds, without padding? Evidence can only ever take words away, never earn them.",
         "For a list article the items share evenly, because a reader reads them side by side. One item "
         "is not three times more important because the research happened to turn up more about it.",
     ],
     "produces": "A word target on every section."},
    {"n": 4, "id": "keywords", "name": "Section keywords",
     "one_line": "Work out which sections deserve their own search keyword, and which one.",
     "detail": [
         "Most sections should not have one. The article has one main search target already. The rest "
         "of the sections exist to carry the argument.",
         "So there is a gate first, and it is free: would a real person type this section's subject "
         "into Google on its own? Only the sections that pass go on to the paid keyword lookup.",
         "For each of those, the AI reads that section's actual facts (a heading can lie, the evidence "
         "cannot), writes two or three short search phrases, pulls real search data, and picks one "
         "keyword or none. Picking none is treated as a good answer.",
     ],
     "produces": "A keyword, or an honest nothing, for each section that earned the lookup."},
    {"n": 5, "id": "headings", "name": "Headings",
     "one_line": "Write the final wording of every heading, then the H1.",
     "detail": [
         "Each heading is written on its own, by a call that can see that section's facts, its job and "
         "its keyword. It is free to use the keyword or drop it.",
         "Then one more call reads all the headings together as a set. This is the only step that can "
         "catch what none of the individual writers could: numbering that jumps, one thing called two "
         "different names, half the list in Title Case and half in sentence case, or the same keyword "
         "stuffed into eight headings because every writer was offered it and every writer said yes.",
         "Finally the H1 is written last, once the machine can see everything the article actually "
         "delivers.",
     ],
     "produces": "The finished blueprint the writer works from."},
]

# The fill-ins that appear again and again, explained once.
COMMON_FILLS = [
    ("{{BRAND}}", "The company publishing the article.",
     "One setting in the config file. Change it and the whole machine points at another company."),
    ("{{ABOUT}}", "One line on what that company does.", "The company record."),
    ("{{TITLE}}", "The article's working title.", "The topic queue, the list of articles waiting to be built."),
    ("{{ANGLE}}", "The one thing this article is built to deliver that the pages already ranking do not.",
     "The topic queue, decided back when the topic was chosen."),
    ("{{PERSONA}}", "Who the article is for, in a line or two. The recruiter, not the candidate.",
     "The article plan plus the company's persona sheet."),
    ("{{WORLD_ABOUT}}", "What this article IS about.",
     "Decided once in the research phase, before anything was searched for."),
    ("{{WORLD_NOT_ABOUT}}", "The neighbouring subjects that share our words but are not us. The clinical "
     "use of a term, a different industry, the other side of the table.",
     "Same place. It is the single most-used guard in the whole architect."),
    ("{{SPINE}}", "One paragraph: what the article argues, for whom, and what the reader can do at the end.",
     "Written by step 1 and then carried into every later prompt."),
    ("{{H1}}", "The headline as it was planned, before any of this ran.", "The article plan."),
    ("{{PRIMARY}}", "The article's main search keyword.",
     "Chosen in the research phase from real search data. The architect is not allowed to change it."),
    ("{{BOXES}} / {{MATERIAL}}", "Every fact the research collected, numbered so the AI can answer with "
     "numbers instead of retyping the material.",
     "The research phase. {{MATERIAL}} is the same thing with fuller card text, used by the calls that "
     "have to read the facts closely."),
    ("{{FORMAT_STRUCTURE}}", "The rulebook for this kind of article: what a how-to guide must contain, "
     "what a comparison must contain, and so on.",
     "One playbook file per format, kept separately and edited by hand."),
    ("{{CARDS}}", "Every fact sitting under one section, one per line.", "The cards, filtered to that section."),
]

PROMPTS = [
    # ---------------------------------------------------------------- step 1
    {"file": "detect-entities.md", "step": 1, "title": "Find the things being compared",
     "when": "Only when the article is a comparison or a ranking.",
     "what": [
         "Reads the research material and lists the named options a reader of this article would "
         "genuinely be choosing between.",
         "Most of its length is spent on what does NOT count: an option aimed at the other side of the "
         "table, something from an adjacent category, a research body the cards happen to cite a lot, "
         "or a tool that produced the research rather than appearing in it.",
         "Anything mentioned by fewer than three cards is dropped. One passing mention is not an option.",
     ],
     "fills": [("{{BRAND}}", "common"), ("{{ABOUT}}", "common"), ("{{TITLE}}", "common"),
               ("{{ANGLE}}", "common"), ("{{WORLD_ABOUT}}", "common"), ("{{WORLD_NOT_ABOUT}}", "common"),
               ("{{PERSONA}}", "common"),
               ("{{MATERIAL}}", "All the research, with fuller card text so it can count mentions properly.")]},

    {"file": "find-yardsticks.md", "step": 1, "title": "Pick what every option gets measured on",
     "when": "Only for a comparison or a ranking, straight after the options are found.",
     "what": [
         "Chooses four to six axes a buyer actually weighs, and that the material can genuinely speak to.",
         "They have to measure different things. Four axes that are all about accuracy is one axis, not four.",
     ],
     "fills": [("{{BRAND}}", "common"), ("{{ABOUT}}", "common"), ("{{TITLE}}", "common"),
               ("{{ANGLE}}", "common"), ("{{WORLD_ABOUT}}", "common"), ("{{WORLD_NOT_ABOUT}}", "common"),
               ("{{ENTITIES}}", "The options the previous call just found."),
               ("{{MATERIAL}}", "All the research, with fuller card text.")]},

    {"file": "filter-tools.md", "step": 1, "title": "Drop the options we cannot actually say enough about",
     "when": "Only for a comparison or a ranking, third of the three.",
     "what": [
         "Goes option by option and shows its working: which of the yardsticks does the material really "
         "have information about for this one? Keep it only if it covers at least 60% of them.",
         "There is a sanity check built in. If a dropped option has more cards behind it than a kept "
         "one, the AI is told it has misread the material and must recount that pair.",
         "The publishing company is never dropped. If we are in the comparison, we stay in it and get "
         "judged on the same scale as everyone else.",
     ],
     "fills": [("{{BRAND}}", "common"), ("{{ABOUT}}", "common"), ("{{TITLE}}", "common"),
               ("{{ANGLE}}", "common"), ("{{WORLD_ABOUT}}", "common"), ("{{WORLD_NOT_ABOUT}}", "common"),
               ("{{ENTITIES}}", "The options found two calls ago."),
               ("{{YARDSTICKS}}", "The axes the previous call chose."),
               ("{{MIN_PCT}}", "The pass mark. Set to 60 in the config file."),
               ("{{PAGES_NOTE}}", "Empty in this run. A slot kept for a future variant."),
               ("{{MATERIAL}}", "All the research, with fuller card text.")]},

    {"file": "detect-items.md", "step": 1, "title": "Find the items of a list article",
     "when": "Only when the article is a listicle.",
     "what": [
         "Works out what the individual entries of the list actually are. For an article about "
         "onboarding mistakes it is each mistake; for interview questions it is each question as it "
         "would be asked out loud.",
         "Two items a reader would answer the same way are one item, so near-duplicates get merged.",
         "An item survives only if the material holds evidence about that item specifically. A passing "
         "mention inside a general box does not qualify.",
     ],
     "fills": [("{{BRAND}}", "common"), ("{{ABOUT}}", "common"), ("{{TITLE}}", "common"),
               ("{{ANGLE}}", "common"), ("{{WORLD_ABOUT}}", "common"), ("{{WORLD_NOT_ABOUT}}", "common"),
               ("{{PERSONA}}", "common"),
               ("{{MAX_ITEMS}}", "The ceiling on how many items to return. Set to 12."),
               ("{{MATERIAL}}", "All the research, with fuller card text.")]},

    {"file": "structure-simple.md", "step": 1, "title": "Design the article: the main prompt",
     "when": "The default. Runs for how-to guides, definitional pieces, data reports, glossaries.",
     "headline_prompt": True,
     "what": [
         "This is the longest and most important prompt in the architect, and the three below it are "
         "this same prompt with an extra middle section bolted on.",
         "It hands over every fact as a numbered box and asks for a design: the spine first, then the "
         "sections in reading order, each with its job written before its heading, then which boxes go "
         "in which section, then whether a section is big enough to need sub-headings at all.",
         "A lot of it is arithmetic the AI is made to do out loud. A section needs roughly 300 words, "
         "so the word budget divided by 300 is the ceiling on how many sections there can be. A "
         "paragraph is about 100 words, so a section is about three paragraphs, so a section only "
         "splits into sub-headings when the material is genuinely worth more than that.",
         "Nothing is ever dropped silently. Every box left out of the article needs one line saying why.",
     ],
     "fills": [("{{BRAND}}", "common"), ("{{ABOUT}}", "common"), ("{{TITLE}}", "common"),
               ("{{ANGLE}}", "common"), ("{{H1}}", "common"), ("{{WORLD_ABOUT}}", "common"),
               ("{{WORLD_NOT_ABOUT}}", "common"), ("{{PERSONA}}", "common"),
               ("{{FORMAT_STRUCTURE}}", "common"), ("{{BOXES}}", "common"),
               ("{{WORD_BUDGET}}", "How long the article should be. Comes from the research phase."),
               ("{{SECTION_TARGET}}", "The ceiling on the number of sections: the word budget divided by 300."),
               ("{{WORDS_PER_SECTION}}", "300. A house setting."),
               ("{{WORDS_PER_SENTENCE}}", "25. A house setting."),
               ("{{SENTENCES_PER_PARAGRAPH}}", "4. A house setting."),
               ("{{WORDS_PER_PARAGRAPH}}", "100, worked out from the two above."),
               ("{{PARAGRAPHS_PER_SECTION}}", "3, worked out from 300 words a section."),
               ("{{MIN_WORDS_PER_SUBHEAD}}", "200. The least a sub-heading can be worth before it is "
                "just a label on a paragraph."),
               ("{{PARAGRAPHS_PER_SUBHEAD}}", "2, worked out from the line above.")]},

    {"file": "structure-listicle.md", "step": 1, "title": "Design the article: the list version",
     "when": "Only when the article is a listicle.",
     "what": [
         "The same prompt as above, with two blocks added.",
         "First, arithmetic that fits the list to the word budget: reserve words for the supporting "
         "sections up front, divide what is left by the number of items, and if an item cannot clear "
         "200 words, drop items until they can. Every dropped item is named with a reason.",
         "Second, the per-item contract. If the angle promises something that must come back on every "
         "item (best for, pricing, a strong answer and a weak answer), those become labelled "
         "parts every item section has to end with. The test for a contract field is whether a reader "
         "could lay it side by side across all the items and learn from the differences.",
     ],
     "fills": [("(everything the main prompt takes)", "See the prompt above."),
               ("{{ENTITIES}}", "The list items found by the detect-items call, each with how many cards back it."),
               ("{{SUPPORTING_RESERVE}}", "Words held back for the supporting sections: 900 (3 sections x 300)."),
               ("{{SUPPORTING_MAX}}", "The most supporting sections allowed: 3."),
               ("{{MIN_ITEM_WORDS}}", "200. Below this an item is a stub."),
               ("{{MIN_ITEMS}}", "5. A list shorter than this has stopped being a list.")]},

    {"file": "structure-comparison.md", "step": 1, "title": "Design the article: the comparison version",
     "when": "Only when the article is a comparison or a ranking.",
     "what": [
         "The same prompt again, plus the results of the three calls that ran before it.",
         "Every option that survived gets its own section, even if that pushes the article over the "
         "section ceiling. A comparison that quietly leaves out one of the things it was built to "
         "compare is worse than a long one.",
         "The options that were removed are named too, with an instruction not to use their material "
         "anywhere in the article, not even as an aside.",
         "And there is a credibility rule: if we are one of the options, we appear in every table and "
         "every ranked list the others appear in, judged on the same scale, even where we score below "
         "a rival.",
     ],
     "fills": [("(everything the main prompt takes)", "See the main prompt above."),
               ("{{CATEGORY}}", "What kind of thing the reader is choosing between, in one line."),
               ("{{ENTITIES}}", "The options that survived, each with the yardsticks it is short of information on."),
               ("{{DROPPED}}", "The options that were removed, so the design knows not to use them."),
               ("{{YARDSTICKS}}", "The axes every option's section should speak to.")]},

    {"file": "structure-template.md", "step": 1, "title": "Design the article: the downloadable version",
     "when": "Only when the article wraps a template, checklist or sheet the reader can download.",
     "what": [
         "The same prompt with one addition: as well as designing the page, decide the download itself. "
         "What kind of file it should be, and which material goes inside it rather than on the page "
         "around it.",
     ],
     "fills": [("(everything the main prompt takes)", "See the main prompt above.")]},

    # ---------------------------------------------------------------- step 2
    {"file": "plan-queries.md", "step": 2, "title": "Write the search queries for one gap",
     "when": "Once per research request raised by step 1.",
     "what": [
         "Turns a research request into up to three real search queries, phrased the way people "
         "actually search: short, concrete, varied, so one dead end does not sink the topic.",
         "It is told to aim at the section's job rather than its heading. A heading is a label and can "
         "be vague; the job says what the section actually has to give the reader.",
         "And it must put the setting or the audience into the query itself, because a bare query on a "
         "shared word returns a different field's pages, and every card built from those looks "
         "plausible and is wrong.",
     ],
     "fills": [("{{BRAND}}", "common"), ("{{ABOUT}}", "common"), ("{{TITLE}}", "common"),
               ("{{ANGLE}}", "common"), ("{{WORLD_ABOUT}}", "common"), ("{{WORLD_NOT_ABOUT}}", "common"),
               ("{{PERSONA}}", "common"),
               ("{{SECTION_HEADLINE}}", "The working heading of the section the gap belongs to."),
               ("{{SECTION_JOB}}", "What that section has to deliver, written by step 1."),
               ("{{H3}}", "The research request itself: what is missing."),
               ("{{N}}", "How many queries to write. Set to 3.")]},

    {"file": "search-urls.md", "step": 2, "title": "The backup way to search",
     "when": "Only when the paid search account is out of credit.",
     "what": [
         "Normally the queries go to a paid search data provider. When there is no credit left, this "
         "short prompt asks the AI to run the searches itself and hand back the result links.",
         "The only real rule: real URLs that actually appeared in the results, never constructed or "
         "guessed.",
     ],
     "fills": [("{{QUERIES}}", "The queries the previous call planned."),
               ("{{MAX}}", "How many links to return.")]},

    {"file": "extract-cards.md", "step": 2, "title": "Turn the downloaded pages into fact cards",
     "when": "Once per research request, after the pages have been downloaded.",
     "what": [
         "This is where the machine's honesty rule lives, and it is worth reading in full.",
         "The card is all the writer will ever see. That writer cannot open the source link, cannot "
         "search the web, and cannot see the page being read here. So the actual number has to be in "
         "the card, along with who published it, when, and what it covers.",
         "One card summarises one page only. Blending two sources into a single card is banned.",
         "If the pages turned up nothing genuinely useful, it returns nothing. Weak cards are worse "
         "than no cards.",
     ],
     "fills": [("{{BRAND}}", "common"), ("{{ABOUT}}", "common"), ("{{TITLE}}", "common"),
               ("{{ANGLE}}", "common"),
               ("{{SECTION_HEADLINE}}", "The heading of the section this material is for."),
               ("{{H3}}", "The research request being filled."),
               ("{{PAGES}}", "The text of each downloaded page, labelled with its link. The top 8,000 "
                "characters of each.")]},

    # ---------------------------------------------------------------- step 3
    {"file": "allocate-words.md", "step": 3, "title": "Split the word budget across the sections",
     "when": "Always, once per article.",
     "what": [
         "Asks for a percentage per section, in two passes that answer different questions.",
         "Pass one is importance. The section carrying the article's central claim earns the most words "
         "even when it is thinly evidenced; a section that sets up or hands off earns few even when it "
         "is stacked with facts.",
         "Pass two is a ceiling, never a claim: can this section be written to that length from the "
         "material it holds, without padding? A long list of facts is often the same point restated by "
         "twelve sources and compresses into two sentences.",
         "List items are exempt from the ranking and share evenly, because a reader compares them side "
         "by side.",
     ],
     "fills": [("{{BRAND}}", "common"), ("{{ABOUT}}", "common"), ("{{TITLE}}", "common"),
               ("{{ANGLE}}", "common"), ("{{SPINE}}", "common"), ("{{PERSONA}}", "common"),
               ("{{TARGET}}", "The total words to distribute, the middle of the article's word band."),
               ("{{SECTIONS}}", "Every section with its job, what it covers, how many sub-headings it "
                "has, and a one-line summary of every fact it holds."),
               ("{{MIN_WORDS_PER_SUBHEAD}}", "200, the same floor step 1 used."),
               ("{{CARD_CAP}}", "How many facts are shown per section before the rest are summarised as "
                "a count. Set to 60.")]},

    # ---------------------------------------------------------------- step 4
    {"file": "keyword-gate.md", "step": 4, "title": "Decide which sections deserve a keyword at all",
     "when": "Always, once per article. This call is free.",
     "what": [
         "One question per section: would this reader type this section's subject into Google as their "
         "own search?",
         "Not anyone. That reader. A phrase the other side of the table searches for brings the wrong "
         "visitor to the page, and they leave.",
         "It is told to expect roughly a third to a half to be yes, and told plainly that saying yes to "
         "nearly all of them means it is being too generous.",
         "Nothing is bought for a section the gate rejects.",
     ],
     "fills": [("{{TITLE}}", "common"), ("{{ANGLE}}", "common"), ("{{SPINE}}", "common"),
               ("{{ABOUT}}", "What the article is about."),
               ("{{NOT_ABOUT}}", "What it is not about."),
               ("{{PRIMARY}}", "common"), ("{{PERSONA}}", "common"),
               ("{{SECTIONS}}", "Every section, numbered, with its job.")]},

    {"file": "section-seeds.md", "step": 4, "title": "Write the search phrases to look up",
     "when": "Once per section that passed the gate.",
     "what": [
         "Asks for two or three short phrases a person would type to find this section.",
         "It is told to read the evidence, not the heading. A section whose heading says 'pricing' but "
         "whose facts are all commission percentages is a section about commission rates.",
         "The most important rule here is length. These phrases go into a keyword lookup that matches "
         "on the phrase itself, and a four or five word phrase almost always returns nothing at all, "
         "which leaves the section with no keyword.",
     ],
     "fills": [("{{TITLE}}", "common"), ("{{SPINE}}", "common"),
               ("{{ABOUT}}", "What the article is about."),
               ("{{NOT_ABOUT}}", "What it is not about."),
               ("{{PRIMARY}}", "common"), ("{{PERSONA}}", "common"),
               ("{{HEADING}}", "This section's working heading."),
               ("{{JOB}}", "What this section has to deliver."),
               ("{{CARDS}}", "Every fact this section holds.")]},

    {"file": "pick-section-keyword.md", "step": 4, "title": "Choose one keyword from the real search data",
     "when": "Once per section, after the lookup has come back.",
     "what": [
         "Real keywords with their monthly search volume and difficulty go in; one choice, or nothing, "
         "comes out.",
         "Fit first, volume second. A bigger number for a phrase the section does not answer is worth "
         "nothing, because the page ranks and the reader bounces.",
         "Returning nothing is stated to be a good answer. Do not stretch.",
     ],
     "fills": [("{{HEADING}}", "This section's working heading."),
               ("{{JOB}}", "What this section has to deliver."),
               ("{{WHY}}", "One line from the previous call on what this section is really about, "
                "judged from its evidence."),
               ("{{SPINE}}", "common"), ("{{NOT_ABOUT}}", "What the article is not about."),
               ("{{PRIMARY}}", "common"),
               ("{{PERSONA}}", "common"),
               ("{{CANDIDATES}}", "The real keywords that survived the filters, with volume and "
                "difficulty. Only phrases with at least 100 monthly searches and difficulty under 40.")]},

    # ---------------------------------------------------------------- step 5
    {"file": "write-heading.md", "step": 5, "title": "Write one section's final heading",
     "when": "Once per section, all of them at the same time.",
     "what": [
         "Writes the heading a reader will actually see, aiming under 60 characters so it is not cut "
         "off in search results.",
         "The keyword is offered, not imposed. There is a four-step order: the section's own researched "
         "keyword, then the leftover pool, then the article's main keyword, then none at all. A "
         "well-researched keyword that does not fit is still a keyword that does not fit.",
         "The evidence overrules the plan. The section's job was written before the research came back; "
         "the evidence is what it really holds now, and where the two disagree the evidence wins.",
         "It names the generic headings an AI reaches for by default (Overview, Key considerations, "
         "Understanding X) and bans them, with worked before-and-after examples.",
     ],
     "fills": [("{{TITLE}}", "common"), ("{{ANGLE}}", "common"), ("{{SPINE}}", "common"),
               ("{{PERSONA}}", "common"), ("{{PRIMARY}}", "common"),
               ("{{VARIATIONS}}", "Other wordings of the main keyword."),
               ("{{HEADING}}", "The draft heading from step 1."),
               ("{{JOB}}", "What this section has to deliver."),
               ("{{SECTION_KEYWORD}}", "The keyword step 4 researched for this section, with its volume "
                "and difficulty, or a note that none was found."),
               ("{{POOL}}", "Researched keywords not yet used anywhere, in case one fits better."),
               ("{{CARDS}}", "Every fact this section holds.")]},

    {"file": "heading-pass.md", "step": 5, "title": "Read all the headings together and fix the set",
     "when": "Always, once, after every heading has been written.",
     "what": [
         "The prompt opens by explaining why it exists: every heading was written by a different call "
         "that could only see its own section, so nobody has read them as a list yet.",
         "It hunts for the faults only the whole set reveals. Numbering that runs 1 to 5 then jumps to "
         "16. One thing called 'BARS' in one heading and its full name in another. Half the article in "
         "Title Case. Eight headings in a row built to the same template. A heading aimed at the wrong "
         "reader.",
         "Two things it may never change: a keyword we paid for stays word for word, and a heading must "
         "still promise what its section can deliver.",
         "The one exception is a keyword that got over-used. Because every heading writer was offered "
         "the same phrase and every one accepted it, the same keyword can end up in most of the "
         "headings, which makes the page read as written for a search engine. This call decides which "
         "two genuinely earn it and strips it from the rest. Code then checks both directions: a "
         "heading that lost a keyword it should have kept is thrown out and the original put back, and "
         "if the pass stripped a phrase from too many headings the whole pass is refused.",
         "And it is told to leave a good heading alone. Changing a heading that works is a cost with no "
         "gain, and it buries the changes that matter.",
     ],
     "fills": [("{{TITLE}}", "common"), ("{{ANGLE}}", "common"), ("{{SPINE}}", "common"),
               ("{{PERSONA}}", "common"), ("{{PRIMARY}}", "common"),
               ("{{HEADINGS}}", "Every heading in order, each with its job and, where research bought "
                "one, its locked keyword."),
               ("{{OVERUSED}}", "Which phrases appear in too many headings, counted by code, not by the AI."),
               ("{{KEYWORD_CAP}}", "The most headings one keyword may appear in. Set to 2.")]},

    {"file": "write-h1.md", "step": 5, "title": "Write the H1, last",
     "when": "Always, once, after the headings are final.",
     "what": [
         "The H1 is written at the very end, once the machine can see every heading the article "
         "actually delivers.",
         "It must carry the main keyword naturally and must not promise something the headings do not "
         "deliver. If the planned H1 already carries the keyword, it is returned unchanged.",
     ],
     "fills": [("{{H1}}", "The H1 as planned before any of this ran."),
               ("{{ANGLE}}", "common"), ("{{SPINE}}", "common"), ("{{PRIMARY}}", "common"),
               ("{{VARIATIONS}}", "Other wordings of the main keyword."),
               ("{{HEADINGS}}", "Every final heading, in order.")]},
]
