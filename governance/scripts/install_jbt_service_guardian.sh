#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GOVERNANCE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${GOVERNANCE_ROOT}/.." && pwd)"
TEMPLATE="${GOVERNANCE_ROOT}/launchagents/com.jbt.service_guardian.plist"
TARGET_DIR="${HOME}/Library/LaunchAgents"
TARGET_PLIST="${TARGET_DIR}/com.jbt.service_guardian.plist"
RUNTIME_DIR="${HOME}/jbt-governance"
RUNTIME_SCRIPTS="${RUNTIME_DIR}/scripts"
RUNTIME_LOGS="${RUNTIME_DIR}/logs"
RUNTIME_STATE="${RUNTIME_DIR}/state"
WRAPPER_SCRIPT="${RUNTIME_SCRIPTS}/jbt_service_guardian.sh"
LOG_PATH="${RUNTIME_LOGS}/jbt_service_guardian.log"
STATE_PATH="${RUNTIME_STATE}/jbt_service_guardian.json"
LABEL="com.jbt.service_guardian"
DOMAIN="gui/$(id -u)"

if [[ ! -f "${TEMPLATE}" ]]; then
    echo "ERROR: plist template not found: ${TEMPLATE}" >&2
    exit 1
fi

PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
    PYTHON_BIN="$(command -v python3)"
fi

mkdir -p "${TARGET_DIR}" "${RUNTIME_SCRIPTS}" "${RUNTIME_LOGS}" "${RUNTIME_STATE}"

cat > "${WRAPPER_SCRIPT}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "${REPO_ROOT}"
exec "${PYTHON_BIN}" "${REPO_ROOT}/governance/scripts/jbt_service_guardian.py" \
  --repo-root "${REPO_ROOT}" \
  --state-path "${STATE_PATH}" \
  --failure-threshold 2 \
  --timeout 6
EOF

chmod +x "${WRAPPER_SCRIPT}"

TEMPLATE_PATH="${TEMPLATE}" \
TARGET_PATH="${TARGET_PLIST}" \
WRAPPER_SCRIPT_VALUE="${WRAPPER_SCRIPT}" \
HOME_VALUE="${HOME}" \
LOG_PATH_VALUE="${LOG_PATH}" \
python3 - <<'PYEOF'
import os
from pathlib import Path

template = Path(os.environ["TEMPLATE_PATH"]).read_text(encoding="utf-8")
rendered = (
    template
    .replace("__WRAPPER_SCRIPT__", os.environ["WRAPPER_SCRIPT_VALUE"])
    .replace("__HOME__", os.environ["HOME_VALUE"])
    .replace("__LOG_PATH__", os.environ["LOG_PATH_VALUE"])
)
Path(os.environ["TARGET_PATH"]).write_text(rendered, encoding="utf-8")
PYEOF

plutil -lint "${TARGET_PLIST}" >/dev/null

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

echo ""
echo "=== JBT Service Guardian Installed ==="
echo "label      = ${LABEL}"
echo "plist      = ${TARGET_PLIST}"
echo "wrapper    = ${WRAPPER_SCRIPT}"
echo "state      = ${STATE_PATH}"
echo "log        = ${LOG_PATH}"
echo "interval   = 60s"
echo "checks     = data / sim-trading / researcher / decision / dashboard / backtest"