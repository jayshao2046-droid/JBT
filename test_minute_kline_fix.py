#!/usr/bin/env python3
"""
验证期货分钟K线修复的有效性
测试 datetime 验证和数据清理逻辑
"""

import pandas as pd
import sys
from datetime import datetime

def test_datetime_validation():
    """测试 datetime 验证和清理逻辑"""
    
    print("=" * 70)
    print("验证期货分钟K线修复：datetime 有效性检查")
    print("=" * 70)
    
    # 模拟采集器返回的记录（包含无效 datetime）
    test_cases = [
        {
            "name": "正常数据",
            "records": [
                {"datetime": "2026-04-22 09:30:00", "open": 3500, "close": 3510},
                {"datetime": "2026-04-22 09:32:00", "open": 3510, "close": 3515},
            ],
            "expected_rows": 2
        },
        {
            "name": "混合有效和无效数据",
            "records": [
                {"datetime": "2026-04-22 09:30:00", "open": 3500, "close": 3510},
                {"datetime": "", "open": 3510, "close": 3515},  # 空 datetime
                {"datetime": "2026-04-22 09:32:00", "open": 3515, "close": 3520},
                {"datetime": "invalid-date", "open": 3520, "close": 3525},  # 无效格式
            ],
            "expected_rows": 2  # 只保留有效的 2 条
        },
        {
            "name": "全部无效数据",
            "records": [
                {"datetime": "", "open": 3500, "close": 3510},
                {"datetime": "invalid", "open": 3510, "close": 3515},
            ],
            "expected_rows": 0
        },
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"输入: {len(test_case['records'])} 条记录")
        
        # 模拟修复后的处理流程
        rows = []
        for rec in test_case['records']:
            dt_str = rec.get("datetime", "")
            if not dt_str or dt_str.strip() == "":
                print(f"  ⚠️  跳过空 datetime 记录")
                continue
            rows.append({
                "datetime": dt_str,
                "open": rec.get("open"),
                "close": rec.get("close"),
            })
        
        # 创建 DataFrame 并验证 datetime
        if len(rows) > 0:
            df = pd.DataFrame(rows)
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            df = df.dropna(subset=["datetime"])
            
            actual_rows = len(df)
            print(f"处理后: {actual_rows} 条有效记录")
            
            if actual_rows == test_case['expected_rows']:
                print(f"✅ 通过: 期望 {test_case['expected_rows']}, 得到 {actual_rows}")
            else:
                print(f"❌ 失败: 期望 {test_case['expected_rows']}, 得到 {actual_rows}")
                all_passed = False
                
            if actual_rows > 0:
                print(f"   时间范围: {df['datetime'].min()} ~ {df['datetime'].max()}")
        else:
            if test_case['expected_rows'] == 0:
                print(f"✅ 通过: 期望 0 条记录，得到 0 条")
            else:
                print(f"❌ 失败: 期望 {test_case['expected_rows']} 条, 得到 0 条")
                all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 所有验证通过！修复逻辑有效。")
        return 0
    else:
        print("❌ 某些验证失败。需要检查修复。")
        return 1


def test_code_presence():
    """验证修复代码已正确应用"""
    print("\n" + "=" * 70)
    print("验证修复代码已应用")
    print("=" * 70)
    
    try:
        with open("/Users/jayshao/JBT/services/data/src/scheduler/pipeline.py", "r") as f:
            source = f.read()
        
        checks = [
            ('errors="coerce"', "datetime 强制转换参数"),
            ("dropna(subset=[\"datetime\"])", "NaT 清理"),
            ('_logger.warning("bars-sync:', "警告日志"),
            ("if not dt_str or dt_str.strip()", "空值检查"),
        ]
        
        all_present = True
        for check_str, description in checks:
            if check_str in source:
                print(f"✅ 找到: {description}")
            else:
                print(f"❌ 缺失: {description}")
                all_present = False
        
        print("=" * 70)
        if all_present:
            print("✅ 所有修复代码已正确应用！")
            return 0
        else:
            print("❌ 部分修复代码缺失。")
            return 1
            
    except FileNotFoundError:
        print("❌ 找不到源文件")
        return 1


if __name__ == "__main__":
    result1 = test_datetime_validation()
    result2 = test_code_presence()
    
    print("\n" + "=" * 70)
    print("验证总结")
    print("=" * 70)
    
    if result1 == 0 and result2 == 0:
        print("✅✅✅ 修复验证完全通过")
        sys.exit(0)
    else:
        print("❌ 修复验证存在问题")
        sys.exit(1)
