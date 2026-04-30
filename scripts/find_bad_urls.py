import json

with open('dashboard/policy_data.json') as f:
    policies = json.load(f)

for i, p in enumerate(policies):
    url = p.get('url','')
    if not url or not url.startswith('http'):
        continue
    if '60349b1a' in url or ('xxxxxx' in url):
        print(f'  [{i}] {p["title"][:55]}')
        print(f'       {url}')
