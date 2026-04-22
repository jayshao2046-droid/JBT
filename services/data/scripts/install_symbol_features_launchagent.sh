#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SERVICE_ROOT}/../.." && pwd)"
TEMPLATE="${SERVICE_ROOT}/configs/launchagents/com.jbt.symbol_features.plist"
TARGET_DIR="${HOME}/Library/LaunchAgents"
TARGET_PLIST="${TARGET_DIR}/com.jbt.symbol_features.plist"
LOG_DIR="${REPO_ROOT}/data/logs"
LOG_PATH="${LOG_DIR}/symbol_features_launchd.log"
SCRIPT_PATH="${REPO_ROOT}/scripts/update_symbol_features.py"
LABEL="com.jbt.symbol_features"
DOMAIN="gui/$(id -u)"

detect_python_bin() {
    if [[ -n "${JBT_SYMBOL_FEATURES_PYTHON:-}" ]]; then
        printf '%s\n' "${JBT_SYMBOL_FEATURES_PYTHON}"
        return
    fi
    command -v python3
}

if [[ ! -f "${TEMPLATE}" ]]; then
    echo "template not found: ${TEMPLATE}" >&2
    exit 1
fi

if [[ ! -f "${SCRIPT_PATH}" ]]; then
    echo "script not found: ${SCRIPT_PATH}" >&2
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
SCRIPT_PATH_VALUE="${SCRIPT_PATH}" \
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
    .replace("__SCRIPT_PATH__", os.environ["SCRIPT_PATH_VALUE"])
)
Path(os.environ["TARGET_PATH"]).write_text(rendered, encoding="utf-8")
PYEOF

plutil -lint "${TARGET_PLIST}" >/dev/null

launchctl enable "user/$(id -u)/${LABEL}" >/dev/null 2>&1 || true
launchctl enable "${DOMAIN}/${LABEL}" >/dev/null 2>&1 || true

if launchctl print "${DOMAIN}/${LABEL}" >/dev/null 2>&1; then
    launchctl bootout "${DOMAIN}/${LABEL}" >/dev/null 2>&1 || true
fi

launchctl bootstrap "${DOMAIN}" "${TARGET_PLIST}"

echo "installed ${LABEL}"
echo "python=${PYTHON_BIN}"
echo "script=${SCRIPT_PATH}"
echo "plist=${TARGET_PLIST}"
echo "log=${LOG_PATH}"