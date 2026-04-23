#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# disable_legacy_data.sh
# 在 Mini (jaybot@192.168.31.156) 上执行，用于：
#   1. 停止旧 J_BotQuant 的所有数据采集进程
#   2. 移除 launchctl 守护
#   3. 禁用 crontab 中的旧采集任务
#   4. 重命名旧目录以防误启
#
# 用法：ssh jaybot@192.168.31.156 'bash ~/JBT/services/data/scripts/disable_legacy.sh'
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

LEGACY_DIR="$HOME/J_BotQuant"
BACKUP_SUFFIX=".disabled-$(date +%Y%m%d%H%M%S)"

echo "=========================================="
echo "  JBT 旧数据端切除脚本"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# ─── 1. 杀掉所有旧 J_BotQuant Python 进程 ───
echo ""
echo "[1/5] 停止旧 J_BotQuant 进程..."
OLD_PIDS=$(pgrep -f "J_BotQuant" 2>/dev/null || true)
if [ -n "$OLD_PIDS" ]; then
    echo "  找到旧进程 PIDs: $OLD_PIDS"
    for pid in $OLD_PIDS; do
        echo "  -> kill $pid ($(ps -p "$pid" -o command= 2>/dev/null || echo 'unknown'))"
        kill "$pid" 2>/dev/null || true
    done
    sleep 3
    # 强杀残留
    REMAINING=$(pgrep -f "J_BotQuant" 2>/dev/null || true)
    if [ -n "$REMAINING" ]; then
        echo "  强杀残留进程: $REMAINING"
        kill -9 $REMAINING 2>/dev/null || true
    fi
    echo "  ✅ 旧进程已全部停止"
else
    echo "  ✅ 无旧进程在运行"
fi

# ─── 2. 卸载 launchctl 守护 ───
echo ""
echo "[2/5] 卸载 launchctl 守护..."
for plist in ~/Library/LaunchAgents/com.botquant.*.plist; do
    if [ -f "$plist" ]; then
        label=$(basename "$plist" .plist)
        echo "  -> unload $label"
        launchctl unload -w "$plist" 2>/dev/null || true
        mv "$plist" "${plist}${BACKUP_SUFFIX}"
        echo "  -> 已备份为 ${plist}${BACKUP_SUFFIX}"
    fi
done
echo "  ✅ launchctl 清理完成"

# ─── 3. 清理 crontab ───
echo ""
echo "[3/5] 清理 crontab 中的旧任务..."
CRON_BACKUP="$HOME/crontab_backup${BACKUP_SUFFIX}.txt"
crontab -l > "$CRON_BACKUP" 2>/dev/null || true
if [ -s "$CRON_BACKUP" ]; then
    echo "  旧 crontab 备份到: $CRON_BACKUP"
    # 注释掉所有包含 J_BotQuant 的行
    crontab -l 2>/dev/null | sed 's|^\([^#].*J_BotQuant.*\)|# DISABLED_JBT_CUTOVER \1|g' | crontab -
    echo "  ✅ 已注释所有 J_BotQuant crontab 条目"
else
    echo "  ✅ 无 crontab 任务"
fi

# ─── 4. 禁用旧 venv（重命名） ───
echo ""
echo "[4/5] 禁用旧 J_BotQuant 虚拟环境..."
if [ -d "$LEGACY_DIR/.venv" ]; then
    mv "$LEGACY_DIR/.venv" "$LEGACY_DIR/.venv${BACKUP_SUFFIX}"
    echo "  ✅ .venv 已重命名为 .venv${BACKUP_SUFFIX}"
else
    echo "  ✅ 旧 .venv 不存在或已禁用"
fi

# ─── 5. 在旧目录下创建锁文件 ───
echo ""
echo "[5/5] 创建迁移锁文件..."
cat > "$LEGACY_DIR/.JBT_MIGRATED" <<EOF
此目录的数据采集服务已于 $(date '+%Y-%m-%d %H:%M:%S') 迁移到 JBT。
新数据服务：~/JBT/services/data/ (Docker: JBT-DATA-8105)
新数据目录：~/jbt-data/

禁止在此目录重新启动任何采集进程。
EOF
echo "  ✅ 锁文件已创建: $LEGACY_DIR/.JBT_MIGRATED"

echo ""
echo "=========================================="
echo "  ✅ 旧数据端切除完成"
echo "  旧进程: 已停止"
echo "  launchctl: 已卸载"
echo "  crontab: 已注释"
echo "  .venv: 已禁用"
echo "  锁文件: 已创建"
echo ""
echo "  下一步：部署 JBT Docker 容器"
echo "  docker compose -f docker-compose.dev.yml up -d jbt-data"
echo "=========================================="
