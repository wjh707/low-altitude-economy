#!/usr/bin/env python3
"""
对162条政策批量标注政策工具标签 v2
优化：排除非低空经济法律，减少误标，覆盖更多类型
"""
import re, json

POLICY_FILE = "/Users/zhoulai/low-altitude-economy/dashboard/policy_data.json"

# 非低空经济相关法律（通用法律，不标注政策工具）
GENERAL_LAWS = [
    "公司法", "合伙企业法", "证券投资基金法", "企业破产法",
    "民法典", "民法典", "民用航空法(修订草案)",
]

# 政策工具 → 关键词映射（优化版）
TOOL_RULES = [
    ("空域管理", [
        "空域", "飞行管制", "飞行基本规则", "飞行服务",
        "航路", "航线", "空中交通管理", "空域基础分类",
        "飞行保障", "低空空域管理改革",
    ]),
    ("财政金融", [
        "专项资金", "产业基金", "贷款贴息", "保险补贴",
        "财政", "金融支持",
    ]),
    ("税收优惠", [
        "税收优惠", "减税", "免税", "所得税", "增值税",
    ]),
    ("土地供应", [
        "土地", "用地保障", "建设用地",
    ]),
    ("基础设施", [
        "机场", "起降", "起降场", "飞行服务站",
        "智联网", "通信导航", "雷达", "设施建设",
        "低空网络", "导航设施",
    ]),
    ("技术创新", [
        "技术创新", "研发", "科技", "标准", "知识产权",
        "科研", "检验检测", "适航标准", "技术攻关",
        "产学研", "创新应用", "装备创新",
    ]),
    ("产业促进", [
        "行动方案", "高质量发展", "产业发展", "产业集群",
        "产业链", "招商引资", "企业培育", "产业园",
        "发展纲要", "发展意见", "发展规划",
        "产业创新", "产业发展", "产业促进",
    ]),
    ("人才引进", [
        "人才", "培训", "驾驶员", "从业人员",
        "专业人员", "培训大纲", "培训机构",
    ]),
    ("安全监管", [
        "安全管理", "安全保卫", "安全规则", "运行安全",
        "适航", "实名制", "登记", "审定",
        "安全要求", "安全评定", "危险品",
        "诚信评价", "经营许可", "许可管理",
        "飞行管理暂行条例", "监管",
    ]),
    ("市场培育", [
        "消费", "旅游", "物流", "配送", "公共服务",
        "救援", "测绘", "户外运动", "体育",
        "应用场景", "示范", "市场",
    ]),
    ("运营管理", [
        "运行规定", "运行管理", "运行安全", "运行识别",
        "飞行活动", "经营许可", "经营许可管理",
        "运行管理办法", "运营服务",
    ]),
    ("标准规范", [
        "安全要求", "性能要求", "指南", "标准",
        "管理程序", "登记管理程序",
    ]),
]

def tag_policy_v2(policy):
    title = policy.get("title", "")
    cat = policy.get("category", "")
    region = policy.get("region", "")
    full = title + " " + cat + " " + region
    
    tags = []
    
    # 排除通用法律
    for gl in GENERAL_LAWS:
        if gl in title:
            return ["通用法律"]
    
    # 按规则匹配
    for tool_name, keywords in TOOL_RULES:
        for kw in keywords:
            if kw in full:
                if tool_name not in tags:
                    tags.append(tool_name)
                break
    
    # 处理地方性法规条例：加入对应标签
    if "条例" in title and "管理" in title and "安全监管" not in tags:
        tags.append("安全监管")
    
    # 部分规章补充标签
    if "运行" in title and "运行管理" not in tags:
        if "运营管理" not in tags:
            tags.append("运营管理")
    
    if "通知" in title and not tags:
        tags.append("产业促进")
    
    return tags

def main():
    with open(POLICY_FILE, 'r', encoding='utf-8') as f:
        policies = json.load(f)
    
    tool_stats = {}
    no_tag_count = 0
    general_law_count = 0
    
    for p in policies:
        tags = tag_policy_v2(p)
        
        # 如果是通用法律，不标
        if tags == ["通用法律"]:
            general_law_count += 1
            p["policy_tools"] = []
            p["note"] = "通用法律，非低空经济专属"
            continue
        
        p["policy_tools"] = tags
        if tags:
            for t in tags:
                tool_stats[t] = tool_stats.get(t, 0) + 1
        else:
            no_tag_count += 1
    
    print("📊 政策工具标注统计 (v2):")
    print(f"{'='*50}")
    for t, c in sorted(tool_stats.items(), key=lambda x: -x[1]):
        print(f"  {t:12s}  {c:3d} 条")
    
    print(f"\n  通用法律(跳过标注): {general_law_count} 条")
    print(f"  已标注工具: {sum(tool_stats.values())} 次")
    
    # 无标签的
    no_tags = [p for p in policies if not p.get("policy_tools") and not p.get("note")]
    if no_tags:
        print(f"\n⚠️ 仍无标签 ({len(no_tags)}条):")
        for n in no_tags[:10]:
            print(f"  {n['title'][:60]}")
    
    # 3+标签的
    multi = [(p, p.get("policy_tools", [])) for p in policies if len(p.get("policy_tools", [])) >= 3]
    if multi:
        print(f"\n📌 含3个以上标签 ({len(multi)}条):")
        for p, ts in multi[:5]:
            print(f"  {p['title'][:45]}")
            print(f"    标签: {', '.join(ts)}")
    
    with open(POLICY_FILE, 'w', encoding='utf-8') as f:
        json.dump(policies, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已保存")
    
    return policies

if __name__ == "__main__":
    main()
