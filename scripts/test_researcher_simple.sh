#!/bin/bash
# 简化版研究员测试脚本
# 跳过 Mini 采集触发（定时自动执行），直接测试 Alienware → Studio 流程

set -e

echo "=========================================="
echo "研究员数据流简化测试"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

ALIENWARE_API="http://192.168.31.223:8199"
STUDIO_API="http://192.168.31.142:8104"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }
info() { echo -e "${YELLOW}→${NC} $1"; }

# 步骤 1：检查服务健康
echo "[1/5] 检查服务健康..."
info "检查 Alienware 研究员服务..."
if curl -sf "${ALIENWARE_API}/health" > /dev/null; then
    success "Alienware 研究员服务正常"
else
    error "Alienware 研究员服务异常"
    exit 1
fi

info "检查 Studio decision 服务..."
if curl -sf "${STUDIO_API}/health" > /dev/null; then
    success "Studio decision 服务正常"
else
    error "Studio decision 服务异常"
    exit 1
fi
echo ""

# 步骤 2：查看队列状态（触发前）
echo "[2/5] 查看队列状态（触发前）..."
QUEUE_BEFORE=$(curl -s "${ALIENWARE_API}/queue/status")
echo "$QUEUE_BEFORE" | jq '.'
PENDING_BEFORE=$(echo "$QUEUE_BEFORE" | jq -r '.pending')
echo ""

# 步骤 3：触发研究员分析
echo "[3/5] 触发研究员分析..."
info "发送触发请求到 Alienware..."
TRIGGER_RESULT=$(curl -s -X POST "${ALIENWARE_API}/run" \
    -H "Content-Type: application/json" \
    -d '{"hour": 15}')

if echo "$TRIGGER_RESULT" | jq -e '.status == "success"' > /dev/null 2>&1; then
    success "研究员触发成功"
    echo "$TRIGGER_RESULT" | jq '.'
else
    error "研究员触发失败"
    echo "$TRIGGER_RESULT"
    exit 1
fi
echo ""

# 步骤 4：等待报告生成并入队
echo "[4/5] 等待报告生成（30秒）..."
sleep 30

QUEUE_AFTER=$(curl -s "${ALIENWARE_API}/queue/status")
echo "$QUEUE_AFTER" | jq '.'
PENDING_AFTER=$(echo "$QUEUE_AFTER" | jq -r '.pending')

if [ "$PENDING_AFTER" -gt "$PENDING_BEFORE" ]; then
    success "新报告已入队（待读：$PENDING_AFTER）"
else
    error "未检测到新报告入队"
fi
echo ""

# 步骤 5：触发 Studio 评级
echo "[5/5] 触发 Studio 评级..."
PENDING_REPORTS=$(curl -s "${ALIENWARE_API}/queue/pending")
REPORT_COUNT=$(echo "$PENDING_REPORTS" | jq '. | length')

if [ "$REPORT_COUNT" -eq 0 ]; then
    info "待读队列为空，跳过评级测试"
else
    info "待读队列有 $REPORT_COUNT 个报告，触发评级..."
    FIRST_REPORT=$(echo "$PENDING_REPORTS" | jq -r '.[0].report_path')

    info "评级报告: $FIRST_REPORT"
    EVAL_RESULT=$(curl -s -X POST "${STUDIO_API}/api/researcher/evaluate" \
        -H "Content-Type: application/json" \
        -d "{\"report_path\": \"$FIRST_REPORT\"}")

    if echo "$EVAL_RESULT" | jq -e '.status == "success"' > /dev/null 2>&1; then
        success "评级完成"
        echo "$EVAL_RESULT" | jq '.'

        # 检查是否已标记为已读
        sleep 2
        QUEUE_FINAL=$(curl -s "${ALIENWARE_API}/queue/status")
        COMPLETED=$(echo "$QUEUE_FINAL" | jq -r '.completed')
        success "已完成报告数：$COMPLETED"
    else
        error "评级失败"
        echo "$EVAL_RESULT"
    fi
fi
echo ""

echo "=========================================="
echo "测试完成"
echo "=========================================="
