#!/opt/anaconda3/bin/python3.12
"""
Final approach: Search using Bing with properly constructed queries.
Key insight: Use fewer, more distinctive words to avoid Bing's Chinese word splitting issue.
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

def bing_search(query, count=10):
    """Search Bing and return parsed results."""
    q = query.replace('"', '')  # Bing ignores quotes anyway
    url = f"https://www.bing.com/search?q={quote(q)}&setlang=zh-Hans&cc=cn&count={count}"
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
            if link:
                title = link[0].text_content().strip()
                href = link[0].get('href', '')
                cite_text = cite[0].text_content().strip() if cite else ''
                if href:
                    results.append({
                        'title': title, 'href': href, 'cite': cite_text
                    })
        return results
    except Exception:
        return []

def is_gov_result(url, title, cite):
    """Check if result is from a government/authoritative domain."""
    combined = (url + ' ' + cite).lower()
    for d in ['gov.cn', 'caac.gov.cn', 'pkulaw.com', 'std.samr.gov.cn']:
        if d in combined:
            return True
    return False

def get_source_name(url, cite):
    """Get readable source name."""
    c = (url + ' ' + cite).lower()
    if 'caac.gov.cn' in c:
        return "中国民用航空局"
    if 'www.gov.cn' in c:
        return "中华人民共和国中央人民政府"
    if 'gov.cn' in c:
        return "政府网站"
    if 'pkulaw.com' in c:
        return "北大法宝"
    if 'std.samr.gov.cn' in c:
        return "全国标准信息公共服务平台"
    return cite[:40] if cite else url[:40]

def clean_title(raw):
    """Clean the title."""
    t = raw.split('....')[0].strip()
    t = re.sub(r'\.{3,}.*$', '', t)
    return t.strip()

def search_policy(clean_title, region):
    """Search for a policy with best-effort strategies."""
    
    # Short, distinctive keywords (avoid common Chinese words that cause splitting)
    # Remove date parentheses
    no_date = re.sub(r'[（(]\d{4}[^）)]*[）)]', '', clean_title).strip()
    # Remove 通知、办法、规定 etc suffixes for more specific terms
    core = re.sub(r'[（(].*?[）)]', '', clean_title).strip()
    core = re.sub(r'^(关于印发《|关于发布《|关于修订《|关于印发《)', '', core)
    core = re.sub(r'》的通知$|》$', '', core).strip()
    
    search_queries = []
    
    # For specific categories of policies
    if '空域基础分类' in clean_title:
        search_queries = ['空域基础分类方法 民航局 caac']
    elif '通用航空经营许可' in clean_title:
        search_queries = ['通用航空经营许可管理规定 gov.cn']
    elif '通用航空安全保卫' in clean_title:
        search_queries = ['通用航空安全保卫规则 民航局 caac']
    elif '通用航空企业诚信' in clean_title:
        search_queries = ['通用航空企业诚信经营评价 民航局']
    elif 'A 类通用机场' in clean_title:
        search_queries = ['A类通用机场 使用许可 运行安全 管理办法 民航局']
    elif '通用航空装备' in clean_title:
        search_queries = ['通用航空装备创新应用实施方案 2024 2030']
    elif '通用航空短途运输' in clean_title:
        search_queries = ['通用航空短途运输运营服务管理办法 民航局']
    elif '通用航空危险品' in clean_title:
        search_queries = ['通用航空危险品运输管理暂行办法 征求意见稿']
    elif '低空飞行服务' in clean_title:
        search_queries = ['低空飞行服务专业人员 基础培训机构 管理办法 民航局']
    elif '空中交通管理规则' in clean_title:
        search_queries = ['民用航空空中交通管理规则 修正 交通运输部']
    elif '产品和零部件' in clean_title:
        search_queries = ['民用航空产品和零部件合格审定规定 修正']
    elif '轻小无人机' in clean_title:
        search_queries = ['轻小无人机运行规定 试行 民航局']
    elif '空中交通管理' in clean_title and '无人驾驶' in clean_title:
        search_queries = ['民用无人驾驶航空器系统空中交通管理办法']
    elif '实名制登记' in clean_title:
        search_queries = ['民用无人驾驶航空器实名制登记管理规定']
    elif '经营性飞行活动' in clean_title:
        search_queries = ['民用无人驾驶航空器经营性飞行活动管理办法']
    elif '无人机驾驶员' in clean_title:
        search_queries = ['民用无人机驾驶员管理规定 修订']
    elif '特定类无人机试运行' in clean_title:
        search_queries = ['特定类无人机试运行管理规程']
    elif '飞行动态数据' in clean_title:
        search_queries = ['轻小型民用无人机飞行动态数据管理规定']
    elif '法规标准体系' in clean_title:
        search_queries = ['民用无人驾驶航空法规标准体系构建指南']
    elif '国籍登记' in clean_title:
        search_queries = ['民用无人驾驶航空器国籍登记管理程序']
    elif '生产管理若干规定' in clean_title:
        search_queries = ['民用无人驾驶航空器生产管理若干规定']
    elif '运行安全管理规则' in clean_title and '无人驾驶' in clean_title:
        search_queries = ['民用无人驾驶航空器运行安全管理规则']
    elif '无线电管理' in clean_title and '无人驾驶' in clean_title:
        search_queries = ['民用无人驾驶航空器无线电管理暂行办法']
    elif '微轻小型' in clean_title:
        search_queries = ['民用微轻小型无人驾驶航空器运行识别 最低性能要求']
    elif '适航安全评定' in clean_title:
        search_queries = ['民用无人驾驶航空器系统适航安全评定指南']
    elif '系统安全要求' in clean_title:
        search_queries = ['民用无人驾驶航空器系统安全要求 GB']
    elif '适航审定管理程序' in clean_title:
        search_queries = ['民用无人驾驶航空器系统适航审定管理程序']
    elif '低空空域管理改革' in clean_title:
        search_queries = ['深化我国低空空域管理改革意见 2010']
    elif '促进通用航空业' in clean_title:
        search_queries = ['促进通用航空业发展指导意见 2016']
    elif '十三五国家科技创新' in clean_title:
        search_queries = ['十三五国家科技创新规划 国务院']
    elif '十三五现代综合交通运输' in clean_title:
        search_queries = ['十三五现代综合交通运输体系发展规划']
    elif '全域旅游' in clean_title:
        search_queries = ['促进全域旅游发展指导意见 2018 gov.cn']
    elif '低空飞行服务保障体系' in clean_title:
        search_queries = ['低空飞行服务保障体系建设总体方案 民航局']
    elif '综合立体交通网' in clean_title:
        search_queries = ['国家综合立体交通网规划纲要 2021']
    elif '十四五现代综合交通运输' in clean_title:
        search_queries = ['十四五现代综合交通运输体系发展规划']
    elif '十四五旅游业' in clean_title:
        search_queries = ['十四五旅游业发展规划 国务院 通知']
    elif '全面深化改革' in clean_title and '中国式现代化' in clean_title:
        search_queries = ['进一步全面深化改革 推进中国式现代化的决定']
    elif '服务消费高质量' in clean_title:
        search_queries = ['促进服务消费高质量发展意见 国务院']
    elif '统一开放的交通运输市场' in clean_title:
        search_queries = ['加快建设统一开放的交通运输市场意见']
    elif '专项债券管理机制' in clean_title:
        search_queries = ['优化完善地方政府专项债券管理机制意见']
    elif '交通运输标准提升' in clean_title:
        search_queries = ['交通运输标准提升行动方案 2024']
    elif '极端场景应急通信' in clean_title:
        search_queries = ['加强极端场景应急通信能力建设']
    elif '服务业扩大开放' in clean_title:
        search_queries = ['国家服务业扩大开放综合试点示范省市']
    elif '培育新增长点' in clean_title or '文化和旅游消费' in clean_title:
        search_queries = ['进一步培育新增长点繁荣文化和旅游消费']
    elif '户外运动' in clean_title:
        search_queries = ['建设高质量户外运动目的地指导意见']
    elif '江苏省民用航空条例' in clean_title:
        search_queries = ['江苏省民用航空条例 2017']
    elif '重庆市民用航空条例' in clean_title:
        search_queries = ['重庆市民用航空条例 2019']
    elif '四川省通用航空条例' in clean_title:
        search_queries = ['四川省通用航空条例 2022']
    else:
        search_queries = [no_date[:60], core[:60]]
    
    if region and region != '全国':
        search_queries.append(f"{no_date[:40]} {region}")
    
    # Try each query
    for q in search_queries:
        if len(q) < 5:
            continue
        results = bing_search(q)
        if results:
            # First: authoritative results
            for r in results:
                if is_gov_result(r['href'], r['title'], r['cite']):
                    # Check relevance
                    relevant_words = [w for w in re.findall(r'[\u4e00-\u9fff]{2,}', clean_title) if len(w) >= 3]
                    title_text = r['title'] + ' ' + r['cite'] + ' ' + r['href']
                    score = sum(1 for w in relevant_words if w in title_text)
                    if score >= 1:
                        return r['href'], get_source_name(r['href'], r['cite'])
            
            # Second: any result that clearly has gov domain
            for r in results:
                url = r['href']
                if 'gov.cn' in url.lower() or 'caac.gov.cn' in url.lower():
                    return url, get_source_name(url, r['cite'])
    
    return None, None

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    print(f"Loaded {len(items)} items")
    all_results = []
    
    for idx, item in enumerate(items):
        raw = item["title"]
        region = item.get("region", "")
        ct = clean_title(raw)
        
        print(f"\n[{idx+1}/{len(items)}] {ct[:60]}...", end=' ')
        
        url, source = search_policy(ct, region)
        
        if url:
            print(f"✓")
            print(f"   URL: {url[:90]}")
            print(f"   Src: {source}")
        else:
            print(f"✗ NOT FOUND")
        
        all_results.append({
            "title": ct,
            "search_keyword": ct,
            "url": url or "",
            "status": "found" if url else "not_found",
            "found_at": source or ""
        })
        
        time.sleep(1.2)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    found = sum(1 for r in all_results if r["status"] == "found")
    print(f"\n{'='*60}")
    print(f"Done! Found: {found}/{len(all_results)} ({100*found//len(all_results)}%)")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
