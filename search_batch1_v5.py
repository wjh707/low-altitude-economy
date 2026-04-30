#!/opt/anaconda3/bin/python3.12
"""
Comprehensive search: broad Bing searches + intelligent filtering for authoritative sources.
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

AUTHORITY_DOMAINS = [
    'gov.cn', 'caac.gov.cn', 'pkulaw.com', 'std.samr.gov.cn',
    'npc.gov.cn', 'ndrc.gov.cn', 'miit.gov.cn', 'mot.gov.cn',
    'mof.gov.cn', 'most.gov.cn', 'mofcom.gov.cn',
]

def bing_search(query):
    """Search Bing and return parsed results."""
    url = f"https://www.bing.com/search?q={quote(query)}&setlang=zh-Hans&cc=cn&count=15"
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
            cite = item.xpath('.//cite')
            snippet = item.xpath('.//p')
            if link:
                title = link[0].text_content().strip()
                href = link[0].get('href', '')
                cite_text = cite[0].text_content().strip() if cite else ''
                snippet_text = snippet[0].text_content().strip() if snippet else ''
                if href:
                    results.append({
                        'title': title, 'href': href,
                        'cite': cite_text, 'snippet': snippet_text
                    })
        return results
    except Exception as e:
        return []

def is_authoritative(url, title='', cite='', snippet=''):
    """Check if result is from authoritative source."""
    combined = (url + ' ' + title + ' ' + cite + ' ' + snippet).lower()
    for d in AUTHORITY_DOMAINS:
        if d in combined:
            return True
    return False

def get_source_name(url, title='', snippet=''):
    """Get human-readable source name."""
    combined = url.lower()
    if 'caac.gov.cn' in combined:
        return "中国民用航空局"
    elif 'www.gov.cn' in combined:
        return "中华人民共和国中央人民政府"
    elif 'pkulaw.com' in combined:
        return "北大法宝"
    elif 'std.samr.gov.cn' in combined:
        return "全国标准信息公共服务平台"
    elif 'gov.cn' in combined:
        return f"政府网站"
    elif 'npc.gov.cn' in combined:
        return "全国人大"
    elif 'ndrc.gov.cn' in combined:
        return "国家发展改革委"
    elif 'miit.gov.cn' in combined:
        return "工业和信息化部"
    elif 'mot.gov.cn' in combined:
        return "交通运输部"
    else:
        return title[:50] if title else url[:50]

def clean(raw_title):
    """Extract clean title from raw item."""
    t = raw_title.split('....')[0].strip()
    t = re.sub(r'\.{3,}.*$', '', t)
    return t.strip()

def extract_core_name(title):
    """Extract the core regulation/policy name for better search."""
    # Remove date annotations in parentheses
    t = re.sub(r'[（(]\d{4}[.\d]*[）)]', '', title)
    t = re.sub(r'[（(]征求意见稿[）)]', '', t)
    t = re.sub(r'[（(]暂行[）)]', '', t)
    t = re.sub(r'[（(]试行[）)]', '', t)
    t = re.sub(r'[（(]\d+[\s]*修正[）)]', '', t)
    t = re.sub(r'[（(]修订[）)]', '', t)
    t = t.strip()
    # Remove common lead-ins
    t = re.sub(r'^(关于印发《|关于发布《|关于修订《|关于印发《)', '', t)
    t = re.sub(r'》的通知$|》$', '', t)
    t = t.strip()
    return t

def search_single(title, region):
    """Search for a single policy using multiple strategies."""
    clean_title = clean(title)
    core_name = extract_core_name(title)
    
    # Strategy pool - try each until we find a result
    strategies = []
    
    # Strategy 1: Full title with "民航局" for aviation stuff
    if any(kw in clean_title for kw in ['空域', '通用航空', '无人机', '无人驾驶', '民航', '机场', '飞行']):
        strategies.append(f"{core_name} 民航局")
        if len(clean_title) > 20:
            strategies.append(f"{core_name} 民航局")
            strategies.append(core_name)
    
    # Strategy 2: Full title
    strategies.append(clean_title)
    
    # Strategy 3: Core name (no dates)
    if core_name and core_name != clean_title:
        strategies.append(core_name)
    
    # Strategy 4: For State Council docs
    if '国务院' in clean_title or '中央军委' in clean_title or '中共中央' in clean_title:
        strategies.append(clean_title)
        strategies.append(core_name if core_name else clean_title)
    
    # Strategy 5: For local regulations
    if region and region != "全国":
        strategies.append(f"{clean_title} {region}")
        if core_name:
            strategies.append(f"{core_name} {region}")
    
    # Strategy 6: Just the first 50 chars
    if len(clean_title) > 50:
        strategies.append(clean_title[:50])
    
    # Deduplicate
    seen = set()
    unique_strategies = []
    for s in strategies:
        s_normalized = s.strip()
        if s_normalized and s_normalized not in seen:
            seen.add(s_normalized)
            unique_strategies.append(s_normalized)
    
    # Try each strategy
    best_result = None
    
    for query in unique_strategies:
        results = bing_search(query)
        if not results:
            continue
        
        # First, look for authoritative results
        for r in results:
            if is_authoritative(r['href'], r['title'], r['cite'], r['snippet']):
                # Verify the result is actually relevant (title or snippet contains keywords)
                combined_text = (r['title'] + ' ' + r['snippet']).lower()
                keywords = extract_keywords(clean_title)
                relevance_score = sum(1 for kw in keywords if kw in combined_text)
                if relevance_score >= 1:
                    best_result = r
                    break
        
        if best_result:
            break
    
    # If no authoritative result, try without site filter but mark as not found
    # (We only want to return authoritative results)
    return best_result

def extract_keywords(title):
    """Extract important keywords from title for relevance checking."""
    # Remove common words and extract meaningful terms
    stop_words = ['关于', '印发', '通知', '的', '和', '与', '等', '及', '或者', '暂行', '试行',
                  '管理', '规定', '办法', '规则', '意见', '方案', '规划', '纲要', '决定',
                  '修订', '实施', '发布', '印发']
    words = re.findall(r'[\w\u4e00-\u9fff]+', title)
    keywords = [w for w in words if len(w) >= 2 and w not in stop_words]
    return keywords[:8]

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    print(f"Loaded {len(items)} items to search")
    all_results = []
    
    for idx, item in enumerate(items):
        raw_title = item["title"]
        region = item.get("region", "")
        clean_title = clean(raw_title)
        
        print(f"\n[{idx+1}/{len(items)}] {clean_title[:70]}...")
        
        best = search_single(raw_title, region)
        
        if best:
            url = best['href']
            src = get_source_name(url, best['title'], best['snippet'])
            print(f"  ✓ {url[:90]}")
            print(f"    ↳ {src}")
            all_results.append({
                "title": clean_title,
                "search_keyword": clean_title,
                "url": url,
                "status": "found",
                "found_at": src
            })
        else:
            print(f"  ✗ NOT FOUND")
            all_results.append({
                "title": clean_title,
                "search_keyword": clean_title,
                "url": "",
                "status": "not_found",
                "found_at": ""
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
