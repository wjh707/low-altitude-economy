#!/opt/anaconda3/bin/python3.12
"""
Search batch2 policies using Bing search to find official government URLs.
Adapted from search_batch1_v6.py for the 49 local/regional low-altitude economy policies.
"""
import json
import re
import time
import requests
from lxml import html
from urllib.parse import quote

INPUT_FILE = "/Users/zhoulai/low-altitude-economy/data/search_batch2.json"
OUTPUT_FILE = "/Users/zhoulai/low-altitude-economy/data/search_batch2_result.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def bing_search(query, count=15):
    """Search Bing and return parsed results."""
    q = query.replace('"', '')
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
    except Exception as e:
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
    lower_cite = cite.lower()
    
    if 'caac.gov.cn' in c:
        return "中国民用航空局"
    if 'www.gov.cn' in c:
        return "中华人民共和国中央人民政府"
    if 'gov.cn' in c:
        # Try to identify specific government
        if 'nhc.gov.cn' in c: return "国家卫生健康委员会"
        if 'miit.gov.cn' in c: return "工业和信息化部"
        if 'mof.gov.cn' in c: return "财政部"
        if 'ndrc.gov.cn' in c: return "国家发展和改革委员会"
        if 'mofcom.gov.cn' in c: return "商务部"
        if 'mps.gov.cn' in c: return "公安部"
        if 'most.gov.cn' in c: return "科学技术部"
        if 'beijing.gov.cn' in c or 'bj' in c: return "北京市政府网站"
        if 'shanghai.gov.cn' in c or 'sh.gov.cn' in c: return "上海市政府网站"
        if 'gd.gov.cn' in c: return "广东省政府网站"
        if 'sz.gov.cn' in c: return "深圳市政府网站"
        if 'nj.gov.cn' in c: return "南京市政府网站"
        if 'su Zhou' in lower_cite or 'suzhou' in c: return "苏州市政府网站"
        if 'wuxi' in c: return "无锡市政府网站"
        if 'changzhou' in c: return "常州市政府网站"
        if 'nantong' in c: return "南通市政府网站"
        if 'zhuhai' in c: return "珠海市政府网站"
        if 'huizhou' in c: return "惠州市政府网站"
        if 'zhongshan' in c: return "中山市政府网站"
        if 'dongguan' in c: return "东莞市政府网站"
        if 'foshan' in c: return "佛山市政府网站"
        if 'maoming' in c: return "茂名市政府网站"
        if 'zhanjiang' in c: return "湛江市政府网站"
        if 'tianjin' in c or 'tj.gov.cn' in c: return "天津市政府网站"
        if 'chongqing' in c or 'cq.gov.cn' in c: return "重庆市政府网站"
        if 'hunan' in c or 'hn.gov.cn' in c: return "湖南省政府网站"
        if 'zhejiang' in c or 'zj.gov.cn' in c: return "浙江省政府网站"
        if 'jiangsu' in c or 'js.gov.cn' in c: return "江苏省政府网站"
        if 'guangdong' in c: return "广东省政府网站"
        return "政府网站"
    if 'pkulaw.com' in c:
        return "北大法宝"
    if 'std.samr.gov.cn' in c:
        return "全国标准信息公共服务平台"
    return cite[:40] if cite else url[:40]

def clean_title(raw):
    """Clean the raw title."""
    # Remove trailing dots/ellipsis and page numbers
    t = raw.split('....')[0].strip()
    t = re.sub(r'\\.{3,}.*$', '', t)
    t = re.sub(r'\\.{2,}$', '', t)
    # Remove page number at the end like "...... 1311" or "......1439"
    t = re.sub(r'\\.*[\d]+$', '', t).strip()
    return t.strip()

def build_search_queries(clean_title, region):
    """Build targeted search queries for each policy."""
    queries = []
    no_date = re.sub(r'[（(]\d{4}[^）)]*[）)]', '', clean_title).strip()
    
    # Extract core document name (remove 关于印发 etc.)
    core = clean_title
    core = re.sub(r'^关于印发《|^关于印发|^关于联合印发《|^关于联合印发', '', core)
    core = re.sub(r'^关于发布《|^关于修订《', '', core)
    core = re.sub(r'》的通知$|》$|的通知$', '', core)
    core = core.strip()
    
    # Specific targeting based on content
    lower = clean_title.lower()
    
    # ====== Provincial regulations ======
    if '湖南省通用航空条例' in clean_title:
        queries = ['湖南省通用航空条例 gov.cn', '湖南省通用航空条例 全文']
    elif '浙江省无人驾驶航空器公共安全管理规定' in clean_title:
        queries = ['浙江省无人驾驶航空器公共安全管理规定 gov.cn', '浙江省无人驾驶航空器公共安全管理规定 全文']
    elif '深圳经济特区低空经济产业促进条例' in clean_title:
        queries = ['深圳经济特区低空经济产业促进条例 sz.gov.cn', '深圳经济特区低空经济产业促进条例 全文']
    elif '珠海经济特区低空交通建设管理条例' in clean_title:
        queries = ['珠海经济特区低空交通建设管理条例 gov.cn', '珠海经济特区低空交通建设管理条例 全文']
    elif '广州市低空经济发展条例' in clean_title:
        queries = ['广州市低空经济发展条例 gov.cn', '广州市低空经济发展条例 全文']
    elif '深圳市民用微轻型无人机管理暂行办法' in clean_title:
        queries = ['深圳市民用微轻型无人机管理暂行办法 2019 sz.gov.cn']
    elif '重庆市民用无人驾驶航空器公共安全管理办法' in clean_title:
        queries = ['重庆市民用无人驾驶航空器公共安全管理办法 2024 cq.gov.cn']
    
    # ====== Beijing ======
    elif '北京市促进低空经济产业高质量发展行动方案' in clean_title:
        queries = ['北京市促进低空经济产业高质量发展行动方案 2024-2027 beijing.gov.cn']
    elif '房山区低空经济产业发展行动方案' in clean_title:
        queries = ['房山区低空经济产业发展行动方案 2024-2027']
    elif '中关村延庆园无人机产业创新发展行动方案' in clean_title:
        queries = ['中关村延庆园无人机产业创新发展行动方案 beijing.gov.cn']
    elif '丰台区低空经济产业高质量发展的指导意见' in clean_title:
        queries = ['丰台区低空经济产业高质量发展 指导意见 2024-2026']
    
    # ====== Shanghai ======
    elif '上海市低空经济产业高质量发展行动方案' in clean_title:
        queries = ['上海市低空经济产业高质量发展行动方案 2024-2027 shanghai.gov.cn']
    elif '杨浦区促进低空经济发展的若干措施' in clean_title:
        queries = ['杨浦区促进低空经济发展的若干措施 试行 2024 shanghai.gov.cn']
    elif '金山区关于加快低空经济产业高质量发展的政策措施' in clean_title:
        queries = ['金山区 加快低空经济产业高质量发展 政策措施 2024']
    
    # ====== Guangdong Province ======
    elif '广东省推动低空经济高质量发展行动方案' in clean_title:
        queries = ['广东省推动低空经济高质量发展行动方案 2024-2026 gd.gov.cn']
    elif '广州市低空经济发展实施方案' in clean_title:
        queries = ['广州市低空经济发展实施方案 2024 gz.gov.cn']
    elif '惠州市推动低空经济高质量发展行动方案' in clean_title:
        queries = ['惠州市推动低空经济高质量发展行动方案 2024-2026']
    elif '中山市低空经济高质量发展行动方案' in clean_title:
        queries = ['中山市低空经济高质量发展行动方案 2024']
    elif '东莞市推动低空经济高质量发展实施方案' in clean_title:
        queries = ['东莞市推动低空经济高质量发展实施方案 2024-2026']
    elif '佛山市推动低空经济高质量发展实施方案' in clean_title:
        queries = ['佛山市推动低空经济高质量发展实施方案 2024-2026']
    elif '茂名市推动低空经济高质量发展实施方案' in clean_title:
        queries = ['茂名市推动低空经济高质量发展实施方案 2024-2026']
    elif '湛江市推动低空经济高质量发展行动方案' in clean_title:
        queries = ['湛江市推动低空经济高质量发展行动方案 2024-2026']
    elif '珠海市人民政府关于印发支持低空经济高质量发展若干措施' in clean_title:
        queries = ['珠海市 支持低空经济高质量发展若干措施 2024']
    elif '深圳市支持低空经济高质量发展的若干措施' in clean_title:
        queries = ['深圳市支持低空经济高质量发展的若干措施 2023 sz.gov.cn']
    elif '广州市推动低空经济高质量发展若干措施' in clean_title:
        queries = ['广州市推动低空经济高质量发展若干措施 gz.gov.cn']
    elif '深圳市宝安区关于促进低空经济产业发展' in clean_title:
        queries = ['深圳市宝安区 促进低空经济产业发展 措施 2024']
    elif '深圳市龙华区促进低空经济产业高质量发展若干措施' in clean_title:
        queries = ['深圳市龙华区 促进低空经济产业高质量发展若干措施 2023']
    elif '广州开发区（黄埔区）促进' in clean_title or '黄埔区' in clean_title:
        queries = ['广州开发区 黄埔区 促进低空经济 措施']
    elif '龙岗区关于促进低空经济产业发展' in clean_title:
        queries = ['龙岗区 促进低空经济产业发展 若干措施 2023']
    elif '深圳市罗湖区促进商旅文低空应用的若干措施' in clean_title:
        queries = ['罗湖区 促进商旅文低空应用 若干措施 2024']
    elif '南山区促进低空经济发展专项扶持措施' in clean_title:
        queries = ['南山区 促进低空经济发展 专项扶持措施 2024']
    elif '盐田区关于促进低空经济产业创新发展的' in clean_title:
        queries = ['盐田区 促进低空经济产业创新发展 措施']
    elif '阜沙镇促进低空经济高质量发展实干措施' in clean_title:
        queries = ['阜沙镇 促进低空经济高质量发展 实干措施']
    elif '深圳市福田区支持低空经济高质量' in clean_title:
        queries = ['福田区 支持低空经济高质量发展 措施 2024']
    elif '谢岗镇支持新能源汽车产业和低空经济产业发展扶持措施' in clean_title:
        queries = ['谢岗镇 低空经济 扶持措施 试行']
    
    # ====== Tianjin ======
    elif '天津市宁河区低空经济高质量发展行动' in clean_title:
        queries = ['宁河区低空经济高质量发展行动方案 gov.cn']
    elif '宁河区促进低空经济高质量发展的八条措施' in clean_title:
        queries = ['宁河区 促进低空经济高质量发展 八条措施']
    elif '天津东疆综合保税区关于支持低空经济高质量发展若干措施' in clean_title:
        queries = ['天津东疆综合保税区 支持低空经济 若干措施 征求意见稿']
    
    # ====== Chongqing ======
    elif '重庆市推动低空空域管理改革促进低空经济' in clean_title:
        queries = ['重庆市推动低空空域管理改革促进低空经济高质量发展 行动方案 2024-2027']
    elif '梁平区支持低空经济高质量发展十条激励措施' in clean_title:
        queries = ['梁平区 支持低空经济高质量发展 十条激励措施 试行']
    
    # ====== Jiangsu ======
    elif '江苏省航空航天产业发展三年行动计划' in clean_title:
        queries = ['江苏省航空航天产业发展三年行动计划 gov.cn']
    elif '南京市促进低空经济高质量发展实施方案' in clean_title:
        queries = ['南京市促进低空经济高质量发展实施方案 2023-2025']
    elif '南京市低空飞行服务保障体系建设行动' in clean_title:
        queries = ['南京市低空飞行服务保障体系建设行动计划 2024-2026']
    elif '苏州市低空经济高质量发展实施方案' in clean_title:
        queries = ['苏州市低空经济高质量发展实施方案 2024-2026']
    elif '苏州工业园区低空经济高质量发展行动计划' in clean_title:
        queries = ['苏州工业园区低空经济高质量发展行动计划 2024-2026']
    elif '吴中区低空经济高质量发展三年行动计划' in clean_title:
        queries = ['吴中区 低空经济高质量发展 三年行动计划 2024']
    elif '无锡市低空经济高质量发展三年行动方案' in clean_title:
        queries = ['无锡市低空经济高质量发展三年行动方案']
    elif '常州市低空经济高质量发展三年行动方案' in clean_title:
        queries = ['常州市低空经济高质量发展三年行动方案 2024-2026']
    elif '南通市低空经济高质量发展行动方案' in clean_title:
        queries = ['南通市低空经济高质量发展行动方案 2024-2027']
    
    # ====== Fallback ======
    else:
        # Generic fallback
        queries = [no_date[:60], core[:60]]
        if region and region != '全国':
            queries.append(f"{no_date[:40]} {region}")
    
    # Add region-specific query as supplementary
    if region and region != '全国':
        region_specific = f"{no_date[:30]} {region}"
        if region_specific not in queries and len(region_specific) > 8:
            queries.append(region_specific)
    
    # Deduplicate while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)
    
    return unique_queries


def check_relevance(result, clean_title):
    """Check if search result is relevant to the policy we're looking for."""
    title_text = result['title'] + ' ' + result['cite'] + ' ' + result['href']
    # Extract key Chinese words (2+ chars)
    key_words = re.findall(r'[\u4e00-\u9fff]{2,}', clean_title)
    # Filter to meaningful words (3+ chars or specific patterns)
    meaningful = [w for w in key_words if len(w) >= 3]
    
    score = sum(1 for w in meaningful if w in title_text)
    return score, len(meaningful)


def search_policy(clean_title, region):
    """Search for a policy and return (url, source_name)."""
    
    queries = build_search_queries(clean_title, region)
    
    for q in queries:
        if len(q) < 5:
            continue
        
        results = bing_search(q)
        if not results:
            continue
        
        # Priority 1: Authoritative (.gov.cn, caac.gov.cn) AND relevant
        best_gov = None
        best_gov_score = 0
        
        for r in results:
            if is_gov_result(r['href'], r['title'], r['cite']):
                score, total = check_relevance(r, clean_title)
                if score >= 1 or total == 0:
                    if score > best_gov_score:
                        best_gov_score = score
                        best_gov = r
        
        if best_gov:
            return best_gov['href'], get_source_name(best_gov['href'], best_gov['cite'])
        
        # Priority 2: Any result with .gov.cn domain regardless of relevance
        for r in results:
            if 'gov.cn' in r['href'].lower() or 'caac.gov.cn' in r['href'].lower():
                return r['href'], get_source_name(r['href'], r['cite'])
    
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
        
        msg = f"[{idx+1}/{len(items)}] [{region}] {ct[:60]}..."
        print(msg, end=' ', flush=True)
        
        url, source = search_policy(ct, region)
        
        if url:
            print(f"✓ FOUND", flush=True)
            print(f"   URL: {url[:100]}", flush=True)
            print(f"   Src: {source}", flush=True)
        else:
            print(f"✗ NOT FOUND", flush=True)
        
        all_results.append({
            "title": ct,
            "search_keyword": ct,
            "url": url or "",
            "status": "found" if url else "not_found",
            "found_at": source or ""
        })
        
        time.sleep(1.2)  # Rate limiting
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    found = sum(1 for r in all_results if r["status"] == "found")
    print(f"\n{'='*60}", flush=True)
    print(f"Done! Found: {found}/{len(all_results)} ({100*found//len(all_results)}%)", flush=True)
    print(f"Saved to: {OUTPUT_FILE}", flush=True)


if __name__ == "__main__":
    main()
