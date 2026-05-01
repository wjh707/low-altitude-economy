#!/usr/bin/env python3
"""
低空经济产业竞争情报系统 - 每日日报生成

从 data/ 目录读取最新数据，生成格式化的日报文本。
被 cron job 调用，输出日报内容到 stdout，由 cron 框架通过 send_message 推送。

用法：
  python3 scripts/daily_report.py                # 完整日报
  python3 scripts/daily_report.py --brief        # 精简版（微信消息长度友好）
"""

import json
import os
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")


def load_json(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def load_latest_changelog():
    """读取 changelog，获取最近一次更新记录"""
    changelog = load_json(os.path.join(DATA_DIR, "changelog.json"))
    if not changelog:
        return {}
    result = {}
    for entry in changelog:
        mod = entry.get("module")
        if mod not in result:
            result[mod] = entry
    return result


def build_report(brief=False):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    width = 32

    # ======== 头部 ========
    lines.append("┌" + "─" * width + "┐")
    lines.append(f"│ {'🚁 低空经济情报日报':^{width-2}} │")
    lines.append(f"│ {'📅 ' + today:^{width-2}} │")
    lines.append("└" + "─" * width + "┘")
    lines.append("")

    # ======== 1. 政策情报 ========
    policies = load_json(os.path.join(DATA_DIR, "policy_data.json"))
    stats = load_json(os.path.join(DATA_DIR, "stats.json"))

    if policies:
        sorted_p = sorted(policies, key=lambda x: x.get("date", ""), reverse=True)
        latest = sorted_p[:5]

        lines.append("━" * width)
        lines.append("📜 政策情报")
        lines.append("━" * width)
        lines.append(f"  在库政策：{len(policies)} 条")
        if stats:
            lines.append(f"  覆盖省市：{len(stats.get('by_region', {}))} 个")
            lines.append(f"  时间跨度：{stats.get('time_span', {}).get('start', '?')} ~ {stats.get('time_span', {}).get('end', '?')}")
        lines.append("")

        if not brief:
            lines.append("  📌 最新政策（TOP5）：")
            for p in latest:
                level_icon = {"national": "🏛", "provincial": "🏗", "city": "🏙"}
                icon = level_icon.get(p.get("level", ""), "📄")
                lines.append(f"    {icon} {p.get('date', '--')} {p.get('title', '')[:40]}")
            lines.append("")

    # ======== 2. 人才情报 ========
    talent_stats = load_json(os.path.join(DATA_DIR, "talent_stats.json"))
    talent_data = load_json(os.path.join(DATA_DIR, "talent_data.json"))

    lines.append("━" * width)
    lines.append("👥 人才情报")
    lines.append("━" * width)

    if talent_stats:
        total = talent_stats.get("total_jobs", len(talent_data) if talent_data else 0)
        lines.append(f"  在招岗位：{total} 个")
        by_cat = talent_stats.get("by_category", {})
        if by_cat:
            top_cat = sorted(by_cat.items(), key=lambda x: -x[1])[:3]
            lines.append(f"  热门方向：{'  '.join([f'{k}({v})' for k, v in top_cat])}")
        by_city = talent_stats.get("by_city", {})
        if by_city:
            top_cities = sorted(by_city.items(), key=lambda x: -x[1])[:3]
            lines.append(f"  热门城市：{'  '.join([f'{k}({v})' for k, v in top_cities])}")
    else:
        lines.append(f"  在招岗位：{len(talent_data)} 个" if talent_data else "  暂无数据")
    lines.append("")

    # ======== 3. 企业动态 ========
    company_news = load_json(os.path.join(DATA_DIR, "company_news.json"))

    lines.append("━" * width)
    lines.append("🏢 企业动态")
    lines.append("━" * width)

    if company_news:
        sorted_news = sorted(company_news, key=lambda x: x.get("date", ""), reverse=True)
        lines.append(f"  累计追踪：{len(company_news)} 条动态")

        # 最新动态
        latest_news = sorted_news[:3]
        if not brief:
            lines.append("")
            lines.append("  📌 最新动态：")
            for n in latest_news:
                cat_icon = {"融资": "💰", "产品发布": "🚀", "战略合作": "🤝", "重大项目": "🏗️",
                           "适航取证": "✅", "企业经营": "📊", "政策响应": "📋"}
                icon = cat_icon.get(n.get("category", ""), "📌")
                lines.append(f"    {icon} {n.get('date', '')} [{n.get('company', '')}]")
                lines.append(f"       {n.get('headline', '')}")
            lines.append("")
    else:
        lines.append("  暂无企业动态数据")
        lines.append("")

    # ======== 4. 产业链概览 ========
    companies = load_json(os.path.join(DATA_DIR, "companies.json"))
    if companies:
        lines.append("━" * width)
        lines.append("🔗 产业链概览")
        lines.append("━" * width)
        by_chain = {}
        for c in companies:
            link = c.get("chain_link", "其他")
            by_chain.setdefault(link, 0)
            by_chain[link] += 1
        chain_order = ["材料/零部件", "整机制造", "空域基建/通信", "运营服务", "应用场景", "综合保障"]
        for link in chain_order:
            count = by_chain.get(link, 0)
            if count:
                bar = "█" * count
                lines.append(f"    {link:>10} {bar} {count}家")
        lines.append("")

    # ======== 页脚 ========
    lines.append("─" * width)
    lines.append(f"📊 看板地址：")
    lines.append(f"   https://wjh707.github.io/low-altitude-economy/")
    lines.append(f"🤖 每日自动更新 · {today}")
    lines.append("─" * width)

    return "\n".join(lines)


def main():
    brief = "--brief" in sys.argv
    report = build_report(brief=brief)
    print(report)


if __name__ == "__main__":
    main()
