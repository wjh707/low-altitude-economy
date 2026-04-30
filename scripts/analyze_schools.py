#!/usr/bin/env python3
"""Analyze school major data and compute stats."""
import json
from collections import Counter, defaultdict

with open('data/school_majors.json') as f:
    majors = json.load(f)

# Overall stats
print(f"总记录数: {len(majors)}")

# By level
by_level = Counter(m['level'] for m in majors)
print(f"\n按层次分布:")
for k, v in sorted(by_level.items(), key=lambda x:-x[1]):
    print(f"  {k}: {v}")

# By type
by_type = Counter(m['type'] for m in majors)
print(f"\n按类型分布:")
for k, v in sorted(by_type.items(), key=lambda x:-x[1]):
    print(f"  {k}: {v}")

# By province
by_province = Counter(m['province'] for m in majors)
print(f"\n按省份分布:")
for k, v in sorted(by_province.items(), key=lambda x:-x[1]):
    print(f"  {k}: {v}")

# By city
by_city = Counter(m['city'] for m in majors)
print(f"\n按城市分布:")
for k, v in sorted(by_city.items(), key=lambda x:-x[1]):
    print(f"  {k}: {v}")

# By major
by_major = Counter(m['major'] for m in majors)
print(f"\n按专业分布:")
for k, v in sorted(by_major.items(), key=lambda x:-x[1]):
    print(f"  {k}: {v}")

# By year
by_year = Counter(m['year'] for m in majors)
print(f"\n按年份分布:")
for k, v in sorted(by_year.items(), key=lambda x:-x[1]):
    print(f"  {k}: {v}")

# Stats for dashboard
stats = {
    "total_schools": len(majors),
    "by_level": dict(by_level),
    "by_type": dict(by_type),
    "by_province": dict(sorted(by_province.items(), key=lambda x:-x[1])),
    "by_city": dict(sorted(by_city.items(), key=lambda x:-x[1])),
    "by_major": dict(sorted(by_major.items(), key=lambda x:-x[1])),
    "by_year": dict(sorted(by_year.items())),
    "top_schools": [m['school'] for m in majors if '低空技术与工程' in m['major'] and m['level'] == '本科'],
    "major_list": [m['major'] for m in sorted(majors, key=lambda x: (x['level'], x['school']))]
}

with open('dashboard/school_stats.json', 'w') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print(f"\n\n统计已保存到 dashboard/school_stats.json")
