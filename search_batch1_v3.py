#!/opt/anaconda3/bin/python3.12
"""
Search batch1 policies using Bing search and find official source URLs.
Focus on .gov.cn, caac.gov.cn, pkulaw.com and other authoritative sources.
Uses lxml for robust HTML parsing.
"""
import json
import re
import time
import requests
from lxml import html

INPUT_FILE = "/Users/zhoulai/low-altitude-economy/data/search_batch1.json"
OUTPUT_FILE = "/Users/zhoulai/low-altitude-economy/data/search_batch1_result.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def search_bing(query):
    """Search Bing for the given query and return parsed results."""
    url = f"https://www.bing.com/search?q={requests.utils.quote(query)}&setlang=zh-Hans&cc=cn"
    
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.encoding = 'utf-8'
            
            if r.status_code != 200:
                time.sleep(2)
                continue
            
            tree = html.fromstring(r.text)
            results = []
            
            # Parse result items
            result_items = tree.xpath('//ol[@id="b_results"]//li[@class="b_algo"]')
            
            for item in result_items:
                link = item.xpath('.//h2/a')
                if not link:
                    continue
                title = link[0].text_content().strip()
                href = link[0].get('href', '')
                if href:
                    results.append({'title': title, 'href': href})
            
            if results:
                return results
            
            # Try alternate pattern
            result_items2 = tree.xpath('//li[@class="b_algo"]')
            for item in result_items2:
                link = item.xpath('.//a[contains(@href, "http")]')
                if link:
                    title = link[0].text_content().strip()
                    href = link[0].get('href', '')
                    if href and title:
                        results.append({'title': title, 'href': href})
            
            if results:
                return results
            
            time.sleep(2)
            
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
    
    return []

def is_authoritative_url(url):
    """Check if a URL is from an authoritative source."""
    url_lower = url.lower()
    authoritative_domains = [
        'gov.cn', 'caac.gov.cn', 'pkulaw.com', 'std.samr.gov.cn',
        'npc.gov.cn', 'ndrc.gov.cn', 'miit.gov.cn', 'mot.gov.cn',
        'mof.gov.cn', 'most.gov.cn', 'mofcom.gov.cn', 'cnsa.gov.cn',
    ]
    return any(d in url_lower for d in authoritative_domains)

def extract_source_name(url):
    """Extract a human-readable source name from URL."""
    url_lower = url.lower()
    if 'caac.gov.cn' in url_lower:
        return "中国民用航空局"
    elif 'www.gov.cn' in url_lower:
        return "中华人民共和国中央人民政府"
    elif 'gov.cn' in url_lower:
        return f"政府网站 ({url.split('/')[2]})"
    elif 'pkulaw.com' in url_lower:
        return "北大法宝"
    elif 'std.samr.gov.cn' in url_lower:
        return "全国标准信息公共服务平台"
    elif 'npc.gov.cn' in url_lower:
        return "全国人大"
    elif 'ndrc.gov.cn' in url_lower:
        return "国家发展改革委"
    elif 'miit.gov.cn' in url_lower:
        return "工业和信息化部"
    elif 'mot.gov.cn' in url_lower:
        return "交通运输部"
    else:
        return url[:50]

def clean_title_and_build_keyword(item):
    """Clean the raw title and build an effective search keyword."""
    title = item["title"]
    region = item.get("region", "")
    category = item.get("category", "")
    
    # Extract the part before page numbers (....)
    clean = title.split('....')[0].strip()
    
    # Remove trailing page number references
    clean = re.sub(r'[\s]*\d+[\s]*$', '', clean)
    
    # Build keyword - use the clean title
    # For better results on Bing, keep the year numbers
    if region and region != "全国":
        return clean, f"{clean} {region}"
    return clean, clean

def search_with_retry(item):
    """Search for a policy, trying multiple strategies."""
    clean_title, keyword = clean_title_and_build_keyword(item)
    
    # Strategy 1: Search with keywords and authoritative site filter
    results = search_bing(keyword)
    
    if results:
        # Check for authoritative sources
        for r in results:
            url = r.get('href', '')
            if is_authoritative_url(url):
                return url, extract_source_name(url), clean_title
    
    # Strategy 2: Try without date/parenthetical info
    simpler = re.sub(r'[（(][^）)]*[）)]', '', clean_title).strip()
    simpler = re.sub(r'\s+', ' ', simpler)
    if simpler != clean_title and len(simpler) > 10:
        if item.get("region", "") and item["region"] != "全国":
            kw2 = f"{simpler} {item['region']}"
        else:
            kw2 = simpler
        
        if kw2 != keyword:
            results2 = search_bing(kw2)
            if results2:
                for r in results2:
                    url = r.get('href', '')
                    if is_authoritative_url(url):
                        return url, extract_source_name(url), clean_title
    
    # Strategy 3: Just take the first meaningful result if it's not spam
    if results:
        non_spam = [r for r in results if 'baike.baidu.com' not in r.get('href', '')]
        if non_spam:
            first = non_spam[0]
            return first['href'], first['title'][:40], clean_title
    
    return None, None, clean_title

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    print(f"Loaded {len(items)} items to search")
    
    all_results = []
    
    for idx, item in enumerate(items):
        clean_title, keyword = clean_title_and_build_keyword(item)
        
        print(f"\n[{idx+1}/{len(items)}] Searching: {keyword[:80]}...")
        
        url, found_at, final_title = search_with_retry(item)
        
        if url:
            print(f"  ✓ FOUND: {url}")
            print(f"    Source: {found_at}")
        else:
            print(f"  ✗ NOT FOUND")
        
        result = {
            "title": final_title,
            "search_keyword": keyword,
            "url": url or "",
            "status": "found" if url else "not_found",
            "found_at": found_at or ""
        }
        
        all_results.append(result)
        
        # Rate limiting
        time.sleep(1.5)
    
    # Write output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    found_count = sum(1 for r in all_results if r["status"] == "found")
    print(f"\n{'='*60}")
    print(f"Done! Found: {found_count}/{len(all_results)} ({100*found_count//len(all_results)}%)")
    print(f"Output saved to: {OUTPUT_FILE}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
