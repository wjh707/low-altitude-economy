#!/usr/bin/env python3
"""Search for recent low-altitude economy policies from various keyword combinations."""
import urllib.request
import urllib.parse
import json
import re
import time
import ssl
import sys

# Disable SSL verification for simplicity
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def bing_search(query, count=10):
    """Search Bing for policies"""
    encoded = urllib.parse.quote(query)
    url = f"https://www.bing.com/search?q={encoded}&count={count}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml'
    })
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        # Extract result links
        links = re.findall(r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', html)
        results = []
        for href, title in links:
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            if clean_title and '低空' in clean_title:
                results.append({'title': clean_title, 'url': href})
        return results[:10]
    except Exception as e:
        return [{'title': f'Error: {e}', 'url': ''}]

def baidu_search_html(query):
    """Search Baidu and return raw HTML for manual analysis"""
    encoded = urllib.parse.quote(query)
    url = f"https://www.baidu.com/s?wd={encoded}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml'
    })
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        # Extract policy links from gov.cn
        links = re.findall(r'<a[^>]*href="(https?://[^"]*gov\.cn[^"]*)"[^>]*>(.*?)</a>', html)
        results = []
        seen = set()
        for href, title in links:
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            if clean_title and len(clean_title) > 8 and clean_title not in seen:
                seen.add(clean_title)
                results.append({'title': clean_title, 'url': href})
        return results[:15]
    except Exception as e:
        return [{'title': f'Error: {e}', 'url': ''}]

keywords = [
    "低空经济 政策 2025 site:gov.cn",
    "低空经济 政策 2024 site:gov.cn",
    "低空经济 管理办法 site:gov.cn",
    "低空经济 促进条例 site:gov.cn",
    "低空经济 行动方案 2025 site:gov.cn",
    "低空经济 产业发展 site:gov.cn",
    "低空经济 空域管理 site:gov.cn",
    "低空经济 基础设施 site:gov.cn",
    "低空经济 无人机管理 site:gov.cn",
    "低空经济 适航管理 site:gov.cn",
    "低空经济 资金补贴 site:gov.cn",
    "低空经济 人才政策 site:gov.cn",
]

all_found = {}
for kw in keywords:
    print(f"\n=== Searching: {kw} ===")
    results = baidu_search_html(kw)
    for r in results:
        if r['url'] and 'gov.cn' in r['url'].lower():
            key = r['title'][:50]
            if key not in all_found:
                all_found[key] = r
                print(f"  [{len(all_found)}] {r['title'][:70]}")
                print(f"       {r['url']}")
    time.sleep(2)

print(f"\n\nTotal unique policy links found: {len(all_found)}")
print(json.dumps(list(all_found.values()), ensure_ascii=False, indent=2))
