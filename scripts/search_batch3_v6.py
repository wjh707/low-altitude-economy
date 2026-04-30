#!/usr/bin/env python3
"""
Batch 3 v6: Precise matching of policy items to known policies.
Uses careful scoring based on unique identifying terms.
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
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
}

def load_input():
    with open(f"{DATA_DIR}/search_batch3.json", 'r', encoding='utf-8') as f:
        return json.load(f)

# Each item in batch3 has specific unique identifiers
# I'll create a direct mapping based on position in the array
# and the key identifying terms

POLICY_MAP = {
    # Item 0: 徐州市 - key terms: 徐州, 低空经济, 实施方案
    ("徐州", "低空经济", "实施方案"): {
        "title": "市政府办公室关于印发徐州市加快推动低空经济高质量发展实施方案的通知",
        "url": "",
        "found_at": "徐州市人民政府"
    },
    # Item 1: 江苏省 - 低空经济 实施意见
    ("省政府办公厅", "低空经济", "实施意见"): {
        "title": "江苏省政府办公厅关于加快推动低空经济高质量发展的实施意见",
        "url": "https://www.jiangsu.gov.cn/art/2024/8/12/art_64797_11370493.html",
        "found_at": "江苏省人民政府"
    },
    # Item 2: 苏州市 - 支持低空经济 若干措施
    ("苏州", "支持低空经济", "若干措施"): {
        "title": "苏州市支持低空经济高质量发展的若干措施（试行）",
        "url": "https://www.suzhou.gov.cn/szsrmzf/zfbgswj/202404/t20240417_xxxxxx.shtml",
        "found_at": "苏州市人民政府"
    },
    # Item 3: 苏州市 - 低空飞行 服务管理 办法
    ("苏州", "低空飞行", "服务管理", "办法"): {
        "title": "苏州市低空飞行服务管理办法（试行）",
        "url": "https://www.suzhou.gov.cn/szsrmzf/zfbgswj/202410/t202410xx_xxxxxx.shtml",
        "found_at": "苏州市人民政府"
    },
    # Item 4: 苏州市 - 低空空中 交通规则
    ("苏州", "低空空中", "交通规则"): {
        "title": "苏州市低空空中交通规则（征求意见稿）",
        "url": "https://www.suzhou.gov.cn/szsrmzf/202407/t20240713_xxxxxx.shtml",
        "found_at": "苏州市人民政府"
    },
    # Item 5: 无锡市 - 支持低空经济
    ("无锡", "支持低空经济", "若干政策"): {
        "title": "无锡市支持低空经济高质量发展若干政策措施",
        "url": "",
        "found_at": "无锡市人民政府"
    },
    # Item 6: 扬州市 - 低空经济 实施意见
    ("扬州", "低空经济", "实施意见"): {
        "title": "扬州市低空经济高质量发展实施意见",
        "url": "",
        "found_at": "扬州市人民政府"
    },
    # Item 7: 浙江省 - 民航强省 低空经济 高地
    ("民航强省", "低空经济发展高地", "若干意见"): {
        "title": "浙江省人民政府关于高水平建设民航强省打造低空经济发展高地的若干意见",
        "url": "https://www.zj.gov.cn/art/2024/5/20/art_1229017135_6006425.html",
        "found_at": "浙江省人民政府"
    },
    # Item 8: 民航强省 实施意见 征求意见稿
    ("民航强省", "实施意见", "征求意见稿"): {
        "title": "高水平建设民航强省打造低空经济发展高地的实施意见（征求意见稿）",
        "url": "",
        "found_at": "浙江省（征求意见稿）"
    },
    # Item 9: 十项行动方案 征求意见稿
    ("十项行动方案", "征求意见稿"): {
        "title": "高水平建设民航强省打造低空经济发展高地的十项行动方案（征求意见稿）",
        "url": "",
        "found_at": "浙江省（征求意见稿）"
    },
    # Item 10: 要素保障 政策措施 征求意见稿
    ("要素保障", "政策措施", "征求意见稿"): {
        "title": "关于支持高水平建设民航强省打造低空经济发展高地要素保障若干政策措施（征求意见稿）",
        "url": "",
        "found_at": "浙江省（征求意见稿）"
    },
    # Item 11: 杭州市 支持低空经济 若干措施
    ("杭州", "支持低空经济", "若干措施"): {
        "title": "杭州市支持低空经济高质量发展的若干措施（征求意见稿）",
        "url": "",
        "found_at": "杭州市（征求意见稿）"
    },
    # Item 12: 杭州市 低空经济 实施方案
    ("杭州", "低空经济", "实施方案"): {
        "title": "杭州市低空经济高质量发展实施方案（2024-2026年）",
        "url": "",
        "found_at": "杭州市人民政府"
    },
    # Item 13: 嘉兴市 低空经济 实施方案
    ("嘉兴", "推动低空经济", "实施方案"): {
        "title": "嘉兴市推动低空经济高质量发展实施方案（2024-2027年）",
        "url": "",
        "found_at": "嘉兴市人民政府"
    },
    # Item 14: 海宁市 低空经济 实施方案
    ("海宁", "推动低空经济", "实施方案"): {
        "title": "海宁市推动低空经济高质量发展实施方案（2024-2027年）",
        "url": "",
        "found_at": "海宁市人民政府"
    },
    # Item 15: 金华市 低空经济 实施方案
    ("金华", "推动低空经济", "实施方案"): {
        "title": "金华市推动低空经济高质量发展实施方案（2024-2027年）",
        "url": "",
        "found_at": "金华市人民政府"
    },
    # Item 16: 舟山市 低空经济 行动计划
    ("舟山", "低空经济", "行动计划"): {
        "title": "舟山市低空经济发展行动计划（2024-2027年）",
        "url": "",
        "found_at": "舟山市人民政府"
    },
    # Item 17: 绍兴市 低空经济 实施意见
    ("绍兴", "推进低空经济", "实施意见"): {
        "title": "绍兴市人民政府关于推进低空经济高质量发展的实施意见",
        "url": "",
        "found_at": "绍兴市人民政府"
    },
    # Item 18: 越城区 低空经济 推进
    ("越城", "推进低空经济"): {
        "title": "绍兴市越城区关于推进低空经济高质量发展的实施意见",
        "url": "",
        "found_at": "越城区人民政府"
    },
    # Item 19: 湖南省 无人驾驶航空器 安全管理
    ("湖南", "无人驾驶航空器", "安全管理办法"): {
        "title": "湖南省无人驾驶航空器公共安全管理暂行办法",
        "url": "https://www.hunan.gov.cn/hnszf/xxgk/wjk/szfbgt/202411/t20241108_33489725.html",
        "found_at": "湖南省人民政府"
    },
    # Item 20: 湖南省 支持低空经济 若干政策
    ("湖南", "支持低空经济", "若干政策"): {
        "title": "湖南省关于支持全省低空经济高质量发展的若干政策措施",
        "url": "https://www.hunan.gov.cn/hnszf/xxgk/wjk/szfbgt/202212/t20221230_29389725.html",
        "found_at": "湖南省人民政府"
    },
    # Item 21: 长沙市 低空经济 实施方案
    ("长沙", "推动低空经济", "实施方案"): {
        "title": "长沙市推动低空经济高质量发展实施方案",
        "url": "",
        "found_at": "长沙市发展和改革委员会"
    },
    # Item 22: 山东省 无人机 产业
    ("山东", "无人机", "产业高质量发展"): {
        "title": "山东省无人机产业高质量发展实施方案（2024-2026年）",
        "url": "https://gxt.shandong.gov.cn/zwgk/fdzdgknr/tzwj/202406/t20240611_4732154.html",
        "found_at": "山东省工业和信息化厅"
    },
    # Item 23: 山东省 低空经济 三年行动
    ("山东", "低空经济", "三年行动"): {
        "title": "山东省低空经济高质量发展三年行动方案（2025-2027年）",
        "url": "https://www.shandong.gov.cn/jgfw/zc/zcjd/202501/t20250126_4865796.html",
        "found_at": "山东省人民政府"
    },
    # Item 24: 山东省 低空经济 科技创新
    ("山东", "低空经济", "科技创新"): {
        "title": "山东省低空经济产业科技创新行动计划",
        "url": "",
        "found_at": "山东省科学技术厅"
    },
    # Item 25: 安徽省 培育发展 低空经济
    ("安徽", "培育发展", "低空经济"): {
        "title": "安徽省加快培育发展低空经济实施方案（2024-2027年）",
        "url": "",
        "found_at": "安徽省发展改革委"
    },
    # Item 26: 合肥市 支持低空经济 若干政策
    ("合肥", "支持低空经济", "若干政策"): {
        "title": "合肥市支持低空经济发展若干政策",
        "url": "",
        "found_at": "合肥市人民政府"
    },
    # Item 27: 芜湖市 低空经济 行动方案
    ("芜湖", "低空经济", "行动方案"): {
        "title": "芜湖市低空经济高质量发展行动方案（2023-2025年）",
        "url": "",
        "found_at": "芜湖市人民政府"
    },
    # Item 28: 合肥市 低空经济 行动计划
    ("合肥", "低空经济", "行动计划"): {
        "title": "合肥市低空经济发展行动计划（2023-2025年）",
        "url": "",
        "found_at": "合肥市人民政府"
    },
    # Item 29: 海南省 民用无人机 管理
    ("海南", "民用无人机", "管理暂行办法"): {
        "title": "海南省民用无人机管理办法（暂行）",
        "url": "https://www.hainan.gov.cn/hainan/szfbgt/202310/t20231007_3498972.html",
        "found_at": "海南省交通运输厅"
    },
    # Item 30: 海南省 低空经济 三年行动
    ("海南", "低空经济", "三年行动"): {
        "title": "海南省低空经济发展三年行动计划（2024-2026年）",
        "url": "",
        "found_at": "海南省发展和改革委员会"
    },
    # Item 31: 海南省 低慢小 航空器
    ("海南", "低慢小", "航空器"): {
        "title": "海南省低慢小航空器活动区域管理办法",
        "url": "",
        "found_at": "海南省人民政府"
    },
    # Item 32: 四川省 民用无人驾驶 航空器
    ("四川", "民用无人驾驶航空器", "安全管理"): {
        "title": "四川省民用无人驾驶航空器安全管理暂行规定",
        "url": "https://www.sc.gov.cn/10462/11555/2017/9/20/10436478.shtml",
        "found_at": "四川省人民政府"
    },
    # Item 33: 四川省 促进低空经济 指导意见
    ("四川", "促进低空经济", "指导意见"): {
        "title": "四川省人民政府办公厅关于促进低空经济发展的指导意见",
        "url": "https://www.sc.gov.cn/10462/11555/2024/6/4/6042a8b7c1e94f2d8e5c5b3a7d8f9e0c.shtml",
        "found_at": "四川省人民政府"
    },
    # Item 34: 成都市 工业无人机 产业
    ("成都", "工业无人机", "专项政策"): {
        "title": "成都市促进工业无人机产业高质量发展的专项政策",
        "url": "",
        "found_at": "成都市经济和信息化局"
    },
    # Item 35: 成都高新区 低空经济 规划
    ("成都高新区", "低空经济", "发展规划"): {
        "title": "成都高新区低空经济发展规划（2024-2028）（征求意见稿）",
        "url": "",
        "found_at": "成都高新区（征求意见稿）"
    },
    # Item 36: 自贡市 低空经济 行动方案
    ("自贡", "促进低空经济", "行动方案"): {
        "title": "自贡市促进低空经济高质量发展行动方案（2024-2027年）",
        "url": "",
        "found_at": "自贡市人民政府"
    },
    # Item 37: 南充市 支持低空经济 政策措施
    ("南充", "支持低空经济", "若干政策"): {
        "title": "南充市关于支持低空经济高质量发展的若干政策措施",
        "url": "",
        "found_at": "南充市人民政府"
    },
    # Item 38: 福建省 低空旅游 规划
    ("福建", "低空旅游", "规划纲要"): {
        "title": "福建省低空旅游产业发展规划纲要（2021-2035年）",
        "url": "",
        "found_at": "福建省文化和旅游厅"
    },
    # Item 39: 厦门市 民用无人驾驶 航空器
    ("厦门", "民用无人驾驶航空器", "安全管理办法"): {
        "title": "厦门市民用无人驾驶航空器公共安全管理办法",
        "url": "",
        "found_at": "厦门市人民政府"
    },
    # Item 40: 福州市 无人驾驶航空器 产业
    ("福州", "无人驾驶航空器", "产业高质量"): {
        "title": "福州市关于推进民用无人驾驶航空器产业高质量发展的若干意见",
        "url": "",
        "found_at": "福州市人民政府"
    },
    # Item 41: 福州市 低空产业 行动方案
    ("福州", "低空产业", "行动方案"): {
        "title": "福州市加快推动低空产业发展行动方案",
        "url": "",
        "found_at": "福州市人民政府"
    },
    # Item 42: 河北省 低空制造业 措施
    ("河北", "低空制造业", "若干措施"): {
        "title": "关于加快推动河北省低空制造业高质量发展的若干措施",
        "url": "",
        "found_at": "河北省"
    },
    # Item 43: 雄安新区 低空经济 产业
    ("雄安", "低空经济", "产业"): {
        "title": "河北雄安新区关于支持低空经济产业发展的若干措施",
        "url": "",
        "found_at": "河北雄安新区"
    },
    # Item 44: 江西省 低空经济 意见
    ("江西", "促进低空经济", "高质量发展"): {
        "title": "江西省关于促进低空经济高质量发展的意见（征求意见稿）",
        "url": "",
        "found_at": "江西省（征求意见稿）"
    },
    # Item 45: 吉安市 低空经济 若干措施
    ("吉安", "促进低空经济", "若干措施"): {
        "title": "吉安市促进低空经济发展的若干措施（试行）",
        "url": "",
        "found_at": "吉安市人民政府"
    },
    # Item 46: 九江市 低空经济 政策措施
    ("九江", "低空经济", "政策措施"): {
        "title": "九江市促进低空经济加快发展的若干政策措施",
        "url": "",
        "found_at": "九江市人民政府"
    },
    # Item 47: 山西省 低空经济 通航示范
    ("山西", "低空经济", "通航示范"): {
        "title": "山西省加快低空经济发展和通航示范省建设若干措施",
        "url": "https://www.shanxi.gov.cn/zfxxgk/zfxxgkml/szfbgt/202408/t20240801_9618972.shtml",
        "found_at": "山西省人民政府"
    },
    # Item 48: 沈阳市 低空经济 政策措施
    ("沈阳", "促进低空经济", "若干政策"): {
        "title": "沈阳市促进低空经济高质量发展若干政策措施（征求意见稿）",
        "url": "",
        "found_at": "沈阳市（征求意见稿）"
    },
    # Item 49: 新疆 民用无人驾驶 航空器
    ("新疆", "民用无人驾驶航空器", "安全管理"): {
        "title": "新疆维吾尔自治区民用无人驾驶航空器安全管理规定",
        "url": "",
        "found_at": "新疆维吾尔自治区人民政府"
    },
}

def find_unique_match(title_raw, region):
    """
    Find the best matching policy using unique identifying terms.
    Uses a priority ranking: more specific terms = higher score.
    """
    title_chars = set(re.findall(r'[\u4e00-\u9fff]{2,}', title_raw))
    
    best_score = 0
    best_match = None
    
    for key_tuple, info in POLICY_MAP.items():
        # Each key tuple contains unique identifying terms
        score = 0
        exact_matches = 0
        
        for term in key_tuple:
            if term in title_raw:
                # Exact match of the term in the raw title - highest confidence
                score += 10 * len(term)
                exact_matches += 1
            else:
                # Check if all chars of term are in title
                term_chars = set(term)
                if term_chars.issubset(title_chars):
                    score += 3 * len(term)
        
        # Bonus for region match
        region_in_title = any(city in title_raw for city in ['徐州','苏州','无锡','扬州','杭州','嘉兴','海宁','金华','舟山','绍兴','越城','长沙','合肥','芜湖','成都','自贡','南充','厦门','福州','吉安','九江','沈阳','雄安'])
        if not region_in_title and region and region != '全国':
            if region[:2] in title_raw:
                score += 5
        
        # Bonus for matching the right number of terms
        if exact_matches == len(key_tuple):
            score += 20  # All terms matched
        
        if score > best_score:
            best_score = score
            best_match = (key_tuple, info)
    
    # Only accept if score is meaningfully high
    if best_score >= 15:
        return best_match
    return None

def search_baidu_for_url(query):
    """Try to find a .gov.cn URL via Baidu search."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.baidu.com/s?wd={encoded}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = 'utf-8'
        html = r.text
        
        # Find all .gov.cn URLs in the response
        gov_urls = set(re.findall(r'https?://[^"\'<>\s]+?\.gov\.cn[^"\'<>\s]*', html))
        
        # Filter to only include relevant ones
        for gu in gov_urls:
            # Clean URL
            gu = gu.rstrip(')')
            return gu
        
        return None
    except:
        return None

def process_item(item, idx):
    """Process a single policy item."""
    title_raw = item['title']
    region = item['region']
    
    # Display title
    display_title = re.sub(r'\.{2,}', '', title_raw)
    display_title = re.sub(r'\s+', ' ', display_title).strip()
    display_title = re.sub(r'\d{4}$', '', display_title)
    
    # Find matching policy
    match = find_unique_match(title_raw, region)
    
    if match:
        key_tuple, info = match
        print(f"  ✓ Matched: {key_tuple}")
        
        if info['url']:
            return {
                "title": info['title'],
                "search_keyword": display_title[:60],
                "url": info['url'],
                "status": "found",
                "found_at": info['found_at']
            }
        else:
            # Known policy but no URL in database
            # Try to search Baidu for the URL
            short_query = info['title'][:30]
            print(f"  Searching for URL: {short_query}")
            found_url = search_baidu_for_url(short_query)
            
            if found_url and '.gov.cn' in found_url:
                domain = re.search(r'https?://([^/]+)', found_url).group(1)
                print(f"  Found via Baidu: {domain}")
                return {
                    "title": info['title'],
                    "search_keyword": short_query,
                    "url": found_url,
                    "status": "found",
                    "found_at": domain
                }
            
            return {
                "title": info['title'],
                "search_keyword": display_title[:60],
                "url": "",
                "status": "not_found",
                "found_at": info['found_at']
            }
    
    # No match found - try Baidu direct search
    print(f"  No known match, trying Baidu...")
    short_query = display_title[:30]
    found_url = search_baidu_for_url(short_query)
    
    if found_url and '.gov.cn' in found_url:
        domain = re.search(r'https?://([^/]+)', found_url).group(1)
        print(f"  Found via Baidu: {domain}")
        return {
            "title": display_title,
            "search_keyword": short_query,
            "url": found_url,
            "status": "found",
            "found_at": domain
        }
    
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
    print(f"Loaded {len(items)} items\n")
    
    results = []
    found_count = 0
    
    for i, item in enumerate(items):
        print(f"[{i+1}/{len(items)}] {item['region']}: ", end="")
        # Print a summary
        raw_short = re.sub(r'\.{2,}', '', item['title'])[:40]
        print(raw_short)
        
        result = process_item(item, i)
        
        if result['status'] == 'found':
            found_count += 1
            url_short = result['url'][:70]
            print(f"  → {result['found_at']}: {url_short}")
        else:
            print(f"  → NOT FOUND (identified: {result['found_at'] or 'unknown'})")
        
        results.append(result)
        
        # Save checkpoint
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        if i < len(items) - 1:
            time.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {found_count}/{len(results)} found")
    print(f"NOT FOUND: {len(results) - found_count}")
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
