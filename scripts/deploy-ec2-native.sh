#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/smartspend}"
APP_USER="${APP_USER:-ubuntu}"
APP_GROUP="${APP_GROUP:-ubuntu}"
APP_URL="${APP_URL:-http://127.0.0.1}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"
FRONTEND_ORIGINS="${FRONTEND_ORIGINS:-$APP_URL,http://127.0.0.1:3001,http://localhost:3001}"
FRONTEND_ORIGIN_REGEX="${FRONTEND_ORIGIN_REGEX:-https://.*\\.vercel\\.app}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$APP_DIR"

sudo chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"

if [ ! -d backend/.venv ]; then
  "$PYTHON_BIN" -m venv backend/.venv
fi

source backend/.venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
deactivate

npm install

export BACKEND_API_BASE="http://${BACKEND_HOST}:${BACKEND_PORT}"
export NEXT_PUBLIC_BACKEND_API_BASE="http://${BACKEND_HOST}:${BACKEND_PORT}"
export NEXT_PUBLIC_BACKEND_WS_BASE="ws://${BACKEND_HOST}:${BACKEND_PORT}"
export APP_URL="$APP_URL"
export NEXT_PUBLIC_APP_URL="$APP_URL"

npm run build

sudo tee /etc/systemd/system/smartspend-backend.service >/dev/null <<EOF
[Unit]
Description=SmartSpend FastAPI Backend
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR
Environment=FRONTEND_ORIGINS=$FRONTEND_ORIGINS
Environment=FRONTEND_ORIGIN_REGEX=$FRONTEND_ORIGIN_REGEX
Environment=SMARTSPEND_LOG_DIR=$APP_DIR/backend/logs
ExecStart=$APP_DIR/backend/.venv/bin/python -m uvicorn backend.main:app --host $BACKEND_HOST --port $BACKEND_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/smartspend-frontend.service >/dev/null <<EOF
[Unit]
Description=SmartSpend Next.js Frontend
After=network.target smartspend-backend.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR
Environment=BACKEND_API_BASE=http://$BACKEND_HOST:$BACKEND_PORT
Environment=NEXT_PUBLIC_BACKEND_API_BASE=http://$BACKEND_HOST:$BACKEND_PORT
Environment=NEXT_PUBLIC_BACKEND_WS_BASE=ws://$BACKEND_HOST:$BACKEND_PORT
Environment=APP_URL=$APP_URL
Environment=NEXT_PUBLIC_APP_URL=$APP_URL
ExecStart=/usr/bin/npm run start -- --hostname 127.0.0.1 --port $FRONTEND_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable smartspend-backend smartspend-frontend
sudo systemctl restart smartspend-backend
sleep 10
sudo systemctl restart smartspend-frontend
sleep 10

curl --fail "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null
curl --fail "http://127.0.0.1:${FRONTEND_PORT}/api/health" >/dev/null
