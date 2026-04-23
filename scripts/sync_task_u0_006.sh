#!/bin/bash
# TASK-U0-20260417-006 代码同步脚本
#
# 功能：将修改后的代码同步到 Alienware 和 Studio
# 执行位置：MacBook Air

set -e

echo "=========================================="
echo "TASK-U0-20260417-006 代码同步"
echo "=========================================="
echo ""

# 配置
ALIENWARE_HOST="17621@192.168.31.187"
ALIENWARE_PATH="C:/Users/17621/JBT/services/data/"
STUDIO_HOST="jay@192.168.31.142"
STUDIO_PATH="~/JBT/services/decision/"

echo "[1/2] 同步 data 服务到 Alienware (192.168.31.187)..."
echo ""

# 同步 data 服务
rsync -avz --progress \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='runtime/' \
  --exclude='logs/' \
  services/data/ \
  "${ALIENWARE_HOST}:${ALIENWARE_PATH}"

echo ""
echo "✓ data 服务同步完成"
echo ""

echo "[2/2] 同步 decision 服务到 Studio (192.168.31.142)..."
echo ""

# 同步 decision 服务
rsync -avz --progress \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='runtime/' \
  --exclude='logs/' \
  services/decision/ \
  "${STUDIO_HOST}:${STUDIO_PATH}"

echo ""
echo "✓ decision 服务同步完成"
echo ""

echo "=========================================="
echo "同步完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 在 Alienware 上配置 Windows 任务计划"
echo "   cd C:\\Users\\17621\\JBT\\services\\data\\scripts"
echo "   .\\setup_researcher_windows_task.ps1"
echo ""
echo "2. 在 Studio 上重启 decision 服务"
echo "   ssh ${STUDIO_HOST}"
echo "   cd ~/JBT/services/decision"
echo "   pkill -f 'uvicorn.*decision'"
echo "   nohup python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8104 > logs/decision.log 2>&1 &"
echo ""
echo "3. 验证服务"
echo "   curl http://192.168.31.187:8199/health"
echo "   curl http://192.168.31.142:8104/health"
echo ""
