#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SERVICE_ROOT}/../.." && pwd)"
TEMPLATE="${SERVICE_ROOT}/configs/launchagents/com.jbt.data_scheduler.plist"
TARGET_DIR="${HOME}/Library/LaunchAgents"
TARGET_PLIST="${TARGET_DIR}/com.jbt.data_scheduler.plist"
LOG_DIR="${HOME}/jbt-data/logs"
LOG_PATH="${LOG_DIR}/data_scheduler_launchd.log"
LABEL="com.jbt.data_scheduler"
DOMAIN="gui/$(id -u)"

detect_python_bin() {
    if [[ -n "${JBT_DATA_PYTHON:-}" ]]; then
        printf '%s\n' "${JBT_DATA_PYTHON}"
        return
    fi

    local running
    running="$(ps aux | grep 'services.data.src.scheduler.data_scheduler --daemon' | grep -v grep | awk '{print $11; exit}')"
    if [[ -n "${running}" ]]; then
        printf '%s\n' "${running}"
        return
    fi

    if [[ -x "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python" ]]; then
        printf '%s\n' "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python"
        return
    fi

    command -v python3
}

if [[ ! -f "${TEMPLATE}" ]]; then
    echo "template not found: ${TEMPLATE}" >&2
    exit 1
fi

mkdir -p "${TARGET_DIR}" "${LOG_DIR}"
PYTHON_BIN="$(detect_python_bin)"

TEMPLATE_PATH="${TEMPLATE}" \
TARGET_PATH="${TARGET_PLIST}" \
PYTHON_PATH_VALUE="${PYTHON_BIN}" \
REPO_ROOT_VALUE="${REPO_ROOT}" \
HOME_VALUE="${HOME}" \
LOG_PATH_VALUE="${LOG_PATH}" \
python3 - <<'PYEOF'
import os
from pathlib import Path

template = Path(os.environ["TEMPLATE_PATH"]).read_text(encoding="utf-8")
rendered = (
    template
    .replace("__PYTHON_BIN__", os.environ["PYTHON_PATH_VALUE"])
    .replace("__REPO_ROOT__", os.environ["REPO_ROOT_VALUE"])
    .replace("__HOME__", os.environ["HOME_VALUE"])
    .replace("__LOG_PATH__", os.environ["LOG_PATH_VALUE"])
)
Path(os.environ["TARGET_PATH"]).write_text(rendered, encoding="utf-8")
PYEOF

plutil -lint "${TARGET_PLIST}" >/dev/null

pkill -f "services.data.src.scheduler.data_scheduler --daemon" >/dev/null 2>&1 || true
sleep 2

launchctl enable "user/$(id -u)/${LABEL}" >/dev/null 2>&1 || true
launchctl enable "${DOMAIN}/${LABEL}" >/dev/null 2>&1 || true

if launchctl print "${DOMAIN}/${LABEL}" >/dev/null 2>&1; then
    launchctl bootout "${DOMAIN}/${LABEL}" >/dev/null 2>&1 || true
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        if ! launchctl print "${DOMAIN}/${LABEL}" >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
fi

if launchctl print "${DOMAIN}/${LABEL}" >/dev/null 2>&1; then
    launchctl kickstart -k "${DOMAIN}/${LABEL}"
else
    launchctl bootstrap "${DOMAIN}" "${TARGET_PLIST}"
fi

echo "installed ${LABEL}"
echo "python=${PYTHON_BIN}"
echo "plist=${TARGET_PLIST}"