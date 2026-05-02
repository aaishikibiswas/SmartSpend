#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y nginx

# Simple health endpoint and page so ALB target checks pass consistently.
cat >/var/www/html/index.html <<'EOF'
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>SmartSpend Scalable Web Tier</title>
  </head>
  <body style="font-family: Arial, sans-serif; padding: 24px;">
    <h1>SmartSpend Auto Scaling Tier</h1>
    <p>This page is served by an EC2 instance behind an Application Load Balancer.</p>
  </body>
</html>
EOF

cat >/var/www/html/health <<'EOF'
ok
EOF

cat >/etc/nginx/sites-available/default <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    root /var/www/html;
    index index.html;

    location = /health {
        add_header Content-Type text/plain;
        return 200 "ok";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

systemctl enable nginx
systemctl restart nginx
