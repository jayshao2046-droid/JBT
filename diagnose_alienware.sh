#!/bin/bash
# Alienware sim-trading 诊断脚本
# 生成时间: 2026-04-16

echo "=========================================="
echo "Alienware sim-trading 诊断报告"
echo "=========================================="
echo ""

# 1. 检查 sim-trading 服务状态
echo "1. 检查 sim-trading 服务健康状态..."
curl -s http://192.168.31.223:8101/health || echo "❌ 服务不可达"
echo ""

# 2. 检查系统状态
echo "2. 检查系统状态..."
curl -s http://192.168.31.223:8101/api/v1/system/state | python3 -m json.tool 2>/dev/null || echo "❌ 无法获取系统状态"
echo ""

# 3. 检查最近订单
echo "3. 检查最近订单..."
curl -s http://192.168.31.223:8101/api/v1/orders | python3 -m json.tool 2>/dev/null || echo "❌ 无法获取订单"
echo ""

# 4. 检查 Studio decision 服务
echo "4. 检查 Studio decision 服务..."
curl -s http://192.168.31.142:8104/health || echo "❌ Studio decision 不可达"
echo ""

# 5. SSH 到 Alienware 查看日志（需要手动执行）
echo "5. 如需查看 Alienware 日志，请手动执行："
echo "   ssh alienware 'tail -100 /path/to/sim-trading.log | grep -E \"ORDER|TRADE\"'"
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
