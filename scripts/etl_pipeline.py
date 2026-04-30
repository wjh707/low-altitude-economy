#!/usr/bin/env python3
"""
低空经济产业竞争情报系统 - ETL 数据管道
负责：数据采集、清洗、去重、统计聚合、历史存档

架构：
  scripts/fetch_policy.py  ────→  data/raw/policy_raw_YYYY-MM-DD.json
  scripts/fetch_talent.py  ────→  data/raw/talent_raw_YYYY-MM-DD.json
                                       │
                                  scripts/etl_pipeline.py
                                       │
                                       ├──→ data/policy_data.json       (看板主数据)
                                       ├──→ data/talent_data.json       (看板主数据)
                                       ├──→ data/stats.json             (聚合统计)
                                       ├──→ data/changelog.json          (变更日志)
                                       └──→ data/archive/               (历史快照)
"""

import json
import os
import sys
import datetime
import hashlib
import shutil
from collections import OrderedDict

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [ETL] {msg}"
    print(line)
    log_path = os.path.join(LOG_DIR, "etl.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# 步骤 1: 采集（调用 fetch 脚本）
# ============================================================
def run_fetch(module_name):
    """运行指定模块的数据采集脚本"""
    script_path = os.path.join(BASE_DIR, "scripts", f"fetch_{module_name}.py")
    if not os.path.exists(script_path):
        log(f"⚠️ 采集脚本不存在: {script_path}")
        return None

    log(f"📡 运行 {module_name} 采集脚本...")
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"fetch_{module_name}", script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    data = mod.main()
    return data


# ============================================================
# 步骤 2: 保存原始数据（时间戳归档，不覆盖）
# ============================================================
def save_raw(data, module_name):
    """保存带时间戳的原始数据快照"""
    if not data:
        log(f"⚠️ {module_name} 无数据，跳过保存")
        return None

    today = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    raw_file = os.path.join(RAW_DIR, f"{module_name}_raw_{today}.json")

    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log(f"💾 原始数据已保存: {raw_file} ({len(data)} 条)")
    return raw_file


# ============================================================
# 步骤 3: 数据清洗 & 去重
# ============================================================
def clean_policy(policy):
    """清洗单条政策数据"""
    cleaned = {}
    cleaned["title"] = (policy.get("title") or "").strip()
    cleaned["date"] = (policy.get("date") or "").strip()
    cleaned["source"] = (policy.get("source") or "").strip()
    cleaned["level"] = (policy.get("level") or "national").strip()
    cleaned["region"] = (policy.get("region") or "全国").strip()
    cleaned["category"] = (policy.get("category") or "其他").strip()
    cleaned["summary"] = (policy.get("summary") or "").strip()
    cleaned["url"] = (policy.get("url") or "").strip()
    cleaned["keywords"] = policy.get("keywords", [])
    cleaned["intensity"] = int(policy.get("intensity") or 1)
    # 添加元数据
    cleaned["_etl_version"] = "1.0"
    cleaned["_etl_timestamp"] = datetime.datetime.now().isoformat()
    return cleaned


def clean_talent(job):
    """清洗单条招聘数据"""
    cleaned = {}
    cleaned["title"] = (job.get("title") or "").strip()
    cleaned["category"] = (job.get("category") or "").strip()
    cleaned["company"] = (job.get("company") or "").strip()
    cleaned["city"] = (job.get("city") or "").strip()
    cleaned["salary_min"] = job.get("salary_min", 0)
    cleaned["salary_max"] = job.get("salary_max", 0)
    cleaned["education"] = (job.get("education") or "").strip()
    cleaned["experience"] = (job.get("experience") or "").strip()
    cleaned["date"] = (job.get("date") or "").strip()
    cleaned["source"] = (job.get("source") or "").strip()
    cleaned["url"] = (job.get("url") or "").strip()
    cleaned["_etl_version"] = "1.0"
    cleaned["_etl_timestamp"] = datetime.datetime.now().isoformat()
    return cleaned


def deduplicate(items, id_fields):
    """基于指定字段去重"""
    seen = set()
    unique = []
    for item in items:
        key_parts = [str(item.get(f, "")) for f in id_fields]
        key = "|".join(key_parts)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


# ============================================================
# 步骤 4: 合并新旧数据（保留历史）
# ============================================================
def merge_with_existing(new_data, existing_path, id_fields):
    """合并新数据与已有的历史数据，保留全部记录"""
    existing = []
    if os.path.exists(existing_path):
        try:
            with open(existing_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            log(f"📖 读取已有数据: {existing_path} ({len(existing)} 条)")
        except (json.JSONDecodeError, Exception) as e:
            log(f"⚠️ 读取已有数据失败: {e}，将覆盖")

    # 合并：新数据优先（可能包含更新的信息）
    merged = new_data + existing

    # 去重（新数据在前，保留最新的）
    deduped = deduplicate(merged, id_fields)

    log(f"🔀 合并后: {len(merged)} 条 → 去重后: {len(deduped)} 条")
    log(f"   新增: {len(new_data)} 条，已有: {len(existing)} 条，去重: {len(merged)-len(deduped)} 条")

    return deduped


# ============================================================
# 步骤 5: 生成统计
# ============================================================
def compute_policy_stats(policies):
    """计算政策统计信息"""
    by_level = {}
    by_region = {}
    by_category = {}
    by_month = {}
    keywords_count = {}
    all_keywords = []

    for p in policies:
        by_level[p["level"]] = by_level.get(p["level"], 0) + 1
        by_region[p["region"]] = by_region.get(p["region"], 0) + 1
        by_category[p["category"]] = by_category.get(p["category"], 0) + 1

        month = p["date"][:7] if p["date"] else "unknown"
        by_month[month] = by_month.get(month, 0) + 1

        for kw in p.get("keywords", []):
            keywords_count[kw] = keywords_count.get(kw, 0) + 1

    # 按日期排序月份
    sorted_months = OrderedDict()
    for m in sorted(by_month.keys()):
        sorted_months[m] = by_month[m]

    # 热词排序
    hot_keywords = sorted(
        [{"keyword": k, "count": v} for k, v in keywords_count.items()],
        key=lambda x: x["count"], reverse=True
    )[:20]

    # 时间范围
    dates = [p["date"] for p in policies if p.get("date")]
    time_span = {}
    if dates:
        time_span = {"start": min(dates), "end": max(dates)}

    return {
        "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_policies": len(policies),
        "time_span": time_span,
        "by_level": by_level,
        "by_region": by_region,
        "by_category": by_category,
        "by_month": dict(sorted_months),
        "hot_keywords": hot_keywords,
    }


def compute_talent_stats(jobs):
    """计算人才招聘统计"""
    by_category = {}
    by_city = {}
    by_company = {}
    by_education = {}
    salary_by_category = {}

    for j in jobs:
        cat = j.get("category", "其他")
        city = j.get("city", "未知")
        company = j.get("company", "未知")
        edu = j.get("education", "不限")

        by_category[cat] = by_category.get(cat, 0) + 1
        by_city[city] = by_city.get(city, 0) + 1
        by_company[company] = by_company.get(company, 0) + 1
        by_education[edu] = by_education.get(edu, 0) + 1

        if cat not in salary_by_category:
            salary_by_category[cat] = []
        smin = j.get("salary_min", 0)
        smax = j.get("salary_max", 0)
        if smin and smax:
            salary_by_category[cat].append((smin + smax) / 2)

    avg_salary = {}
    for cat, vals in salary_by_category.items():
        if vals:
            avg_salary[cat] = round(sum(vals) / len(vals))

    return {
        "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_jobs": len(jobs),
        "by_category": by_category,
        "by_city": dict(sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:15]),
        "by_company": dict(sorted(by_company.items(), key=lambda x: x[1], reverse=True)[:15]),
        "by_education": by_education,
        "avg_salary_by_category": avg_salary,
    }


# ============================================================
# 步骤 6: 更新 changelog
# ============================================================
def update_changelog(module, stats_before, stats_after, new_count):
    """记录每次 ETL 运行的变更"""
    changelog_path = os.path.join(DATA_DIR, "changelog.json")

    entries = []
    if os.path.exists(changelog_path):
        try:
            with open(changelog_path, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except:
            entries = []

    entry = {
        "time": datetime.datetime.now().isoformat(),
        "module": module,
        "before": stats_before,
        "after": stats_after,
        "new_records": new_count,
    }
    entries.append(entry)

    # 只保留最近 100 条
    if len(entries) > 100:
        entries = entries[-100:]

    with open(changelog_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    log(f"📝 changelog 已更新 ({len(entries)} 条记录)")


# ============================================================
# 步骤 7: 全量 ETL 执行
# ============================================================
def run_etl(module, fetch_func, clean_func, id_fields, output_file, stats_output_file):
    """执行完整的 ETL 流程"""
    log(f"{'='*50}")
    log(f"🚀 开始 ETL 流程: {module}")
    log(f"{'='*50}")

    # Step 1: 采集
    new_data = fetch_func()
    if not new_data:
        log(f"❌ {module} 采集失败或无数据")
        return False

    # Step 2: 保存原始数据
    save_raw(new_data, module)

    # Step 3: 清洗
    log(f"🧹 清洗数据...")
    cleaned = [clean_func(item) for item in new_data if clean_func(item)]

    # Step 4: 合并并保留历史
    existing_count = 0
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                existing_count = len(json.load(f))
        except:
            pass

    merged = merge_with_existing(cleaned, output_file, id_fields)

    # Step 5: 写入主数据文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    log(f"💾 主数据已更新: {output_file} ({len(merged)} 条)")

    # Step 6: 计算并保存统计
    if module == "policy":
        stats = compute_policy_stats(merged)
    elif module == "talent":
        stats = compute_talent_stats(merged)
    else:
        log(f"⚠️ 未知模块: {module}")

    with open(stats_output_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    log(f"📊 统计已更新: {stats_output_file}")

    # Step 7: 更新 changelog
    new_count = len(merged) - existing_count if existing_count > 0 else len(merged)
    update_changelog(module, existing_count, len(merged), max(0, new_count))

    return True


# ============================================================
# 主入口
# ============================================================
def main(modules=None):
    """
    主入口
    Args:
        modules: 列表，如 ["policy", "talent"]，默认为全部
    """
    if modules is None:
        modules = ["policy", "talent"]

    results = {}

    for mod in modules:
        import importlib.util
        import sys as _sys
        fetch_path = os.path.join(BASE_DIR, "scripts", f"fetch_{mod}.py")
        if not os.path.exists(fetch_path):
            log(f"❌ 采集脚本不存在: {fetch_path}")
            results[mod] = "❌ 脚本不存在"
            continue

        spec = importlib.util.spec_from_file_location(f"fetch_{mod}", fetch_path)
        fetch_mod = importlib.util.module_from_spec(spec)
        _sys.modules[f"fetch_{mod}"] = fetch_mod
        spec.loader.exec_module(fetch_mod)

        if mod == "policy":
            success = run_etl(
                module="policy",
                fetch_func=fetch_mod.generate_mock_policies,
                clean_func=clean_policy,
                id_fields=["title", "date", "source"],
                output_file=os.path.join(DATA_DIR, "policy_data.json"),
                stats_output_file=os.path.join(DATA_DIR, "stats.json"),
            )
        elif mod == "talent":
            success = run_etl(
                module="talent",
                fetch_func=fetch_mod.generate_mock_jobs,
                clean_func=clean_talent,
                id_fields=["title", "company", "city"],
                output_file=os.path.join(DATA_DIR, "talent_data.json"),
                stats_output_file=os.path.join(DATA_DIR, "talent_stats.json"),
            )
        else:
            log(f"❌ 未知模块: {mod}")
            continue

        results[mod] = "✅ 成功" if success else "❌ 失败"

    log(f"{'='*50}")
    log(f"📋 ETL 执行结果:")
    for mod, result in results.items():
        log(f"  {mod}: {result}")
    log(f"{'='*50}")

    return results


if __name__ == "__main__":
    import sys
    modules = sys.argv[1:] if len(sys.argv) > 1 else None
    main(modules)
