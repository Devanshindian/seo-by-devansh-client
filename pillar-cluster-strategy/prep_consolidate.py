#!/usr/bin/env python3
"""Group the 402 fine pillars into ~9 domain jobs for a consolidation pass,
and pool all orphans into one rescue job."""
import json, os, collections

fine = json.load(open("data/fine-clusters.json"))

# slice -> consolidation job
JOB = {}
for s in ["w01","w02","w03"]: JOB[s]="j1_interview_by_role"
for s in ["w04","w05","w06","w24","w25","w29","w30"]: JOB[s]="j2_assessments_tests_types"
for s in ["w14","w15","w19"]: JOB[s]="j3_skills_tests_screening"
for s in ["w07","w08","w09","w12","w20","w22","w27"]: JOB[s]="j4_recruiting_process"
for s in ["w16","w17","w13"]: JOB[s]="j5_hiring"
for s in ["w21","w26","w33","w38"]: JOB[s]="j6_employee_experience"
for s in ["w23","w28","w31","w32","w34","w35","w36","w37"]: JOB[s]="j7_workplace_hr_skillsmgmt"
for s in ["w18"]: JOB[s]="j8_alternatives"
for s in ["w10","w11","w39"]: JOB[s]="j9_misc"

jobs = collections.defaultdict(list)
for p in fine["pillars"]:
    # a merged pillar can span slices; assign by its first slice
    job = JOB.get(p["slices"][0], "j9_misc")
    jobs[job].append({"pillar": p["pillar"], "intent": p["intent"], "spokes": p["spokes"]})

os.makedirs("data/consolidate", exist_ok=True)
for f in os.listdir("data/consolidate"):
    os.remove(os.path.join("data/consolidate", f))

for job, pills in sorted(jobs.items()):
    json.dump({"job": job, "pillars": pills},
              open(f"data/consolidate/{job}.json", "w"), indent=2)
    n_sp = sum(len(p["spokes"]) for p in pills)
    print(f"{job}: {len(pills)} pillars, {n_sp} spokes")

json.dump({"orphans": fine["orphans"]},
          open("data/consolidate/j0_orphans.json", "w"), indent=2)
print(f"j0_orphans: {len(fine['orphans'])} orphans to rescue")
