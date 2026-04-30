#!/usr/bin/env python3
"""
清洗低空经济政策数据脚本
修复：地区误判、标题不完整、重复条目、类别错误
"""
import json
import re
import sys
from collections import Counter

# ============================================================
# 配置
# ============================================================
INPUT_FILE = "/Users/zhoulai/low-altitude-economy/dashboard/policy_data.json"
OUTPUT_FILE = "/Users/zhoulai/low-altitude-economy/dashboard/policy_data.json"

# ============================================================
# 1. 标题过滤 - 明显不是政策标题的条目
# ============================================================
REJECT_TITLE_KEYWORDS = [
    "前言", "编写说明", "编制说明", "本文旨在", "为更好地向", "这本资料",
    "法律汇编", "政策汇编", "合集", "索引", "目 录", "为了让更好地推广",
    "旨在建立", "尝试建立", "资料尝试",
]

def is_garbage_title(title):
    """判断是否为非政策标题"""
    if not title:
        return True
    t = title.strip()
    # 长度过滤
    if len(t) < 8 or len(t) > 80:
        return True
    # 关键词过滤
    tl = t.lower()
    for kw in REJECT_TITLE_KEYWORDS:
        if kw.lower() in tl:
            return True
    # 以非标题字符开头（如"的"、"为"、"除"、"符"、"及"、"及时"、"健全"等断章取义片段）
    bad_starts = ["的", "为", "除", "符", "及", "及时", "健全", "符合", "属于",
                  "民用航空器经", "民用航空器未", "运输机场应当", "空域管理的",
                  "及时向飞行", "飞行高度层", "类空域通常", "空域分类具体",
                  "表明身份", "拒绝", "空中交通", "机场应当", "未经",
                  "个通用机场", "依法对", "使用低空航空器", "从事经营性飞行",
                  "人民政府应当", "低空飞行服务机构", "使用低空航空器",
                  "低空经济主要依托", "低空产业园区", "低空运营服务",
                  "全省通用机场",
                  # 法条片段
                  "一章", "第二章", "上级", "不对", "不按", "不符合",
                  "上升", "应当", "不符合"]
    for bs in bad_starts:
        if t.startswith(bs):
            return True
    
    # 标题太短且不含政策关键词的（法条片段）
    if len(t) < 15:
        # 检查是否含有政策标题常见词
        has_policy_kw = any(kw in t for kw in [
            "关于", "办法", "规定", "条例", "通知", "法",
            "方案", "规划", "意见", "标准", "指南", "规范",
            "细则", "措施", "纲要", "规则", "决定", "公告",
            "通告", "批复", "报告", "管理", "安全", "发展",
            "促进", "支持", "推动", "鼓励", "产业", "航空",
            "无人机", "飞行", "机场", "空域", "适航",
        ])
        if not has_policy_kw:
            return True
    
    return False

# ============================================================
# 2. 地区修复
# ============================================================
NATIONAL_KEYWORDS = [
    "中华人民共和国", "国家空域", "全国", "民用航空", "通用航空",
    "国务院", "中央军委", "国家发展改革委", "交通运输部",
    "中国民航", "民航局", "CAAC", "空域管理条例",
]

# 省市关键词映射
PROVINCE_KEYWORDS = {
    "北京": "北京市", "天津": "天津市", "上海": "上海市", "重庆": "重庆市",
    "河北": "河北省", "山西": "山西省", "辽宁": "辽宁省", "吉林": "吉林省",
    "黑龙江": "黑龙江省", "江苏": "江苏省", "浙江": "浙江省", "安徽": "安徽省",
    "福建": "福建省", "江西": "江西省", "山东": "山东省", "河南": "河南省",
    "湖北": "湖北省", "湖南": "湖南省", "广东": "广东省", "海南": "海南省",
    "四川": "四川省", "贵州": "贵州省", "云南": "云南省", "陕西": "陕西省",
    "甘肃": "甘肃省", "青海": "青海省", "台湾": "台湾省",
    "内蒙古": "内蒙古自治区", "广西": "广西壮族自治区", "西藏": "西藏自治区",
    "宁夏": "宁夏回族自治区", "新疆": "新疆维吾尔自治区",
    "香港": "香港特别行政区", "澳门": "澳门特别行政区",
    # 地级市/区
    "深圳": "深圳市", "广州": "广州市", "成都": "成都市",
    "杭州": "杭州市", "南京": "南京市", "武汉": "武汉市",
    "郑州": "郑州市", "西安": "西安市", "长沙": "长沙市",
    "合肥": "合肥市", "福州": "福州市", "南昌": "南昌市",
    "昆明": "昆明市", "贵阳": "贵阳市", "海口": "海口市",
    "石家庄": "石家庄市", "太原": "太原市", "济南": "济南市",
    "哈尔滨": "哈尔滨市", "长春": "长春市", "沈阳": "沈阳市",
    "兰州": "兰州市", "西宁": "西宁市",
    "苏州": "苏州市", "无锡": "无锡市", "常州": "常州市",
    "扬州": "扬州市", "镇江": "镇江市", "南通": "南通市",
    "徐州": "徐州市", "宁波": "宁波市", "温州": "温州市",
    "嘉兴": "嘉兴市", "湖州": "湖州市", "绍兴": "绍兴市",
    "金华": "金华市", "台州": "台州市", "珠海": "珠海市",
    "佛山": "佛山市", "东莞": "东莞市", "中山": "中山市",
    "惠州": "惠州市", "汕头": "汕头市", "桂林": "桂林市",
    "三亚": "三亚市", "厦门": "厦门市", "青岛": "青岛市",
    "大连": "大连市", "苏州": "苏州市",
    "延庆": "北京市", "丰台": "北京市", "房山": "北京市",
    "吴中": "苏州市", "梁平": "重庆市", "杨浦": "上海市",
    "海宁": "嘉兴市", "自贡": "自贡市", "中关村": "北京市",
}

def fix_region(item):
    """根据标题修复地区"""
    title = item.get("title", "")
    original_region = item.get("region", "")
    
    # 先检查国家级关键词
    for kw in NATIONAL_KEYWORDS:
        if kw in title:
            return "全国", "国家"
    
    # 再检查省市名
    for keyword, province in sorted(PROVINCE_KEYWORDS.items(), key=lambda x: -len(x[0])):
        if keyword in title:
            return province, "provincial"
    
    # 保持原样 - 但如果原地区是"江苏省"而标题没提到江苏，且有国家级特征，改为全国
    if original_region == "江苏省" and "江苏" not in title:
        # 检查是否看起来像国家政策（含"全国""国家""民用"等）
        for kw in ["全国", "国家", "民用航空", "通用航空", "十三五", "十四五",
                    "国务院", "交通运输", "民航局", "中央军委", "CAAC"]:
            if kw in title:
                return "全国", "国家"
        # 包含其他省份/城市名但被偷懒归为江苏 → 保持原有region不变（其实已在上面匹配过）
        # 其他情况：很可能是断章取义的片段或前言文字，置为全国
        return "全国", "国家"
    
    return original_region, item.get("level", "")

# ============================================================
# 3. 类别修正
# ============================================================
def fix_category(title):
    """根据标题后缀修正类别"""
    t = title.strip()
    if t.endswith("法"):
        return "法律"
    if t.endswith("条例"):
        return "行政法规"
    if t.endswith("规定") or t.endswith("办法") or t.endswith("细则"):
        return "部门规章"
    if any(t.endswith(s) for s in ["通知", "意见", "纲要", "规划", "方案", "措施"]):
        return "政策文件"
    if any(t.endswith(s) for s in ["标准", "指南", "规范"]):
        return "技术规范"
    return "其他"

# ============================================================
# 4. 去重 - 基于规范化标题
# ============================================================
def normalize_title(title):
    """规范化标题：去空格、标点、引号，取前25个字符"""
    t = title.strip()
    # 去除所有空格
    t = re.sub(r'\s+', '', t)
    # 去除标点符号和引号
    t = re.sub(r'[，。！？、；：""''（）【】《》\-\—\·\（\）\？\！\（\）\（\）\,\.\!\?\;\:\"\'\(\)\[\]\{\}]', '', t)
    # 去除英文标点
    t = re.sub(r'[,\.!?;:\"\'`\(\)\[\]\{\}]', '', t)
    # 取前25个字符
    return t[:25]

def deduplicate(items):
    """基于规范化标题去重，保留第一条"""
    seen = {}
    result = []
    dup_count = 0
    for item in items:
        key = normalize_title(item.get("title", ""))
        if not key:
            continue
        if key in seen:
            dup_count += 1
            # 如果已有的条目是垃圾而新条目更好，替换
            existing = seen[key]
            if is_garbage_title(existing.get("title", "")) and not is_garbage_title(item.get("title", "")):
                # 替换
                result[result.index(existing)] = item
                seen[key] = item
        else:
            seen[key] = item
            result.append(item)
    return result, dup_count

# ============================================================
# 主流程
# ============================================================
def main():
    # 读取数据
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    original_count = len(data)
    print(f"📊 原始数据: {original_count} 条")
    
    # 步骤1: 标题过滤
    before_filter = len(data)
    data = [item for item in data if not is_garbage_title(item.get("title", ""))]
    after_filter = len(data)
    print(f"🔍 标题过滤: 剔除 {before_filter - after_filter} 条 (剩余 {after_filter})")
    
    # 步骤2: 地区修复 & 类别修正
    for item in data:
        new_region, new_level = fix_region(item)
        item["region"] = new_region
        if new_level:
            item["level"] = new_level
        item["category"] = fix_category(item.get("title", ""))
    
    # 统计修复后的地区分布
    regions = Counter(item.get("region", "") for item in data)
    print(f"📍 地区修复后分布: {dict(regions.most_common(10))}")
    
    # 步骤3: 去重
    data, dup_count = deduplicate(data)
    print(f"🔄 去重: 移除 {dup_count} 条重复 (剩余 {len(data)})")
    
    # 步骤4: 最终排序（按地区、标题）
    data.sort(key=lambda x: (x.get("region", ""), x.get("title", "")))
    
    print(f"\n✅ 清洗完成: {original_count} → {len(data)} 条")
    
    # 统计类目
    cats = Counter(item.get("category", "") for item in data)
    print(f"📂 类别分布: {dict(cats)}")
    
    # 写入
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 写入: {OUTPUT_FILE}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
