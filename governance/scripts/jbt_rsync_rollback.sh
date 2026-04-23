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
#   ./jbt_rsync_rollback.sh --service data --list
#   ./jbt_rsync_rollback.sh --service sim-trading
#   ./jbt_rsync_rollback.sh --service researcher --pick 2

set -euo pipefail

MANIFEST_FILE="${HOME}/jbt-governance/deploy-manifest.jsonl"

# ============================================================
# 设备配置（与 deploy 保持一致）
# ============================================================
MINI_HOST="jaybot@192.168.31.74"
MINI_PATH="~/JBT/services"
MINI_IP="192.168.31.74"

STUDIO_HOST="jaybot@192.168.31.142"
STUDIO_PATH="~/JBT/services"
STUDIO_IP="192.168.31.142"

AIR_HOST="jayshao@192.168.31.156"
AIR_PATH="~/JBT/services"
AIR_IP="192.168.31.156"

ALIENWARE_HOST="17621@192.168.31.187"
ALIENWARE_PATH="C:/Users/17621/jbt/services"
ALIENWARE_IP="192.168.31.187"

# ============================================================
# 服务配置查询函数（兼容 bash 3.2，不使用 declare -A）
# 格式: HOST|PATH|IP|PORT|HEALTH_PATH|RESTART_MODE|RUNTIME_ID|LOCAL_DIR|REMOTE_DIR
# ============================================================
get_service_config() {
    local svc="$1"
    case "$svc" in
        data)
            echo "${MINI_HOST}|${MINI_PATH}|${MINI_IP}|8105|/health|docker|JBT-DATA-8105|data|data"
            ;;
        decision)
            echo "${STUDIO_HOST}|${STUDIO_PATH}|${STUDIO_IP}|8104|/health|docker|JBT-DECISION-8104|decision|decision"
            ;;
        dashboard)
            echo "${STUDIO_HOST}|${STUDIO_PATH}|${STUDIO_IP}|8106|/health|docker|JBT-DASHBOARD-8106|dashboard|dashboard"
            ;;
        backtest)
            echo "${AIR_HOST}|${AIR_PATH}|${AIR_IP}|8103|/api/health|docker|JBT-BACKTEST-8103|backtest|backtest"
            ;;
        sim-trading)
            echo "${ALIENWARE_HOST}|${ALIENWARE_PATH}|${ALIENWARE_IP}|8101|/health|windows_uvicorn|sim-trading|sim-trading|sim-trading"
            ;;
        researcher)
            echo "${ALIENWARE_HOST}|${ALIENWARE_PATH}|${ALIENWARE_IP}|8199|/health|windows_researcher|researcher|data|data"
            ;;
        *)
            return 1
            ;;
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
        --list) LIST_ONLY=true; shift ;;
        --pick) PICK_N="$2"; shift 2 ;;
        -h|--help)
            sed -n '3,14p' "$0"
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
    echo "用法: $0 --service <data|decision|dashboard|backtest|sim-trading|researcher>"
    exit 1
fi

get_service_config "$SERVICE" > /dev/null 2>&1 || {
    echo "[ERROR] 未知服务: ${SERVICE}（合法值：data|decision|dashboard|backtest|sim-trading|researcher）"
    exit 1
}

log() { echo "[$(date '+%H:%M:%S')] $*"; }
ok() { echo "[$(date '+%H:%M:%S')] ✓ $*"; }
warn() { echo "[$(date '+%H:%M:%S')] ⚠ $*"; }
err() { echo "[$(date '+%H:%M:%S')] ✗ $*" >&2; }

run_windows_powershell() {
    local host="$1"
    local ps_cmd="$2"
    local prepared_cmd
    local encoded
    prepared_cmd="\$ProgressPreference='SilentlyContinue'; ${ps_cmd}"
    encoded=$(printf '%s' "$prepared_cmd" | iconv -f UTF-8 -t UTF-16LE | base64 | tr -d '\n')
    ssh "$host" "powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded"
}

restart_windows_uvicorn_service() {
    local host="$1"
    local remote_path="$2"
    local port="$3"

    local ps_cmd
    ps_cmd="\$work='${remote_path%/}'; \$task='JBT_SimTrading_Watchdog'; \$logDir='C:/Users/17621/jbt/runtime/sim-trading/logs'; \$logFile='C:/Users/17621/jbt/runtime/sim-trading/logs/server.log'; Set-Location \$work; try { Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id \$_ -Force -ErrorAction SilentlyContinue } } catch {}; Start-Sleep -Seconds 2; schtasks.exe /Query /TN \$task 2>\$null | Out-Null; if (\$LASTEXITCODE -eq 0) { schtasks.exe /Run /TN \$task | Out-Null; exit 0 }; if (Test-Path 'start_sim_trading.ps1') { Start-Process -FilePath 'powershell.exe' -WorkingDirectory \$work -ArgumentList '-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-NonInteractive','-File','start_sim_trading.ps1'; exit 0 }; if (Test-Path '.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '.venv\\Scripts\\python.exe').Path } elseif (Test-Path '..\\.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '..\\.venv\\Scripts\\python.exe').Path } elseif (Test-Path '..\\..\\.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '..\\..\\.venv\\Scripts\\python.exe').Path } else { \$py = 'python' }; New-Item -ItemType Directory -Force -Path \$logDir | Out-Null; \$cmd = 'cmd.exe /c cd /d "' + \$work + '" && set PYTHONUNBUFFERED=1 && "' + \$py + '" -m uvicorn src.main:app --host 0.0.0.0 --port ${port} >> "' + \$logFile + '" 2>&1'; if (Get-Command 'wmic.exe' -ErrorAction SilentlyContinue) { wmic.exe process call create \$cmd | Out-Null } else { Start-Process -FilePath 'cmd.exe' -WorkingDirectory \$work -ArgumentList '/c', \$cmd -WindowStyle Hidden }"

    run_windows_powershell "$host" "$ps_cmd"
}

restart_windows_researcher_service() {
    local host="$1"
    local remote_path="$2"
    local port="$3"

    local ps_cmd
    ps_cmd="\$work='${remote_path%/}'; \$task='JBT_Researcher_Service'; \$logDir='C:/Users/17621/jbt/runtime/researcher/logs'; \$logFile='C:/Users/17621/jbt/runtime/researcher/logs/server.log'; Set-Location \$work; try { Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id \$_ -Force -ErrorAction SilentlyContinue } } catch {}; Start-Sleep -Seconds 2; cmd.exe /c \"schtasks /Query /TN \"\"\$task\"\" >nul 2>nul\"; if (\$LASTEXITCODE -eq 0) { schtasks.exe /Run /TN \$task | Out-Null; exit 0 }; if (Test-Path 'start_researcher.bat') { Start-Process -FilePath 'cmd.exe' -WorkingDirectory \$work -ArgumentList '/c','start_researcher.bat' -WindowStyle Hidden } else { if (Test-Path '.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '.venv\\Scripts\\python.exe').Path } elseif (Test-Path '..\\.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '..\\.venv\\Scripts\\python.exe').Path } elseif (Test-Path '..\\..\\.venv\\Scripts\\python.exe') { \$py = (Resolve-Path '..\\..\\.venv\\Scripts\\python.exe').Path } else { \$py = 'python' }; New-Item -ItemType Directory -Force -Path \$logDir | Out-Null; \$cmd = 'cd /d "' + \$work + '" && set OLLAMA_URL=http://localhost:11434 && set DATA_API_URL=http://192.168.31.74:8105 && set PYTHONUNBUFFERED=1 && "' + \$py + '" -u run_researcher_server.py >> "' + \$logFile + '" 2>&1'; Start-Process -FilePath 'cmd.exe' -WorkingDirectory \$work -ArgumentList '/c', \$cmd -WindowStyle Hidden }"

    run_windows_powershell "$host" "$ps_cmd"
}

restart_service() {
    local mode="$1"
    local host="$2"
    local runtime_id="$3"
    local remote_path="$4"
    local port="$5"

    case "$mode" in
        docker)
            ssh "$host" "docker restart ${runtime_id} 2>&1"
            ;;
        windows_uvicorn)
            restart_windows_uvicorn_service "$host" "$remote_path" "$port"
            ;;
        windows_researcher)
            restart_windows_researcher_service "$host" "$remote_path" "$port"
            ;;
        *)
            err "未知重启模式: ${mode}"
            return 1
            ;;
    esac
}

snapshot_exists() {
    local mode="$1"
    local host="$2"
    local snapshot="$3"

    case "$mode" in
        docker)
            ssh "$host" "test -d ${snapshot}"
            ;;
        windows_uvicorn|windows_researcher)
            local ps_cmd
            ps_cmd="if (Test-Path '${snapshot}') { exit 0 } else { exit 1 }"
            run_windows_powershell "$host" "$ps_cmd"
            ;;
        *)
            return 1
            ;;
    esac
}

restore_snapshot() {
    local mode="$1"
    local host="$2"
    local snapshot="$3"
    local remote_path="$4"

    case "$mode" in
        docker)
            ssh "$host" "rsync -a --delete ${snapshot}/ ${remote_path}/"
            ;;
        windows_uvicorn|windows_researcher)
            local ps_cmd
            ps_cmd="\$src='${snapshot}'; \$dst='${remote_path%/}'; if (!(Test-Path \$src)) { exit 1 }; New-Item -ItemType Directory -Force -Path \$dst | Out-Null; \$null = robocopy \$src \$dst /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP; exit 0"
            run_windows_powershell "$host" "$ps_cmd"
            ;;
        *)
            err "未知恢复模式: ${mode}"
            return 1
            ;;
    esac
}

if [[ ! -f "$MANIFEST_FILE" ]]; then
    err "清单文件不存在: ${MANIFEST_FILE}"
    err "请先运行 jbt_rsync_deploy.sh 创建部署记录"
    exit 1
fi

ENTRIES=$(grep "\"service\":\"${SERVICE}\"" "$MANIFEST_FILE" | grep -E '"status":"(success|success_no_health)"' | grep '"dry_run":false' || true)

if [[ -z "$ENTRIES" ]]; then
    err "未找到服务 [${SERVICE}] 的成功部署记录"
    err "请检查清单: ${MANIFEST_FILE}"
    exit 1
fi

SORTED=$(echo "$ENTRIES" | sort -t'"' -k4 -r)
TOTAL=$(echo "$SORTED" | wc -l | tr -d ' ')

list_snapshots() {
    echo ""
    echo "服务 [${SERVICE}] 可用快照（共 ${TOTAL} 条，最新在前）："
    echo "──────────────────────────────────────────────────────"

    local idx=1
    while IFS= read -r entry; do
        local ts snapshot host
        ts=$(echo "$entry" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ts'])")
        snapshot=$(echo "$entry" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['snapshot'])")
        host=$(echo "$entry" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['host'])")
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

if [[ $PICK_N -lt 1 || $PICK_N -gt $TOTAL ]]; then
    err "无效的序号 --pick ${PICK_N}，有效范围: 1~${TOTAL}"
    exit 1
fi

SELECTED=$(echo "$SORTED" | sed -n "${PICK_N}p")
SNAPSHOT=$(echo "$SELECTED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['snapshot'])")
MANIFEST_HOST=$(echo "$SELECTED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('host',''))")
MANIFEST_IP=$(echo "$SELECTED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ip',''))")
MANIFEST_REMOTE_PATH=$(echo "$SELECTED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('remote_dest',''))")
TS=$(echo "$SELECTED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ts'])")

config=$(get_service_config "$SERVICE")
IFS='|' read -r host remote_base ip port health_path restart_mode runtime_id local_dir remote_dir <<< "$config"

if [[ -n "$MANIFEST_HOST" ]]; then
    host="$MANIFEST_HOST"
fi
if [[ -n "$MANIFEST_IP" ]]; then
    ip="$MANIFEST_IP"
fi

remote_path="${remote_base}/${remote_dir}"
if [[ -n "$MANIFEST_REMOTE_PATH" ]]; then
    remote_path="$MANIFEST_REMOTE_PATH"
fi

echo ""
warn "即将回滚服务 [${SERVICE}]"
warn "  快照时间: ${TS}"
warn "  快照路径: ${host}:${SNAPSHOT}"
warn "  回滚目标: ${host}:${remote_path}"
echo ""
read -rp "确认回滚？[y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    log "已取消"
    exit 0
fi

log "开始回滚..."

if ! snapshot_exists "$restart_mode" "$host" "$SNAPSHOT"; then
    err "快照目录不存在: ${host}:${SNAPSHOT}"
    err "快照可能已过期或被删除"
    exit 1
fi

log "恢复快照 → 目标..."
restore_snapshot "$restart_mode" "$host" "$SNAPSHOT" "$remote_path"
ok "快照恢复完成"

log "重启服务..."
if restart_service "$restart_mode" "$host" "$runtime_id" "$remote_path" "$port"; then
    ok "重启成功"
    sleep 5
else
    err "重启失败，请手动检查"
    exit 1
fi

health_url="http://${ip}:${port}${health_path}"
log "健康检查: ${health_url}"
attempt=0
while [[ $attempt -lt 6 ]]; do
    attempt=$((attempt + 1))
    if curl -sf --max-time 5 "$health_url" > /dev/null 2>&1; then
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

mkdir -p "$(dirname "$MANIFEST_FILE")"
printf '{"ts":"%s","service":"%s","status":"rollback","host":"%s","ip":"%s","remote_dest":"%s","snapshot":"%s","dry_run":false}\n' \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$SERVICE" "$host" "$ip" "$remote_path" "$SNAPSHOT" >> "$MANIFEST_FILE"

ok "回滚完成！服务 [${SERVICE}] 已恢复到 ${TS}"
