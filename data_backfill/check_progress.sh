#!/bin/bash
# 监控回补进度

echo "========================================"
echo "期货分钟K线回补进度监控"
echo "========================================"

# 检查进程状态
if ps aux | grep -v grep | grep batch_backfill.sh > /dev/null; then
    echo "✅ 批量回补任务正在运行中"
else
    echo "❌ 批量回补任务未运行"
fi

echo ""
echo "--- 最新日志 (最后20行) ---"
tail -20 /Users/jaybot/JBT/data_backfill/logs/batch_run.log 2>/dev/null || echo "日志文件不存在"

echo ""
echo "--- 已完成的品种数量 ---"
grep -c "✅.*完成" /Users/jaybot/JBT/data_backfill/logs/batch_run.log 2>/dev/null || echo "0"

echo ""
echo "--- 回补数据统计 ---"
OUTPUT_DIR="/Users/jaybot/JBT/data_backfill/output"
if [ -d "$OUTPUT_DIR" ]; then
    SYMBOL_COUNT=$(ls -d "$OUTPUT_DIR"/KQ_m_* 2>/dev/null | wc -l)
    echo "已生成数据的品种数: $SYMBOL_COUNT / 35"

    echo ""
    echo "各品种数据文件数:"
    for dir in "$OUTPUT_DIR"/KQ_m_*; do
        if [ -d "$dir" ]; then
            symbol=$(basename "$dir")
            file_count=$(find "$dir" -name "*.parquet" | wc -l)
            echo "  $symbol: $file_count 个文件"
        fi
    done | tail -10
else
    echo "输出目录不存在"
fi

echo ""
echo "========================================"
echo "提示: 运行 'tail -f /Users/jaybot/JBT/data_backfill/logs/batch_run.log' 查看实时日志"
echo "========================================"
