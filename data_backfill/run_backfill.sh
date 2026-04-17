#!/bin/bash
# 一键回补所有35个期货品种的缺失数据
# 使用方法: ./run_backfill.sh

set -e

# 配置参数
START_DATE="2026-04-10"
END_DATE="2026-04-17"
BACKFILL_DIR="/Users/jaybot/JBT/data_backfill"
LOG_FILE="$BACKFILL_DIR/logs/run_backfill_$(date +%Y%m%d_%H%M%S).log"

# 天勤账号（需要用户提供）
read -p "请输入天勤账号: " TQ_ACCOUNT
read -sp "请输入天勤密码: " TQ_PASSWORD
echo ""

echo "========================================" | tee -a "$LOG_FILE"
echo "期货分钟K线数据回补任务" | tee -a "$LOG_FILE"
echo "开始时间: $(date)" | tee -a "$LOG_FILE"
echo "回补时间段: $START_DATE ~ $END_DATE" | tee -a "$LOG_FILE"
echo "回补品种: 35个连续合约" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 步骤1: 回补数据
echo "" | tee -a "$LOG_FILE"
echo "[步骤 1/3] 开始回补数据..." | tee -a "$LOG_FILE"
cd "$BACKFILL_DIR/scripts"

python3 backfill_futures_minute.py \
  --start "$START_DATE" \
  --end "$END_DATE" \
  --account "$TQ_ACCOUNT" \
  --password "$TQ_PASSWORD" \
  2>&1 | tee -a "$LOG_FILE"

if [ $? -ne 0 ]; then
    echo "❌ 回补失败，请查看日志: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 步骤2: 验证数据
echo "" | tee -a "$LOG_FILE"
echo "[步骤 2/3] 验证回补数据..." | tee -a "$LOG_FILE"

python3 verify_and_import.py \
  --verify \
  --start "$START_DATE" \
  --end "$END_DATE" \
  2>&1 | tee -a "$LOG_FILE"

if [ $? -ne 0 ]; then
    echo "⚠️  验证失败，但可以继续导入。请检查日志确认问题。" | tee -a "$LOG_FILE"
    read -p "是否继续导入? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo "已取消导入" | tee -a "$LOG_FILE"
        exit 1
    fi
fi

# 步骤3: 导入数据并清除临时文件
echo "" | tee -a "$LOG_FILE"
echo "[步骤 3/3] 导入数据到正式目录..." | tee -a "$LOG_FILE"

python3 verify_and_import.py \
  --import \
  --clean \
  2>&1 | tee -a "$LOG_FILE"

if [ $? -ne 0 ]; then
    echo "❌ 导入失败，请查看日志: $LOG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 完成
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "✅ 回补任务完成！" | tee -a "$LOG_FILE"
echo "结束时间: $(date)" | tee -a "$LOG_FILE"
echo "日志文件: $LOG_FILE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 显示数据统计
echo "" | tee -a "$LOG_FILE"
echo "数据统计:" | tee -a "$LOG_FILE"
du -sh /Users/jaybot/JBT/data/futures_minute/1m/ | tee -a "$LOG_FILE"
find /Users/jaybot/JBT/data/futures_minute/1m/ -name "*.parquet" | wc -l | xargs echo "Parquet 文件数:" | tee -a "$LOG_FILE"
