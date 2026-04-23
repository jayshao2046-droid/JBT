#!/bin/bash
# Deployment script for minute K-line fix
# This script deploys the fix to Mini and verifies it

set -e

echo "=========================================="
echo "部署期货分钟K线采集修复"
echo "=========================================="

# Configuration
MINI_IP="192.168.31.156"
MINI_USER="jaybot"
CONTAINER_NAME="JBT-DATA-8105"
REPO_PATH="~/JBT"

# Step 1: Connect to Mini and pull code
echo ""
echo "[步骤1] 连接Mini并拉取最新代码..."
ssh $MINI_USER@$MINI_IP "cd $REPO_PATH && git pull origin main" 2>&1 | head -20

if [ $? -ne 0 ]; then
    echo "❌ Git pull失败"
    exit 1
fi

echo "✅ 代码已拉取"

# Step 2: Verify code changes on Mini
echo ""
echo "[步骤2] 验证代码修改..."
ssh $MINI_USER@$MINI_IP "grep -q 'errors=\"coerce\"' $REPO_PATH/services/data/src/scheduler/pipeline.py && echo '✅ datetime coerce 已应用' || echo '❌ 修改未找到'"

# Step 3: Restart container
echo ""
echo "[步骤3] 重启容器..."
ssh $MINI_USER@$MINI_IP "docker restart $CONTAINER_NAME" 2>&1

echo "✅ 容器已重启"

# Step 4: Wait for container to be healthy
echo ""
echo "[步骤4] 等待容器就绪..."
sleep 5

# Step 5: Health check
echo ""
echo "[步骤5] 健康检查..."
ssh $MINI_USER@$MINI_IP "curl -s http://localhost:8105/health | grep -q 'ok' && echo '✅ API 健康' || echo '⚠️  API 检查'"

# Step 6: Monitor logs
echo ""
echo "[步骤6] 监控初始日志..."
ssh $MINI_USER@$MINI_IP "docker logs $CONTAINER_NAME 2>&1 | tail -30"

echo ""
echo "=========================================="
echo "✅ 部署完成"
echo "=========================================="
echo ""
echo "下一步验证（明天早盘09:30+）："
echo "  ssh $MINI_USER@$MINI_IP"
echo "  docker exec $CONTAINER_NAME tail -100 /data/logs/info_*.log | grep 'bars-sync'"
echo ""
echo "预期看到："
echo "  bars-sync minute: SHFE_rb2605 → 70 bars (from 70 records), first=..., last=..."
echo ""
