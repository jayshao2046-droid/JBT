#!/bin/bash
# Studio decision 服务重启脚本
# 在 Studio (192.168.31.142) 上执行

echo "=========================================="
echo "Studio decision 服务重启"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# 配置
JBT_ROOT="$HOME/jbt"
DECISION_SERVICE="$JBT_ROOT/services/decision"
VENV_PYTHON="$JBT_ROOT/.venv/bin/python"

# 步骤 1：拉取最新代码
echo "[1/4] 拉取最新代码..."
echo ""

cd "$JBT_ROOT"
git pull
echo ""

# 步骤 2：停止现有服务
echo "[2/4] 停止现有服务..."
echo ""

pkill -f "uvicorn.*decision" && echo "  ✓ 服务已停止" || echo "  ⚠ 无运行中的服务"
sleep 2
echo ""

# 步骤 3：启动服务
echo "[3/4] 启动 decision 服务..."
echo ""

cd "$DECISION_SERVICE"

# 确保日志目录存在
mkdir -p logs

# 启动服务
nohup "$VENV_PYTHON" -m uvicorn src.api.app:app \
  --host 0.0.0.0 \
  --port 8104 \
  > logs/decision.log 2>&1 &

PID=$!
echo "  ✓ 服务已启动 (PID: $PID)"
echo ""

# 等待服务启动
echo "  等待服务启动 (5秒)..."
sleep 5
echo ""

# 步骤 4：验证服务
echo "[4/4] 验证服务..."
echo ""

# 测试健康检查
if curl -s http://localhost:8104/health > /dev/null; then
    echo "  ✓ 服务正常运行"
    curl -s http://localhost:8104/health | jq '.'
else
    echo "  ✗ 服务不可用"
    echo ""
    echo "查看日志:"
    echo "  tail -50 $DECISION_SERVICE/logs/decision.log"
    exit 1
fi

echo ""
echo "=========================================="
echo "重启完成"
echo "=========================================="
echo ""
echo "服务信息:"
echo "  端口: 8104"
echo "  PID: $PID"
echo "  日志: $DECISION_SERVICE/logs/decision.log"
echo ""
echo "查看日志:"
echo "  tail -f $DECISION_SERVICE/logs/decision.log"
echo ""
echo "查看评级日志:"
echo "  tail -f $DECISION_SERVICE/logs/decision.log | grep -E '(SCORER|收到研究员报告|评级)'"
echo ""
