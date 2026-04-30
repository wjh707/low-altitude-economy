#!/usr/bin/env python3
"""
从PDF正文提取未搜到条目的内容
同时生成最终看板数据
"""
import re, json, os
import fitz

PDF_PATH = os.path.expanduser("~/.hermes/cache/documents/doc_5e33ec52d2c0_2025中国低空经济法律、法规、政策文件汇编.pdf")
OUTPUT = os.path.expanduser("~/low-altitude-economy/dashboard/policy_data.json")

def get_page_text(page_num):
    """获取指定页的文本"""
    doc = fitz.open(PDF_PATH)
    text = ""
    if 0 <= page_num - 1 < len(doc):
        text = doc[page_num - 1].get_text("text")
    doc.close()
    return text

def extract_title_from_page(page_num):
    """从指定页提取政策标题"""
    text = get_page_text(page_num)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        # 找 "数字、标题（日期）" 格式
        m = re.match(r'(\d+)[、\.]\s*(.*)', line)
        if m:
            title = m.group(2).strip()
            # 去掉末尾的页码数字
            title = re.sub(r'\s+\d{1,4}\s*$', '', title)
            return title
    return ""

def extract_meta_from_page(page_num):
    """从页面提取元数据（发文机关、日期等）"""
    text = get_page_text(page_num)
    meta = {"issuer": "", "publish_date": ""}
    
    for line in text.split('\n'):
        line = line.strip()
        if '发文机关' in line:
            meta["issuer"] = line.split('：')[-1] if '：' in line else line.split(':')[-1]
        if '发布日期' in line:
            meta["publish_date"] = line.split('：')[-1] if '：' in line else line.split(':')[-1]
    
    return meta

def categories():
    with open("/Users/zhoulai/low-altitude-economy/data/toc_entries.json") as f:
        toc = json.load(f)

    # 收集搜索结果
    all_results = {}
    for i in range(1, 4):
        path = f"/Users/zhoulai/low-altitude-economy/data/search_batch{i}_result.json"
        if os.path.exists(path):
            with open(path) as f:
                for item in json.load(f):
                    title_key = item.get("title", "")[:40]
                    all_results[title_key] = item

    # 生成看板数据
    dashboard = []

    for item in toc:
        title_clean = item["title"].strip()
        title_clean = re.sub(r'[\.\s]{3,}\d{1,4}\s*$', '', title_clean)
        title_clean = re.sub(r'\s{2,}', ' ', title_clean)
        if not title_clean or len(title_clean) < 5:
            continue

        page = item.get("page", 0)
        category = item.get("category", "其他")
        region = item.get("region", "全国")

        # 法律/行政法规不搜
        if category in ["法律", "行政法规"]:
            dashboard.append({
                "title": title_clean,
                "date": "",
                "region": region,
                "source": "2025中国低空经济政策汇编",
                "category": category,
                "url": "",
                "note": "无需搜索"
            })
            continue

        # 查搜索结果
        sr = None
        for k, v in all_results.items():
            if k in title_clean or title_clean[:30] in k:
                sr = v
                break

        url = ""
        date = ""
        issuer = ""

        if sr and sr.get("status") == "found":
            url = sr.get("url", "")
        
        # 有页码的从正文提取详情
        if page and page > 0 and page <= 1869:
            meta = extract_meta_from_page(page)
            title_from_page = extract_title_from_page(page)
            if title_from_page and len(title_from_page) > len(title_clean):
                title_clean = title_from_page
            date = meta.get("publish_date", "")
        
        dashboard.append({
            "title": title_clean,
            "date": date,
            "region": region,
            "source": "2025中国低空经济政策汇编",
            "category": category,
            "url": url,
            "issuer": issuer
        })

    # 去重
    seen = set()
    deduped = []
    for d in dashboard:
        key = re.sub(r'[\s《》（）\(\)''"【】]', '', d["title"])[:25]
        if key not in seen:
            seen.add(key)
            deduped.append(d)

    # 保存
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)

    # 统计
    with_url = sum(1 for d in deduped if d.get("url"))
    without_url = sum(1 for d in deduped if not d.get("url"))
    print(f"看板数据总量: {len(deduped)} 条")
    print(f"已有URL: {with_url} 条")
    print(f"无URL: {without_url} 条")
    
    regions = {}
    cats = {}
    for d in deduped:
        regions[d["region"]] = regions.get(d["region"], 0) + 1
        cats[d["category"]] = cats.get(d["category"], 0) + 1
    
    print(f"\n地区分布:")
    for r, c in sorted(regions.items(), key=lambda x: -x[1]):
        print(f"  {r}: {c}")
    print(f"\n类别分布:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")

    return deduped

if __name__ == "__main__":
    result = categories()
