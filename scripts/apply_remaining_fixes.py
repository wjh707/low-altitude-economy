#!/usr/bin/env python3
"""Apply remaining URL fixes or clear bad URLs."""
import json

with open('dashboard/policy_data.json') as f:
    policies = json.load(f)

changes = 0

for i, p in enumerate(policies):
    title = p['title']
    url = p.get('url', '')
    
    # 1. 四川省 - 清空URL（sc.gov.cn不可达）
    if '60349b1a' in url and 'sc.gov.cn' in url:
        old = url
        p['url'] = ''
        print(f'❌ [69] 四川省促进低空经济发展指导意见 - 清空URL')
        changes += 1
    
    # 2. 广西 - 404，清空
    if 'gxzf.gov.cn' in url and '19184310' in url:
        p['url'] = ''
        print(f'❌ [74] 广西低空经济行动方案 - 清空URL')
        changes += 1
    
    # 3. 苏州[25] - 标题有残留，清理标题并使用找到的URL
    if 'xxxxxx' in url and 'suzhou' in url and ('202404' in url):
        p['url'] = 'https://www.suzhou.gov.cn/szsrmzf/zfbgswj/202402/1ea65ae34733413ba188c04f8690267a.shtml'
        # 清理标题中的残留
        p['title'] = '市政府办公室关于印发苏州市低空经济高质量发展实施方案（2024～2026年）的通知'
        print(f'✅ [25] 苏州低空经济实施方案 - URL已修复')
        changes += 1
    
    # 4. 苏州[56] - 查看是否为重复
    if 'xxxxxx' in url and '202410' in url:
        # 检查完整标题
        if '低空飞行服务管理' in title or '2024.12.01' in title:
            p['url'] = 'https://www.suzhou.gov.cn/szsrmzf/gbzfgfxwj/202412/d80bb09276c8477e8179c4c098248691.shtml'
            print(f'✅ [56] 苏州低空飞行服务管理 - URL已修复')
            changes += 1
    
    # 5. 深圳jtys.sz.gov.cn SSL错误 - 保留但标注
    if 'jtys.sz.gov.cn' in url and 'post_11076249' in url:
        # 保留，因为SSL问题是环境问题，不一定对用户不可用
        print(f'⚠️ [77] 深圳市低空经济措施 - SSL问题，保留URL')
    
    # 6. 海南连接被重置 - 保留
    if 'hainan.gov.cn' in url and '20231007' in url:
        print(f'⚠️ [78] 海南省无人机管理 - 连接被重置，保留URL')
    
    # 7. 深圳sf.sz.gov.cn SSL错误 - 保留
    if 'sf.sz.gov.cn' in url and '2969335' in url:
        print(f'⚠️ [113] 深圳微轻型无人机 - SSL问题，保留URL')

with open('dashboard/policy_data.json', 'w') as f:
    json.dump(policies, f, ensure_ascii=False, indent=2)

print(f'\n共修改: {changes} 条')
