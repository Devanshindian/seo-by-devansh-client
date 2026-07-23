#!/usr/bin/env python3
"""Classify Testlify blog + page URLs into pillar/cluster taxonomy from slugs.
Structure-based only (no API). Ordered rules: first match wins."""
import re, csv, collections

LANGS = {"ar","pl","it","pt-br","no","da","ja","es","de","sv","nl","fr","el"}

def slug(url):
    s = url.replace("https://testlify.com/","").strip("/")
    return s

def load(fn):
    with open(fn) as f:
        return [l.strip() for l in f if l.strip()]

blog = load("blog-urls.txt")
pages = load("page-urls.txt")

# ---- ordered classification rules on the slug ----
# each rule: (cluster, subcluster_or_None, regex)
RULES = [
    # --- role-based programmatic-style blog clusters ---
    ("Interview Questions (by role)", None, r"interview-question"),
    ("Hiring by Role", None, r"(^|-)how-to-hire-|(^|/)hire-[a-z]|-hiring-guide"),
    ("Screening by Skill/Role", None, r"screen-candidates-for|screen-candidates|screening-|to-screen-"),
    ("Skills Tests & Evaluation (by skill)", None, r"evaluate-.*skill|assess-.*skill|-skills?-(test|assessment)|skills?-of-a"),
    # --- assessment / testing science ---
    ("Assessments & Testing", "Personality & Psychometric", r"personality|disc|psychometric|myers|big-five|enneagram|16-?personalit"),
    ("Assessments & Testing", "Aptitude & Cognitive", r"aptitude|cognitive|numerical|verbal-reasoning|logical|abstract-reasoning|iq-test"),
    ("Assessments & Testing", "Pre-employment / Pre-hire", r"pre-employment|pre-hire|pre-screen"),
    ("Assessments & Testing", "Proctoring & Integrity", r"proctor|cheat|dishonest|fraud|credibility|background-check|reference-check|validity|blind-hiring"),
    ("Assessments & Testing", "Assessment general", r"assessment|-test(s|ing)?(-|$)|talent-test|skill-test|typing-test|coding-test|situational-judg"),
    # --- competitor / comparison ---
    ("Competitor Alternatives & Comparisons", None, r"alternatives?$|-vs-|comparison"),
    # --- recruiting / TA ---
    ("Recruiting & Talent Acquisition", "Sourcing & Candidate Pool", r"sourc|talent-pool|candidate-pool|talent-pipeline|passive-candidate|find-.*(worker|candidate|talent)"),
    ("Recruiting & Talent Acquisition", "Recruitment Process & Strategy", r"recruit|talent-acquisition|applicant|ats|hiring-process|hiring-strateg|selection-process|candidate-experience"),
    ("Recruiting & Talent Acquisition", "Interviewing (process/skills)", r"interview"),
    # --- skills management (the example pillar) ---
    ("Skills Management", None, r"skills?-(management|mapping|gap|matrix|framework|taxonomy|based|inventory|audit|develop|mismatch)|competency|upskill|reskill|skill-gap|soft-skill|transferable-skill|hard-skill|leadership-skill"),
    # --- HR ops / people ops ---
    ("HR Operations & Compliance", "Compensation & Benefits", r"salary|compensation|payroll|benefit|bonus|wage|garden-leave|pto|leave-|paid-time"),
    ("HR Operations & Compliance", "Policies & Compliance", r"policy|compliance|labor-law|eeoc|gdpr|discrimination|harassment|work-schedule|9-80|workweek"),
    ("HR Operations & Compliance", "Workforce & Succession Planning", r"succession|workforce-planning|internal-mobility|job-analysis|organizational-structure|org-structure|job-characteristics|headcount|capacity-planning"),
    ("HR Operations & Compliance", "HR general / HRM", r"(^|/)hr-|human-resource|hrm|people-ops|people-management|hr-tech|hris|hr-toolkit|hr-case"),
    # --- employee lifecycle ---
    ("Employee Experience & Development", "Onboarding", r"onboard"),
    ("Employee Experience & Development", "Engagement & Retention", r"engagement|retention|turnover|attrition|employee-experience|morale|recognition|wellbeing|well-being|burnout|satisfaction"),
    ("Employee Experience & Development", "Performance & L&D", r"performance-(review|management|appraisal)|training|learning-and-development|l-and-d|career-development|mentor|coaching"),
    ("Employee Experience & Development", "Employee general", r"employee|workforce|staff"),
    # --- future of work / workplace culture ---
    ("Workplace, Culture & Future of Work", "Remote & Hybrid", r"remote|work-from-home|hybrid|distributed-team|wfh"),
    ("Workplace, Culture & Future of Work", "DEI", r"diversity|inclusion|dei|equity|belonging|bias"),
    ("Workplace, Culture & Future of Work", "Culture & Trends", r"culture|future-of-work|workplace|trend|great-resignation|quiet-quit|employer-brand"),
    # --- role/career guides ---
    ("Career & Role Guides", None, r"how-to-become|career-path|job-description|what-does-a-.*-do|-career|day-in-the-life"),
    # --- broad fallbacks (catch general hiring/recruiting posts the specific rules missed) ---
    ("Recruiting & Talent Acquisition", "General Hiring", r"hir(e|ing)|bad-hire|offer-letter|job-board|job-application|job-offer|job-posting|onboarding-vs|new-hire|time-to-fill|quality-of-hire"),
    ("Recruiting & Talent Acquisition", "General Talent/Team-building", r"team|leader|manage(r|ment)|talent|workforce|productivity|collaboration"),
]

def classify(s):
    for cluster, sub, rx in RULES:
        if re.search(rx, s):
            return cluster, (sub or "")
    return "Unclustered / Other", ""

# classify blog
rows = []
cluster_ct = collections.Counter()
sub_ct = collections.Counter()
for u in blog:
    s = slug(u)
    c, sub = classify(s)
    cluster_ct[c]+=1
    sub_ct[(c,sub)]+=1
    rows.append((u, s, "blog", c, sub))

# pages: split i18n vs english, classify english
page_en = []
i18n_ct = collections.Counter()
for u in pages:
    s = slug(u)
    first = s.split("/")[0]
    if first in LANGS:
        i18n_ct[first]+=1
        rows.append((u, s, "page-i18n", "i18n Translations", first))
        continue
    if s.startswith("hiring-guides/"):
        rows.append((u, s, "page", "Hiring Guides (page hub)", ""))
        cluster_ct["Hiring Guides (page hub)"]+=1
        continue
    page_en.append(u)
    c, sub = classify(s)
    rows.append((u, s, "page", "PAGE: "+c, sub))

with open("url-clusters.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["url","slug","type","cluster","subcluster"])
    w.writerows(rows)

print("=== BLOG CLUSTERS (of %d) ===" % len(blog))
for c,n in cluster_ct.most_common():
    print(f"{n:5d}  {c}")
print("\n=== BLOG SUBCLUSTERS ===")
for (c,sub),n in sub_ct.most_common():
    if sub: print(f"{n:5d}  {c}  ›  {sub}")
print("\n=== PAGES: english=%d, hiring-guides=88, i18n=%d ===" % (len(page_en), sum(i18n_ct.values())))
print("i18n langs:", dict(i18n_ct))
