#!/usr/bin/env python3
"""
Batch 3: Search for official government policy URLs.
Uses smarter short queries and resolves Baidu redirect URLs.
"""
import json
import re
import time
import random
import urllib.parse
import requests

DATA_DIR = "/Users/zhoulai/low-altitude-economy/data"
OUTPUT_FILE = f"{DATA_DIR}/search_batch3_result.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def clean_title_from_input(raw):
    """Clean up the messy input title."""
    t = raw
    # Remove garbage dots and page numbers
    t = re.sub(r'\.{2,}', '', t)
    t = re.sub(r'\d{4}$', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def search_baidu(query):
    """Search Baidu and return raw HTML."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.baidu.com/s?wd={encoded}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f"  Search error: {e}")
        return ""

def extract_baidu_results(html):
    """Extract search results from Baidu HTML, getting real URLs."""
    results = []
    
    # Baidu stores results in a specific div structure
    # Find all result blocks
    # Pattern 1: Standard results with h3 > a
    blocks = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
    for block in blocks:
        a_match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
        if a_match:
            href = a_match.group(1)
            title = re.sub(r'<[^>]+>', '', a_match.group(2)).strip()
            title = re.sub(r'\s+', ' ', title)
            title = title.replace('&nbsp;', ' ').replace('&amp;', '&')
            if href and not href.startswith('#'):
                results.append((title, href))
    
    # Pattern 2: result item containers
    if not results:
        items = re.findall(r'<div[^>]*class="[^"]*result[^"]*c-container[^"]*"[^>]*id="(\d+)"', html)
        for item_id in items:
            item_html = re.search(rf'<div[^>]*id="{item_id}"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
            if item_html:
                content = item_html.group(1)
                a_match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', content, re.DOTALL)
                if a_match:
                    href = a_match.group(1)
                    title = re.sub(r'<[^>]+>', '', a_match.group(2)).strip()
                    if href and not href.startswith('#'):
                        results.append((title, href))
    
    return results

def resolve_baidu_url(baidu_url):
    """Follow Baidu redirect to get the real URL."""
    try:
        resp = requests.get(baidu_url, headers=HEADERS, timeout=10, allow_redirects=True)
        if resp.url:
            return resp.url
        return baidu_url
    except:
        return baidu_url

def extract_source_name(url):
    domain_match = re.search(r'https?://([^/]+)', url)
    if not domain_match:
        return ""
    domain = domain_match.group(1)
    
    domain_map = {
        'www.gov.cn': '中华人民共和国中央人民政府',
        'caac.gov.cn': '中国民用航空局',
        'pkulaw.com': '北大法宝',
        'pkulaw.cn': '北大法宝',
        'pkulaw.com/law': '北大法宝',
        'std.samr.gov.cn': '全国标准信息公共服务平台',
        'flk.npc.gov.cn': '国家法律法规数据库',
    }
    
    for key, name in domain_map.items():
        if key in domain:
            return name
    
    if domain.endswith('.gov.cn'):
        return domain
    if 'baike.baidu.com' in domain:
        return '百度百科'
    if 'wenku.baidu.com' in domain:
        return '百度文库'
    if 'doc88' in domain or 'docin' in domain or 'mbalib' in domain:
        return domain
    
    return domain

def find_official_url(query, region, title_raw):
    """
    Search with a short, focused query and look for government URLs.
    """
    # First, try the original title as a phrase search
    search_queries = []
    
    # Short, focused query for government site
    # Extract key identifying information
    clean = re.sub(r'\.{2,}', ' ', title_raw)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    # Try to extract the core policy name
    # Pattern: "XXX关于印发《YYY》的通知" -> extract YYY
    m = re.search(r'关于印发[《（]([^》）]+)[》）]', clean)
    if m:
        core = m.group(1)
        if region and region != '全国':
            search_queries.append(f"{region} {core}")
        search_queries.append(core)
    
    # Try with just region + key terms
    if region and region != '全国':
        keywords = re.findall(r'[\u4e00-\u9fff]{4,}', clean)
        city_words = [k for k in keywords if region[:2] in k or len(k) >= 4][:5]
        if city_words:
            search_queries.append(f"{region} {' '.join(city_words[:3])}")
    
    # Try the full title without garbage
    clean2 = clean
    clean2 = re.sub(r'（\d{4}\.\d{2}\.\d{2}）', '', clean2)
    clean2 = re.sub(r'\(\d{4}\.\d{2}\.\d{2}\)', '', clean2)
    clean2 = re.sub(r'\d{4}年\)', '', clean2)
    clean2 = re.sub(r'知[^）)]*', '', clean2)
    clean2 = re.sub(r'\s+', ' ', clean2).strip()
    if len(clean2) > 8:
        # Take first 50 chars max
        search_queries.append(clean2[:60])
    
    # Final fallback: just region + "低空经济"
    if region and region != '全国':
        search_queries.append(f"{region} 低空经济")
    
    # Deduplicate
    seen = set()
    unique_queries = []
    for q in search_queries:
        if q not in seen and len(q) > 4:
            seen.add(q)
            unique_queries.append(q)
    
    # Try each query
    found_urls = set()
    for query_text in unique_queries[:5]:  # max 5 attempts
        print(f"  Trying: \"{query_text[:60]}\"")
        html = search_baidu(query_text)
        if not html:
            continue
        
        results = extract_baidu_results(html)
        if not results:
            print(f"    No results extracted")
            continue
        
        print(f"    Got {len(results)} results")
        
        for title, search_url in results:
            # Check for official Chinese government domains
            official_domains = ['.gov.cn', 'caac.gov.cn', 'pkulaw.com', 'pkulaw.cn', 
                                'std.samr.gov.cn', 'flk.npc.gov.cn']
            is_official = any(d in search_url for d in official_domains)
            
            if is_official:
                real_url = resolve_baidu_url(search_url)
                source = extract_source_name(real_url)
                print(f"    OFFICIAL: {title[:60]} -> {real_url[:80]}")
                print(f"    Source: {source}")
                return (title, real_url, source)
            
            # Also check for known authoritative titles
            title_lower = title.lower()
            if any(kw in title_lower for kw in ['人民政府', '政府办公厅', '政府办公室', 
                                                  '民航局', '交通运输厅', '发改委',
                                                  '工业和信息化厅', '科学技术厅']):
                if '百度文库' not in search_url and '百度百科' not in search_url:
                    real_url = resolve_baidu_url(search_url)
                    source = extract_source_name(real_url)
                    print(f"    GOV-LIKE: {title[:60]} -> {real_url[:80]}")
                    return (title, real_url, source)
        
        # If no official result, remember the best result URL for potential follow-up
        for title, search_url in results[:3]:
            if 'baidu.com/link' in search_url:
                continue
            if 'baike.baidu.com' in search_url or 'wenku.baidu.com' in search_url:
                continue
            found_urls.add((title, search_url))
        
        time.sleep(1 + random.random())
    
    # If nothing official found, try resolving the best non-Baidu URL
    for title, search_url in found_urls:
        if 'baidu.com' not in search_url:
            real_url = resolve_baidu_url(search_url)
            source = extract_source_name(real_url)
            if '.gov.cn' in real_url or 'caac.gov.cn' in real_url:
                print(f"    RESOLVED OFFICIAL: {title[:60]} -> {real_url[:80]}")
                return (title, real_url, source)
    
    return (None, None, None)

def process_all(items):
    """Process all items and return results."""
    results = []
    
    for i, item in enumerate(items):
        title_raw = item['title']
        region = item['region']
        
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(items)}] Region: {region}")
        print(f"  Raw: {title_raw[:80]}")
        
        # Generate search keyword
        keyword = re.sub(r'\.{2,}', ' ', title_raw)
        keyword = re.sub(r'\s+', ' ', keyword).strip()
        keyword = keyword[:80]
        
        # Search
        found_title, found_url, found_source = find_official_url(keyword, region, title_raw)
        
        if found_url:
            display_title = clean_title_from_input(title_raw)
            result = {
                "title": found_title or display_title,
                "search_keyword": keyword,
                "url": found_url,
                "status": "found",
                "found_at": found_source
            }
            print(f"  ✓ FOUND: {found_url[:80]}")
        else:
            display_title = clean_title_from_input(title_raw)
            result = {
                "title": display_title,
                "search_keyword": keyword,
                "url": "",
                "status": "not_found",
                "found_at": ""
            }
            print(f"  ✗ NOT FOUND")
        
        results.append(result)
        
        # Save checkpoint every 5 items
        if (i + 1) % 5 == 0 or i == len(items) - 1:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"  [Checkpoint: {i+1}/{len(items)} saved]")
        
        # Delay between searches
        if i < len(items) - 1:
            time.sleep(2 + random.random() * 1.5)
    
    return results

def main():
    with open(f"{DATA_DIR}/search_batch3.json", 'r', encoding='utf-8') as f:
        items = json.load(f)
    print(f"Loaded {len(items)} items")
    
    results = process_all(items)
    
    # Summary
    found = sum(1 for r in results if r['status'] == 'found')
    not_found = sum(1 for r in results if r['status'] == 'not_found')
    print(f"\n{'='*60}")
    print(f"SUMMARY: {found} found, {not_found} not found out of {len(results)} total")
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
