#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <ec2-user> <ec2-host> <app-url>"
  exit 1
fi

EC2_USER="$1"
EC2_HOST="$2"
APP_URL="$3"

: "${FRONTEND_IMAGE:?Set FRONTEND_IMAGE before running}"
: "${BACKEND_IMAGE:?Set BACKEND_IMAGE before running}"
: "${FRONTEND_ORIGINS:?Set FRONTEND_ORIGINS before running}"

ssh "${EC2_USER}@${EC2_HOST}" bash <<EOF
set -euo pipefail
mkdir -p ~/smartspend
cat > ~/smartspend/docker-compose.prod.yml <<COMPOSE
services:
  backend:
    image: ${BACKEND_IMAGE}
    restart: unless-stopped
    environment:
      FRONTEND_ORIGINS: ${FRONTEND_ORIGINS}
      FRONTEND_ORIGIN_REGEX: https://.*\\.vercel\\.app
      SMARTSPEND_LOG_DIR: /app/backend/logs
    ports:
      - "8001:8001"
    volumes:
      - backend_data:/app/backend/data
      - backend_logs:/app/backend/logs

  frontend:
    image: ${FRONTEND_IMAGE}
    restart: unless-stopped
    depends_on:
      - backend
    environment:
      BACKEND_API_BASE: http://backend:8001
      NEXT_PUBLIC_BACKEND_API_BASE: http://backend:8001
      NEXT_PUBLIC_BACKEND_WS_BASE: wss://${APP_URL#https://}
      APP_URL: ${APP_URL}
      NEXT_PUBLIC_APP_URL: ${APP_URL}
    ports:
      - "3001:3001"

volumes:
  backend_data:
  backend_logs:
COMPOSE

docker compose -f ~/smartspend/docker-compose.prod.yml pull
docker compose -f ~/smartspend/docker-compose.prod.yml up -d
curl --fail http://127.0.0.1:8001/health
EOF
