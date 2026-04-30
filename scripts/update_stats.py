#!/usr/bin/env python3
"""Regenerate stats.json from updated policy data."""
import json
from datetime import datetime

with open('dashboard/policy_data.json') as f:
    policies = json.load(f)

# Compute stats
dates = [p.get('date', '') for p in policies if p.get('date', '')]
valid_dates = [d for d in dates if len(d) >= 10 and d[:4].isdigit()]
latest_date = max(valid_dates) if valid_dates else ''
earliest_date = min(valid_dates) if valid_dates else ''

by_level = {}
by_region = {}
by_category = {}
by_month = {}

for p in policies:
    lv = p.get('level', '其他')
    by_level[lv] = by_level.get(lv, 0) + 1
    
    rg = p.get('region', '其他')
    by_region[rg] = by_region.get(rg, 0) + 1
    
    cat = p.get('category', '其他')
    by_category[cat] = by_category.get(cat, 0) + 1
    
    d = p.get('date', '')
    if d and len(d) >= 7:
        month_key = d[:7]
        by_month[month_key] = by_month.get(month_key, 0) + 1

# Keywords (simple freq from titles)
all_words = ' '.join([p.get('title', '') for p in policies])
keywords = ['低空经济', '无人机', '无人驾驶航空器', '通用航空', 'eVTOL', '空域管理', '产业促进',
            '基础设施', '安全监管', '人才', '适航', '飞行服务', '深圳', '广东', '安徽', '湖南', '四川',
            '立法', '补贴', '标准', '财政', '税收', '创新', '数据']
word_counts = {}
for kw in keywords:
    count = all_words.count(kw)
    if count > 0:
        word_counts[kw] = count

sorted_kws = sorted(word_counts.items(), key=lambda x: -x[1])[:20]
hot_keywords = [{'keyword': k, 'count': v} for k, v in sorted_kws]

stats = {
    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'total_policies': len(policies),
    'time_span': {
        'start': earliest_date[:10],
        'end': latest_date[:10]
    },
    'by_level': by_level,
    'by_region': by_region,
    'by_category': by_category,
    'by_month': dict(sorted(by_month.items())),
    'hot_keywords': hot_keywords
}

with open('dashboard/stats.json', 'w') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print(f"Stats updated: {len(policies)} policies, {len(by_level)} levels, {len(by_region)} regions")
print(f"Time span: {earliest_date[:10]} ~ {latest_date[:10]}")
print(f"Categories: {by_category}")
