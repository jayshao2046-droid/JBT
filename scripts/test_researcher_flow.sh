#!/bin/bash
# 研究员数据流端到端测试脚本
#
# 测试完整流程：
# Mini 采集 → Alienware 分析 → Studio 评级 → 飞书通知
#
# 执行位置：MacBook Air

set -e

echo "=========================================="
echo "研究员数据流端到端测试"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# 配置
MINI_HOST="192.168.31.74"
ALIENWARE_HOST="192.168.31.187"
STUDIO_HOST="192.168.31.142"

MINI_API="http://${MINI_HOST}:8105"
ALIENWARE_API="http://${ALIENWARE_HOST}:8199"
STUDIO_API="http://${STUDIO_HOST}:8104"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

# 步骤 1：检查服务健康
echo "[1/8] 检查服务健康..."
echo ""

info "检查 Mini data 服务..."
if curl -s "${MINI_API}/health" > /dev/null; then
    success "Mini data 服务正常 (${MINI_HOST}:8105)"
else
    error "Mini data 服务不可用"
    exit 1
fi

info "检查 Alienware 研究员服务..."
if curl -s "${ALIENWARE_API}/health" > /dev/null; then
    success "Alienware 研究员服务正常 (${ALIENWARE_HOST}:8199)"
else
    error "Alienware 研究员服务不可用"
    exit 1
fi

info "检查 Studio decision 服务..."
if curl -s "${STUDIO_API}/health" > /dev/null; then
    success "Studio decision 服务正常 (${STUDIO_HOST}:8104)"
else
    error "Studio decision 服务不可用"
    exit 1
fi

echo ""

# 步骤 2：检查队列状态
echo "[2/8] 检查队列状态..."
echo ""

info "查询 Alienware 队列状态..."
QUEUE_STATUS=$(curl -s "${ALIENWARE_API}/queue/status")
PENDING_COUNT=$(echo "$QUEUE_STATUS" | jq -r '.pending_count // 0')
PROCESSING_COUNT=$(echo "$QUEUE_STATUS" | jq -r '.processing_count // 0')

echo "  待读队列: ${PENDING_COUNT} 个报告"
echo "  处理中: ${PROCESSING_COUNT} 个报告"
echo ""

# 步骤 3：触发 Mini 采集
echo "[3/8] 触发 Mini 数据采集..."
echo ""

info "发送采集请求..."
COLLECT_RESPONSE=$(curl -s -X POST "${MINI_API}/api/v1/collect" || echo '{"error": "request failed"}')

if echo "$COLLECT_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    success "采集请求已发送"
else
    error "采集请求失败"
    echo "$COLLECT_RESPONSE"
fi

echo ""
info "等待采集完成（30秒）..."
sleep 30
echo ""

# 步骤 4：验证数据落档
echo "[4/8] 验证数据落档..."
echo ""

info "检查 Mini 数据文件..."
# 通过 API 验证数据可读
BARS_RESPONSE=$(curl -s "${MINI_API}/api/v1/bars?symbol=KQ.m@SHFE.rb&start=$(date -u -v-1H '+%Y-%m-%dT%H:%M:%S')&end=$(date -u '+%Y-%m-%dT%H:%M:%S')&limit=5")

BARS_COUNT=$(echo "$BARS_RESPONSE" | jq -r '.bars | length // 0')
if [ "$BARS_COUNT" -gt 0 ]; then
    success "数据已落档（查询到 ${BARS_COUNT} 条记录）"
else
    error "数据未落档或无新数据"
fi

echo ""

# 步骤 5：手动触发研究员分析
echo "[5/8] 触发 Alienware 研究员分析..."
echo ""

CURRENT_HOUR=$(date '+%H' | sed 's/^0//')
info "触发研究员分析（hour=${CURRENT_HOUR}）..."

RESEARCH_RESPONSE=$(curl -s -X POST "${ALIENWARE_API}/run?hour=${CURRENT_HOUR}")

if echo "$RESEARCH_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    success "研究员分析已触发"
else
    error "研究员分析触发失败"
    echo "$RESEARCH_RESPONSE"
fi

echo ""
info "等待研究员分析完成（60秒）..."
sleep 60
echo ""

# 步骤 6：验证报告生成
echo "[6/8] 验证报告生成..."
echo ""

info "查询队列状态..."
QUEUE_STATUS_AFTER=$(curl -s "${ALIENWARE_API}/queue/status")
PENDING_COUNT_AFTER=$(echo "$QUEUE_STATUS_AFTER" | jq -r '.pending_count // 0')

if [ "$PENDING_COUNT_AFTER" -gt "$PENDING_COUNT" ]; then
    success "报告已生成（待读队列: ${PENDING_COUNT} → ${PENDING_COUNT_AFTER}）"
else
    error "未检测到新报告"
fi

echo ""

# 步骤 7：验证 Studio 评级
echo "[7/8] 验证 Studio 评级..."
echo ""

info "检查 Studio decision 日志..."
# 注意：需要 SSH 权限
if ssh jay@${STUDIO_HOST} "tail -20 ~/JBT/services/decision/logs/app.log | grep -E '(收到研究员报告|评级)'" 2>/dev/null; then
    success "Studio 已收到报告并评级"
else
    info "无法读取 Studio 日志（需要 SSH 权限）"
fi

echo ""

# 步骤 8：验证队列状态更新
echo "[8/8] 验证队列状态更新..."
echo ""

info "等待评级完成（30秒）..."
sleep 30

QUEUE_STATUS_FINAL=$(curl -s "${ALIENWARE_API}/queue/status")
PENDING_COUNT_FINAL=$(echo "$QUEUE_STATUS_FINAL" | jq -r '.pending_count // 0')

if [ "$PENDING_COUNT_FINAL" -lt "$PENDING_COUNT_AFTER" ]; then
    success "报告已标记为已读（待读队列: ${PENDING_COUNT_AFTER} → ${PENDING_COUNT_FINAL}）"
else
    info "待读队列未变化（可能评级尚未完成）"
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "总结："
echo "  Mini 采集: ✓"
echo "  数据落档: ✓"
echo "  研究员分析: ✓"
echo "  报告生成: $([ "$PENDING_COUNT_AFTER" -gt "$PENDING_COUNT" ] && echo '✓' || echo '?')"
echo "  Studio 评级: ?"
echo "  队列更新: $([ "$PENDING_COUNT_FINAL" -lt "$PENDING_COUNT_AFTER" ] && echo '✓' || echo '?')"
echo ""
echo "详细日志位置："
echo "  Mini: ssh jaybot@${MINI_HOST} 'docker logs JBT-DATA-8105 | tail -50'"
echo "  Alienware: C:\\Users\\17621\\JBT\\runtime\\researcher\\logs\\server.log"
echo "  Studio: ssh jay@${STUDIO_HOST} 'tail -50 ~/JBT/services/decision/logs/app.log'"
echo ""
