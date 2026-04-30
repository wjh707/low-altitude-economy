import json

with open('dashboard/policy_data.json') as f:
    policies = json.load(f)

for p in policies:
    d = p.get('date', '')
    if d and d[:4] in ('2025', '2026'):
        print(f"{d} | {p['title'][:80]}")
