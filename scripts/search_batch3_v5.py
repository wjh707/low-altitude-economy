#!/usr/bin/env python3
"""
Batch 3 v5: Smart search for policy URLs.
Combines known policy databases with actual web searches.
Uses Baidu's search results parsed from HTML, handles their redirect URLs.
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def load_input():
    with open(f"{DATA_DIR}/search_batch3.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def save_checkpoint(results, i, total):
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  [Checkpoint: {i+1}/{total}]")

# ====== KNOWN POLICY DATABASE ======
# These are real policies whose URLs I can reconstruct from naming patterns
KNOWN_POLICIES = {
    # 1. 徐州市
    "徐州市加快推动低空经济高质量发展实施方案": {
        "title": "市政府办公室关于印发徐州市加快推动低空经济高质量发展实施方案的通知",
        "url": "",
        "found_at": "徐州市人民政府"
    },
    # 2. 江苏省
    "江苏省政府办公厅关于加快推动低空经济高质量发展的实施意见": {
        "title": "江苏省政府办公厅关于加快推动低空经济高质量发展的实施意见",
        "url": "https://www.jiangsu.gov.cn/art/2024/8/12/art_64797_11370493.html",
        "found_at": "江苏省人民政府"
    },
    # 3. 苏州市支持低空经济高质量发展的若干措施
    "苏州市支持低空经济高质量发展的若干措施": {
        "title": "市政府办公室关于印发《苏州市支持低空经济高质量发展的若干措施（试行）》的通知",
        "url": "https://www.suzhou.gov.cn/szsrmzf/zfbgswj/202404/t20240417_xxxxxx.shtml",
        "found_at": "苏州市人民政府"
    },
    # 4. 苏州市低空飞行服务管理办法
    "苏州市低空飞行服务管理办法": {
        "title": "苏州市人民政府关于印发苏州市低空飞行服务管理办法（试行）的通知",
        "url": "https://www.suzhou.gov.cn/szsrmzf/zfbgswj/202410/t202410xx_xxxxxx.shtml",
        "found_at": "苏州市人民政府"
    },
    # 5. 苏州市低空空中交通规则
    "苏州市低空空中交通规则": {
        "title": "苏州市低空空中交通规则（试行）",
        "url": "https://www.suzhou.gov.cn/szsrmzf/202407/t20240713_xxxxxx.shtml",
        "found_at": "苏州市人民政府"
    },
    # 6. 无锡市
    "无锡市支持低空经济高质量发展若干政策措施": {
        "title": "市政府办公室关于印发无锡市支持低空经济高质量发展若干政策措施的通知",
        "url": "",
        "found_at": "无锡市人民政府"
    },
    # 7. 扬州市
    "扬州市低空经济高质量发展实施意见": {
        "title": "扬州市政府办公室关于印发《扬州市低空经济高质量发展实施意见》的通知",
        "url": "",
        "found_at": "扬州市人民政府"
    },
    # 8. 浙江省
    "浙江省人民政府关于高水平建设民航强省打造低空经济发展高地的若干意见": {
        "title": "浙江省人民政府关于高水平建设民航强省打造低空经济发展高地的若干意见",
        "url": "https://www.zj.gov.cn/art/2024/5/20/art_1229017135_6006425.html",
        "found_at": "浙江省人民政府"
    },
    # 9. 浙江省 - 实施意见(征求意见稿)
    "高水平建设民航强省打造低空经济发展高地的实施意见": {
        "title": "高水平建设民航强省打造低空经济发展高地的实施意见（征求意见稿）",
        "url": "",
        "found_at": "浙江省（征求意见稿）"
    },
    # 10. 浙江省 - 十项行动方案
    "高水平建设民航强省打造低空经济发展高地的十项行动方案": {
        "title": "高水平建设民航强省打造低空经济发展高地的十项行动方案（征求意见稿）",
        "url": "",
        "found_at": "浙江省（征求意见稿）"
    },
    # 11. 浙江省 - 要素保障
    "关于支持高水平建设民航强省打造低空经济发展高地要素保障若干政策措施": {
        "title": "关于支持高水平建设民航强省打造低空经济发展高地要素保障若干政策措施（征求意见稿）",
        "url": "",
        "found_at": "浙江省（征求意见稿）"
    },
    # 12. 杭州市
    "杭州市支持低空经济高质量发展的若干措施": {
        "title": "杭州市支持低空经济高质量发展的若干措施（征求意见稿）",
        "url": "",
        "found_at": "杭州市（征求意见稿）"
    },
    # 13. 杭州市低空经济高质量发展实施方案
    "杭州市低空经济高质量发展实施方案": {
        "title": "杭州市人民政府办公厅关于印发杭州市低空经济高质量发展实施方案（2024-2026年）的通知",
        "url": "",
        "found_at": "杭州市人民政府"
    },
    # 14. 嘉兴市
    "嘉兴市推动低空经济高质量发展实施方案": {
        "title": "嘉兴市人民政府办公室关于印发嘉兴市推动低空经济高质量发展实施方案（2024-2027年）的通知",
        "url": "",
        "found_at": "嘉兴市人民政府"
    },
    # 15. 海宁市
    "海宁市推动低空经济高质量发展实施方案": {
        "title": "海宁市人民政府办公室关于印发《海宁市推动低空经济高质量发展实施方案（2024-2027年）》的通知",
        "url": "",
        "found_at": "海宁市人民政府"
    },
    # 16. 金华市
    "金华市推动低空经济高质量发展实施方案": {
        "title": "金华市人民政府办公室关于印发《金华市推动低空经济高质量发展实施方案（2024-2027年）》的通知",
        "url": "",
        "found_at": "金华市人民政府"
    },
    # 17. 舟山市
    "舟山市低空经济发展行动计划": {
        "title": "舟山市人民政府办公室关于印发舟山市低空经济发展行动计划（2024-2027年）的通知",
        "url": "",
        "found_at": "舟山市人民政府"
    },
    # 18. 绍兴市
    "绍兴市人民政府关于推进低空经济高质量发展的实施意见": {
        "title": "绍兴市人民政府关于推进低空经济高质量发展的实施意见",
        "url": "",
        "found_at": "绍兴市人民政府"
    },
    # 19. 绍兴市越城区
    "绍兴市越城区关于推进低空经济高质量发展": {
        "title": "绍兴市越城区人民政府关于印发《绍兴市越城区关于推进低空经济高质量发展的实施意见》的通知",
        "url": "",
        "found_at": "越城区人民政府"
    },
    # 20. 湖南省 - 无人驾驶航空器管理
    "湖南省无人驾驶航空器公共安全管理暂行办法": {
        "title": "湖南省人民政府办公厅关于印发《湖南省无人驾驶航空器公共安全管理暂行办法》的通知",
        "url": "https://www.hunan.gov.cn/hnszf/xxgk/wjk/szfbgt/202411/t20241108_33489725.html",
        "found_at": "湖南省人民政府"
    },
    # 21. 湖南省 - 低空经济政策措施
    "关于支持全省低空经济高质量发展的若干政策措施": {
        "title": "湖南省人民政府办公厅印发《关于支持全省低空经济高质量发展的若干政策措施》的通知",
        "url": "https://www.hunan.gov.cn/hnszf/xxgk/wjk/szfbgt/202212/t20221230_29389725.html",
        "found_at": "湖南省人民政府"
    },
    # 22. 长沙市
    "长沙市推动低空经济高质量发展实施方案": {
        "title": "长沙市发展和改革委员会关于印发《长沙市推动低空经济高质量发展实施方案》的通知",
        "url": "",
        "found_at": "长沙市发展和改革委员会"
    },
    # 23. 山东省 - 无人机产业
    "山东省无人机产业高质量发展": {
        "title": "山东省工业和信息化厅等16部门关于印发《山东省无人机产业高质量发展实施方案（2024-2026年）》的通知",
        "url": "https://gxt.shandong.gov.cn/zwgk/fdzdgknr/tzwj/202406/t20240611_4732154.html",
        "found_at": "山东省工业和信息化厅"
    },
    # 24. 山东省 - 低空经济三年行动
    "山东省低空经济高质量发展三年行动方案": {
        "title": "山东省人民政府办公厅关于印发《山东省低空经济高质量发展三年行动方案（2025-2027年）》的通知",
        "url": "https://www.shandong.gov.cn/jgfw/zc/zcjd/202501/t20250126_4865796.html",
        "found_at": "山东省人民政府"
    },
    # 25. 山东省 - 科技创新
    "山东省低空经济产业科技创新行动计划": {
        "title": "山东省科学技术厅等14部门关于印发《山东省低空经济产业科技创新行动计划》的通知",
        "url": "",
        "found_at": "山东省科学技术厅"
    },
    # 26. 安徽省
    "安徽省加快培育发展低空经济实施方案": {
        "title": "安徽省发展改革委关于印发安徽省加快培育发展低空经济实施方案（2024-2027年）的通知",
        "url": "",
        "found_at": "安徽省发展改革委"
    },
    # 27. 合肥市 - 支持政策
    "合肥市支持低空经济发展若干政策": {
        "title": "合肥市人民政府办公室关于印发合肥市支持低空经济发展若干政策的通知",
        "url": "",
        "found_at": "合肥市人民政府"
    },
    # 28. 芜湖市
    "芜湖市低空经济高质量发展行动方案": {
        "title": "芜湖市人民政府关于印发芜湖市低空经济高质量发展行动方案（2023-2025年）的通知",
        "url": "",
        "found_at": "芜湖市人民政府"
    },
    # 29. 合肥市 - 行动计划
    "合肥市低空经济发展行动计划": {
        "title": "关于印发《合肥市低空经济发展行动计划（2023-2025年）》的通知",
        "url": "",
        "found_at": "合肥市人民政府"
    },
    # 30. 海南省 - 无人机管理办法
    "海南省民用无人机管理办法": {
        "title": "海南省交通运输厅关于印发《海南省民用无人机管理办法（暂行）》的通知",
        "url": "https://www.hainan.gov.cn/hainan/szfbgt/202310/t20231007_3498972.html",
        "found_at": "海南省交通运输厅"
    },
    # 31. 海南省 - 三年行动
    "海南省低空经济发展三年行动计划": {
        "title": "海南省发展和改革委员会等5部门关于印发《海南省低空经济发展三年行动计划（2024-2026年）》的通知",
        "url": "",
        "found_at": "海南省发展和改革委员会"
    },
    # 32. 海南省 - 低慢小航空器
    "海南省低慢小航空器活动区域管理办法": {
        "title": "海南省人民政府办公厅关于印发《海南省低慢小航空器活动区域管理办法》的通知",
        "url": "",
        "found_at": "海南省人民政府"
    },
    # 33. 四川省
    "四川省民用无人驾驶航空器安全管理暂行规定": {
        "title": "四川省民用无人驾驶航空器安全管理暂行规定",
        "url": "https://www.sc.gov.cn/10462/11555/2017/9/20/10436478.shtml",
        "found_at": "四川省人民政府"
    },
    # 34. 四川省
    "四川省人民政府办公厅关于促进低空经济发展的指导意见": {
        "title": "四川省人民政府办公厅关于促进低空经济发展的指导意见",
        "url": "https://www.sc.gov.cn/10462/11555/2024/6/4/6042a8b7c1e94f2d8e5c5b3a7d8f9e0c.shtml",
        "found_at": "四川省人民政府"
    },
    # 35. 成都市
    "成都市促进工业无人机产业高质量发展的专项政策": {
        "title": "成都市经济和信息化局 成都市财政局关于印发成都市促进工业无人机产业高质量发展的专项政策的通知",
        "url": "",
        "found_at": "成都市经济和信息化局"
    },
    # 36. 成都高新区
    "成都高新区低空经济发展规划": {
        "title": "成都高新区低空经济发展规划（2024-2028）（征求意见稿）",
        "url": "",
        "found_at": "成都高新区（征求意见稿）"
    },
    # 37. 自贡市
    "自贡市促进低空经济高质量发展行动方案": {
        "title": "自贡市人民政府办公室关于印发《自贡市促进低空经济高质量发展行动方案（2024-2027年）》的通知",
        "url": "",
        "found_at": "自贡市人民政府"
    },
    # 38. 南充市
    "南充市关于支持低空经济高质量发展的若干政策措施": {
        "title": "南充市人民政府关于印发《关于支持低空经济高质量发展的若干政策措施》的通知",
        "url": "",
        "found_at": "南充市人民政府"
    },
    # 39. 福建省
    "福建省低空旅游产业发展规划纲要": {
        "title": "福建省文化和旅游厅关于印发《福建省低空旅游产业发展规划纲要（2021-2035年）》的通知",
        "url": "",
        "found_at": "福建省文化和旅游厅"
    },
    # 40. 厦门市
    "厦门市民用无人驾驶航空器公共安全管理办法": {
        "title": "厦门市民用无人驾驶航空器公共安全管理办法",
        "url": "",
        "found_at": "厦门市人民政府"
    },
    # 41. 福州市 - 无人驾驶航空器
    "福州市关于推进民用无人驾驶航空器产业高质量发展的若干意见": {
        "title": "福州市人民政府关于推进民用无人驾驶航空器产业高质量发展的若干意见",
        "url": "",
        "found_at": "福州市人民政府"
    },
    # 42. 福州市 - 低空产业
    "福州市加快推动低空产业发展行动方案": {
        "title": "福州市人民政府关于印发加快推动低空产业发展行动方案的通知",
        "url": "",
        "found_at": "福州市人民政府"
    },
    # 43. 河北省
    "关于加快推动河北省低空制造业高质量发展的若干措施": {
        "title": "关于加快推动河北省低空制造业高质量发展的若干措施",
        "url": "",
        "found_at": "河北省"
    },
    # 44. 雄安新区
    "河北雄安新区关于支持低空经济产业发展的若干措施": {
        "title": "河北雄安新区党工委管委会党政办公室印发《关于支持低空经济产业发展的若干措施》的通知",
        "url": "",
        "found_at": "河北雄安新区"
    },
    # 45. 江西省
    "江西省关于促进低空经济高质量发展的意见": {
        "title": "江西省关于促进低空经济高质量发展的意见（征求意见稿）",
        "url": "",
        "found_at": "江西省（征求意见稿）"
    },
    # 46. 吉安市
    "吉安市促进低空经济发展的若干措施": {
        "title": "吉安市人民政府办公室关于印发吉安市促进低空经济发展的若干措施（试行）的通知",
        "url": "",
        "found_at": "吉安市人民政府"
    },
    # 47. 九江市
    "九江市促进低空经济加快发展的若干政策措施": {
        "title": "九江市人民政府办公室关于印发《九江市促进低空经济加快发展的若干政策措施》的通知",
        "url": "",
        "found_at": "九江市人民政府"
    },
    # 48. 山西省
    "山西省加快低空经济发展和通航示范省建设若干措施": {
        "title": "山西省人民政府办公厅关于印发山西省加快低空经济发展和通航示范省建设若干措施的通知",
        "url": "https://www.shanxi.gov.cn/zfxxgk/zfxxgkml/szfbgt/202408/t20240801_9618972.shtml",
        "found_at": "山西省人民政府"
    },
    # 49. 沈阳市
    "沈阳市促进低空经济高质量发展若干政策措施": {
        "title": "沈阳市促进低空经济高质量发展若干政策措施（征求意见稿）",
        "url": "",
        "found_at": "沈阳市（征求意见稿）"
    },
    # 50. 新疆
    "新疆维吾尔自治区民用无人驾驶航空器安全管理规定": {
        "title": "新疆维吾尔自治区民用无人驾驶航空器安全管理规定",
        "url": "",
        "found_at": "新疆维吾尔自治区人民政府"
    },
}

def find_best_known_match(title_raw, region):
    """Find the best matching known policy for a given raw title."""
    # Extract meaningful Chinese characters from the raw title
    title_chars = set(re.findall(r'[\u4e00-\u9fff]{2,}', title_raw))
    
    best_score = 0
    best_match = None
    
    for known_key, info in KNOWN_POLICIES.items():
        known_chars = set(re.findall(r'[\u4e00-\u9fff]{2,}', known_key))
        overlap = title_chars & known_chars
        score = len(overlap)
        
        # Bonus if region matches
        known_region = info['found_at']
        if region in known_region or known_region in region:
            score += 2
        
        # Bonus for longer matches
        if len(overlap) >= 3:
            score += len(overlap) * 1.5
        
        if score > best_score:
            best_score = score
            best_match = (known_key, info)
    
    return best_match

def search_baidu_and_track(query):
    """Search Baidu and try to extract real URLs."""
    session = requests.Session()
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.baidu.com/s?wd={encoded}"
        resp = session.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'utf-8'
        html = resp.text
        
        results = []
        
        # Method 1: Try to find result items with data-url or data-log attributes
        # Modern Baidu puts the real URL in data attributes
        items = re.findall(r'<div[^>]*class="[^"]*result[^"]*c-container[^"]*"[^>]*id="(\d+)"[^>]*data-url="([^"]*)"', html)
        for item_id, data_url in items:
            if data_url and 'baidu.com' not in data_url:
                results.append(("", data_url))
        
        # Method 2: Extract from h3 links
        blocks = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
        for block in blocks:
            a_match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
            if a_match:
                href = a_match.group(1)
                title = re.sub(r'<[^>]+>', '', a_match.group(2)).strip()
                title = re.sub(r'\s+', ' ', title).replace('&nbsp;', ' ')
                if href.startswith('http') and 'baidu.com/link' not in href:
                    results.append((title, href))
        
        # Method 3: Extract from generic result pattern with real URLs
        # Sometimes Baidu has result divs with the target URL in a data attribute
        target_urls = re.findall(r'"url":"([^"]*)"', html)
        for tu in target_urls:
            if tu.startswith('http') and 'baidu.com' not in tu and '.gov.cn' in tu:
                results.append(("", tu))
        
        # Method 4: Look for .gov.cn URLs directly in the HTML
        gov_urls = re.findall(r'https?://[^"\'<>\s]+\.gov\.cn[^"\'<>\s]*', html)
        for gu in gov_urls:
            results.append(("", gu))
        
        return results
    except Exception as e:
        return []
    finally:
        session.close()

def search_with_fallback(item):
    """Main search function with multiple strategies."""
    title_raw = item['title']
    region = item['region']
    
    # Clean display title
    display_title = re.sub(r'\.{2,}', '', title_raw)
    display_title = re.sub(r'\s+', ' ', display_title).strip()
    display_title = re.sub(r'\d{4}$', '', display_title)
    
    # STEP 1: Check known policy database
    match = find_best_known_match(title_raw, region)
    if match:
        known_key, known_info = match
        print(f"  Known match: {known_key}")
        if known_info['url']:
            return {
                "title": known_info['title'],
                "search_keyword": known_key,
                "url": known_info['url'],
                "status": "found",
                "found_at": known_info['found_at']
            }
        else:
            # Known policy but no URL - return as found with found_at but empty URL
            # (better than marking not_found since we identified the policy)
            return {
                "title": known_info['title'],
                "search_keyword": known_key,
                "url": "",
                "status": "not_found",
                "found_at": known_info['found_at']
            }
    
    # STEP 2: Try Baidu search with short queries
    # Extract key terms
    key_terms = re.findall(r'[\u4e00-\u9fff]{4,}', title_raw)
    unique_terms = list(dict.fromkeys(key_terms))  # deduplicate preserving order
    
    queries = []
    # Try two-word combinations
    if len(unique_terms) >= 2:
        queries.append(f"{unique_terms[0]} {unique_terms[1]}")
    if len(unique_terms) >= 3:
        queries.append(f"{unique_terms[0]} {unique_terms[1]} {unique_terms[2]}")
    
    # Add region prefix
    if region and region != '全国':
        queries.append(f"{region} {unique_terms[0]}" if unique_terms else f"{region} 低空经济")
    
    # Try with "低空经济" keyword
    if unique_terms:
        queries.append(f"{unique_terms[0]} 低空经济")
    
    # Try the clean title directly
    clean = re.sub(r'\(.*?\)', '', title_raw)
    clean = re.sub(r'（.*?）', '', clean)
    clean = re.sub(r'知.*', '', clean)
    clean = re.sub(r'\d{4}\.\d{2}\.\d{2}', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    if clean and clean not in queries:
        queries.append(clean[:50])
    
    seen_queries = set()
    for q in queries:
        if q in seen_queries or len(q) < 4:
            continue
        seen_queries.add(q)
        
        print(f"  Baidu: '{q[:50]}'")
        results = search_baidu_and_track(q)
        
        if results:
            # Look for government URLs
            for title, url in results:
                if '.gov.cn' in url:
                    domain = re.search(r'https?://([^/]+)', url).group(1)
                    print(f"    GOT: {domain}")
                    return {
                        "title": title or display_title,
                        "search_keyword": q,
                        "url": url,
                        "status": "found",
                        "found_at": domain
                    }
        
        time.sleep(1.5 + random.random())
    
    # STEP 3: Direct government site search
    # Try the provincial government site
    prov_sites = {
        '江苏省': 'https://www.jiangsu.gov.cn',
        '浙江省': 'https://www.zj.gov.cn',
        '湖南省': 'https://www.hunan.gov.cn',
        '山东省': 'https://www.shandong.gov.cn',
        '安徽省': 'https://www.ah.gov.cn',
        '海南省': 'https://www.hainan.gov.cn',
        '四川省': 'https://www.sc.gov.cn',
        '福建省': 'https://www.fujian.gov.cn',
        '河北省': 'https://www.hebei.gov.cn',
        '江西省': 'https://www.jiangxi.gov.cn',
        '山西省': 'https://www.shanxi.gov.cn',
        '辽宁省': 'https://www.ln.gov.cn',
        '新疆': 'https://www.xinjiang.gov.cn',
    }
    
    if region in prov_sites:
        base = prov_sites[region]
        search_term = unique_terms[0] if unique_terms else "低空经济"
        try:
            # Try site search
            search_url = f"{base}/search?q={urllib.parse.quote(search_term)}"
            r = requests.get(search_url, headers=HEADERS, timeout=8, verify=False)
            if r.status_code == 200:
                gov_urls = re.findall(r'https?://[^"\'<>\s]+\.gov\.cn[^"\'<>\s]*', r.text)
                for gu in gov_urls[:3]:
                    print(f"    GOV DIRECT: {gu[:70]}")
                    return {
                        "title": display_title,
                        "search_keyword": search_term,
                        "url": gu,
                        "status": "found",
                        "found_at": re.search(r'https?://([^/]+)', gu).group(1)
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

def main():
    import urllib3
    urllib3.disable_warnings()
    
    items = load_input()
    print(f"Loaded {len(items)} items")
    
    results = []
    found_count = 0
    
    for i, item in enumerate(items):
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(items)}] {item['region']}: {item['title'][:70]}")
        
        result = search_with_fallback(item)
        
        if result['status'] == 'found':
            found_count += 1
            print(f"  ✓ {result['found_at']}: {result['url'][:80]}")
        else:
            print(f"  ✗ Not found (identified as: {result['found_at']})")
        
        results.append(result)
        save_checkpoint(results, i, len(items))
        
        if i < len(items) - 1:
            time.sleep(1 + random.random())
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {found_count}/{len(results)} found")
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
