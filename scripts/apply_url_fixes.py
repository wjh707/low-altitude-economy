#!/usr/bin/env python3
"""Apply verified URL fixes and continue searching for remaining broken URLs."""
import json

with open('dashboard/policy_data.json') as f:
    policies = json.load(f)

# Verified URL fixes from subagent
fixes = {
    # 民用航空产品和零部件合格审定规定（2024修正）
    "民用航空产品和零部件合格审定规定": "https://www.gov.cn/gongbao/2024/issue_11306/202404/content_6947723.html",
    
    # 江苏省政府办公厅关于加快推动低空经济高质量发展的实施意见
    "江苏省政府办公厅关于加快推动低空经济高质量发展的实施意见": "https://www.jiangsu.gov.cn/art/2024/9/4/art_84418_11344150.html",
    
    # 苏州市委办公... / 苏州市低空经济高质量发展实施方案
    "苏州市低空经济高质量发展实施方案": "https://www.suzhou.gov.cn/szsrmzf/zfbgswj/202402/1ea65ae34733413ba188c04f8690267a.shtml",
    
    # 苏州市低空飞行服务管理办法（试行）
    "苏州市低空飞行服务管理办法": "https://www.suzhou.gov.cn/szsrmzf/gbzfgfxwj/202412/d80bb09276c8477e8179c4c098248691.shtml",
    
    # 苏州市低空空中交通规则（征求意见稿）
    "苏州市低空空中交通规则": "https://www.suzhou.gov.cn/szsrmzf/yjzj/202406/6867d06df44a4e459ce4ca926bfaeb3f.shtml",
    
    # 浙江省人民政府关于高水平建设民航强省打造低空经济发展高地的若干意见
    "浙江省人民政府关于高水平建设民航强省打造低空经济发展高地的若干意见": "https://www.zj.gov.cn/art/2024/8/7/art_1229017138_2526807.html",
    
    # 湖南省 - 子任务说404了，但提供了另一个链接
    "关于支持全省低空经济高质量发展的若干政策措施": "https://www.hunan.gov.cn/hnszf/szf/hnzb_18/c102939/202412/t20241204_33511679.html",
    
    # 广西 - 子任务没找到
    # 四川省 - sc.gov.cn不可达
}

applied = 0
not_found = []
for p in policies:
    url = p.get('url', '')
    title = p['title']
    
    for key, new_url in fixes.items():
        if key in title:
            if url != new_url:
                p['url'] = new_url
                applied += 1
                print(f'✅ 修复: {title[:50]}')
                print(f'   新URL: {new_url}')
            break
    else:
        # Check if this policy has a bad URL
        if url and ('xxxxxx' in url or 'abc123' in url or ('sc.gov.cn' in url and '60349b1a' in url) or url.endswith('_223980.html') or url.endswith('_11370493.html')):
            not_found.append((title, url))

with open('dashboard/policy_data.json', 'w') as f:
    json.dump(policies, f, ensure_ascii=False, indent=2)

print(f'\n已修复: {applied} 条')

if not_found:
    print(f'\n仍未修复 ({len(not_found)}条):')
    for t, u in not_found:
        print(f'  {t[:55]}')
        print(f'    旧: {u}')
