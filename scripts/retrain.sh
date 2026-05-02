#!/usr/bin/env bash
set -euo pipefail

# SmartSpend daily retraining script.
# Usage:
#   bash scripts/retrain.sh
#   bash scripts/retrain.sh --install-cron

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DATASET_PATH="${DATASET_PATH:-$PROJECT_DIR/data/transactions.csv}"
LOG_DIR="${PROJECT_DIR}/results"
LOG_FILE="${LOG_DIR}/cron_retrain.log"
CRON_EXPR="${CRON_EXPR:-0 2 * * *}" # default: daily at 2 AM

mkdir -p "$LOG_DIR" "$PROJECT_DIR/models"

run_training() {
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting daily retraining..." | tee -a "$LOG_FILE"
  "$PYTHON_BIN" "$PROJECT_DIR/src/train.py" \
    --dataset "$DATASET_PATH" \
    --models-dir "$PROJECT_DIR/models" \
    --results-dir "$PROJECT_DIR/results" \
    --run-tag "cron-daily" | tee -a "$LOG_FILE"
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Retraining complete." | tee -a "$LOG_FILE"
}

install_cron() {
  local cmd="${CRON_EXPR} cd ${PROJECT_DIR} && ${PYTHON_BIN} ${PROJECT_DIR}/src/train.py --dataset ${DATASET_PATH} --models-dir ${PROJECT_DIR}/models --results-dir ${PROJECT_DIR}/results --run-tag cron-daily >> ${LOG_FILE} 2>&1"
  (crontab -l 2>/dev/null | grep -v "src/train.py --dataset"; echo "$cmd") | crontab -
  echo "Installed cron job:"
  echo "$cmd"
}

if [[ "${1:-}" == "--install-cron" ]]; then
  install_cron
else
  run_training
fi

