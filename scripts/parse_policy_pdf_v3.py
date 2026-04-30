#!/usr/bin/env python3
"""
低空经济政策PDF解析器 v3.0 — 多pass策略
Pass 1: 提取目录章节结构（第一编/第二编...各省标题）
Pass 2: 逐页扫描政策条目
Pass 3: 用目录章节推断地区和日期
Pass 4: 合并去重 + 交叉验证
"""

import re, json, os
from pathlib import Path

PDF_PATH = os.path.expanduser(
    "~/.hermes/cache/documents/doc_5e33ec52d2c0_2025中国低空经济法律、法规、政策文件汇编.pdf"
)
OUTPUT_DIR = os.path.expanduser("~/low-altitude-economy/data")

# ── 已知的省市标题列表（PDF目录中的章节标记） ──
KNOWN_REGIONS = {
    "北京市": "北京市",
    "天津市": "天津市",
    "上海市": "上海市",
    "重庆市": "重庆市",
    "河北省": "河北省",
    "山西省": "山西省",
    "辽宁省": "辽宁省",
    "吉林省": "吉林省",
    "黑龙江省": "黑龙江省",
    "江苏省": "江苏省",
    "浙江省": "浙江省",
    "安徽省": "安徽省",
    "福建省": "福建省",
    "江西省": "江西省",
    "山东省": "山东省",
    "河南省": "河南省",
    "湖北省": "湖北省",
    "湖南省": "湖南省",
    "广东省": "广东省",
    "海南省": "海南省",
    "四川省": "四川省",
    "贵州省": "贵州省",
    "云南省": "云南省",
    "陕西省": "陕西省",
    "甘肃省": "甘肃省",
    "青海省": "青海省",
    "内蒙古自治区": "内蒙古",
    "广西壮族自治区": "广西",
    "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
    "深圳市": "广东省",
    "广州市": "广东省",
    "杭州市": "浙江省",
    "成都市": "四川省",
    "南京市": "江苏省",
    "武汉市": "湖北省",
    "长沙市": "湖南省",
    "郑州市": "河南省",
    "合肥市": "安徽省",
    "西安市": "陕西省",
    "宁波市": "浙江省",
    "厦门市": "福建省",
    "青岛市": "山东省",
    "大连市": "辽宁省",
}

# 按照字符长度降序排序（避免短名称先匹配）
SORTED_REGIONS = sorted(KNOWN_REGIONS.keys(), key=len, reverse=True)

def extract_pdf_text(pdf_path):
    """提取PDF全部文本"""
    import fitz
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append({"page": i + 1, "text": text})
    doc.close()
    return pages

def pass1_parse_toc(pages):
    """
    Pass 1: 解析目录结构
    识别编、章、节标题及其页码范围
    """
    toc_structure = []
    current_part = None  # 第一编/第二编...
    current_chapter = None  # 一、法律 / 二、行政法规...
    current_region = None  # 北京市/广东省...
    current_section = None  # 政策文件名称
    
    # 提取全部目录页文本（前20页左右）
    toc_pages = []
    for p in pages[:25]:  # 目录大约在前25页
        toc_pages.append(p["text"])
    toc_text = "\n".join(toc_pages)
    
    lines = toc_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 识别编
        m = re.match(r'第[一二三四五六七八九十]+编\s+(.+)', line)
        if m:
            current_part = m.group(1).strip()
            continue
        
        # 识别节（省市标题）
        for region in SORTED_REGIONS:
            if region in line:
                current_region = region
                current_part = f"{region}"
                toc_structure.append({
                    "type": "region",
                    "name": region,
                    "province": KNOWN_REGIONS[region],
                    "line": line[:100]
                })
                break
        
        # 识别法律/行政法规等大类
        m = re.match(r'[一二三四五六七八九十]+[、\.]\s*(法律|行政法规|部门规章|规范性文件|地方法规|地方规章)', line)
        if m:
            current_chapter = m.group(1).strip()
            continue
        
        # 目录中的政策文件条目（带页码）
        m = re.match(r'[《]?([^《》\d]{4,50})[》]?\s*(\d{1,4})\s*$', line)
        if m and current_region:
            title = m.group(1).strip()
            page = m.group(2)
            toc_structure.append({
                "type": "entry",
                "title": title,
                "page": int(page),
                "region": current_region,
                "province": KNOWN_REGIONS.get(current_region, "全国"),
                "chapter": current_chapter,
                "part": current_part
            })
    
    return toc_structure

def pass2_full_text_search(pages):
    """
    Pass 2: 全文搜索所有可能的政策名称
    宽匹配，宁可误报也不要漏报
    """
    entries = set()
    
    for p in pages:
        text = p["text"]
        
        # 模式A: 《XXX》
        for m in re.finditer(r'[（(]?\s*《([^》]{4,60})》\s*[）)]?', text):
            title = m.group(1).strip()
            if title and len(title) >= 4:
                entries.add((title, p["page"]))
    
    return list(entries)

def pass3_region_inference(toc, entries, pages):
    """
    Pass 3: 用目录结构推断每条政策的地区和日期
    """
    # 构建"页码 → 地区"映射表
    page_region = {}
    prev_page = 0
    prev_region = "全国"
    
    for item in toc:
        if item["type"] == "region":
            # 从上一个地区结束到下一个地区开始之间的页属于前一个地区
            # 这里简化处理
            pass
    
    # 从目录条目建立页码关联
    for item in toc:
        if item["type"] == "entry" and "page" in item:
            p = item["page"]
            region = item.get("region", "全国")
            page_region[p] = region
    
    # 对于全文搜索到的条目，查找最近的地区
    result = []
    for title, page in entries:
        # 找距离最近且有地区标记的条目
        region = "全国"
        closest_diff = float('inf')
        for p, r in page_region.items():
            diff = abs(p - page)
            if diff < closest_diff:
                closest_diff = diff
                region = r
        
        # 检查上下文文本是否有地区关键词
        if page <= len(pages):
            context = pages[page - 1]["text"]
            for r in SORTED_REGIONS:
                if r in context:
                    region = r
                    break
        
        result.append({
            "title": title,
            "page": page,
            "region": KNOWN_REGIONS.get(region, "全国"),
            "region_raw": region
        })
    
    return result

def pass4_clean_and_merge(all_entries):
    """
    Pass 4: 清洗、去重、补充信息
    """
    seen = set()
    cleaned = []
    
    for entry in all_entries:
        title = entry["title"]
        # 清洗标题
        title = re.sub(r'^\d+[\.\s、]+\s*', '', title)
        title = re.sub(r'\s{2,}', ' ', title).strip()
        
        if not title or len(title) < 4:
            continue
        
        # 去重
        key = title[:20]
        if key in seen:
            continue
        seen.add(key)
        
        # 推测类别
        cat_rules = [
            (r'法$', "法律"),
            (r'条例', "行政法规"),
            (r'规定|办法|细则', "部门规章"),
            (r'通知|意见|纲要|规划|方案|措施', "政策文件"),
            (r'标准|规范|指南', "技术规范"),
        ]
        category = "其他"
        for pat, cat in cat_rules:
            if re.search(pat, title):
                category = cat
                break
        
        # 推测日期（从标题中提取年份）
        year = ""
        m = re.search(r'(\d{4})年', title)
        if m:
            year = f"{m.group(1)}年"
        m = re.search(r'(\d{4})', title)
        if m:
            year = f"{m.group(1)}年"
        
        cleaned.append({
            "title": title,
            "date": year,
            "region": entry.get("region", "全国"),
            "source": "2025中国低空经济政策汇编",
            "category": category,
            "level": "国家" if entry.get("region", "全国") == "全国" else "地方",
            "page": entry.get("page", 0)
        })
    
    return cleaned

def main():
    print("=" * 60)
    print("低空经济政策PDF解析器 v3.0")
    print("=" * 60)
    
    # Step 1: 提取PDF文本
    print("\n[1/5] 提取PDF文本 (1869页)...")
    pages = extract_pdf_text(PDF_PATH)
    print(f"  成功加载 {len(pages)} 页")
    
    # Step 2: Pass1 - 解析目录
    print("\n[2/5] Pass1: 解析目录结构...")
    toc = pass1_parse_toc(pages)
    print(f"  目录条目: {len(toc)} 条")
    
    # 统计地区覆盖
    regions_in_toc = set()
    for item in toc:
        if item["type"] == "region":
            regions_in_toc.add(item["name"])
    print(f"  目录覆盖地区: {sorted(regions_in_toc)}")
    
    # Step 3: Pass2 - 全文搜索
    print("\n[3/5] Pass2: 全文搜索政策条目...")
    entries = pass2_full_text_search(pages)
    print(f"  找到 {len(entries)} 条候选条目")
    
    # Step 4: Pass3 - 地区推断
    print("\n[4/5] Pass3: 地区和日期推断...")
    inferred = pass3_region_inference(toc, entries, pages)
    print(f"  推断完成: {len(inferred)} 条")
    
    # Step 5: Pass4 - 清洗去重
    print("\n[5/5] Pass4: 清洗、去重、补全...")
    cleaned = pass4_clean_and_merge(inferred)
    print(f"  有效政策: {len(cleaned)} 条")
    
    # 统计
    levels = {}
    regions = {}
    cats = {}
    for c in cleaned:
        levels[c["level"]] = levels.get(c["level"], 0) + 1
        r = c["region"]
        regions[r] = regions.get(r, 0) + 1
        cats[c["category"]] = cats.get(c["category"], 0) + 1
    
    print(f"\n  📊 统计:")
    print(f"    国家层面: {levels.get('国家', 0)} 条")
    print(f"    地方层面: {levels.get('地方', 0)} 条")
    print(f"    覆盖地区: {len(regions)} 个")
    print(f"    类别分布: {json.dumps(cats, ensure_ascii=False)}")
    
    # 输出
    output_path = os.path.join(OUTPUT_DIR, "parsed_policies_v3.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"\n  已写入: {output_path}")
    
    # 按地区预览
    print(f"\n📍 地区分布:")
    for r, c in sorted(regions.items(), key=lambda x: -x[1]):
        print(f"  {r}: {c}条")
    
    print(f"\n📋 前20条预览:")
    for c in cleaned[:20]:
        print(f"  [{c['region']}] [{c['category']}] {c['title']} ({c['date']})")
    
    return cleaned

if __name__ == "__main__":
    cleaned = main()
