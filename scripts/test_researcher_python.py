#!/usr/bin/env python3
"""研究员数据流测试脚本（Python版本）"""

import requests
import json
import time
from datetime import datetime

# 配置
ALIENWARE_API = "http://192.168.31.223:8199"
STUDIO_API = "http://192.168.31.142:8104"

def print_step(step, total, msg):
    print(f"\n[{step}/{total}] {msg}...")

def success(msg):
    print(f"✓ {msg}")

def error(msg):
    print(f"✗ {msg}")

def info(msg):
    print(f"→ {msg}")

def main():
    print("=" * 50)
    print("研究员数据流测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 步骤 1：检查服务健康
    print_step(1, 5, "检查服务健康")

    try:
        r = requests.get(f"{ALIENWARE_API}/health", timeout=5)
        if r.status_code == 200:
            success("Alienware 研究员服务正常")
        else:
            error(f"Alienware 服务异常: {r.status_code}")
            return
    except Exception as e:
        error(f"Alienware 服务不可达: {e}")
        return

    try:
        r = requests.get(f"{STUDIO_API}/health", timeout=5)
        if r.status_code == 200:
            success("Studio decision 服务正常")
        else:
            error(f"Studio 服务异常: {r.status_code}")
            return
    except Exception as e:
        error(f"Studio 服务不可达: {e}")
        return

    # 步骤 2：查看队列状态（触发前）
    print_step(2, 5, "查看队列状态（触发前）")

    try:
        r = requests.get(f"{ALIENWARE_API}/queue/status", timeout=5)
        queue_status = r.json()
        print(json.dumps(queue_status, indent=2, ensure_ascii=False))
        pending_count_before = queue_status.get('pending', 0)
        info(f"待读队列: {pending_count_before} 个报告")
    except Exception as e:
        error(f"获取队列状态失败: {e}")
        pending_count_before = 0

    # 步骤 3：触发研究员分析
    print_step(3, 5, "触发研究员分析")

    current_hour = datetime.now().hour
    info(f"触发 {current_hour}:00 分析...")

    try:
        r = requests.post(
            f"{ALIENWARE_API}/run",
            json={"hour": current_hour},
            timeout=10
        )
        result = r.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        success("研究员已触发")
    except Exception as e:
        error(f"触发失败: {e}")
        return

    # 步骤 4：等待报告生成
    print_step(4, 5, "等待报告生成（30秒）")

    for i in range(6):
        time.sleep(5)
        info(f"等待中... {(i+1)*5}秒")

    try:
        r = requests.get(f"{ALIENWARE_API}/queue/status", timeout=5)
        queue_status = r.json()
        pending_count_after = queue_status.get('pending', 0)

        print(json.dumps(queue_status, indent=2, ensure_ascii=False))

        if pending_count_after > pending_count_before:
            success(f"新报告已入队（待读：{pending_count_after}）")
        else:
            error(f"未检测到新报告（待读：{pending_count_after}）")
            info("可能原因：数据未就绪或已有报告")

        # 获取待读报告列表
        pending_reports = queue_status.get('pending_reports', [])
    except Exception as e:
        error(f"获取队列状态失败: {e}")
        return

    # 步骤 5：触发 Studio 评级
    print_step(5, 5, "触发 Studio 评级")

    if pending_count_after == 0:
        info("待读队列为空，跳过评级测试")
        return

    try:
        # 获取第一个待读报告
        if not pending_reports:
            error("待读报告列表为空")
            return

        first_report = pending_reports[0]
        report_id = first_report.get('report_id')

        info(f"评级报告 ID: {report_id}")

        # 调用评级 API（使用 report_id 标记已读）
        r = requests.post(
            f"{ALIENWARE_API}/reports/{report_id}/mark_read",
            json={"score": 0.85, "reasoning": "测试评级", "model": "qwen3:14b"},
            timeout=120
        )

        mark_result = r.json()
        print(json.dumps(mark_result, indent=2, ensure_ascii=False))

        if mark_result.get('status') == 'success':
            success("报告已标记为已读")

            # 检查队列状态
            time.sleep(2)
            r = requests.get(f"{ALIENWARE_API}/queue/status", timeout=5)
            queue_final = r.json()
            pending_count_final = queue_final.get('pending', 0)
            completed_count = queue_final.get('completed', 0)

            if pending_count_final < pending_count_after:
                success(f"队列更新成功（待读：{pending_count_final}，已完成：{completed_count}）")
            else:
                error("队列状态未更新")
        else:
            error("标记已读失败")

    except Exception as e:
        error(f"评级过程失败: {e}")

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
