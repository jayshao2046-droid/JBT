#!/usr/bin/env python3
"""
通过 rsync/scp 同步代码到 Alienware
绕过 git 命令问题
"""

import subprocess
import sys
import time
import requests

HOST = "17621@192.168.31.187"
LOCAL_PATH = "/Users/jayshao/JBT"
REMOTE_PATH = "C:/Users/17621/jbt"

def run_cmd(command, description):
    """执行本地命令"""
    print(f"\n→ {description}")
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"✓ 成功")
        if result.stdout.strip():
            print(f"  {result.stdout.strip()}")
        return True
    else:
        print(f"✗ 失败")
        if result.stderr.strip():
            print(f"  {result.stderr.strip()}")
        return False

def main():
    print("=" * 60)
    print("Alienware 代码同步部署")
    print("=" * 60)

    # 1. 停止现有服务
    print("\n[1/5] 停止现有服务...")
    subprocess.run(
        f'ssh {HOST} "taskkill /F /IM python.exe"',
        shell=True,
        capture_output=True
    )
    print("✓ 已发送停止命令")
    time.sleep(3)

    # 2. 同步关键文件
    print("\n[2/5] 同步代码文件...")

    files_to_sync = [
        "services/data/run_researcher_server.py",
        "services/data/src/researcher/queue_manager.py",
        "services/data/src/researcher/reporter.py",
        "services/decision/src/llm/researcher_phi4_scorer.py",
    ]

    for file in files_to_sync:
        local_file = f"{LOCAL_PATH}/{file}"
        remote_file = f"{HOST}:{REMOTE_PATH}/{file}"

        cmd = f'scp "{local_file}" "{remote_file}"'
        success = run_cmd(cmd, f"同步 {file}")

        if not success:
            print(f"⚠️  {file} 同步失败，继续...")

    # 3. 启动服务
    print("\n[3/5] 启动研究员服务...")
    subprocess.run(
        f'ssh {HOST} "cd C:/Users/17621/jbt && start /B python services\\\\data\\\\run_researcher_server.py"',
        shell=True,
        capture_output=True
    )
    print("✓ 已发送启动命令")

    print("\n等待服务启动...")
    for i in range(10):
        time.sleep(1)
        try:
            r = requests.get("http://192.168.31.187:8199/health", timeout=2)
            if r.status_code == 200:
                print(f"✓ 服务已启动 ({i+1}秒)")
                break
        except:
            print(f"  等待中... {i+1}秒")
    else:
        print("✗ 服务启动超时")
        sys.exit(1)

    # 4. 验证队列 API
    print("\n[4/5] 验证队列 API...")
    try:
        r = requests.get("http://192.168.31.187:8199/queue/status", timeout=5)
        data = r.json()

        if "pending_count" in data:
            print("✓ 队列状态 API 正常")
            print(f"  待读: {data.get('pending_count', 0)}")
            print(f"  处理中: {data.get('processing_count', 0)}")
        else:
            print("✗ API 返回格式错误（仍是旧版本）")
            print(f"  返回: {data}")
            print("\n可能原因: 文件同步失败或服务未重启")
            sys.exit(1)
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        sys.exit(1)

    # 5. 运行完整测试
    print("\n[5/5] 运行完整测试...")
    result = subprocess.run(
        "python3 scripts/test_researcher_python.py",
        shell=True,
        cwd=LOCAL_PATH
    )

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✓ 部署和测试完成")
        print("=" * 60)
    else:
        print("\n⚠️  测试未完全通过，请检查日志")

if __name__ == "__main__":
    main()
