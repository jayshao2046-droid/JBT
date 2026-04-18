#!/bin/bash
# Alienware 部署脚本 - 心跳健康报告
# 在 Alienware (192.168.31.223) 上执行

echo "=========================================="
echo "Sim-Trading 心跳健康报告部署"
echo "=========================================="
echo ""

# 1. 检查当前进程
echo "[1/5] 检查当前 sim-trading 进程..."
ps aux | grep -E "sim.*trading|main\.py" | grep -v grep

# 2. 停止现有进程
echo ""
echo "[2/5] 停止现有 sim-trading 进程..."
pkill -f "sim-trading" || echo "没有运行中的进程"
pkill -f "main.py" || echo "没有运行中的进程"
sleep 2

# 3. 验证文件
echo ""
echo "[3/5] 验证文件..."
ls -lh ~/JBT/services/sim-trading/src/health/heartbeat.py
ls -lh ~/JBT/scripts/trace_order_source.py
ls -lh ~/JBT/scripts/diagnose_ctp_disconnect.py

# 4. 启动 sim-trading（后台运行）
echo ""
echo "[4/5] 启动 sim-trading（带心跳报告）..."
cd ~/JBT
nohup python3 services/sim-trading/src/main.py > /tmp/sim-trading.log 2>&1 &
SIM_PID=$!
echo "进程 PID: $SIM_PID"

# 5. 等待启动并检查日志
echo ""
echo "[5/5] 等待启动（10秒）..."
sleep 10

echo ""
echo "=========================================="
echo "启动日志（最近 30 行）："
echo "=========================================="
tail -30 /tmp/sim-trading.log

echo ""
echo "=========================================="
echo "进程状态："
echo "=========================================="
ps aux | grep -E "sim.*trading|main\.py" | grep -v grep

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "下一个心跳报告时间："
CURRENT_HOUR=$(date +%H)
NEXT_HOUR=$(( (CURRENT_HOUR / 2) * 2 + 2 ))
if [ $NEXT_HOUR -ge 24 ]; then
    NEXT_HOUR=$(( NEXT_HOUR - 24 ))
    echo "  明天 $(printf '%02d' $NEXT_HOUR):00"
else
    echo "  今天 $(printf '%02d' $NEXT_HOUR):00"
fi
echo ""
echo "实时日志："
echo "  tail -f /tmp/sim-trading.log"
echo ""
echo "订单追踪（按需启动）："
echo "  python3 ~/JBT/scripts/trace_order_source.py"
echo ""
