#!/bin/bash
# jbt_rsync_rollback.sh — JBT rsync 快照回滚脚本
#
# 功能：从 deploy-manifest.jsonl 读取历史部署记录，将指定快照恢复到远端
# 执行位置：MacBook（控制端）
#
# 用法：
#   ./jbt_rsync_rollback.sh --service <服务名> [--list] [--pick <N>]
#
# 示例：
#   ./jbt_rsync_rollback.sh --service data --list        # 列出可用快照
#   ./jbt_rsync_rollback.sh --service data               # 回滚到最近一次成功部署
#   ./jbt_rsync_rollback.sh --service data --pick 2      # 回滚到倒数第 2 次成功部署

set -euo pipefail

MANIFEST_FILE="${HOME}/jbt-governance/deploy-manifest.jsonl"

# ============================================================
# 设备配置（与 deploy 保持一致）
# ============================================================
MINI_HOST="jaybot@192.168.31.74"
MINI_IP="192.168.31.74"

STUDIO_HOST="jaybot@192.168.31.142"
STUDIO_IP="192.168.31.142"

AIR_HOST="jayshao@192.168.31.245"
AIR_IP="192.168.31.245"

# ============================================================
# 服务配置查询函数（兼容 bash 3.2，不使用 declare -A）
# 格式: HOST|IP|PORT|HEALTH_PATH|CONTAINER|REMOTE_PATH
# ============================================================
get_service_config() {
    local svc="$1"
    case "$svc" in
        data)      echo "${MINI_HOST}|${MINI_IP}|8105|/health|JBT-DATA-8105|~/JBT/services/data" ;;
        decision)  echo "${STUDIO_HOST}|${STUDIO_IP}|8104|/health|JBT-DECISION-8104|~/JBT/services/decision" ;;
        dashboard) echo "${STUDIO_HOST}|${STUDIO_IP}|8106|/health|JBT-DASHBOARD-8106|~/JBT/services/dashboard" ;;
        backtest)  echo "${AIR_HOST}|${AIR_IP}|8103|/api/health|JBT-BACKTEST-8103|~/JBT/services/backtest" ;;
        *) return 1 ;;
    esac
}

# ============================================================
# 解析参数
# ============================================================
SERVICE=""
LIST_ONLY=false
PICK_N=1

while [[ $# -gt 0 ]]; do
    case "$1" in
        --service) SERVICE="$2"; shift 2 ;;
        --list)    LIST_ONLY=true; shift ;;
        --pick)    PICK_N="$2"; shift 2 ;;
        -h|--help)
            sed -n '3,15p' "$0"
            exit 0
            ;;
        *) echo "[ERROR] 未知参数: $1"; exit 1 ;;
    esac
done

if [[ -z "$SERVICE" ]]; then
    echo "[ERROR] 必须指定 --service"
    echo "用法: $0 --service <data|decision|dashboard|backtest>"
    exit 1
fi

# 验证服务名合法性
get_service_config "$SERVICE" > /dev/null 2>&1 || { echo "[ERROR] 未知服务: ${SERVICE}（合法值：data|decision|dashboard|backtest）"; exit 1; }

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo "[$(date '+%H:%M:%S')] ✓ $*"; }
warn() { echo "[$(date '+%H:%M:%S')] ⚠ $*"; }
err()  { echo "[$(date '+%H:%M:%S')] ✗ $*" >&2; }

# ============================================================
# 检查清单文件
# ============================================================
if [[ ! -f "$MANIFEST_FILE" ]]; then
    err "清单文件不存在: ${MANIFEST_FILE}"
    err "请先运行 jbt_rsync_deploy.sh 创建部署记录"
    exit 1
fi

# 过滤该服务的成功记录（status=success）
ENTRIES=$(grep "\"service\":\"${SERVICE}\"" "$MANIFEST_FILE" | grep '"status":"success"' | grep '"dry_run":false' || true)

if [[ -z "$ENTRIES" ]]; then
    err "未找到服务 [${SERVICE}] 的成功部署记录"
    err "请检查清单: ${MANIFEST_FILE}"
    exit 1
fi

# 按时间倒序排列
SORTED=$(echo "$ENTRIES" | sort -t'"' -k4 -r)
TOTAL=$(echo "$SORTED" | wc -l | tr -d ' ')

# ============================================================
# 列出快照
# ============================================================
list_snapshots() {
    echo ""
    echo "服务 [${SERVICE}] 可用快照（共 ${TOTAL} 条，最新在前）："
    echo "──────────────────────────────────────────────────────"
    local idx=1
    while IFS= read -r entry; do
        local ts snapshot host
        ts=$(echo "$entry" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ts'])" 2>/dev/null || echo "$entry" | grep -o '"ts":"[^"]*"' | cut -d'"' -f4)
        snapshot=$(echo "$entry" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['snapshot'])" 2>/dev/null || echo "$entry" | grep -o '"snapshot":"[^"]*"' | cut -d'"' -f4)
        host=$(echo "$entry" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['host'])" 2>/dev/null || echo "$entry" | grep -o '"host":"[^"]*"' | cut -d'"' -f4)
        echo "  [${idx}] ${ts}  ${host}:${snapshot}"
        idx=$((idx + 1))
    done <<< "$SORTED"
    echo "──────────────────────────────────────────────────────"
    echo ""
}

list_snapshots

if [[ "$LIST_ONLY" == "true" ]]; then
    exit 0
fi

# ============================================================
# 选择快照
# ============================================================
if [[ $PICK_N -lt 1 || $PICK_N -gt $TOTAL ]]; then
    err "无效的序号 --pick ${PICK_N}，有效范围: 1~${TOTAL}"
    exit 1
fi

SELECTED=$(echo "$SORTED" | sed -n "${PICK_N}p")
SNAPSHOT=$(echo "$SELECTED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['snapshot'])" 2>/dev/null || echo "$SELECTED" | grep -o '"snapshot":"[^"]*"' | cut -d'"' -f4)
HOST=$(echo "$SELECTED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['host'])" 2>/dev/null || echo "$SELECTED" | grep -o '"host":"[^"]*"' | cut -d'"' -f4)
TS=$(echo "$SELECTED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ts'])" 2>/dev/null || echo "$SELECTED" | grep -o '"ts":"[^"]*"' | cut -d'"' -f4)

local config
config=$(get_service_config "$SERVICE")
IFS='|' read -r host ip port health_path container remote_path <<< "$config"

echo ""
warn "即将回滚服务 [${SERVICE}]"
warn "  快照时间: ${TS}"
warn "  快照路径: ${HOST}:${SNAPSHOT}"
warn "  回滚目标: ${host}:${remote_path}"
echo ""
read -rp "确认回滚？[y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    log "已取消"
    exit 0
fi

# ============================================================
# 执行回滚
# ============================================================
log "开始回滚..."

# 检查快照是否存在
if ! ssh "${host}" "test -d ${SNAPSHOT}"; then
    err "快照目录不存在: ${host}:${SNAPSHOT}"
    err "快照可能已过期或被删除"
    exit 1
fi

# rsync 快照 → 目标路径
log "rsync 快照 → 目标..."
ssh "${host}" "rsync -a --delete ${SNAPSHOT}/ ${remote_path}/"
ok "rsync 完成"

# 重启容器
log "重启容器: ${container}..."
if ssh "${host}" "docker restart ${container} 2>&1"; then
    ok "容器重启成功"
    sleep 5
else
    warn "docker restart 失败，请手动检查"
    sleep 3
fi

# 健康检查
health_url="http://${ip}:${port}${health_path}"
log "健康检查: ${health_url}"
attempt=0
while [[ $attempt -lt 6 ]]; do
    attempt=$((attempt + 1))
    if curl -sf --max-time 5 "${health_url}" > /dev/null 2>&1; then
        ok "健康检查通过 (尝试 ${attempt}/6)"
        break
    fi
    warn "健康检查失败 (${attempt}/6)，5s 后重试..."
    sleep 5
    if [[ $attempt -eq 6 ]]; then
        err "健康检查超时，请手动检查服务"
        exit 1
    fi
done

# 写回滚记录
mkdir -p "$(dirname "$MANIFEST_FILE")"
printf '{"ts":"%s","service":"%s","status":"rollback","host":"%s","snapshot":"%s","dry_run":false}\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$SERVICE" "$HOST" "$SNAPSHOT" >> "$MANIFEST_FILE"

ok "回滚完成！服务 [${SERVICE}] 已恢复到 ${TS}"
