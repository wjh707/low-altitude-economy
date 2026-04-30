#!/opt/anaconda3/bin/python3.12
"""
Search batch1 policies using Bing search and find official source URLs.
Focus on .gov.cn, caac.gov.cn, pkulaw.com and other authoritative sources.
"""
import json
import re
import time
import requests

INPUT_FILE = "/Users/zhoulai/low-altitude-economy/data/search_batch1.json"
OUTPUT_FILE = "/Users/zhoulai/low-altitude-economy/data/search_batch1_result.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def search_bing(query, max_retries=3):
    """Search Bing for the given query."""
    url = f"https://www.bing.com/search?q={requests.utils.quote(query)}&setlang=zh-Hans&cc=cn"
    
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                # Parse results
                results = []
                # Find all result links
                # Bing results are in <h2><a href="...">
                pattern = r'<h2><a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a></h2>'
                matches = re.findall(pattern, r.text, re.DOTALL)
                for href, title_html in matches[:10]:
                    # Clean title
                    title_clean = re.sub(r'<[^>]+>', '', title_html).strip()
                    results.append({'title': title_clean, 'href': href})
                
                if results:
                    return results
                
                # Try alternate pattern
                pattern2 = r'<cite[^>]*>(.*?)</cite>'
                hrefs = re.findall(r'<a[^>]*href="(https?://(?:www\.)?bing\.com[^"]*)"', r.text)
                if not results and not hrefs:
                    # Maybe we got a captcha or block
                    if 'captcha' in r.text.lower() or 'verify' in r.text.lower():
                        time.sleep(5)
                        continue
            return results
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return []

def is_authoritative_url(url):
    """Check if a URL is from an authoritative source."""
    url_lower = url.lower()
    if any(domain in url_lower for domain in [
        'gov.cn', 'caac.gov.cn', 'pkulaw.com', 'std.samr.gov.cn',
        'mof.gov.cn', 'miit.gov.cn', 'mot.gov.cn', 'ndrc.gov.cn',
        'cnsa.gov.cn', 'mfa.gov.cn', 'moe.gov.cn', 'mohrss.gov.cn',
        'mofcom.gov.cn', 'miit.gov.cn', 'most.gov.cn', 'npc.gov.cn',
        'cma.gov.cn', 'sport.gov.cn', 'culture.gov.cn',
    ]):
        return True
    return False

def extract_source_name(url):
    """Extract a human-readable source name from URL."""
    url_lower = url.lower()
    
    if 'caac.gov.cn' in url_lower:
        return "中国民用航空局"
    elif 'www.gov.cn' in url_lower:
        return "中华人民共和国中央人民政府"
    elif 'gov.cn' in url_lower:
        return "政府网站"
    elif 'pkulaw.com' in url_lower:
        return "北大法宝"
    elif 'std.samr.gov.cn' in url_lower:
        return "全国标准信息公共服务平台"
    elif 'mof.gov.cn' in url_lower:
        return "财政部"
    elif 'miit.gov.cn' in url_lower:
        return "工业和信息化部"
    elif 'mot.gov.cn' in url_lower:
        return "交通运输部"
    elif 'ndrc.gov.cn' in url_lower:
        return "国家发展改革委"
    elif 'npc.gov.cn' in url_lower:
        return "全国人大"
    else:
        return url[:50]

def clean_title(title):
    """Clean title by removing trailing dots, page numbers, etc."""
    t = re.sub(r'[.。\s]+$', '', title)
    t = re.sub(r'\.{2,}\s*\d+$', '', t)
    # Remove trailing sub_category artifacts
    t = re.sub(r'\.{2,}.*$', '', t)
    return t.strip()

def search_policy(keyword):
    """Search for a policy and return the best official URL."""
    results = search_bing(keyword)
    
    if not results:
        return None, None
    
    # First pass: look for authoritative sources (gov.cn, caac.gov.cn)
    for r in results:
        url = r.get('href', '')
        if is_authoritative_url(url):
            return url, extract_source_name(url)
    
    # Second pass: return first meaningful result
    for r in results:
        url = r.get('href', '')
        if 'baike.baidu.com' in url:
            continue  # Skip Baidu Baike, not official
        return url, r.get('title', '')[:40]
    
    return None, None

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    print(f"Loaded {len(items)} items to search")
    
    all_results = []
    
    for idx, item in enumerate(items):
        # Build keyword
        title = item["title"]
        region = item.get("region", "")
        
        # Clean title for search
        search_title = clean_title(title)
        
        # For items with page number artifacts, extract clean title
        # The title might have page numbers appended
        if '....' in title:
            search_title = title.split('....')[0].strip()
        
        # Remove any trailing page number
        search_title = re.sub(r'\s*\d+\s*$', '', search_title)
        
        # Build keyword
        if region and region != "全国":
            keyword = f"{search_title} {region}"
        else:
            keyword = search_title
        
        print(f"\n[{idx+1}/{len(items)}] Searching: {keyword[:80]}...")
        
        url, found_at = search_policy(keyword)
        
        if url:
            print(f"  FOUND: {url} [{found_at}]")
        else:
            print(f"  NOT FOUND - trying broader search...")
            # Try shorter version for better results
            short_kw = search_title[:60]
            url, found_at = search_policy(short_kw)
            if url:
                print(f"  FOUND (retry): {url} [{found_at}]")
            else:
                print(f"  STILL NOT FOUND")
        
        result = {
            "title": clean_title(title),
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
    print(f"\n\nDone! Found: {found_count}/{len(all_results)}. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
