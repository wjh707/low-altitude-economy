#!/usr/bin/env python3
"""Correctly fix remaining policy URLs - careful not to mix up different policies."""
import json

with open('dashboard/policy_data.json') as f:
    policies = json.load(f)

fixes = {}

for i, p in enumerate(policies):
    title = p['title']
    url = p.get('url', '')
    
    # ===== [25] 苏州市支持低空经济高质量发展的若干措施（试行）- 标题有PDF残留 =====
    if '市委办公' in title and '苏州市支持低空经济高质量发展' in title:
        # 只清理标题，不碰URL（因为没有，清空）
        clean = title.split(' ')[-1] if ' ' in title else title
        # 去掉前面的垃圾数字
        import re
        clean = re.sub(r'^[^市]*', '', title)
        if '市政府办公室' not in clean:
            clean = '市政府办公室关于印发《苏州市支持低空经济高质量发展的若干措施（试行）》的通知（2024.04.17）'
        p['title'] = clean
        fixes[i] = ('【25】标题已清理', 'URL暂缺（未找到suzhou.gov.cn原文）')
    
    # ===== [56] 知（2024.12.01）- 标题不完整 =====
    if title == '知（2024.12.01）':
        p['title'] = '苏州市人民政府关于印发苏州市低空飞行服务管理办法（试行）的通知（2024.12.01）'
        fixes[i] = ('【56】标题已补全', 'URL已修复')

    # ===== 苏州 xxxxxx URL修复 =====
    if 'xxxxxx' in url and 'suzhou' in url:
        if '低空飞行服务管理' in title and '2024.12.01' in title:
            p['url'] = 'https://www.suzhou.gov.cn/szsrmzf/gbzfgfxwj/202412/d80bb09276c8477e8179c4c098248691.shtml'
            fixes[i] = ('【56】URL已修复', p['url'])
        elif '苏州市低空空中交通规则' in title:
            p['url'] = 'https://www.suzhou.gov.cn/szsrmzf/yjzj/202406/6867d06df44a4e459ce4ca926bfaeb3f.shtml'
            fixes[i] = ('【27】URL已修复', p['url'])
        elif '支持低空经济高质量发展' in title:
            # 清空，找不到suzhou.gov.cn原文
            p['url'] = ''
            fixes[i] = ('【25】URL清空', '找不到suzhou.gov.cn原文')
        else:
            p['url'] = ''
            fixes[i] = (f'【{i}】URL清空', f'未知条目: {title[:40]}')
    
    # ===== 四川省 - sc.gov.cn虚假URL =====
    if '60349b1a' in url and 'sc.gov.cn' in url:
        p['url'] = ''
        fixes[i] = ('【69】URL清空', 'sc.gov.cn不可达')
    
    # ===== 广西 - 404 =====
    if 'gxzf.gov.cn' in url and '19184310' in url:
        p['url'] = ''
        fixes[i] = ('【74】URL清空', '404')
    
    # ===== 湖南省 - 404 =====
    if 'hunan.gov.cn' in url and 't20240628_33340205' in url:
        p['url'] = ''
        fixes[i] = ('【70】URL清空', '404')

# 单独修复苏州低空飞行服务管理办法的第二个条目（它和[56]可能是同一文件）
for i, p in enumerate(policies):
    title = p['title']
    url = p.get('url', '')
    if '苏州市低空飞行服务管理办法' in title and 'xxxxxx' in url:
        p['url'] = 'https://www.suzhou.gov.cn/szsrmzf/gbzfgfxwj/202412/d80bb09276c8477e8179c4c098248691.shtml'
        fixes[i] = (f'【{i}】URL已修复', p['url'])

with open('dashboard/policy_data.json', 'w') as f:
    json.dump(policies, f, ensure_ascii=False, indent=2)

print('=== 修复结果 ===')
for idx, (action, detail) in sorted(fixes.items()):
    print(f'  {action}')
    print(f'    {detail}')
