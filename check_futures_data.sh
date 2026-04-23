#!/bin/bash
# 检查期货分钟K线数据采集状态

echo "========================================"
echo "期货分钟K线数据采集状态检查"
echo "========================================"
echo ""

# 1. 检查容器时区
echo "1. 容器时区:"
ssh jaybot@192.168.31.74 "docker exec JBT-DATA-8105 date"
echo ""

# 2. 检查交易时段判断
echo "2. 交易时段判断:"
ssh jaybot@192.168.31.74 "docker exec JBT-DATA-8105 python3 -c \"
import sys
sys.path.insert(0, '/app')
from datetime import datetime
from src.scheduler.data_scheduler import _is_trading_session
now = datetime.now()
is_trading = _is_trading_session(now)
print(f'当前时间: {now.strftime(\\\"%Y-%m-%d %H:%M:%S\\\")}')
print(f'是否交易时段: {is_trading}')
\""
echo ""

# 3. 检查最近的采集日志
echo "3. 最近的采集日志 (最后10条):"
ssh jaybot@192.168.31.74 "docker logs JBT-DATA-8105 2>&1 | grep '国内期货分钟K线' | tail -10"
echo ""

# 4. 检查最新数据文件
echo "4. 最新数据文件 (螺纹钢 rb2510):"
ssh jaybot@192.168.31.74 "find /Users/jaybot/JBT/data/futures_minute/1m -name 'SHFE_rb2510' -type d -exec ls -lht {}/202604.parquet 2>/dev/null \; | head -1"
echo ""

echo "========================================"
echo "提示: 下午开盘时间 13:30，夜盘开盘时间 21:00"
echo "========================================"
