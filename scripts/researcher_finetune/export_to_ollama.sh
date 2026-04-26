#!/usr/bin/env bash
# F4: 把 LoRA adapter 合并到基础权重 → 量化 q4_K_M → ollama create
#
# 在 Studio 上执行（紧接 train_lora_mlx.sh train 之后）
#
# 用法：
#   bash scripts/researcher_finetune/export_to_ollama.sh

set -euo pipefail

JBT_ROOT="${JBT_ROOT:-$HOME/jbt}"
SCRIPT_DIR="$JBT_ROOT/scripts/researcher_finetune"
RUNTIME_DIR="$JBT_ROOT/runtime/researcher_finetune"
ADAPTER_DIR="$RUNTIME_DIR/adapters"
FUSED_DIR="$RUNTIME_DIR/fused_model"
GGUF_DIR="$RUNTIME_DIR/gguf"
PROGRESS_LOG="$RUNTIME_DIR/train_progress.log"

BASE_MODEL="${BASE_MODEL:-mlx-community/Qwen3-14B-4bit}"
TARGET_TAG="${TARGET_TAG:-qwen3-jbt-news:14b-q4_K_M}"

mkdir -p "$FUSED_DIR" "$GGUF_DIR"

log_progress() {
  echo "[$(date -u +%FT%TZ)] export: $1" | tee -a "$PROGRESS_LOG"
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

if [[ -d "$HOME/jbt-mlx-venv" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/jbt-mlx-venv/bin/activate"
fi

# ============================================================
# Step 1: fuse adapter 回基础模型
# ============================================================
log_progress "==== fuse: 合并 LoRA adapter → fused_model ===="
notify "FUSE_START" "开始合并 LoRA adapter 到基础权重"

python3 -u -m mlx_lm.fuse \
  --model "$BASE_MODEL" \
  --adapter-path "$ADAPTER_DIR" \
  --save-path "$FUSED_DIR" \
  2>&1 | tee -a "$PROGRESS_LOG"

log_progress "fuse done: $FUSED_DIR"

# ============================================================
# Step 2: 转 GGUF + 量化 q4_K_M
# ============================================================
# 优先用 llama.cpp 的 convert 脚本（需在 Studio 上预装 llama.cpp 或借助 ollama 的本地 modelfile）
log_progress "==== convert + quantize → gguf q4_K_M ===="
notify "QUANT_START" "开始转 GGUF 并量化为 q4_K_M"

if command -v llama.cpp >/dev/null 2>&1; then
  CONVERT="$(command -v llama.cpp)/convert.py"
elif [[ -x "$HOME/llama.cpp/convert.py" ]]; then
  CONVERT="$HOME/llama.cpp/convert.py"
elif [[ -x "$HOME/llama.cpp/convert_hf_to_gguf.py" ]]; then
  CONVERT="$HOME/llama.cpp/convert_hf_to_gguf.py"
else
  log_progress "WARN: 未找到 llama.cpp convert 脚本，将尝试通过 ollama create 直接打包 fused_model（不经 gguf 中转，体积更大）"
  CONVERT=""
fi

GGUF_PATH="$GGUF_DIR/qwen3-jbt-news-14b-f16.gguf"
QUANT_PATH="$GGUF_DIR/qwen3-jbt-news-14b-q4_K_M.gguf"

if [[ -n "$CONVERT" ]]; then
  python3 "$CONVERT" "$FUSED_DIR" --outfile "$GGUF_PATH" --outtype f16 2>&1 | tee -a "$PROGRESS_LOG"

  if command -v llama-quantize >/dev/null 2>&1; then
    QUANT_BIN="$(command -v llama-quantize)"
  elif [[ -x "$HOME/llama.cpp/llama-quantize" ]]; then
    QUANT_BIN="$HOME/llama.cpp/llama-quantize"
  elif [[ -x "$HOME/llama.cpp/build/bin/llama-quantize" ]]; then
    QUANT_BIN="$HOME/llama.cpp/build/bin/llama-quantize"
  else
    log_progress "ERROR: 未找到 llama-quantize 二进制"
    notify "QUANT_ERROR" "缺少 llama-quantize 二进制，请在 Studio 安装 llama.cpp"
    exit 3
  fi

  "$QUANT_BIN" "$GGUF_PATH" "$QUANT_PATH" Q4_K_M 2>&1 | tee -a "$PROGRESS_LOG"
  log_progress "quantize done: $QUANT_PATH"
fi

# ============================================================
# Step 3: ollama create
# ============================================================
log_progress "==== ollama create $TARGET_TAG ===="

MODELFILE="$RUNTIME_DIR/Modelfile.${TARGET_TAG//[:\/]/_}"
if [[ -f "$QUANT_PATH" ]]; then
  cat > "$MODELFILE" <<EOF
FROM $QUANT_PATH
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
PARAMETER temperature 0.0
PARAMETER num_ctx 8192
SYSTEM """You are the JBT researcher model. Return strict JSON only. Do not emit reasoning, markdown fences, or think tags."""
EOF
else
  log_progress "WARN: GGUF 量化文件缺失，使用 fused_model 直接构建（体积大）"
  cat > "$MODELFILE" <<EOF
FROM $FUSED_DIR
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
PARAMETER temperature 0.0
PARAMETER num_ctx 8192
SYSTEM """You are the JBT researcher model. Return strict JSON only. Do not emit reasoning, markdown fences, or think tags."""
EOF
fi

ollama create "$TARGET_TAG" -f "$MODELFILE" 2>&1 | tee -a "$PROGRESS_LOG"

log_progress "ollama create done: $TARGET_TAG"
notify "QUANT_DONE" "量化打包完成，模型已注册: $TARGET_TAG"
