#!/usr/bin/env python3
"""
政策数据手动录入工具
将手动收集的政策数据导入主数据文件（自动去重合并）

用法：
  python3 scripts/manual_import.py                    # 导入 data/manual/ 下的所有文件
  python3 scripts/manual_import.py data/manual/xxx.json  # 导入指定文件

输入格式：
  JSON 或 CSV 文件，放在 data/manual/ 目录下
"""

import json
import csv
import os
import sys
import datetime
import glob

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MANUAL_DIR = os.path.join(DATA_DIR, "manual")
POLICY_FILE = os.path.join(DATA_DIR, "policy_data.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(MANUAL_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [IMPORT] {msg}"
    print(line)
    log_path = os.path.join(LOG_DIR, "import.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


POLICY_SCHEMA = {
    "title": "政策标题（必填）",
    "date": "发布日期，格式 YYYY-MM-DD（必填）",
    "source": "发布机构（必填）",
    "level": "级别: national / provincial / city（必填）",
    "region": "地区: 全国 / 广东省 / 深圳市 等（必填）",
    "category": "类别: 产业促进 / 空域管理 / 基础设施 / 资金补贴 / 适航审定 / 人才引进",
    "summary": "政策摘要（可选）",
    "url": "原文链接（可选）",
    "keywords": "关键词列表，如 [\"低空经济\", \"空域管理\"]（可选）",
    "intensity": "力度评分 1-5（可选）",
}


def generate_template():
    """生成录入模板 JSON"""
    template = {
        "source_note": "将此文件放在 data/manual/ 目录下，运行 manual_import.py 自动导入",
        "import_time": datetime.datetime.now().isoformat(),
        "policies": [
            {
                "title": "示例：XX市低空经济促进政策",
                "date": "2026-04-30",
                "source": "XX市人民政府",
                "level": "city",
                "region": "XX市",
                "category": "产业促进",
                "summary": "政策主要内容摘要",
                "url": "https://example.gov.cn/policy/xxx",
                "keywords": ["低空经济", "产业促进"],
                "intensity": 4,
            }
        ],
    }
    template_path = os.path.join(MANUAL_DIR, "template.json")
    with open(template_path, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    log(f"📝 模板已生成: {template_path}")
    return template_path


def validate_policy(p):
    """验证单条政策数据"""
    errors = []
    if not p.get("title"):
        errors.append("缺少 title")
    if not p.get("date"):
        errors.append("缺少 date")
    if not p.get("source"):
        errors.append("缺少 source")
    if p.get("level") not in ("national", "provincial", "city", ""):
        errors.append(f"level 值无效: {p.get('level')}")
    if not p.get("region"):
        errors.append("缺少 region")
    return errors


def load_json_file(filepath):
    """加载 JSON 文件，支持单条或列表格式"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if "policies" in data:
            return data["policies"]
        elif "records" in data:
            return data["records"]
        else:
            return [data]
    return []


def load_csv_file(filepath):
    """加载 CSV 文件"""
    policies = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 处理 keywords 字段（可能以字符串形式存储）
            if "keywords" in row and isinstance(row["keywords"], str):
                try:
                    row["keywords"] = json.loads(row["keywords"])
                except:
                    row["keywords"] = [kw.strip() for kw in row["keywords"].split(",") if kw.strip()]
            # 处理 intensity
            if "intensity" in row and row["intensity"]:
                try:
                    row["intensity"] = int(row["intensity"])
                except:
                    row["intensity"] = 3
            policies.append(row)
    return policies


def import_manual_files(filepaths=None):
    """导入手动收集的数据"""
    log("=" * 50)
    log("📥 手动数据导入开始")
    log("=" * 50)

    # 收集要导入的文件
    if filepaths:
        files = filepaths
    else:
        files = glob.glob(os.path.join(MANUAL_DIR, "*.json"))
        files += glob.glob(os.path.join(MANUAL_DIR, "*.csv"))
        # 排除模板文件
        files = [f for f in files if "template" not in os.path.basename(f)]

    if not files:
        log("⚠️  没有找到要导入的文件")
        log(f"💡 模板文件: {os.path.join(MANUAL_DIR, 'template.json')}")
        log(f"💡 将你的政策数据文件（JSON/CSV）放在 {MANUAL_DIR}/ 目录下")
        return []

    # 读取所有手动数据
    all_new = []
    for fp in sorted(files):
        try:
            if fp.endswith(".csv"):
                policies = load_csv_file(fp)
            else:
                policies = load_json_file(fp)

            # 验证
            valid = []
            for p in policies:
                errs = validate_policy(p)
                if errs:
                    log(f"  ⚠️  跳过无效记录 ({', '.join(errs)}): {p.get('title', '无标题')[:30]}")
                else:
                    valid.append(p)

            log(f"  📄 {os.path.basename(fp)}: {len(policies)} 条 → 有效 {len(valid)} 条")
            all_new.extend(valid)
        except Exception as e:
            log(f"  ❌ 读取失败 {os.path.basename(fp)}: {e}")

    if not all_new:
        log("⚠️  没有有效数据可导入")
        return []

    log(f"📦 共 {len(all_new)} 条有效数据")

    # 加载现有数据
    existing = []
    if os.path.exists(POLICY_FILE):
        with open(POLICY_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        log(f"📖 现有数据: {len(existing)} 条")

    # 合并（新数据在前，去重保留最新）
    merged = all_new + existing
    # 去重（内联 deduplicate）
    seen = set()
    deduped = []
    for item in merged:
        key_parts = [str(item.get(f, "")) for f in ["title", "date", "source"]]
        key = "|".join(key_parts)
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    log(f"🔀 合并后 {len(merged)} 条 → 去重后 {len(deduped)} 条")
    log(f"   新增: {len(all_new)} 条，原有: {len(existing)} 条")

    # 写入
    with open(POLICY_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    log(f"💾 已写入 {POLICY_FILE}")

    # 移动已导入的文件到已处理目录
    processed_dir = os.path.join(MANUAL_DIR, "processed")
    os.makedirs(processed_dir, exist_ok=True)
    for fp in files:
        import shutil
        shutil.move(fp, os.path.join(processed_dir, os.path.basename(fp)))
    log(f"📂 已导入文件移至 {processed_dir}/")

    return deduped


def main():
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = None

    # 首先生成模板（如果不存在）
    template_path = os.path.join(MANUAL_DIR, "template.json")
    if not os.path.exists(template_path):
        generate_template()

    # 导入手动数据
    result = import_manual_files(files)

    if result:
        log(f"🎉 导入完成！共 {len(result)} 条数据")
    else:
        log("💡 你可以在 data/manual/template.json 看到录入格式")
        log("💡 按格式填好后，再运行此脚本导入")

    return result


if __name__ == "__main__":
    main()
