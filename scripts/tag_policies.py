#!/usr/bin/env python3
"""
对162条政策批量标注政策工具标签
规则：基于标题关键词匹配
"""
import re, json

POLICY_FILE = "/Users/zhoulai/low-altitude-economy/dashboard/policy_data.json"
OUTPUT = POLICY_FILE

# 政策工具 → 关键词映射
TOOL_RULES = [
    ("空域管理", [
        "空域", "飞行管制", "飞行基本规则", "飞行服务", "飞行计划",
        "航路", "航线", "管制空域", "报告空域", "低空空域",
        "空中交通管理"
    ]),
    ("财政金融", [
        "资金", "补贴", "奖励", "基金", "贷款", "贴息", "保险",
        "专项资金", "财政", "金融", "投资", "经费"
    ]),
    ("税收优惠", [
        "税收", "税务", "所得税", "增值税", "关税",
        "减免税", "税收优惠", "加计扣除"
    ]),
    ("土地供应", [
        "土地", "用地", "建设用地", "园区", "功能区",
        "国土", "规划用地"
    ]),
    ("基础设施", [
        "机场", "起降", "通用机场", "飞行服务站", "起降场",
        "智联网", "通信", "导航", "监视", "雷达",
        "基础设施建设", "低空网络", "设施", "跑道"
    ]),
    ("技术创新", [
        "技术", "研发", "创新", "标准", "专利", "知识产",
        "科研", "实验", "检验检测", "适航标准", "安全标准",
        "攻关", "产学研", "科技"
    ]),
    ("产业促进", [
        "产业", "产业链", "集群", "招商", "企业培育",
        "专精特新", "产业联盟", "高质量", "行动方案",
        "实施方案", "发展规划", "发展纲要", "发展意见",
        "产业促进", "产业创新"
    ]),
    ("人才引进", [
        "人才", "培训", "人员", "驾驶员", "飞手",
        "教育", "培训大纲", "执照", "资格",
        "航空人员", "专业人员"
    ]),
    ("安全监管", [
        "安全", "监管", "适航", "登记", "实名",
        "审定", "事故", "应急", "反制", "防御",
        "危险品", "安保", "保卫", "管理规则",
        "许可证", "许可", "诚信", "评价"
    ]),
    ("市场培育", [
        "采购", "场景", "示范", "消费", "旅游",
        "物流", "配送", "农业", "植保", "巡查",
        "公共服务", "救援", "测绘", "游览",
        "户外运动", "体育", "文体"
    ]),
]

def tag_policy(policy):
    """对一条政策标注工具标签"""
    title = policy.get("title", "") + " " + policy.get("category", "") + " " + policy.get("region", "")
    tags = []
    
    # 法律/行政法规 -> 安全监管（基础法律框架）
    cat = policy.get("category", "")
    if cat == "法律":
        tags.append("安全监管")
    
    for tool_name, keywords in TOOL_RULES:
        for kw in keywords:
            if kw in title:
                if tool_name not in tags:
                    tags.append(tool_name)
                break
    
    # 部分法规类型的补充标签
    if "条例" in title and "管理" in title:
        if "安全监管" not in tags:
            tags.append("安全监管")
    
    # 通用航空/无人驾驶类 -> 自动加上"市场培育"
    if ("通用航空" in title or "无人机" in title) and "市场培育" not in tags:
        pass  # 不自动加
    
    return tags

def main():
    with open(POLICY_FILE, 'r', encoding='utf-8') as f:
        policies = json.load(f)
    
    # 统计各工具
    tool_stats = {}
    for p in policies:
        tags = tag_policy(p)
        p["policy_tools"] = tags
        for t in tags:
            tool_stats[t] = tool_stats.get(t, 0) + 1
    
    print("📊 政策工具标注统计:")
    print(f"{'='*50}")
    for t, c in sorted(tool_stats.items(), key=lambda x: -x[1]):
        print(f"  {t:12s}  {c:3d} 条")
    
    # 统计含多标签的政策
    multi = [p for p in policies if len(p.get("policy_tools", [])) >= 2]
    none = [p for p in policies if not p.get("policy_tools", [])]
    print(f"\n  含2个以上标签: {len(multi)} 条")
    print(f"  无标签: {len(none)} 条")
    
    if none:
        print(f"\n⚠️ 无标签的政策:")
        for n in none[:10]:
            print(f"  {n['title'][:60]}")
    
    # 保存
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(policies, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已保存到 {OUTPUT}")
    
    # 示例
    print(f"\n📋 样例:")
    for p in policies[:5]:
        print(f"  {p['title'][:40]}")
        print(f"    标签: {', '.join(p.get('policy_tools', []))}")

if __name__ == "__main__":
    main()
