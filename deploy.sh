#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/deploy-logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/deploy-$(date +%Y%m%d-%H%M%S).log"

log() {
  echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG_FILE"
}

retry() {
  local attempts="$1"
  local sleep_seconds="$2"
  shift 2
  local n=1
  until "$@"; do
    if [[ "$n" -ge "$attempts" ]]; then
      return 1
    fi
    log "Retry $n/$attempts failed for: $*"
    sleep "$sleep_seconds"
    n=$((n + 1))
  done
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Missing required command: $1"
    exit 1
  fi
}

cd "$ROOT_DIR"

require_command docker
require_command curl

log "Validating frontend"
npm run lint | tee -a "$LOG_FILE"
npm run build | tee -a "$LOG_FILE"

log "Validating backend import"
python -c "import backend.main; print('backend_import_ok')" | tee -a "$LOG_FILE"

log "Building and starting docker compose stack"
docker compose down --remove-orphans | tee -a "$LOG_FILE" || true
docker compose build | tee -a "$LOG_FILE"
docker compose up -d | tee -a "$LOG_FILE"

log "Waiting for backend health"
retry 20 5 curl --fail --silent http://127.0.0.1:8001/health >/dev/null

log "Waiting for frontend health"
retry 20 5 curl --fail --silent http://127.0.0.1:3001/api/health >/dev/null

log "Deployment verified successfully"
log "Frontend: http://127.0.0.1:3001"
log "Backend: http://127.0.0.1:8001/health"
