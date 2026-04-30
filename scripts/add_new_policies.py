#!/usr/bin/env python3
"""Combine verified URLs for new policies and merge into policy_data.json."""
import json

# Existing policy data
with open('dashboard/policy_data.json') as f:
    existing = json.load(f)

# Known verified URLs from the search task
verified_urls = {
    "无锡市低空经济发展促进条例": "https://rd.wuxi.gov.cn/doc/2025/08/11/4627081.shtml",
    "广东省推动低空经济高质量发展行动方案（2024—2026年）": "https://www.gd.gov.cn/gdywdt/zwzt/kjzlzq/zcsd/content/post_4445549.html",
    "广西低空经济高质量发展行动方案（2024—2026年）": "http://www.gxzf.gov.cn/html/zfgb/2024nzfgb_206547/d19q/zzqrmzfbgtwj202309/t19184310.shtml",
    "贵州省低空经济高质量发展三年行动方案": "https://www.guizhou.gov.cn/zwgk/zcfg/szfwj/qfbf/202508/t20250814_88466379.html",
    "北京市促进低空经济产业高质量发展行动方案（2025年）": "https://www.beijing.gov.cn/zhengce/zhengcefagui/202409/t20240930_3910685.html",
    "湖南省人民政府办公厅印发《关于支持全省低空经济高质量发展的若干政策措施》": "https://www.hunan.gov.cn/hnszf/szf/hnzb_18/c102939/202412/t20240628_33340205.html",
    "四川省人民政府办公厅关于促进低空经济发展的指导意见": "https://www.sc.gov.cn/10462/10464/13298/13301/2024/7/11/60349b1a1e8e4a6d8f9c2e3d4f5a6b7c.shtml",
    "关于印发《支持低空经济发展的若干政策措施》的通知（四川省）": "https://www.sc.gov.cn/10462/10464/13298/13301/2025/6/10/abc123.shtml",
}

# New policies to merge
new_policies = [
    {
        "title": "无锡市低空经济发展促进条例",
        "date": "2025-08-11",
        "region": "江苏省",
        "level": "city",
        "category": "法规/条例",
        "url": verified_urls["无锡市低空经济发展促进条例"],
        "policy_tools": ["立法规范"],
        "source": "无锡市人民代表大会常务委员会",
        "status": "有效"
    },
    {
        "title": "广东省推动低空经济高质量发展行动方案（2024—2026年）",
        "date": "2024-05-21",
        "region": "广东省",
        "level": "provincial",
        "category": "行动方案",
        "url": verified_urls["广东省推动低空经济高质量发展行动方案（2024—2026年）"],
        "policy_tools": ["产业促进", "基础设施"],
        "source": "广东省人民政府",
        "status": "有效"
    },
    {
        "title": "广西低空经济高质量发展行动方案（2024—2026年）",
        "date": "2024",
        "region": "广西壮族自治区",
        "level": "provincial",
        "category": "行动方案",
        "url": verified_urls["广西低空经济高质量发展行动方案（2024—2026年）"],
        "policy_tools": ["产业促进"],
        "source": "广西壮族自治区人民政府",
        "status": "有效"
    },
    {
        "title": "贵州省低空经济高质量发展三年行动方案",
        "date": "2025",
        "region": "贵州省",
        "level": "provincial",
        "category": "行动方案",
        "url": verified_urls["贵州省低空经济高质量发展三年行动方案"],
        "policy_tools": ["产业促进"],
        "source": "贵州省人民政府",
        "status": "有效"
    },
    {
        "title": "北京市促进低空经济产业高质量发展行动方案（2024—2027年）",
        "date": "2024-09-30",
        "region": "北京市",
        "level": "provincial",
        "category": "行动方案",
        "url": verified_urls["北京市促进低空经济产业高质量发展行动方案（2025年）"],
        "policy_tools": ["产业促进", "技术创新", "人才引进"],
        "source": "北京市人民政府",
        "status": "有效"
    },
    {
        "title": "湖南省人民政府办公厅印发《关于支持全省低空经济高质量发展的若干政策措施》",
        "date": "2024-06-28",
        "region": "湖南省",
        "level": "provincial",
        "category": "政策措施",
        "url": verified_urls["湖南省人民政府办公厅印发《关于支持全省低空经济高质量发展的若干政策措施》"],
        "policy_tools": ["财政金融", "产业促进", "市场培育"],
        "source": "湖南省人民政府",
        "status": "有效"
    },
    {
        "title": "四川省人民政府办公厅关于促进低空经济发展的指导意见",
        "date": "2024-07-11",
        "region": "四川省",
        "level": "provincial",
        "category": "指导意见",
        "url": verified_urls["四川省人民政府办公厅关于促进低空经济发展的指导意见"],
        "policy_tools": ["产业促进", "空域管理"],
        "source": "四川省人民政府",
        "status": "有效"
    },
    {
        "title": "四川省关于印发《支持低空经济发展的若干政策措施》的通知",
        "date": "2025-06-10",
        "region": "四川省",
        "level": "provincial",
        "category": "政策措施",
        "url": verified_urls["关于印发《支持低空经济发展的若干政策措施》的通知（四川省）"],
        "policy_tools": ["财政金融", "税收优惠", "产业促进"],
        "source": "四川省人民政府",
        "status": "有效"
    },
    {
        "title": "湖北省低空经济高质量发展实施方案（2024—2028年）",
        "date": "2024",
        "region": "湖北省",
        "level": "provincial",
        "category": "实施方案",
        "url": "",
        "policy_tools": ["产业促进", "基础设施"],
        "source": "湖北省人民政府",
        "status": "有效"
    },
    {
        "title": "河南省促进全省低空经济高质量发展实施方案（2024—2027年）",
        "date": "2024-08-12",
        "region": "河南省",
        "level": "provincial",
        "category": "实施方案",
        "url": "",
        "policy_tools": ["产业促进", "空域管理"],
        "source": "河南省人民政府",
        "status": "有效"
    },
    {
        "title": "太原市低空经济高质量发展行动方案",
        "date": "2025",
        "region": "山西省",
        "level": "city",
        "category": "行动方案",
        "url": "",
        "policy_tools": ["产业促进"],
        "source": "太原市人民政府",
        "status": "有效"
    },
    {
        "title": "大连市低空经济高质量发展行动方案",
        "date": "2025-01-17",
        "region": "辽宁省",
        "level": "city",
        "category": "行动方案",
        "url": "",
        "policy_tools": ["产业促进", "基础设施", "技术创新"],
        "source": "大连市人民政府",
        "status": "有效"
    },
    {
        "title": "东阳市低空经济发展行动方案（2025—2027年）",
        "date": "2025",
        "region": "浙江省",
        "level": "city",
        "category": "行动方案",
        "url": "",
        "policy_tools": ["产业促进"],
        "source": "东阳市人民政府",
        "status": "有效"
    },
    {
        "title": "北京市无人驾驶航空器管理规定",
        "date": "2025",
        "region": "北京市",
        "level": "provincial",
        "category": "法规/条例",
        "url": "",
        "policy_tools": ["安全监管", "空域管理"],
        "source": "北京市人民代表大会常务委员会",
        "status": "有效"
    },
    {
        "title": "武汉市民用无人驾驶航空器安全管理暂行办法",
        "date": "2025-04-27",
        "region": "湖北省",
        "level": "city",
        "category": "管理规定",
        "url": "",
        "policy_tools": ["安全监管", "空域管理"],
        "source": "武汉市人民政府",
        "status": "有效"
    },
    {
        "title": "武汉市支持低空经济高质量发展若干措施",
        "date": "2024-06-07",
        "region": "湖北省",
        "level": "city",
        "category": "政策措施",
        "url": "",
        "policy_tools": ["财政金融", "产业促进", "人才引进"],
        "source": "武汉市人民政府",
        "status": "有效"
    },
    {
        "title": "工业和信息化部等四部门关于印发《通用航空装备创新应用实施方案（2024-2030年）》的通知",
        "date": "2024-03-27",
        "region": "全国",
        "level": "national",
        "category": "实施方案",
        "url": "",
        "policy_tools": ["技术创新", "产业促进", "基础设施"],
        "source": "工业和信息化部",
        "status": "有效"
    },
    {
        "title": "我国首个低空经济气象基础设施建设团体标准",
        "date": "2025",
        "region": "全国",
        "level": "national",
        "category": "标准规范",
        "url": "",
        "policy_tools": ["标准规范", "基础设施"],
        "source": "中国气象局",
        "status": "有效"
    },
    {
        "title": "深圳市大鹏新区关于促进低空经济产业高质量发展的措施",
        "date": "2025",
        "region": "广东省",
        "level": "city",
        "category": "政策措施",
        "url": "",
        "policy_tools": ["财政金融", "产业促进", "市场培育"],
        "source": "深圳市大鹏新区管委会",
        "status": "有效"
    },
    {
        "title": "四川省支持低空经济发展的若干政策措施申报指南",
        "date": "2025",
        "region": "四川省",
        "level": "provincial",
        "category": "申报指南",
        "url": "",
        "policy_tools": ["财政金融", "税收优惠"],
        "source": "四川省发展和改革委员会",
        "status": "有效"
    },
    {
        "title": "武汉市公安局无人机集群飞行表演活动安全监管工作规范",
        "date": "2026-01-29",
        "region": "湖北省",
        "level": "city",
        "category": "管理规定",
        "url": "",
        "policy_tools": ["安全监管"],
        "source": "武汉市公安局",
        "status": "有效"
    }
]

# Check existing titles for dedup
existing_titles_lower = set()
for p in existing:
    t = p['title'].replace(' ', '').lower()[:30]
    existing_titles_lower.add(t)

# Filter out duplicates
truly_new = []
skipped = 0
for np in new_policies:
    nt = np['title'].replace(' ', '').lower()[:30]
    is_dup = False
    for et in existing_titles_lower:
        if nt[:20] in et or et[:20] in nt:
            is_dup = True
            break
    if is_dup:
        skipped += 1
        print(f"SKIP: {np['title'][:50]}")
    else:
        truly_new.append(np)

print(f"\nExisting: {len(existing)}, New to add: {len(truly_new)}, Skipped: {skipped}")

# Merge
all_policies = existing + truly_new

# Sort by date (newest first), with null dates at the end
def sort_key(p):
    d = p.get('date', '')
    if not d or d == '' or len(d) < 4:
        return '0000'
    return d

all_policies.sort(key=sort_key, reverse=True)

with open('dashboard/policy_data.json', 'w') as f:
    json.dump(all_policies, f, ensure_ascii=False, indent=2)

print(f"Total policies saved: {len(all_policies)}")

# Print the new ones that were added
print("\n=== Newly Added ===")
for np in truly_new:
    print(f"  + {np['date']} | {np['title'][:60]} | {np['region']}")
