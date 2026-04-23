#!/bin/bash
# jbt_rsync_deploy.sh — JBT 无 git 依赖 rsync 发布脚本
#
# 功能：通过 rsync 将本地服务代码发布到指定远端设备，自动做快照、重启、健康检查
# 执行位置：MacBook（控制端）
#
# 用法：
#   ./jbt_rsync_deploy.sh --service <服务名> [--target <目标>] [--dry-run] [--skip-restart] [--skip-health]
#
# 服务名：data | decision | dashboard | backtest | sim-trading | researcher | all
# 目标：  mini | studio | air | alienware
#
# 示例：
#   ./jbt_rsync_deploy.sh --service data
#   ./jbt_rsync_deploy.sh --service sim-trading
#   ./jbt_rsync_deploy.sh --service researcher
#   ./jbt_rsync_deploy.sh --service backtest --target studio
#   ./jbt_rsync_deploy.sh --service all
#   ./jbt_rsync_deploy.sh --service sim-trading --dry-run

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

ALIENWARE_HOST="17621@192.168.31.187"
ALIENWARE_PATH="C:/Users/17621/jbt/services"
ALIENWARE_IP="192.168.31.187"

UNIX_SNAPSHOT_BASE="~/jbt-governance/snapshots"
WINDOWS_SNAPSHOT_BASE="C:/Users/17621/jbt-governance/snapshots"

# ============================================================
# 服务配置查询函数（兼容 bash 3.2，不使用 declare -A）
# 格式: HOST|PATH|IP|PORT|HEALTH_PATH|RESTART_MODE|RUNTIME_ID|LOCAL_DIR|REMOTE_DIR|SNAPSHOT_BASE
# ============================================================
get_service_config() {
    local svc="$1"
    case "$svc" in
        data)
            echo "${MINI_HOST}|${MINI_PATH}|${MINI_IP}|8105|/health|docker|JBT-DATA-8105|data|data|${UNIX_SNAPSHOT_BASE}"
            ;;
        decision)
            echo "${STUDIO_HOST}|${STUDIO_PATH}|${STUDIO_IP}|8104|/health|docker|JBT-DECISION-8104|decision|decision|${UNIX_SNAPSHOT_BASE}"
            ;;
        dashboard)
            echo "${STUDIO_HOST}|${STUDIO_PATH}|${STUDIO_IP}|8106|/health|docker|JBT-DASHBOARD-8106|dashboard|dashboard|${UNIX_SNAPSHOT_BASE}"
            ;;
        backtest)
            echo "${AIR_HOST}|${AIR_PATH}|${AIR_IP}|8103|/api/health|docker|JBT-BACKTEST-8103|backtest|backtest|${UNIX_SNAPSHOT_BASE}"
            ;;
        sim-trading)
            echo "${ALIENWARE_HOST}|${ALIENWARE_PATH}|${ALIENWARE_IP}|8101|/health|windows_uvicorn|sim-trading|sim-trading|sim-trading|${WINDOWS_SNAPSHOT_BASE}"
            ;;
        researcher)
            echo "${ALIENWARE_HOST}|${ALIENWARE_PATH}|${ALIENWARE_IP}|8199|/health|windows_researcher|researcher|data|data|${WINDOWS_SNAPSHOT_BASE}"
            ;;
        *)
            return 1
            ;;
    esac
}

# 清单文件路径
MANIFEST_FILE="${HOME}/jbt-governance/deploy-manifest.jsonl"

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
        --target) TARGET="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        --skip-restart) SKIP_RESTART=true; shift ;;
        --skip-health) SKIP_HEALTH=true; shift ;;
        -h|--help)
            sed -n '3,22p' "$0"
            exit 0
            ;;
        *)
            echo "[ERROR] 未知参数: $1"
            exit 1
            ;;
    esac
done

if [[ -z "$SERVICE" ]]; then
    echo "[ERROR] 必须指定 --service"
    echo "用法: $0 --service <data|decision|dashboard|backtest|sim-trading|researcher|all>"
    exit 1
fi

# ============================================================
# 工具函数
# ============================================================
log() { echo "[$(date '+%H:%M:%S')] $*"; }
ok() { echo "[$(date '+%H:%M:%S')] ✓ $*"; }
warn() { echo "[$(date '+%H:%M:%S')] ⚠ $*"; }
err() { echo "[$(date '+%H:%M:%S')] ✗ $*" >&2; }

write_manifest() {
    local svc="$1"
    local status="$2"
    local snapshot_dir="$3"
    local host="$4"
    local ip="$5"
    local remote_dest="$6"

    mkdir -p "$(dirname "$MANIFEST_FILE")"
    local ts
    ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    printf '{"ts":"%s","service":"%s","status":"%s","host":"%s","ip":"%s","remote_dest":"%s","snapshot":"%s","dry_run":%s}\n' \
        "$ts" "$svc" "$status" "$host" "$ip" "$remote_dest" "$snapshot_dir" "$DRY_RUN" >> "$MANIFEST_FILE"
}

resolve_target_override() {
    case "$1" in
        mini)
            echo "${MINI_HOST}|${MINI_PATH}|${MINI_IP}|${UNIX_SNAPSHOT_BASE}"
            ;;
        studio)
            echo "${STUDIO_HOST}|${STUDIO_PATH}|${STUDIO_IP}|${UNIX_SNAPSHOT_BASE}"
            ;;
        air)
            echo "${AIR_HOST}|${AIR_PATH}|${AIR_IP}|${UNIX_SNAPSHOT_BASE}"
            ;;
        alienware)
            echo "${ALIENWARE_HOST}|${ALIENWARE_PATH}|${ALIENWARE_IP}|${WINDOWS_SNAPSHOT_BASE}"
            ;;
        *)
            err "未知 --target: $1（合法值：mini|studio|air|alienware）"
            exit 1
            ;;
    esac
}

validate_target_override() {
    local svc="$1"
    local target="$2"

    [[ -z "$target" ]] && return 0

    case "${svc}:${target}" in
        data:mini|decision:studio|dashboard:studio|backtest:air|backtest:studio|sim-trading:alienware|researcher:alienware)
            return 0
            ;;
        *)
            err "--target ${target} 不适用于服务 ${svc}"
            exit 1
            ;;
    esac
}

run_windows_powershell() {
    local host="$1"
    local ps_cmd="$2"
    local prepared_cmd
    local encoded
    prepared_cmd="\$ProgressPreference='SilentlyContinue'; ${ps_cmd}"
    encoded=$(printf '%s' "$prepared_cmd" | iconv -f UTF-8 -t UTF-16LE | base64 | tr -d '\n')
    ssh "$host" "powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded"
}

is_windows_restart_mode() {
    case "$1" in
        windows_uvicorn|windows_researcher)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

create_local_sync_tarball() {
    local local_src="$1"
    local archive_path="$2"
    local svc="${3:-}"
    local stage_dir
    local extra_excludes=()

    case "$svc" in
        sim-trading)
            # sim-trading 的参考文档目录包含 macOS framework symlink，打到 Windows payload 后会让 robocopy 失败。
            extra_excludes+=("--exclude=参考文档/")
            ;;
    esac

    stage_dir=$(mktemp -d "${TMPDIR:-/tmp}/jbt-rsync-stage.XXXXXX")
    rsync -a --delete "${RSYNC_EXCLUDES[@]}" "${extra_excludes[@]}" "$local_src" "$stage_dir/"
    tar -czf "$archive_path" -C "$stage_dir" .
    rm -rf "$stage_dir"
}

sync_windows_payload() {
    local host="$1"
    local local_src="$2"
    local remote_dest="$3"
    local svc="$4"
    local ts="$5"

    local remote_tmp_root="C:/Users/17621/jbt-governance/tmp"
    local remote_archive="${remote_tmp_root}/${svc}-${ts}.tgz"
    local remote_extract="${remote_tmp_root}/${svc}-${ts}"
    local local_archive

    local_archive=$(mktemp "${TMPDIR:-/tmp}/jbt-${svc}.XXXXXX.tgz")
    create_local_sync_tarball "$local_src" "$local_archive" "$svc"

    run_windows_powershell "$host" "New-Item -ItemType Directory -Force -Path '${remote_tmp_root}' | Out-Null" >/dev/null

    if ! scp "$local_archive" "${host}:${remote_archive}"; then
        rm -f "$local_archive"
        return 1
    fi

    local ps_cmd
    ps_cmd="\$archive='${remote_archive}'; \$extract='${remote_extract}'; \$dest='${remote_dest%/}'; if (!(Test-Path \$archive)) { exit 1 }; if (Test-Path \$extract) { Remove-Item -Recurse -Force \$extract -ErrorAction SilentlyContinue }; New-Item -ItemType Directory -Force -Path \$extract | Out-Null; tar -xf \$archive -C \$extract; New-Item -ItemType Directory -Force -Path \$dest | Out-Null; if ('${svc}' -eq 'sim-trading') { \$null = robocopy \$extract \$dest /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD '参考文档' '.venv' 'runtime' /XF '.env' 'check_trading_day.py' 'manage_sim_trading.py' 'start_am.ps1' 'start_night.ps1' 'start_pm.ps1' 'start_sim_trading.ps1' 'stop_am.ps1' 'stop_night.ps1' 'stop_pm.ps1' 'stop_sim_trading.ps1' 'watchdog.ps1' 'watchdog_sim.log' 'watchdog_sim_trading.ps1' } else { \$null = robocopy \$extract \$dest /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP }; if (\$LASTEXITCODE -gt 7) { exit \$LASTEXITCODE }; Remove-Item -Force \$archive -ErrorAction SilentlyContinue; Remove-Item -Recurse -Force \$extract -ErrorAction SilentlyContinue; exit 0"

    if ! run_windows_powershell "$host" "$ps_cmd"; then
        rm -f "$local_archive"
        return 1
    fi

    rm -f "$local_archive"
}

create_remote_snapshot() {
    local mode="$1"
    local host="$2"
    local remote_dest="$3"
    local snapshot_dir="$4"

    case "$mode" in
        docker)
            ssh "$host" "mkdir -p ${snapshot_dir} && rsync -a --ignore-missing-args ${remote_dest} ${snapshot_dir}/ 2>/dev/null || true"
            ;;
        windows_uvicorn|windows_researcher)
            local ps_cmd
            ps_cmd="\$src='${remote_dest%/}'; \$dst='${snapshot_dir}'; New-Item -ItemType Directory -Force -Path \$dst | Out-Null; if (Test-Path \$src) { \$null = robocopy \$src \$dst /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP }; exit 0"
            run_windows_powershell "$host" "$ps_cmd" >/dev/null 2>&1 || warn "Windows 快照创建失败，继续执行"
            ;;
        *)
            warn "未知快照模式: ${mode}"
            ;;
    esac
}

restart_windows_uvicorn_service() {
    local host="$1"
    local remote_dest="$2"
    local port="$3"

    local ps_cmd
    ps_cmd="\$work='${remote_dest%/}'; \$task='JBT_SimTrading_Watchdog'; \$logDir='C:/Users/17621/jbt/runtime/sim-trading/logs'; \$logFile='C:/Users/17621/jbt/runtime/sim-trading/logs/server.log'; Set-Location \$work; try { Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id \$_ -Force -ErrorAction SilentlyContinue } } catch {}; Start-Sleep -Seconds 2; schtasks.exe /Query /TN \$task 2>\$null | Out-Null; if (\$LASTEXITCODE -eq 0) { schtasks.exe /Run /TN \$task | Out-Null; exit 0 }; if (Test-Path 'start_sim_trading.ps1') { Start-Process -FilePath 'powershell.exe' -WorkingDirectory \$work -ArgumentList '-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-NonInteractive','-File','start_sim_trading.ps1'; exit 0 }; if (Test-Path '.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '.venv\\Scripts\\python.exe').Path } elseif (Test-Path '..\\.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '..\\.venv\\Scripts\\python.exe').Path } elseif (Test-Path '..\\..\\.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '..\\..\\.venv\\Scripts\\python.exe').Path } else { \$py = 'python' }; New-Item -ItemType Directory -Force -Path \$logDir | Out-Null; \$cmd = 'cmd.exe /c cd /d "' + \$work + '" && set PYTHONUNBUFFERED=1 && "' + \$py + '" -m uvicorn src.main:app --host 0.0.0.0 --port ${port} >> "' + \$logFile + '" 2>&1'; if (Get-Command 'wmic.exe' -ErrorAction SilentlyContinue) { wmic.exe process call create \$cmd | Out-Null } else { Start-Process -FilePath 'cmd.exe' -WorkingDirectory \$work -ArgumentList '/c', \$cmd -WindowStyle Hidden }"

    run_windows_powershell "$host" "$ps_cmd"
}

restart_windows_researcher_service() {
    local host="$1"
    local remote_dest="$2"
    local port="$3"

    local ps_cmd
    ps_cmd="\$work='${remote_dest%/}'; \$task='JBT_Researcher_Service'; \$logDir='C:/Users/17621/jbt/runtime/researcher/logs'; \$logFile='C:/Users/17621/jbt/runtime/researcher/logs/server.log'; Set-Location \$work; try { Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id \$_ -Force -ErrorAction SilentlyContinue } } catch {}; Start-Sleep -Seconds 2; cmd.exe /c \"schtasks /Query /TN \"\"\$task\"\" >nul 2>nul\"; if (\$LASTEXITCODE -eq 0) { schtasks.exe /Run /TN \$task | Out-Null; exit 0 }; if (Test-Path 'start_researcher.bat') { Start-Process -FilePath 'cmd.exe' -WorkingDirectory \$work -ArgumentList '/c','start_researcher.bat' -WindowStyle Hidden } else { if (Test-Path '.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '.venv\\Scripts\\python.exe').Path } elseif (Test-Path '..\\.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '..\\.venv\\Scripts\\python.exe').Path } elseif (Test-Path '..\\..\\.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '..\\..\\.venv\\Scripts\\python.exe').Path } else { \$py = 'python' }; New-Item -ItemType Directory -Force -Path \$logDir | Out-Null; \$cmd = 'cd /d "' + \$work + '" && set OLLAMA_URL=http://localhost:11434 && set DATA_API_URL=http://${MINI_IP}:8105 && set PYTHONUNBUFFERED=1 && "' + \$py + '" -u run_researcher_server.py >> "' + \$logFile + '" 2>&1'; Start-Process -FilePath 'cmd.exe' -WorkingDirectory \$work -ArgumentList '/c', \$cmd -WindowStyle Hidden }"

    run_windows_powershell "$host" "$ps_cmd"
}

restart_service() {
    local mode="$1"
    local host="$2"
    local runtime_id="$3"
    local remote_dest="$4"
    local port="$5"
    local svc="$6"

    case "$mode" in
        docker)
            log "重启容器: ${runtime_id}..."
            ssh "$host" "docker restart ${runtime_id} 2>&1"
            ;;
        windows_uvicorn)
            log "重启 Windows 服务: ${svc}..."
            restart_windows_uvicorn_service "$host" "$remote_dest" "$port"
            ;;
        windows_researcher)
            log "重启 Windows 服务: ${svc}..."
            restart_windows_researcher_service "$host" "$remote_dest" "$port"
            ;;
        *)
            warn "未知重启模式: ${mode}"
            return 1
            ;;
    esac
}

deploy_service() {
    local svc="$1"

    local config
    config=$(get_service_config "$svc") || {
        err "未知服务: ${svc}"
        return 1
    }

    local host remote_base ip port health_path restart_mode runtime_id local_dir remote_dir snapshot_base
    IFS='|' read -r host remote_base ip port health_path restart_mode runtime_id local_dir remote_dir snapshot_base <<< "$config"

    validate_target_override "$svc" "$TARGET"
    if [[ -n "$TARGET" ]]; then
        local target_override t_host t_path t_ip t_snapshot_base
        target_override=$(resolve_target_override "$TARGET")
        IFS='|' read -r t_host t_path t_ip t_snapshot_base <<< "$target_override"
        warn "--target ${TARGET} 覆盖默认设备: ${host} → ${t_host}"
        host="$t_host"
        remote_base="$t_path"
        ip="$t_ip"
        snapshot_base="$t_snapshot_base"
    fi

    local local_src="${PWD}/services/${local_dir}/"
    local remote_dest="${remote_base}/${remote_dir}/"
    local ts
    ts=$(date '+%Y%m%d-%H%M%S')
    local snapshot_dir="${snapshot_base}/${svc}-${ts}"

    log "========================================"
    log "发布服务: ${svc}"
    log "  源:    ${local_src}"
    log "  目标:  ${host}:${remote_dest}"
    log "  快照:  ${snapshot_dir}"
    log "========================================"

    if [[ ! -d "$local_src" ]]; then
        err "本地目录不存在: ${local_src}"
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] 仅做离线预演，不连接远端"
        if is_windows_restart_mode "$restart_mode"; then
            log "[DRY-RUN] 将执行: 本地打包 + scp 上传 + Windows robocopy 镜像同步 ${local_src} -> ${host}:${remote_dest}"
        else
            log "[DRY-RUN] 将执行: rsync -avz --delete ... ${local_src} ${host}:${remote_dest}"
        fi
        ok "dry-run 预演完成，跳过快照、rsync、重启与健康检查"
        write_manifest "$svc" "dry_run" "$snapshot_dir" "$host" "$ip" "$remote_dest"
        return 0
    fi

    local rsync_cmd=(
        rsync -avz
        --delete
        "${RSYNC_EXCLUDES[@]}"
    )

    log "在远端创建快照..."
    create_remote_snapshot "$restart_mode" "$host" "$remote_dest" "$snapshot_dir"

    if is_windows_restart_mode "$restart_mode"; then
        log "开始 Windows 文件同步..."
        if sync_windows_payload "$host" "$local_src" "$remote_dest" "$svc" "$ts"; then
            ok "Windows 文件同步完成"
        else
            err "Windows 文件同步失败"
            write_manifest "$svc" "sync_failed" "$snapshot_dir" "$host" "$ip" "$remote_dest"
            return 1
        fi
    else
        rsync_cmd+=("${local_src}" "${host}:${remote_dest}")

        log "开始 rsync..."
        if "${rsync_cmd[@]}"; then
            ok "rsync 完成"
        else
            err "rsync 失败"
            write_manifest "$svc" "rsync_failed" "$snapshot_dir" "$host" "$ip" "$remote_dest"
            return 1
        fi
    fi

    if [[ "$SKIP_RESTART" != "true" ]]; then
        if restart_service "$restart_mode" "$host" "$runtime_id" "$remote_dest" "$port" "$svc"; then
            ok "重启成功"
            sleep 5
        else
            err "重启失败"
            write_manifest "$svc" "restart_failed" "$snapshot_dir" "$host" "$ip" "$remote_dest"
            return 1
        fi
    else
        warn "--skip-restart: 跳过重启"
    fi

    if [[ "$SKIP_HEALTH" != "true" ]]; then
        local health_url="http://${ip}:${port}${health_path}"
        log "健康检查: ${health_url}"
        local attempt=0
        local max_attempts=6
        while [[ $attempt -lt $max_attempts ]]; do
            attempt=$((attempt + 1))
            if curl -sf --max-time 5 "$health_url" > /dev/null 2>&1; then
                ok "健康检查通过 (尝试 ${attempt}/${max_attempts})"
                write_manifest "$svc" "success" "$snapshot_dir" "$host" "$ip" "$remote_dest"
                return 0
            fi
            warn "健康检查失败 (${attempt}/${max_attempts})，5s 后重试..."
            sleep 5
        done

        err "健康检查超时，服务可能未正常启动"
        err "快照路径: ${host}:${snapshot_dir}"
        err "可使用 jbt_rsync_rollback.sh --service ${svc} 回滚"
        write_manifest "$svc" "health_failed" "$snapshot_dir" "$host" "$ip" "$remote_dest"
        return 1
    fi

    warn "--skip-health: 跳过健康检查"
    write_manifest "$svc" "success_no_health" "$snapshot_dir" "$host" "$ip" "$remote_dest"
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
    SERVICES=("data" "decision" "dashboard" "backtest" "sim-trading" "researcher")
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
