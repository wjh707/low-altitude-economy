#!/usr/bin/env python3
"""
低空经济政策数据更新脚本
读取 policy_data.json，更新统计信息并输出 stats.json
支持增量更新（按日期检查新增）
"""

import json
import datetime
import os
import sys
from collections import Counter, OrderedDict

# ============================================================
# 配置区域
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
POLICY_FILE = os.path.join(DATA_DIR, "policy_data.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")


def log(msg):
    """打印带时间戳的日志"""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [INFO] {msg}")


def load_policies(filepath):
    """加载政策数据"""
    if not os.path.exists(filepath):
        log(f"错误：文件不存在 {filepath}")
        log("请先运行 scripts/fetch_policy.py 生成政策数据")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    log(f"已加载 {len(data)} 条政策数据")
    return data


def compute_stats(policies):
    """
    计算统计数据
    - total_policies: 总数
    - by_level: 按级别统计
    - by_region: 按地区统计
    - by_month: 按月统计
    - by_category: 按类别统计
    - recent_additions: 最近30天新增
    - hot_keywords: 热门关键词TOP15
    """
    total = len(policies)

    # 按级别统计
    by_level = Counter()
    for p in policies:
        by_level[p["level"]] += 1

    # 按地区统计
    by_region = Counter()
    for p in policies:
        by_region[p["region"]] += 1

    # 按月统计
    by_month = OrderedDict()
    sorted_policies = sorted(policies, key=lambda x: x["date"])
    for p in sorted_policies:
        month_key = p["date"][:7]  # YYYY-MM
        by_month[month_key] = by_month.get(month_key, 0) + 1

    # 按类别统计
    by_category = Counter()
    for p in policies:
        by_category[p["category"]] += 1

    # 最近新增（最近30天）
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)
    recent = []
    for p in policies:
        try:
            pub_date = datetime.date.fromisoformat(p["date"])
            if pub_date >= thirty_days_ago and pub_date <= today:
                recent.append({
                    "title": p["title"],
                    "date": p["date"],
                    "source": p["source"],
                    "level": p["level"],
                    "region": p["region"]
                })
        except ValueError:
            continue
    # 按日期排序（最新的在前）
    recent.sort(key=lambda x: x["date"], reverse=True)

    # 热门关键词
    keyword_counter = Counter()
    for p in policies:
        for kw in p.get("keywords", []):
            keyword_counter[kw] += 1
    hot_keywords = [{"keyword": k, "count": v}
                    for k, v in keyword_counter.most_common(15)]

    stats = OrderedDict([
        ("update_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("total_policies", total),
        ("time_span", {
            "start": sorted_policies[0]["date"] if sorted_policies else None,
            "end": sorted_policies[-1]["date"] if sorted_policies else None
        }),
        ("by_level", dict(by_level.most_common())),
        ("by_region", dict(by_region.most_common())),
        ("by_month", dict(by_month)),
        ("by_category", dict(by_category.most_common())),
        ("recent_additions", recent),
        ("hot_keywords", hot_keywords),
    ])

    return stats


def save_stats(stats, filepath):
    """保存统计结果"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    log(f"统计结果已保存到 {filepath}")


def print_summary(stats):
    """打印统计摘要"""
    log("=" * 50)
    log("统计摘要")
    log("=" * 50)
    log(f"  政策总数: {stats['total_policies']}")
    log(f"  时间跨度: {stats['time_span']['start']} ~ {stats['time_span']['end']}")
    log(f"  各级别分布: {stats['by_level']}")
    log(f"  各地区分布: {stats['by_region']}")
    log(f"  政策类别分布: {stats['by_category']}")
    log(f"  最近新增: {len(stats['recent_additions'])} 条")
    log("  热门关键词 TOP5:")
    for kw in stats['hot_keywords'][:5]:
        log(f"    · {kw['keyword']} ({kw['count']}次)")


def main():
    """主函数"""
    log("=" * 50)
    log("低空经济政策数据更新脚本启动")
    log("=" * 50)

    # 加载数据
    policies = load_policies(POLICY_FILE)
    if not policies:
        sys.exit(1)

    # 计算统计
    log("正在计算统计数据...")
    stats = compute_stats(policies)

    # 保存统计
    save_stats(stats, STATS_FILE)

    # 打印摘要
    print_summary(stats)

    log("数据更新完成！")
    return stats


if __name__ == "__main__":
    main()
