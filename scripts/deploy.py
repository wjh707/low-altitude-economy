#!/usr/bin/env python3
"""
一键更新脚本：运行 ETL 管道 → 复制数据到 dashboard → 推送到 GitHub

用法：
  python3 scripts/deploy.py             # 更新全部模块
  python3 scripts/deploy.py policy      # 仅更新政策模块
  python3 scripts/deploy.py talent      # 仅更新人才模块
"""

import os
import sys
import json
import base64
import datetime
import subprocess
import urllib.request
import urllib.error

# ============================================================
# 配置
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
LOG_DIR = os.path.join(BASE_DIR, "logs")

TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "wjh707"
REPO = "low-altitude-economy"

os.makedirs(LOG_DIR, exist_ok=True)


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [DEPLOY] {msg}"
    print(line)
    log_path = os.path.join(LOG_DIR, "deploy.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# 步骤 1: 运行 ETL 管道
# ============================================================
def run_etl(modules):
    """运行指定的 ETL 模块"""
    log("🚀 运行 ETL 管道...")
    
    # 动态导入
    sys.path.insert(0, BASE_DIR)
    from scripts import etl_pipeline
    
    results = etl_pipeline.main(modules)
    
    log(f"📋 ETL 结果: {results}")
    return all(v == "✅ 成功" for v in results.values())


# ============================================================
# 步骤 2: 复制数据到 dashboard 目录
# ============================================================
def copy_to_dashboard():
    """将数据文件复制到 dashboard 目录"""
    log("📂 复制数据文件到 dashboard...")
    
    data_map = {
        "policy_data.json": "policy_data.json",
        "stats.json": "stats.json",
        "talent_data.json": "talent_data.json",
        "talent_stats.json": "talent_stats.json",
        "company_news.json": "company_news.json",
        "companies.json": "companies.json",
    }
    
    copied = []
    for src_name, dst_name in data_map.items():
        src = os.path.join(DATA_DIR, src_name)
        dst = os.path.join(DASHBOARD_DIR, dst_name)
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, dst)
            copied.append(dst_name)
            log(f"  ✅ {dst_name}")
        else:
            log(f"  ⚠️ {src_name} 不存在，跳过")
    
    return copied


# ============================================================
# 步骤 3: 推送到 GitHub
# ============================================================
def upload_to_github(file_pairs):
    """使用 git 推送 dashboard 目录文件到 GitHub"""
    if not TOKEN:
        log("❌ GITHUB_TOKEN 未设置，跳过上传")
        return False
    
    log("☁️  推送到 GitHub (git push)...")
    
    # git add dashboard 目录下的所有更新文件
    dashboard_dir = os.path.join(BASE_DIR, "dashboard")
    os.chdir(BASE_DIR)
    
    # 只 add 需要推送的 dashboard 文件
    add_files = []
    for local_path, github_path in file_pairs:
        if os.path.exists(local_path):
            add_files.append(github_path)
    
    add_cmd = ["git", "add"] + [os.path.join("dashboard", f) for f in add_files]
    result = subprocess.run(add_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"  ❌ git add 失败: {result.stderr[:200]}")
        return False
    
    # 检查是否有变更
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not result.stdout.strip():
        log("  ℹ️  无变更，跳过推送")
        return True
    
    # commit
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    result = subprocess.run(
        ["git", "commit", "-m", f"🤖 自动更新: {today} 低空经济数据"],
        capture_output=True, text=True
    )
    if result.returncode != 0 and "nothing to commit" not in result.stderr:
        log(f"  ⚠️  commit 可能失败: {result.stderr[:200]}")
    
    # push
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        log("  ✅ 推送成功")
        for f in add_files:
            log(f"  ✅ {f}")
        return True
    else:
        log(f"  ❌ git push 失败: {result.stderr[:200]}")
        return False


# ============================================================
# 主流程
# ============================================================
def main():
    log("=" * 50)
    log("🚀 低空经济情报系统 - 一键更新开始")
    log("=" * 50)
    
    # 解析命令行参数
    modules = sys.argv[1:] if len(sys.argv) > 1 else ["policy", "talent"]
    log(f"📋 更新模块: {', '.join(modules)}")
    
    # Step 1: ETL
    etl_ok = run_etl(modules)
    if not etl_ok:
        log("⚠️  ETL 部分模块失败，继续后续步骤")
    
    # Step 2: 复制到 dashboard
    copied = copy_to_dashboard()
    
    # Step 3: 推送到 GitHub
    file_pairs = [
        (os.path.join(DASHBOARD_DIR, f), f)
        for f in copied
    ]
    # 也上传 index.html（可能已修改）
    index_path = os.path.join(DASHBOARD_DIR, "index.html")
    if os.path.exists(index_path):
        file_pairs.append((index_path, "index.html"))
    talent_path = os.path.join(DASHBOARD_DIR, "talent.html")
    if os.path.exists(talent_path):
        file_pairs.append((talent_path, "talent.html"))
    
    upload_ok = upload_to_github(file_pairs)
    
    log("=" * 50)
    if upload_ok:
        log("🎉 一键更新完成！所有文件已推送到 GitHub")
        log(f"🌐 https://wjh707.github.io/low-altitude-economy/")
    else:
        log("⚠️  更新完成，但部分文件上传失败")
    log("=" * 50)
    
    return 0 if upload_ok else 1


if __name__ == "__main__":
    sys.exit(main())
