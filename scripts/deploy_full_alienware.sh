#!/bin/bash
# Alienware 完整部署脚本
# 部署心跳报告 + 启动订单追踪 + CTP 断联诊断

echo "=========================================="
echo "Sim-Trading 完整部署"
echo "=========================================="
echo "当前时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. 停止所有相关进程
echo "[1/6] 停止现有进程..."
pkill -f "sim-trading" 2>/dev/null || echo "  sim-trading 未运行"
pkill -f "main.py" 2>/dev/null || echo "  main.py 未运行"
pkill -f "trace_order_source.py" 2>/dev/null || echo "  订单追踪未运行"
pkill -f "diagnose_ctp_disconnect.py" 2>/dev/null || echo "  CTP 诊断未运行"
sleep 3

# 2. 验证文件
echo ""
echo "[2/6] 验证文件..."
cd ~/JBT
if [ ! -f "services/sim-trading/src/health/heartbeat.py" ]; then
    echo "  ❌ heartbeat.py 不存在"
    exit 1
fi
if [ ! -f "scripts/trace_order_source.py" ]; then
    echo "  ❌ trace_order_source.py 不存在"
    exit 1
fi
if [ ! -f "scripts/diagnose_ctp_disconnect.py" ]; then
    echo "  ❌ diagnose_ctp_disconnect.py 不存在"
    exit 1
fi
echo "  ✅ 所有文件就绪"

# 3. 清理旧日志
echo ""
echo "[3/6] 清理旧日志..."
rm -f /tmp/sim-trading.log
rm -f /tmp/order_trace.jsonl
rm -f /tmp/ctp_disconnect_diagnosis.jsonl
echo "  ✅ 日志已清理"

# 4. 启动 sim-trading（带心跳报告）
echo ""
echo "[4/6] 启动 sim-trading（带心跳报告，00:00-08:00 静默）..."
cd ~/JBT
nohup python3 services/sim-trading/src/main.py > /tmp/sim-trading.log 2>&1 &
SIM_PID=$!
echo "  进程 PID: $SIM_PID"

# 5. 启动订单追踪（后台）
echo ""
echo "[5/6] 启动订单追踪..."
nohup python3 scripts/trace_order_source.py > /tmp/order_trace.log 2>&1 &
ORDER_PID=$!
echo "  进程 PID: $ORDER_PID"
echo "  追踪日志: /tmp/order_trace.jsonl"

# 6. 启动 CTP 断联诊断（后台）
echo ""
echo "[6/6] 启动 CTP 断联诊断..."
nohup python3 scripts/diagnose_ctp_disconnect.py > /tmp/ctp_diagnosis.log 2>&1 &
CTP_PID=$!
echo "  进程 PID: $CTP_PID"
echo "  诊断日志: /tmp/ctp_disconnect_diagnosis.jsonl"

# 等待启动
echo ""
echo "等待启动（15秒）..."
sleep 15

# 检查进程状态
echo ""
echo "=========================================="
echo "进程状态"
echo "=========================================="
ps aux | grep -E "sim.*trading|main\.py|trace_order|diagnose_ctp" | grep -v grep

# 显示启动日志
echo ""
echo "=========================================="
echo "Sim-Trading 启动日志（最近 20 行）"
echo "=========================================="
tail -20 /tmp/sim-trading.log

echo ""
echo "=========================================="
echo "订单追踪启动日志（最近 10 行）"
echo "=========================================="
tail -10 /tmp/order_trace.log 2>/dev/null || echo "  日志文件尚未生成"

echo ""
echo "=========================================="
echo "CTP 诊断启动日志（最近 10 行）"
echo "=========================================="
tail -10 /tmp/ctp_diagnosis.log 2>/dev/null || echo "  日志文件尚未生成"

# 计算下一个心跳时间
echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "📊 心跳健康报告："
CURRENT_HOUR=$(date +%H)
if [ $CURRENT_HOUR -ge 0 ] && [ $CURRENT_HOUR -lt 8 ]; then
    echo "  下一次: 今天 08:00（当前静默时段）"
elif [ $CURRENT_HOUR -ge 22 ]; then
    echo "  下一次: 明天 08:00"
else
    NEXT_HOUR=$(( (CURRENT_HOUR / 2) * 2 + 2 ))
    echo "  下一次: 今天 $(printf '%02d' $NEXT_HOUR):00"
fi
echo "  静默时段: 00:00-08:00"
echo ""
echo "🔍 订单追踪："
echo "  状态: 运行中（PID $ORDER_PID）"
echo "  日志: tail -f /tmp/order_trace.log"
echo "  分析: python3 ~/JBT/scripts/analyze_order_trace.py"
echo ""
echo "🔧 CTP 断联诊断："
echo "  状态: 运行中（PID $CTP_PID）"
echo "  日志: tail -f /tmp/ctp_diagnosis.log"
echo "  分析: python3 ~/JBT/scripts/analyze_ctp_disconnect.py"
echo ""
echo "📝 实时日志："
echo "  tail -f /tmp/sim-trading.log"
echo ""
