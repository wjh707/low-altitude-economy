#!/usr/bin/env python3
"""
低空经济政策PDF解析脚本 v2.0
目标：从1869页的政策汇编PDF中批量提取结构化政策数据
策略：多层pass + 正则匹配 + 上下文推测
"""

import re, json, os, sys
from pathlib import Path

PDF_PATH = os.path.expanduser(
    "~/.hermes/cache/documents/doc_5e33ec52d2c0_2025中国低空经济法律、法规、政策文件汇编.pdf"
)
OUTPUT = os.path.expanduser("~/low-altitude-economy/data/parsed_policies.json")

# ── 各章标题（用于切分区域） ──
CHAPTERS = [
    "第一编", "第二编", "第三编", "第四编", "第五编", "第六编", "第七编",
]

SECTION_HEADERS = [
    "一、法律", "二、行政法规", "三、部门规章", "四、规范性文件",
    "一、地方法规", "二、地方规章", "三、地方规范性文件",
    "一、国家层面", "二、地方层面",
]

PROVINCES = [
    "北京市", "天津市", "上海市", "重庆市",
    "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
    "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省",
    "河南省", "湖北省", "湖南省", "广东省", "海南省",
    "四川省", "贵州省", "云南省", "陕西省", "甘肃省", "青海省",
    "台湾省", "内蒙古", "广西", "西藏", "宁夏", "新疆",
    "深圳市", "广州市", "杭州市", "成都市", "南京市",
    "苏州市", "武汉市", "长沙市", "郑州市", "合肥市", "西安市",
    "宁波市", "厦门市", "青岛市", "大连市",
]

def extract_pdf_text(pdf_path):
    """提取PDF全部文本"""
    import fitz
    doc = fitz.open(pdf_path)
    all_text = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        all_text.append({
            "page": i + 1,
            "text": text
        })
    doc.close()
    return all_text

def find_policy_entries_via_regex(text):
    """
    Pass 1: 正则匹配政策条目
    尝试匹配的模式：
      1. 《XXX》+日期/文号
      2. 编号+政策名称+日期
      3. 标题行（无书名号但看起来像政策文件）
    """
    entries = []
    
    # 模式1: 《政策名称》YYYY年... 或 《政策名称》（...号）
    pattern1 = re.compile(
        r'[（(]?\s*《([^》]+)》\s*[）)]?\s*'
        r'(?:（|\(|\s)'
        r'([^）)]{5,80}?)'
        r'(?:）|\)|\s)',
        re.DOTALL
    )
    
    # 模式2: 文号驱动匹配，如 国发〔2024〕7号《XXX》
    pattern2 = re.compile(
        r'([\u4e00-\u9fa5]+\s*[〔\[]?\s*\d{4}\s*[〕\]].{0,10}?号)\s*'
        r'《([^》]+)》',
        re.DOTALL
    )
    
    # 模式3: 纯日期匹配
    pattern3 = re.compile(
        r'《([^》]+)》\s*[（(](\d{4})[年\s](\d{1,2})?[月]?(\d{1,2})?[日]?[）)]',
        re.DOTALL
    )
    
    # 模式4: 不含书名号的政策标题（如以"关于印发"开头）
    pattern4 = re.compile(
        r'(关于印发[^。]{10,80}?的通知)\s*[（(](\d{4})[年\s]',
        re.DOTALL
    )
    
    # 模式5: "法"或"条例"结尾的法规名称
    pattern5 = re.compile(
        r'[（(]?((?:中华人民共和国)?[\u4e00-\u9fa5]{2,30}(?:法|条例|规定|办法|细则|意见|通知|决定|纲要|规划))[）)]?\s*'
        r'[（(](\d{4})[年\s]',
        re.DOTALL
    )

    for line in text.split('\n'):
        line = line.strip()
        if not line or len(line) < 8:
            continue
            
        match2 = pattern2.search(line)
        if match2:
            entries.append({
                "title": match2.group(2).strip(),
                "doc_number": match2.group(1).strip(),
                "source_text": line[:120]
            })
            
        match3 = pattern3.search(line)
        if match3:
            title = match3.group(1).strip()
            year = match3.group(2)
            month = match3.group(3) or ""
            day = match3.group(4) or ""
            entries.append({
                "title": title,
                "date": f"{year}年{month}月{day}日".replace("月日", "月").replace("年 ", "年"),
                "source_text": line[:120]
            })
            
        match1 = pattern1.search(line)
        if match1:
            title = match1.group(1).strip()
            extra = match1.group(2).strip()
            # 避免已匹配过的
            if not any(e["title"] == title for e in entries):
                entries.append({
                    "title": title,
                    "extra": extra,
                    "source_text": line[:120]
                })

    # 去重
    seen = set()
    unique = []
    for e in entries:
        key = e["title"]
        if key not in seen:
            seen.add(key)
            unique.append(e)
    
    return unique

def extract_doc_year(text):
    """从文本中提取文号和年份"""
    # 国发〔2024〕7号
    m = re.search(r'([\u4e00-\u9fa5]+)\s*[〔\[【]\s*(\d{4})\s*[〕\]】]?\s*(\d+)\s*号', text)
    if m:
        return f"{m.group(1)}〔{m.group(2)}〕{m.group(3)}号", m.group(2)
    # 2024年
    m = re.search(r'(\d{4})\s*年', text)
    if m:
        return "", m.group(1)
    return "", ""

def guess_province(text):
    """根据文本猜测所属省份"""
    for p in PROVINCES:
        if p in text:
            return p
    return "全国"

def clean_entry(entry, page_num):
    """单条清洗"""
    title = entry["title"].strip()
    title = re.sub(r'^\d+[\.\s、]+', '', title)
    title = re.sub(r'\s{2,}', ' ', title)
    
    source_text = entry.get("source_text", entry.get("extra", ""))
    doc_number, year = extract_doc_year(source_text)
    
    province = guess_province(title + " " + source_text)
    
    # 类别猜测
    if any(kw in title for kw in ["法", "条例", "规定"]):
        category = "法律/法规"
    elif any(kw in title for kw in ["通知", "意见", "办法", "纲要", "规划"]):
        category = "政策文件"
    else:
        category = "其他"
    
    return {
        "title": title,
        "date": f"{year}年" if year else "",
        "region": province,
        "source": "政策汇编",
        "category": category,
        "doc_number": doc_number,
        "page": page_num,
        "level": "国家" if province == "全国" else "地方"
    }

def merge_policy_data(existing, new_entries):
    """合并并去重"""
    seen_titles = {e["title"] for e in existing}
    merged = list(existing)
    added = 0
    for e in new_entries:
        if e["title"] not in seen_titles:
            merged.append(e)
            seen_titles.add(e["title"])
            added += 1
    return merged, added

def main():
    print("=" * 60)
    print("低空经济政策PDF解析器 v2.0")
    print("=" * 60)
    
    # Step 1: 提取文本
    print("\n[1/4] 解析PDF文本...")
    pages = extract_pdf_text(PDF_PATH)
    print(f"  共 {len(pages)} 页")
    
    # Step 2: 收集所有文本 + 按省份切分
    print("\n[2/4] 正则匹配政策条目...")
    all_text = "\n".join([p["text"] for p in pages])
    
    entries = find_policy_entries_via_regex(all_text)
    print(f"  正则匹配到 {len(entries)} 条候选条目")
    
    # Step 3: 清洗 + 结构化
    print("\n[3/4] 清洗和结构化...")
    parsed = []
    for i, entry in enumerate(entries):
        page_num = 0
        cleaned = clean_entry(entry, page_num)
        if cleaned["title"] and len(cleaned["title"]) >= 6:
            parsed.append(cleaned)
    
    print(f"  清洗后得到 {len(parsed)} 条有效政策")
    
    # 统计
    levels = {}
    provinces = {}
    for p in parsed:
        levels[p["level"]] = levels.get(p["level"], 0) + 1
        provinces[p["region"]] = provinces.get(p["region"], 0) + 1
    
    print(f"\n  国家层面: {levels.get('国家', 0)} 条")
    print(f"  地方层面: {levels.get('地方', 0)} 条")
    print(f"  覆盖地区: {len(provinces)} 个")
    print(f"  各省分布: {json.dumps(provinces, ensure_ascii=False, indent=2)}")
    
    # Step 4: 输出
    print("\n[4/4] 写入JSON...")
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    
    print(f"  已写入: {OUTPUT}")
    print(f"  {len(parsed)} 条政策数据")
    print("\n✅ 解析完成!")
    
    return parsed

if __name__ == "__main__":
    parsed = main()
    print(f"\n前10条预览:")
    for p in parsed[:10]:
        print(f"  - [{p['region']}] {p['title']} ({p['date']})")
