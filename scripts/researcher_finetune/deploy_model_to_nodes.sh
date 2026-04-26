#!/usr/bin/env bash
# F4: 推送新模型 qwen3-jbt-news:14b-q4_K_M 到 Alienware 与 Studio 两端
#
# 在 Studio 上执行（紧接 export_to_ollama.sh 之后）
# 通过 ollama show / ollama pull / scp gguf 的方式同步两端
#
# 用法：
#   bash scripts/researcher_finetune/deploy_model_to_nodes.sh

set -euo pipefail

JBT_ROOT="${JBT_ROOT:-$HOME/jbt}"
SCRIPT_DIR="$JBT_ROOT/scripts/researcher_finetune"
RUNTIME_DIR="$JBT_ROOT/runtime/researcher_finetune"
GGUF_DIR="$RUNTIME_DIR/gguf"
PROGRESS_LOG="$RUNTIME_DIR/train_progress.log"

TARGET_TAG="${TARGET_TAG:-qwen3-jbt-news:14b-q4_K_M}"
BASELINE_TAG="${BASELINE_TAG:-qwen3:14b-q4_K_M}"
QUANT_PATH="$GGUF_DIR/qwen3-jbt-news-14b-q4_K_M.gguf"

ALIENWARE_HOST="${ALIENWARE_HOST:-17621@192.168.31.187}"
ALIENWARE_REMOTE_DIR='C:/Users/17621/jbt-models'

log_progress() {
  echo "[$(date -u +%FT%TZ)] deploy: $1" | tee -a "$PROGRESS_LOG"
}

FEISHU_WEBHOOK="${FEISHU_WEBHOOK:-}"
if [[ -z "$FEISHU_WEBHOOK" && -f "$JBT_ROOT/services/data/.env" ]]; then
  FEISHU_WEBHOOK="$(grep -E '^FEISHU_TRADING_WEBHOOK_URL=' "$JBT_ROOT/services/data/.env" | head -1 | cut -d= -f2- || true)"
fi
export FEISHU_WEBHOOK

notify() {
  local stage="$1"; shift
  STAGE="$stage" MSG="$*" python3 - <<'PYEOF' || true
import json, os, sys, urllib.request, datetime
url = os.environ.get("FEISHU_WEBHOOK", "").strip()
if not url:
    sys.exit(0)
stage = os.environ.get("STAGE", "NOTIFY")
msg = os.environ.get("MSG", "")
ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
card = {
    "msg_type": "interactive",
    "card": {
        "header": {"title": {"tag": "plain_text",
                              "content": f"\U0001F4E3 [TRAIN-NOTIFY] qwen3-jbt-news LoRA - {stage}"},
                   "template": "turquoise"},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md",
                                       "content": f"**事件**：{stage}\n**详情**：{msg}"}},
            {"tag": "hr"},
            {"tag": "note", "elements": [{"tag": "plain_text",
                                            "content": f"JBT data | researcher LoRA | {ts}"}]},
        ],
    },
}
try:
    req = urllib.request.Request(url, data=json.dumps(card).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5).read()
except Exception as e:
    print(f"[notify-warn] {e}", file=sys.stderr)
PYEOF
}

# ============================================================
# Step 1: Studio 端校验（已通过 export_to_ollama.sh 注册）
# ============================================================
log_progress "==== studio: 校验 baseline $BASELINE_TAG ===="
if ollama list | grep -q "^$BASELINE_TAG[[:space:]]"; then
  log_progress "studio: baseline $BASELINE_TAG 已就位"
else
  log_progress "WARN: studio 上未找到 baseline $BASELINE_TAG；后续仍以 BASE_MODEL=$BASELINE_TAG 对齐口径"
fi

log_progress "==== studio: 校验 ollama list 包含 $TARGET_TAG ===="
if ollama list | grep -q "^$TARGET_TAG[[:space:]]"; then
  log_progress "studio: $TARGET_TAG 已就位"
else
  log_progress "ERROR: studio 上 ollama list 未找到 $TARGET_TAG"
  notify "DEPLOY_ERROR" "Studio 上模型缺失：$TARGET_TAG"
  exit 4
fi

# ============================================================
# Step 2: 推送 GGUF 到 Alienware 并执行远端 ollama create
# ============================================================
log_progress "==== alienware: baseline align → $BASELINE_TAG ===="
if ssh -o ConnectTimeout=10 "$ALIENWARE_HOST" "ollama list" | tr -d '\r' | grep -q "^$BASELINE_TAG[[:space:]]"; then
  log_progress "alienware: baseline $BASELINE_TAG 已存在"
else
  if ssh -o ConnectTimeout=10 "$ALIENWARE_HOST" "ollama cp qwen3:14b $BASELINE_TAG"; then
    log_progress "alienware: 通过 ollama cp 将 qwen3:14b 对齐为 $BASELINE_TAG"
  else
    log_progress "alienware: ollama cp 不可用，回退为 ollama pull $BASELINE_TAG"
    ssh -o ConnectTimeout=10 "$ALIENWARE_HOST" "ollama pull $BASELINE_TAG"
  fi
fi

log_progress "==== alienware: scp gguf → $ALIENWARE_HOST ===="
notify "PUSH_START" "开始向 Alienware 推送模型 $TARGET_TAG"

if [[ ! -f "$QUANT_PATH" ]]; then
  log_progress "ERROR: $QUANT_PATH 不存在，请先执行 export_to_ollama.sh"
  notify "DEPLOY_ERROR" "GGUF 量化文件缺失：$QUANT_PATH"
  exit 5
fi

# Alienware 是 Windows + OpenSSH，使用 powershell 创建目录
ssh -o ConnectTimeout=10 "$ALIENWARE_HOST" \
  "powershell -Command \"New-Item -ItemType Directory -Force -Path '$ALIENWARE_REMOTE_DIR' | Out-Null; Write-Output OK\""

scp -o ConnectTimeout=10 "$QUANT_PATH" "$ALIENWARE_HOST:$ALIENWARE_REMOTE_DIR/qwen3-jbt-news-14b-q4_K_M.gguf"

# 在 Alienware 端创建 Modelfile 并执行 ollama create
ssh -o ConnectTimeout=10 "$ALIENWARE_HOST" "powershell -Command \"\$mf = @'
FROM $ALIENWARE_REMOTE_DIR/qwen3-jbt-news-14b-q4_K_M.gguf
TEMPLATE \\\"\\\"\\\"{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
\\\"\\\"\\\"
PARAMETER stop \\\"<|im_end|>\\\"
PARAMETER stop \\\"<|im_start|>\\\"
PARAMETER temperature 0.0
PARAMETER num_ctx 8192
SYSTEM \\\"\\\"\\\"You are the JBT researcher model. Return strict JSON only. Do not emit reasoning, markdown fences, or think tags.\\\"\\\"\\\"
'@ ; \$mf | Out-File -Encoding ascii -FilePath '$ALIENWARE_REMOTE_DIR/Modelfile.qwen3-jbt-news' ; ollama create $TARGET_TAG -f '$ALIENWARE_REMOTE_DIR/Modelfile.qwen3-jbt-news'\""

# 校验 Alienware 端
log_progress "==== alienware: 校验 ollama list 包含 $TARGET_TAG ===="
ssh -o ConnectTimeout=10 "$ALIENWARE_HOST" "ollama list" | tr -d '\r' | tee -a "$PROGRESS_LOG" | grep -q "^$TARGET_TAG[[:space:]]" || {
  log_progress "ERROR: alienware 上 ollama list 未找到 $TARGET_TAG"
  notify "DEPLOY_ERROR" "Alienware 上模型缺失：$TARGET_TAG"
  exit 6
}

log_progress "==== deploy done: 两端均已就位 ===="
notify "PUSH_DONE" "两端推送完成 ✅ Studio + Alienware 均已就位 $TARGET_TAG"
