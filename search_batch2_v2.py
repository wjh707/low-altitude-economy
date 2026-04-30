#!/opt/anaconda3/bin/python3.12
"""
Search batch2 policies using Bing search to find official government URLs.
Fixed version - simpler relevance checking, better query construction.
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
    for d in ['gov.cn', 'caac.gov.cn', 'pkulaw.com', 'std.samr.gov.cn', 'npc.gov.cn']:
        if d in combined:
            return True
    return False

def get_source_name(url, cite):
    """Get readable source name."""
    c = (url + ' ' + cite).lower()
    
    if 'caac.gov.cn' in c:
        return "中国民用航空局"
    if 'www.gov.cn' in c or 'gov.cn' in c.lower():
        # Try to identify specific government
        if 'npc.gov.cn' in c: return "国家法律法规数据库"
        if 'beijing.gov.cn' in c or 'bj' in c.lower() and 'gov.cn' in c: return "北京市政府网站"
        if 'shanghai.gov.cn' in c or 'sh.gov.cn' in c: return "上海市政府网站"
        if 'gd.gov.cn' in c: return "广东省政府网站"
        if 'sz.gov.cn' in c: return "深圳市政府网站"
        if 'gz.gov.cn' in c: return "广州市政府网站"
        if 'nj.gov.cn' in c: return "南京市政府网站"
        if 'suzhou.gov.cn' in c: return "苏州市政府网站"
        if 'wuxi.gov.cn' in c: return "无锡市政府网站"
        if 'changzhou.gov.cn' in c: return "常州市政府网站"
        if 'nantong.gov.cn' in c: return "南通市政府网站"
        if 'zhuhai.gov.cn' in c or 'zhrd.gov.cn' in c: return "珠海市政府网站"
        if 'huizhou.gov.cn' in c: return "惠州市政府网站"
        if 'zhongshan.gov.cn' in c: return "中山市政府网站"
        if 'dongguan.gov.cn' in c: return "东莞市政府网站"
        if 'foshan.gov.cn' in c: return "佛山市政府网站"
        if 'maoming.gov.cn' in c: return "茂名市政府网站"
        if 'zhanjiang.gov.cn' in c: return "湛江市政府网站"
        if 'tianjin.gov.cn' in c or 'tj.gov.cn' in c: return "天津市政府网站"
        if 'chongqing.gov.cn' in c or 'cq.gov.cn' in c: return "重庆市政府网站"
        if 'hunan.gov.cn' in c or 'hn.gov.cn' in c: return "湖南省政府网站"
        if 'zhejiang.gov.cn' in c or 'zj.gov.cn' in c: return "浙江省政府网站"
        if 'jiangsu.gov.cn' in c or 'js.gov.cn' in c: return "江苏省政府网站"
        if 'guangdong.gov.cn' in c: return "广东省政府网站"
        # Check common subdomains
        if 'rd.' in c and 'gov.cn' in c: return "地方人大网站"
        if 'jtys.' in c and 'sz.gov.cn' in c: return "深圳市交通运输局"
        if 'sf.' in c and 'sz.gov.cn' in c: return "深圳市司法局"
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
    t = re.sub(r'\s*[\.\s]*[\d]+$', '', t).strip()
    return t.strip()

def search_with_queries(queries, clean_title):
    """Try multiple queries and return best result."""
    for q in queries:
        if len(q) < 5:
            continue
        results = bing_search(q)
        if not results:
            continue
        
        # First pass: authoritative (.gov.cn) results
        for r in results:
            if is_gov_result(r['href'], r['title'], r['cite']):
                return r['href'], get_source_name(r['href'], r['cite'])
        
        # Second pass: any result with gov.cn or caac.gov.cn
        for r in results:
            if 'gov.cn' in r['href'].lower() or 'caac.gov.cn' in r['href'].lower():
                return r['href'], get_source_name(r['href'], r['cite'])
    
    return None, None


def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    print(f"Loaded {len(items)} items", flush=True)
    all_results = []
    
    for idx, item in enumerate(items):
        raw = item["title"]
        region = item.get("region", "")
        ct = clean_title(raw)
        
        # Build targeted queries based on clean_title and region
        queries = []
        
        # Strategy 1: Exact policy name + site restriction
        # Extract concise policy name
        name = ct
        # Remove date parentheses
        name_no_date = re.sub(r'[（(]\d{4}[^）)]*[）)]', '', ct).strip()
        name_no_date = re.sub(r'\s+', ' ', name_no_date).strip()
        
        # Strategy 2: Shorter core name (remove preamble like 关于印发 etc)
        core = name_no_date
        core = re.sub(r'^(关于印发《|关于印发|关于联合印发《|关于联合印发|关于发布《|关于修订《|印发《)', '', core)
        core = re.sub(r'》的通知$|》$|的通知$|（试行）$', '', core).strip()
        
        # Build different query strategies
        # 1. Short, concise query
        if region and region != '全国':
            queries.append(f"{name_no_date[:60]} {region}")
        
        # 2. Core name
        if core and core != name_no_date:
            queries.append(core[:60])
        
        # 3. Just the unique identifying part
        queries.append(name_no_date[:60])
        
        # 4. Remove all parenthetical content for broader match
        bare = re.sub(r'[（(][^）)]*[）)]', '', name_no_date).strip()
        if bare != name_no_date:
            queries.append(bare[:60])
        
        # 5. With site operator for known government domains
        if '湖南' in ct: queries.append(f"湖南省通用航空条例 site:hunan.gov.cn")
        if '浙江' in ct and '无人驾驶' in ct: queries.append(f"浙江省无人驾驶航空器公共安全管理规定 site:zj.gov.cn")
        if '深圳' in ct and '低空经济' in ct and '促进条例' in ct: queries.append(f"深圳经济特区低空经济产业促进条例 site:sz.gov.cn")
        if '珠海' in ct and '低空交通' in ct: queries.append(f"珠海经济特区低空交通建设管理条例 site:zhuhai.gov.cn")
        if '广州' in ct and '低空经济' in ct and '条例' in ct: queries.append(f"广州市低空经济发展条例 site:gz.gov.cn")
        if '北京' in ct and '低空经济' in ct and '行动方案' in ct: queries.append(f"北京市促进低空经济产业高质量发展行动方案 site:beijing.gov.cn")
        if '上海' in ct and '低空经济' in ct and '行动方案' in ct: queries.append(f"上海市低空经济产业高质量发展行动方案 site:shanghai.gov.cn")
        if '广东' in ct and '推动低空经济' in ct: queries.append(f"广东省推动低空经济高质量发展行动方案 site:gd.gov.cn")
        if '广州' in ct and '低空经济发展实施方案' in ct: queries.append(f"广州市低空经济发展实施方案 site:gz.gov.cn")
        if '深圳' in ct and '支持低空经济' in ct and '若干措施' in ct: queries.append(f"深圳市支持低空经济高质量发展的若干措施 site:sz.gov.cn")
        if '广州' in ct and '低空经济高质量发展若干措施' in ct: queries.append(f"广州市推动低空经济高质量发展若干措施 site:gz.gov.cn")
        if '重庆' in ct and '推动低空空域管理改革' in ct: queries.append(f"重庆市推动低空空域管理改革促进低空经济高质量发展 site:cq.gov.cn")
        if '江苏' in ct and '航空航天' in ct: queries.append(f"江苏省航空航天产业发展三年行动计划 site:jiangsu.gov.cn")
        if '南京' in ct and '低空经济高质量发展实施方案' in ct: queries.append(f"南京市促进低空经济高质量发展实施方案 site:nj.gov.cn")
        if '南京' in ct and '低空飞行服务' in ct: queries.append(f"南京市低空飞行服务保障体系建设行动计划 site:nj.gov.cn")
        if '苏州' in ct and '低空经济高质量发展实施方案' in ct: queries.append(f"苏州市低空经济高质量发展实施方案 site:suzhou.gov.cn")
        if '苏州工业园区' in ct: queries.append(f"苏州工业园区低空经济高质量发展行动计划 site:suzhou.gov.cn")
        if '无锡' in ct: queries.append(f"无锡市低空经济高质量发展三年行动方案 site:wuxi.gov.cn")
        if '常州' in ct: queries.append(f"常州市低空经济高质量发展三年行动方案 site:changzhou.gov.cn")
        if '南通' in ct: queries.append(f"南通市低空经济高质量发展行动方案 site:nantong.gov.cn")
        if '天津' in ct and '宁河区' in ct and '行动' in ct: queries.append(f"天津市宁河区低空经济高质量发展行动方案 site:tj.gov.cn")
        if '宁河区' in ct and '八条' in ct: queries.append(f"宁河区促进低空经济高质量发展的八条措施 site:tj.gov.cn")
        if '东疆' in ct: queries.append(f"天津东疆综合保税区 低空经济 若干措施 site:tj.gov.cn")
        if '重庆' in ct and '无人驾驶' in ct: queries.append(f"重庆市民用无人驾驶航空器公共安全管理办法 site:cq.gov.cn")
        if '梁平' in ct: queries.append(f"梁平区支持低空经济高质量发展十条激励措施 site:cq.gov.cn")
        if '深圳' in ct and '民用微轻型无人机' in ct: queries.append(f"深圳市民用微轻型无人机管理暂行办法 site:sz.gov.cn")
        
        # Remove duplicates
        seen = set()
        unique_queries = []
        for q in queries:
            q_norm = q.strip().lower()
            if q_norm and q_norm not in seen and len(q_norm) >= 5:
                seen.add(q_norm)
                unique_queries.append(q.strip())
        
        msg = f"[{idx+1}/{len(items)}] [{region}] {ct[:60]}..."
        print(msg, end=' ', flush=True)
        
        url, source = search_with_queries(unique_queries, ct)
        
        if url:
            print(f"✓ FOUND", flush=True)
            print(f"   URL: {url[:110]}", flush=True)
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
        
        time.sleep(1.2)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    found = sum(1 for r in all_results if r["status"] == "found")
    print(f"\n{'='*60}", flush=True)
    print(f"Done! Found: {found}/{len(all_results)} ({100*found//len(all_results)}%)", flush=True)
    print(f"Saved to: {OUTPUT_FILE}", flush=True)


if __name__ == "__main__":
    main()
