import json

with open('dashboard/policy_data.json') as f:
    policies = json.load(f)

for i, p in enumerate(policies):
    url = p.get('url', '')
    if url and url.startswith('http'):
        bad = 'abc123' in url or 'xxxxxx' in url or '/abc' in url.lower() or '60349b1a' in url or 'f5a6b7c' in url
        tag = '⚠️ BAD' if bad else '✅'
        print(f'{i:3d}. {tag} {p["title"][:55]}')
        print(f'     {url}')
