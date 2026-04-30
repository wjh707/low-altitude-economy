#!/opt/anaconda3/bin/python3.12
"""
Improved search: Use targeted site: queries on Bing to find official policy URLs.
"""
import json
import re
import time
import requests
from lxml import html
from urllib.parse import quote

INPUT_FILE = "/Users/zhoulai/low-altitude-economy/data/search_batch1.json"
OUTPUT_FILE = "/Users/zhoulai/low-altitude-economy/data/search_batch1_result.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def bing_search_site(query, site=None):
    """Search Bing with optional site: filter."""
    if site:
        q = f"{query} site:{site}"
    else:
        q = query
    url = f"https://www.bing.com/search?q={quote(q)}&setlang=zh-Hans&cc=cn&count=10"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = 'utf-8'
        if r.status_code != 200:
            return []
        tree = html.fromstring(r.text)
        results = []
        items = tree.xpath('//ol[@id="b_results"]//li[@class="b_algo"]')
        for item in items:
            link = item.xpath('.//h2/a')
            if link:
                title = link[0].text_content().strip()
                href = link[0].get('href', '')
                if href:
                    results.append({'title': title, 'href': href})
        return results
    except Exception:
        return []

def extract_clean_title(raw_title):
    """Extract clean title from the raw item title."""
    t = raw_title.split('....')[0].strip()
    t = re.sub(r'\.{3,}.*$', '', t)
    t = t.strip()
    return t

def get_authoritative_url(title, region):
    """Multi-strategy search for authoritative URL."""
    
    clean = extract_clean_title(title)
    
    # Strategy A: For aviation-specific regulations, search caac.gov.cn directly
    if any(kw in clean for kw in ['通用航空', '空域', '民航', '无人机', '无人驾驶航空', '机场', '飞行']):
        # Generate 2-3 variants of shortened search terms
        variants = [clean]
        
        # Remove parenthetical dates for broader matching
        no_date = re.sub(r'[（(]\d{4}[^）)]*[）)]', '', clean).strip()
        if no_date != clean:
            variants.append(no_date)
        
        # Very short variant - just the core regulation name
        core = clean.split('（')[0].split('(')[0].strip()
        # Remove common prefixes
        core = re.sub(r'^(关于|关于印发|关于修订|关于发布|关于印发《)', '', core)
        core = re.sub(r'》的通知$', '', core)
        core = re.sub(r'》$', '', core)
        core = re.sub(r'^《', '', core)
        if len(core) > 8 and core != clean:
            variants.append(core)
        
        # Try caac.gov.cn with each variant
        for v in variants:
            results = bing_search_site(v, 'caac.gov.cn')
            for r in results:
                url = r['href']
                if 'caac.gov.cn' in url.lower():
                    return url, "中国民用航空局", clean
        
        # Try gov.cn
        for v in variants:
            results = bing_search_site(f"{v} 民航局", 'gov.cn')
            for r in results:
                url = r['href']
                if 'gov.cn' in url.lower() and not any(s in url.lower() for s in ['zhihu', 'baidu', 'bbs.']):
                    return url, "中华人民共和国中央人民政府", clean
    
    # Strategy B: For State Council documents, search gov.cn
    if any(kw in clean for kw in ['国务院', '中央军委', '中共中央', '国家']):
        variants = [clean]
        no_date = re.sub(r'[（(]\d{4}[^）)]*[）)]', '', clean).strip()
        if no_date != clean:
            variants.append(no_date)
        
        for v in variants:
            results = bing_search_site(v, 'gov.cn')
            for r in results:
                url = r['href']
                if 'gov.cn' in url.lower() and not any(s in url.lower() for s in ['zhihu', 'baidu', 'bbs.']):
                    return url, "中华人民共和国中央人民政府", clean
    
    # Strategy C: For local regulations, search with region
    if region and region != "全国":
        variants = [f"{clean} {region}"]
        no_date = re.sub(r'[（(]\d{4}[^）)]*[）)]', '', clean).strip()
        if no_date != clean:
            variants.append(f"{no_date} {region}")
        
        for v in variants:
            # Try region's gov.cn
            results = bing_search_site(v, 'gov.cn')
            for r in results:
                url = r['href']
                if 'gov.cn' in url.lower() and not any(s in url.lower() for s in ['zhihu', 'baidu', 'bbs.']):
                    return url, f"政府网站", clean
    
    # Strategy D: Broad search with quotes for exact match
    for v in [clean, re.sub(r'[（(][^）)]*[）)]', '', clean).strip()]:
        results = bing_search_site(f'"{v}"' if len(v) > 15 else v)
        for r in results:
            url = r['href']
            if 'gov.cn' in url.lower() or 'caac.gov.cn' in url.lower() or 'pkulaw.com' in url.lower() or 'std.samr.gov.cn' in url.lower():
                return url, url.split('/')[2] if url else "", clean
    
    # Strategy E: Last resort - try broader search
    results = bing_search_site(clean[:60])
    for r in results:
        url = r['href']
        if 'gov.cn' in url.lower() or 'caac.gov.cn' in url.lower():
            return url, url.split('/')[2] if url else "", clean
    
    return None, None, clean

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    print(f"Loaded {len(items)} items to search")
    all_results = []
    
    for idx, item in enumerate(items):
        raw_title = item["title"]
        region = item.get("region", "")
        
        print(f"\n[{idx+1}/{len(items)}] {extract_clean_title(raw_title)[:70]}...")
        
        url, found_at, final_title = get_authoritative_url(raw_title, region)
        
        if url:
            print(f"  ✓ {url[:90]}")
            print(f"    ↳ {found_at}")
        else:
            print(f"  ✗ NOT FOUND")
        
        all_results.append({
            "title": final_title,
            "search_keyword": extract_clean_title(raw_title),
            "url": url or "",
            "status": "found" if url else "not_found",
            "found_at": found_at or ""
        })
        
        time.sleep(1.5)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    found = sum(1 for r in all_results if r["status"] == "found")
    print(f"\n{'='*60}")
    print(f"Done! Found: {found}/{len(all_results)} ({100*found//len(all_results)}%)")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
