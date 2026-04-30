#!/usr/bin/env python3
"""
Batch 3: Search for official government URLs for each policy entry using Baidu search.
"""
import json
import re
import time
import urllib.parse
import requests

DATA_DIR = "/Users/zhoulai/low-altitude-economy/data"
INPUT_FILE = f"{DATA_DIR}/search_batch3.json"
OUTPUT_FILE = f"{DATA_DIR}/search_batch3_result.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def load_input():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_results(results):
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(results)} results to {OUTPUT_FILE}")

def search_baidu(query):
    """Search Baidu and return list of (title, url, source) tuples."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.baidu.com/s?wd={encoded}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = 'utf-8'
        html = resp.text
        
        results = []
        # Find result blocks
        pattern = r'<div[^>]*class="[^"]*result[^"]*"[^>]*>.*?<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
        # Alternative: Find all h3 > a patterns
        blocks = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
        
        for block in blocks:
            a_match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
            if a_match:
                href = a_match.group(1)
                title = re.sub(r'<[^>]+>', '', a_match.group(2)).strip()
                # Get source from the result
                results.append((title, href))
        
        return results
    except Exception as e:
        print(f"  Search error: {e}")
        return []

def extract_source_name(url):
    """Extract source website name from URL."""
    domain_match = re.search(r'https?://([^/]+)', url)
    if not domain_match:
        return ""
    domain = domain_match.group(1)
    
    # Map domains to friendly names
    domain_map = {
        'www.gov.cn': '中华人民共和国中央人民政府',
        'gov.cn': '政府网站',
        'caac.gov.cn': '中国民用航空局',
        'pkulaw.com': '北大法宝',
        'pkulaw.cn': '北大法宝',
        'std.samr.gov.cn': '全国标准信息公共服务平台',
        'moa.gov.cn': '中华人民共和国农业农村部',
        'miit.gov.cn': '工业和信息化部',
        'ndrc.gov.cn': '国家发展和改革委员会',
        'most.gov.cn': '科学技术部',
    }
    
    for key, name in domain_map.items():
        if key in domain:
            return name
    
    # For local government sites
    if domain.endswith('.gov.cn'):
        parts = domain.split('.')
        if len(parts) >= 3:
            city = parts[0]
            return f"{city.upper()}.gov.cn"
        return domain
    
    return domain

def clean_title(title):
    """Clean HTML entities and extra whitespace from title."""
    title = title.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    title = re.sub(r'\s+', ' ', title).strip()
    # Remove bracketed content like [百度百科] [图文]
    title = re.sub(r'[\[【][^\]】]*[\]】]', '', title).strip()
    return title

def get_best_result(query, search_results, region=""):
    """
    Find the best official result from search results.
    Priority: .gov.cn > caac.gov.cn > other authoritative sources
    """
    if not search_results:
        return None, None, None
    
    # Score each result
    scored = []
    for title, url in search_results:
        title_clean = clean_title(title)
        score = 0
        source = extract_source_name(url)
        
        # Check if it's a .gov.cn site
        if '.gov.cn' in url:
            score += 10
        if 'caac.gov.cn' in url:
            score += 10
        if 'pkulaw.com' in url or 'pkulaw.cn' in url:
            score += 8
        if 'std.samr.gov.cn' in url:
            score += 9
        
        # Check if title contains key policy terms from query
        query_keywords = set(query.lower().split())
        title_keywords = set(title_clean.lower().split())
        overlap = query_keywords & title_keywords
        score += len(overlap) * 2
        
        # Bonus for exact or near-exact matches
        if '通知' in title_clean or '意见' in title_clean or '办法' in title_clean or '方案' in title_clean:
            score += 1
        if '低空经济' in title_clean:
            score += 2
        
        scored.append((score, title_clean, url, source))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0]
    
    if best[0] >= 5:
        return best[1], best[2], best[3]
    return None, None, None

def generate_search_keyword(item):
    """Generate the best search keyword from a policy item."""
    title = item['title']
    region = item['region']
    
    # Clean the title - remove trailing dots and garbled text
    clean = re.sub(r'\.{2,}', '', title)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    # Remove suspicious suffixes that look like page numbers
    clean = re.sub(r'\d{4}$', '', clean)
    
    # If the title is obviously truncated, use region + key terms
    if len(clean) < 15 or '...' in title:
        # Extract key terms
        key_terms = re.sub(r'[（(][^)）]*[)）]', '', title)
        key_terms = re.sub(r'\.{2,}', '', key_terms)
        key_terms = re.sub(r'\d{4}\.\d{2}\.\d{2}', '', key_terms)
        terms = [t for t in key_terms.split() if len(t) > 2]
        if terms:
            clean = ' '.join(terms[:5])
    
    if region and region not in clean and region != '全国':
        clean = f"{region} {clean}"
    
    return clean.strip()

def process_item(item):
    """Process a single policy item."""
    title = item['title']
    region = item['region']
    
    # Clean the original title to get a better display title
    display_title = re.sub(r'\s+', ' ', title).strip()
    display_title = re.sub(r'\.{2,}', '', display_title)
    # Remove trailing page number references
    display_title = re.sub(r'\d{4}$', '', display_title)
    
    # Generate search keyword
    keyword = generate_search_keyword(item)
    
    print(f"\n{'='*60}")
    print(f"Searching: {keyword[:100]}")
    
    # Try multiple search queries if needed
    search_results = search_baidu(keyword)
    best_title, best_url, best_source = get_best_result(keyword, search_results, region)
    
    if best_url:
        print(f"  FOUND: {best_title[:80]}")
        print(f"  URL: {best_url[:100]}")
        print(f"  Source: {best_source}")
        return {
            "title": best_title,
            "search_keyword": keyword,
            "url": best_url,
            "status": "found",
            "found_at": best_source
        }
    
    # Try fallback: search with just the region + key terms
    if region and region != '全国':
        fallback_keyword = f"{region} 低空经济 {keyword.split(region)[-1] if region in keyword else keyword}"
        if fallback_keyword != keyword:
            print(f"  Fallback: {fallback_keyword[:100]}")
            time.sleep(1)
            search_results2 = search_baidu(fallback_keyword)
            best_title2, best_url2, best_source2 = get_best_result(fallback_keyword, search_results2, region)
            if best_url2:
                print(f"  FOUND (fallback): {best_title2[:80]}")
                return {
                    "title": best_title2,
                    "search_keyword": fallback_keyword,
                    "url": best_url2,
                    "status": "found",
                    "found_at": best_source2
                }
    
    print(f"  NOT FOUND")
    return {
        "title": display_title,
        "search_keyword": keyword,
        "url": "",
        "status": "not_found",
        "found_at": ""
    }

def main():
    print("Loading input data...")
    items = load_input()
    print(f"Loaded {len(items)} items")
    
    results = []
    for i, item in enumerate(items):
        print(f"\n[{i+1}/{len(items)}]", end="")
        result = process_item(item)
        results.append(result)
        
        # Save intermediate results every 10 items
        if (i + 1) % 10 == 0:
            save_results(results)
            print(f"  [Checkpoint saved at item {i+1}]")
        
        # Be polite to Baidu - delay between requests
        if i < len(items) - 1:
            delay = 2 + random.random() * 1
            time.sleep(delay)
    
    save_results(results)
    
    # Summary
    found = sum(1 for r in results if r['status'] == 'found')
    not_found = sum(1 for r in results if r['status'] == 'not_found')
    print(f"\n{'='*60}")
    print(f"SUMMARY: {found} found, {not_found} not found out of {len(results)} total")

if __name__ == '__main__':
    import random
    main()
