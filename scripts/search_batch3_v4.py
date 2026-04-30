#!/usr/bin/env python3
"""
Batch 3 v4: Search government websites directly for policy documents.
For each policy, we construct a smart search query and check multiple data sources.
"""
import json
import re
import time
import random
import urllib.parse
import requests
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = "/Users/zhoulai/low-altitude-economy/data"
OUTPUT_FILE = f"{DATA_DIR}/search_batch3_result.json"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

# Government site search URLs
GOV_SEARCH = {
    '江苏省': 'https://www.jiangsu.gov.cn',
    '浙江省': 'https://www.zj.gov.cn',
    '湖南省': 'https://www.hunan.gov.cn',
    '海南省': 'https://www.hainan.gov.cn',
    '四川省': 'https://www.sc.gov.cn',
    '山西省': 'https://www.shanxi.gov.cn',
    '新疆': 'https://www.xinjiang.gov.cn',
}

def load_input():
    with open(f"{DATA_DIR}/search_batch3.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_city_url(region):
    """Get the government website URL for a city."""
    city_sites = {
        '徐州市': 'https://www.xz.gov.cn',
        '苏州市': 'https://www.suzhou.gov.cn',
        '无锡市': 'https://www.wuxi.gov.cn',
        '扬州市': 'https://www.yangzhou.gov.cn',
        '杭州市': 'https://www.hangzhou.gov.cn',
        '嘉兴市': 'https://www.jiaxing.gov.cn',
        '海宁市': 'https://www.haining.gov.cn',
        '金华市': 'https://www.jinhua.gov.cn',
        '舟山市': 'https://www.zhoushan.gov.cn',
        '绍兴市': 'https://www.sx.gov.cn',
        '长沙市': 'https://www.changsha.gov.cn',
        '合肥市': 'https://www.hefei.gov.cn',
        '芜湖市': 'https://www.wuhu.gov.cn',
        '福州市': 'https://www.fuzhou.gov.cn',
        '厦门市': 'https://www.xiamen.gov.cn',
        '成都市': 'https://www.chengdu.gov.cn',
        '自贡市': 'https://www.zg.gov.cn',
        '南充市': 'https://www.nanchong.gov.cn',
        '吉安市': 'https://www.jian.gov.cn',
        '九江市': 'https://www.jiujiang.gov.cn',
        '沈阳市': 'https://www.shenyang.gov.cn',
    }
    for city, url in city_sites.items():
        if city in region or city in "":
            return url
    return None

def search_gov_site(base_url, keyword, max_pages=3):
    """Search a government website for a policy document."""
    results = []
    try:
        # Most gov sites use a common search interface
        search_urls = [
            f"{base_url}/search?q={urllib.parse.quote(keyword)}",
            f"{base_url}/so/search?q={urllib.parse.quote(keyword)}",
            f"{base_url}/site/search.html?q={urllib.parse.quote(keyword)}",
        ]
        for search_url in search_urls:
            try:
                r = requests.get(search_url, headers=HEADERS, timeout=8, verify=False)
                if r.status_code == 200:
                    html = r.text
                    # Extract links
                    links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
                    for link_url, link_text in links:
                        text = re.sub(r'<[^>]+>', '', link_text).strip()
                        if '低空' in text or keyword[:4] in text:
                            full_url = link_url if link_url.startswith('http') else base_url + link_url if link_url.startswith('/') else link_url
                            if '.gov.cn' in full_url:
                                results.append((text, full_url))
                    if results:
                        break
            except:
                continue
    except:
        pass
    return results

def search_provincial_policy(region, keywords):
    """Search a provincial government site for policies."""
    base_url = GOV_SEARCH.get(region)
    if not base_url:
        return []
    
    results = []
    # Try common policy listing pages
    policy_urls = [
        f"{base_url}/zwgk/zcjd/",
        f"{base_url}/zwgk/zcwj/",
        f"{base_url}/zfxxgk/",
    ]
    
    for policy_url in policy_urls:
        try:
            r = requests.get(policy_url, headers=HEADERS, timeout=8, verify=False)
            if r.status_code == 200:
                html = r.text
                links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
                for link_url, link_text in links:
                    text = re.sub(r'<[^>]+>', '', link_text).strip()
                    if any(kw in text for kw in keywords):
                        full_url = link_url if link_url.startswith('http') else base_url + link_url
                        results.append((text, full_url))
        except:
            continue
    
    return results

def search_baidu_site(domain, query):
    """Use Baidu site: operator to search a specific domain."""
    try:
        search_q = f"site:{domain} {query}"
        encoded = urllib.parse.quote(search_q)
        url = f"https://www.baidu.com/s?wd={encoded}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = 'utf-8'
        html = r.text
        
        results = []
        # Try to find result links  
        blocks = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
        for block in blocks:
            a_match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
            if a_match:
                href = a_match.group(1)
                title = re.sub(r'<[^>]+>', '', a_match.group(2)).strip()
                if domain in href:
                    results.append((title, href))
        return results
    except:
        return []

def normalize_title(raw):
    """Clean up the raw title from the input."""
    t = re.sub(r'\.{2,}', '', raw)
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'\d{4}$', '', t)
    return t

def extract_region_city(raw, region):
    """Try to extract the city name from the policy title."""
    cities = ['徐州', '苏州', '无锡', '扬州', '杭州', '嘉兴', '海宁', '金华', '舟山', 
              '绍兴', '越城', '长沙', '合肥', '芜湖', '成都', '高新', '自贡', '南充',
              '厦门', '福州', '雄安', '吉安', '九江', '沈阳']
    for city in cities:
        if city in raw:
            return city
    return region

def search_policy(item):
    title_raw = item['title']
    region = item['region']
    
    # Generate clean display title
    display_title = normalize_title(title_raw)
    
    # Extract key identifying terms
    # Get the core policy name (between 《》)
    m = re.search(r'[《（]([^》）]+)[》）]', title_raw)
    core_policy = m.group(1) if m else ""
    
    # Get the city name
    city = extract_region_city(title_raw, region)
    
    # Generate search queries - short and focused
    search_queries = []
    
    # Strategy 1: Search the provincial government site directly
    if region in GOV_SEARCH:
        search_queries.append(("province", region, title_raw[:20]))
    
    # Strategy 2: Search the city government site
    city_url = extract_city_url(city)
    if city_url:
        domain = re.search(r'https?://([^/]+)', city_url).group(1)
        # Search with key terms
        key_terms = re.findall(r'[\u4e00-\u9fff]{4,10}', title_raw)
        if key_terms:
            search_queries.append(("city_baidu", domain, ' '.join(key_terms[:3])))
    
    # Strategy 3: Try Baidu with short query
    short_query = f"{city} 低空经济"
    search_queries.append(("baidu_short", "", short_query))
    
    short_query2 = f"{region} 低空经济"
    search_queries.append(("baidu_short", "", short_query2))
    
    # Strategy 4: Use Baidu site: operator for provincial gov
    if region in GOV_SEARCH:
        prov_domain = re.search(r'https?://([^/]+)', GOV_SEARCH[region]).group(1)
        key_terms = re.findall(r'[\u4e00-\u9fff]{4,10}', title_raw)
        if key_terms:
            search_queries.append(("baidu_site", prov_domain, ' '.join(key_terms[:2])))
    
    # Search
    found_results = []
    
    for strategy, domain, query in search_queries:
        if strategy == "province":
            results = search_provincial_policy(region, [query])
            found_results.extend(results)
        elif strategy == "city_baidu":
            results = search_baidu_site(domain, query)
            found_results.extend(results)
        elif strategy == "baidu_short":
            results = search_baidu_short(query)
            found_results.extend(results)
        elif strategy == "baidu_site":
            results = search_baidu_site(domain, query)
            found_results.extend(results)
        
        if found_results:
            # Check for government URLs
            for t, u in found_results:
                if '.gov.cn' in u:
                    src = re.search(r'https?://([^/]+)', u).group(1) if re.search(r'https?://([^/]+)', u) else ""
                    print(f"  FOUND: {t[:60]}")
                    print(f"  URL: {u[:80]}")
                    return {
                        "title": t,
                        "search_keyword": query,
                        "url": u,
                        "status": "found",
                        "found_at": src
                    }
        
        time.sleep(0.5)
    
    # Also try: directly accessing known policy pages on government sites
    # Many governments have "政策文件" or "政府文件" sections
    known_policy_urls = {
        '江苏省': 'https://www.jiangsu.gov.cn/col/col64797/index.html',
        '浙江省': 'https://www.zj.gov.cn/col/col1229017135/index.html',
        '湖南省': 'https://www.hunan.gov.cn/hnszf/xxgk/wjk/szfbgt/index.html',
        '海南省': 'https://www.hainan.gov.cn/hainan/5200/xxgk_list.shtml',
        '四川省': 'https://www.sc.gov.cn/10462/11555/index.shtml',
        '山西省': 'https://www.shanxi.gov.cn/zfxxgk/zfxxgkml/szfbgt/index.shtml',
    }
    
    if region in known_policy_urls:
        try:
            policy_list_url = known_policy_urls[region]
            r = requests.get(policy_list_url, headers=HEADERS, timeout=10, verify=False)
            if r.status_code == 200:
                html = r.text
                # Look for links containing our key terms
                key_terms = re.findall(r'[\u4e00-\u9fff]{4,10}', title_raw)
                for term in key_terms[:3]:
                    links = re.findall(rf'<a[^>]*href="([^"]*)"[^>]*>[^<]*{term}[^<]*</a>', html)
                    for link in links:
                        full_url = link if link.startswith('http') else region_url_base(region) + link if link.startswith('/') else link
                        print(f"  FOUND (policy list): {full_url[:80]}")
                        return {
                            "title": display_title,
                            "search_keyword": term,
                            "url": full_url,
                            "status": "found",
                            "found_at": re.search(r'https?://([^/]+)', full_url).group(1) if re.search(r'https?://([^/]+)', full_url) else ""
                        }
        except:
            pass
    
    return {
        "title": display_title,
        "search_keyword": display_title[:60],
        "url": "",
        "status": "not_found",
        "found_at": ""
    }

def region_url_base(region):
    return GOV_SEARCH.get(region, 'https://www.gov.cn')

def search_baidu_short(query):
    """Search Baidu with a short query and extract URLs."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.baidu.com/s?wd={encoded}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = 'utf-8'
        html = r.text
        
        results = []
        blocks = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
        for block in blocks:
            a_match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
            if a_match:
                href = a_match.group(1)
                title = re.sub(r'<[^>]+>', '', a_match.group(2)).strip()
                # Only keep if it looks like a real URL (not Baidu wrapper)
                if 'baidu.com/link' not in href:
                    results.append((title, href))
        
        # Also try extracting from result divs
        if not results:
            # Alternative parsing
            result_divs = re.findall(r'<div[^>]*class="[^"]*c-container[^"]*"[^>]*data-url="([^"]*)"', html)
            for data_url in result_divs:
                results.append(("", data_url))
        
        return results
    except:
        return []

def main():
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings()
    
    items = load_input()
    print(f"Loaded {len(items)} items")
    
    results = []
    successes = 0
    
    for i, item in enumerate(items):
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(items)}] {item['region']}: {item['title'][:70]}")
        
        result = search_policy(item)
        
        if result['status'] == 'found':
            successes += 1
            print(f"  ✓ {result['found_at']}: {result['url'][:80]}")
        else:
            print(f"  ✗ Not found")
        
        results.append(result)
        
        if (i + 1) % 5 == 0 or i == len(items) - 1:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"  Checkpoint: {i+1}/{len(items)}")
        
        if i < len(items) - 1:
            time.sleep(1 + random.random())
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {successes}/{len(results)} found")
    print(f"Results: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
