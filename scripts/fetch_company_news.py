#!/usr/bin/env python3
"""
企业动态采集脚本 — 预留爬虫接口
用法：
  python3 scripts/fetch_company_news.py          # 使用现有数据
  python3 scripts/fetch_company_news.py --search  # 预留：启动网络搜索
  python3 scripts/fetch_company_news.py --output-dir ./dashboard
"""
import json, os, sys, time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_companies():
    """加载企业名录"""
    path = os.path.join(BASE_DIR, "data", "companies.json")
    with open(path, "r", encoding="utf-8") as f:
        return {c["name"]: c for c in json.load(f)}

def load_existing_news():
    """加载已有动态数据（用于合并去重）"""
    path = os.path.join(BASE_DIR, "dashboard", "company_news.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def deduplicate(news_list):
    """基于 company + headline + date 三元组去重"""
    seen = set()
    result = []
    for n in news_list:
        key = (n.get("company", ""), n.get("headline", ""), n.get("date", ""))
        if key not in seen:
            seen.add(key)
            result.append(n)
    return result

def search_online(company_name):
    """
    预留：从网络搜索企业最新动态
    TODO: 接入Bing News API 或 百度新闻搜索
    """
    # 占位 — 后续实现真实爬虫
    return []

def batch_search(companies):
    """批量搜索各企业最新动态（预留）"""
    all_news = []
    for name, info in companies.items():
        news = search_online(name)
        all_news.extend(news)
        time.sleep(1)  # 礼貌间隔
    return all_news

def merge_news(existing, new_news):
    """合并新数据到已有数据"""
    combined = new_news + existing
    return deduplicate(combined)

def save_news(news, output_dir):
    """保存动态数据"""
    news.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    data_path = os.path.join(output_dir, "company_news.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存: {data_path} ({len(news)}条)")

def print_stats(news):
    from collections import Counter
    companies = set(n.get("company", "") for n in news)
    print(f"\n📊 统计")
    print(f"  动态总数: {len(news)}")
    print(f"  覆盖企业: {len(companies)}")
    print(f"  动态分类:")
    for k, v in Counter(n.get("category", "") for n in news).most_common():
        print(f"    {k}: {v}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="企业动态采集脚本")
    parser.add_argument("--output-dir", default=None, help="输出目录（默认同步到data/和dashboard/）")
    parser.add_argument("--search", action="store_true", help="启动网络搜索模式（预留）")
    args = parser.parse_args()
    
    if args.search:
        print("🔍 网络搜索模式（功能预留，待实现）")
        companies = load_companies()
        new_news = batch_search(companies)
        existing = load_existing_news()
        merged = merge_news(existing, new_news)
        output = args.output_dir or os.path.join(BASE_DIR, "dashboard")
        save_news(merged, output)
        print_stats(merged)
    else:
        print("📋 本地模式：同步已有数据到dashboard/")
        src = os.path.join(BASE_DIR, "data", "company_news.json")
        dst = os.path.join(BASE_DIR, "dashboard", "company_news.json")
        if os.path.exists(src):
            with open(src, "r") as f:
                data = json.load(f)
            with open(dst, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已同步: {dst}")
            print_stats(data)
        else:
            print("⚠️  未找到数据文件，请先运行 scripts/generate_news.py")
