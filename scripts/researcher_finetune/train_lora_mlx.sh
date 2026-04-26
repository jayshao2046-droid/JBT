#!/usr/bin/env bash
# F4: Studio QLoRA 训练脚本（mlx-lm）
# 在 Studio (M2 Max 32GB) 上执行，全程后台 nohup 运行 ~24h
#
# 工作流：
#   1. 从 Alienware (D:\researcher_reports) 拉取历史研报到本地 raw/
#   2. 调用 prepare_dataset.py 规整为 messages JSONL → dataset_f4.jsonl
#   3. 调用 build_finance_corpus.py 生成 F5 金融语料 → dataset_f5.jsonl
#   4. 调用 merge_with_f4_dataset.py 合并 → train.jsonl + val.jsonl
#   5. mlx_lm.lora 训练 LoRA，输出到 adapters/
#   6. 全程通过 send_milestone_notify.py 发飞书通知
#
# 用法（Studio）：
#   bash scripts/researcher_finetune/train_lora_mlx.sh prepare   # 仅准备数据
#   bash scripts/researcher_finetune/train_lora_mlx.sh train     # 仅训练（需先 prepare）
#   bash scripts/researcher_finetune/train_lora_mlx.sh full      # 一条龙

set -euo pipefail

PHASE="${1:-full}"

# ============================================================
# 路径配置
# ============================================================
JBT_ROOT="${JBT_ROOT:-$HOME/jbt}"
SCRIPT_DIR="$JBT_ROOT/scripts/researcher_finetune"
RUNTIME_DIR="$JBT_ROOT/runtime/researcher_finetune"
RAW_DIR="$RUNTIME_DIR/raw_alienware"
DATA_DIR="$RUNTIME_DIR/dataset"
ADAPTER_DIR="$RUNTIME_DIR/adapters"
EXTERNAL_DIR="$RUNTIME_DIR/external"
LOG_DIR="$RUNTIME_DIR"
PROGRESS_LOG="$LOG_DIR/train_progress.log"
TRAIN_LOG="$LOG_DIR/train_run.log"

mkdir -p "$RAW_DIR" "$DATA_DIR" "$ADAPTER_DIR" "$EXTERNAL_DIR" "$LOG_DIR"

# ============================================================
# 训练超参
# ============================================================
BASE_MODEL="${BASE_MODEL:-mlx-community/Qwen3-14B-4bit}"
# Note: mlx-lm 默认基座对齐 F4/F5 任务目标 qwen3:14b。
# 若后续需要切换到本地 convert 产物，可通过环境变量覆盖 BASE_MODEL。
LORA_RANK="${LORA_RANK:-32}"
LORA_ALPHA="${LORA_ALPHA:-64}"
NUM_EPOCHS="${NUM_EPOCHS:-5}"
BATCH_SIZE="${BATCH_SIZE:-2}"
LEARNING_RATE="${LEARNING_RATE:-1e-4}"
SAVE_EVERY="${SAVE_EVERY:-200}"
STEPS_PER_EPOCH="${STEPS_PER_EPOCH:-0}"

# ============================================================
# Alienware 拉取配置
# ============================================================
ALIENWARE_HOST="${ALIENWARE_HOST:-17621@192.168.31.187}"
ALIENWARE_REPORTS_PATH='D:/researcher_reports'

# ============================================================
# 飞书通知（每个里程碑，turquoise NOTIFY 卡片，按 user memory 标准）
# 走 services/data/.env 的 FEISHU_TRADING_WEBHOOK_URL
# ============================================================
FEISHU_WEBHOOK="${FEISHU_WEBHOOK:-}"
if [[ -z "$FEISHU_WEBHOOK" && -f "$JBT_ROOT/services/data/.env" ]]; then
  FEISHU_WEBHOOK="$(grep -E '^FEISHU_TRADING_WEBHOOK_URL=' "$JBT_ROOT/services/data/.env" | head -1 | cut -d= -f2- || true)"
fi
export FEISHU_WEBHOOK

notify() {
  local stage="$1"; shift
  local message="$*"
  STAGE="$stage" MSG="$message" python3 - <<'PYEOF' || true
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
        "header": {
            "title": {"tag": "plain_text",
                       "content": f"\U0001F4E3 [TRAIN-NOTIFY] qwen3-jbt-news LoRA - {stage}"},
            "template": "turquoise",
        },
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md",
                                       "content": f"**事件**：{stage}\n**详情**：{msg}"}},
            {"tag": "hr"},
            {"tag": "note",
             "elements": [{"tag": "plain_text",
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

log_progress() {
  local msg="$1"
  echo "[$(date -u +%FT%TZ)] $msg" | tee -a "$PROGRESS_LOG"
}

# ============================================================
# Phase 1: 拉取 Alienware 历史研报
# ============================================================
phase_fetch() {
  log_progress "==== fetch: 拉取 Alienware D:\\researcher_reports → $RAW_DIR ===="
  notify "FETCH_START" "开始从 Alienware 拉取历史研报到 Studio"
  # 使用 ssh + tar 的方式，规避 Windows rsync 兼容性
  ssh -o ConnectTimeout=10 "$ALIENWARE_HOST" \
    "powershell -Command \"if (Test-Path 'D:\\researcher_reports') { Compress-Archive -Path 'D:\\researcher_reports\\*' -DestinationPath 'D:\\researcher_reports_pull.zip' -Force; Write-Output OK } else { Write-Output MISSING; exit 1 }\""
  scp -o ConnectTimeout=10 "$ALIENWARE_HOST:D:/researcher_reports_pull.zip" "$RUNTIME_DIR/researcher_reports_pull.zip"
  ssh -o ConnectTimeout=10 "$ALIENWARE_HOST" \
    "powershell -Command \"Remove-Item 'D:\\researcher_reports_pull.zip' -Force\"" || true
  rm -rf "$RAW_DIR"
  mkdir -p "$RAW_DIR"
  unzip -q -o "$RUNTIME_DIR/researcher_reports_pull.zip" -d "$RAW_DIR"
  rm -f "$RUNTIME_DIR/researcher_reports_pull.zip"
  local count
  count=$(find "$RAW_DIR" -name "*.json" | wc -l | tr -d ' ')
  log_progress "fetch done: $count json files"
  notify "FETCH_DONE" "Alienware 拉取完成，共 $count 个 JSON 文件"
}

# ============================================================
# Phase 2: 数据规整
# ============================================================
phase_prepare() {
  log_progress "==== prepare: 规整数据 ===="
  notify "PREPARE_START" "开始规整 F4+F5 数据集"

  local external_args=()
  local external_count=0
  if find "$EXTERNAL_DIR" -maxdepth 1 -type f -name '*.jsonl' | grep -q .; then
    while IFS= read -r ext_file; do
      external_args+=(--external-jsonl "$ext_file")
      external_count=$((external_count + 1))
    done < <(find "$EXTERNAL_DIR" -maxdepth 1 -type f -name '*.jsonl' | sort)
  fi

  python3 "$SCRIPT_DIR/prepare_dataset.py" \
    --input "$RAW_DIR" \
    --output "$DATA_DIR/dataset_f4.jsonl" \
    --format messages \
    --keep-metadata

  python3 "$SCRIPT_DIR/build_finance_corpus.py" \
    --out-dir "$DATA_DIR" \
    "${external_args[@]}"

  python3 "$SCRIPT_DIR/merge_with_f4_dataset.py" \
    --f4-jsonl "$DATA_DIR/dataset_f4.jsonl" \
    --f5-jsonl "$DATA_DIR/dataset_f5.jsonl" \
    --out-dir "$DATA_DIR" \
    --val-ratio 0.1

  local train_n val_n
  train_n=$(wc -l < "$DATA_DIR/train.jsonl" | tr -d ' ')
  val_n=$(wc -l < "$DATA_DIR/val.jsonl" | tr -d ' ')
  log_progress "prepare done: train=$train_n val=$val_n external_jsonl=$external_count"
  notify "PREPARE_DONE" "数据规整完成: train=$train_n val=$val_n external_jsonl=$external_count"
}

# ============================================================
# Phase 3: LoRA 训练
# ============================================================
phase_train() {
  log_progress "==== train: 启动 LoRA 训练 ===="
  notify "TRAIN_START" "LoRA 训练启动 base=$BASE_MODEL rank=$LORA_RANK epoch=$NUM_EPOCHS"

  pushd "$RUNTIME_DIR" >/dev/null

  # 优先使用 Studio 上的 venv（若存在）
  if [[ -d "$HOME/jbt-mlx-venv" ]]; then
    # shellcheck disable=SC1091
    source "$HOME/jbt-mlx-venv/bin/activate"
  fi

  if ! python3 -c "import mlx_lm" 2>/dev/null; then
    log_progress "ERROR: mlx-lm 未安装。请先在 Studio 上执行: python3 -m venv ~/jbt-mlx-venv && source ~/jbt-mlx-venv/bin/activate && pip install -U mlx mlx-lm"
    notify "TRAIN_ERROR" "mlx-lm 未安装，已退出"
    exit 2
  fi

  # 估算总迭代步数
  local train_n iters
  train_n=$(wc -l < "$DATA_DIR/train.jsonl" | tr -d ' ')
  if [[ "$STEPS_PER_EPOCH" -gt 0 ]]; then
    iters="$STEPS_PER_EPOCH"
  else
    iters=$(( (train_n / BATCH_SIZE + 1) * NUM_EPOCHS ))
  fi
  log_progress "estimated iters: $iters (train_n=$train_n batch=$BATCH_SIZE epoch=$NUM_EPOCHS)"

  # mlx-lm 期望数据目录中包含 train.jsonl / valid.jsonl
  cp -f "$DATA_DIR/train.jsonl" "$DATA_DIR/train.jsonl.bak" 2>/dev/null || true
  cp -f "$DATA_DIR/val.jsonl" "$DATA_DIR/valid.jsonl"

  # mlx-lm >= 0.21 不再支持 --lora-parameters 内联参数，改为 YAML config
  local LORA_CONFIG="$RUNTIME_DIR/lora_config.yaml"
  cat > "$LORA_CONFIG" <<EOF
lora_parameters:
  rank: $LORA_RANK
  scale: 20.0
  dropout: 0.05
EOF
  log_progress "lora config: $LORA_CONFIG (rank=$LORA_RANK alpha=$LORA_ALPHA scale=20.0 dropout=0.05)"

  python3 -u -m mlx_lm lora \
    --model "$BASE_MODEL" \
    --train \
    --data "$DATA_DIR" \
    --adapter-path "$ADAPTER_DIR" \
    --batch-size "$BATCH_SIZE" \
    --num-layers 16 \
    --iters "$iters" \
    --learning-rate "$LEARNING_RATE" \
    --steps-per-eval 100 \
    --steps-per-report 20 \
    --save-every "$SAVE_EVERY" \
    -c "$LORA_CONFIG" \
    2>&1 | tee -a "$TRAIN_LOG"

  popd >/dev/null

  log_progress "==== train done ===="
  notify "TRAIN_DONE" "LoRA 训练完成，adapter 输出: $ADAPTER_DIR"
}

# ============================================================
# 主流程
# ============================================================
case "$PHASE" in
  fetch)    phase_fetch ;;
  prepare)  phase_prepare ;;
  train)    phase_train ;;
  full)
    phase_fetch
    phase_prepare
    phase_train
    ;;
  *)
    echo "用法: $0 {fetch|prepare|train|full}"
    exit 1
    ;;
esac
