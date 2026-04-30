#!/usr/bin/env python3
"""
PDF全文提取器 — 提取政策正文内容
策略：跳过封面前言目录，识别每章标题，提取正文段落
"""
import re, json, os

PDF_PATH = os.path.expanduser(
    "~/.hermes/cache/documents/doc_5e33ec52d2c0_2025中国低空经济法律、法规、政策文件汇编.pdf"
)
OUTPUT_DIR = os.path.expanduser("~/low-altitude-economy/data")

def extract(pdf_path):
    import fitz
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append({"page": i + 1, "text": text})
    doc.close()
    return pages

def extract_full_text(pages):
    """提取全文，跳过封面/前言/目录"""
    # 找正文起始页：跳过前N页的封面+前言+目录
    # 目录一般在 "第一编" 之前结束
    full_text_pages = []
    skip = True
    
    for p in pages:
        text = p["text"]
        page_num = p["page"]
        
        # 跳过封面/前言/目录：直到出现 "第一编"
        if skip and ("第一编" in text):
            skip = False
        
        if not skip:
            full_text_pages.append({
                "page": page_num,
                "text": text
            })
    
    return full_text_pages

def split_by_categories(pages):
    """
    把全文切分为章节块
    输出: [{ "part": "第一编", "chapters": [...] }]
    """
    # 识别编标题和页范围
    parts = []
    current_part = None
    current_part_pages = []
    
    for p in pages:
        text = p["text"]
        page_num = p["page"]
        
        # 检测 "第X编" 标题行
        m = re.search(r'^第[一二三四五六七八九十]+编(.+)$', text, re.MULTILINE)
        if m:
            if current_part:
                parts.append({"name": current_part, "pages": current_part_pages})
            current_part = m.group(0).strip()
            current_part_pages = [p]
        else:
            # 也可以匹配页眉
            m2 = re.search(r'第[一二三四五六七八九十]+编\s+', text)
            if m2 and current_part is None:
                current_part = m2.group(0).strip()
                current_part_pages = [p]
            else:
                if current_part:
                    current_part_pages.append(p)
                else:
                    current_part_pages.append(p)
    
    if current_part and current_part_pages:
        parts.append({"name": current_part, "pages": current_part_pages})
    
    return parts

def extract_policy_content(pages):
    """
    提取每条政策的全文
    基于PDF的排版特征：政策标题后跟正文段落
    """
    policies = []
    current_policy = None
    
    for p in pages:
        text = p["text"]
        page_num = p["page"]
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # 跳过页眉/页脚
            if re.match(r'^\d{1,4}$', line):  # 页码
                continue
            if '编' in line and len(line) < 20:  # 编标题
                continue
            if re.match(r'第[一二三四五六七八九十]+章', line):  # 章标题
                continue
            
            # 检测政策标题：《XXX》
            m = re.match(r'.*?《([^》]+)》', line)
            if m and len(line) < 100:
                # 新的政策开始
                if current_policy:
                    policies.append(current_policy)
                title = m.group(1).strip()
                current_policy = {
                    "title": title,
                    "content": [line],
                    "start_page": page_num
                }
            elif current_policy:
                # 正文延续
                current_policy["content"].append(line)
    
    if current_policy:
        policies.append(current_policy)
    
    return policies

def main():
    print("=" * 60)
    print("PDF全文提取")
    print("=" * 60)
    
    print("\n[1/3] 提取PDF文本...")
    pages = extract(PDF_PATH)
    print(f"  共 {len(pages)} 页")
    
    print("\n[2/3] 跳过前言目录...")
    content_pages = extract_full_text(pages)
    print(f"  正文从第{content_pages[0]['page']}页开始，共{len(content_pages)}页")
    
    print("\n[3/3] 提取政策内容...")
    parts = split_by_categories(content_pages)
    print(f"  识别到 {len(parts)} 个编")
    
    policies = extract_policy_content(content_pages)
    print(f"  提取到 {len(policies)} 条政策（含正文）")
    
    # 输出样例
    print(f"\n📋 样例:")
    for p in policies[:5]:
        content_len = sum(len(l) for l in p["content"])
        print(f"  [{p['start_page']}页] {p['title']} ({content_len}字)")
    
    # 保存全文JSON（每条带内容）
    output = []
    for p in policies[:50]:  # 先保存50条样例
        output.append({
            "title": p["title"],
            "content": "\n".join(p["content"][:200]),  # 最多200行
            "page": p["start_page"]
        })
    
    output_path = os.path.join(OUTPUT_DIR, "parsed_with_content.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  已保存50条含正文的数据到: {output_path}")
    
    return policies

if __name__ == "__main__":
    main()
