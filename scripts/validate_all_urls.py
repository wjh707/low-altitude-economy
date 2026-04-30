#!/usr/bin/env python3
"""批量验证所有政策URL的可访问性"""
import json
import urllib.request
import urllib.error
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open('dashboard/policy_data.json') as f:
    policies = json.load(f)

results = []
total = 0
good = 0
bad = 0
timeout_errors = 0

for i, p in enumerate(policies):
    url = p.get('url', '')
    if not url or not url.startswith('http'):
        continue
    
    total += 1
    # Skip obviously fake URLs
    if 'xxxxxx' in url or 'abc123' in url:
        results.append((i, p['title'][:60], url, 'FAKE'))
        bad += 1
        continue
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            status = resp.status
            if status == 200:
                results.append((i, p['title'][:60], url, '✅ OK'))
                good += 1
            else:
                results.append((i, p['title'][:60], url, f'❌ {status}'))
                bad += 1
    except urllib.error.HTTPError as e:
        results.append((i, p['title'][:60], url, f'❌ {e.code}'))
        bad += 1
    except urllib.error.URLError as e:
        results.append((i, p['title'][:60], url, f'❌ {e.reason}'))
        bad += 1
    except Exception as e:
        results.append((i, p['title'][:60], url, f'❌ {str(e)[:30]}'))
        bad += 1
    
    if total % 10 == 0:
        print(f'Progress: {total}/{total}...')
    time.sleep(0.5)

print(f'\n\n=== 验证结果 ===')
print(f'总验证: {total}, 可用: {good}, 不可用: {bad}')
print(f'\n--- 可用URL ({good}条) ---')
for i, title, url, status in results:
    if status == '✅ OK':
        print(f'  {title}')
        print(f'    {url}')

print(f'\n--- 不可用URL ({bad}条) ---')
for i, title, url, status in results:
    if status != '✅ OK':
        print(f'  {status} {title}')
        print(f'    {url}')
