#!/usr/bin/env python3
"""
清洗目录条目，分类：法律/行政法规不搜，其余需要搜索
输出三个JSON文件：
- no_search.json: 法律+行政法规（14条）
- needs_search.json: 需要搜索的（约148条）
"""
import re, json

with open("/Users/zhoulai/low-altitude-economy/data/toc_entries.json") as f:
    entries = json.load(f)

def clean_title(t):
    """清洗标题：去掉页码点和多余空格"""
    # 去掉末尾的页码点（....123）
    t = re.sub(r'[\.\s]{3,}\d{1,4}\s*$', '', t)
    t = re.sub(r'\s{2,}', ' ', t)
    # 去掉末尾的页码数字（单独数字）
    t = re.sub(r'\s+\d{1,3}\s*$', '', t)
    t = t.strip()
    return t

# 清洗标题
for e in entries:
    e["title"] = clean_title(e["title"])

# 分类
no_search = []   # 法律+行政法规
needs_search = [] # 需要搜索的

for e in entries:
    cat = e.get("category", "")
    title = e["title"]
    
    # 法律+行政法规：不搜
    if cat in ["法律", "行政法规"]:
        no_search.append(e)
        continue
    
    # 地方性法规：需要搜（各地自己的条例）
    if "条例" in title or "地方性法规" in cat:
        needs_search.append(e)
        continue
    
    # 其余全部需要搜索
    needs_search.append(e)

print(f"无需搜索(法律+行政法规): {len(no_search)} 条")
print(f"需要搜索: {len(needs_search)} 条")

# 输出无需搜索的
with open("/Users/zhoulai/low-altitude-economy/data/no_search.json", 'w', encoding='utf-8') as f:
    json.dump(no_search, f, ensure_ascii=False, indent=2)

# 输出需要搜索的
with open("/Users/zhoulai/low-altitude-economy/data/needs_search.json", 'w', encoding='utf-8') as f:
    json.dump(needs_search, f, ensure_ascii=False, indent=2)

print(f"\n📋 无需搜索的:")
for e in no_search:
    print(f"  [{e['region']}] {e['title'][:50]}")

print(f"\n📋 需要搜索的 (前20条):")
for e in needs_search[:20]:
    print(f"  [{e['region']}] [{e['category']}] {e['title'][:60]}")
print(f"  ...共{len(needs_search)}条")

# 检查法律里有没有混入奇怪的
for e in no_search:
    if e["category"] == "法律":
        print(f"  法律: {e['title'][:60]}")
