#!/usr/bin/env python3
"""
低空经济政策PDF解析器 v4.0 — 终版
- 修复标题换行拼接
- 强化日期提取
- 提升地区推断精度
- 严格去重
- 补充文号信息
- 输出完整结构化数据
"""

import re, json, os

PDF_PATH = os.path.expanduser(
    "~/.hermes/cache/documents/doc_5e33ec52d2c0_2025中国低空经济法律、法规、政策文件汇编.pdf"
)
OUTPUT_DIR = os.path.expanduser("~/low-altitude-economy/data")

KNOWN_PROVINCES = {
    "北京市", "天津市", "上海市", "重庆市",
    "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
    "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省",
    "河南省", "湖北省", "湖南省", "广东省", "海南省",
    "四川省", "贵州省", "云南省", "陕西省", "甘肃省", "青海省",
}

KNOWN_CITIES = {
    "深圳市": "广东省", "广州市": "广东省",
    "杭州市": "浙江省", "宁波市": "浙江省", "温州市": "浙江省",
    "成都市": "四川省", "南京市": "江苏省", "苏州市": "江苏省",
    "武汉市": "湖北省", "长沙市": "湖南省",
    "郑州市": "河南省", "合肥市": "安徽省", "西安市": "陕西省",
    "厦门市": "福建省", "福州市": "福建省",
    "青岛市": "山东省", "济南市": "山东省",
    "大连市": "辽宁省", "沈阳市": "辽宁省",
    "嘉兴市": "浙江省", "无锡市": "江苏省", "东莞市": "广东省",
    "珠海市": "广东省", "佛山市": "广东省",
}

ALL_REGIONS = {**{p: p for p in KNOWN_PROVINCES}, **KNOWN_CITIES}
SORTED_REGIONS = sorted(ALL_REGIONS.keys(), key=len, reverse=True)

# ── 低空经济/通用航空政策文件关键词（用于过滤非相关条目） ──
RELEVANT_KW = [
    "低空", "无人机", "无人驾驶航空器", "通用航空", "通航",
    "航空器", "空域", "飞行", "适航", "民航",
    "直升机", "eVTOL", "飞行汽车", "空中交通",
    "机场", "起降", "跑道", "航路",
    "飞行人员", "驾驶员", "飞手",
    "航空运动", "飞行营地",
    "航空法", "民航法", "航空安全",
    "航空工业", "航空制造",
]

def extract_pdf_text(pdf_path):
    import fitz
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append({"page": i + 1, "text": text})
    doc.close()
    return pages

def smart_join(text):
    """智能拼接换行（修复被换行切断的中文词）"""
    # 中文换行：如果行末是中文且下一行开头是中文，则拼接
    lines = text.split('\n')
    result = []
    for line in lines:
        if result and result[-1] and line:
            last_char = result[-1][-1]
            first_char = line[0]
            # 中文连中文、中文连英文、英文连中文
            if (('\u4e00' <= last_char <= '\u9fff' and '\u4e00' <= first_char <= '\u9fff') or
                (last_char.isalpha() and first_char.isalpha()) or
                (last_char == '）' and first_char == '《')):
                result[-1] += line
            elif ('\u4e00' <= last_char <= '\u9fff' or last_char in '）】」》〕' or first_char in '〔（【「《('):
                result[-1] += line
            else:
                result.append(line)
        else:
            result.append(line)
    return '\n'.join(result)

def extract_all_entries(pages):
    """
    全面提取所有符合条件的政策条目
    策略：对每一页做全面的模式匹配
    """
    entries_raw = []
    
    for p in pages:
        text = smart_join(p["text"])
        page_num = p["page"]
        
        # ── 各种匹配模式 ──
        
        # 模式A: 《政策名称》——最常用
        for m in re.finditer(r'《([^》]{4,80})》', text):
            title = m.group(1).strip()
            if any(kw in title for kw in RELEVANT_KW):
                # 尝试提取后面的日期/文号
                after = text[m.end():m.end()+200]
                date_info = extract_date_and_doc(after)
                entries_raw.append({
                    "title": title,
                    "page": page_num,
                    "date": date_info["date"],
                    "doc_number": date_info["doc_number"],
                    "source_context": after[:100]
                })
                continue
            
        # 模式B: 纯文字标题（不含书名号），但包含低空经济关键词
        for m in re.finditer(r'([\u4e00-\u9fa5]{6,60}(?:法|条例|规定|办法|细则|意见|通知|决定|纲要|规划|方案|措施|标准|指南|规范|目录))', text):
            title = m.group(1).strip()
            if any(kw in title for kw in RELEVANT_KW):
                # 检查是否已经被《》模式捕获
                if title.startswith('《') or title.endswith('》'):
                    continue
                after = text[m.end():m.end()+200]
                date_info = extract_date_and_doc(after)
                entries_raw.append({
                    "title": title,
                    "page": page_num,
                    "date": date_info["date"],
                    "doc_number": date_info["doc_number"],
                    "source_context": after[:100]
                })
        
        # 模式C: "关于印发...的通知"系列
        for m in re.finditer(r'关于印发[《]?([^》\n]{6,60})[》]?\s*(?:的通知|办法|方案)', text):
            title = m.group(0).strip()
            after = text[m.end():m.end()+200]
            date_info = extract_date_and_doc(after)
            entries_raw.append({
                "title": title,
                "page": page_num,
                "date": date_info["date"],
                "doc_number": date_info["doc_number"],
                "source_context": after[:100]
            })
    
    return entries_raw

def extract_date_and_doc(text):
    """从文本中提取日期和文号"""
    result = {"date": "", "doc_number": ""}
    
    # 日期: YYYY年MM月DD日
    m = re.search(r'(\d{4})\s*[年\s\.]\s*(\d{1,2})?\s*[月\s\.]?\s*(\d{1,2})?\s*[日]?', text)
    if m:
        y, mo, d = m.group(1), m.group(2) or "", m.group(3) or ""
        parts = [y + "年"]
        if mo:
            parts.append(mo + "月")
        if d:
            parts.append(d + "日")
        result["date"] = "".join(parts)
    
    # 文号: 国发〔2024〕7号 / 工信部联〔2024〕2号 / CAAC文号
    m = re.search(r'([\u4e00-\u9fa5A-Z]+\s*[〔\[【]\s*\d{4}\s*[〕\]】]\s*\d+\s*号)', text)
    if m:
        result["doc_number"] = m.group(1).strip()
    
    # 如果上面没匹配到，尝试：发改高技〔2023〕1288号
    if not result["doc_number"]:
        m = re.search(r'([\u4e00-\u9fa5]+\s*[〔\[【]]?\s*\d{4}\s*[〕\]】]?\s*\d+\s*号)', text)
        if m:
            result["doc_number"] = m.group(1).strip()
    
    return result

def infer_region_from_title(title):
    """从标题推理地区"""
    for region in SORTED_REGIONS:
        if region in title:
            return ALL_REGIONS[region]
    return "全国"

def infer_region_from_page(pages, page_num, context_window=5):
    """从页面前后上下文推理地区"""
    start = max(0, page_num - context_window - 1)
    end = min(len(pages), page_num + context_window)
    
    for i in range(start, end):
        text = pages[i]["text"]
        for region in SORTED_REGIONS:
            if region in text:
                return ALL_REGIONS[region]
    return ""

def categorize(title):
    """智能分类"""
    rules = [
        (r'法$', "法律"),
        (r'条例', "行政法规"),
        (r'规定|办法|细则', "部门规章"),
        (r'通知|意见|纲要|规划|方案|措施', "政策文件"),
        (r'标准|指南|规范', "技术规范"),
    ]
    # 先把"印发...通知"类归为政策文件
    if re.match(r'关于印发', title):
        return "政策文件"
    for pat, cat in rules:
        if re.search(pat, title):
            return cat
    return "其他"

def classify_level(region, category):
    """判断国家/地方层级"""
    if region == "全国":
        return "国家"
    # 法律类即使是地方出的也算国家（民航法、空域法等）
    if category == "法律":
        return "国家"
    return "地方"

def deduce_year(title, date_str):
    """从标题和日期中提取年份"""
    # 优先用提取到的日期
    m = re.match(r'(\d{4})', date_str)
    if m:
        return m.group(1) + "年"
    
    # 从标题提取
    for m in re.finditer(r'(20\d{2})', title):
        return m.group(1) + "年"
    
    return ""

def dedup_and_clean(entries_raw, pages):
    """严格去重 + 清洗"""
    seen = set()
    cleaned = []
    
    for e in entries_raw:
        # 清洗标题
        title = e["title"]
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'^[《]?', '', title)
        title = re.sub(r'[》]?$', '', title)
        title = title.strip()
        
        if not title or len(title) < 6:
            continue
        
        # 去重（基于标题前30个字符 + 简化后的标题）
        key1 = title[:30]
        key2 = re.sub(r'[《》（）\(\)〔〕【】\s]', '', title)[:25]
        if key1 in seen or key2 in seen:
            continue
        seen.add(key1)
        seen.add(key2)
        
        # 地区推断
        region = infer_region_from_title(title)
        if not region or region == "全国":
            page_region = infer_region_from_page(pages, e["page"])
            if page_region:
                region = page_region
        
        # 分类
        category = categorize(title)
        level = classify_level(region, category)
        
        # 年份
        year = deduce_year(title, e.get("date", ""))
        
        cleaned.append({
            "title": title,
            "date": e.get("date", year) or year,
            "doc_number": e.get("doc_number", ""),
            "region": region,
            "category": category,
            "level": level,
            "source": "2025中国低空经济政策汇编",
            "page": e["page"]
        })
    
    return cleaned

def analyze_coverage(cleaned):
    """分析覆盖范围"""
    stats = {
        "level": {},
        "region": {},
        "category": {},
        "has_date": 0,
        "has_doc": 0
    }
    for c in cleaned:
        stats["level"][c["level"]] = stats["level"].get(c["level"], 0) + 1
        stats["region"][c["region"]] = stats["region"].get(c["region"], 0) + 1
        stats["category"][c["category"]] = stats["category"].get(c["category"], 0) + 1
        if c["date"]:
            stats["has_date"] += 1
        if c["doc_number"]:
            stats["has_doc"] += 1
    return stats

def main():
    print("=" * 60)
    print("低空经济政策PDF解析器 v4.0 — 终版")
    print("=" * 60)
    
    print("\n[1/4] 提取PDF文本...")
    pages = extract_pdf_text(PDF_PATH)
    print(f"  共 {len(pages)} 页")
    
    print("\n[2/4] 全面搜索政策条目...")
    entries_raw = extract_all_entries(pages)
    print(f"  匹配到 {len(entries_raw)} 条原始条目")
    
    print("\n[3/4] 去重 + 清洗...")
    cleaned = dedup_and_clean(entries_raw, pages)
    print(f"  去重后有效政策: {len(cleaned)} 条")
    
    stats = analyze_coverage(cleaned)
    
    print(f"\n  📊 统计:")
    print(f"    国家层面: {stats['level'].get('国家', 0)} 条")
    print(f"    地方层面: {stats['level'].get('地方', 0)} 条")
    print(f"    覆盖地区: {len(stats['region'])} 个")
    print(f"    有日期: {stats['has_date']} 条")
    print(f"    有文号: {stats['has_doc']} 条")
    print(f"    类别分布: {json.dumps(stats['category'], ensure_ascii=False)}")
    
    print(f"\n  📍 地区分布 (Top 15):")
    for r, c in sorted(stats['region'].items(), key=lambda x: -x[1])[:15]:
        print(f"    {r}: {c}条")
    
    print("\n[4/4] 输出JSON...")
    output_path = os.path.join(OUTPUT_DIR, "parsed_policies_v4.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    
    print(f"  已写入: {output_path}")
    
    # ── 同时生成合并后的数据（替换看板数据） ──
    # 加载原有 policy_data.json
    existing_path = os.path.join(OUTPUT_DIR, "policy_data.json").replace("/data", "/dashboard")
    existing_path = os.path.join(os.path.expanduser("~/low-altitude-economy/dashboard"), "policy_data.json")
    
    existing = []
    if os.path.exists(existing_path):
        try:
            with open(existing_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            print(f"\n  📦 原有数据: {len(existing)} 条")
        except:
            pass
    
    # 合并去重
    seen_titles = {e["title"] for e in existing}
    merged = list(existing)
    for c in cleaned:
        if c["title"] not in seen_titles:
            merged.append({
                "title": c["title"],
                "date": c["date"],
                "region": c["region"],
                "source": c["source"],
                "category": c["category"]
            })
            seen_titles.add(c["title"])
    
    print(f"  📦 合并后数据: {len(merged)} 条 (新增 {len(merged) - len(existing)} 条)")
    
    with open(existing_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 已更新看板数据: {existing_path}")
    
    # 打印预览
    print(f"\n📋 预览 (前20条):")
    for c in cleaned[:20]:
        doc_str = f" [{c['doc_number']}]" if c['doc_number'] else ""
        date_str = f" ({c['date']})" if c['date'] else ""
        print(f"  [{c['region']}] [{c['category']}]{doc_str} {c['title']}{date_str}")
    
    print(f"\n{'='*60}")
    print(f"🎉 解析完成！看板数据已更新为 {len(merged)} 条")
    print(f"{'='*60}")
    
    return merged

if __name__ == "__main__":
    main()
