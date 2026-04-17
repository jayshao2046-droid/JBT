#!/bin/bash
# 分批回补35个期货品种（每次1个品种）
set -e

START_DATE="2026-04-09"
END_DATE="2026-04-17"
ACCOUNT="17621181300"
PASSWORD="Jay.486858"
SCRIPT_DIR="/Users/jaybot/JBT/data_backfill/scripts"
LOG_DIR="/Users/jaybot/JBT/data_backfill/logs"

# 35个品种列表
SYMBOLS=(
    "KQ.m@CZCE.CF" "KQ.m@CZCE.FG" "KQ.m@CZCE.MA" "KQ.m@CZCE.OI" "KQ.m@CZCE.PF"
    "KQ.m@CZCE.RM" "KQ.m@CZCE.SA" "KQ.m@CZCE.SR" "KQ.m@CZCE.TA" "KQ.m@CZCE.UR"
    "KQ.m@DCE.a" "KQ.m@DCE.c" "KQ.m@DCE.eb" "KQ.m@DCE.i" "KQ.m@DCE.j"
    "KQ.m@DCE.jd" "KQ.m@DCE.jm" "KQ.m@DCE.l" "KQ.m@DCE.lh" "KQ.m@DCE.m"
    "KQ.m@DCE.p" "KQ.m@DCE.pg" "KQ.m@DCE.pp" "KQ.m@DCE.v" "KQ.m@DCE.y"
    "KQ.m@SHFE.ag" "KQ.m@SHFE.al" "KQ.m@SHFE.au" "KQ.m@SHFE.cu" "KQ.m@SHFE.hc"
    "KQ.m@SHFE.rb" "KQ.m@SHFE.ru" "KQ.m@SHFE.sp" "KQ.m@SHFE.ss" "KQ.m@SHFE.zn"
)

echo "========================================"
echo "期货分钟K线批量回补任务"
echo "开始时间: $(date)"
echo "回补时间段: $START_DATE ~ $END_DATE"
echo "品种数量: ${#SYMBOLS[@]}"
echo "========================================"

SUCCESS_COUNT=0
FAILED_SYMBOLS=()

for i in "${!SYMBOLS[@]}"; do
    SYMBOL="${SYMBOLS[$i]}"
    INDEX=$((i + 1))

    echo ""
    echo "[$INDEX/${#SYMBOLS[@]}] 回补 $SYMBOL ..."

    cd "$SCRIPT_DIR"
    python3 backfill_futures_minute.py \
        --start "$START_DATE" \
        --end "$END_DATE" \
        --symbols "$SYMBOL" \
        --account "$ACCOUNT" \
        --password "$PASSWORD" \
        2>&1 | tee -a "$LOG_DIR/batch_backfill.log"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        echo "✅ $SYMBOL 完成"
    else
        FAILED_SYMBOLS+=("$SYMBOL")
        echo "❌ $SYMBOL 失败"
    fi

    # 每个品种之间暂停2秒，避免API限流
    sleep 2
done

echo ""
echo "========================================"
echo "回补任务完成"
echo "结束时间: $(date)"
echo "成功: $SUCCESS_COUNT/${#SYMBOLS[@]}"
if [ ${#FAILED_SYMBOLS[@]} -gt 0 ]; then
    echo "失败的品种: ${FAILED_SYMBOLS[*]}"
fi
echo "========================================"
