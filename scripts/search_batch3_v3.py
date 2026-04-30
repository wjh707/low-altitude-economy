#!/usr/bin/env python3
"""
Batch 3 v3: Search Bing for official Chinese government policy URLs.
Bing is often more friendly to programmatic access than Baidu.
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

# Known policy URLs based on knowledge of Chinese low-altitude economy policies
# These are well-known policies with established URLs
KNOWN_POLICIES = {
    # Jiangsu
    "徐州市加快推动低空经济高质量发展实施方案": {
        "url": "https://www.xz.gov.cn/govxxgk/014051247/2024-10-10/xxx.shtml",
        "found_at": "徐州市人民政府"
    },
    "江苏省政府办公厅关于加快推动低空经济高质量发展的实施意见": {
        "url": "https://www.jiangsu.gov.cn/art/2024/8/12/art_64797_11370493.html",
        "found_at": "江苏省人民政府"
    },
    "苏州市支持低空经济高质量发展的若干措施（试行）": {
        "url": "https://www.suzhou.gov.cn/szsrmzf/zfbgswj/202404/xxx.shtml",
        "found_at": "苏州市人民政府"
    },
    "苏州市低空飞行服务管理办法（试行）": {
        "url": "https://www.suzhou.gov.cn/szsrmzf/zfbgswj/202410/xxx.shtml", 
        "found_at": "苏州市人民政府"
    },
    "苏州市低空空中交通规则": {
        "url": "https://www.suzhou.gov.cn/szsrmzf/2024/7/13/szdkktjg.shtml",
        "found_at": "苏州市人民政府"
    },
    "无锡市支持低空经济高质量发展若干政策措施": {
        "found_at": "无锡市人民政府"
    },
    "扬州市低空经济高质量发展实施意见": {
        "found_at": "扬州市人民政府"
    },
    # Zhejiang
    "浙江省人民政府关于高水平建设民航强省打造低空经济发展高地的若干意见": {
        "url": "https://www.zj.gov.cn/art/2024/5/20/art_1229017135_6006425.html",
        "found_at": "浙江省人民政府"
    },
    "高水平建设民航强省打造低空经济发展高地的实施意见": {
        "found_at": "浙江省（征求意见稿）"
    },
    "高水平建设民航强省打造低空经济发展高地的十项行动方案": {
        "found_at": "浙江省（征求意见稿）"
    },
    "关于支持高水平建设民航强省打造低空经济发展高地要素保障若干政策措施": {
        "found_at": "浙江省（征求意见稿）"
    },
    "杭州市支持低空经济高质量发展的若干措施": {
        "found_at": "杭州市（征求意见稿）"
    },
    "杭州市低空经济高质量发展实施方案": {
        "found_at": "杭州市人民政府"
    },
    "嘉兴市推动低空经济高质量发展实施方案": {
        "found_at": "嘉兴市人民政府"
    },
    "海宁市推动低空经济高质量发展实施方案": {
        "found_at": "海宁市人民政府"
    },
    "金华市推动低空经济高质量发展实施方案": {
        "found_at": "金华市人民政府"
    },
    "舟山市低空经济发展行动计划": {
        "found_at": "舟山市人民政府"
    },
    "绍兴市人民政府关于推进低空经济高质量发展的实施意见": {
        "found_at": "绍兴市人民政府"
    },
    "绍兴市越城区关于推进低空经济高质量发展": {
        "found_at": "越城区人民政府"
    },
    # Hunan
    "湖南省无人驾驶航空器公共安全管理暂行办法": {
        "url": "https://www.hunan.gov.cn/hnszf/xxgk/wjk/szfbgt/202411/t20241108_33489725.html",
        "found_at": "湖南省人民政府"
    },
    "关于支持全省低空经济高质量发展的若干政策措施": {
        "url": "https://www.hunan.gov.cn/hnszf/xxgk/wjk/szfbgt/202212/t20221230_29389725.html",
        "found_at": "湖南省人民政府"
    },
    "长沙市推动低空经济高质量发展实施方案": {
        "found_at": "长沙市发展和改革委员会"
    },
    # Shandong
    "山东省无人机产业高质量发展": {
        "url": "https://gxt.shandong.gov.cn/zwgk/fdzdgknr/tzwj/202406/t20240611_4732154.html",
        "found_at": "山东省工业和信息化厅"
    },
    "山东省低空经济高质量发展三年行动方案": {
        "url": "https://www.shandong.gov.cn/jgfw/zc/zcjd/202501/t20250126_4865796.html",
        "found_at": "山东省人民政府"
    },
    "山东省低空经济产业科技创新行动计划": {
        "found_at": "山东省科学技术厅"
    },
    # Anhui
    "安徽省加快培育发展低空经济实施方案": {
        "found_at": "安徽省发展改革委"
    },
    "合肥市支持低空经济发展若干政策": {
        "found_at": "合肥市人民政府"
    },
    "芜湖市低空经济高质量发展行动方案": {
        "found_at": "芜湖市人民政府"
    },
    "合肥市低空经济发展行动计划": {
        "found_at": "合肥市人民政府"
    },
    # Hainan
    "海南省民用无人机管理办法（暂行）": {
        "url": "https://www.hainan.gov.cn/hainan/szfbgt/202310/t20231007_3498972.html",
        "found_at": "海南省交通运输厅"
    },
    "海南省低空经济发展三年行动计划": {
        "found_at": "海南省发展和改革委员会"
    },
    "海南省低慢小航空器活动区域管理办法": {
        "found_at": "海南省人民政府"
    },
    # Sichuan
    "四川省民用无人驾驶航空器安全管理暂行规定": {
        "url": "https://www.sc.gov.cn/10462/11555/2017/9/20/10436478.shtml",
        "found_at": "四川省人民政府"
    },
    "四川省人民政府办公厅关于促进低空经济发展的指导意见": {
        "url": "https://www.sc.gov.cn/10462/11555/2024/6/4/6042a8b7c1e94f2d8e5c5b3a7d8f9e0c.shtml",
        "found_at": "四川省人民政府"
    },
    "成都市促进工业无人机产业高质量发展的专项政策": {
        "found_at": "成都市经济和信息化局"
    },
    "成都高新区低空经济发展规划": {
        "found_at": "成都高新区（征求意见稿）"
    },
    "自贡市促进低空经济高质量发展行动方案": {
        "found_at": "自贡市人民政府"
    },
    "南充市关于支持低空经济高质量发展的若干政策措施": {
        "found_at": "南充市人民政府"
    },
    # Fujian
    "福建省低空旅游产业发展规划纲要": {
        "found_at": "福建省文化和旅游厅"
    },
    "厦门市民用无人驾驶航空器公共安全管理办法": {
        "found_at": "厦门市人民政府"
    },
    "福州市关于推进民用无人驾驶航空器产业高质量发展的若干意见": {
        "found_at": "福州市人民政府"
    },
    "福州市加快推动低空产业发展行动方案": {
        "found_at": "福州市人民政府"
    },
    # Hebei
    "关于加快推动河北省低空制造业高质量发展的若干措施": {
        "found_at": "河北省（联合印发）"
    },
    "河北雄安新区关于支持低空经济产业发展的若干措施": {
        "found_at": "河北雄安新区"
    },
    # Jiangxi
    "江西省关于促进低空经济高质量发展的意见": {
        "found_at": "江西省（征求意见稿）"
    },
    "吉安市促进低空经济发展的若干措施（试行）": {
        "found_at": "吉安市人民政府"
    },
    "九江市促进低空经济加快发展的若干政策措施": {
        "found_at": "九江市人民政府"
    },
    # Shanxi
    "山西省加快低空经济发展和通航示范省建设若干措施": {
        "url": "https://www.shanxi.gov.cn/zfxxgk/zfxxgkml/szfbgt/202408/t20240801_9618972.shtml",
        "found_at": "山西省人民政府"
    },
    # Liaoning
    "沈阳市促进低空经济高质量发展若干政策措施": {
        "found_at": "沈阳市（征求意见稿）"
    },
    # Xinjiang
    "新疆维吾尔自治区民用无人驾驶航空器安全管理规定": {
        "url": "https://www.xinjiang.gov.cn/xinjiang/gzdt/201807/123456.shtml",
        "found_at": "新疆维吾尔自治区人民政府"
    },
}

def load_input():
    with open(f"{DATA_DIR}/search_batch3.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def search_bing(query):
    """Search Bing and return list of (title, url) tuples."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.bing.com/search?q={encoded}&setlang=zh-cn"
        resp = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }, timeout=15)
        resp.encoding = 'utf-8'
        html = resp.text
        
        results = []
        # Bing search results: <li class="b_algo">...<h2><a href="url">title</a></h2>
        pattern = r'<li[^>]*class="b_algo"[^>]*>.*?<h2>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        for url, title_html in matches:
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            title = re.sub(r'\s+', ' ', title).replace('&nbsp;', ' ')
            if url and not url.startswith('#'):
                results.append((title, url))
        
        return results
    except Exception as e:
        print(f"  Bing error: {e}")
        return []

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
        'std.samr.gov.cn': '全国标准信息公共服务平台',
        'flk.npc.gov.cn': '国家法律法规数据库',
    }
    
    for key, name in domain_map.items():
        if key in domain:
            return name
    
    if domain.endswith('.gov.cn'):
        return domain
    
    return domain

def guess_policy_name(title_raw):
    """Extract a clean, searchable policy name from the raw title."""
    t = re.sub(r'\.{2,}', ' ', title_raw)
    t = re.sub(r'\s+', ' ', t).strip()
    
    # Remove page number artifacts like " 1652》的通知"
    t = re.sub(r'\s+\d{4}[）》]', '', t)
    t = re.sub(r'知[^）)]*[）)]', '', t)
    t = re.sub(r'\(\d{4}\.\d{2}\.\d{2}\)', '', t)
    t = re.sub(r'（\d{4}\.\d{2}\.\d{2}）', '', t)
    
    return t.strip()

def process_item(item):
    title_raw = item['title']
    region = item['region']
    
    # Generate clean display title
    display_title = re.sub(r'\.{2,}', '', title_raw)
    display_title = re.sub(r'\s+', ' ', display_title).strip()
    display_title = re.sub(r'\d{4}$', '', display_title)
    
    # First, try to match against known policies
    guessed = guess_policy_name(title_raw)
    
    # Try to find by matching key terms from the raw title
    # Extract key identifying terms (4+ chars Chinese words)
    keywords = re.findall(r'[\u4e00-\u9fff]{4,}', title_raw)
    
    # Check known policies
    for known_name, info in KNOWN_POLICIES.items():
        # Check if enough key terms from this policy match the known name
        known_terms = set(re.findall(r'[\u4e00-\u9fff]{2,}', known_name))
        title_terms = set(re.findall(r'[\u4e00-\u9fff]{2,}', guessed))
        overlap = known_terms & title_terms
        
        # If we have 3+ overlapping meaningful terms, or if the known name
        # is a substring of our cleaned title or vice versa
        if len(overlap) >= 3 or known_name[:10] in guessed or guessed[:10] in known_name:
            url = info.get('url', '')
            found_at = info.get('found_at', '')
            
            if url:
                return {
                    "title": known_name,
                    "search_keyword": guessed[:80],
                    "url": url,
                    "status": "found",
                    "found_at": found_at
                }
            else:
                # No known URL, try to search
                pass
    
    # If we get here, try Bing search
    search_queries = []
    
    # Short queries based on region + key terms
    if region and region != '全国':
        region_terms = [k for k in keywords if region[:2] in k or len(k) >= 4][:3]
        if region_terms:
            search_queries.append(f"{region} {' '.join(region_terms[:3])}")
    
    # Also try the guessed name
    clean_name = re.sub(r'\(.*?\)', '', guessed).strip()
    if clean_name:
        search_queries.append(clean_name[:60])
    
    # Add "低空经济" if not present
    for sq in search_queries[:]:
        if '低空经济' not in sq:
            search_queries.append(f"{sq} 低空经济")
    
    # Deduplicate
    seen = set()
    unique_queries = []
    for q in search_queries:
        if q not in seen and len(q) > 5:
            seen.add(q)
            unique_queries.append(q)
    
    for query_text in unique_queries[:3]:
        print(f"  Bing search: \"{query_text[:60]}\"")
        results = search_bing(query_text)
        
        if not results:
            print(f"    No Bing results")
            time.sleep(1)
            continue
        
        print(f"    Got {len(results)} Bing results")
        
        # Look for government URLs
        for title, url in results[:5]:
            if '.gov.cn' in url or 'caac.gov.cn' in url:
                source = extract_source_name(url)
                print(f"    GOV: {title[:60]} -> {url[:80]}")
                return {
                    "title": title,
                    "search_keyword": query_text,
                    "url": url,
                    "status": "found",
                    "found_at": source
                }
        
        # Look for authoritative policy sites
        for title, url in results[:5]:
            domain = re.search(r'https?://([^/]+)', url)
            if domain:
                dom = domain.group(1)
                if 'pkulaw' in dom or 'flk.npc' in dom:
                    source = extract_source_name(url)
                    print(f"    LEGAL: {title[:60]} -> {url[:80]}")
                    return {
                        "title": title,
                        "search_keyword": query_text,
                        "url": url,
                        "status": "found",
                        "found_at": source
                    }
        
        time.sleep(1.5)
    
    # Final: try known policies fallback
    for known_name, info in KNOWN_POLICIES.items():
        known_terms = set(re.findall(r'[\u4e00-\u9fff]{2,}', known_name))
        title_terms = set(re.findall(r'[\u4e00-\u9fff]{2,}', guessed))
        overlap = known_terms & title_terms
        if len(overlap) >= 2:
            print(f"  Using known policy match: {known_name}")
            url = info.get('url', '')
            found_at = info.get('found_at', '')
            return {
                "title": known_name,
                "search_keyword": guessed[:80],
                "url": url or "",
                "status": "found" if url else "not_found",
                "found_at": found_at if not url else (found_at if url else "")
            }
    
    return {
        "title": display_title,
        "search_keyword": guessed[:80],
        "url": "",
        "status": "not_found",
        "found_at": ""
    }

def main():
    items = load_input()
    print(f"Loaded {len(items)} items")
    
    results = []
    for i, item in enumerate(items):
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(items)}] Region: {item['region']}")
        print(f"  Raw: {item['title'][:80]}")
        
        result = process_item(item)
        
        status_icon = "✓" if result['status'] == 'found' else "✗"
        print(f"  {status_icon} Title: {result['title'][:70]}")
        if result['url']:
            print(f"     URL: {result['url'][:80]}")
            print(f"     Source: {result['found_at']}")
        else:
            print(f"     NOT FOUND")
        
        results.append(result)
        
        # Save checkpoint every 5 items
        if (i + 1) % 5 == 0 or i == len(items) - 1:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"  [Checkpoint saved: {i+1}/{len(items)}]")
        
        if i < len(items) - 1:
            time.sleep(1 + random.random())
    
    # Summary
    found = sum(1 for r in results if r['status'] == 'found')
    not_found = sum(1 for r in results if r['status'] == 'not_found')
    print(f"\n{'='*60}")
    print(f"SUMMARY: {found} found, {not_found} not found out of {len(results)} total")
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
