#!/usr/bin/env python3
"""
低空经济政策数据按年份拆分脚本
从 policy_data.json 读取数据，按年份拆分输出
生成 policy_data_2024.json 和 policy_data_2025.json 等
"""

import json
import datetime
import os
import sys
from collections import defaultdict

# ============================================================
# 配置区域
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
POLICY_FILE = os.path.join(DATA_DIR, "policy_data.json")


def log(msg):
    """打印带时间戳的日志"""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [INFO] {msg}")


def load_policies(filepath):
    """加载政策数据"""
    if not os.path.exists(filepath):
        log(f"错误：文件不存在 {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    log(f"已加载 {len(data)} 条政策数据")
    return data


def split_by_year(policies):
    """
    按年份拆分政策数据
    返回: {year: [policies]}
    """
    yearly = defaultdict(list)
    for p in policies:
        try:
            year = p["date"][:4]
            yearly[year].append(p)
        except (IndexError, KeyError):
            log(f"警告：跳过无效日期的政策 '{p.get('title', 'unknown')}'")
            continue
    return dict(yearly)


def save_yearly(yearly_data):
    """保存各年份数据到单独文件"""
    saved_files = []
    for year in sorted(yearly_data.keys()):
        filename = f"policy_data_{year}.json"
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(yearly_data[year], f, ensure_ascii=False, indent=2)
        log(f"已保存 {year} 年 {len(yearly_data[year])} 条政策 → {filename}")
        saved_files.append(filepath)
    return saved_files


def main():
    """主函数"""
    log("=" * 50)
    log("低空经济政策数据按年份拆分")
    log("=" * 50)

    # 加载数据
    policies = load_policies(POLICY_FILE)
    if not policies:
        sys.exit(1)

    # 按年份拆分
    yearly_data = split_by_year(policies)
    log(f"共覆盖 {len(yearly_data)} 个年份: {', '.join(sorted(yearly_data.keys()))}")

    # 输出各年份数量
    for year in sorted(yearly_data.keys()):
        log(f"  {year}年: {len(yearly_data[year])} 条")

    # 保存文件
    saved = save_yearly(yearly_data)
    log(f"已完成！共生成 {len(saved)} 个文件")


if __name__ == "__main__":
    main()
