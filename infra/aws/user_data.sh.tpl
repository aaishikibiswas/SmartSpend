#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y \
  git \
  curl \
  nginx \
  nodejs \
  npm \
  python3 \
  python3-pip \
  python3-venv \
  build-essential \
  libgomp1

npm install -g pm2

cat >/etc/nginx/sites-available/smartspend <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/smartspend /etc/nginx/sites-enabled/smartspend
systemctl enable nginx
systemctl restart nginx

mkdir -p /opt/smartspend
chown -R ubuntu:ubuntu /opt/smartspend
