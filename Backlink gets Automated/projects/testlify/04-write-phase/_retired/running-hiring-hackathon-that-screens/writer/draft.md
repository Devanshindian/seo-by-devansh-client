# Hiring Hackathon Judging: Rubric, Calibration, AI Rule

The demos land, the panel takes notes, and hackathon judging turns into a room where every judge measured something different. In a SHRM Labs report, 45.8% of HR and talent acquisition practitioners called their own hiring process inconsistent.

A score that changes with the judge is a hire that changes with the judge. The fix sits in the scoring, not the event. Three things decide it: the rubric, a panel that reads it the same way, and the rule on AI.

## Quick answer

Build the scoring before the event exists. Take five or six weighted criteria from the job description, not from what the demos happen to show. Write down what a failing, an acceptable and a top submission looks like on each.

Have judges score practice work privately, then compare numbers and fix any wording two people read differently. Publish an AI rule with the brief: what candidates may generate, what they must disclose, what disqualifies them. Score how well AI was used, not whether it was.

## Your Hackathon Is a Work Sample Test, Not a Demo Day

Ask candidates to build in a realistic environment and you have run a [work sample test](https://testlify.com/job-simulation/). That changes what your scoring has to survive.

Work samples show a standardized mean difference of about 0.38 between Black and white test-takers, against about 1.0 for cognitive ability tests. So they carry far lower adverse impact risk: rejecting one group at a much higher rate than another. That holds only if you score on predetermined, job-linked criteria. Because the tasks come from the job itself, your rubric also becomes a content-validity argument under the Uniform Guidelines on Employee Selection Procedures (1978).

Designing the build task itself is a separate job, and we have set out [how to design a job-linked coding exercise](https://testlify.com/best-practices-for-designing-coding-assessments/).

## The Judging Criteria: Five or Six, Weighted, One Total

Score five or six criteria, not ten, and fix the weights before the event opens. Predefine the skills the exercise actually tests, and pick one scale. Too many criteria tire judges and lower consistency. Too few leave you unable to tell what went wrong. Pull them from the job description, not from what the demos show you.

Weighting stops a candidate who presents beautifully from finishing level with one who built the thing. Adjust this allocation to the role, keep it summing to 100, and publish it with the brief.

| Criterion | What you score | Weight |
|---|---|---|
| Technical execution | Code quality, difficulty, how much of the demo is real  | 30% |
| Problem solving | Approach, trade-offs, optimization  | 20% |
| Feasibility and fit | Could it ship, does it fit how the team works  | 20% |
| Testing | Common and corner cases, self-correcting bugs  | 15% |
| Communication | Explains the approach while building  | 10% |
| Originality | Novel idea, creative use of the theme or tools  | 5% |

(score ÷ maximum) × weight, summed across criteria = the total out of 100 

Run that in a spreadsheet, and sanity-check the ranks before anyone makes a call.

## 1-5 Rating Scale Definitions: What a 1, a 3 and a 5 Mean

"Score from 1 to 5" is not a rubric. Vague criteria produce noisy scores however good the criteria are. Write one definition per number, per criterion, before the event. Three anchors hold [a five-point scale](https://testlify.com/hr-glossary/what-is-a-behaviourally-anchored-rating-scale-bars/) steady: failing, acceptable, top.

On problem fit:

- **1**: solves something the brief did not ask for
- **3**: addresses the stated problem with an obvious workaround
- **5**: handles it, including the edge case named in the brief

Two and four sit between the written bands. Attach an example to each anchor, so a 5 means the same thing to every judge. A 0 sits below the 1 band. It means no evidence at all, not poor work.

## Submission Review Focus: What Makes a Project Stand Out, and the Common Score Reducers

Say what a judge may look at: the submission and the stated requirements only, or outside knowledge too? Tight evidence rules cut disagreement between judges. Ask judges to write their reasoning first and the score second. That is more accurate and it leaves a record. Every low score quotes the evidence behind it.

What lifts a submission is the specification the candidate wrote, the architectural call they made, and how well they debugged.

Common score reducers:

- No evidence at all on a criterion, which scores 0 rather than 1 
- A build that ignores a stated constraint, once you have decided whether that fails completeness or instruction adherence 
- Non-disclosure of AI, which employer codes treat as grounds for disqualification or a withdrawn offer [1]

## The Judge Process: Calibrate the Panel Before Anyone Scores

Calibration runs before live judging, and it is separate from writing the rubric. The hackathon judging rubric says what a strong submission looks like. Calibration proves the panel applies it the same way.

Run it as one 90-minute session:

1. Walk the rubric together. Read out each criterion, its weight and the scale, and take questions.
2. Score one or two practice submissions privately. Anonymized past work or a seeded build, no discussion.
3. Put every score on one sheet, revealed only once everyone has finished.
4. Discuss only the outliers. A 2 against a 5 on one criterion gets examined. Leave the rows within a point alone.
5. Rewrite the wording, not the scores. You are hunting the sentence two judges read differently.

Private first, compare second. Otherwise the most senior voice sets the answer before anyone else looks at the evidence. When two judges still disagree, make each justify the rating with something the submission shows [2].

## What Calibration Will Never Fix

Calibration fixes unwritten standards. It does not make the panel neutral.

Judges avoid extreme scores early on, so the first submissions get marked more harshly than identical ones seen later. They also drift toward each other's numbers.

Structure narrows where bias operates. Anchored, structured scoring cuts the Black-White standardized mean difference in ratings from d = 0.56 to about d = 0.23. In a 2012 Yale study, science faculty rated an identical application as more competent when the applicant was labeled male, and offered that person $4,000 more. Trained evaluators were not immune.

So use two independent readers per submission, and a second reader on any borderline result.

## How to Calculate Inter-Rater Reliability

Calibration tells you the panel talked. Agreement tells you the rubric worked. Double-score 10 to 20 percent of submissions, and settle every disagreement.

Use Cohen's kappa when two judges score the same work. Use Krippendorff's alpha (an agreement statistic that handles more than two raters and missing scores) for a larger panel. In recruiting practice, anything below 0.40 reads as inconsistent evaluation, tracked monthly.

Read the split, not just the coefficient. More than one point apart on the same criterion is your trigger to reconvene [2]. If it keeps happening on the same criterion, the rubric is the problem, not the panel [2]. Two defects cause most of it: dimensions that overlap, so "quality" and "completeness" partly mean the same thing, and anchors that give adjectives instead of a concrete threshold.

Never average a split. Resolve it by discussion or a third reviewer, then log the criterion, the decision and the reasoning. That log is what you pull when a placement is challenged.

## Set the AI Rule Before Candidates Set It for You

Everything above assumes the submission is the candidate's own work. With no stated AI rule, your scores compare tool access, not skill. Almost half of job seekers were already using ChatGPT for resumes and cover letters in a 2023 survey [3]. Code, a build plan and a demo script look the same whether a person or a model produced them.

The line that holds is preparation versus substitution. AI may scaffold commodity work, but it may not produce the thing being judged. Publish that with the brief, not after submissions land.

Boilerplate has a test. Delete a block: if a template from the internet could replace it in five minutes, it is boilerplate. If deleting it breaks something only your product does, that is the feature code where the hiring signal lives.

| AI use in a build submission | Policy tier | How judging treats it |
|---|---|---|
| Scaffolding: component setup, database connections, error wrappers, route registration  | Permitted where the brief allows [1] | Scored normally, no penalty  |
| A write-up of past work in the README  | Permitted [1] | Never used against the candidate  |
| Generated design rationale, where reflection is what you assess  | Disclosable [1] | Explained at the live defense |
| Live prompting during a supervised demo or defense  | Prohibited [1] | Disqualifying |
| Feature code or architecture decisions passed off undisclosed [1] | Prohibited [1] | Disqualifying |

## An AI Disclosure Statement Example You Can Copy

A complete disclosure names three things: the tool, the task it did, and the human review that followed. Missing one makes it incomplete rather than absent, and your rubric should score it that way.

Publishing has settled on a sentence that adapts almost word for word: "The author(s) used [NAME OF TOOL / SERVICE] in order to [REASON]. After using this tool/service, the author(s) reviewed and edited the content as needed and take(s) full responsibility".

Put it in a mandatory field next to the code, not in terms-of-service language nobody reads. Two to four sentences is enough, and one consistent structure saves both sides guessing.

Scale the detail to how much AI shaped the graded work. A polishing pass needs one line: no new content was generated, and the author reviewed every edit. Ask for the rest category by category, so a judge scoring architecture can see whether AI touched architecture. A candidate who writes "used AI to help" scores lower than one who itemizes where AI entered the build.

## Spotting Undisclosed AI, and Scoring How Well It Was Used

The check that holds is the live defense conversation, not a detector score. AI produces polished work across a wide range of tasks, so only a conversation verifies the candidate understands what they submitted.

Flag these before that conversation:

- Generic content that never addresses the specific task, plus formatting inconsistencies inside one submission [3]
- Two independent submissions that overlap in wording or structure [3]
- A solution that arrives fully formed, with no commit history and no documented dead ends 
- Line-by-line comments human developers rarely write 

None of these is proof, and [detection tools](https://testlify.com/how-to-prevent-cheating-in-online-interviews/) flag non-native English writers at higher rates [4]. Treat each tell as a question: walk me through why you chose this loop structure.

Then score how well the candidate directed, checked and built on what the model returned. Use separate anchored line items, each needing evidence: prompting shown, output verified and debugged, disclosure specific. Grade them from the disclosure plus any trace they submit, such as a prompt log, git history, or their walkthrough.

One warning. Across 16 studies with more than 27,000 participants, text labeled AI-assisted was rated lower than identical text labeled human-written. Authenticity explained the gap, not quality. So promising that disclosure will not count against a candidate is not enough. Make every AI-use score name its evidence, or you teach candidates to stop telling you.

## Build the Rubric Before You Book the Venue

The event is the easy part. Hackathon judging holds up when the rubric, the calibrated panel and the AI rule all exist before submissions open.

Testlify covers the screening either side of it. Our [3,500+ validated skills assessments](https://testlify.com/) are written by industrial and organizational psychologists, checked for adverse impact, and scored the same way for every candidate. Start with the role your next hackathon is hiring for.

## Frequently asked questions

**How many judges do you need on a hiring hackathon panel?**

Enough for two independent reads of every submission, so three to five judges. A bigger panel adds scheduling cost without adding signal. Bring in a third reader only on borderline results.

**Is a hiring hackathon better than a take-home assignment?**

A hackathon shows how someone works and lets you question them live. A take-home costs candidates less time. Choose the hackathon when collaboration and judgment under pressure are the skills you are hiring for.

**Do you have to pay candidates for a hiring hackathon?**

Pay when the event runs long or the work has commercial value. A few hours of assessment is normally unpaid. A full day deserves a stipend, and never ship a candidate's build without paying.

**Should you share hackathon judging scores with candidates?**

Share the criterion-level feedback, not the leaderboard. The written rationale your judges already recorded becomes usable feedback with no extra work. Keep other candidates' scores private, and say up front what you will share.

## Sources

1. https://careers.fidelityinternational.com/working-here-overview/candidate-code-of-conduct-use-of-artificial-intelligence-ai/
2. https://www.scu.edu/provost/institutional-effectiveness/assessment/doing-assessment/using-rubrics/
3. https://www.klgates.com/Should-Job-Applicants-be-Permitted-to-Use-Artificial-Intelligence-3-27-2024
4. https://lawlibguides.sandiego.edu/c.php?g=1443311&p=10721367
