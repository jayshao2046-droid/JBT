#!/usr/bin/env python3
"""
Alienware 远程部署脚本
通过 SSH 执行部署命令
"""

import subprocess
import sys
import time

HOST = "17621@192.168.31.223"
JBT_PATH = "C:/Users/17621/jbt"

def run_ssh(command, description):
    """执行 SSH 命令"""
    print(f"\n→ {description}")
    print(f"  命令: {command}")

    full_cmd = f'ssh {HOST} "{command}"'
    result = subprocess.run(
        full_cmd,
        shell=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )

    if result.stdout:
        print(f"  输出: {result.stdout.strip()}")
    if result.stderr:
        print(f"  错误: {result.stderr.strip()}")

    return result.returncode == 0

def main():
    print("=" * 60)
    print("Alienware 远程部署")
    print("=" * 60)

    # 1. 停止现有服务
    print("\n[1/4] 停止现有服务...")
    run_ssh(
        "taskkill /F /IM python.exe",
        "停止所有 Python 进程"
    )
    time.sleep(2)

    # 2. 拉取最新代码（尝试多种方式）
    print("\n[2/4] 拉取最新代码...")

    # 方式1: 直接 git pull
    success = run_ssh(
        f"cd {JBT_PATH} && git pull",
        "尝试 git pull"
    )

    if not success:
        # 方式2: 使用完整路径
        success = run_ssh(
            f'cd {JBT_PATH} && "C:\\Program Files\\Git\\bin\\git.exe" pull',
            "使用完整路径 git pull"
        )

    if not success:
        print("\n⚠️  git pull 失败，尝试手动同步...")
        print("请在 Alienware 上手动执行:")
        print(f"  cd {JBT_PATH}")
        print("  git pull")

        response = input("\n已手动执行 git pull? (y/n): ")
        if response.lower() != 'y':
            print("部署中止")
            sys.exit(1)

    # 3. 启动服务
    print("\n[3/4] 启动研究员服务...")
    run_ssh(
        f"cd {JBT_PATH} && start /B python services\\data\\run_researcher_server.py",
        "后台启动服务"
    )

    print("\n等待服务启动...")
    time.sleep(5)

    # 4. 验证服务
    print("\n[4/4] 验证服务...")

    import requests
    try:
        r = requests.get("http://192.168.31.223:8199/health", timeout=5)
        if r.status_code == 200:
            print("✓ 服务健康检查通过")
        else:
            print(f"✗ 健康检查失败: {r.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"✗ 无法连接服务: {e}")
        sys.exit(1)

    # 测试队列状态
    try:
        r = requests.get("http://192.168.31.223:8199/queue/status", timeout=5)
        data = r.json()

        if "pending_count" in data:
            print("✓ 队列状态 API 正常")
            print(f"  待读: {data['pending_count']}")
            print(f"  处理中: {data['processing_count']}")
        else:
            print("✗ 队列状态 API 返回格式错误（可能是旧版本）")
            print(f"  返回: {data}")
            sys.exit(1)
    except Exception as e:
        print(f"✗ 队列状态检查失败: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ 部署完成")
    print("=" * 60)
    print("\n下一步: 运行测试脚本")
    print("  python3 scripts/test_researcher_python.py")

if __name__ == "__main__":
    main()
