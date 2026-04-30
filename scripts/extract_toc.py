#!/usr/bin/env python3
"""
从PDF目录提取所有政策条目，支持跨行拼接和分类
"""
import re, json, os

PDF_PATH = os.path.expanduser("~/.hermes/cache/documents/doc_5e33ec52d2c0_2025中国低空经济法律、法规、政策文件汇编.pdf")
OUTPUT = os.path.expanduser("~/low-altitude-economy/data/toc_entries.json")

def extract_toc():
    import fitz
    doc = fitz.open(PDF_PATH)
    
    toc_pages = []
    for i in range(4, 13):  # 第5-13页（0-index: 4-12）
        text = doc[i].get_text("text")
        toc_pages.append(text)
    doc.close()
    
    lines = []
    for page_text in toc_pages:
        for line in page_text.split('\n'):
            l = line.strip()
            if l:
                lines.append(l)
    
    entries = []  # {title, category, region, part, page}
    current_part = "国家层面"
    current_category = ""
    current_sub = ""  # 空域管理类/通用航空类...
    current_region = "全国"
    
    for i, line in enumerate(lines):
        # 章：第一章国家层面/第二章地方层面
        m = re.match(r'第[一二三四五六七八九十]+章\s*(国家层面|地方层面)', line)
        if m:
            current_part = m.group(1)
            continue
        
        # 一级分类：一、法律 / 二、行政法规 / 三、部门规章 / 四、政策文件 / 一、地方性法规 / 二、规范性文件和政策
        m = re.match(r'[一二三四五六七八九十]+[、\.]\s*(法律|行政法规|部门规章(?:和规范性文件)?|规范性文件和政策|规范性文件|政策文件(?:[（(].*?[）)])?)', line)
        if m:
            cat = m.group(1)
            cat = cat.replace("和规范性文件", "").replace("和政策", "")
            if current_part == "国家层面":
                current_category = cat
            else:
                current_category = cat
            continue
        
        # 子分类：（一）空域管理类 /（二）通用航空类...
        m = re.match(r'[（(][一二三四五六七八九十]+[)）]\s*(.+)', line)
        if m:
            current_sub = m.group(1).strip()
            continue
        
        # 地区标记：北京/上海/广东/天津/重庆/江苏/浙江...
        m = re.match(r'[（(][一二三四五六七八九十]+[)）]\s*(\S{2,6})', line)
        if m:
            current_region = m.group(1)
            # 地区名包含"省"的情况
            continue
        
        # 政策条目：数字+标题+页码
        m = re.match(r'(\d+)[、\.]\s*(.*)', line)
        if m:
            num = m.group(1)
            rest = m.group(2).strip()
            
            # 提取页码（末尾3-4位数字）
            page_match = re.search(r'(\d{3,4})\s*$', rest)
            page = int(page_match.group(1)) if page_match else 0
            title = re.sub(r'\s*\d{3,4}\s*$', '', rest).strip()
            
            if title and len(title) >= 4 and not title.startswith('�'):
                entries.append({
                    "title": title,
                    "category": current_category,
                    "sub_category": current_sub,
                    "part": current_part,
                    "region": current_region,
                    "page": page,
                    "toc_line": i
                })
        else:
            # 续行（PDF换行导致标题被切断，但不含页码）
            if entries and line and not line.startswith('本报告') and not line.startswith('http'):
                last = entries[-1]
                # 检查是不是地区标记的续行
                if any(kw in line for kw in ['北京', '上海', '广东', '天津', '重庆', '江苏', '浙江', '湖南', '山东', '安徽', '海南', '四川', '福建', '河北', '江西', '山西', '辽宁', '新疆']):
                    # 可能是地区标记
                    m = re.match(r'[（(][一二三四五六七八九十]+[)）]\s*(\S+)', line)
                    if m:
                        current_region = m.group(1)
                else:
                    # 拼接续行（去掉前导数字空格）
                    cleaned = re.sub(r'^\d+\s+', '', line)
                    if cleaned and not re.match(r'^\d+[、\.]', cleaned) and len(cleaned) > 4:
                        last["title"] += cleaned
    
    return entries

def main():
    entries = extract_toc()
    
    # 二次清洗
    clean = []
    seen = set()
    for e in entries:
        title = e["title"].strip()
        # 清理异常字符
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'[�]', '', title)
        if not title or len(title) < 5:
            continue
        # 去重（基于简化标题）
        key = re.sub(r'[\s《》（）\(\)〔〕【】]', '', title)[:25]
        if key in seen:
            continue
        seen.add(key)
        
        # 修复地区
        region = e["region"]
        # 从标题推断更精确的省市
        for kw, prov in [
            ("北京", "北京市"), ("上海", "上海市"), ("天津", "天津市"), ("重庆", "重庆市"),
            ("广东", "广东省"), ("深圳", "广东省"), ("广州", "广东省"), ("珠海", "广东省"),
            ("惠州", "广东省"), ("中山", "广东省"), ("东莞", "广东省"), ("佛山", "广东省"),
            ("茂名", "广东省"), ("湛江", "广东省"), ("福田", "广东省"),
            ("宝安", "广东省"), ("龙华", "广东省"), ("龙岗", "广东省"), ("罗湖", "广东省"),
            ("盐田", "广东省"), ("南山", "广东省"), ("黄埔", "广东省"), ("谢岗", "广东省"),
            ("阜沙", "广东省"),
            ("浙江", "浙江省"), ("杭州", "浙江省"), ("嘉兴", "浙江省"),
            ("海宁", "浙江省"), ("金华", "浙江省"), ("舟山", "浙江省"),
            ("绍兴", "浙江省"), ("越城", "浙江省"), ("宁波", "浙江省"),
            ("江苏", "江苏省"), ("南京", "江苏省"), ("苏州", "江苏省"),
            ("无锡", "江苏省"), ("常州", "江苏省"), ("南通", "江苏省"),
            ("徐州", "江苏省"), ("扬州", "江苏省"), ("吴中", "江苏省"),
            ("湖南", "湖南省"), ("长沙", "湖南省"),
            ("福建", "福建省"), ("厦门", "福建省"), ("福州", "福建省"),
            ("四川", "四川省"), ("成都", "四川省"), ("自贡", "四川省"), ("南充", "四川省"),
            ("安徽", "安徽省"), ("合肥", "安徽省"), ("芜湖", "安徽省"),
            ("山东", "山东省"),
            ("江西", "江西省"), ("吉安", "江西省"), ("九江", "江西省"),
            ("海南", "海南省"),
            ("河北", "河北省"), ("雄安", "河北省"),
            ("山西", "山西省"),
            ("新疆", "新疆"),
            ("辽宁", "辽宁省"), ("沈阳", "辽宁省"),
        ]:
            if kw in title:
                region = prov
                break
        
        # 如果标题有"国务院"、"国家"、"全国"等且当前是全国，保留全国
        if region == "全国" and any(kw in title for kw in ["国务院", "国家", "中国民航局", "中央军委", "中共中央"]):
            pass  # 保持全国
        
        clean.append({
            "title": title,
            "category": e["category"],
            "sub_category": e["sub_category"],
            "part": e["part"],
            "region": region,
            "page": e.get("page", ""),
        })
    
    print(f"目录原始条目: {len(entries)}")
    print(f"去重清洗后: {len(clean)}")
    
    # 统计
    parts = {}
    cats = {}
    regions = {}
    for c in clean:
        parts[c["part"]] = parts.get(c["part"], 0) + 1
        cats[c["category"]] = cats.get(c["category"], 0) + 1
        regions[c["region"]] = regions.get(c["region"], 0) + 1
    
    print(f"\n国家层面: {parts.get('国家层面', 0)} 条")
    print(f"地方层面: {parts.get('地方层面', 0)} 条")
    print(f"\n分类:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")
    print(f"\n地区:")
    for r, n in sorted(regions.items(), key=lambda x: -x[1]):
        print(f"  {r}: {n}")
    
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已保存到: {OUTPUT}")
    
    # 预览
    print(f"\n📋 完整列表:")
    for i, c in enumerate(clean):
        print(f"  {i+1:3d}. [{c['region']}] [{c['category']}] {c['title'][:60]}")
    
    return clean

if __name__ == "__main__":
    main()
