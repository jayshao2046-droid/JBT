#!/bin/bash
# jbt_rsync_deploy.sh — JBT 无 git 依赖 rsync 发布脚本
#
# 功能：通过 rsync 将本地服务代码发布到指定远端设备，自动做快照、重启、健康检查
# 执行位置：MacBook（控制端）
#
# 用法：
#   ./jbt_rsync_deploy.sh --service <服务名> [--target <目标>] [--dry-run] [--skip-restart] [--skip-health]
#
# 服务名：data | decision | dashboard | backtest | all
# 目标：  mini | studio | air | all（默认按服务自动选择）
#
# 示例：
#   ./jbt_rsync_deploy.sh --service data
#   ./jbt_rsync_deploy.sh --service decision --target studio
#   ./jbt_rsync_deploy.sh --service all
#   ./jbt_rsync_deploy.sh --service backtest --dry-run

set -euo pipefail

# ============================================================
# 设备配置（内网优先）
# ============================================================
MINI_HOST="jaybot@192.168.31.74"
MINI_PATH="~/JBT/services"
MINI_IP="192.168.31.74"

STUDIO_HOST="jaybot@192.168.31.142"
STUDIO_PATH="~/JBT/services"
STUDIO_IP="192.168.31.142"

AIR_HOST="jayshao@192.168.31.245"
AIR_PATH="~/JBT/services"
AIR_IP="192.168.31.245"

# ============================================================
# 服务配置：service -> (设备, 容器名, 健康检查URL)
# ============================================================
# 格式: HOST|PATH|IP|PORT|HEALTH_PATH|CONTAINER
declare -A SERVICE_CONFIG
SERVICE_CONFIG["data"]="${MINI_HOST}|${MINI_PATH}|${MINI_IP}|8105|/health|JBT-DATA-8105"
SERVICE_CONFIG["decision"]="${STUDIO_HOST}|${STUDIO_PATH}|${STUDIO_IP}|8104|/health|JBT-DECISION-8104"
SERVICE_CONFIG["dashboard"]="${STUDIO_HOST}|${STUDIO_PATH}|${STUDIO_IP}|8106|/health|JBT-DASHBOARD-8106"
SERVICE_CONFIG["backtest"]="${AIR_HOST}|${AIR_PATH}|${AIR_IP}|8103|/api/health|JBT-BACKTEST-8103"

# 清单文件路径
MANIFEST_FILE="${HOME}/jbt-governance/deploy-manifest.jsonl"
SNAPSHOT_BASE="~/jbt-governance/snapshots"

# ============================================================
# rsync 排除列表
# ============================================================
RSYNC_EXCLUDES=(
    "--exclude=.git"
    "--exclude=__pycache__"
    "--exclude=*.pyc"
    "--exclude=*.pyo"
    "--exclude=runtime/"
    "--exclude=logs/"
    "--exclude=.env"
    "--exclude=*.db"
    "--exclude=*.sqlite"
    "--exclude=node_modules/"
    "--exclude=.next/"
    "--exclude=dist/"
    "--exclude=build/"
)

# ============================================================
# 解析参数
# ============================================================
SERVICE=""
TARGET=""
DRY_RUN=false
SKIP_RESTART=false
SKIP_HEALTH=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --service) SERVICE="$2"; shift 2 ;;
        --target)  TARGET="$2";  shift 2 ;;
        --dry-run)     DRY_RUN=true;     shift ;;
        --skip-restart) SKIP_RESTART=true; shift ;;
        --skip-health) SKIP_HEALTH=true;  shift ;;
        -h|--help)
            sed -n '3,20p' "$0"
            exit 0
            ;;
        *) echo "[ERROR] 未知参数: $1"; exit 1 ;;
    esac
done

if [[ -z "$SERVICE" ]]; then
    echo "[ERROR] 必须指定 --service"
    echo "用法: $0 --service <data|decision|dashboard|backtest|all>"
    exit 1
fi

# ============================================================
# 工具函数
# ============================================================
log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo "[$(date '+%H:%M:%S')] ✓ $*"; }
warn() { echo "[$(date '+%H:%M:%S')] ⚠ $*"; }
err()  { echo "[$(date '+%H:%M:%S')] ✗ $*" >&2; }

# 写入部署清单
write_manifest() {
    local svc="$1" status="$2" snapshot_dir="$3" host="$4"
    mkdir -p "$(dirname "$MANIFEST_FILE")"
    local ts
    ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    printf '{"ts":"%s","service":"%s","status":"%s","host":"%s","snapshot":"%s","dry_run":%s}\n' \
        "$ts" "$svc" "$status" "$host" "$snapshot_dir" "$DRY_RUN" >> "$MANIFEST_FILE"
}

# 发布单个服务
deploy_service() {
    local svc="$1"

    if [[ -z "${SERVICE_CONFIG[$svc]+_}" ]]; then
        err "未知服务: $svc"
        return 1
    fi

    IFS='|' read -r host remote_base ip port health_path container <<< "${SERVICE_CONFIG[$svc]}"
    local local_src="${PWD}/services/${svc}/"
    local remote_dest="${remote_base}/${svc}/"
    local ts
    ts=$(date '+%Y%m%d-%H%M%S')
    local snapshot_dir="${SNAPSHOT_BASE}/${svc}-${ts}"

    log "========================================"
    log "发布服务: ${svc}"
    log "  源:    ${local_src}"
    log "  目标:  ${host}:${remote_dest}"
    log "  快照:  ${snapshot_dir}"
    log "========================================"

    # 检查本地源目录
    if [[ ! -d "$local_src" ]]; then
        err "本地目录不存在: ${local_src}"
        return 1
    fi

    # 构造 rsync 命令
    local rsync_cmd=(
        rsync -avz
        --delete
        "${RSYNC_EXCLUDES[@]}"
    )

    if [[ "$DRY_RUN" == "true" ]]; then
        rsync_cmd+=(--dry-run)
        log "[DRY-RUN] 模拟同步，不实际修改文件"
    else
        # 在远端创建快照目录并备份
        log "在远端创建快照..."
        ssh "${host}" "mkdir -p ${snapshot_dir} && rsync -a --ignore-missing-args ${remote_dest} ${snapshot_dir}/ 2>/dev/null || true"
        rsync_cmd+=("--backup-dir=${snapshot_dir}")
    fi

    rsync_cmd+=("${local_src}" "${host}:${remote_dest}")

    log "开始 rsync..."
    if "${rsync_cmd[@]}"; then
        ok "rsync 完成"
    else
        err "rsync 失败"
        write_manifest "$svc" "rsync_failed" "$snapshot_dir" "$host"
        return 1
    fi

    [[ "$DRY_RUN" == "true" ]] && { ok "dry-run 完成，跳过重启与健康检查"; write_manifest "$svc" "dry_run" "$snapshot_dir" "$host"; return 0; }

    # 重启容器
    if [[ "$SKIP_RESTART" != "true" ]]; then
        log "重启容器: ${container}..."
        if ssh "${host}" "docker restart ${container} 2>&1"; then
            ok "容器重启成功"
            sleep 5
        else
            warn "docker restart 失败，尝试通过 systemctl/nohup..."
            # 对于非 docker 部署的服务（如 Alienware），此处 fallback
            ssh "${host}" "cd ~/JBT/services/${svc} && pkill -f 'uvicorn.*${svc}' 2>/dev/null || true; sleep 2; nohup python -m uvicorn src.api.app:app --host 0.0.0.0 --port ${port} > logs/${svc}.log 2>&1 &" || warn "重启命令执行失败，请手动检查"
            sleep 8
        fi
    else
        warn "--skip-restart: 跳过容器重启"
    fi

    # 健康检查
    if [[ "$SKIP_HEALTH" != "true" ]]; then
        local health_url="http://${ip}:${port}${health_path}"
        log "健康检查: ${health_url}"
        local attempt=0
        local max_attempts=6
        while [[ $attempt -lt $max_attempts ]]; do
            attempt=$((attempt + 1))
            if curl -sf --max-time 5 "${health_url}" > /dev/null 2>&1; then
                ok "健康检查通过 (尝试 ${attempt}/${max_attempts})"
                write_manifest "$svc" "success" "$snapshot_dir" "$host"
                return 0
            fi
            warn "健康检查失败 (${attempt}/${max_attempts})，5s 后重试..."
            sleep 5
        done
        err "健康检查超时，服务可能未正常启动"
        err "快照路径: ${host}:${snapshot_dir}"
        err "可使用 jbt_rsync_rollback.sh --service ${svc} 回滚"
        write_manifest "$svc" "health_failed" "$snapshot_dir" "$host"
        return 1
    else
        warn "--skip-health: 跳过健康检查"
        write_manifest "$svc" "success_no_health" "$snapshot_dir" "$host"
    fi
}

# ============================================================
# 主流程
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

log "JBT rsync 发布 | 仓库根: ${REPO_ROOT}"
log "服务: ${SERVICE} | DRY_RUN: ${DRY_RUN}"

FAILED_SERVICES=()

if [[ "$SERVICE" == "all" ]]; then
    SERVICES=("data" "decision" "dashboard" "backtest")
else
    SERVICES=("$SERVICE")
fi

for svc in "${SERVICES[@]}"; do
    echo ""
    if ! deploy_service "$svc"; then
        FAILED_SERVICES+=("$svc")
    fi
done

echo ""
log "========================================"
if [[ ${#FAILED_SERVICES[@]} -eq 0 ]]; then
    ok "全部发布完成！"
    [[ -f "$MANIFEST_FILE" ]] && log "清单已更新: ${MANIFEST_FILE}"
else
    err "以下服务发布失败: ${FAILED_SERVICES[*]}"
    log "清单路径: ${MANIFEST_FILE}"
    log "回滚命令: governance/scripts/jbt_rsync_rollback.sh --service <服务名>"
    exit 1
fi
log "========================================"
