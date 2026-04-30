#!/usr/bin/env python3
"""
PDF政策汇编解析器 — 精准版
从目录获取政策名称和页码范围，从正文提取元数据和全文
"""
import re, json, os

PDF_PATH = os.path.expanduser(
    "~/.hermes/cache/documents/doc_5e33ec52d2c0_2025中国低空经济法律、法规、政策文件汇编.pdf"
)
OUTPUT_DIR = os.path.expanduser("~/low-altitude-economy/data")

def extract(p):
    import fitz
    doc = fitz.open(p)
    pages = [{"page": i+1, "text": doc[i].get_text("text")} for i in range(len(doc))]
    doc.close()
    return pages

def parse_toc(pages):
    """
    从目录页（5-13页）解析政策条目
    返回: [{title, start_page, chapter, region}, ...]
    """
    toc_text = "\n".join([p["text"] for p in pages[4:13]])  # 第5-13页
    entries = []
    
    current_chapter = None
    current_region = None
    current_part = None  # 国家/地方
    
    # 先切分出"第一章国家层面"和"第二章地方层面"
    lines = toc_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 四大层级标记
        m = re.match(r'第[一二三四五六七八九十]+章\s*(国家层面|地方层面)', line)
        if m:
            current_part = m.group(1)
            continue
        
        # 法律/行政法规/部门规章/政策文件
        m = re.match(r'[一二三四五六七八九十]+[、\.]\s*(法律|行政法规|部门规章(?:和规范性文件)?|规范性文件|政策文件)', line)
        if m:
            current_chapter = m.group(1)
            current_chapter = re.sub(r'和规范性文件', '', current_chapter)
            continue
        
        # 地方章节：北京/上海/广东...
        m = re.match(r'[（(]([一二三四五六七八九十]+)[)）]\s*([\u4e00-\u9fa5]{2,6})', line)
        if m and current_part == "地方层面":
            current_region = m.group(2)
            continue
        
        # 北京/上海/广东...（没有括号标记的）
        m = re.match(r'（([三四五六七八九十]+)）([\u4e00-\u9fa5]{2,6})', line)
        if m:
            current_region = m.group(2)
            continue
        
        # ⭐ 政策条目：数字 + 标题 + 页码
        m = re.match(r'(\d+)[、\.]\s*(.*?)\s*(\d{3,4})\s*$', line)
        if m:
            num = m.group(1)
            title = m.group(2).strip()
            page = int(m.group(3))
            
            # 清理PDF换行导致的碎片
            if title.startswith('》'):
                continue
            if len(title) < 5:
                continue
            
            entries.append({
                "title": title,
                "start_page": page,
                "chapter": current_chapter,
                "region": current_region or (current_part if current_part == "国家层面" else "全国"),
                "part": current_part
            })
            continue
        
        # 续行（PDF换行导致的长标题被切断）
        if entries and line and re.match(r'^[^\d]', line):
            last = entries[-1]
            if not line.endswith('...'):
                last["title"] += line.strip()
    
    return entries

def parse_policy_meta(pages, entry):
    """
    从正文页解析一条政策的元数据
    第14页格式示例:
      发文机关：全国人民代表大会常务委员会
      发布日期：2021.04.29
      生效日期：2021.04.29
      时效性：现行有效
    """
    sp = entry["start_page"] - 1  # 0-index
    if sp >= len(pages):
        return {}
    
    text = pages[sp]["text"]
    
    meta = {}
    
    # 发文机关
    m = re.search(r'发文机关[：:]\s*(.+)', text)
    if m:
        meta["issuer"] = m.group(1).strip()
    
    # 发布日期
    m = re.search(r'发布日期[：:]\s*(.+)', text)
    if m:
        meta["publish_date"] = m.group(1).strip()
    
    # 生效日期
    m = re.search(r'生效日期[：:]\s*(.+)', text)
    if m:
        meta["effective_date"] = m.group(1).strip()
    
    # 时效性
    m = re.search(r'时效性[：:]\s*(.+)', text)
    if m:
        meta["validity"] = m.group(1).strip()
    
    return meta

def extract_full_content(pages, entry):
    """
    提取一条政策的完整正文
    从 start_page 到下一政策的 start_page
    """
    sp = entry["start_page"] - 1
    ep = entry.get("end_page", sp + 5)  # 默认向后5页
    
    content_parts = []
    for i in range(sp, min(ep + 1, len(pages))):
        text = pages[i]["text"]
        # 去除页眉页码
        lines = text.split('\n')
        clean_lines = [l for l in lines if not re.match(r'^\d{1,4}$', l.strip())]
        content_parts.append('\n'.join(clean_lines))
    
    return '\n'.join(content_parts)

def main():
    print("=" * 60)
    print("PDF政策汇编解析器 — 精准版")
    print("=" * 60)
    
    print("\n[1/4] 提取PDF文本...")
    pages = extract(PDF_PATH)
    print(f"  共 {len(pages)} 页")
    
    print("\n[2/4] 解析目录...")
    toc = parse_toc(pages)
    print(f"  目录解析到 {len(toc)} 条政策")
    
    # 统计
    parts = {}
    for e in toc:
        parts[e["part"]] = parts.get(e["part"], 0) + 1
    print(f"  国家层面: {parts.get('国家层面', 0)} 条")
    print(f"  地方层面: {parts.get('地方层面', 0)} 条")
    
    print("\n[3/4] 提取元数据...")
    policies = []
    for i, entry in enumerate(toc):
        meta = parse_policy_meta(pages, entry)
        
        # 确定结束页（下一条政策的起始页-1）
        if i + 1 < len(toc):
            end_page = toc[i + 1]["start_page"] - 1
        else:
            end_page = entry["start_page"] + 5  # 最后一条保守估计
        
        # 地区
        region = entry.get("region", "全国")
        if region in ["国家层面", None]:
            region = "全国"
        
        policy = {
            "title": entry["title"],
            "start_page": entry["start_page"],
            "end_page": end_page,
            "chapter": entry.get("chapter", ""),
            "region": region,
            "part": entry.get("part", ""),
            "issuer": meta.get("issuer", ""),
            "publish_date": meta.get("publish_date", ""),
            "effective_date": meta.get("effective_date", ""),
            "validity": meta.get("validity", ""),
        }
        
        # 提取正文前200字符作为摘要
        content = extract_full_content(pages, {
            "start_page": entry["start_page"],
            "end_page": end_page
        })
        policy["summary"] = content[:500]
        policy["content_length"] = len(content)
        
        policies.append(policy)
    
    print(f"  处理完成: {len(policies)} 条")
    print(f"  有发文机关的: {sum(1 for p in policies if p['issuer'])} 条")
    print(f"  有发布日期的: {sum(1 for p in policies if p['publish_date'])} 条")
    print(f"  有生效日期的: {sum(1 for p in policies if p['effective_date'])} 条")
    
    print("\n[4/4] 保存结果...")
    
    # 保存完整数据（含元数据）
    output_path = os.path.join(OUTPUT_DIR, "policies_full.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(policies, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 完整数据已保存: {output_path}")
    print(f"  {len(policies)} 条政策，含元数据和摘要")
    
    # 保存看板用简版数据
    dashboard_data = []
    for p in policies:
        dashboard_data.append({
            "title": p["title"],
            "date": p["publish_date"],
            "region": p["region"],
            "source": "2025中国低空经济政策汇编",
            "category": p["chapter"],
            "issuer": p["issuer"],
            "summary": p["summary"][:200]
        })
    
    dp_path = os.path.join(os.path.expanduser("~/low-altitude-economy/dashboard"), "policy_data.json")
    with open(dp_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 看板数据已更新: {dp_path}")
    print(f"  {len(dashboard_data)} 条")
    
    # 预览
    print(f"\n📋 预览 (前10条):")
    for p in policies[:10]:
        print(f"  [{p['region']}] [{p['chapter']}] {p['title']}")
        print(f"    发文: {p['issuer']} | 发布: {p['publish_date']} | 生效: {p['effective_date']}")
        print(f"    摘要: {p['summary'][:80]}...")
        print()
    
    return policies

if __name__ == "__main__":
    main()
