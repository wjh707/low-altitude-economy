#!/usr/bin/env python3
"""Generate stats for real talent data and update dashboard."""
import json
from collections import Counter, defaultdict
from datetime import datetime

with open('data/real_talent_data.json') as f:
    jobs = json.load(f)

# Stats
by_category = Counter(j['category'] for j in jobs)
by_company = Counter(j['company'] for j in jobs)
by_city = Counter(j['city'] for j in jobs)
by_month = Counter(j['publish_date'][:7] for j in jobs if j['publish_date'])

# Average salary by position
salary_by_pos = defaultdict(list)
for j in jobs:
    avg = (j['salary_min'] + j['salary_max']) / 2
    salary_by_pos[j['position']].append(avg)
avg_salary_by_position = {k: round(sum(v)/len(v), 1) for k, v in sorted(salary_by_pos.items(), key=lambda x: -sum(x[1])/len(x[1]))}

stats = {
    "total_jobs": len(jobs),
    "by_category": dict(by_category),
    "by_company": dict(by_company.most_common(25)),
    "by_city": dict(by_city.most_common(15)),
    "by_month": dict(sorted(by_month.items())),
    "avg_salary_by_position": avg_salary_by_position
}

with open('dashboard/talent_stats.json', 'w') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

# Also copy talent data to dashboard
with open('data/real_talent_data.json') as f:
    data = json.load(f)
with open('dashboard/talent_data.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Stats generated:")
print(json.dumps(stats, ensure_ascii=False, indent=2))
