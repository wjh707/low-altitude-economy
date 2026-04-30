#!/usr/bin/env python3
"""
为有正文的政策政策生成独立HTML页面
输出到 dashboard/pages/ 目录
"""
import json, os, re

DATA_FILE = "/Users/zhoulai/low-altitude-economy/dashboard/policy_data.json"
ANCHOR_FILE = "/Users/zhoulai/low-altitude-economy/data/policies_anchor.json"
OUTPUT_DIR = "/Users/zhoulai/low-altitude-economy/dashboard/pages"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(DATA_FILE) as f:
    dashboard = json.load(f)

with open(ANCHOR_FILE) as f:
    anchor = json.load(f)

# 建立标题→anchor映射
anchor_map = {}
for a in anchor:
    anchor_map[a["title"][:40]] = a

generated = 0
for d in dashboard:
    title = d["title"]
    if d.get("url"):
        continue  # 有URL的不生成
    
    # 找对应的正文
    content = ""
    for key, a in anchor_map.items():
        if key in title or title[:40] in key:
            content = a.get("summary", "")
            break
    
    if not content or len(content) < 50:
        continue
    
    # 安全文件名
    safe = re.sub(r'[《》\(\)\s/\\:\.]', '_', title[:40]).strip('_')[:50]
    safe = safe or "policy_" + str(hash(title))[:8]
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f5f7fa;
    color: #333;
    line-height: 1.8;
    padding: 20px;
  }}
  .container {{
    max-width: 900px;
    margin: 0 auto;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    padding: 40px 48px;
  }}
  .header {{
    border-bottom: 2px solid #1a73e8;
    padding-bottom: 20px;
    margin-bottom: 24px;
  }}
  .title {{
    font-size: 22px;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 12px;
  }}
  .meta {{
    color: #666;
    font-size: 13px;
    line-height: 2;
  }}
  .meta span {{
    display: inline-block;
    margin-right: 20px;
  }}
  .meta .label {{
    color: #999;
  }}
  .content {{
    font-size: 15px;
    line-height: 2;
    text-align: justify;
  }}
  .content p {{
    margin-bottom: 12px;
    text-indent: 2em;
  }}
  .back {{
    display: inline-block;
    margin-bottom: 20px;
    color: #1a73e8;
    text-decoration: none;
    font-size: 14px;
  }}
  .back:hover {{ text-decoration: underline; }}
  .tags {{
    margin: 16px 0;
  }}
  .tag {{
    display: inline-block;
    background: #e8f0fe;
    color: #1967d2;
    font-size: 12px;
    padding: 3px 10px;
    border-radius: 12px;
    margin: 2px 4px;
  }}
  @media (max-width: 640px) {{
    .container {{ padding: 20px 16px; }}
    .title {{ font-size: 18px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <a class="back" href="../index.html">← 返回政策看板</a>
  <div class="header">
    <div class="title">{title}</div>
    <div class="meta">
      <span><span class="label">地区：</span>{d.get("region", "全国")}</span>
      <span><span class="label">类别：</span>{d.get("category", "其他")}</span>
      <span><span class="label">来源：</span>2025中国低空经济政策汇编</span>
      <span><span class="label">日期：</span>{d.get("date", "--")}</span>
    </div>
    <div class="tags">
      {''.join(f'<span class="tag">{t}</span>' for t in d.get("policy_tools", []))}
    </div>
  </div>
  <div class="content">
    {''.join(f'<p>{p}</p>' for p in content.split('\\n') if p.strip())}
  </div>
</div>
</body>
</html>'''
    
    filepath = os.path.join(OUTPUT_DIR, safe + ".html")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # 更新看板数据中的local_page
    d["local_page"] = "pages/" + safe + ".html"
    generated += 1

# 保存更新后的看板数据
with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(dashboard, f, ensure_ascii=False, indent=2)

print(f"✅ 生成了 {generated} 个本地页面")
print(f"📁 位置: {OUTPUT_DIR}")
print(f"📊 看板数据: {len(dashboard)} 条")
print(f"  有URL: {sum(1 for d in dashboard if d.get('url'))}")
print(f"  有本地页面: {sum(1 for d in dashboard if d.get('local_page'))}")
