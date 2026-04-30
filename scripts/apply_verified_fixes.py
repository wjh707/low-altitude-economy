#!/usr/bin/env python3
"""Apply verified URL fixes after rollback."""
import json

with open('dashboard/policy_data.json') as f:
    policies = json.load(f)

fixes = []

for i, p in enumerate(policies):
    title = p['title']
    url = p.get('url', '')
    changed = False
    
    # 1. 民用航空产品和零部件 - 已找到gov.cn真实链接
    if 't20240227_223980' in url and 'caac.gov.cn' in url:
        p['url'] = 'https://www.gov.cn/gongbao/2024/issue_11306/202404/content_6947723.html'
        fixes.append(f'✅ [{i}] 民用航空产品合格审定 - URL已修复')
        changed = True
    
    # 2. 江苏省 - 已找到正确文章ID
    if 'art_64797_11370493' in url and 'jiangsu.gov.cn' in url:
        p['url'] = 'https://www.jiangsu.gov.cn/art/2024/9/4/art_84418_11344150.html'
        fixes.append(f'✅ [{i}] 江苏省低空经济实施意见 - URL已修复')
        changed = True
    
    # 3. 四川省（abc123）- 用户给了sczgb.org.cn真实链接（已修复）
    if 'abc123' in url and 'sc.gov.cn' in url:
        p['url'] = 'https://sczgb.org.cn/nd.jsp?id=3627'
        fixes.append(f'✅ [{i}] 四川省支持低空经济措施 - URL已修复(用户提供)')
        changed = True
    
    # 4. 苏州 xxxxxx - 
    if 'xxxxxx' in url and 'suzhou.gov.cn' in url:
        if '低空飞行服务管理' in title:
            p['url'] = 'https://www.suzhou.gov.cn/szsrmzf/gbzfgfxwj/202412/d80bb09276c8477e8179c4c098248691.shtml'
            fixes.append(f'✅ [{i}] 苏州飞行服务管理办法 - URL已修复')
        elif '低空空中交通规则' in title:
            p['url'] = 'https://www.suzhou.gov.cn/szsrmzf/yjzj/202406/6867d06df44a4e459ce4ca926bfaeb3f.shtml'
            fixes.append(f'✅ [{i}] 苏州低空空中交通规则 - URL已修复')
        else:
            p['url'] = ''
            fixes.append(f'⚠️ [{i}] {title[:50]} - URL清空')
        changed = True
    
    # 5. 浙江省 - 404，换正确链接
    if 'art_1229017135_6006425' in url:
        p['url'] = 'https://www.zj.gov.cn/art/2024/8/7/art_1229017138_2526807.html'
        fixes.append(f'✅ [{i}] 浙江省民航强省意见 - URL已修复')
        changed = True
    
    # 6. 湖南省 - 404，换正确链接
    if 't20240628_33340205' in url:
        p['url'] = 'https://www.hunan.gov.cn/hnszf/szf/hnzb_18/c102939/202412/t20241204_33511679.html'
        fixes.append(f'✅ [{i}] 湖南省低空经济措施 - URL已修复')
        changed = True
    
    # 7. 四川省促进低空经济发展 - sc.gov.cn不可达，清空
    if '60349b1a' in url:
        p['url'] = ''
        fixes.append(f'⚠️ [{i}] 四川省低空经济指导意见 - 清空URL(sc.gov.cn不可达)')
        changed = True
    
    # 8. 广西 - 404，清空
    if '19184310' in url and 'gxzf.gov.cn' in url:
        p['url'] = ''
        fixes.append(f'⚠️ [{i}] 广西低空经济行动方案 - 清空URL(404)')
        changed = True
    
    if changed:
        print(fixes[-1])

with open('dashboard/policy_data.json', 'w') as f:
    json.dump(policies, f, ensure_ascii=False, indent=2)

print(f'\n共修复: {len(fixes)} 条')
