# AI Recruitment Tools That Can Survive a Bias Audit

You ask a vendor for the bias audit behind their AI recruitment tools, and back comes a link to a responsible-AI page. It has a diagram on it. It has no auditor's name and no numbers. That means it is not the thing a regulator will ask you for.

That gap is yours to carry, not the vendor's. If the tool selects one group at half the rate of another, the complaint lands on your company. Pointing at the software has never worked as a defence. So the only sensible way to rank these tools is by what an outside auditor has tested and published. Judged that way, four of the five best-known tools leave a blank where the numbers should be.

## Quick answer

Judge a recruiting tool on published audit evidence, not on a fairness claim, because you are the one who answers for the outcome. The evidence you want names an independent auditor, says what method they used, and reports selection rates by sex, by race, and both combined. Then one figure does the deciding. A group that gets picked at under 80% of the top group's rate is a problem worth investigating. On that test, only Eightfold AI publishes something a compliance reviewer could read end to end. HireVue gates its audits. Workday publishes none. Testlify's page carries no impact ratios.

## The Four Kinds of AI Hiring Tools, and Which Ones Actually Decide

Vendors sell one product, but four different things sit inside it. Parsing lifts data off a resume and drops it into fields. That is tidying, not judging. Screening applies criteria and decides who moves forward. Assessments measure skills, and their scores feed the screening step. [Conversational AI](https://testlify.com/how-conversational-ai-reshapes-entry-level-hiring/) runs a chat or SMS exchange to collect things like availability.

Only some of those make a call about a person. That is what an audit has to follow. Your vendor bundles all four under one contract, one login, and one responsible-AI page, but they are separate systems with separate training data and separate thresholds. An audit opinion covering the assessment engine tells you nothing about the screening rule sitting on top of it. Ask which component was tested before you accept anything as evidence.

The screening layer is where the first failure shows up, and it has nothing to do with a protected class. These tools rank people on how closely their words match the job description. So a candidate with the skill but not the vocabulary is filtered out before a recruiter opens the file. Your strongest support lead writes "de-escalation" where your posting says "conflict resolution". She never reaches the shortlist. Nobody on the hiring panel ever learns she applied.

## The Four-Fifths Rule Every Bias Audit Turns On

The whole thing runs on one number you can work out on a napkin. Take the group your tool selects most often as the benchmark, then divide every other group's selection rate by it. Anything under 0.80 counts as evidence of [adverse impact](https://testlify.com/hr-glossary/disparate-impact/). That is the four-fifths rule. Say your screen passes 10% of white applicants and 5% of Black applicants. The ratio is 0.50, and you have something to investigate before someone else finds it for you.

Nobody has to prove you meant it. That is the part buyers underestimate, and it is why "we bought this off the shelf" is not a defence. The EEOC holds employers liable for discriminatory outcomes produced by a third party's AI hiring product. The vendor keeps the licence fee. You keep the claim.

Treat the number as a smoke alarm rather than a verdict. It ignores how big the pool was, and it misfires in both directions. A 1.5% rate against a 2% rate breaks the rule on half a percentage point, while 76% against 95% clears it on a nineteen-point gap [1]. So a failing ratio tells you to go and look at the workflow. It is not proof the tool is broken. A passing ratio proves even less, because it says nothing about whether the scores predict how anyone performs in the job.

The wider question of whether an assessment is fair in the first place, and what to examine beyond a ratio, is covered in our guide to [bias-free employment assessments](https://testlify.com/ensure-bias-free-employment-assessments/).

## The Five Tools at a Glance, and How to Read the Blanks

Here is the whole ranking in one view, before the reasoning behind it. Read the dashes carefully. A dash means the public record holds nothing on that yardstick. It does not mean the tool cleared it.

| Tool | What it scores | Published bias audit | Impact ratios public? | Known legal exposure |
|---|---|---|---|---|
| 1. [Eightfold](https://eightfold.ai/trust/bias-audit-results/) AI | Candidate matching and ranking | Yes, by BABL AI, with a named auditor and a stated method | Yes, within the audit's scope | - |
| 2. Pymetrics | Behavioral game performance | Source-code audit by academic researchers | Partial, through the auditors' own account | Score reuse across employers, undisclosed |
| 3. Testlify | Skills assessment and matching | Third-party audit of the matching model, June 2023 | No | - |
| 4. HireVue | Video responses, including facial action | Two audits, neither published in full | No | FTC complaint; accessibility complaint |
| 5. Workday | Applicant screening and ranking | None published | No | Mobley v. Workday, age collective certified |

The pattern across those rows is transparency, not fairness. Most of these vendors are not failing an impact-ratio test in public. They are declining to run one where anyone can see the result, a different problem that leaves you holding the risk.

## 1. Eightfold AI: The BABL AI Audit You Can Read End to End

Eightfold is the only tool here that hands you paperwork instead of a promise. An independent third party, BABL AI, completed a bias audit of the Eightfold Matching Model, and a named lead auditor signed and dated it [2]. A compliance reviewer can open that document, see who did the work, see what was tested, and check the date against a renewal calendar. Nothing else on this list clears that bar.

Copy one detail from the engagement into your own vendor questionnaire. BABL's fees are fixed. They do not depend on the opinion the auditor reaches [2]. An auditor who earns more for a clean result is not independent in any sense a regulator would recognise. You can settle that question in a single email before you sign anything.

Eightfold also states its limits rather than burying them, which is the strongest signal in the whole document. The audit does not certify the model as bias free. No audit can. It covers the matching model, not everything else in the suite. Buy this when your exposure is regulatory and you need published evidence to hand over. Do not assume the opinion stretches to whatever else you switch on next quarter.

## 2. Pymetrics: The One Vendor That Let Auditors Read the Code

Where every other vendor here published a summary, Pymetrics gave outside academic auditors access to its source code. That is a different class of evidence. A summary tells you what the vendor says the model does. Reading the code tells you what it actually does. The researchers could confirm the four-fifths logic was built the way the company described it.

Then they found something the marketing never mentioned. The platform reused an applicant's scores for up to 330 days, and that reuse crossed employer boundaries. So a candidate rejected by one company in January could carry the same score into an unrelated company's funnel in November, without being told. The second employer never learns the score is secondhand.

Take that away as a question, not a verdict on Pymetrics. Ask every vendor on your shortlist whether scores are reused across clients, and for how long. A transparent one answers in a sentence. A vendor who needs a week to come back to you has already told you something useful.

## 3. Testlify: A Transparency Page, Without the Impact Ratios

We publish a Local Law 144 transparency page, and a completed third-party bias audit of our matching model dated June 16, 2023. That puts us ahead of the vendors offering nothing at all. It also puts us short of the standard this article sets. You should be aiming higher.

Here is what we are missing. A full disclosure reports selection rates and impact ratios by sex, by race and ethnicity, and by the two crossed. Such as female Hispanic, or male Asian. Those tables are not in our public record, so a reviewer cannot check our numbers the way they can check Eightfold's. Monitoring an algorithm for bias is a design commitment rather than a measurement, and we will not present it as one.

Use us where a reviewer wants a named third-party audit of a matching model with a validated assessment library underneath it. Do not use us when that reviewer asks to see ratios by group. Nobody else on this list publishes those either. That is the honest state of the market, not an excuse for it.

## 4. HireVue: Two Audits, Neither One You Can Read

HireVue films candidates and scores what it sees and hears. The company's own chief industrial-organizational psychologist told the Washington Post that facial actions alone can account for 29% of that score [3]. Nearly a third of a hiring signal rests on a candidate's face, the part of the measurement with the thinnest published validity evidence and the clearest disability exposure.

Two audits do exist. Getting at them is the problem. The public could see summaries only after handing over personal information and agreeing not to reproduce any part of them. An audit your legal team cannot quote in a memo is not usable evidence, whatever it happened to conclude.

If HireVue is already in your stack, narrow what it scores. Turn off the visual and vocal inferences. Keep only what the candidate actually said. Treat the output as one input into a decision a named recruiter signs. Used that way it is defensible. Used as the shortlist itself, it is the hardest tool here to explain to anyone.

## 5. Workday AI Lawsuit: No Published Audit, One Live Federal Case

Workday has published no bias-audit results, no Local Law 144 summary, and no four-fifths outcomes for its [AI hiring features](https://testlify.com/hr-glossary/algorithmic-accountability/). What exists instead is litigation. It is a poor substitute for evidence, and a much louder one.

Derek Mobley is a Black man over 40 with a disability. He applied to more than 100 jobs through employers running Workday's screening platform, and he says every one of them rejected him. He never claimed Workday was his employer. He argued the software acts as an agent of the companies using it. The court agreed that the complaint adequately alleged the platform takes part in the decision by recommending some candidates and rejecting others. The neutral-tool position did not survive that ruling.

Scale is what should change your procurement conversation. Workday told the court that roughly 1.1 billion applications were rejected through its system during the relevant period. Run these screening features today and you cannot show a regulator an audit. The case makes that absence conspicuous. Run the four-fifths math on your own funnel, keep your rejection logs, and stop waiting for a document the vendor has not produced in three years.

## What NYC Local Law 144 Requires of You, Not Your Vendor

The law does not ban AI in hiring. It makes using a covered tool conditional on three things. An independent bias audit, conducted within the year before you use it. A public summary of the results. Notice to the candidate. All three duties sit with the employer, and none of them moves to the company that sold you the software.

The trigger is the candidate's address, not your head office. If someone living in the five boroughs is evaluated by your tool, you are in scope from Denver or Dublin. The summary has to sit somewhere a candidate can actually find it, which in practice means the careers page rather than a legal subfolder nobody links to. The notice has to reach them at least 10 business days before the evaluation. It must tell them how to ask for an alternative process or an accommodation.

The arithmetic of ignoring this is unpleasant. Penalties stack per violation and per day. One tool left unaudited for a month runs to roughly $15,000 to $45,000 for that month alone, before any notice failures are counted on top. Enforcement was thin in the law's first two years. Planning around that is a bet that the city stays understaffed.

## How to Choose an AI Recruiting Tool You Can Defend

Bias has moved into procurement, ahead of the demo. Warden AI surveyed more than 100 vendors and practitioners. In that survey, 75% of HR leaders named bias a top concern when evaluating AI hiring tools, second only to data privacy. That only helps if the concern has a document attached to it. A demo shows you a polished candidate flow and a clean score, and tells you nothing about how the score was produced.

Ask for five things in writing. Name the artifact that answers each one:

- **The audit summary itself:** not a link to a fairness page. A document carrying an auditor's name, a date, and the method they used.
- **The impact ratios by group:** selection rates by sex, by race and ethnicity, and by the two crossed. Aggregate numbers hide the cut that fails.
- **The scoring inputs:** what goes into the score, which weights and thresholds you can tune, and a human-readable reason attached to each ranking.
- **The ATS integration and notice tooling:** whether it writes back to your applicant tracking system, and whether it gives you what you need to send the candidate notice and prove you sent it.
- **The contract language:** only 17% of AI vendor contracts commit to complying with all applicable laws, against 36% of ordinary software agreements [4].

Then pilot the tool on one role. Write the pass/fail criteria down before it starts. A vendor who can answer all five inside a week is selling you a system. One who cannot is selling you a claim.

## Testing Skills You Can Show an Auditor

Most vendors sell a fairness claim. It costs far less than an audit record. We hold part of that record and not all of it. We have a completed third-party audit of our matching model, and we have a transparency page. We have not published impact ratios. We are not going to call our tests bias free. What we can put in front of a reviewer is our [3,500+ validated skills assessments](https://testlify.com/), built by I/O psychologists. Start a free trial, run one role through it, and export every question, rubric, and outcome your next audit cycle will ask you for.

## Frequently asked questions

**Which AI tool is best for recruitment?**

On the published evidence, Eightfold AI. It is the only one of the five that names an independent auditor and states the method behind its matching model [2]. Which tool fits your own roles is a separate question.

**How to use AI tools for recruitment?**

Use them to rank and sequence candidates, never to auto-reject. Keep hard requirements as plain rules you could defend out loud, and have a person sign off on every advance and rejection. Log the model version behind each ranking.

**Does the EU AI Act apply to AI recruitment tools?**

Yes. Recruitment and candidate screening both count as high risk. That high-risk classification brings duties on risk management, on data governance, on human oversight and on record keeping. You also have to tell candidates an AI system is evaluating them.

**How long does a bias audit take to complete?**

Plan for four to eight weeks. Most of that is data work. You pull selection outcomes by role, match demographic fields, and explain the gaps. The auditor's own analysis is usually the fastest part of it.

## Sources

1. https://rules.cityofnewyork.us/rule/automated-employment-decision-tools-2/
2. https://eightfold.ai/trust/bias-audit-results/
3. https://www.brookings.edu/articles/for-some-employment-algorithms-disability-discrimination-by-default/
4. https://law.stanford.edu/2025/03/21/navigating-ai-vendor-contracts-and-the-future-of-law-a-guide-for-legal-tech-innovators/
