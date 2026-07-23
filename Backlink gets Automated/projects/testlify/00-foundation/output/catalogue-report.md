# Catalogue report — testlify

- Generated: 2026-07-19
- Domain: testlify.com · market: United States/en
- Confidence: PARTIAL (CMS count headers verified for every type that answered, but 3 type(s) never did — kadence_form, kadence_header, kadence_navigation. Their size is unknowable from the CMS, so total coverage is incomplete by an unknown amount; see 'Coverage UNKNOWN' below)
- Rows: 9968 · overall body coverage: 100.0%

## Gates

- all gates PASS
- warn: gate2: 27 documents without a closing </html> (warn only — some servers truncate their own responses)

### Withheld by the CMS — 136 record(s) counted but not served

Every request for these types answered HTTP 200; the CMS simply served fewer records than its own count header claims. That is a permissions boundary, not a failure: these are private, draft or otherwise protected records an anonymous client may not read. They are counted here so the difference can never be mistaken for pages we lost.

- `wp_block`: served 0 of 136 (136 withheld)

### Coverage UNKNOWN — 3 content type(s) whose endpoint is broken

Every request to these types errored, so the CMS never served a count for them and their true size is **unknowable from this source**. They are NOT assumed empty. Any of their pages that the sitemap, archive or traffic layers found are still catalogued via those sources; pages only this endpoint knew about cannot be counted, so this run's CMS-side coverage is incomplete by an unknown amount.

- `kadence_form` (kadence_form): 6 items failed individually (HTTP 500) — the endpoint is failing, not its records
- `kadence_header` (kadence_header): 6 items failed individually (HTTP 500) — the endpoint is failing, not its records
- `kadence_navigation` (kadence_navigation): 6 items failed individually (HTTP 500) — the endpoint is failing, not its records

### Known gaps — 1 item(s) the CMS itself cannot render

The CMS answers HTTP 5xx for these items (a fatal error rendering that record), so they cannot be enumerated by any client. Located by bisection and listed here rather than lost; coverage below EXCLUDES them.

- `kadence_element`: item position(s) [148]

## Coverage per type

| Type | Rows | ok | stub | flagged | failed | Coverage | Baseline non-empty | Baseline rows |
|---|---|---|---|---|---|---|---|---|
| test-library | 3621 | 3594 | 0 | 27 | 0 | 100.0% | 3386 | 3620 |
| post | 2920 | 2920 | 0 | 0 | 0 | 100.0% | — | — |
| page | 992 | 921 | 11 | 59 | 1 | 99.9% | — | — |
| hr-glossary | 859 | 859 | 0 | 0 | 0 | 100.0% | 858 | 858 |
| job-description | 645 | 645 | 0 | 0 | 0 | 100.0% | 645 | 645 |
| techglossary | 398 | 398 | 0 | 0 | 0 | 100.0% | 397 | 397 |
| interviews | 161 | 161 | 0 | 0 | 0 | 100.0% | 138 | 161 |
| competitors | 122 | 121 | 0 | 1 | 0 | 100.0% | 27 | 142 |
| integrations | 114 | 114 | 0 | 0 | 0 | 100.0% | 113 | 113 |
| successstory | 36 | 36 | 0 | 0 | 0 | 100.0% | 12 | 19 |
| author | 18 | 11 | 0 | 7 | 0 | 100.0% | — | — |
| our-partner | 17 | 14 | 0 | 3 | 0 | 100.0% | 0 | 16 |
| pages | 16 | 15 | 0 | 1 | 0 | 100.0% | 1093 | 1109 |
| job-openings | 12 | 12 | 0 | 0 | 0 | 100.0% | 12 | 12 |
| simple-pay | 9 | 9 | 0 | 0 | 0 | 100.0% | — | — |
| podcast | 8 | 8 | 0 | 0 | 0 | 100.0% | 7 | 7 |
| certifications | 6 | 6 | 0 | 0 | 0 | 100.0% | 0 | 5 |
| ebooks | 6 | 6 | 0 | 0 | 0 | 100.0% | 5 | 5 |
| skill-mapping | 5 | 5 | 0 | 0 | 0 | 100.0% | 4 | 4 |
| press-release | 2 | 2 | 0 | 0 | 0 | 100.0% | 1 | 1 |
| wp_navigation | 1 | 1 | 0 | 0 | 0 | 100.0% | — | — |

Baseline: `_baseline-2026-07-18` — total 10085 rows. The rebuild must match or beat every number; regressions are failures, not footnotes.

## Provenance (the set differences are findings)

- union 10358 -> final 9968 pages
- wp 10268 · sitemap 9660 · archive 734 · crawl 0
- wp-only 611 (the CMS lists these; the sitemap does not) · sitemap-only 42 · archive-only 47
- dropped: dead 4 · soft-404 0 · collapsed aliases 386 · offsite 0 · robots 0
- fan-in flags (NOT collapsed, inspect these): 0

## Traffic

- 2254 ranked pages (market United States/en) · join fills the catalogue's Traffic/Intent with the CLEANED figure
- vendor total_count 18937 vs 18028 rows actually served (the tail is etv~0; shortfall is the vendor's, recorded here)
- pull cost $2.67

## Provable gaps (79 ranking pages the catalogue lacks)

- https://help.testlify.com/article/378-difference-between-tests-and-assessments
- https://testlify.com/test-library/disc-testlify-personality-assessment/
- https://testlify.com/category/talent-assessment/
- https://app.testlify.com/login
- https://testlify.com/test-library/c/
- https://testlify.com/test-library/culture-fit/
- https://help.testlify.com/article/330-copy-paste-tracking-in-assessments
- https://help.testlify.com/category/620-test-libraries
- https://help.testlify.com/article/364-utilizing-the-question-palette-option-in-your-assessments
- https://help.testlify.com/article/595-overview-of-the-system-requirement-check-feature-in-testlify
- https://help.testlify.com/article/389-ip-address-whitelisting
- https://testlify.com/testlify-vs-testgenius-detailed-comparison/
- https://help.testlify.com/article/367-how-to-view-questions-and-answers-to-the-tests-a-step-by-step-guide
- https://app.testlify.com/register
- https://cdn.testlify.com/technicalManual/pdf/62fe3438aade49c1b84b927b.pdf
- https://testlify.com/test-library/hr-specialist-test/
- https://help.testlify.com/article/498-how-to-test-your-microphone-and-camera-before-starting-your-assessment
- https://testlify.com/top-employment-assessment-tools/
- https://testlify.com/traitify-alternatives/
- https://roadmap.testlify.com/p/rtl-right-to-left-language-support-KGjLDG
- https://help.testlify.com/article/304-how-to-contact-your-test-administrator-for-assistance-during-an-assessment
- https://help.testlify.com/article/545-how-to-join-an-assessment-using-an-access-code
- https://help.testlify.com/article/249-how-to-cancel-your-testlify-subscription
- https://testlify.com/vendor-management-coordinator-interview-questions-to-ask-job-applicants/
- https://app.testlify.com/assessments
- https://help.testlify.com/article/267-qualifying-questions-for-assessments
- https://testlify.com/testlify-vs-talogy-detailed-comparison/
- https://testlify.com/brillium-alternatives/
- https://testlify.com/how-to-choose-the-right-organizational-development-intervention/
- https://testlify.com/wp-content/uploads/2024/09/DISC-Personality-Sample-Report.pdf
- https://help.testlify.com/article/237-smtp-setup-using-microsoft-outlook
- https://testlify.com/testlify-vs-adaface-detailed-comparison/
- https://help.testlify.com/article/360-how-to-invite-candidates-to-your-assessments
- https://help.testlify.com/article/247-api-rate-limiting-documentation
- https://help.testlify.com/article/272-how-to-grant-screen-share-access-for-your-test
- https://testlify.com/wp-content/uploads/2024/12/Recruitment-report-template.pdf
- https://testlify.com/best-cappfinity-alternative/
- https://testlify.com/benefits-coordinator-interview-questions-to-ask-job-applicants/
- https://testlify.com/testlify-vs-testello-detailed-comparison/
- https://help.testlify.com/article/547-additional-assessment-attempts-to-individual-candidates
- https://testlify.com/test-library/u-s-bookkeeping-proficiency-test/
- https://testlify.com/thomas-international-alternatives/
- https://trust.testlify.com/
- https://help.testlify.com/article/323-types-of-personality-culture-tests-on-testlify
- https://help.testlify.com/article/393-scoring-for-coding-questions-at-test-case-level
- https://help.testlify.com/article/401-how-to-configure-saml-authentication-with-azure-active-directory-on-testlify
- https://help.testlify.com/article/416-camera-and-microphone-permissions-troubleshooting
- https://roadmap.testlify.com/p/new-question-type-linear-scale-WRfKEK
- https://help.testlify.com/article/387-how-to-create-and-add-a-public-link
- https://testlify.com/successfinder-alternatives/
- … and 29 more
