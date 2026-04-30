#!/usr/bin/env python3
"""
PDF政策汇编解析器 — 锚点法
直接用"发文机关"作为锚点，精确提取每条政策
"""
import re, json, os

PDF_PATH = os.path.expanduser("~/.hermes/cache/documents/doc_5e33ec52d2c0_2025中国低空经济法律、法规、政策文件汇编.pdf")
OUTPUT_DIR = os.path.expanduser("~/low-altitude-economy/data")
DASHBOARD_DIR = os.path.expanduser("~/low-altitude-economy/dashboard")

def load_pdf(p):
    import fitz
    doc = fitz.open(p)
    pages = []
    for i in range(len(doc)):
        text = doc[i].get_text("text")
        # 去页码行
        clean_lines = [l for l in text.split('\n') if not re.match(r'^\d{1,4}$', l.strip())]
        pages.append({"page": i+1, "text": '\n'.join(clean_lines)})
    doc.close()
    return pages

def extract_all_policies(pages):
    """
    核心算法：扫描14-210页，以"发文机关"锚点切分政策
    每遇到一个"发文机关"，就是新政策的开始
    """
    policies = []
    current = None
    
    for p in pages:
        page_num = p["page"]
        text = p["text"]
        
        # 查找"发文机关"锚点
        if '发文机关' in text or '第一章' in text or re.search(r'\d+[、\.]\s*\S', text[:200]):
            # 检测是否是政策起点
            is_new_policy = False
            
            # 标记1: 包含"发文机关"
            if '发文机关' in text:
                is_new_policy = True
            
            # 标记2: 页首有"第一章"（每章第一个政策）
            if page_num > 13 and '第一章' in text[:100]:
                is_new_policy = True
            
            if is_new_policy:
                if current and current.get("lines"):
                    policies.append(current)
                
                # 提取政策标题（发文机关前面那行）
                lines = text.split('\n')
                title_line = ""
                meta = {"issuer": "", "publish_date": "", "effective_date": "", "validity": ""}
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # 找政策标题行（发文机关前面那行）
                    if '发文机关' in line:
                        # 向上找标题
                        for j in range(i-1, max(i-5, -1), -1):
                            candidate = lines[j].strip()
                            if candidate and not re.match(r'^[一二三四五六七八九十]+[、\.]', candidate) and not candidate.startswith('第一章') and not candidate.startswith('第二章'):
                                title_line = candidate
                                break
                        
                        # 提取元数据
                        meta["issuer"] = line.split('：')[-1] if '：' in line else line.split(':')[-1]
                    
                    if '发布日期' in line:
                        meta["publish_date"] = line.split('：')[-1] if '：' in line else line.split(':')[-1]
                    if '生效日期' in line:
                        meta["effective_date"] = line.split('：')[-1] if '：' in line else line.split(':')[-1]
                    if '时效性' in line:
                        meta["validity"] = line.split('：')[-1] if '：' in line else line.split(':')[-1]
                
                current = {
                    "title": title_line,
                    "start_page": page_num,
                    **meta,
                    "lines": [text]
                }
                continue
        
        if current:
            current["lines"].append(text)
    
    # 最后一条
    if current and current.get("lines"):
        policies.append(current)
    
    return policies

def parse_chapter_and_region(text):
    """从政策开头的章节标记提取分类和地区"""
    chapter = ""
    region = "全国"
    
    lines = text.split('\n')[:5]
    for line in lines:
        if '第一章' in line:
            chapter = "法律"
        elif '第二章' in line:
            region = "地方"
            # 继续判断
            if '北京' in line: region = "北京市"
            elif '上海' in line: region = "上海市" 
            elif '广东' in line: region = "广东省"
            elif '浙江' in line: region = "浙江省"
            elif '江苏' in line: region = "江苏省"
            elif '湖南' in line: region = "湖南省"
            elif '福建' in line: region = "福建省"
        
        m = re.match(r'[一二三四五六七八九十]+[、\.]\s*(法律|行政法规|部门规章|规范性文件|政策文件)', line)
        if m:
            chapter = m.group(1)
            if '规范性文件' in chapter:
                chapter = '规范性文件'
            break
    
    return chapter, region

def categorize_by_title(title):
    rules = [
        (r'法$', "法律"),
        (r'条例', "行政法规"),
        (r'规定|办法|细则', "部门规章"),
        (r'通知|意见|纲要|规划|方案|措施', "政策文件"),
        (r'标准|指南|规范', "技术规范"),
    ]
    for pat, cat in rules:
        if re.search(pat, title):
            return cat
    return "政策文件"

def extract_date(policy):
    """从发布日期和标题提取年份"""
    d = policy.get("publish_date", "")
    if d:
        m = re.match(r'(\d{4})', d)
        if m:
            return m.group(1) + "年"
    m = re.search(r'(20\d{2})', policy.get("title", ""))
    if m:
        return m.group(1) + "年"
    return ""

def main():
    print("=" * 60)
    print("政策正文提取 — 锚点法")
    print("=" * 60)
    
    print("\n[1/3] 加载PDF...")
    pages = load_pdf(PDF_PATH)
    print(f"  共 {len(pages)} 页")
    
    print("\n[2/3] 锚点提取政策...")
    policies = extract_all_policies(pages)
    print(f"  提取到 {len(policies)} 条政策")
    
    # 清理和去重
    clean = []
    seen = set()
    for p in policies:
        title = p["title"]
        if not title or len(title) < 4:
            continue
        # 去重
        key = re.sub(r'[《》（）\s]', '', title)[:20]
        if key in seen:
            continue
        seen.add(key)
        
        category = categorize_by_title(title)
        
        # 推测地区
        region = "全国"
        for kw, prov in [
            ("北京", "北京市"), ("上海", "上海市"), ("天津", "天津市"), ("重庆", "重庆市"),
            ("广东", "广东省"), ("深圳", "广东省"), ("广州", "广东省"), ("珠海", "广东省"),
            ("浙江", "浙江省"), ("杭州", "浙江省"), ("嘉兴", "浙江省"),
            ("江苏", "江苏省"), ("南京", "江苏省"), ("苏州", "江苏省"),
            ("湖南", "湖南省"), ("长沙", "湖南省"),
            ("福建", "福建省"), ("厦门", "福建省"), ("福州", "福建省"),
            ("四川", "四川省"), ("成都", "四川省"),
            ("安徽", "安徽省"), ("合肥", "安徽省"),
            ("山东", "山东省"),
            ("江西", "江西省"),
            ("海南", "海南省"),
            ("河北", "河北省"),
            ("山西", "山西省"),
            ("新疆", "新疆"),
            ("辽宁", "辽宁省"),
        ]:
            if kw in title:
                region = prov
                break
        
        clean.append({
            "title": title,
            "category": category,
            "region": region,
            "level": "国家" if region == "全国" else "地方",
            "issuer": p.get("issuer", ""),
            "publish_date": p.get("publish_date", ""),
            "effective_date": p.get("effective_date", ""),
            "validity": p.get("validity", ""),
            "start_page": p.get("start_page", 0),
            "content_length": sum(len(l) for l in p.get("lines", [])),
            "summary": (p.get("lines", [""])[0][:500] if p.get("lines") else "")[:500]
        })
    
    print(f"  清洗后: {len(clean)} 条")
    print(f"  国家: {sum(1 for c in clean if c['level']=='国家')} 条")
    print(f"  地方: {sum(1 for c in clean if c['level']=='地方')} 条")
    print(f"  有发文机关: {sum(1 for c in clean if c['issuer'])} 条")
    print(f"  有发布日期: {sum(1 for c in clean if c['publish_date'])} 条")
    
    # 保存
    print("\n[3/3] 保存...")
    
    # 完整数据
    with open(os.path.join(OUTPUT_DIR, "policies_anchor.json"), 'w', encoding='utf-8') as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 完整数据: data/policies_anchor.json")
    
    # 看板数据
    dashboard = []
    for c in clean:
        dashboard.append({
            "title": c["title"],
            "date": c["publish_date"] or extract_date(c),
            "region": c["region"],
            "source": "2025中国低空经济政策汇编",
            "category": c["category"],
            "issuer": c["issuer"],
            "summary": c["summary"][:200]
        })
    
    with open(os.path.join(DASHBOARD_DIR, "policy_data.json"), 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 看板数据更新: {len(dashboard)} 条")
    
    # 预览
    print(f"\n📋 前15条:")
    for c in clean[:15]:
        print(f"  [{c['region']}] [{c['category']}] {c['title'][:50]}")
        print(f"    {c['issuer']} | {c['publish_date']} | 正文{c['content_length']}字")
    
    return clean

if __name__ == "__main__":
    main()
